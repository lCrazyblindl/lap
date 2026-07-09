"""v0.8 P3 — referee round 2: the "MCP uses 35x more tokens than CLI" claim.

The claim's family tree: a widely-recirculated number (MindStudio and others cite it
with NO methodology) whose one reproducible artifact is scalekit-inc/mcp-vs-cli-benchmark
(gh CLI vs the official GitHub MCP server, Claude Sonnet 4, 5 tasks, published code +
raw results; per-task headline ratios 15-80x, from single runs). This script measures
the *structural* component of that gap with our own ruler, on the same pair of real
artifacts:

- the **hosted official GitHub MCP server** (https://api.githubcopilot.com/mcp/),
  authenticated with `gh auth token`, tool list fetched live and scored like
  `lap lint --mcp` (this is also the long-cited server we could never score before -
  Docker daemon down; the hosted endpoint finally closes that gap);
- the **`gh` CLI's own help surface** - the top-level `gh --help` plus the subcommand
  helps an agent would plausibly read for the benchmark's task family (repo / pr /
  release / api) - i.e. the *most generous* CLI-side "menu" (in practice models know
  `gh` from training and read ~none of it).

Writes docs/MCP-VS-CLI.md. Needs: gh CLI authenticated; fastmcp. The token from
`gh auth token` is used in-process for the Authorization header and never printed.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lap import grade, lint, mcp_client, tokens  # noqa: E402

MCP_URL = "https://api.githubcopilot.com/mcp/"
HELP_CMDS = [["gh", "--help"], ["gh", "repo", "--help"], ["gh", "pr", "--help"],
             ["gh", "release", "--help"], ["gh", "api", "--help"]]
TURNS = [1, 3, 8]  # assistant turns in a session; the naive menu is re-sent each turn
TOOL_SEARCH_CUT = 0.90  # our own live, billed measurement of defer_loading (docs/TOOL-SEARCH.md, R5)


def gh_help_tokens() -> list[tuple[str, int]]:
    out = []
    for cmd in HELP_CMDS:
        text = subprocess.run(cmd, capture_output=True, text=True).stdout
        out.append((" ".join(cmd), tokens.count(text)))
    return out


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    tok = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    if not tok:
        sys.exit("gh auth token is empty - authenticate gh first")
    from fastmcp.client.transports import StreamableHttpTransport

    transport = StreamableHttpTransport(MCP_URL, headers={"Authorization": f"Bearer {tok}"})
    tools = mcp_client.fetch_tools(transport, timeout=60)
    s = mcp_client.score_tools(tools)
    menu, compact = s["menu"]["mcp_live"], s["menu"]["compact_sig"]
    found = lint.lint_tools(tools)
    warns = sum(1 for f in found if f.severity == "warn")
    g = grade.compute_parts(len(tools), menu, 0, warns, len(found) - warns)
    heavy = max(tools, key=lambda t: tokens.count_tools([t]))
    print(f"GitHub MCP (hosted): {len(tools)} tools, menu {menu}, compact {compact}, "
          f"grade {g['letter']} ({g['score']})")

    helps = gh_help_tokens()
    cli_menu = sum(n for _, n in helps)
    for name, n in helps:
        print(f"  {name:18} {n:5} tok")

    lines = [
        "# Referee: the \"MCP uses 35x more tokens than CLI\" claim",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/mcp_vs_cli.py`](../experiments/mcp_vs_cli.py); tokenizer: "
        f"**{tokens.backend_name()}**. Live fetch of the hosted official GitHub MCP server's "
        "tool list (authenticated with the local `gh` token); `gh` help texts tokenized "
        "locally._",
        "",
        "## The claim and its family tree",
        "",
        "\"MCP servers use **35x more tokens** than CLI tools - and reliability drops to "
        "**72%** on hard tasks\" circulates widely (e.g. "
        "[MindStudio](https://www.mindstudio.ai/blog/mcp-servers-35x-more-tokens-cli-tools-reliability-benchmark), "
        "which cites *someone ran the same agentic task...* with no methodology, servers, "
        "model, tasks, or data). The one **reproducible** artifact in the family is "
        "[scalekit-inc/mcp-vs-cli-benchmark](https://github.com/scalekit-inc/mcp-vs-cli-benchmark) "
        "(gh CLI vs the official GitHub MCP server, Claude Sonnet 4, 5 tasks, code + raw "
        "results published): per-task ratios **15-80x**, with the stated caveat that headline "
        "numbers come from single runs. The \"35x\" meme number is a mid-range anecdote from "
        "this family, not a stable constant.",
        "",
        "## What we measured (the structural component)",
        "",
        f"**The hosted official GitHub MCP server advertises {len(tools)} tools costing "
        f"{menu:,} tokens** (grade **{g['letter']} ({g['score']})**; heaviest tool "
        f"`{heavy['name']}` at {tokens.count_tools([heavy])} tokens; {warns} warn / "
        f"{len(found) - warns} info lint findings). The widely-cited \"~94 tools / ~17.6k "
        "tokens\" is stale - the server has slimmed down, but it still charges "
        f"~{menu // 1000}k tokens per session. A compact rendering of the same tools: "
        f"{compact:,} tokens.",
        "",
        "The `gh` CLI's *entire* plausible help surface for the benchmark's task family "
        f"costs **{cli_menu:,} tokens - read at most once**, not per turn (and in practice "
        "~zero: models know `gh` from training):",
        "",
        "| help text | tokens |",
        "| --- | ---: |",
    ]
    lines += [f"| `{name}` | {n} |" for name, n in helps]
    naive_rows = []
    for t in TURNS:
        mcp_cost = menu * t
        search_cost = round(menu * (1 - TOOL_SEARCH_CUT)) * t
        compact_cost = compact * t
        naive_rows.append((t, mcp_cost, compact_cost, search_cost,
                           round(mcp_cost / cli_menu, 1)))
    lines += [
        "",
        "## The menu component alone reproduces the gap's magnitude",
        "",
        "An agent loop re-sends the tool definitions with **every** assistant turn "
        "(uncached; caching discounts price, not context - "
        "[CACHE-ECONOMICS](CACHE-ECONOMICS.md)). The CLI pays its help text once. Menu "
        "component only - before any call/result differences:",
        "",
        "| assistant turns | naive MCP menu | compact menu | deferred (Tool Search) | naive-MCP : CLI-help ratio |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for t, m, c, sch, ratio in naive_rows:
        lines.append(f"| {t} | {m:,} | {c:,} | {sch:,} | {ratio}x |")
    lines += [
        "",
        f"_Deferred column = our own live, billed Tool Search measurement (~{int(TOOL_SEARCH_CUT * 100)}% "
        "cut, server-enforced - [TOOL-SEARCH](TOOL-SEARCH.md))._",
        "",
        "## Referee verdict",
        "",
        "- **The magnitude is real for a naive client.** The menu tax alone reaches the "
        "benchmark family's 15-80x range within a handful of turns; scalekit's own "
        "attribution (\"schema overhead included in every request\") matches what we measure. "
        "Add MCP's verbose JSON results vs the CLI's terse text and the per-task ratios are "
        "entirely believable.",
        "- **But it's a naive-client number, and naive is no longer the default.** Claude "
        "Code 2.1.x defers MCP tool definitions via Tool Search by default; our live "
        "measurement of that mechanism cut billed input ~90% (server-enforced). Under "
        "deferral or a compact rendering the \"35x\" collapses to low single digits - the "
        "comparison is *client-configuration-dependent*, not a property of the protocol.",
        "- **The CLI side rides on a training-data subsidy.** `gh` costs ~0 menu tokens "
        "because models already know it. A CLI for *your* API gets no such subsidy - the "
        "agent reads your `--help` (or guesses). The fair comparison for a custom API is "
        "compact/deferred MCP vs an unknown CLI, and that gap is far smaller than 35x.",
        "- **The reliability number (72%) is unverifiable as published.** MindStudio cites "
        "no tasks, model, or runs; scalekit publishes code but flags its headline numbers "
        "as single-run. Not disputed - just unproven at the advertised generality. (Our own "
        "500-run matrix found form-related accuracy differences are model-dependent and "
        "small when descriptions are kept.)",
        "",
        f"_Registry entry: [FIELD.md](FIELD.md). Also new here: the official GitHub MCP "
        f"server finally scored ({len(tools)} tools / {menu:,} tokens / {g['letter']}) - "
        "cited since R3, unmeasurable until the hosted endpoint._",
    ]
    out = REPO / "docs" / "MCP-VS-CLI.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {out}")


if __name__ == "__main__":
    main()
