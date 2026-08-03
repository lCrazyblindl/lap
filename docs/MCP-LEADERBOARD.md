# MCP-server leaderboard — what popular published servers charge your context window

_Generated 2026-08-03 by [`experiments/mcp_leaderboard.py`](../experiments/mcp_leaderboard.py); tokenizer: **tiktoken-approx**. Each server was installed and run locally in an isolated env (`uvx` / `npx -y`), its advertised tool list fetched over stdio with **no credentials** (dummy env vars only where a server refuses to boot without them), and scored exactly like `lap lint --mcp`: menu (bucket A) tokens + M-rule hygiene + the composite grade (result sub-score skipped - tool listings don't declare response shapes). Same method as the [OpenAPI leaderboard](LEADERBOARD.md)._

**19 servers reachable, 425 tools; their menus total 99,295 tokens per session before the first user message** - a compact rendering of the same tools would cost 6,844 (93% less). Every session with these servers connected pays the menu whether the tools are used or not ([cache math](CACHE-ECONOMICS.md): caching discounts the price, not the context).

| server | by | tools | menu tok | tok/tool | compact | saved | findings (warn/info) | grade |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| datadog-mcp (@us-all) | community | 166 | 28,835 | 174 | 2,799 | 90% | 1/25 | **B** (82) |
| notion-mcp-server | Notion | 24 | 21,411 | 892 | 400 | 98% | 25/14 | **F** (19) |
| firecrawl-mcp | Firecrawl | 26 | 9,948 | 383 | 773 | 92% | 6/28 | **D** (43) |
| easy-notion-mcp | community (Grey-Iris) | 42 | 8,199 | 195 | 554 | 93% | 0/2 | **B** (83) |
| yfmcp (Yahoo Finance) | community | 13 | 4,412 | 339 | 229 | 95% | 1/2 | **C** (68) |
| playwright-mcp | Microsoft | 24 | 4,018 | 167 | 288 | 93% | 3/6 | **B** (77) |
| excel-mcp-server | community | 25 | 3,955 | 158 | 494 | 88% | 0/26 | **C** (69) |
| aws-documentation-mcp | AWS Labs | 5 | 3,604 | 721 | 81 | 98% | 3/0 | **F** (37) |
| arxiv-mcp-server | community | 14 | 3,346 | 239 | 198 | 94% | 1/4 | **B** (72) |
| mcp-server-datadog (winor30) | community (winor30) | 21 | 2,497 | 119 | 316 | 87% | 0/13 | **B** (81) |
| wikipedia-mcp | community | 22 | 1,933 | 88 | 235 | 88% | 0/18 | **B** (83) |
| server-filesystem | official reference | 14 | 1,915 | 137 | 130 | 93% | 0/12 | **B** (74) |
| server-everything | official reference | 13 | 1,302 | 100 | 114 | 91% | 0/5 | **A** (89) |
| server-memory | official reference | 9 | 1,117 | 124 | 69 | 94% | 0/4 | **B** (84) |
| context7 | Upstash | 2 | 1,032 | 516 | 31 | 97% | 1/0 | **D** (47) |
| sequential-thinking | official reference | 1 | 921 | 921 | 59 | 94% | 1/0 | **F** (18) |
| duckduckgo-mcp-server | community | 2 | 729 | 364 | 41 | 94% | 0/2 | **D** (53) |
| markitdown-mcp | Microsoft | 1 | 79 | 79 | 18 | 77% | 0/1 | **B** (82) |
| server-postgres | official (archived) | 1 | 42 | 42 | 15 | 64% | 0/2 | **C** (64) |

_`saved` = compact signatures of the same tools (what [rule D1](../profile/llm-api-profile.md) asks for). Grades: menu weight 0.45 + hygiene 0.25, renormalized; A >= 85 ... F < 40._

## Not reachable without credentials / extra runtime

These wouldn't even list tools in a clean environment - noted, not scored:

| server | kind | error |
| --- | --- | --- |
| mcp-server-git | pip | `McpError: Connection closed` |
| mcp-server-time | pip | `McpError: Connection closed` |
| mcp-server-fetch | pip | `McpError: Connection closed` |
| mcp-server-sqlite | pip | `McpError: Connection closed` |
| mcp-atlassian | pip | `RuntimeError: advertised 0 tools` |
| mcp-server-calculator | pip | `McpError: Connection closed` |

## Cross-check: agent-friend's published grades

[agent-friend](https://github.com/0-co/agent-friend) (MCP-only static linter, 156 checks, 40% correctness / 30% efficiency / 30% quality) published grades for 201 servers (2026-03). On the servers both tools scored:

| server | agent-friend | lap | lap menu tok |
| --- | --- | --- | ---: |
| notion-mcp-server | F (19.8/100); 4,483 tok / 22 tools | F (19) | 21,411 |
| context7 | F (7.5/100) | D (47) | 1,032 |
| server-postgres | 100/100 ("perfect") | C (64) | 42 |

Read: the graders *converge on Notion* (both F, scores within a point) yet *diverge hard on server-postgres* (their "perfect 100" vs our C - one tiny tool, but its 42-token menu hides an inputSchema with no descriptions, which our M-rules charge) and on context7 (D vs F). And even where the letters agree, the token counts don't (Notion: our 21,411 vs their 4,483 - different server versions, tokenizers, and what counts as "the schema"). The lesson is the referee point: **letters are formula artifacts; raw, reproducible token numbers are the measurement.** This leaderboard publishes both, plus the script.

_Caveats: tool listing only (no calls billed or executed); one run per server; a server's menu can differ per version and per advertised capabilities; npm servers ran via `npx -y` (whatever version the registry serves today). Reproduce: `python experiments/mcp_leaderboard.py` - needs `uv` (pip) and Node for the npm rows._
