# LAP efficiency leaderboard — agent-menu token cost of real public APIs

_Generated 2026-07-07 by [`experiments/leaderboard.py`](../experiments/leaderboard.py) over specs from [APIs.guru](https://apis.guru)._

**How to read it.** Each row is a real public API. **menu (full)** is the bucket-A token cost of the naive OpenAPI→tools menu a generic MCP/OpenAPI bridge emits — what an agent pays, once per session, just to *see* the API. **compact** and **tool_search** are the LAP-style menus (compact signatures; lazy search+execute) generated from the same spec, with the % saved vs full. Sorted by the naive menu cost (heaviest first): the APIs at the top cost agents the most tokens up front and have the most to gain from a leaner menu. **heaviest result (C)** is the largest single response (bucket C) the estimator finds for the API - the *recurring* per-call cost that field projection and pagination (LAP R1/R3) target. It's a structural lower bound at ~20 items/page, envelope-aware: a list wrapped in an envelope (`{data:[...]}`, k8s `items`) is scaled to a full page too, with its sibling fields (counts, cursors, kind/apiVersion, ...) counted once alongside it. Where a schema carries a real `example`/`examples` value, that's used instead of a synthetic placeholder - real data an API author wrote down beats a guess.

- tokenizer: **tiktoken-approx**  _(approximate — relative ranking is the signal; set `ANTHROPIC_API_KEY` for faithful counts)_
- APIs scored: **50**

| # | API | provider | ops | menu A (full) | compact | save | tool_search | save | heaviest result (C) |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Xero Accounting API | xero.com | 224 | 4041667 | 7800 | +99% | 1213 | +99% | 16463 |
| 2 | Kubernetes | kubernetes.io | 821 | 2864414 | 45015 | +98% | 8369 | +99% | 7658 |
| 3 | Amazon Elastic Compute Cloud | amazonaws.com | 1182 | 1046048 | 86031 | +92% | 8862 | +99% | 365 |
| 4 | Google Sheets API | googleapis.com | 17 | 495263 | 1483 | +99% | 283 | +99% | 5169 |
| 5 | The Jira Cloud platform REST API | atlassian.com | 487 | 356320 | 18121 | +95% | 2401 | +99% | 35105 |
| 6 | Stripe API | stripe.com | 446 | 253265 | 32941 | +87% | 2958 | +99% | 16450 |
| 7 | Amazon Relational Database Service | amazonaws.com | 282 | 227975 | 23917 | +90% | 2062 | +99% | 2090 |
| 8 | Bitbucket API | bitbucket.org | 303 | 180071 | 10811 | +94% | 1563 | +99% | 6607 |
| 9 | Adyen Checkout API | adyen.com | 24 | 169343 | 8334 | +95% | 293 | +99% | 2119 |
| 10 | Amazon DynamoDB | amazonaws.com | 53 | 118053 | 4350 | +96% | 361 | +99% | 260 |
| 11 | GitHub v3 REST API | github.com | 845 | 112818 | 31980 | +72% | 6214 | +94% | 165565 |
| 12 | BigQuery API | googleapis.com | 36 | 101590 | 3563 | +96% | 347 | +99% | 5090 |
| 13 | Zoom API | zoom.us | 373 | 98966 | 7374 | +93% | 1810 | +98% | 11346 |
| 14 | The Plaid API | plaid.com | 198 | 91565 | 25068 | +73% | 1144 | +99% | 6429 |
| 15 | Asana | asana.com | 167 | 90687 | 2362 | +97% | 887 | +99% | 4823 |
| 16 | Linode API | linode.com | 350 | 88906 | 11797 | +87% | 1792 | +98% | 4796 |
| 17 | YouTube Data API v3 | googleapis.com | 76 | 73834 | 3755 | +95% | 570 | +99% | 9416 |
| 18 | ComputeManagementClient | azure.com | 109 | 72620 | 5052 | +93% | 886 | +99% | 3370 |
| 19 | Box Platform API | box.com | 258 | 62765 | 10967 | +83% | 1900 | +97% | 12031 |
| 20 | Vimeo | vimeo.com | 326 | 47081 | 7721 | +84% | 1794 | +96% | 146145 |
| 21 | Drive API | googleapis.com | 48 | 45987 | 3078 | +93% | 372 | +99% | 17802 |
| 22 | Trello | trello.com | 324 | 42800 | 9861 | +77% | 2730 | +94% | - |
| 23 | Amazon Simple Storage Service | amazonaws.com | 95 | 40673 | 3129 | +92% | 587 | +99% | 483 |
| 24 | Calendar API | googleapis.com | 37 | 40637 | 2269 | +94% | 314 | +99% | 7868 |
| 25 | Gitea API. | gitea.io | 325 | 38003 | 11275 | +70% | 1663 | +96% | 44085 |
| 26 | Email Activity (beta) | sendgrid.com | 334 | 36753 | 8781 | +76% | 2456 | +93% | 10325 |
| 27 | Gmail API | googleapis.com | 79 | 31169 | 2960 | +91% | 690 | +98% | 1485 |
| 28 | AWS Lambda | amazonaws.com | 66 | 29623 | 3818 | +87% | 444 | +99% | 319 |
| 29 | Amazon Simple Queue Service | amazonaws.com | 40 | 28142 | 2005 | +93% | 342 | +99% | 36 |
| 30 | Gitlab | gitlab.com | 358 | 27595 | 9079 | +67% | 3506 | +87% | 821 |
| 31 | Spotify Web API | spotify.com | 88 | 26568 | 2696 | +90% | 698 | +97% | 8884 |
| 32 | Vercel API | vercel.com | 112 | 26388 | 3564 | +86% | 571 | +98% | 25326 |
| 33 | Amazon Simple Notification Service | amazonaws.com | 84 | 25095 | 3925 | +84% | 608 | +98% | 11 |
| 34 | DigitalOcean API | digitalocean.com | 290 | 21569 | 3819 | +82% | 1584 | +93% | 19904 |
| 35 | KeyVaultClient | azure.com | 78 | 20572 | 3423 | +83% | 446 | +98% | 1330 |
| 36 | Slack Web API | slack.com | 174 | 17212 | 2566 | +85% | 913 | +95% | 24965 |
| 37 | LaunchDarkly REST API | launchdarkly.com | 105 | 12445 | 3580 | +71% | 593 | +95% | 5401 |
| 38 | OpenAI API | openai.com | 28 | 12264 | 2195 | +82% | 247 | +98% | 1854 |
| 39 | Netlify's API documentation | netlify.com | 120 | 11657 | 3980 | +66% | 656 | +94% | 9645 |
| 40 | StorageManagementClient | azure.com | 19 | 10941 | 1343 | +88% | 247 | +98% | 3850 |
| 41 | Lucidtech API | webflow.com | 81 | 10310 | 4967 | +52% | 423 | +96% | 6290 |
| 42 | Firebase Management API | googleapis.com | 21 | 8056 | 1042 | +87% | 272 | +97% | 1311 |
| 43 | Postman API | getpostman.com | 57 | 7772 | 725 | +91% | 352 | +95% | 2925 |
| 44 | Platform API | ably.io | 22 | 5283 | 642 | +88% | 253 | +95% | 1405 |
| 45 | Notion API | notion.com | 13 | 1637 | 168 | +90% | 197 | +88% | 14898 |
| 46 | CircleCI REST API | circleci.com | 22 | 1598 | 801 | +50% | 232 | +85% | 6065 |
| 47 | DVP Data API | docker.com | 8 | 796 | 303 | +62% | 186 | +77% | 335 |
| 48 | Events API | 1password.com | 3 | 123 | 111 | +10% | 158 | -28% | 2865 |
| 49 | clickup20 | clickup.com | 2 | 101 | 43 | +57% | 153 | -51% | - |
| 50 | APOD | nasa.gov | 1 | 54 | 31 | +43% | 148 | -174% | 45 |

**Across all 50 APIs:** the naive menus total **11,175,074 tokens** (bucket A); `compact_sig` saves **+82%** on average and `tool_search` **+86%** (it wins most where operation counts are high). And that's before results come back: **10 of 50** have list endpoints with **no pagination**, so an agent can pull the *whole* collection into context (bucket C), not just a page. These APIs expose OpenAPI, which a generic bridge turns into the naive menu — so for an agent front-end the saving is mostly still on the table.

_Methodology: **A** (menu) is measured; **heaviest result (C)** is estimated from response schemas (structural lower bound; top-level AND envelope-wrapped lists scaled to ~20 items/page; real schema `example`/`examples` values preferred over the 6-char synthetic placeholder where present - `--string-len` on `lap score` raises the placeholder for un-exampled fields). **B** (the call) needs per-API tasks - see [`experiments/token-bench`](../experiments/token-bench/README.md). Regenerate with `python experiments/leaderboard.py`._
