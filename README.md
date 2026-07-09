# lap — how many tokens does your API cost an LLM agent?

[![ci](https://github.com/lCrazyblindl/lap/actions/workflows/ci.yml/badge.svg)](https://github.com/lCrazyblindl/lap/actions/workflows/ci.yml) [![LAP grade (bundled example)](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FlCrazyblindl%2Flap%2Fmain%2Fdocs%2Flap-badge.json)](profile/llm-api-profile.md) [![PyPI](https://img.shields.io/pypi/v/lap-score)](https://pypi.org/project/lap-score/) · MIT · [Changelog](CHANGELOG.md) · [Live leaderboard](https://lcrazyblindl.github.io/lap/)

Every agent session starts by paying for tool definitions it mostly won't use — and pays
again for every call and every response. **lap** measures that, for any OpenAPI spec, live
MCP server, or your own agent config: the token cost decomposed (**A** menu / **B** call /
**C** result), a **0–100 grade**, the rule violations driving the cost, and an applicable
patch for the fixable ones. Free, neutral, reproducible — a measuring stick, not a product.

## Try it (60 seconds)

```bash
pip install "lap-score[mcp]"

lap stack                                   # YOUR installed MCP servers: tokens paid before you type a word
lap score  openapi.json                     # A/B/C decomposition + grade (also --mcp-url for live servers)
lap lint   openapi.json                     # the violations driving the cost (also --mcp "cmd" for servers)
lap fix    openapi.json --apply patched.json  # fixable findings as an OpenAPI Overlay patch
lap badge  openapi.json                     # shields.io grade badge for your README
```

```
$ lap stack
  server        kind   tools  menu tokens  compact
  time          stdio      2          283       31
  git           stdio     12         1418      153
  TOTAL                    14         1701      184
Your agent pays ~1,701 tokens of tool menus at session start - before you type a word.

$ lap fix api/openapi.json --apply patched.json
[written] lap-overlay.yaml  (6 action(s))
[written] patched.json  (lint findings: 15 -> 3)     # grade: B (72) -> A (91)
```

Everything is `--json`-able and CI-gateable (`--max-menu-tokens`, `--diff --max-growth`,
`--fail-on`; a composite [GitHub Action](action.yml) and a [Spectral ruleset](spectral/README.md)
ship in-repo). Full CLI docs: [`lap/README.md`](lap/README.md).

## What the measurements show

**[The leaderboard](https://lcrazyblindl.github.io/lap/)** — 50 real public APIs, refreshed
monthly. Their naive agent menus total **~11.2M tokens**; rendering the *same operations*
compactly recovers **~82%** on average (lazy tool-search: ~86%). Nobody ships the compact form.

| API | naive menu (bucket A) | LAP compact | saved |
| --- | ---: | ---: | ---: |
| Xero Accounting | 4,041,667 | 7,800 | **+99%** |
| Kubernetes | 2,864,414 | 45,015 | **+98%** |
| Amazon EC2 | 1,046,048 | 86,031 | **+92%** |
| _…47 more, sortable, with history_ | | | |

**Real tools, not just our own variants** — the same accounting pointed at the ecosystem,
live, with billed calls where it matters:

- **3 real OpenAPI→MCP generators** all emit menus *heavier* than the naive baseline, 5–28×
  heavier than compact ([GENERATORS](docs/GENERATORS.md), [MCP-SERVERS](docs/MCP-SERVERS.md)).
- **20 popular published MCP servers, scored as installed** — menus from 42 to **21,411**
  tokens per session (Notion's official server, grade F); ~64k tokens if you connect them all,
  before the first user message ([MCP-LEADERBOARD](docs/MCP-LEADERBOARD.md), refreshed monthly,
  incl. a grade cross-check against another grader).
- **Anthropic's Tool Search: verified live** — ~90% billed-token cut on a real 290-op API,
  server-enforced ([TOOL-SEARCH](docs/TOOL-SEARCH.md)). **Their code-execution: disputed on
  our workload** — heavier than naive in 5/5 repeats; its saving is *behavioral*, not
  structural ([CODE-EXEC](docs/CODE-EXEC.md)).
- **A third-party optimizer's self-reported % was mismeasuring** — root-caused in its own
  source: character counts with an asymmetric formula ([MCP-COMPRESSOR](docs/MCP-COMPRESSOR.md)).
- **Compression doesn't cost accuracy** — a 500-run live matrix (2 models × 10 tasks × 5
  forms): every compressed form matched or beat the naive menu; the *cheapest correct answer*
  turned out to be model-dependent ([validation.md](experiments/token-bench/validation.md)).

Results that don't flatter the thesis ship as prominently as the ones that do — the
verified/disputed registry of the field's headline claims is [docs/FIELD.md](docs/FIELD.md),
and the standard objections are priced out in [CACHE-ECONOMICS](docs/CACHE-ECONOMICS.md)
("isn't it cached?") and [TOKENIZERS](docs/TOKENIZERS.md) ("whose tokens?").

## Who it's for

- **You ship an API or MCP server** → `lap score`/`lint`/`fix` give you a number, the
  violations behind it, and a patch; the Action gates PRs that bloat the menu; `lap badge`
  shows the grade in your README.
- **You build agents** → `lap stack` audits what your own config burns; the leaderboard is
  due-diligence before wiring up an API.
- **You're choosing between MCP / Tool Search / code-execution / a query DSL** → this repo
  measured all of them on the same tasks with the same accounting
  ([token-bench](experiments/token-bench/README.md), [LANDSCAPE](docs/LANDSCAPE.md)).
- **You design API conventions** → the [LAP profile](profile/llm-api-profile.md) is the rule
  set behind the linter; every rule cites its measurement, including the two that earned
  honest caveats.

## Project map

- [`lap/`](lap/README.md) — the pip-installable toolkit (start here).
- [`profile/`](profile/llm-api-profile.md) — the LAP profile: measured conventions, L1–L4 levels, the grade formula.
- [`experiments/`](experiments/token-bench/README.md) — the benchmark ([pet-zoo](pet-zoo/README.md) testbed) + every measurement script behind the docs (leaderboard, spec-#2808 simulation, cache economics, tokenizer matrix, …).
- [`docs/`](docs/LEADERBOARD.md) — the receipts: leaderboard (+ its [MCP-server twin](docs/MCP-LEADERBOARD.md)), real-tool tests, [FIELD](docs/FIELD.md) claims registry, [SPEC-2808](docs/SPEC-2808.md) input for the MCP spec discussion.
- [`spectral/`](spectral/README.md) — the lint rules for existing Spectral setups.
- [`ROADMAP.md`](ROADMAP.md) — the full staged history and what's next.

## Status & contributing

**0.5.x**, pre-1.0, actively maintained, MIT — no telemetry, no paid tier, no company. Issues
and PRs welcome: [CONTRIBUTING.md](CONTRIBUTING.md) covers dev setup and the house policies
(vendor neutrality, claims need receipts), and there's a **"Score my API"** issue template —
disputes of our numbers are explicitly invited.
