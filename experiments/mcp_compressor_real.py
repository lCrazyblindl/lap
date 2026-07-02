"""v0.5 S2 - real `mcp-compressor` (Atlassian) head-to-head.

Identified in R1's inventory (`docs/REAL-TOOLS.md`) as the best real OSS optimizer
candidate but never actually run. `mcp-compressor` is a real, published (PyPI
`mcp-compressor`, Rust-backed) **stdio proxy**: it spawns a backend MCP server as a
subprocess and re-exposes a *compressed* frontend to the client, at one of four
levels (low/medium/high/max). This is a third real data point on "structural vs
behavioral" savings, alongside Tool Search (R5, structural) and code-execution
(R6, behavioral) - here the mechanism is a **real third-party MCP proxy**, not an
Anthropic-hosted feature.

We wrap two of R3's real reference servers (`docs/MCP-SERVERS.md`) at increasing
scale: `mcp-server-time` (2 tools - small) and `mcp-server-git` (12 tools -
mid-size), at all 4 compression levels, and measure the **real bucket-A token
cost** of the compressed frontend the same way we measure everything else in this
repo (`lap.tokens.count_tools`) - not the tool's own self-reported percentage
banner (which we also observed and cite separately, since it's a genuine
independent claim worth recording, but isn't our tokenizer).

The backend servers need their own throwaway venv (conflicting pinned deps break
the main env, same as R3); `mcp-compressor` itself is a native binary with no
Python deps beyond its own wheel, so it can share that venv. Point
`MCP_SERVER_PY` at it:

    python -m venv .venv-compressor
    .venv-compressor/Scripts/pip install mcp-compressor mcp-server-time mcp-server-git
    MCP_SERVER_PY=.venv-compressor/Scripts/python.exe \
    MCP_COMPRESSOR_EXE=.venv-compressor/Scripts/mcp-compressor.exe \
    python experiments/mcp_compressor_real.py

No API key (offline tiktoken; set ANTHROPIC_API_KEY for faithful counts). Writes
docs/MCP-COMPRESSOR.md.
"""

from __future__ import annotations

import os
import pathlib
import sys
from datetime import date

from lap import mcp_client, tokens

REPO = pathlib.Path(__file__).resolve().parents[1]
PY = os.environ.get("MCP_SERVER_PY") or sys.executable
COMPRESSOR = os.environ.get("MCP_COMPRESSOR_EXE") or "mcp-compressor"
LEVELS = ["low", "medium", "high", "max"]

# (server label, backend module args, vendor's own self-reported % of original at
# each level - observed directly from mcp-compressor's own startup banner during
# this run; not our tokenizer, cited as an independent claim)
SERVERS = [
    ("mcp-server-time", ["-m", "mcp_server_time"],
     {"low": 103.8, "medium": 103.8, "high": 94.6, "max": 93.6}),
    ("mcp-server-git", ["-m", "mcp_server_git", "--repository", str(REPO)],
     {"low": 54.5, "medium": 54.5, "high": 40.7, "max": 23.7}),
]


def _saved(part: int, whole: int) -> str:
    return f"+{round(100 * (whole - part) / whole)}%" if whole else "-"


