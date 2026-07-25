# Bucket C, measured — a price list of real MCP tool responses

_Generated 2026-07-25 by [`experiments/response_costs.py`](../experiments/response_costs.py); tokenizer **tiktoken-approx**. Real calls to read-only tools on credential-free published servers; the token figure is the `tool_result` content as a client feeds it back into the model. Calls come from a committed allowlist ([`response_fixtures.json`](../experiments/response_fixtures.json)) — this script never enumerates and calls a server's tools. No LLM involved._

**What this is.** Reference data, not a ranking. Our bucket-C figures were schema-based estimates for OpenAPI and absent for MCP servers ([the grade skips the result sub-score](MCP-LEADERBOARD.md)); as far as we know nobody had published measured response costs at all. Response size belongs to the *request* — a long article is long because we asked for an article — so a big number in this table is not by itself a finding. What the dataset supports: budgeting (what does a call of this shape put into context?), validating estimators, and the two structural observations below, which don't depend on any response being "too big".

**29 calls across 13 servers, 35,564 tokens of replies** — ranging from 1 token(s) (`calculate`) to 18,439 (`wikipedia-mcp`/`get_article`, a full article). Payload form: 13 JSON, 13 free text, 3 Python-`repr()`. `projected` = the same payload with each item cut to its first 3 fields; treat it as a *ceiling* on what caller-side field selection could reclaim, not a saving (see the caveat on where the heuristic breaks).

| server | tool | args | response tok | projected | payload |
| --- | --- | --- | ---: | ---: | --- |
| wikipedia-mcp | `get_article` | `{"title": "Python (programming language)…` | 18,439 | 12,764 | JSON |
| wikipedia-mcp | `get_sections` | `{"title": "Python (programming language)…` | 8,700 | 3,025 | JSON |
| arxiv-mcp-server | `search_papers` | `{"query": "model context protocol", "max…` | 1,955 | 239 | JSON |
| mcp-server-git | `git_log` | `{"repo_path": "{REPO}", "max_count": 5}` | 1,281 | — | **text** |
| wikipedia-mcp | `search_wikipedia` | `{"query": "Model Context Protocol", "lim…` | 1,077 | 861 | JSON |
| duckduckgo-mcp-server | `search` | `{"query": "model context protocol token …` | 954 | — | **text** |
| mcp-server-git | `git_show` | `{"repo_path": "{REPO}", "revision": "HEA…` | 905 | — | **text** |
| mcp-server-sqlite | `read_query` | `{"query": "SELECT * FROM items"}` | 482 | 162 | **repr** (not JSON) |
| arxiv-mcp-server | `get_abstract` | `{"paper_id": "2103.00020"}` | 475 | 27 ⚠ | JSON |
| wikipedia-mcp | `get_summary` | `{"title": "Python (programming language)…` | 260 | 260 | JSON |
| mcp-server-sqlite | `describe_table` | `{"table_name": "items"}` | 229 | 75 | **repr** (not JSON) |
| mcp-server-fetch | `fetch` | `{"url": "https://example.com", "raw": tr…` | 187 | — | **text** |
| server-filesystem | `get_file_info` | `{"path": "{TMP}/notes.md"}` | 125 | — | **text** |
| mcp-server-time | `convert_time` | `{"source_timezone": "UTC", "time": "12:0…` | 120 | 84 | JSON |
| mcp-server-git | `git_status` | `{"repo_path": "{REPO}"}` | 89 | — | **text** |
| mcp-server-time | `get_current_time` | `{"timezone": "UTC"}` | 47 | 30 | JSON |
| sequential-thinking | `sequentialthinking` | `{"thought": "Measure the response, then …` | 41 | 18 | JSON |
| server-filesystem | `directory_tree` | `{"path": "{TMP}"}` | 40 | 21 | JSON |
| mcp-server-fetch | `fetch` | `{"url": "https://example.com"}` | 34 | — | **text** |
| server-filesystem | `read_text_file` | `{"path": "{TMP}/notes.md"}` | 29 | — | **text** |
| markitdown-mcp | `convert_to_markdown` | `{"uri": "file:///{TMP}/notes.md"}` | 29 | — | **text** |
| server-everything | `get-structured-content` | `{"location": "New York"}` | 14 | 14 | JSON |
| server-memory | `read_graph` | `{}` | 12 | 7 | JSON |
| server-everything | `get-sum` | `{"a": 2, "b": 3}` | 12 | — | **text** |
| server-filesystem | `list_directory` | `{"path": "{TMP}"}` | 11 | — | **text** |
| mcp-server-sqlite | `list_tables` | `{}` | 8 | 7 | **repr** (not JSON) |
| mcp-server-git | `git_diff_unstaged` | `{"repo_path": "{REPO}"}` | 5 | — | **text** |
| server-everything | `echo` | `{"message": "hello"}` | 3 | — | **text** |
| mcp-server-calculator | `calculate` | `{"expression": "2+2*10"}` | 1 | 1 | JSON |

