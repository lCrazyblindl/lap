# Arazzo workflows as macro tools — the declared chain vs the ad-hoc chain

_Generated 2026-07-10 by [`experiments/arazzo_score.py`](../experiments/arazzo_score.py); tokenizer **tiktoken-approx**. Corpus: the [Arazzo 1.0 specification's own example documents](https://github.com/OAI/Arazzo-Specification/tree/main/examples/1.0.0) (real third-party artifacts), workflows resolved against their paired OpenAPI descriptions. B estimates are the same structural lower bounds `lap score` uses (required-only args in a minimal tool-use envelope)._

**The idea.** An [Arazzo](https://github.com/OAI/Arazzo-Specification) document declares a multi-step workflow — steps, data flow, success criteria — that an executor can run server-side. To an agent that's a **macro tool**: advertise the workflow's id + summary + `inputs` schema as ONE tool instead of asking the model to plan the chain against the full API menu.

| doc | workflow | steps | menu: naive API → workflow-tool | call(s): ad-hoc chain → one call |
| --- | --- | ---: | ---: | ---: |
| pet-coupons | `apply-coupon` (2/3 resolved) | 3 | 1,268 → **40** | 27 → **11** |
| pet-coupons | `buy-available-pet` (1/2 resolved) | 2 | 1,268 → **43** | 14 → **12** |
| pet-coupons | `place-order` | 1 | 1,268 → **122** | 38 → **23** |
| bnpl | `ApplyForLoanAtCheckout` | 7 | 1,109 → **490** | 174 → **69** |
| oauth | `refresh-token-flow` (1/2 resolved) | 2 | 182 → **90** | 20 → **30** |
| oauth | `client-credentials-flow` | 1 | 182 → **73** | 20 → **22** |
| oauth | `authorization-code-flow` | 2 | 182 → **91** | 55 → **27** |

**Read.** Across 7 example workflows the workflow-as-tool menu costs **50%–97% less** than the naive menu of the underlying API (bucket A). Bucket B splits by chain size — **the win grows with the chain**: the 7-step `ApplyForLoanAtCheckout` drops 174 → 69 tokens per invocation, while 2 of 7 tiny flows actually pay *more* (a workflow's `inputs` schema can exceed the one or two small calls it replaces — the same below-threshold shape we measured for tool_search under ~10 tools and for schema dedupe on thin params). And the biggest effect doesn't show in A/B accounting at all: **the intermediate step results never enter the model's context** (each ad-hoc step's bucket-C response would have; the executor consumes them server-side). That's a *structural* saving — the same server-enforced property that made Tool Search hold up in our live tests ([TOOL-SEARCH](TOOL-SEARCH.md)) where behavioral savings didn't ([CODE-EXEC](CODE-EXEC.md)).

**Honest caveats.** (1) These are the spec's own examples — small APIs; on a leaderboard-scale API the menu gap widens mechanically, but nobody ships Arazzo documents for those yet (adoption is the bottleneck, as with every declared artifact). (2) A macro tool trades *flexibility* for cost: the model can't deviate mid-chain — right for stable business flows, wrong for exploration (the same category-shaped trade our matrix found for query DSLs, X1). (3) The executor is real infrastructure someone must run; Arazzo runners exist but are young. (4) B savings assume required-only inputs, as everywhere in `lap score`.

**Where this could go**: an `x-lap-workflow` pointer from an OpenAPI description to its Arazzo document would let `lap score` report the macro-tool figure next to the menu figures automatically — see the [x-lap strawman](X-LAP.md).
