# LAP Roadmap — token-efficiency layer for the agentic web

**What this is:** the staged plan for **LAP**, an open, neutral toolkit that measures
the token cost of agent-facing APIs (A/B/C buckets) and scores them against the LAP
profile. Positioned as an open, reproducible **efficiency-measurement + guidance layer** —
complementary to MCP/NLWeb (and to the token-efficiency tools it credits), **not** a rebuild
of gateways/auth/discovery
(those are already covered by Microsoft NLWeb, AWS/Hypr MCP gateways, NIST/IETF auth).

**How to resume (future sessions):** read this file, find the **▶** stage, do it, tick
it `[x]`, move **▶** to the next stage, and update the `lap-roadmap` memory pointer.
Load only the files that stage needs — the user has a limited token budget, so this is
built for stop/resume, one bounded session per stage.

## Reuse (don't rebuild)

`experiments/token-bench/`: `spec_source.py` (the `Op` IR, `list_operations`,
`inline_refs`), `tokens.py` (count backends), `variants/*`
(openapi_full / compact_sig / numbered / code_exec / odata_query / mcp_fastmcp),
`query_engine.py`, `sandbox.py` + `sandbox_runner.py`, `run_bench.py`;
`profile/llm-api-profile.md` (the LAP profile draft). Run with `./.venv/Scripts/python.exe`.

## Stages

- [x] **Stage 0 — Persist the plan.** `ROADMAP.md` + `lap-roadmap` memory pointer +
  repo `CLAUDE.md` link. _Done: a new session resumes from the pointer alone._
- [x] **Stage 1 — Landscape & positioning** → [`docs/LANDSCAPE.md`](docs/LANDSCAPE.md).
  Done: June-2026 landscape (NLWeb, llms.txt, MCP gateways, NIST/IETF auth, efficiency
  patterns) mapped with sources; LAP positioned as the efficiency-measurement niche.
- [x] **Stage 2 — Generalize the scorer beyond pet-zoo.** Done: standalone [`lap/`](lap/)
  toolkit — `python -m lap.score <openapi-file-or-url>` loads any spec, normalizes it
  (`lap/openapi_ir.py`), renders openapi_full / compact_sig / numbered menus
  (`lap/menu.py`) and reports bucket-A tokens + reduction. Verified on a non-pet-zoo
  Bookstore spec (418 → 205 compact). B/C still need per-API tasks (token-bench).
- [x] **Stage 3 — Score real ecosystem targets.** Done: `lap/mcp_form.py` adds a
  real-MCP baseline via `FastMCP.from_openapi`; `lap score` now includes the real MCP
  menu (+ output-schema figure). Verified end-to-end on the **live Swagger Petstore**
  (19 ops): real MCP 2226 (3844 w/ output schemas) vs compact 415 — the toy finding
  holds in the wild (real MCP is heavier than the naive baseline).
- [x] **Stage 4 — Faithful tokens + success check (mechanism only).** The live check
  defaults to a cheap model (`claude-haiku-4-5`) + a `--quick` subset to bound spend;
  both token-bench and `lap` use faithful `count_tokens` automatically when a key is set.
  **Closed by choice:** no API key available (Pro ≠ API), so faithful/live numbers were
  skipped; the budget-safe mechanism is committed and runs anytime via
  `ANTHROPIC_API_KEY=... python experiments/token-bench/run_bench.py --live --quick`.
- [x] **Stage 5 — LAP profile v1.0 + linter.** Done: profile promoted to v1.0;
  `lap/lint.py` + `python -m lap.lint <openapi>` flags D3 / R1 / R2 / R3 / W1 / E1 / A1
  with rule citations — verified on the live Swagger Petstore (6 warnings, 10 suggestions).