## What the dataset supports

- **A price list.** Every row quotes its exact arguments because the cost belongs to the request; use the table to budget what a call of a given shape puts into context, the way the [leaderboard](MCP-LEADERBOARD.md) budgets menus. No row is an accusation.
- **The affordance gap (structural — visible in the schemas, independent of any measured size).** Some tools give the caller a brake: `fetch` has `max_length`/`start_index`, `git_log` has `max_count`, `read_text_file` has `head`/`tail`, the search tools have `max_results`. Others don't: `get_article` accepts only `title`, `get_abstract` only `paper_id` — whatever comes back, comes back whole. And MCP itself has no standard caller-side field or page selection (OpenAPI has R1/R3 for exactly this), so where the author didn't add a limit parameter, no one downstream can add one. A protocol-shaped gap, not an author mistake.
- **Response form (structural).** 13 of 29 replies are free text: whatever their size, the caller can't parse, filter or paginate them — the model pays for narrative formatting it may not need. Tools that return computed data leave the narrative to the model (a point MCP server authors have raised independently).
- **Projection ceiling, stated carefully.** Under the first-3-fields heuristic, 44% of the projectable tokens would be cut (15 rows where the projection keeps the payload's largest field). This is an upper bound on what caller-side field selection *could* reclaim if MCP had such a mechanism — not a measured saving, and the heuristic itself fails on some shapes (next bullet).
- **⚠ Where our own projection model breaks down** — on `arxiv-mcp-server`/`get_abstract` the first-3-fields projection removes the payload's largest field: `get_abstract` replies `{status, paper_id, title, authors, …, abstract}`, so "projected" would drop the abstract itself and claim a ~94% saving for an answer that no longer answers. Those rows are marked ⚠, excluded from the aggregate above, and stand as a limitation of the heuristic that `lap score`'s projected bucket-C shares: *field order is a proxy for importance, and sometimes it's a bad one.*
- **3 replies serialize structured data as Python `repr()`** (single quotes, `None`/`True`) instead of JSON — e.g. `mcp-server-sqlite`/`list_tables`, `mcp-server-sqlite`/`describe_table`, `mcp-server-sqlite`/`read_query`. The data is all there, but a caller can't parse it, so it lands in the model's context as opaque text. Cost-wise it is close to the JSON of the same data (482 vs 363 tokens on the heaviest such row, `read_query`) — this is an interoperability finding, not a token one.

_Caveats: one call per fixture (network-backed servers may vary run to run — local targets like git/sqlite/filesystem are deterministic); tool_result text is what most clients forward, but a client that forwards `structured_content` instead pays the figure in the JSON data file; and no LLM was involved, so this dataset says nothing about model behavior — e.g. whether models over-pick heavy tools when a cheaper one would do (`get_article` vs `get_summary`) is a plausible hypothesis this data cannot test; it would need a live experiment._
