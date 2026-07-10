# Upstream issues — measured, POSTED 2026-07-10 (owner-authorized)

_Generated 2026-07-10 by [`experiments/upstream_issues.py`](../experiments/upstream_issues.py); tokenizer **tiktoken-approx**; servers fetched live via `npx -y` (versions = registry latest on the scan date). **All three were posted on 2026-07-10 with the owner's authorization**: [servers#4507](https://github.com/modelcontextprotocol/servers/issues/4507) · [firecrawl#309](https://github.com/firecrawl/firecrawl-mcp-server/issues/309) · [notion#330](https://github.com/makenotion/notion-mcp-server/issues/330); the twice-daily watch tracks replies. The motion is the one that already converted: [mcp-compressor #236 → fixed & shipped in a day](MCP-COMPRESSOR.md)._

| target | repo | today | measured what-if | saving |
| --- | --- | ---: | ---: | ---: |
| sequential-thinking | modelcontextprotocol/servers | 921 tok | 463 tok | 50% |
| firecrawl-mcp | firecrawl/firecrawl-mcp-server | 18,511 tok | 9,218 tok | 50% |
| notion-mcp-server | makenotion/notion-mcp-server | 21,411 tok | ~6,600 tok | ~69% (dedupe alone) |

---

## 1. modelcontextprotocol/servers — `sequentialthinking`

**Evidence.** One tool, **921 tokens** per session (566 description + 320 schema). All 9 parameters already carry `description`s in the inputSchema — yet the tool description's *"Parameters explained"* section restates every one of them in prose, and clients send both. "Key features" is marketing, not selection signal.

**Measured what-if:** keeping the intro + "When to use this tool" block (dropping the two duplicating sections) → description 566 → 119 tok, tool 921 → **463 tok (50% less, every session, no semantic loss** — the parameter semantics stay in the schema where they already live).

**The issue as posted ([servers#4507](https://github.com/modelcontextprotocol/servers/issues/4507)):**

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

**The issue as posted ([firecrawl#309](https://github.com/firecrawl/firecrawl-mcp-server/issues/309)):**

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

**The issue as posted ([notion#330](https://github.com/makenotion/notion-mcp-server/issues/330)):**

> **Tool inputSchemas inline whole Notion object trees per tool — ~21k tokens of definitions per session**
>
> The server's 24 tools cost **~21,411 tokens** (tiktoken cl100k) at `tools/list` — the heaviest of 20 popular servers we measured (https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-LEADERBOARD.md). The descriptions are terse (nice!); the weight is schemas: `API-update-page-markdown` ~1469 tokens, `API-post-search` ~1258 — the same Notion object subtrees inlined into tool after tool.
>
> Measured: hoisting identical repeated subtrees (≥120 chars, seen ≥2×) into shared `$defs` saves **~14,811 tokens (~69%) on its own**, before any semantic slimming. The 2026-07-28 MCP spec explicitly allows `$ref`/`$defs` in `inputSchema` (SEP-2106), so the compatibility risk that used to argue for inlining is going away. Separately, 12 tools declare parameters without descriptions. Method + script: https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.
>
> Happy to contribute the $defs hoisting or the measurement harness. (Disclosure: I maintain `lap`, the measurement tool; MIT, no product.)

---

_Outcome tracking: replies and closures are watched twice daily alongside #2812 and mcp-compressor#236 (which converted into a merged fix in a day — [MCP-COMPRESSOR.md](MCP-COMPRESSOR.md))._
