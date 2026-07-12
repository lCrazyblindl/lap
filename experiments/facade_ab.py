"""v0.9 — live A/B: gcore PR#13's deferred facade vs the direct subset menu.

The static half is done (menu 363 vs 488,013 tokens; docs/UPSTREAM-ISSUES.md §4). This
measures the half that is live-only: what the deferred tier actually costs and whether the
model can *use* it. Discovery tasks — "find the right catalog tool for X and report its
required parameters" — need no real Gcore account (search_tools/get_tool_schema run
locally against the catalog; nothing is executed), have unambiguous ground truth from the
static scan, and exercise exactly the round-trips deferral moves the cost into.

Modes, same 5 tasks, k repeats, billed usage from the API (not estimates):
- direct: the README-suggested 77-tool subset menu in `tools=`; the model answers from
  the menu (instructed not to invoke - a tool_use gets an error tool_result and costs a
  turn, which is honest: that's what a wrong call costs a real session too).
- facade: the PR branch's 3 meta-tools in `tools=`; search_tools/get_tool_schema calls
  are executed against the live MCP server (dummy key - discovery never hits the API).

Cost control: Haiku, per-run turn caps, a global billed-input abort at MAX_INPUT_TOKENS.
Reads ANTHROPIC_API_KEY from the environment (set at User scope; never printed).
Checkpoints every run to %TEMP%; --tasks / --modes filters allow resume. Writes
docs/FACADE-AB.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
import tempfile
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lap import mcp_client  # noqa: E402

UVX = str(REPO / ".venv" / "Scripts" / "uvx.exe")
GIT_MAIN = "gcore-mcp-server@git+https://github.com/G-Core/gcore-mcp-server.git"
GIT_PR13 = GIT_MAIN + "@feat/code-execution-mode-impl"
SUBSET = "instances,management,cloud.gpu_baremetal.clusters.*"
MODEL = "claude-haiku-4-5"
MAX_INPUT_TOKENS = 5_000_000  # global abort: ~$5 at Haiku input pricing
CHECKPOINT = pathlib.Path(tempfile.gettempdir()) / "lap-facade-ab.jsonl"

# (task prompt, subset underscore name, facade catalog dotted name) - the same operation
# is named differently per mode (direct abbreviates: rgns/insts/clstrs; the catalog is
# full-form dotted), so BOTH count as correct.
TASKS = [
    ("List all cloud regions available in this account.",
     "cloud_rgns_ls", "cloud.regions.list"),
    ("Get the details of one specific cloud project.",
     "cloud_projs_get", "cloud.projects.get"),
    ("Resize an existing virtual machine instance to a different flavor.",
     "cloud_insts_resz", "cloud.instances.resize"),
    ("List the hardware flavors available for GPU baremetal clusters.",
     "cloud_gpu_baremetal_clstrs_flavs_ls", "cloud.gpu_baremetal.clusters.flavors.list"),
    ("Acknowledge all pending cloud tasks in a project at once.",
     "cloud_tsks_ack_all", "cloud.tasks.acknowledge_all"),
]

PROMPT = ("You are connected to the Gcore API via tools. Task: {task}\n"
          "Do NOT perform the operation. Identify which single tool is the right one and "
          "reply in plain text with: the tool name, and its required parameters. "
          "{mode_hint}")
HINT_DIRECT = "Answer directly from the tool definitions you already have; do not call any tool."
HINT_FACADE = ("Use search_tools/get_tool_schema to find it in the catalog first, then answer "
               "in text. Do not use execute_code.")


def env_for(pkg_env: dict) -> dict:
    return {**os.environ, "GCORE_API_KEY": "dummy-lap-scan", **pkg_env}


def anthropic_tools(tools: list[dict]) -> list[dict]:
    return [{"name": t["name"], "description": t["description"] or "",
             "input_schema": t["input_schema"] or {"type": "object", "properties": {}}}
            for t in tools]


def norm(s: str) -> str:
    return s.lower().replace(".", "_").replace("-", "_")


def correct(text: str, names: list[str], required: list[str]) -> bool:
    t = norm(text)
    return any(norm(n) in t for n in names) and all(p.lower() in t for p in required)


async def run_one(client, tools_param, transport, task, mode, max_turns):
    from fastmcp import Client as McpClient

    messages = [{"role": "user", "content": PROMPT.format(
        task=task, mode_hint=HINT_FACADE if mode == "facade" else HINT_DIRECT)}]
    usage_in = usage_out = calls = 0
    text = ""

    async def loop(mcp):
        nonlocal usage_in, usage_out, calls, text
        for _ in range(max_turns):
            resp = await client.messages.create(
                model=MODEL, max_tokens=700, tools=tools_param, messages=messages)
            usage_in += resp.usage.input_tokens
            usage_out += resp.usage.output_tokens
            text = " ".join(b.text for b in resp.content if b.type == "text") or text
            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            if not tool_uses:
                return
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for tu in tool_uses:
                calls += 1
                if mode == "facade" and mcp is not None and tu.name != "execute_code":
                    try:
                        out = await mcp.call_tool(tu.name, tu.input or {})
                        payload = json.dumps(getattr(out, "structured_content", None)
                                             or [getattr(c, "text", "") for c in out.content],
                                             ensure_ascii=False)[:4000]
                    except Exception as exc:  # noqa: BLE001
                        payload = f"error: {exc!r}"[:300]
                else:
                    payload = ("error: do not invoke tools for this task; "
                               "answer in plain text")
                results.append({"type": "tool_result", "tool_use_id": tu.id, "content": payload})
            messages.append({"role": "user", "content": results})

    if mode == "facade":
        async with McpClient(transport) as mcp:
            await loop(mcp)
    else:
        await loop(None)
    return {"input": usage_in, "output": usage_out, "tool_calls": calls, "text": text}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--tasks", default="", help="comma list of task indices to run (resume)")
    ap.add_argument("--modes", default="direct,facade")
    args = ap.parse_args()
    sys.stdout.reconfigure(errors="replace")

    from fastmcp.client.transports import StdioTransport

    print("fetching subset menu...")
    sub_transport = StdioTransport(UVX, ["--from", GIT_MAIN, "gcore-mcp-server"],
                                   env=env_for({"GCORE_TOOLS": SUBSET}), keep_alive=False)
    subset_tools = mcp_client.fetch_tools(sub_transport, timeout=240)
    by_name = {t["name"]: t for t in subset_tools}
    for _, gt, _cat in TASKS:
        assert gt in by_name, f"ground-truth tool {gt} missing from subset"
    print("fetching facade menu...")
    fac_env = env_for({"GCORE_MCP_ROUTING": "code_exec", "GCORE_TOOLS": "*"})
    facade_tools = mcp_client.fetch_tools(
        StdioTransport(UVX, ["--from", GIT_PR13, "gcore-mcp-server"],
                       env=fac_env, keep_alive=False), timeout=240)
    asyncio.run(run_all(args, subset_tools, by_name, facade_tools, fac_env))


async def run_all(args, subset_tools, by_name, facade_tools, fac_env) -> None:
    from anthropic import AsyncAnthropic
    from fastmcp.client.transports import StdioTransport

    client = AsyncAnthropic()
    mode_cfg = {
        "direct": (anthropic_tools(subset_tools), None, 3),
        "facade": (anthropic_tools(facade_tools), None, 6),
    }
    task_idx = [int(x) for x in args.tasks.split(",") if x.strip()] or range(len(TASKS))
    total_in = 0
    done = [json.loads(line) for line in CHECKPOINT.read_text(encoding="utf-8").splitlines()] \
        if CHECKPOINT.exists() else []
    have = {(r["task"], r["mode"], r["rep"]) for r in done}

    for ti in task_idx:
        task, gt, cat = TASKS[ti]
        required = (by_name[gt]["input_schema"] or {}).get("required") or []
        for mode in args.modes.split(","):
            tools_param, _, max_turns = mode_cfg[mode]
            for rep in range(args.repeats):
                if (ti, mode, rep) in have:
                    continue
                transport = StdioTransport(UVX, ["--from", GIT_PR13, "gcore-mcp-server"],
                                           env=fac_env, keep_alive=False) \
                    if mode == "facade" else None
                r = await run_one(client, tools_param, transport, task, mode, max_turns)
                r.update({"task": ti, "mode": mode, "rep": rep, "gt": gt,
                          "ok": correct(r["text"], [gt, cat], required)})
                r["text"] = r["text"][:300]
                total_in += r["input"]
                with CHECKPOINT.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(r) + "\n")
                print(f"T{ti} {mode:6} rep{rep}: in={r['input']:>6} out={r['output']:>4} "
                      f"calls={r['tool_calls']} ok={r['ok']}")
                if total_in > MAX_INPUT_TOKENS:
                    sys.exit("aborting: MAX_INPUT_TOKENS budget reached")

    rows = [json.loads(line) for line in CHECKPOINT.read_text(encoding="utf-8").splitlines()]
    write_doc(rows)


def write_doc(rows: list[dict]) -> None:
    def agg(mode):
        sel = [r for r in rows if r["mode"] == mode]
        return {"runs": len(sel),
                "ok": sum(r["ok"] for r in sel),
                "in": sum(r["input"] for r in sel) / max(1, len(sel)),
                "out": sum(r["output"] for r in sel) / max(1, len(sel)),
                "calls": sum(r["tool_calls"] for r in sel) / max(1, len(sel))}

    d, f = agg("direct"), agg("facade")
    lines = [
        "# Live A/B — gcore PR#13's deferred facade vs the direct subset menu",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/facade_ab.py`](../experiments/facade_ab.py). Model "
        f"**{MODEL}**, billed `usage` figures from the API (no estimates, no prompt "
        "caching). Discovery tasks (find the right catalog tool + its required params) — "
        "ground truth from the static scan; nothing is executed against Gcore (dummy key; "
        "`search_tools`/`get_tool_schema` run locally). Static context: the facade menu "
        "measures 363 tokens vs 488,013 for `GCORE_TOOLS=*` and 46,528 for the README "
        "subset ([UPSTREAM-ISSUES §4](UPSTREAM-ISSUES.md))._",
        "",
        "| mode | runs | correct | avg billed input/run | avg output | avg tool round-trips |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| direct (77-tool subset in context) | {d['runs']} | {d['ok']}/{d['runs']} | "
        f"{d['in']:,.0f} | {d['out']:,.0f} | {d['calls']:.1f} |",
        f"| facade (3 meta-tools, search on demand) | {f['runs']} | {f['ok']}/{f['runs']} | "
        f"{f['in']:,.0f} | {f['out']:,.0f} | {f['calls']:.1f} |",
        "",
        "## Per-task",
        "",
        "| task | direct ok | direct in | facade ok | facade in | facade round-trips |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for ti, (task, _gt, _cat) in enumerate(TASKS):
        def sel(mode):
            return [r for r in rows if r["mode"] == mode and r["task"] == ti]
        ds, fs = sel("direct"), sel("facade")
        if not ds and not fs:
            continue
        lines.append(
            f"| {task[:52]} | {sum(r['ok'] for r in ds)}/{len(ds)} | "
            f"{sum(r['input'] for r in ds) / max(1, len(ds)):,.0f} | "
            f"{sum(r['ok'] for r in fs)}/{len(fs)} | "
            f"{sum(r['input'] for r in fs) / max(1, len(fs)):,.0f} | "
            f"{sum(r['tool_calls'] for r in fs) / max(1, len(fs)):.1f} |")
    ratio = d["in"] / f["in"] if f["in"] else 0
    lines += [
        "",
        f"**Read.** Per discovery task the facade billed **{ratio:.1f}× less input** on "
        "average. The structural cause: the direct mode re-sends the whole subset menu with "
        "every API call, the facade sends 3 meta-tool definitions plus only the search/schema "
        "results it asked for. Accuracy is the behavioral half — see the table (the R6 lesson "
        "is why this run exists: paper savings and live savings are different claims).",
        "",
        "_Caveats: one cheap model, k per cell as shown, 5 discovery tasks (tool selection, "
        "not end-to-end execution — that needs a real Gcore account); no prompt caching "
        "(deliberate: it discounts price, not context); facade `execute_code` was off-limits "
        "by instruction._",
    ]
    out = REPO / "docs" / "FACADE-AB.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {out}")


if __name__ == "__main__":
    main()
