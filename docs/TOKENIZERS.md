# Tokenizer sensitivity - whose tokens are these anyway?

_Generated 2026-07-07 by [`experiments/tokenizer_matrix.py`](../experiments/tokenizer_matrix.py) over the 51-API leaderboard corpus._

lap's offline backend counts with **cl100k_base** and says so on every report ("absolute numbers approximate, relative ordering robust"). This doc checks that claim against three other BPE vocabularies on the exact same menu texts.

## What moves and what doesn't

| metric | cl100k_base | o200k_base | p50k_base | gpt2 |
| --- | ---: | ---: | ---: | ---: |
| naive total (tokens) | 12,056,451 | 12,073,505 | 12,952,178 | 12,976,913 |
| mean compact saving | 82.4% | 82.3% | 79.4% | 79.4% |
| per-API saving spread (stdev) | 17.0 pp | 17.4 pp | 18.8 pp | 18.8 pp |
| ranking vs cl100k (Kendall tau) | 1.000 | 0.997 | 0.994 | 0.992 |

- **Absolute totals swing by up to 8%** across vocabularies - never quote lap's offline absolutes as model-billing numbers (set `ANTHROPIC_API_KEY` for faithful counts; Stage 13 measured those at ~60% above the approximation with identical ordering).
- **The savings claim barely moves**: the mean compact saving varies by 3.0 percentage points across vocabularies; the single worst per-API spread is 12.6 pp (CircleCI REST API).
- **The ranking doesn't move**: Kendall tau >= 0.992 against the baseline for every vocabulary - "which APIs are heaviest and what a compact menu saves" is tokenizer-robust.

## Sample (10 heaviest APIs, naive-menu tokens per vocabulary)

| API | cl100k_base | o200k_base | p50k_base | gpt2 | save (min..max) |
| --- | ---: | ---: | ---: | ---: | --- |
| Xero Accounting API | 4,041,667 | 4,044,760 | 4,269,387 | 4,269,469 | 100..100% |
| Kubernetes | 2,864,414 | 2,865,470 | 3,108,574 | 3,130,639 | 98..98% |
| Amazon Elastic Compute Cloud | 1,046,048 | 1,044,415 | 1,141,593 | 1,141,593 | 91..92% |
| Compute Engine API | 881,377 | 880,813 | 943,916 | 943,916 | 94..95% |
| Google Sheets API | 495,263 | 497,389 | 524,956 | 524,956 | 100..100% |
| The Jira Cloud platform REST A | 356,320 | 360,811 | 380,628 | 381,040 | 94..95% |
| Stripe API | 253,265 | 256,263 | 282,860 | 282,860 | 84..87% |
| Amazon Relational Database Ser | 227,975 | 228,129 | 247,905 | 247,905 | 89..90% |
| Bitbucket API | 180,071 | 180,240 | 195,038 | 195,628 | 92..94% |
| Adyen Checkout API | 169,343 | 170,043 | 182,814 | 182,822 | 94..95% |

_Method: identical menu texts (naive `openapi_full` JSON, LAP `compact_sig` text) per API, re-encoded with each vocabulary via tiktoken, `disallowed_special=()`. The compressed-vs-verbose gap is a property of the *text*, not the ruler._
