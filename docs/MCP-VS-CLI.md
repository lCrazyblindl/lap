# Referee: the "MCP uses 35x more tokens than CLI" claim

_Generated 2026-07-09 by [`experiments/mcp_vs_cli.py`](../experiments/mcp_vs_cli.py); tokenizer: **tiktoken-approx**. Live fetch of the hosted official GitHub MCP server's tool list (authenticated with the local `gh` token); `gh` help texts tokenized locally._

## The claim and its family tree

"MCP servers use **35x more tokens** than CLI tools - and reliability drops to **72%** on hard tasks" circulates widely (e.g. [MindStudio](https://www.mindstudio.ai/blog/mcp-servers-35x-more-tokens-cli-tools-reliability-benchmark), which cites *someone ran the same agentic task...* with no methodology, servers, model, tasks, or data). The one **reproducible** artifact in the family is [scalekit-inc/mcp-vs-cli-benchmark](https://github.com/scalekit-inc/mcp-vs-cli-benchmark) (gh CLI vs the official GitHub MCP server, Claude Sonnet 4, 5 tasks, code + raw results published): per-task ratios **15-80x**, with the stated caveat that headline numbers come from single runs. The "35x" meme number is a mid-range anecdote from this family, not a stable constant.

## What we measured (the structural component)

**The hosted official GitHub MCP server advertises 44 tools costing 11,461 tokens** (grade **B (76)**; heaviest tool `issue_write` at 738 tokens; 1 warn / 1 info lint findings). The widely-cited "~94 tools / ~17.6k tokens" is stale - the server has slimmed down, but it still charges ~11k tokens per session. A compact rendering of the same tools: 927 tokens.

The `gh` CLI's *entire* plausible help surface for the benchmark's task family costs **3,449 tokens - read at most once**, not per turn (and in practice ~zero: models know `gh` from training):

| help text | tokens |
| --- | ---: |
| `gh --help` | 595 |
| `gh repo --help` | 357 |
| `gh pr --help` | 429 |
| `gh release --help` | 232 |
| `gh api --help` | 1836 |

## The menu component alone reproduces the gap's magnitude

An agent loop re-sends the tool definitions with **every** assistant turn (uncached; caching discounts price, not context - [CACHE-ECONOMICS](CACHE-ECONOMICS.md)). The CLI pays its help text once. Menu component only - before any call/result differences:

| assistant turns | naive MCP menu | compact menu | deferred (Tool Search) | naive-MCP : CLI-help ratio |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 11,461 | 927 | 1,146 | 3.3x |
| 3 | 34,383 | 2,781 | 3,438 | 10.0x |
| 8 | 91,688 | 7,416 | 9,168 | 26.6x |

_Deferred column = our own live, billed Tool Search measurement (~90% cut, server-enforced - [TOOL-SEARCH](TOOL-SEARCH.md))._

## Referee verdict

- **The magnitude is real for a naive client.** The menu tax alone reaches the benchmark family's 15-80x range within a handful of turns; scalekit's own attribution ("schema overhead included in every request") matches what we measure. Add MCP's verbose JSON results vs the CLI's terse text and the per-task ratios are entirely believable.
- **But it's a naive-client number, and naive is no longer the default.** Claude Code 2.1.x defers MCP tool definitions via Tool Search by default; our live measurement of that mechanism cut billed input ~90% (server-enforced). Under deferral or a compact rendering the "35x" collapses to low single digits - the comparison is *client-configuration-dependent*, not a property of the protocol.
- **The CLI side rides on a training-data subsidy.** `gh` costs ~0 menu tokens because models already know it. A CLI for *your* API gets no such subsidy - the agent reads your `--help` (or guesses). The fair comparison for a custom API is compact/deferred MCP vs an unknown CLI, and that gap is far smaller than 35x.
- **The reliability number (72%) is unverifiable as published.** MindStudio cites no tasks, model, or runs; scalekit publishes code but flags its headline numbers as single-run. Not disputed - just unproven at the advertised generality. (Our own 500-run matrix found form-related accuracy differences are model-dependent and small when descriptions are kept.)

_Registry entry: [FIELD.md](FIELD.md). Also new here: the official GitHub MCP server finally scored (44 tools / 11,461 tokens / B) - cited since R3, unmeasurable until the hosted endpoint._
