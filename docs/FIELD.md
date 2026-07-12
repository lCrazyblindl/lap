# State of the field — who measures (and who optimizes) agent-API token cost

_Compiled 2026-07-07 from public sources (linked inline) + our own measurements. This is the
positioning document behind LAP: what exists, what each thing actually does, and which public
headline numbers we could and couldn't verify. Corrections welcome — file an issue._

## TL;DR

Token/context bloat went mainstream in 2026 — [enterprise write-ups](https://agentmarketcap.ai/blog/2026/04/08/mcp-context-bloat-enterprise-scale-tool-definitions-agent-context-budget)
call it a deployment blocker, and the MCP spec itself has an open issue
([#2808](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2808)) about
tool-schema overhead. The field splits into **optimizers** (vendors shipping fixes, each
publishing its own incomparable percentage) and **evaluators** (benchmarks measuring agent
*accuracy*, not interface *cost*). As of this writing, **no other neutral open-source tool
decomposes and scores the token cost of an agent-facing interface** — a
[StackOne survey](https://www.stackone.com/blog/mcp-token-optimization/) of the four
optimization approaches cites only vendor-published numbers and names no independent
measurement tooling. That gap is what LAP fills.

## Measurement & linting tools

| tool | what it does | inputs | token model | maturity |
| --- | --- | --- | --- | --- |
| **lap** (this repo) | A/B/C token decomposition, 4 menu forms + real-MCP baseline, lint (7 OpenAPI rules + 4 MCP M-rules), composite grade + badge, `--diff` CI gate, [50-API leaderboard](LEADERBOARD.md), `lap stack` for your installed config | OpenAPI (file/URL), live MCP (HTTP + stdio), agent configs | tiktoken approx or faithful Anthropic `count_tokens` | released ([PyPI 0.4.0](https://pypi.org/project/lap-score/0.4.0/)), 49 tests, fuzz-checked on 175+ real specs |
| [mcpx](https://github.com/sameenchand/mcpx) | A–F schema-quality grade, flags missing descriptions + token bloat | live MCP over HTTP only | token estimate (tokenizer undisclosed) | early (~2 stars, 14 commits) |
| [AgentDX](https://news.ycombinator.com/item?id=47062753) | 18 static lint rules + an LLM-judged bench (tool selection, parameter correctness) → DX score 0–100 | MCP servers | n/a (LLM-judged, needs API keys for bench) | early alpha (Show HN 2026) |
| [agent-friend](https://github.com/0-co/agent-friend) | 156 static checks → A+–F grade (40% correctness / 30% efficiency / 30% quality), auto-fix (6 rules), pre-commit hook, REST grading API; published grades for [201 servers](https://dev.to/0coceo/i-graded-201-mcp-servers-the-most-popular-ones-are-the-worst-114i) (2026-03) | MCP servers only (static schema analysis; no live calls, no OpenAPI, no result sizes) | multiple tokenizers reported per schema | early (~4 stars); its grades cross-checked against ours in [MCP-LEADERBOARD.md](MCP-LEADERBOARD.md) |
| [MCP Inspector](https://github.com/modelcontextprotocol/inspector) (official) | visual/protocol testing of MCP servers | live MCP | none | active, no token focus |
| [mcp-scan](https://stytch.com/blog/mcp-scan/) / [Proximity](https://www.helpnetsecurity.com/2025/10/29/proximity-open-source-mcp-security-scanner/) / [APIsec audit](https://apisec-inc.github.io/mcp-audit/) | **security** scanners (tool poisoning, secrets, risk flags) | installed/live MCP | none | active |

**Benchmarks** — [MCPMark](https://mcpmark.ai/) (127 verifiable tasks),
[MCP-Bench](https://github.com/Accenture/mcp-bench) (Accenture; 250 tools / 28 servers),
[MCP-Atlas](https://labs.scale.com/leaderboard/mcp_atlas) (Scale) — all measure **task
accuracy/capability** of models+agents. None decompose what the *interface itself* costs in
tokens; they're complementary to LAP (their accuracy × our cost would be the full picture —
that bridge is on our roadmap, Track V).

**What they have that lap doesn't** (honesty cuts both ways): AgentDX's LLM-judged
tool-*selection* accuracy is a real dimension our static lint can't see; agent-friend's rule
set is an order of magnitude larger than our M-rules (156 checks vs ~12), and it ships an
MCP-side auto-fix, a pre-commit hook, and a hosted grading API we don't; the security scanners
cover threats we deliberately don't; the big benchmarks have task suites and leaderboard
infrastructure far beyond ours.

## Optimizers (we measure them; they publish their own numbers)

| mechanism | vendor(s) | the published claim | our independent result |
| --- | --- | --- | --- |
| Tool search / lazy loading | [Anthropic Tool Search](https://mcp.directory/blog/mcp-context-bloat-fix-2026-tool-search-code-mode-progressive-disclosure) (GA 02-2026) | ~85% token reduction | **✅ verified live**: ~90% billed saving at 290 real ops ([TOOL-SEARCH.md](TOOL-SEARCH.md)); **and** verified *negative* below ~10 tools — both directions on real APIs |
| Code execution / "Code Mode" | [Anthropic](https://www.anthropic.com/engineering/code-execution-with-mcp), [Cloudflare](https://blog.cloudflare.com/code-mode-mcp/), [Bifrost](https://www.getmaxim.ai/bifrost/blog/code-mode-and-the-architecture-of-token-efficient-mcp-agentscode-mode), StackOne | 98.7% (150k→2k); "entire API in ~1000 tokens"; 92.8% at 508 tools | **⚠ disputed on one axis**: the *menu* saving is real (our `tool_search` form measures +82–95% on the same pattern), but the *end-to-end* saving is **behavioral** — Anthropic's real code execution cost **more** than naive in 5/5 live repeats on a small task ([CODE-EXEC.md](CODE-EXEC.md)) |
| Schema compression proxy | [mcp-compressor](MCP-COMPRESSOR.md) (Atlassian) | 23.7–103.8% self-reported (level/scale-dependent) | **⚠ discrepancy root-caused (v0.7 V1)**: its banner counts *characters, not tokens*, with an asymmetric formula (original side undercounted) — on a 2-tool server it prints a >100% "loss" where the served frontend is actually smaller by any symmetric measure (−12% tokens); scale effect itself confirmed (+67% on a 12-tool server) |
| Dynamic toolsets | [Speakeasy](https://www.stackone.com/blog/mcp-token-optimization/) | 400k+ → ~6k tokens | 🔒 hosted product, not reproducible without an account |
| Response filtering | StackOne et al. | ~95% per call | ≈ plausible, mechanism matches our R1/A1 measurements (5–19 vs ~1161 tokens on aggregates); scoring projection affordances is roadmap Track M |

## Claims registry

Every widely-quoted number, with a status: **✅ verified-by-us** (independent measurement in
this repo) · **≈ plausible-unverified** (mechanism consistent with our data, number itself not
reproduced) · **🔒 not-reproducible-without-account** · **⚠ disputed** (our measurement
disagrees).

| claim | source | status |
| --- | --- | --- |
| Tool Search saves ~85% | Anthropic / [MCP.Directory](https://mcp.directory/blog/mcp-context-bloat-fix-2026-tool-search-code-mode-progressive-disclosure) | ✅ we measured ~90% live at scale — *and* it's server-enforced (structural), unlike code-exec ([TOOL-SEARCH.md](TOOL-SEARCH.md)) |
| Not worth it under ~10 tools | Anthropic guidance | ✅ verified twice: live Petstore (19 ops, cost *more* than compact) and 1–3-op leaderboard APIs (negative savings) |
| Code execution: 150 000 → 2 000 tokens (−98.7%) | [Anthropic engineering blog](https://www.anthropic.com/engineering/code-execution-with-mcp) | ⚠ workload-specific: on our small live task the same real feature was **heavier than naive, 5/5 repeats** — the saving is behavioral, not guaranteed ([CODE-EXEC.md](CODE-EXEC.md)) |
| "Entire API in ~1000 tokens" (−99.9% input) | [Cloudflare Code Mode](https://blog.cloudflare.com/code-mode-mcp/) | ≈→✅ menu-side confirmed on a real server (gcore PR#13 facade: 741 tools → 3 / 363 tok) **and now behaviorally too**: our live A/B on that facade measured **8.1× less billed input at equal 15/15 accuracy** on discovery tasks ([FACADE-AB.md](FACADE-AB.md)) — the first code-mode variant that held up live (contrast the Anthropic-hosted one above) |
| 92.8% cut at 508 tools, zero accuracy loss | [Bifrost benchmark](https://www.getmaxim.ai/bifrost/blog/code-mode-and-the-architecture-of-token-efficient-mcp-agentscode-mode) | ≈/🔒 pattern-consistent, needs their gateway to reproduce |
| GitHub MCP server ≈ 17.6k tokens of definitions | community measurements | ⚠ **stale — we scored the hosted server directly** (2026-07-09): **44 tools / 11,461 tokens, grade B (76)** — the server slimmed down since the number started circulating ([MCP-VS-CLI.md](MCP-VS-CLI.md)) |
| MCP uses **35× more tokens than CLI**; reliability drops to 72% | [MindStudio](https://www.mindstudio.ai/blog/mcp-servers-35x-more-tokens-cli-tools-reliability-benchmark) (no methodology) ← [scalekit benchmark](https://github.com/scalekit-inc/mcp-vs-cli-benchmark) (reproducible; 15–80× per task, single-run headlines) | ≈ **magnitude real for a *naive* client, structurally reproduced** ([MCP-VS-CLI.md](MCP-VS-CLI.md)): the GitHub-MCP menu re-sent per turn alone reaches 27× the gh-help cost by 8 turns — but it collapses under Tool Search (default in Claude Code; our live −90%) or a compact menu, and the CLI side rides a training-data subsidy (`gh` costs ~0 because models know it; *your* API's CLI wouldn't). The 72% reliability figure is unverifiable as published |
| 100–200k tokens loaded before the first prompt (5–10 servers) | [AgentMarketCap](https://agentmarketcap.ai/blog/2026/04/08/mcp-context-bloat-enterprise-scale-tool-definitions-agent-context-budget) | ✅ mechanism verified — `lap stack` reproduces the per-server menu tax on *your* config (our 2-reference-server demo: 1 701 tokens; heavy servers multiply it) |
| Schemas cost 5–15× a minimal rendering; tiered schemas would save 60–70% | [MCP spec issue #2808](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2808) | ✅ **simulated over 51 real APIs** ([SPEC-2808.md](SPEC-2808.md)): discovery tier saves mean 85% (the 60–70% estimate is conservative); dedupe is 23% mean but ranges −10…94% — pays only on fat repeated schemas |
| mcp-compressor self-reported percentages | its startup banner | ✅ **was mismeasured — FIXED upstream after our report, verified** (the referee loop closed end-to-end in ~a day): root-caused from `banner.rs` (character counts, asymmetric formula), reported as [#236](https://github.com/atlassian-labs/mcp-compressor/issues/236) → maintainers merged [PR #237](https://github.com/atlassian-labs/mcp-compressor/pull/237) within 3 hours, released 0.31.5 same evening; our re-run confirms the banner is now symmetric (git@medium: banner 41.9% vs our 41.0% chars; the small-server sign flip is gone) ([MCP-COMPRESSOR.md](MCP-COMPRESSOR.md)) |
| 4 approaches, 70–99% each | [StackOne comparison](https://www.stackone.com/blog/mcp-token-optimization/) | ≈ directionally consistent with everything above; the article itself names **no independent measurement tooling** — this repo is that |

## Where LAP sits

Nobody else in this table does **neutral, reproducible token-cost decomposition** across both
OpenAPI and MCP, publishes a comparable **cross-API dataset** ([LEADERBOARD.md](LEADERBOARD.md)),
and **live-verifies vendor claims with billed calls** — including the two cases above where
verification *disagreed* with the vendor's own number. That last part is the point: an
ecosystem where every efficiency number comes from the vendor selling the mechanism needs a
referee. LAP is built to be that referee, and shows its work.
