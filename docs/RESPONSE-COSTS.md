# Bucket C, measured — what real MCP tool responses cost in context

_Generated 2026-07-25 by [`experiments/response_costs.py`](../experiments/response_costs.py); tokenizer **tiktoken-approx**. Real calls to read-only tools on credential-free published servers; the token figure is the `tool_result` content as a client feeds it back into the model. Calls come from a committed allowlist ([`response_fixtures.json`](../experiments/response_fixtures.json)) — this script never enumerates and calls a server's tools. No LLM involved._

**Why this exists.** Every mitigation the ecosystem has (compact menus, deferred loading, meta-tool facades) shrinks the *menu*. None of them touch the reply. Our own bucket-C figures were schema-based estimates for OpenAPI and simply absent for MCP servers ([the grade skips the result sub-score](MCP-LEADERBOARD.md)). These are measured.

**29 calls across 13 servers, 35,564 tokens of replies.** Heaviest single response: **18,439 tokens** from `wikipedia-mcp` / `get_article`. `projected` = the same payload with each item cut to its first 3 fields (the model `lap score`'s projected bucket C already uses): **44% of projectable response tokens sit in fields past the first 3** (over the 15 rows where that projection still keeps the payload's largest field — see the caveat below). 13 of 29 replies are free text — nothing for a caller to project, filter or paginate; 3 more return structured data in a **non-JSON serialization** (Python `repr()`), which a caller can't parse either.

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

## Read

- **Response size is argument-dependent** — a search returns ten hits because the fixture asked for ten. That's why every row quotes its exact arguments and the allowlist is committed. The conclusions below are only about *avoidable* overhead.
- **Free-text responses are the response-side counterpart of a bloated menu**: they can't be projected, filtered or paginated by the caller, and the model pays for narrative it didn't ask for. Tools that return computed data let the model own the narrative (a point MCP server authors have raised independently).
- **Field selection is the biggest lever we can quantify here** — 44% of projectable response tokens are in fields past the first 3. But an MCP tool has no standard way for a caller to ask for fewer fields (or a smaller page): that is a **protocol-shaped gap**, not an author mistake. On the OpenAPI side the same saving has a name and a rule (R1 field projection, R3 pagination); MCP has no equivalent, so the only lever left to a server author is choosing what to return by default.
- **⚠ Where our own projection model breaks down** — on `arxiv-mcp-server`/`get_abstract` the first-3-fields projection removes the payload's largest field: `get_abstract` replies `{status, paper_id, title, authors, …, abstract}`, so "projected" would drop the abstract itself and claim a ~94% saving for an answer that no longer answers. Those rows are marked ⚠, excluded from the aggregate above, and stand as a limitation of the heuristic that `lap score`'s projected bucket-C shares: *field order is a proxy for importance, and sometimes it's a bad one.*
- **3 replies serialize structured data as Python `repr()`** (single quotes, `None`/`True`) instead of JSON — e.g. `mcp-server-sqlite`/`list_tables`, `mcp-server-sqlite`/`describe_table`, `mcp-server-sqlite`/`read_query`. The data is all there, but a caller can't parse it, so it lands in the model's context as opaque text. Cost-wise it is close to the JSON of the same data (482 vs 363 tokens on the heaviest such row, `read_query`) — this is an interoperability finding, not a token one.

_Caveats: one call per fixture (network-backed servers may vary run to run — local targets like git/sqlite/filesystem are deterministic); tool_result text is what most clients forward, but a client that forwards `structured_content` instead pays the figure in the JSON data file; no LLM in the loop, so this says nothing about whether a trimmed response preserves accuracy — that's a separate live experiment._
