# Live A/B — gcore PR#13's deferred facade vs the direct subset menu

_Generated 2026-07-12 by [`experiments/facade_ab.py`](../experiments/facade_ab.py). Model **claude-haiku-4-5**, billed `usage` figures from the API (no estimates, no prompt caching). Discovery tasks (find the right catalog tool + its required params) — ground truth from the static scan; nothing is executed against Gcore (dummy key; `search_tools`/`get_tool_schema` run locally). Static context: the facade menu measures 363 tokens vs 488,013 for `GCORE_TOOLS=*` and 46,528 for the README subset ([UPSTREAM-ISSUES §4](UPSTREAM-ISSUES.md))._

| mode | runs | correct | avg billed input/run | avg output | avg tool round-trips |
| --- | ---: | ---: | ---: | ---: | ---: |
| direct (77-tool subset in context) | 15 | 15/15 | 54,275 | 117 | 0.0 |
| facade (3 meta-tools, search on demand) | 15 | 15/15 | 6,723 | 309 | 2.5 |

## Per-task

| task | direct ok | direct in | facade ok | facade in | facade round-trips |
| --- | ---: | ---: | ---: | ---: | ---: |
| List all cloud regions available in this account. | 3/3 | 54,273 | 3/3 | 5,819 | 2.0 |
| Get the details of one specific cloud project. | 3/3 | 54,273 | 3/3 | 8,797 | 3.0 |
| Resize an existing virtual machine instance to a dif | 3/3 | 54,276 | 3/3 | 5,618 | 2.0 |
| List the hardware flavors available for GPU baremeta | 3/3 | 54,277 | 3/3 | 6,532 | 2.7 |
| Acknowledge all pending cloud tasks in a project at  | 3/3 | 54,276 | 3/3 | 6,849 | 3.0 |

**Read.** Per discovery task the facade billed **8.1× less input** on average. The structural cause: the direct mode re-sends the whole subset menu with every API call, the facade sends 3 meta-tool definitions plus only the search/schema results it asked for. Accuracy is the behavioral half — see the table (the R6 lesson is why this run exists: paper savings and live savings are different claims).

_Caveats: one cheap model, k per cell as shown, 5 discovery tasks (tool selection, not end-to-end execution — that needs a real Gcore account); no prompt caching (deliberate: it discounts price, not context); facade `execute_code` was off-limits by instruction._