- [x] **Stage 6 — Package & share.** Done: `pyproject.toml` (core deps httpx+tiktoken,
  extras `[mcp]`/`[faithful]`) + `lap/cli.py` console script — `pip install -e .` gives a
  `lap` command; `lap score` / `lap lint` verified as installed commands. **Remaining manual
  step (owner's):** publish to PyPI + a GitHub release to make it `pip install lap-score`.

## Stages — v0.2 (planned improvements; same stop/resume model)

Ordered: trust foundation → robustness → value features → (last) the key-needing live
validation. Each is one bounded session. `[no key]` = doable without an API key.

- [x] **Stage 7 — Tests + CI + LICENSE.** Done: `tests/test_lap.py` (8 tests, green) over
  IR / menu / lint / tokens / score on the bookstore spec; `.github/workflows/ci.yml` (pytest +
  smoke `lap lint`); MIT `LICENSE`; `dev` extra + CI badge in README.  `[no key]`
- [x] **Stage 8 — Robustness on real specs.** Done: rewrote `lap/openapi_ir.py` to handle
  `allOf`/`oneOf`/`anyOf`, `$ref` in params/requestBodies/responses, path-item-level
  parameters, OpenAPI 3.1 `type` lists, external `$ref`s (left intact), and YAML input. Added
  `lap/examples/gnarly.openapi.json` (3.1) + 4 regression tests (now 12 passing); live Petstore
  unregressed.  `[no key]`
- [x] **Stage 9 — Estimate bucket C from response schemas.** Done: `lap/estimate.py` synthesizes
  an instance from each success-response schema, counts its tokens, and (for arrays) multiplies
  by `--page-size`; `lap score` now prints an "Estimated result size (bucket C)" table flagging
  heavy lists (Petstore `GET /pet/findByStatus` ~785 tok/page vs ~39 for objects). +1 test (13).  `[no key]`
- [x] **Stage 10 — `--json` output + CI gate.** Done: `lap score`/`lap lint` take `--json`
  (structured output); `lap score --gate-form F --max-menu-tokens N` and `lap lint --fail-on
  warn` set a non-zero exit code; rule suppression via `--ignore R2,A1` or a `./.lapignore`
  file; GH Action snippet in the README. Exit codes verified; +2 tests (15).  `[no key]`
- [x] **Stage 11 — `tool_search` menu form.** Done: `lap/menu.py` `tool_search` (fixed
  `search_tools`+`call_tool` + name index; schemas on demand) added to `lap score`. Its bucket A
  is ~flat in #ops: Petstore 1740→207 (−88%), a synthetic 120-op API 3722→624 (−83%), beating
  even compact at scale. +1 test (16). `[no key]`
- [x] **Stage 12 — Score live MCP/NLWeb endpoints.** Done: `lap/mcp_client.py` + `lap score
  --mcp-url <url>` connects via a FastMCP MCP client, lists advertised tools, and reports
  mcp_live vs compact/tool_search. Verified end to end against a local HTTP MCP server (6 tools,
  mcp_live 422 → compact 69 / tool_search 149) + an in-memory test. +1 test (17).  `[no key]`
- [x] **Stage 13 (LAST) — Live success + faithful validation.** Done with a real API key:
  faithful `count_tokens` (anthropic backend) reran token-bench — **same ordering** as the
  tiktoken approximation, ~60% higher absolute (e.g. openapi_full 2665, compact 634, real MCP
  2752/6418, code 555). `--live --quick` on Claude Haiku: **every variant answered correctly**
  (compression doesn't cost accuracy) while compact/code/query spent ~3–4× fewer total tokens;
  the T5 DSL-gap shows live (odata 2995 vs code 1735). Also fixed a latent empty-content bug in
  token-bench `tokens.py` that the faithful run surfaced. `results.md` now holds faithful+live.

## Stages — v0.3 (post-validation hardening + reach)

Same stop/resume model. `[key]` = needs `ANTHROPIC_API_KEY` (read the User-scope value into the
command, or restart Claude Code so all tools inherit it).

- [x] **Stage 14 — Rename + rebrand to `lap`.** _(Done 2026-06-30 — owner renamed the repo on
  GitHub; agent pointed `origin`, the CI badge, and `pyproject` `[project.urls]` at `/lap`.)_
  README title/tagline + `CLAUDE.md` were already rebranded to `lap` (LLM-API Profile). The local
  folder stays `LLMToHTTP`; GitHub auto-redirects the old URL.  `[no key]`
  - **To let the agent do the rename itself, the owner provides ONE of:** (a) install GitHub CLI
    + `gh auth login` (one-time, interactive; then the agent runs `gh repo rename lap` + `gh repo
    edit --description ...`); (b) a GitHub token in env `GH_TOKEN` at User scope (classic `repo`
    scope, or fine-grained Administration: write) — never pasted in chat — then restart so the
    process inherits it, and the agent renames via the REST API. Probed 2026-06-30: `gh` absent,
    no `GH_TOKEN`/`GITHUB_TOKEN`. Zero-credential fallback: owner renames in the web UI and the
    agent flips the refs (no auth needed for that part).
  - **Naming decision (owner asked to record):** keep the repo name **`lap`** — the umbrella
    *toolkit*, not any one part — and let the **description enumerate all four deliverables incl.
    the benchmark**, so the name matches the full implementation (not `lap-profile`/`lap-bench`,
    which would privilege one part). Canonical description to apply at rename: **"lap — measure &
    improve the token-efficiency of agent-facing APIs (OpenAPI & MCP): scorer, linter, the LAP
    profile, and a reproducible token benchmark."** README tagline already lists all four.
- [x] **Stage 15 — Honest validation.** Done. (a) The profile no longer says "validated" — it
  reports a measured success rate with caveats. (b) Ran a live **success-rate matrix** (new
  `run_bench.py --matrix` / `live_runs.run_matrix`): Claude Haiku, one task per category × **k=3
  repeats**, `numbered` included → [`validation.md`](experiments/token-bench/validation.md).
  **Compression did not cost accuracy:** `numbered`/`code_exec`/`odata_query` 15/15, `compact_sig`
  14/15, naive `openapi_full` *last* at 13/15 (both misses on the aggregate-count task), while the
  compact/code/query forms used ~1.4–4× fewer total tokens. Profile updated with this evidence +
  caveats (one cheap model, k=3 noisy at n=3, toy API). The key was read from User scope per-command
  (process didn't inherit it). _sonnet pass + ≥2 tasks/category left as cheap follow-ups._  `[key]`
- [x] **Stage 16 — Grouped, ≥2-per-category benchmark tasks.** Done: `tasks.py` now carries a
  `category` per task and has **10 tasks across the 5 categories** (write / aggregate-read /
  peek-read / multi-step / beyond-DSL), ≥2 each; `run_bench` prints a **per-category averages**
  table (mean A+B+C vs baseline) ahead of the per-task tables; `results.md` regenerated (the prior
  faithful+live run kept as `results-faithful.md`). +4 bench tests (`test_bench_tasks.py`, guarded
  by `importorskip("fastapi")` so package CI skips it) — full suite 21 passing. The DSL gap holds
  as a category average: code_exec ~92% on beyond-DSL vs odata_query ~78% (it must project all
  rows for avg/argmax over a computed property).  `[no key]`
- [x] **Stage 17 — Fuzz on a real-spec corpus.** Done: `experiments/fuzz_corpus.py` runs the whole
  parser surface (IR + all menus via `score` + `lint` + bucket-C estimate) over APIs.guru. **175+
  real specs across two random seeds + a curated gnarly set (Stripe, GitHub 845 ops, Kubernetes,
  EC2 1182 ops, Jira, Azure, googleapis compute) → zero crashes** — the named long-tail
  (`discriminator`, webhooks, deep nesting, 1000+ ops) was already crash-robust (Stage 8). The real
  gap was **degenerate output, not crashes**: Swagger/OpenAPI **2.0** specs (~25% of the corpus, e.g.
  kubernetes/azure) reported every op as `returns=void`, empty body, no W1/R* — because 2.0 puts the
  response schema under `response.schema` (not `content`) and the body in an `in: body` param; some
  3.0 specs (EC2) were void too (responses are `text/xml`, not `application/json`). Fixed in
  `openapi_ir.py` (additive, 3.x unchanged): a JSON-ish **media-type fallback** (`*+json`/form/xml),
  **2.0 response `schema`**, **2.0 `in: body` params**, type-on-parameter, and `#/definitions` type
  blocks. Regression sample `lap/examples/swagger2.json` + 4 tests (25 passing); k8s went from 0
  findings to 284, EC2 returns 0→1070.  `[no key]`
- [x] **Stage 18 — Efficiency leaderboard.** Done: `experiments/leaderboard.py` scores real public
  APIs from APIs.guru and writes [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md) — **20 APIs** ranked by
  naive agent-menu (bucket A) cost: Kubernetes 2.82M tokens, EC2 606k, Jira 346k, Stripe 232k, …;
  naive menus total ~4.9M, `compact_sig` saves ~86% on average and `tool_search` ~96% (mostly
  still on the table for agent front-ends). Surfaced + fixed a real crash on the way: tiktoken
  raised on the literal `<|endoftext|>`
  in OpenAI's spec — `lap/tokens.py` now encodes with `disallowed_special=()` (+regression test, 25
  passing).  `[no key]`
- [x] **Stage 19 — Ship it. FULLY RELEASED, 2026-07-01.** Artifacts: `CHANGELOG.md` (0.3.0,
  folded in the v0.4 real-tool findings before cutting the release), version bump `pyproject`
  `0.1.0 → 0.3.0` + classifiers + Changelog/Leaderboard urls, a composite marketplace **GitHub
  Action** (`action.yml`), and [`RELEASING.md`](RELEASING.md). **PyPI:** `python -m build` →
  `twine check` (both PASSED) → `twine upload` — **`lap-score` 0.3.0 is live**:
  https://pypi.org/project/lap-score/0.3.0/, verified for real in a fresh throwaway venv (`pip
  install lap-score` + `lap score <spec>` worked exactly as documented). **GitHub:** tag `v0.3.0`
  pushed; `gh release create v0.3.0` published (both dist files attached) at
  https://github.com/lCrazyblindl/lap/releases/tag/v0.3.0 — unblocked mid-session when the owner
  ran `gh auth login` themselves (the agent's shell had a stale PATH cached from before `gh` was
  installed; refreshing `$env:Path` from the registry inside the command found it). Also fixed the
  repo's GitHub description to the canonical one now that `gh repo edit` was available. **Only
  remaining, optional, UI-only step:** "Publish this Action to the Marketplace" from the release
  page (owner action — no `gh` command for this one).  `[owner action, optional]`

## Stages — v0.4 (measure real tools, not our own)

New direction (owner's push): a benchmark should measure **real, third-party artifacts**, not
only our own interface generators. Reproducible scope = **OSS tools + real Anthropic API
features** (we have a key); commercial hosted products (Speakeasy Gram, Stainless, StackOne,
Cloudflare Code Mode) are **cited, not run**. Our own variants stay as a controlled demo of the
*principle*; this track shows it holds against real tools. Same stop/resume model. Inventory of
candidates: [`docs/REAL-TOOLS.md`](docs/REAL-TOOLS.md).

- [x] **R1 — Inventory the reproducible real tools.** Done: [`docs/REAL-TOOLS.md`](docs/REAL-TOOLS.md)
  maps OSS OpenAPI→MCP generators (FastMCP + `openapi-to-mcp` / `openapi-mcp` / cnoe
  `openapi-mcp-codegen`), a real OSS optimizer (**Atlassian `mcp-compressor`**), locally-runnable
  real MCP servers (`uvx` reference servers; Docker `github`/`filesystem`), and the real Anthropic
  features (Tool Search, code execution) — with an explicit account-gated exclusion list.  `[no key]`
- [x] **R2 — Real generator shoot-out (bucket A).** Done: [`docs/GENERATORS.md`](docs/GENERATORS.md)
  + [`experiments/generators.py`](experiments/generators.py) score **three real** OpenAPI→MCP
  generators on the live Swagger Petstore (19 ops): openapi-to-mcp **2130**, FastMCP **2226**,
  openapi-mcp **4274** (→ **11756** with response schemas) — **every one heavier than the naive
  baseline (1740), and 5–28× heavier than a compact menu (415)**. No real generator ships the
  compact form → the savings are unclaimed by the ecosystem (mirrors "real MCP is heavier", now
  across 3 real tools). Honest caveat: the generators have conflicting pinned deps, so they were
  measured across two venvs (they broke pet-zoo once; env restored, 25 tests green); `generators.py`
  skips absent generators with a note.  `[no key]`
- [x] **R3 — Score the live MCP ecosystem.** Done: [`experiments/mcp_servers.py`](experiments/mcp_servers.py)
  connects over **stdio** to three real published reference servers and scores their advertised menus
  → [`docs/MCP-SERVERS.md`](docs/MCP-SERVERS.md): mcp-server-git 12 tools **1418**→153 (−89%),
  mcp-server-fetch **290**→28 (−90%), mcp-server-time **283**→31 (−89%). Even reference servers pay a
  fixed menu tax a compact rendering cuts ~89%; cites the official GitHub MCP (~94 tools/~17.6k) as
  the heavy real example (Docker daemon was down, so Docker-only servers weren't run). Servers ran
  from an isolated venv (`MCP_SERVER_PY`).  `[no key / Docker]`
- [x] **R4 — End-to-end on a real live API.** Done: [`experiments/real_api_matrix.py`]
  (experiments/real_api_matrix.py) runs the live matrix on the **hosted Swagger Petstore** — real
  HTTP execution, Claude Haiku, k=3 — comparing our naive/compact menus and the **real FastMCP**
  menu → [`validation-real.md`](experiments/token-bench/validation-real.md). **Compression didn't
  cost accuracy — it helped:** naive `openapi_full` *failed* the count task **0/3** (heaviest +
  least reliable), while `compact_sig` and **real FastMCP** were **3/3**, and compact used ~half the
  tokens of naive. Closes the pet-zoo toy gap. Caveats: 1 cheap model, k=3 (noisy), 2 tasks, 1 API.  `[key]`
- [x] **R5 — Real Tool Search head-to-head.** Done, no beta header needed (GA feature) —
  [`experiments/tool_search_real.py`](experiments/tool_search_real.py) →
  [`docs/TOOL-SEARCH.md`](docs/TOOL-SEARCH.md), plus a 4th form added to the Petstore live matrix
  ([`experiments/real_api_matrix.py`](experiments/real_api_matrix.py) →
  [`validation-real.md`](experiments/token-bench/validation-real.md)). **At real scale (live
  DigitalOcean, 290 real ops): real Tool Search billed 4789 input tokens vs 50617 for the identical
  schemas without `defer_loading` — a real, live, ~90% cut**, isolating just the mechanism (same
  question, same model, same tool schemas). **At small scale (live Petstore, 19 ops): real Tool
  Search cost *more* than `compact_sig`/real FastMCP** (11728 vs 5418/7206 on one task) — matches
  Anthropic's own "10+ tools" guidance, now empirically confirmed both ways on real APIs. Real find:
  the free `count_tokens` endpoint **rejects any request containing a server tool** (400) — real
  Tool Search's bucket A can only be measured via a live, billed call, unlike every other row in
  this repo. Also real: Kubernetes (821 ops) was tried first and rejected — its naive $ref-inlined
  schema is ~4.2M faithful tokens, and since *every* tool's full definition (deferred or not) must
  still be sent in the request, even `defer_loading` can't get an oversized corpus under a model's
  context window (Haiku 4.5: 200K) — a real, useful limit, not just a documented one.  `[key]`
- [x] **R6 — Real code-execution head-to-head.** Done, no beta header for the tool itself (only
  Files API needs `betas=["files-api-2025-04-14"]`) —
  [`experiments/code_exec_real.py`](experiments/code_exec_real.py) →
  [`docs/CODE-EXEC.md`](docs/CODE-EXEC.md). Used `code_execution_20250825` (the version Haiku 4.5
  supports) on the exact task Stage 15 already validated, so the new real number sits beside
  already-real naive (6121 tok) and our own `code_exec` (1636 tok) numbers. **A genuinely humbling,
  honest result:** real code-execution totaled **15613 tokens** — *heavier* than both. The
  content-block trace shows why: the model **viewed the uploaded file first** (re-entering the raw
  data into context, same as a naive fetch), then needed a retry to get the right path. This is a
  real, structural finding: **Tool Search's saving is enforced by the server** (`defer_loading`
  worked regardless of model behavior, R5) while **code-execution's saving is only behavioral** —
  it holds only if the model's own code never prints the raw data; our sandbox enforces that
  structurally (only `result` can leave the subprocess), real code-execution doesn't. Caveat: k=1,
  one model, one task — noisy, not a claim that real code-execution is inherently worse.  `[key]`
  Neither sandbox can call a *live* external API (no internet in Anthropic's container; ours is
  hard-wired to an in-process client) — a live-API-backed comparison is out of scope, would need
  its own security review to extend our sandbox's network access.
- [x] **R7 — Envelope-aware bucket C.** Done: `lap/estimate.py` detects a list wrapped in an
  envelope object (`_find_envelope_key` — Stripe/JSON:API `{"data":[...]}`, k8s `{"items":[...]}`,
  OData `{"value":[...]}`, preferring conventional names deterministically) and scales it to a
  full page **with its sibling fields kept**, instead of scoring it as a tiny "object". Regenerated
  [`docs/LEADERBOARD.md`](docs/LEADERBOARD.md): **15 of 20** real APIs' heaviest-result estimate
  changed, several substantially (Kubernetes 1303→**7613**, Stripe 1588→**15868**, DigitalOcean
  616→**12244**, Notion 412→**6118**) — the previous numbers were undercounting real, enveloped
  responses. +4 tests (29 passing).  `[no key]`
- [x] **R8 — Reframe the story honestly.** Done. `profile/llm-api-profile.md`: rule **D2** (Tool
  Search) now cites our own real ~90% verification alongside the vendor number, and explicitly
  notes it's *server-enforced*; rule **X1** (code-execution escape hatch) now carries an explicit
  caveat that its saving is **behavioral, not structural** — cites the real R6 counter-example
  (cost more than naive on one run) and contrasts it with D2's server-enforced guarantee.
  `docs/LANDSCAPE.md` §5 (Efficiency patterns): added that we tested two of Anthropic's own
  features live rather than only citing headline numbers — Tool Search held up, code-execution
  didn't on one run — with the general lesson (structural vs behavioral savings). README's v0.4
  bullet already stated the R6 counter-example plainly (done in the R6 commit); left as-is.
  _Done: docs updated, "ours vs real" kept explicit, the R6 counter-example is not buried._  `[no key]`

Recommended order: **R1 → R2 → R4 → R3 → R7 → R5 → R6 → R8**. **All of v0.4's numbered stages
(R1–R8) are now done.**

## Stages — v0.5 (deepen the real-tool track; finish the toolkit backlog)

Post-release (0.3.0 is live on PyPI + GitHub). Same stop/resume model. `[key]` = needs
`ANTHROPIC_API_KEY`; `[no key]` = doable without one.

- [x] **S1 — Re-run R6 (code-execution) with repeats.** Done. Re-ran
  `experiments/code_exec_real.py` with k=5 against Claude Haiku 4.5, and instrumented each run
  for exec-attempt count + failed-attempt detection (not just "did it view the file", which
  turned out not to be the real driver). **Result: not a fluke — a confirmed pattern.** All 5/5
  repeats came in above the naive baseline (mean 17863 vs. naive 6121, ours 1636), 5/5 correct.
  The verified mechanism: every run needed 2–4 `bash_code_execution` attempts because the model
  guessed the wrong sandboxed file path on its first try and had to retry — each retry re-sends
  the growing turn history, which is what inflates billed tokens. Our own sandbox has no
  equivalent failure mode (an injected client object can't be given a wrong path). Updated
  `docs/CODE-EXEC.md`, `profile/llm-api-profile.md` (rule X1), `docs/LANDSCAPE.md` §5, and
  `README.md`'s real-tool table to state "5/5, confirmed pattern" instead of "k=1, noisy."
  `[key]`
- [x] **S2 — Test `mcp-compressor` (Atlassian), a third real compression mechanism.** Done.
  Wrapped two of R3's real reference servers with the real, published (PyPI `mcp-compressor`,
  Rust-backed) stdio proxy at all 4 compression levels: `mcp-server-time` (2 tools, small) and
  `mcp-server-git` (12 tools, mid-size). **Scale amplifies the win** — our own tokenizer measured
  real savings at both scales (+12% small, +67% big at `medium`), bigger menus compressing more.
  **Genuine cross-check discrepancy found:** the tool's own self-reported startup-banner
  percentage disagreed with us on the small server — it claimed `medium` cost *more* than
  original (103.8%) where our bucket-A count of that exact same output measured a real, if
  modest, saving (+12%). Flagged honestly rather than smoothed over (likely a different internal
  metric, e.g. raw bytes vs our tokenizer — not confirmed). Wrote `docs/MCP-COMPRESSOR.md`;
  updated `docs/REAL-TOOLS.md` and README's real-tool table/links.  `[no key]`
- [x] **S3 — Leaderboard expansion, 20 → 40+ real APIs.** Done. Extended
  `experiments/leaderboard.py`'s `CURATED` list to 50 candidates, each verified present in
  APIs.guru's live directory first (dropped unresolvable guesses rather than leaving silent
  skips); all 50 scored cleanly. New heaviest entry: Xero Accounting (4,039,605 naive tokens,
  even heavier than Kubernetes). Totals across 50: **10,426,548 naive tokens**; `compact_sig`
  **+80%** avg saved, `tool_search` **+82%** avg (and, now visible at this scale, genuinely
  *negative* on 1-3-op APIs like NASA APOD/ClickUp/1Password — tool_search costing more than
  naive — a live illustration of the "not worth it below ~10 tools" caveat). Fixed a cosmetic
  bug the expansion surfaced: negative `save_search`/`save_compact` percentages rendered as
  `+-51%` (double sign) in the table; added a `_signed()` helper. Updated README's leaderboard
  sample table/count/totals.  `[no key]`
- [x] **S4 — `lap score before after` diff mode.** Done. Added `score.diff(before, after)`:
  menu (bucket A) token delta per interface form (`openapi_full`/`compact_sig`/`numbered`/
  `tool_search`), plus which LAP lint findings were newly introduced or fixed — matched by
  `(rule, where)` so wording changes don't count as a different finding. Wired into the CLI as
  `lap score --diff <before> <after>` (human + `--json`), and a CI gate `--max-growth` (reuses
  `--gate-form`; exit 1 if that form's menu grew by more than N tokens). +3 tests (32 passing).
  This is real, shipped-package code (not just docs/experiments) — added an `[Unreleased]`
  section to `CHANGELOG.md` for it since 0.3.0 is already tagged. Updated `lap/README.md`.
  `[no key]`
- [x] **S5 — estimate-C realism.** Done. `example_instance()` now checks a schema for a real
  `example` (OpenAPI 3.0) or `examples[0]` (JSON Schema 2020-12 / OpenAPI 3.1) value first,
  before any synthetic placeholder or even `enum`/`allOf`/`oneOf` handling — real data an API
  author wrote down beats a guess, unconditionally. The synthetic string placeholder's length is
  now a `string_len` parameter (`estimate()`/`example_instance()`) and a CLI flag
  (`lap score --string-len N`, default 6 = unchanged, since there's no universally "correct"
  default). +5 tests (37 passing). **Real, substantial leaderboard impact**: of 48 comparable
  rows, **41 grew, 1 shrank (EC2 - its `enum[0]` was longer than its real `example`), 6 were
  unchanged** (no examples in those schemas); the leaderboard's total heaviest-result estimate
  rose **~41%** (482,795 → 681,830 tokens) — the placeholder-only estimate had been undercounting
  real payload sizes wherever specs actually documented example values. Regenerated
  `docs/LEADERBOARD.md`, updated its methodology note, `CHANGELOG.md` `[Unreleased]`, and
  `lap/README.md`.  `[no key]`
- [ ] **S6 — Broader validation matrix.** _(superseded → carried into v0.6 as **N8**, unchanged
  in substance)_  `[key]`
- [ ] **S7 — CONTRIBUTING.md + issue templates.** _(superseded → v0.7 Track C backlog)_  `[no key]`
- [ ] **S8 — Profile L0 "be-discoverable" rule + NLWeb endpoint scoring.** _(superseded → v0.7
  Track S backlog)_  `[no key]`

Recommended order was **S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8**; after S5 the plan was re-drawn
from a fresh July-2026 landscape re-check (below), and the S6–S8 tail was folded into it.

### Further backlog (unscheduled, key-free)
**Shipped after the v0.3 stages:** the LAP rules as a **Spectral ruleset**
([`spectral/`](spectral/README.md), executed + asserted in CI, verified locally on Spectral
6.11.0 = same 15 findings as `lap lint`); the leaderboard gained a **bucket-C** (heaviest
result) column. _(The two honest gaps that surfaced — real-API end-to-end validation, and
envelope-aware bucket C — became v0.4 **R4** and **R7**, both now done.)_
Still open, unscheduled: a short **Related work / credit** note in the README; caching economics
(first-call vs amortized A); a bucket-B estimate in `lap score` (currently only measured in
token-bench); lint auto-fix (emit a suggested compact manifest); GitHub's official MCP server
(~94 tools/~17.6k, cited in R3 but never scored — Docker daemon was down; revisit if it comes
up); a second real API for Tool Search/code-execution to check R5/R6 generalize beyond
DigitalOcean/pet-zoo.

## Stages — v0.6 (drafted 2026-07-06 from a fresh landscape re-check)

**Why a new plan.** A July-2026 re-check of the field found: (1) the problem LAP measures went
mainstream — "MCP context bloat" is now called an enterprise deployment blocker, Tool Search went
GA (Feb 2026), "Code Mode" is everywhere (Cloudflare/Anthropic/Bifrost/StackOne); (2) the MCP spec
itself has an open issue ([#2808](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2808))
about tool-schema token overhead, proposing tiered schemas / versioning / namespacing — with no
measurement companion; (3) two direct competitors appeared, both far earlier-stage than LAP —
**mcpx** (A–F linter, live-MCP-only, ~2 stars, opaque tokenizer) and **AgentDX** (18 static rules
+ LLM-judged DX score, early alpha); (4) the recognized MCP benchmarks (MCPMark, MCP-Bench,
MCP-Atlas) all measure *accuracy/capability*, not token cost; (5) a StackOne survey of the 4
optimization approaches explicitly notes **no neutral open-source measurement/scoring tooling
exists** — which is exactly LAP. Conclusion: LAP's niche is validated and still open, but LAP is
invisible and its MCP-side ergonomics lag its OpenAPI side. v0.6 = close the product gaps that
make LAP demo-able and sticky, then take the public position while it's unclaimed.

Same stop/resume model, one bounded session per stage. `[key]` / `[no key]` as before.

- [x] **N1 — `lap stack`: score YOUR installed MCP stack.** Done. New `lap/stack.py` +
  `lap stack` subcommand: reads the agent's own config (Claude Code project `.mcp.json`,
  Claude Code `~/.claude.json`, Claude Desktop `claude_desktop_config.json` incl. macOS/Linux
  paths, or an explicit path to any JSON with an `mcpServers` map; `${VAR}` env expansion),
  connects to every listed server (stdio + HTTP, one shared event loop, per-server `--timeout`),
  and totals bucket A: *"your agent pays N tokens before you type a word."* Unreachable servers
  (missing binary/creds) become annotated rows, not crashes. What-ifs: per-server compact +
  a stack-level `tool_search` counted honestly (fixed search/call tools paid **once** across the
  whole stack + a cross-server name index). `--only`, `--json`. Verified end-to-end on a config
  with 2 real reference servers + 1 dead one (recreated `.venv-srv`): time 283 + git 1418 =
  **1701 tokens** naive vs 184 compact / 193 stack tool_search (**+89%**); auto-discovery ran
  clean against the owner's real (empty) Claude configs. +3 tests (tests/ 36, full suite 40).
  README + lap/README + CHANGELOG `[Unreleased]` updated.  `[no key]`
- [x] **N2 — Composite LAP grade + badge.** Done. New `lap/grade.py`: three documented
  sub-scores — **menu** (naive tokens/op, weight 0.45), **result** (heaviest estimated response,
  0.30; skipped+renormalized when nothing is estimable), **hygiene** (weighted lint findings/op,
  0.25) — log-scaled with all constants in one place, composite → letter (A ≥85 … F). Grade is
  always printed by `lap score` (human + `--json`); `lap badge <spec> -o file` writes a
  shields.io endpoint JSON; the composite Action gained `badge-path`. Formula documented in the
  profile ("The LAP grade" section) with a calibration snapshot over the cached leaderboard
  corpus: sensible spread on real APIs — Spotify/LaunchDarkly **B**, SQS/Postman/SendGrid **C**,
  GitHub/DynamoDB/Vimeo **D**, Google Drive **F (17)**; no sampled API reached **A** (needs real
  pagination/projection/error discipline, by design). Our own README now carries the badge for
  the bundled Bookstore example — an honest **B (72)**. +4 tests (tests/ 40, full suite 44).
  `[no key]`
- [x] **N3 — Lint parity for MCP servers.** Done. `lap lint --mcp-url <url>` / `--mcp "<stdio
  command>"` lints a live server's advertised tools: D3 carries over; new **M-rules** — M1
  missing/short tool description (warn), M2 undescribed input parameters (info), M3 heavy tool
  definition >~600 tokens (warn; the spec-#2808 pathology), M4 params without a `required` list
  (info) — documented in the profile ("MCP tools — bucket A"). Prints the composite grade
  (menu + hygiene; result sub-score skipped — MCP listings don't declare response shapes).
  `--ignore`/`.lapignore`/`--fail-on`/`--json` all work unchanged. Real end-to-end:
  **mcp-server-git B (71)** — 2 tools with <20-char descriptions, `repo_path` undescribed in
  11/12 tools; **mcp-server-time A (89)** — clean (the first A, honest contrast). Also fixed en
  route: `keep_alive=False` on stdio transports (kills Windows Proactor teardown noise
  everywhere, incl. `lap stack`) and a real latent crash — the `✓` in "no violations" broke
  cp1251 Windows consoles. +2 tests (tests/ 42, full suite 46).  `[no key]`
- [x] **N4 — Bucket-B estimate in `lap score`.** Done. `estimate.estimate_call(spec, op,
  string_len)`: synthesizes a typical invocation — tool name + **required** args (path params
  always, optional query params omitted, request-body `required` list honored, real schema
  examples win here too) — counted in a minimal `{"name":..., "input":{...}}` tool-use envelope;
  a structural lower bound like the C estimate. `lap score` now reports the full **A/B/C** story:
  a new "Estimated call size (bucket B)" line (mean + heaviest call) in human output and
  `estimated_b` in `--json`. Sanity-checked live: Bookstore mean ~18/heaviest PUT 31; Petstore
  mean ~21/heaviest `POST /user/createWithList` 52 — plausible shapes. +3 tests (tests/ 45, full
  suite 49).  `[no key]`
- [x] **N5 — Release 0.4.0. FULLY RELEASED, 2026-07-06.** Ships S4+S5+N1–N4: `lap stack`,
  composite grade + `lap badge` (+ Action `badge-path`), MCP lint (M-rules), bucket-B estimate,
  `score --diff`/`--max-growth`, `--string-len` + real-example preference, Windows fixes.
  **PyPI:** https://pypi.org/project/lap-score/0.4.0/ (twine check PASSED ×2; verified in a
  fresh venv — score/badge/`lint --mcp` all work from the published package). **GitHub:** tag
  `v0.4.0` + release with both dist files:
  https://github.com/lCrazyblindl/lap/releases/tag/v0.4.0. Action examples bumped to `@v0.4.0`.
  Gotcha: PS 5.1 `Set-Content -Encoding utf8` writes a BOM → broke `pyproject.toml` TOML parsing
  until stripped (recipe now in `RELEASING.md`).  `[release creds]`
- [x] **N6 — "State of the field" + claims registry.** Done → [`docs/FIELD.md`](docs/FIELD.md).
  Three tables: (1) measurement/linting tools — lap vs mcpx vs AgentDX vs MCP Inspector vs the
  security scanners, with an honest "what they have that lap doesn't" paragraph; (2) optimizers
  (Tool Search, Code Mode ×3 vendors, mcp-compressor, Speakeasy, response filtering) with
  published claim vs our independent result side by side; (3) a **claims registry** — 10
  widely-quoted numbers each marked ✅ verified-by-us / ≈ plausible-unverified / 🔒 needs-account /
  **⚠ disputed** (two ⚠: Anthropic's 98.7% code-exec number vs our 5/5 heavier-than-naive, and
  mcp-compressor's self-report vs our +12%). Closes with the referee positioning. README project
  map links it; README status bumped to v0.4.0 en route.  `[no key]`
- [x] **N7 — Empirical input to MCP spec issue #2808.** Done →
  [`docs/SPEC-2808.md`](docs/SPEC-2808.md) + [`experiments/spec_2808.py`](experiments/spec_2808.py)
  (51 cached leaderboard APIs + 2 real MCP servers over stdio). **Tiered schemas (proposal 1):
  discovery tier saves mean 85% / median 91% (range 32–100%)** — the issue's 60–70% estimate is
  conservative at real-API scale; net saving at a typical 3-invocation session still ~70%;
  break-even ~177 invoked tools. Caveat measured too: flips negative below ~10 tools (Events API,
  3 tools: −68%) — same shape as our live Tool Search result. **Namespacing/dedupe (proposal 3):
  mean 23% but range −10…94%** — the distribution is the finding: pays on *fat* repeated schemas
  (Kubernetes 94%, Compute 69%, Jira 63%), goes negative on tiny ones (a `$ref` costs more than
  `{"type":"string"}`; CircleCI −10%); and mcp-server-git — which repeats `repo_path` in ~every
  tool — saves ~0%, so repetition alone doesn't pay. Doc includes a ready-to-paste comment
  (owner posts it under their account; recommends a size threshold + small-server opt-in).
  FIELD.md registry row updated to "simulated". `[no key]`
- [ ] **N8 — Validation matrix v2** _(ex-S6)_. Sonnet + Haiku, all 10 grouped tasks, k≈5 →
  expanded `validation.md`; add a **cost-per-correct-answer** metric per form (tokens spent ÷
  successes) — the number that actually matters for buyers. `[key]`
- [x] **N9 — Leaderboard as a living page.** Done. `experiments/leaderboard.py` now also emits a
  static **sortable** page (`docs/index.html`, vanilla JS, no build step), machine-readable
  `docs/leaderboard-data.json`, and a dated monthly snapshot under `docs/leaderboard-history/`
  (`2026-07.json` is the first) — so month-over-month trends stay diffable. **GitHub Pages
  enabled via `gh api`** (main → `/docs`, `.nojekyll` added): **https://lcrazyblindl.github.io/lap/**.
  A monthly cron (`.github/workflows/leaderboard.yml`, 3rd of each month + `workflow_dispatch`)
  regenerates everything and commits as github-actions[bot]. Gotcha: Pages doesn't list
  directories — the page's "history" link points at the GitHub tree instead.  `[no key]`
- [ ] **N10 — Launch write-up.** A data-first post: *"We measured the agent-menu tax of 50 real
  public APIs — 10.4M tokens"* + Show HN / r/mcp drafts; the owner publishes. LAP's biggest gap is
  visibility, and the data is the hook. _Done: `docs/POST.md` ready to paste._  `[no key]`

Recommended order: **N1 → N2 → N3 → N4 → N5 → N6 → N7 → N9 → N10 → N8** (product gaps → release →
public position; the key-needing science stage last, as always).

## Tracks — v0.7+ (unscheduled backlog, drawn from the same landscape re-check)

Pick from these once v0.6 is done (or opportunistically). Grouped by track; each bullet is
roughly one bounded session unless noted.

**Track V — independent verification (the "Consumer Reports" role):**
- GitHub's official MCP server (~94 tools / ~17.6k tokens — the number *everyone* cites): score
  it directly once Docker is available (or via its hosted endpoint + PAT).
- A 2nd/3rd real API for Tool Search + code-execution — do R5/R6 generalize beyond
  DigitalOcean/pet-zoo?
- Reproduce one vendor code-mode claim end-to-end with OSS parts (e.g. Bifrost's 92.8% at 508
  tools) — verified or not-reproducible, either result is a finding.  `[key]`
- Root-cause the mcp-compressor self-report discrepancy (bytes vs tokens?) and file an upstream
  issue — turns a finding into an ecosystem contribution.
- Live A/B of progressive disclosure: same task, tiered menu vs full menu, accuracy + tokens.  `[key]`
- MCPMark-subset bridge: run a small recognized-benchmark slice under naive vs compact forms —
  attaches *third-party* accuracy to our token findings.  `[key]`

**Track M — measurement science (deepen the moat):**
- Response-filtering scoring: detect field-projection affordances (`fields=`, `$select`, sparse
  fieldsets) in specs and quantify the bucket-C reduction they enable (StackOne's approach #3 —
  currently invisible to `lap score`).
- Cache economics: amortized bucket-A under prompt caching (first-call vs cached vs
  Tool-Search-deferred) — answers "doesn't caching make A free?" with a model + numbers.
- Tokenizer sensitivity matrix: tiktoken vs Anthropic vs ≥1 more, same corpus — defuses "whose
  tokens?" and likely explains vendor-number discrepancies (S2).
- Namespacing/dedup measurement (spec-#2808 proposal 3) as a standalone score dimension.
- Bucket-C pagination realism beyond `--page-size`: honor `limit`-param maxima and cursor
  envelopes found in the spec.
- Bucket-B *measured* (not just estimated) generalized outside token-bench.

**Track S — standards & artifacts (from advisory to actionable):**
- **Lint auto-fix as an OpenAPI Overlay**: emit a standard Overlay document that *applies* the
  compact-menu fixes (trim descriptions, add pagination params, mark heavy ops) — authors apply
  it with existing Overlay tooling; LAP stops being advice and becomes a patch.
- Arazzo (OpenAPI workflows) scoring: multi-step bucket-B cost of a declared workflow vs ad-hoc
  chaining.
- Profile v1.1: crosswalk LAP rules ↔ 2026 vocabulary (AX, progressive disclosure, code mode,
  tiered schemas) so newcomers find us from the terms they already know.
- llms.txt / NLWeb "be-discoverable" L0 rule + scoring a live NLWeb `/ask` endpoint _(ex-S8)_.
- An `x-lap-*` OpenAPI extension proposal (declare page-size maxima, projection params, heavy
  ops) — strawman doc, gather feedback before implementing.

**Track C — community & reach:**
- CONTRIBUTING.md + issue templates + 3–5 curated good-first-issues _(ex-S7)_.
- Outreach to mcpx/AgentDX authors with the N6 comparison — collaborate, don't compete (their
  UX + our measurement).
- Get listed: awesome-mcp lists, MCP.Directory, PyPI classifiers/keywords pass.
- GitHub Action to the Marketplace (owner UI step, already release-ready).
- Badge adoption drive: PR the LAP badge onto 2–3 friendly OSS API repos.

**Track E — engineering health:**
- Property-based tests (hypothesis) for IR/estimator — the fuzz corpus found the 2.0 gap; PBT
  finds the next one cheaper.
- Cross-OS CI matrix (ubuntu/windows/macos × 3.11–3.14).
- Perf pass on 4M-token specs (Xero/K8s currently slow-ish paths in `inline_refs`).
- Documented stable Python API (`lap.score_spec()` etc.) + written 1.0 criteria.
- `lap score --diff --git HEAD~1` (diff directly against git refs, no temp files).
- Pre-commit hook recipe.

## Status

**v0.3 complete (stages 0–19); v0.4 COMPLETE (R1–R8); v0.3.0 FULLY RELEASED 2026-07-01; v0.5 IN
PROGRESS.** `lap-score` 0.3.0 is live on PyPI (https://pypi.org/project/lap-score/0.3.0/,
verified via a fresh-venv install) and the GitHub release is published
(https://github.com/lCrazyblindl/lap/releases/tag/v0.3.0, both dist files attached). The only
release step left is optional and UI-only: listing the Action on the GitHub Marketplace. **v0.5
S1 done** — repeating R6's code-execution comparison 5× confirmed "heavier than naive" is a real
pattern (5/5), driven by retried execution attempts from wrong sandboxed file-path guesses, not
noise. **v0.5 S2 done** — real `mcp-compressor` (Atlassian) on 2 real MCP servers at 2 scales:
scale amplifies the win (+12% small server, +67% big server, our own tokenizer), and a genuine
cross-check discrepancy surfaced — the tool's own self-reported percentage disagreed with us on
the small server. **v0.5 S3 done** — leaderboard expanded 20 → 50 real APIs (10.4M naive tokens
total, +80%/+82% avg saved); also caught and fixed a cosmetic double-sign bug the expansion
surfaced. **v0.5 S4 done** — `lap score --diff <before> <after>`: real, shipped-package code
(menu-token delta per form + added/removed lint findings), a `--max-growth` CI gate, +3 tests;
first v0.5 change to actually land in `lap/`, tracked in `CHANGELOG.md`'s new `[Unreleased]`
section. **v0.5 S5 done** — bucket-C estimate now prefers real schema `example`/`examples` over
synthetic placeholders, plus a configurable `--string-len`; leaderboard's total heaviest-result
estimate rose ~41% (482,795 → 681,830 tokens) once real examples were honored. **After S5 the
plan was re-drawn (2026-07-06) from a fresh landscape re-check — see "Stages — v0.6" above; the
S6–S8 tail is folded into it (S6→N8, S7/S8→v0.7 tracks). v0.6 N1 done — `lap stack` scores the
user's installed MCP stack from their own agent config ("N tokens before you type a word"; demo:
2 real servers, 1701 naive → 184 compact, +89%). v0.6 N2 done — composite LAP grade (0–100 +
letter, documented formula, calibrated on the leaderboard corpus) + `lap badge` shields.io
endpoint + Action `badge-path`; our README carries an honest B (72) for the bundled example.
v0.6 N3 done — `lap lint --mcp-url/--mcp` lints live MCP servers (M1–M4 rules + grade;
mcp-server-git B 71, mcp-server-time A 89). v0.6 N4 done — bucket-B call estimate in `lap
score` (A/B/C in one command); 49 tests green. v0.6 N5 done — **0.4.0 FULLY RELEASED
2026-07-06** (PyPI + GitHub, fresh-venv verified). v0.6 N6 done — `docs/FIELD.md`: field
comparison + 10-claim registry (2 disputed by our measurements). v0.6 N7 done —
`docs/SPEC-2808.md`: tiered schemas save mean 85% over 51 real APIs (issue's estimate is
conservative), dedupe −10…94% (only fat repeated schemas pay); ready-to-paste comment for the
owner. v0.6 N9 done — **live leaderboard at https://lcrazyblindl.github.io/lap/** (sortable
page + JSON + monthly history, cron refresh). ▶ current stage: v0.6 N10 (launch write-up); then
N8 `[key]` last.** Say "continue LAP" to keep going once a stage completes.
v0.4 pivoted the benchmark from our own interface variants to real third-party
artifacts —
real generators, a real live API, real servers, real Anthropic features — and found the compact/
efficient story holds **most, not all**, of the time:

- **Real generators & servers leave savings unclaimed.** Three real OpenAPI→MCP generators
  ([`docs/GENERATORS.md`](docs/GENERATORS.md)) and three real published MCP servers
  ([`docs/MCP-SERVERS.md`](docs/MCP-SERVERS.md)) all emit menus heavier than naive and far heavier
  than compact (5–28× and ~89% respectively) — nobody in the ecosystem ships the compact form.
- **Compression didn't cost accuracy on a real live API — it helped.** End-to-end on the hosted
  Swagger Petstore ([`validation-real.md`](experiments/token-bench/validation-real.md)): the naive
  menu was both the heaviest *and* the least reliable (failed a count task 0/3 while compact/real
  FastMCP hit 3/3).
- **Envelope-aware bucket C** made result-size estimates honest on real APIs — 15 of 20 leaderboard
  rows changed, several substantially (Kubernetes 1303→7613, Stripe 1588→15868).
- **Two of Anthropic's own real efficiency features, tested live, cut two different ways.** Real
  **Tool Search** ([`docs/TOOL-SEARCH.md`](docs/TOOL-SEARCH.md)) held up: ~90% real, billed saving
  at scale (290 real ops), *server-enforced* regardless of model behavior — though it cost more
  than compact at small scale (19 ops), matching Anthropic's own "10+ tools" guidance. Real
  **code-execution** ([`docs/CODE-EXEC.md`](docs/CODE-EXEC.md)) did **not** hold up on one run: it
  cost *more* than both naive and our own sandbox, because the model viewed the raw uploaded data
  before writing code to avoid reprinting it — its saving is *behavioral*, not structural, and
  nothing stops a model from re-materializing the very payload the hatch exists to avoid.
- **R8 reframed the story honestly** — the profile's D2 (Tool Search) and X1 (code-execution) rules
  and `docs/LANDSCAPE.md` §5 now say plainly which savings are server-enforced vs behavior-dependent,
  instead of only citing vendor headline numbers.

A key-free **backlog** remains below (unscheduled, pick anytime); a broader Stage 15(b) matrix
(more models/tasks/repeats) is also open, key-needed. Say "continue LAP" to pick one.

## Sources captured for Stage 1 (so it can be done without re-searching)

- llms.txt (state/adoption, 2026): https://codersera.com/blog/llms-txt-complete-guide-2026/ · https://caseyrb.com/blog/state-of-llms-txt-adoption/
- Microsoft NLWeb (agentic web; sites expose `/ask` + `/mcp`): https://news.microsoft.com/source/features/company-news/introducing-nlweb-bringing-conversational-interfaces-directly-to-the-web/
- MCP gateways (OAuth/DCR, open source): AWS https://aws.amazon.com/blogs/opensource/governing-ai-assets-at-scale-with-mcp-gateway-and-registry/ · Hypr https://github.com/hyprmcp/mcp-gateway · atrawog https://github.com/atrawog/mcp-oauth-gateway
- Agent identity standards: NIST AI Agent Standards Initiative https://workos.com/blog/nist-ai-agent-standards-initiative-explained · IETF https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/ · MCP adopted OAuth 2.1 + RFC 9728 (protected-resource metadata)
