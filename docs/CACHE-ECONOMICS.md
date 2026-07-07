# Cache economics - does prompt caching make the menu free?

_Generated 2026-07-07 by [`experiments/cache_economics.py`](../experiments/cache_economics.py) from the [leaderboard](LEADERBOARD.md) data; tokenizer as there (**tiktoken-approx**)._

**The objection.** "Tool definitions are prompt-cached, so bucket A costs nothing - why optimize the menu?" This doc prices that claim with the standard caching model: a cache **write** bills at **1.25x** base input, a cache **read** at **0.10x**, and the prefix is re-sent **every assistant turn**, so a T-turn session pays `A x T` uncached vs `A x (1.25 + 0.10(T-1))` cached - best case (prefix byte-identical throughout, no idle gap past the cache TTL).

## What caching actually buys

- **At best a 10x discount, asymptotically.** As T grows the cached cost tends to `0.10 x A` per turn - never zero. A compact rendering is a ~5x cut that **composes** with caching: compact+cached ~= 50x cheaper than naive uncached.
- **Break-even vs a compact menu:** with compaction ratio `r = compact/naive`, an *uncached* compact menu beats a *cached* naive one while `T < 1.15 / (r - 0.10)` turns (and at **any** T once `r <= 0.10`). At the leaderboard-average r ~= 0.20 that's ~11 turns; on GitHub (r = 0.32) ~5 turns; on Xero (r = 0.002) - always. So even a caching refusenik wins with the leaner menu on typical sessions; and if you do cache, cache the leaner menu (the strategies compose, they don't compete).
- **Caching pays in dollars, not context.** The cached definitions still occupy the context window and still tax the model's working memory - the reasoning-capacity concern in MCP spec issue #2808 is untouched by caching. Kubernetes' 2.8M-token naive menu doesn't fit a 200K window at any discount. Tool Search / deferred loading is different in kind: the definitions are genuinely absent (saves dollars AND context).
- **The best case is fragile.** Any change to any tool definition invalidates the prefix (that's what #2808's `schema_version` proposal protects); an idle gap longer than the cache TTL (minutes) triggers a full re-write; and the write premium means a cache used only once costs **125%** of not caching at all.

## Worked examples (real menus, billing-weighted input tokens)

Billing-weighted tokens = raw tokens x price multiplier; dollar column at Sonnet-class input pricing ($3.00/M).

### Xero Accounting API - naive 4,039,605 tok, compact 7,794 tok (224 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 4,039,605 | 5,049,506 | 7,794 | 9,742 | compact uncached |
| 3 | 12,118,815 | 5,857,427 | 23,382 | 11,301 | compact cached |
| 8 | 32,316,840 | 7,877,230 | 62,352 | 15,198 | compact cached |
| 25 | 100,990,125 | 14,744,558 | 194,850 | 28,448 | compact cached |
| 100 | 403,960,500 | 45,041,596 | 779,400 | 86,903 | compact cached |

At a typical 8-turn session: naive uncached ~$96.95, compact cached ~$0.046 per session - **2,126x** apart on this API.

### GitHub v3 REST API - naive 100,181 tok, compact 31,888 tok (845 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 100,181 | 125,226 | 31,888 | 39,860 | compact uncached |
| 3 | 300,543 | 145,262 | 95,664 | 46,238 | compact cached |
| 8 | 801,448 | 195,353 | 255,104 | 62,182 | compact cached |
| 25 | 2,504,525 | 365,661 | 797,200 | 116,391 | compact cached |
| 100 | 10,018,100 | 1,117,018 | 3,188,800 | 355,551 | compact cached |

At a typical 8-turn session: naive uncached ~$2.40, compact cached ~$0.187 per session - **13x** apart on this API.

### Notion API - naive 1,587 tok, compact 168 tok (13 ops)

| turns | naive uncached | naive cached | compact uncached | compact cached | cheapest |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1,587 | 1,984 | 168 | 210 | compact uncached |
| 3 | 4,761 | 2,301 | 504 | 244 | compact cached |
| 8 | 12,696 | 3,095 | 1,344 | 328 | compact cached |
| 25 | 39,675 | 5,793 | 4,200 | 613 | compact cached |
| 100 | 158,700 | 17,695 | 16,800 | 1,873 | compact cached |

At a typical 8-turn session: naive uncached ~$0.04, compact cached ~$0.001 per session - **39x** apart on this API.

## Takeaway

Caching is a *price multiplier* (>=0.10x, fragile); menu form is a *token multiplier* (~0.2x, robust, also frees context). They multiply. The order of operations for an API author is therefore: make the menu lean (D1), defer it where the platform can (D2), and *then* let callers cache what remains - not the other way around.
