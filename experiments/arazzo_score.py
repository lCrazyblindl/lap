"""v0.9 W6 — Arazzo workflow scoring: what does a *declared* multi-step workflow cost an
agent vs planning the same chain ad hoc?

[Arazzo](https://github.com/OAI/Arazzo-Specification) (OpenAPI Initiative, 1.0) declares
multi-step API workflows: steps referencing operationIds, workflow-level inputs, data flow
between steps. For an agent this is a *macro tool*: expose the workflow as ONE callable
(name + summary + its `inputs` JSON schema) and an executor runs the steps server-side.

Measured here, on the OAI repo's own example documents (real third-party artifacts, not
ours): per workflow —
- bucket A: the workflow-as-tool definition vs the naive menu of the underlying API;
- bucket B: one workflow call vs the ad-hoc chain (sum of per-step typical calls);
- the structural bonus that doesn't show in A/B: intermediate step *results* (bucket C)
  never enter the model's context at all — the same server-enforced property that made
  Tool Search hold up where behavioral savings didn't (docs/TOOL-SEARCH.md vs CODE-EXEC.md).

Writes docs/ARAZZO.md. Offline; fetches the example files from the OAI repo (cached in
%TEMP%/lap-arazzo)."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from datetime import date

import httpx
import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lap import estimate, tokens  # noqa: E402
from lap import openapi_ir as ir  # noqa: E402
from lap.menu import MENUS  # noqa: E402

RAW = "https://raw.githubusercontent.com/OAI/Arazzo-Specification/main/examples/1.0.0"
PAIRS = [("pet-coupons", "pet-coupons.arazzo.yaml", "pet-coupons.openapi.yaml"),
         ("bnpl", "bnpl-arazzo.yaml", "bnpl-openapi.yaml"),
         ("oauth", "oauth.arazzo.yaml", "oauth.openapi.yaml")]
CACHE = pathlib.Path(tempfile.gettempdir()) / "lap-arazzo"


def fetch(fname: str) -> str:
    CACHE.mkdir(exist_ok=True)
    p = CACHE / fname
    if not p.exists():
        r = httpx.get(f"{RAW}/{fname}", timeout=30, follow_redirects=True)
        r.raise_for_status()
        p.write_text(r.text, encoding="utf-8")
    return p.read_text(encoding="utf-8")


def op_by_id(spec: dict) -> dict:
    out = {}
    for op in ir.operations(spec):
        oid = op.raw.get("operationId")
        if oid:
            out[oid] = op
    return out


def wf_tool(wf: dict) -> dict:
    """The workflow as ONE advertised tool: id + summary + its declared inputs schema."""
    return {"name": wf.get("workflowId", "workflow"),
            "description": (wf.get("summary") or wf.get("description") or "").strip(),
            "input_schema": wf.get("inputs") or {"type": "object", "properties": {}}}


def call_tokens(name: str, spec: dict, schema) -> int:
    args = estimate.example_instance(spec, schema) or {}
    return tokens.count(json.dumps({"name": name, "input": args}, separators=(",", ":")))


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    rows = []
    for label, arazzo_f, openapi_f in PAIRS:
        arazzo = yaml.safe_load(fetch(arazzo_f))
        spec = ir._parse(fetch(openapi_f))
        ops = op_by_id(spec)
        naive_tools, _ = MENUS["openapi_full"](spec)
        naive_menu = tokens.count_tools(naive_tools)
        for wf in arazzo.get("workflows", []):
            steps = wf.get("steps", [])
            step_ops = [ops[s["operationId"]] for s in steps if s.get("operationId") in ops]
            if not step_ops:
                continue  # steps reference other workflows / external paths - skip honestly
            chain_b = sum(estimate.estimate_call(spec, op) for op in step_ops)
            tool = wf_tool(wf)
            wf_menu = tokens.count_tools([tool])
            wf_b = call_tokens(tool["name"], spec, wf.get("inputs") or {})
            rows.append({
                "doc": label, "wf": wf.get("workflowId", "?"), "steps": len(steps),
                "resolved": len(step_ops), "naive_menu": naive_menu, "wf_menu": wf_menu,
                "chain_b": chain_b, "wf_b": wf_b,
            })
            print(f"{label:12} {rows[-1]['wf'][:28]:28} steps={len(steps)} "
                  f"A {naive_menu}->{wf_menu}  B {chain_b}->{wf_b}")

    d = date.today().isoformat()
    lines = [
        "# Arazzo workflows as macro tools — the declared chain vs the ad-hoc chain",
        "",
        f"_Generated {d} by [`experiments/arazzo_score.py`](../experiments/arazzo_score.py); "
        f"tokenizer **{tokens.backend_name()}**. Corpus: the "
        "[Arazzo 1.0 specification's own example documents](https://github.com/OAI/Arazzo-Specification/tree/main/examples/1.0.0) "
        "(real third-party artifacts), workflows resolved against their paired OpenAPI "
        "descriptions. B estimates are the same structural lower bounds `lap score` uses "
        "(required-only args in a minimal tool-use envelope)._",
        "",
        "**The idea.** An [Arazzo](https://github.com/OAI/Arazzo-Specification) document "
        "declares a multi-step workflow — steps, data flow, success criteria — that an "
        "executor can run server-side. To an agent that's a **macro tool**: advertise the "
        "workflow's id + summary + `inputs` schema as ONE tool instead of asking the model "
        "to plan the chain against the full API menu.",
        "",
        "| doc | workflow | steps | menu: naive API → workflow-tool | call(s): ad-hoc chain → one call |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for r in rows:
        note = "" if r["resolved"] == r["steps"] else f" ({r['resolved']}/{r['steps']} resolved)"
        lines.append(
            f"| {r['doc']} | `{r['wf']}`{note} | {r['steps']} | "
            f"{r['naive_menu']:,} → **{r['wf_menu']:,}** | {r['chain_b']:,} → **{r['wf_b']:,}** |")
    a_saves = [1 - r["wf_menu"] / r["naive_menu"] for r in rows]
    b_deltas = [(r, 1 - r["wf_b"] / r["chain_b"]) for r in rows if r["chain_b"]]
    b_wins = [x for x in b_deltas if x[1] > 0]
    b_losses = [x for x in b_deltas if x[1] <= 0]
    best = max(b_deltas, key=lambda x: x[1])[0]
    lines += [
        "",
        f"**Read.** Across {len(rows)} example workflows the workflow-as-tool menu costs "
        f"**{min(a_saves):.0%}–{max(a_saves):.0%} less** than the naive menu of the underlying "
        f"API (bucket A). Bucket B splits by chain size — **the win grows with the chain**: "
        f"the {best['steps']}-step `{best['wf']}` drops {best['chain_b']} → {best['wf_b']} "
        f"tokens per invocation, while {len(b_losses)} of {len(b_deltas)} tiny flows actually "
        "pay *more* (a workflow's `inputs` schema can exceed the one or two small calls it "
        "replaces — the same below-threshold shape we measured for tool_search under ~10 "
        "tools and for schema dedupe on thin params). And the biggest effect doesn't show in "
        "A/B accounting at all: **the intermediate step results never enter the model's "
        "context** (each ad-hoc step's bucket-C response would have; the executor consumes "
        "them server-side). That's a *structural* saving — the same server-enforced property "
        "that made Tool Search hold up in our live tests ([TOOL-SEARCH](TOOL-SEARCH.md)) "
        "where behavioral savings didn't ([CODE-EXEC](CODE-EXEC.md)).",
        "",
        "**Honest caveats.** (1) These are the spec's own examples — small APIs; on a "
        "leaderboard-scale API the menu gap widens mechanically, but nobody ships Arazzo "
        "documents for those yet (adoption is the bottleneck, as with every declared "
        "artifact). (2) A macro tool trades *flexibility* for cost: the model can't deviate "
        "mid-chain — right for stable business flows, wrong for exploration (the same "
        "category-shaped trade our matrix found for query DSLs, X1). (3) The executor is "
        "real infrastructure someone must run; Arazzo runners exist but are young. "
        "(4) B savings assume required-only inputs, as everywhere in `lap score`.",
        "",
        "**Where this could go**: an `x-lap-workflow` pointer from an OpenAPI description to "
        "its Arazzo document would let `lap score` report the macro-tool figure next to the "
        "menu figures automatically — see the [x-lap strawman](X-LAP.md).",
    ]
    out = REPO / "docs" / "ARAZZO.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {out}  ({len(rows)} workflows)")


if __name__ == "__main__":
    main()