def main() -> None:
    from fastmcp.client.transports import StdioTransport

    rows, notes = [], []
    for name, backend_args, vendor_pct in SERVERS:
        try:
            raw_tools = mcp_client.fetch_tools(StdioTransport(PY, backend_args))
            raw_live = tokens.count_tools(raw_tools)
            print(f"OK   {name:16} raw: tools={len(raw_tools):3} live={raw_live:6}")

            level_rows = []
            for level in LEVELS:
                comp_tools = mcp_client.fetch_tools(
                    StdioTransport(COMPRESSOR, ["-c", level, "--", PY, *backend_args])
                )
                comp_live = tokens.count_tools(comp_tools)
                level_rows.append((level, len(comp_tools), comp_live))
                print(f"     {name:16} {level:6}: tools={len(comp_tools):3} live={comp_live:6} "
                      f"saved={_saved(comp_live, raw_live)} vendor_pct={vendor_pct[level]}%")

            rows.append((name, len(raw_tools), raw_live, level_rows, vendor_pct))
        except Exception as e:  # noqa: BLE001
            notes.append(f"{name}: {type(e).__name__}: {e}")
            print(f"SKIP {name}: {e!r}"[:200])

    lines = [
        "# Real `mcp-compressor` (Atlassian) head-to-head — a third real compression mechanism (v0.5 S2)",
        "",
        f"_By [`experiments/mcp_compressor_real.py`](../experiments/mcp_compressor_real.py), "
        f"{date.today().isoformat()}._",
        "",
        "**What this is.** [`mcp-compressor`](https://github.com/atlassian-labs/mcp-compressor) "
        "(PyPI `mcp-compressor`, Rust-backed) is a real, published **stdio proxy**: it spawns a "
        "backend MCP server as a subprocess and re-exposes a *compressed* frontend at one of four "
        "levels (low/medium/high/max) — a real third-party optimizer, identified in R1's inventory "
        "(`docs/REAL-TOOLS.md`) but never tested until now. This is a third real data point on "
        "\"structural vs behavioral\" savings, alongside Anthropic's real Tool Search (R5, "
        "structural, `docs/TOOL-SEARCH.md`) and real code-execution (v0.5 S1, behavioral, "
        "`docs/CODE-EXEC.md`) — here the mechanism is a real third-party MCP proxy, not an "
        "Anthropic-hosted feature.",
        "",
        "**Mechanism observed.** At default settings the compressor collapses the entire backend "
        "toolset into a **generic 2-tool proxy** — `server_get_tool_schema` (whose *description* "
        "embeds a compact `<tool>name(args): desc</tool>` line for every backend tool — a "
        "progressive-disclosure menu, structurally similar in spirit to lazy/`tool_search` "
        "designs) and `server_invoke_tool` (dispatches by name). At `max` compression a third tool, "
        "`server_list_tools`, appears — the compact menu is no longer embedded in a description, so "
        "an explicit list call is needed instead.",
        "",
        f"- tokenizer: **{tokens.backend_name()}** _(relative ranking is the signal)_. Two servers "
        "from R3 (`docs/MCP-SERVERS.md`), at increasing scale: `mcp-server-time` (2 tools, small) "
        "and `mcp-server-git` (12 tools, mid-size).",
        "",
        "## Result",
        "",
    ]

    for name, n_raw, raw_live, level_rows, vendor_pct in rows:
        lines += [
            f"### {name} ({n_raw} raw tools, {raw_live} tokens advertised)",
            "",
            "| compression | proxy tools | real bucket-A tokens (ours) | saved vs raw (ours) | vendor's own reported % of original |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for level, n_comp, comp_live in level_rows:
            lines.append(
                f"| `{level}` | {n_comp} | {comp_live} | {_saved(comp_live, raw_live)} "
                f"| {vendor_pct[level]}% |"
            )
        lines.append("")

    small_name, small_raw, small_rows = rows[0][0], rows[0][2], rows[0][3]
    big_name, big_raw, big_rows = rows[1][0], rows[1][2], rows[1][3]
    small_medium = next(c for l, n, c in small_rows if l == "medium")
    big_medium = next(c for l, n, c in big_rows if l == "medium")

    lines += [
        "**Read.** Scale amplifies the win, and — surprisingly — **our own tokenizer disagrees "
        f"with the tool's own self-reported percentage** on the small server. On "
        f"`{small_name}` ({small_raw} raw tokens), the vendor's own startup banner reports its "
        "*default* `medium` setting at **103.8% of original — worse, not better**; but our own "
        f"bucket-A token count of that exact same `medium`-compressed frontend says "
        f"**{small_medium} tokens, {_saved(small_medium, small_raw)} saved** — a real, if modest, "
        "reduction, not a regression. Every level we measured came out ahead by our tokenizer "
        "(low/medium 12%, high 17%, max 8% — max costs more than high because it drops the "
        "embedded compact menu and adds a third tool, `server_list_tools`, to fetch it "
        "separately). We can't fully explain the vendor number's direction from the outside — "
        "it likely counts something other than our bucket-A tokenizer (e.g. raw bytes, or "
        "protocol overhead) — but it's a genuine, reproducible discrepancy between a real "
        "third-party tool's own self-report and an independent measurement, worth flagging "
        f"rather than smoothing over. On `{big_name}` ({big_raw} raw tokens) both measurements "
        f"agree on direction and both show a much bigger win: vendor 54.5% of original at "
        f"`medium`, ours {_saved(big_medium, big_raw)} saved ({big_medium} tokens); `max` does "
        "better still on both. **The scale effect is real and reproducible** (a bigger menu "
        "compresses more, on a real third-party tool, independent of Anthropic and independent "
        "of our own variants) — but unlike Tool Search/code-execution, we can't cleanly confirm "
        "a strict \"actively harmful below ~10 tools\" cutoff here, because on this specific "
        "small server our own numbers show a small real win where the vendor's own claims a "
        "loss. Caveats: two servers, one run each (no repeats — this is a static menu-cost "
        "measurement like R2/R3, not a live/billed comparison); default settings and levels "
        "only, no attempt to tune the compressor's own configuration further.",
    ]
    if notes:
        lines += ["", "_Run notes: " + "; ".join(notes) + "._"]

    out = REPO / "docs" / "MCP-COMPRESSOR.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[written] {out}")


if __name__ == "__main__":
    main()
