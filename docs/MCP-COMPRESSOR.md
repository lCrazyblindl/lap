# Real `mcp-compressor` (Atlassian) head-to-head — a third real compression mechanism (v0.5 S2)

_By [`experiments/mcp_compressor_real.py`](../experiments/mcp_compressor_real.py), 2026-07-02._

**What this is.** [`mcp-compressor`](https://github.com/atlassian-labs/mcp-compressor) (PyPI `mcp-compressor`, Rust-backed) is a real, published **stdio proxy**: it spawns a backend MCP server as a subprocess and re-exposes a *compressed* frontend at one of four levels (low/medium/high/max) — a real third-party optimizer, identified in R1's inventory (`docs/REAL-TOOLS.md`) but never tested until now. This is a third real data point on "structural vs behavioral" savings, alongside Anthropic's real Tool Search (R5, structural, `docs/TOOL-SEARCH.md`) and real code-execution (v0.5 S1, behavioral, `docs/CODE-EXEC.md`) — here the mechanism is a real third-party MCP proxy, not an Anthropic-hosted feature.

**Mechanism observed.** At default settings the compressor collapses the entire backend toolset into a **generic 2-tool proxy** — `server_get_tool_schema` (whose *description* embeds a compact `<tool>name(args): desc</tool>` line for every backend tool — a progressive-disclosure menu, structurally similar in spirit to lazy/`tool_search` designs) and `server_invoke_tool` (dispatches by name). At `max` compression a third tool, `server_list_tools`, appears — the compact menu is no longer embedded in a description, so an explicit list call is needed instead.

- tokenizer: **tiktoken-approx** _(relative ranking is the signal)_. Two servers from R3 (`docs/MCP-SERVERS.md`), at increasing scale: `mcp-server-time` (2 tools, small) and `mcp-server-git` (12 tools, mid-size).

## Result

### mcp-server-time (2 raw tools, 283 tokens advertised)

| compression | proxy tools | real bucket-A tokens (ours) | saved vs raw (ours) | vendor's own reported % of original |
| --- | ---: | ---: | ---: | ---: |
| `low` | 2 | 250 | +12% | 103.8% |
| `medium` | 2 | 250 | +12% | 103.8% |
| `high` | 2 | 236 | +17% | 94.6% |
| `max` | 3 | 259 | +8% | 93.6% |

### mcp-server-git (12 raw tools, 1418 tokens advertised)

| compression | proxy tools | real bucket-A tokens (ours) | saved vs raw (ours) | vendor's own reported % of original |
| --- | ---: | ---: | ---: | ---: |
| `low` | 2 | 473 | +67% | 54.5% |
| `medium` | 2 | 473 | +67% | 54.5% |
| `high` | 2 | 389 | +73% | 40.7% |
| `max` | 3 | 354 | +75% | 23.7% |

**Read.** Scale amplifies the win, and — surprisingly — **our own tokenizer disagrees with the tool's own self-reported percentage** on the small server. On `mcp-server-time` (283 raw tokens), the vendor's own startup banner reports its *default* `medium` setting at **103.8% of original — worse, not better**; but our own bucket-A token count of that exact same `medium`-compressed frontend says **250 tokens, +12% saved** — a real, if modest, reduction, not a regression. Every level we measured came out ahead by our tokenizer (low/medium 12%, high 17%, max 8% — max costs more than high because it drops the embedded compact menu and adds a third tool, `server_list_tools`, to fetch it separately). We can't fully explain the vendor number's direction from the outside — it likely counts something other than our bucket-A tokenizer (e.g. raw bytes, or protocol overhead) — but it's a genuine, reproducible discrepancy between a real third-party tool's own self-report and an independent measurement, worth flagging rather than smoothing over. On `mcp-server-git` (1418 raw tokens) both measurements agree on direction and both show a much bigger win: vendor 54.5% of original at `medium`, ours +67% saved (473 tokens); `max` does better still on both. **The scale effect is real and reproducible** (a bigger menu compresses more, on a real third-party tool, independent of Anthropic and independent of our own variants) — but unlike Tool Search/code-execution, we can't cleanly confirm a strict "actively harmful below ~10 tools" cutoff here, because on this specific small server our own numbers show a small real win where the vendor's own claims a loss. Caveats: two servers, one run each (no repeats — this is a static menu-cost measurement like R2/R3, not a live/billed comparison); default settings and levels only, no attempt to tune the compressor's own configuration further.
