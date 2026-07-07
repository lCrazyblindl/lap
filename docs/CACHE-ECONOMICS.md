# Cache economics - does prompt caching make the menu free?

_Generated 2026-07-07 by [`experiments/cache_economics.py`](../experiments/cache_economics.py) from the [leaderboard](LEADERBOARD.md) data; tokenizer as there (**tiktoken-approx**)._

**The objection.** "Tool definitions are prompt-cached, so bucket A costs nothing - why optimize the menu?" This doc prices that claim with the standard caching model: a cache **write** bills at **1.25x** base input, a cache **read** at **0.10x**, and the prefix is re-sent **every assistant turn**, so a T-turn session pays `A x T` uncached vs `A x (1.25 + 0.10(T-1))` cached - best case (prefix byte-identical throughout, no idle gap past the cache TTL).

## What caching actually buys

- **At best a 10x discount, asymptotically.** As T grows the cached cost tends to `0.10 x A` per turn - never zero. A compact rendering is a ~5x cut that **composes** with caching: compact+cached ~= 50x cheaper than naive uncached.
- **Break-even vs a compact menu:** with compaction ratio `r = compact/naive`, an *uncached* compact menu beats a *cached* naive one while `T < 1.15 / (r - 0.10)` turns (and at **any** T once `r <= 0.10`). At the leaderboard-average r ~= 0.18 that's ~14 turns; on GitHub (r = 0.28) ~6 turns; on Xero (r = 0.002) - always. So even a caching refusenik wins with the leaner menu on typical sessions; and if you do cache, cache the leaner menu (the strategies compose, they don't compete).
- **Caching pays in dollars, not context.** The cached definitions still occupy the context window and still tax the model's working memory - the reasoning-capacity concern in MCP spec issue #2808 is untouched by caching. Kubernetes' 2.8M-token naive menu doesn't fit a 200K window at any discount. Tool Search / deferred loading is different in kind: the definitions are genuinely absent (saves dollars AND context).
- **The best case is fragile.** Any change to any tool definition invalidates the prefix (that's what #2808's `schema_version` proposal protects); an idle gap longer than the cache TTL (minutes) triggers a full re-write; and the write premium means a cache used only once costs **125%** of not caching at all.

## Worked examples (real menus, billing-weighted input tokens)

Billing-weighted tokens = raw tokens x price multiplier; dollar column at Sonnet-class input pricing ($3.00/M).

### Xero Accounting API - naive 4,041,667 tok, compact 7,800 tok (224 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 4,041,667 | 5,052,084 | 7,800 | 9,750 | compact uncached |
| 3 | 12,125,001 | 5,860,417 | 23,400 | 11,310 | compact cached |
| 8 | 32,333,336 | 7,881,251 | 62,400 | 15,210 | compact cached |
| 25 | 101,041,675 | 14,752,085 | 195,000 | 28,470 | compact cached |
| 100 | 404,166,700 | 45,064,587 | 780,000 | 86,970 | compact cached |

At a typical 8-turn session: naive uncached ~$97.00, compact cached ~$0.046 per session - **2,126x** apart on this API.

### GitHub v3 REST API - naive 112,818 tok, compact 31,980 tok (845 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 112,818 | 141,022 | 31,980 | 39,975 | compact uncached |
| 3 | 338,454 | 163,586 | 95,940 | 46,371 | compact cached |
| 8 | 902,544 | 219,995 | 255,840 | 62,361 | compact cached |
| 25 | 2,820,450 | 411,786 | 799,500 | 116,727 | compact cached |
| 100 | 11,281,800 | 1,257,921 | 3,198,000 | 356,577 | compact cached |

At a typical 8-turn session: naive uncached ~$2.71, compact cached ~$0.187 per session - **14x** apart on this API.

### Notion API - naive 1,637 tok, compact 168 tok (13 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1,637 | 2,046 | 168 | 210 | compact uncached |
| 3 | 4,911 | 2,374 | 504 | 244 | compact cached |
| 8 | 13,096 | 3,192 | 1,344 | 328 | compact cached |
| 25 | 40,925 | 5,975 | 4,200 | 613 | compact cached |
| 100 | 163,700 | 18,253 | 16,800 | 1,873 | compact cached |

At a typical 8-turn session: naive uncached ~$0.04, compact cached ~$0.001 per session - **40x** apart on this API.

## Takeaway

Caching is a *price multiplier* (>=0.10x, fragile); menu form is a *token multiplier* (~0.2x, robust, also frees context). They multiply. The order of operations for an API author is therefore: make the menu lean (D1), defer it where the platform can (D2), and *then* let callers cache what remains - not the other way around.
