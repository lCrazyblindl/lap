# Upstream issues — prepared, measured, awaiting the owner's go-ahead

_Generated 2026-07-11 by [`experiments/upstream_issues.py`](../experiments/upstream_issues.py); tokenizer **tiktoken-approx**; servers fetched live via `npx -y` (versions = registry latest on the scan date). **None of these has been posted** — the owner reviews and authorizes each one individually. The motion is the one that already converted: [mcp-compressor #236 → fixed & shipped in a day](MCP-COMPRESSOR.md)._

| target | repo | today | measured what-if | saving |
| --- | --- | ---: | ---: | ---: |
| sequential-thinking | modelcontextprotocol/servers | 921 tok | 463 tok | 50% |
| firecrawl-mcp | firecrawl/firecrawl-mcp-server | 18,511 tok | 9,218 tok | 50% |
| notion-mcp-server | makenotion/notion-mcp-server | 21,411 tok | ~6,600 tok | ~69% (dedupe alone) |
| gcore-mcp-server (`GCORE_TOOLS=*`) | G-Core/gcore-mcp-server | 488,013 tok | ~367,205 tok | ~25% (dedupe alone) |

---

## 1. modelcontextprotocol/servers — `sequentialthinking`

**Evidence.** One tool, **921 tokens** per session (566 description + 320 schema). All 9 parameters already carry `description`s in the inputSchema — yet the tool description's *"Parameters explained"* section restates every one of them in prose, and clients send both. "Key features" is marketing, not selection signal.

**Measured what-if:** keeping the intro + "When to use this tool" block (dropping the two duplicating sections) → description 566 → 119 tok, tool 921 → **463 tok (50% less, every session, no semantic loss** — the parameter semantics stay in the schema where they already live).

**Ready-to-paste issue:**

> **`sequentialthinking`'s tool definition costs ~921 tokens/session; about half duplicates the schema's own parameter descriptions**
>
> The server advertises one tool whose definition costs **~921 tokens** (tiktoken cl100k; ~566 of that is the description). Every session that connects the server pays this whether the tool is used or not.
>
> Two description sections look droppable at no semantic cost: *"Parameters explained"* restates the `description` that all 9 inputSchema parameters already carry (clients send both, so the text is paid twice), and *"Key features"* describes the tool's virtues rather than when to call it. Keeping the intro + "When to use this tool" yields the same selection signal at **~463 tokens (50% less)** — measured on the published package, method + script: https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.
>
> Happy to send the trim as a PR if the direction sounds right. (Disclosure: I maintain `lap`, the measurement tool used; MIT, no product.)

---

## 2. firecrawl/firecrawl-mcp-server

**Evidence.** 26 tools, **18,511 tokens** of definitions per session. The cost is *descriptions as usage essays*: `firecrawl_monitor_create` desc = 1645 tok; `firecrawl_scrape` desc = 1201 tok; `firecrawl_search_feedback` desc = 944 tok. Sections like *"Usage Example"*, *"CRITICAL - Format Selection"*, *"Common mistakes"* are prompt-engineering docs, not tool-selection signal. Meanwhile **24 of 26 tools have parameters with no description at all** (`lap lint --mcp` rule M2) — the guidance lives in the wrong layer.

**Measured what-if:** first paragraph only per description → **9,218 tok (50% less)**. Realistic target is between the two (keep "Best for" one-liners; move parameter guidance into parameter descriptions).

**Ready-to-paste issue:**

> **Tool descriptions embed usage essays (~18k tokens of definitions per session) while 24/26 tools have undescribed parameters**
>
> The server's 26 tool definitions cost **~18,511 tokens** (tiktoken cl100k) at `tools/list` — paid by every session up front. The bulk is long-form description sections (`firecrawl_scrape` ~1201 tokens of description; "Usage Example", "CRITICAL - Format Selection", "Common mistakes"...). That's documentation, and models are good at *reading docs on demand* — but it's being paid per-session as selection metadata. At the same time, 24 of 26 tools declare parameters with **no** `description`, so the layer models use for argument semantics is empty.
>
> Measured what-if: trimming each description to its first paragraph alone puts the menu at ~9,218 tokens (**50% less**); a realistic middle (keep "Best for" lines, move format guidance into the relevant parameters' descriptions) lands close to that while *improving* argument-level clarity. Method + script: https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.
>
> Happy to draft the restructuring as a PR. (Disclosure: I maintain `lap`, the measurement tool; MIT, no product.)

---

## 3. makenotion/notion-mcp-server

**Evidence.** 24 tools, **21,411 tokens** — the leaderboard's heaviest. The descriptions are admirably terse (13–62 tok); the cost is **schemas**: `API-update-page-markdown` schema = 1469 tok; `API-post-search` schema = 1258 tok; `API-patch-page` schema = 1049 tok. The same Notion object subtrees (rich-text, parent, annotations…) are inlined into tool after tool.

**Measured what-if:** hoisting identical repeated subtrees (≥120 chars, ≥2 uses) into shared `$defs` saves **~14,811 tokens (~69%) by itself** — e.g. one 2317-char subtree × 24; one 2457-char subtree × 2; one 196-char subtree × 3. The 2026 draft spec (SEP-2106) makes `$ref`/`$defs` in inputSchema first-class, so this no longer risks client compatibility. Plus 12 tools carry undescribed parameters (M2).

**Ready-to-paste issue:**

> **Tool inputSchemas inline whole Notion object trees per tool — ~21k tokens of definitions per session**
>
> The server's 24 tools cost **~21,411 tokens** (tiktoken cl100k) at `tools/list` — the heaviest of 20 popular servers we measured (https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-LEADERBOARD.md). The descriptions are terse (nice!); the weight is schemas: `API-update-page-markdown` ~1469 tokens, `API-post-search` ~1258 — the same Notion object subtrees inlined into tool after tool.
>
> Measured: hoisting identical repeated subtrees (≥120 chars, seen ≥2×) into shared `$defs` saves **~14,811 tokens (~69%) on its own**, before any semantic slimming. The 2026-07-28 MCP spec explicitly allows `$ref`/`$defs` in `inputSchema` (SEP-2106), so the compatibility risk that used to argue for inlining is going away. Separately, 12 tools declare parameters without descriptions. Method + script: https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.
>
> Happy to contribute the $defs hoisting or the measurement harness. (Disclosure: I maintain `lap`, the measurement tool; MIT, no product.)

---

## 4. G-Core/gcore-mcp-server (added 2026-07-11)

**Evidence.** With `GCORE_TOOLS=*`: **741 tools, 488,013 tokens** of definitions (659/tool) — the heaviest MCP menu we have ever measured (22× the previous leaderboard maximum), and larger than a 200K context window: the full configuration cannot be loaded at all on most models. The schemas are SDK-generated and inline everything: `cdn_cdn_resources_new` schema = 7046 tok; `cdn_cdn_resources_repl` schema = 6985 tok; `cdn_cdn_resources_upd` schema = 6968 tok. Findings: {'M2': 740, 'M3': 187, 'M4': 90}. One tool fails to register outright (`fastedge.binaries.create`, pydantic can't schema `bytearray`). **Credit where due:** the `GCORE_TOOLS` filter genuinely works — the README's suggested subset is 77 tools / 46,528 tokens (**90% less**) — but even that subset is heavier than the leaderboard's worst full menu, at 604 tok/tool the per-tool density barely moves.

**Measured what-if:** hoisting identical repeated subtrees (≥120 chars, ≥2 uses) into shared `$defs` saves **~120,808 tokens (~25%) by itself** — e.g. one 21656-char subtree × 6; one 129-char subtree × 754; one 24031-char subtree × 3. Composable with the existing subset filter.

**The issue as posted ([gcore#14](https://github.com/G-Core/gcore-mcp-server/issues/14), 2026-07-11):**

> **`GCORE_TOOLS=*` advertises ~488k tokens of tool definitions — larger than most context windows; `$defs` hoisting alone would cut ~25%**
>
> Scored the server with the same open pipeline we use for a public MCP-server leaderboard (fresh `uvx` from git, dummy key, tool listing only, tiktoken): with `GCORE_TOOLS=*` it advertises **741 tools / ~488,013 tokens** (659/tool) — that exceeds a 200K context window on its own, so the full config can't actually be used with most models. Your `GCORE_TOOLS` filter is a real mitigation (the README's suggested subset measures 77 tools / ~46,528 tokens, 90% less) — but the per-tool density stays ~600 tokens either way, because the SDK-generated schemas inline every nested object: `cdn_cdn_resources_new` alone is ~7046 tokens of schema.
>
> Measured on the live listing: hoisting identical repeated subtrees (≥120 chars, seen ≥2×) into shared `$defs` saves **~120,808 tokens (~25%) on its own**, before any semantic slimming — and the 2026-07-28 MCP spec makes `$ref`/`$defs` in `inputSchema` first-class (SEP-2106), so client compatibility is no longer the blocker. Also: `fastedge.binaries.create` fails to register (pydantic can't generate a schema for `bytearray`), and 740 of 741 tools have parameters with no description. Method + script: https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.
>
> Happy to contribute the `$defs` hoisting pass or the measurement harness. (Disclosure: I maintain `lap`, the measurement tool; MIT, no product.)

**Follow-up (2026-07-11): their own pending fix, measured.**
[PR #13](https://github.com/G-Core/gcore-mcp-server/pull/13) ("code-execution routing mode",
open since May 15) replaces the ~700 registrations with **3 meta-tools**
(`search_tools` / `get_tool_schema` / `execute_code` in a Pydantic Monty sandbox with a
host-injected `call_tool()`). Scored the branch: **3 tools / 363 tokens — a 99.9% cut vs the
488k `direct` menu**, structural (Tool-Search-family), with the sandbox design that keeps
intermediate results out of context. The measurement was
[posted to the PR](https://github.com/G-Core/gcore-mcp-server/pull/13#issuecomment-4946062304)
as merge support; both threads are on the twice-daily watch.

---

_Posting checklist (owner): review each text → say the word → they get filed one at a time under your account (per the #236 precedent), each then joins the twice-daily reply watch._
