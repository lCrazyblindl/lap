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

**Read.** Scale amplifies the win, and — surprisingly — **our own tokenizer disagrees with the tool's own self-reported percentage** on the small server. On `mcp-server-time` (283 raw tokens), the vendor's own startup banner reports its *default* `medium` setting at **103.8% of original — worse, not better**; but our own bucket-A token count of that exact same `medium`-compressed frontend says **250 tokens, +12% saved** — a real, if modest, reduction, not a regression. Every level we measured came out ahead by our tokenizer (low/medium 12%, high 17%, max 8% — max costs more than high because it drops the embedded compact menu and adds a third tool, `server_list_tools`, to fetch it separately). ~~We can't fully explain the vendor number's direction from the outside~~ — **root-caused in v0.7 V1, see the section below**: the banner counts *characters, not tokens*, and counts *different things* on each side of its own ratio. On `mcp-server-git` (1418 raw tokens) both measurements agree on direction and both show a much bigger win: vendor 54.5% of original at `medium`, ours +67% saved (473 tokens); `max` does better still on both. **The scale effect is real and reproducible** (a bigger menu compresses more, on a real third-party tool, independent of Anthropic and independent of our own variants) — but unlike Tool Search/code-execution, we can't cleanly confirm a strict "actively harmful below ~10 tools" cutoff here, because on this specific small server our own numbers show a small real win where the vendor's own claims a loss. Caveats: two servers, one run each (no repeats — this is a static menu-cost measurement like R2/R3, not a live/billed comparison); default settings and levels only, no attempt to tune the compressor's own configuration further.

## Root cause of the self-report discrepancy (v0.7 V1)

Read the banner's own source
([`crates/mcp-compressor-core/src/app/banner.rs`](https://github.com/atlassian-labs/mcp-compressor/blob/main/crates/mcp-compressor-core/src/app/banner.rs),
`compression_stats()` / `compressed_frontend_size()`) and replicated its formula in Python
([`experiments/mcp_compressor_rootcause.py`](../experiments/mcp_compressor_rootcause.py)).
Two independent causes, both confirmed:

1. **The banner measures characters (Rust `String::len()`), not tokens.** There is no
   tokenizer anywhere in the stats path — so the number can't be compared with token-based
   claims or budgets, even directionally on small inputs (BPE compresses prose-like compact
   menus better than JSON punctuation, which is much of why our token measurement is kinder
   to the compressed form than a character count is).
2. **The ratio's two sides count different things.** *Original* = per tool, only
   `name + description + the JSON of the "properties" sub-object` — the schema's `type`,
   `required` list and the whole tool-object scaffolding are **not counted**. *Compressed* =
   the proxy tools' full description strings **plus their entire wrapper schema JSONs**
   (though not their names). The original side is systematically undercounted, the compressed
   side fully counted.

On a 2-tool server the undercounting dominates: banner-formula original = **793 chars**
vs the compressed side's **885** → >100% "regression", while the *actually advertised* menus
measure raw 1026 vs compressed 1020 chars (−0.6%) and 283 vs 250 tokens (**−12%**) — i.e.
compression wins under any symmetric measurement, and the banner's ">100%" is an artifact of
the asymmetry, not a real cost. Our Python replication of their exact formula reproduces the
banner's direction and magnitude (111.6% vs the printed 103.8% on `mcp-server-time`; 56.5% vs
54.5% on `mcp-server-git` — residuals from small differences between the banner's internal
constants and the served frontend). At 12-tool scale the asymmetry washes out, which is why
both rulers agreed directionally on `mcp-server-git` in the table above.

**Takeaway for the field:** this is exactly why measurement shouldn't be bundled with the
thing it measures — a well-intentioned self-report can be off *in direction* on small inputs
without anyone noticing, because nobody re-measures. (It also means our S2 caveat "can't
confirm the below-10-tools cutoff here" resolves: by symmetric measures the compressor *does*
still win on the tiny server — its own banner was the only dissenter, and the banner is
mismeasuring.)

### Upstream outcome — reported, FIXED, and verified (2026-07-09/10)

The issue below was posted as
[atlassian-labs/mcp-compressor#236](https://github.com/atlassian-labs/mcp-compressor/issues/236)
on 2026-07-09. **A maintainer closed it "completed" within 3 hours**, with
[PR #237](https://github.com/atlassian-labs/mcp-compressor/pull/237) — *"Fix asymmetric
compression statistics in startup banner"*, refactored to "reuse actual wrapper tool
constructors" (i.e. both sides of the ratio now come from the same serialization of the
actually-advertised tool lists, exactly the suggested fix) — **released as 0.31.5 the same
evening** (13 minutes after the merge).

**Verified against the released 0.31.5** (same rig as the root-cause run:
`experiments/mcp_compressor_rootcause.py`, both reference servers):

| server @ `medium` | banner before | banner now (0.31.5) | our symmetric measures |
| --- | ---: | ---: | --- |
| mcp-server-time (2 tools) | **103.8%** ("costs more") | **90.8%** | 88.3% tokens · 99.4% chars |
| mcp-server-git (12 tools) | 54.5% | **41.9%** | **41.0% chars** · 33.4% tokens |

The sign flip on the small server is gone, and at 12-tool scale the new banner matches our
symmetric character measurement almost exactly (41.9% vs 41.0%) — while our replication of
the *old* asymmetric formula still predicts 111.6%/56.5%, confirming the shipped banner no
longer uses it. Remaining honest note: the banner still measures **characters, not tokens**
(our secondary suggestion) — fine for a startup banner, but don't compare it against token
budgets.

_This is the project's referee loop closing end-to-end for the first time: independent
measurement → root cause in the vendor's own source → upstream report → merged fix →
re-verification of the shipped release. Total elapsed: about a day._

### The issue as posted (2026-07-09)

> **Startup banner's compression percentages are character-based and asymmetric — can report
> ">100%" where the served frontend is actually smaller**
>
> `compression_stats()` in `crates/mcp-compressor-core/src/app/banner.rs` compares:
> - *original*: per tool, `name.len() + description.len() + to_string(schema["properties"]).len()`
>   — omitting `type`, `required`, and the tool-object structure;
> - *compressed*: the proxy tools' full descriptions + their **entire** wrapper schema JSONs.
>
> On small backends the asymmetry flips the sign: for `mcp-server-time` (2 tools) the banner
> prints **103.8%** ("compression costs more"), but measuring the *actually advertised* menus
> symmetrically gives raw 1026 vs compressed 1020 chars (−0.6%), and 283 vs 250 tokens (−12%,
> tiktoken) — the compressed frontend is genuinely smaller. Python replication of the current
> formula and full methodology: <link to this doc>.
>
> Suggested fix: compute both sides from the same serialization of the actually-advertised
> tool lists (and consider reporting estimated *tokens*, since that's the budget users care
> about). Happy to contribute the fix or the measurement harness.
