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
- [x] **N8 — Validation matrix v2** _(ex-S6)_. Done (Haiku complete; Sonnet 76%, see N8b).
  New `run_bench.py --matrix-v2 --repeats N --models a,b` (`live_runs.run_matrix_v2`): ALL 10
  grouped tasks × 5 forms × k repeats per model, per-model checkpointing, retry-with-backoff
  that does *not* retry permanent 4xx, and the new **tokens-per-correct-answer** metric →
  rewritten [`validation.md`](experiments/token-bench/validation.md). **Haiku, k=5 (250 runs):
  `code_exec` is the only 100% form (50/50) AND the cheapest right answer (1977 tok — 2.9×
  cheaper than naive's 5759); compact 48/50 ≈ naive 49/50 at ~30% fewer tokens; `numbered`
  measurably worst (46/50, one 2/5 cell — D3 vindicated at k=5); `odata_query` fails 0/5 on
  exactly the one DSL-inexpressible task (X1's category-shaped gap).** Sonnet partial (190/190
  correct across 38 cells — a strong model is form-insensitive for accuracy, but its code runs
  showed 8× token variance on one task, echoing the behavioral-cost finding). The run was
  interrupted at Sonnet cell 39/50 by **API credit exhaustion** (billing 400) — a real budget
  boundary, not a code failure.  `[key]`
- [x] **N8b — Finish the Sonnet pass.** Done after the owner's credit top-up: added a
  `--tasks` resume filter to `run_bench.py` and re-ran only the 3 missing tasks (75 runs
  instead of 250); merged into [`validation.md`](experiments/token-bench/validation.md) —
  Sonnet now complete at **248/250** (worst cell 4/5). **The completed matrix flipped the
  headline: the cheapest right answer is model-dependent.** Haiku: `code_exec` wins (1977
  tok/correct, 2.9× cheaper than naive). Sonnet: the *same* sandbox costs **5345 tok/correct —
  nearly naive-priced** — the stronger model writes exploratory multi-attempt code (14.5k on
  one task); its cheapest right answer is `odata_query` (1902). Also: Sonnet recovers 4/5 on
  the DSL-inexpressible task where Haiku was 0/5 (X1's gap severity is model-dependent), and
  `numbered`'s accuracy penalty is Haiku-only (Sonnet 50/50) — a small-model tax, as D3
  predicts. Profile X1 updated with the own-sandbox confirmation. **v0.6 COMPLETE (N1–N10 +
  N8b).**  `[key]`

## Stages — v0.7 (rolling; drawn from the tracks below as they're picked up)

- [x] **C1 — CONTRIBUTING.md + issue templates + PR template.** Done (promoted after spam PR #1).
  [`CONTRIBUTING.md`](CONTRIBUTING.md): dev setup, and four codified policies — **vendor
  neutrality** (no promo links; leaderboard = the real-API example; corpus additions must be in
  APIs.guru), **claims need receipts** (script + corpus + tokenizer), **honest reporting**
  (counter-examples ship), **measured-not-asserted** (rule PRs cite an experiment). Issue forms:
  bug report, feature request (asks which bucket + what measurement justifies it), and a
  **"Score my API"** form (community hook; disputes explicitly welcome) + PR template with the
  policy checklist. README's "no formal guide yet" line replaced.  `[no key]`
- [x] **M1 — Response-filtering scoring.** Done. `estimate.supports_projection(op)` (reuses
  lint's R1 name set) + `estimate.estimate_projected()` (same page, each item cut to its
  **first 3 schema fields** — author-ordered properties typically lead with identity fields,
  so "first N" models a curated field set without inventing semantics; envelope metadata
  kept). `lap score`'s C table now shows per-list `-> ~N with the advertised projection` or
  `-> ~N if projection were added (R1)` — the one mainstream optimization approach (StackOne's
  #3) lap couldn't see, and R1's saving is now a per-endpoint number (Bookstore: 465 → 305 at
  page 20). `projected`/`has_projection` in `--json`. +3 tests (tests/ 48, full suite 52).
  `[no key]`
- [x] **V1 — Root-cause the mcp-compressor self-report discrepancy.** Done — **found in the
  tool's own source** (`banner.rs`, fetched via `gh api`), confirmed two ways: (1) the banner
  measures **characters, not tokens** (no tokenizer in the stats path); (2) **the ratio is
  asymmetric** — original = name+description+`properties` sub-object only (drops `type`/
  `required`/scaffolding), compressed = full descriptions + entire wrapper schemas. On the
  2-tool server the undercounted original flips the sign: banner prints 103.8% "loss" while
  the actually-advertised menus are smaller by any symmetric measure (chars −0.6%, tokens
  −12%). Python replication of their formula reproduces direction+magnitude (111.6%/56.5% vs
  printed 103.8%/54.5%; residuals = served-frontend vs internal constants). Also resolves S2's
  open caveat: the below-10-tools cutoff does NOT apply to this tool — its banner was the only
  dissenter, and the banner mismeasures. `experiments/mcp_compressor_rootcause.py` (multi-
  metric + formula replication + banner capture via transport `log_file`), root-cause section
  + **ready-to-paste upstream issue** in `docs/MCP-COMPRESSOR.md` (owner posts), FIELD.md rows
  updated to "mismeasured/root-caused".  `[no key]`
- [x] **M2 — Cache economics.** Done → [`docs/CACHE-ECONOMICS.md`](docs/CACHE-ECONOMICS.md)
  (generated by [`experiments/cache_economics.py`](experiments/cache_economics.py) from the
  leaderboard data). The model: write 1.25×, read 0.10×, prefix re-sent every turn → cached
  session = `A×(1.25+0.10(T−1))` vs uncached `A×T`. Key results: caching is **at best a 10×
  price discount, never zero, and pays in dollars not context** (the #2808 reasoning-capacity
  concern is untouched; K8s' 2.8M menu fits no window at any discount); break-even — an
  *uncached compact* menu beats a *cached naive* one while `T < 1.15/(r−0.10)` (≈11 turns at
  r=0.2, always when r≤0.10, e.g. Xero); the strategies **compose** — worked examples: Xero
  compact+cached **2126×** cheaper than naive uncached per 8-turn session ($96.95 → $0.046),
  GitHub 13×, Notion 39×. Profile gained a "but isn't it cached?" call-out under Discovery;
  README project map links the doc.  `[no key]`
- [x] **S1 — Lint auto-fix as an OpenAPI Overlay.** Done. New `lap/overlay.py` + `lap fix
  <spec>`: emits the *structurally fixable* findings as an **Overlay 1.0.0** document — R3 →
  `limit` query param, R1 → `fields`, R2 → `filter`, E1 → declared `4XX` response; one action
  per operation, D3/A1 honestly left advisory (renames/new endpoints are semantic). `--apply`
  does the Overlay-spec structured merge (dicts merge, lists append) and reports the finding
  delta. Live: Bookstore 15 → 3 findings, grade **B (72) → A (91)** — the first A, earned by
  the tool's own patch; live Petstore 16 → 8. +3 tests (tests/ 51, full suite 55). **Also
  surfaced a real measurement gap** (→ M3): `menu._input_schema` counts only path+body params,
  so query params are invisible to every menu form — the leaderboard's "naive" menus are
  *undercounted*, which also explains part of the "real MCP heavier than naive" gap.  `[no key]`
- [x] **M3 — Query params in the menu forms (measurement fix).** Done. `menu._input_schema`
  now carries every path+query parameter (headers stay transport-level — bridges map them to
  transport, not arguments); compact/numbered add **required** query params only (the curated
  calling surface, per D1). **Regenerated everything**: leaderboard naive total **+7.2%**
  (10,426,548 → 11,175,074; Spotify +216%, EC2 +73%, Trello +52%, 5 rows unchanged), avg
  compact save 80→**82%**, tool_search 82→**86%** (compact adds only required query params, so
  the naive↔compact gap *widened*); site + history snapshot + SPEC-2808 tables +
  CACHE-ECONOMICS (avg r now 0.179, GitHub break-even ~6 turns) + POST.md headline (11.2M) all
  refreshed. Grade calibration re-checked: two letters shifted (Spotify B→C, Postman C→D —
  query-param-heavy APIs got honester grades), constants unchanged; profile + lap/README
  calibration text updated. Petstore quote now 1835→207 (−89%). Honest CHANGELOG "Fixed"
  entry (S5-style). +1 test (tests/ 52, full suite 56).  `[no key]`
- [x] **M4 — Tokenizer sensitivity matrix.** Done →
  [`docs/TOKENIZERS.md`](docs/TOKENIZERS.md) ([`experiments/tokenizer_matrix.py`]
  (experiments/tokenizer_matrix.py)): the corpus's naive + compact menus re-encoded under 4
  BPE vocabularies (cl100k baseline, o200k, p50k, gpt2). **Absolutes swing ≤8%; the mean
  compact saving moves 3.0 pp (82.4→79.4%); the API ranking holds at Kendall τ ≥ 0.992** —
  worst single-API saving spread 12.6 pp (CircleCI). Plus the Stage-13 faithful-Anthropic
  citation (~60% higher absolutes, identical ordering). "Whose tokens?" now has a receipt:
  the compressed-vs-verbose gap is a property of the text, not the ruler. POST.md's pushback
  note and the README map point at it.  `[no key]`
- [x] **R — Release 0.5.0. FULLY RELEASED, 2026-07-07.** Ships `lap fix` (Overlay + `--apply`),
  projected bucket-C, and the M3 query-param menu fix — the key argument: the live leaderboard
  is generated with M3 code, so the published package must reproduce the published numbers.
  **PyPI:** https://pypi.org/project/lap-score/0.5.0/ (twine PASSED ×2; fresh-venv verified —
  `lap fix --apply` runs from the published wheel, patched Bookstore scores A 91). **GitHub:**
  tag + release https://github.com/lCrazyblindl/lap/releases/tag/v0.5.0. Action examples at
  `@v0.5.0`.  `[release creds]`
- [x] **S2 — Discoverability rule D0 + llms.txt adoption scan** _(ex-v0.5 S8, trimmed to what's
  measurable)_. Done. Profile gains **L0 / rule D0** (publish `<origin>/llms.txt` pointing at
  your machine-readable interface); `lap lint <url> --discovery` probes the origin and flags
  its absence (info; local files skipped; probe injectable for tests). Evidence:
  [`docs/DISCOVERY.md`](docs/DISCOVERY.md) ([`experiments/discovery_scan.py`]
  (experiments/discovery_scan.py)) scanned the leaderboard's 36 provider apex domains —
  **llms.txt is at 47% adoption** (Stripe, GitHub, Slack, Notion…), which *surprised us*
  (expected near-zero; the pre-drafted "almost none" narrative was rewritten to match the
  data), while MCP discovery conventions are ~absent (`/.well-known/mcp.json` 6%, real `/mcp`
  0% — all apparent hits were SPA HTML fallbacks, caught after extending the soft-404 check to
  every path). Story: **discovery is getting solved; efficiency isn't** — the same providers'
  menus are still the leaderboard's naive kilotokens. NLWeb endpoint scoring: nothing live to
  score (0/36 `/mcp`); `--mcp-url` already covers any that appear. +2 tests (tests/ 54, full
  suite 58).  `[no key]`
- [x] **Plan re-drawn 2026-07-08** from a fresh landscape re-check → see **"Stages — v0.8"**
  below; the open v0.7 track items are folded into it (V 2nd-API → P4, C outreach → P5,
  E perf/PBT → P6).

Two owner actions stay pending meanwhile: post the SPEC-2808 comment (**hold until P1 refreshes
it** — issue #2808 appears closed) and publish `docs/POST.md` (P5 refreshes its numbers).
- [x] **N9 — Leaderboard as a living page.** Done. `experiments/leaderboard.py` now also emits a
  static **sortable** page (`docs/index.html`, vanilla JS, no build step), machine-readable
  `docs/leaderboard-data.json`, and a dated monthly snapshot under `docs/leaderboard-history/`
  (`2026-07.json` is the first) — so month-over-month trends stay diffable. **GitHub Pages
  enabled via `gh api`** (main → `/docs`, `.nojekyll` added): **https://lcrazyblindl.github.io/lap/**.
  A monthly cron (`.github/workflows/leaderboard.yml`, 3rd of each month + `workflow_dispatch`)
  regenerates everything and commits as github-actions[bot]. Gotcha: Pages doesn't list
  directories — the page's "history" link points at the GitHub tree instead.  `[no key]`
- [x] **N10 — Launch write-up.** Done → [`docs/POST.md`](docs/POST.md): three ready-to-paste
  drafts — (1) a data-first blog post ("We measured the agent-menu tax of 50 real public APIs:
  10.4M tokens" — leaderboard numbers, the verified/disputed vendor claims, structural-vs-
  behavioral, spec-#2808 input, try-it section, honest caveats); (2) a **Show HN** (title + the
  author first-comment, linking the live leaderboard page as the submission URL); (3) an
  **r/mcp** post (community-angled: `lap stack`, `lap lint --mcp`, the git/time A-vs-B grades).
  Plus posting notes for the owner (order, timing, where the pushback will come and which
  receipts answer it). **Publishing is the owner's action** — like the SPEC-2808 comment, it
  goes out under their name, not the agent's.  `[no key]`

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
- **Param-description ablation** `[key]`: live A/B — identical menu ± parameter descriptions,
  accuracy at param granularity. Prompted by an r/mcp reply (2026-07-11) reporting
  "undescribed params hurt accuracy more than raw token count did"; we answered honestly
  that we haven't isolated that variable yet. Would give M2 its own accuracy citation
  (M-rules currently inherit the form-level matrix evidence).
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

## Stages — v0.8 (drawn 2026-07-08 from a fresh landscape re-check)

**Why a new plan.** A July-8 re-check found four shifts. (1) **A deadline appeared**: the MCP
spec's final publication lands **2026-07-28** (RC locked May 21 — stateless core, `tools/list`
caching via `ttlMs`/`cacheScope`, full JSON Schema 2020-12 in tool schemas, extensions
framework), and issue **#2808 appears closed** — our prepared comment is stale and must be
refreshed/retargeted before the window closes; nobody has measured the RC's token impact yet.
(2) **Claude Code 2.1.x enabled Tool Search by default** (~85% bucket-A cut — the mechanism we
verified live in R5): the naive-menu headline is now *client-conditional*; B/C and every other
client still pay full price, so "who mitigates what" became an empirical question. (3)
**Competitors multiplied, all tiny, none overlapping the core**:
[agent-friend](https://github.com/0-co/agent-friend) (MCP-only *static* linter, 156 checks,
A+–F grades, auto-fix, graded 201 servers, ~4 stars — but its "I graded 201 MCP servers" posts
prove the public-grading content format), AgentDX (did a Show HN), and MindStudio's unverified
**"MCP = 35× more tokens than CLI"** benchmark claim. Nobody does A/B/C buckets, result-size
estimates, OpenAPI+MCP both, or live accuracy validation. (4) **LAP is still invisible** (5
stars, 1 fork) — the highest-leverage action remains the owner's pending publications; every
stage below has a deadline, produces publishable content, or makes that publishing easier.

Same stop/resume model. Recommended order: **P1 (deadline) → P2 (content) → P5 (unblock the
owner) → P3 → P4 → P6.**

- [x] **P1 — Spec-RC measurement + refreshed spec input.** Done. **Facts nailed down:**
  issue #2808 was closed 2026-05-29 (state_reason "completed", 0 comments) and **converted to
  [discussion #2812](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2812)**
  — alive, single-server data points (11/29/79 tools), and an explicit ask for a CI-checkable
  per-tool token budget ("like bundle size") that `lap lint --mcp` M3 + gates already answers.
  The draft changelog (final 2026-07-28) adopted **none** of #2808's three proposals; its
  token-relevant items: SEP-2549 (`ttlMs`/`cacheScope`), deterministic tool ordering, SEP-2106
  (full JSON Schema 2020-12 in `inputSchema`). **Shipped fix:** `lint.flat_schema()` — params
  behind `allOf`/`oneOf`/`anyOf`/local `$ref` were invisible to M2/M4 and rendered `tool()` in
  compact (cycle-safe, depth-bounded); measured prevalence with FastMCP over real specs:
  **29% of 320 generated tools already carry 2020-12 constructs** (DynamoDB 51/53), 0/320
  lose a param *name* today (nested, not top-level) — a forward-looking fix, and the same
  properties-only blind spot V1 root-caused in mcp-compressor. **Docs:** SPEC-2808.md
  retargeted at #2812 + SEP-2106 section + comment rewritten (answers the CI-budget ask and
  the tokens-vs-reliability tension with matrix-v2 data); CACHE-ECONOMICS.md gains "the 2026
  draft caches the *transport*, not the context". +2 tests (tests/ 56, full suite 60).
  **The refreshed comment was POSTED to discussion #2812 on 2026-07-08** (owner authorized
  the agent to post via their `gh` auth; dedupe examples made dynamic first — the hardcoded
  "Kubernetes 94% / CircleCI −10%" had drifted after M3 to "92% / DVP Data API −10%").  `[no key]`
- [x] **P2 — MCP-server leaderboard.** Done → [`docs/MCP-LEADERBOARD.md`](docs/MCP-LEADERBOARD.md)
  + `mcp-leaderboard-data.json` ([`experiments/mcp_leaderboard.py`](experiments/mcp_leaderboard.py)).
  Environment fixed contained-ly first: `uv` pip-installed into `.venv` (uvx = isolated PyPI
  runs), **portable Node unzipped into gitignored `.tools/node`** (npx for npm servers; its dir
  must be prepended to the spawned env's PATH — npx re-spawns `node` via PATH). **20 of 22
  curated popular servers scored with zero credentials** (dummy env vars only), 199 tools,
  menus 42 → **21,411** tokens/session (Notion official, F 19; firecrawl 18,511 F 27;
  sequential-thinking: ONE tool costing 921 tok, F 18; postgres 42 tok but undescribed schema,
  C 64), ~64k total. 2 honest dead rows (mcp-atlassian lists 0 tools without creds; yfmcp).
  **agent-friend cross-check landed all three ways**: Notion — both F within a point (their
  19.8 vs our 19) yet 4.8× apart on tokens (4,483 vs 21,411); server-postgres — their
  "perfect 100" vs our C; context7 — F vs our D. The referee lesson written into the doc:
  letters are formula artifacts, reproducible token numbers are the measurement. Wired: live
  page nav link, monthly cron step (runner has Node; `pip install -e ".[mcp]" uv`), FIELD.md
  agent-friend row + honesty paragraph, README bullet + map link.  `[no key]`
- [x] **P3 — Referee round 2 + field refresh.** Done → [`docs/MCP-VS-CLI.md`](docs/MCP-VS-CLI.md)
  ([`experiments/mcp_vs_cli.py`](experiments/mcp_vs_cli.py)). **Claim traced**: MindStudio's
  "35×/72%" cites *no* methodology; the one reproducible artifact in the family is scalekit's
  benchmark (gh CLI vs GitHub MCP, published code+data, 15–80× per task, single-run headlines).
  **Bonus: the official GitHub MCP server finally scored directly** (hosted endpoint + `gh auth
  token` — closes the R3-era backlog item): **44 tools / 11,461 tokens / grade B (76)** — the
  circulating "~94 tools/17.6k" is stale. **Structural reproduction**: the menu re-sent per
  turn alone reaches 27× the entire gh-help surface (3,449 tok) by 8 turns — the magnitude is
  real *for a naive client*; it collapses under Tool Search (default in Claude Code; our live
  −90%) or compact (927 tok), and the CLI side rides a training-data subsidy (models know `gh`;
  your API's CLI gets no such discount). 72% reliability: unverifiable as published. FIELD.md:
  two registry rows updated/added (GitHub-MCP size now ⚠ stale-corrected; 35×-vs-CLI ≈
  config-dependent). _Live k=3 slice skipped deliberately: scalekit already publishes raw
  data; the structural decomposition + R5's live Tool Search number explain the magnitude — a
  third anecdote adds nothing, the ruler does._ agent-friend rows landed with P2.  `[no key]`
- [ ] **P4 — 2nd real API for Tool Search + code-exec** _(Track V carry-over)_ `[key]`. Do
  R5/R6 generalize beyond DigitalOcean/pet-zoo? Pick a 100+-op leaderboard API usable without
  a paid account; extend `docs/TOOL-SEARCH.md`/`docs/CODE-EXEC.md`.
- [x] **P5 — Reach without the owner.** Done. **POST.md refreshed** for current main: all
  three drafts gain the MCP-server leaderboard (Notion 21,411 F is now the r/mcp *title*),
  the model-dependent matrix-v2 finding, D0/llms.txt 47%, #2812 retarget ("the summary is
  posted in the discussion"), tiered 85→87%, post-M3 grade calibration (Spotify B→C), and
  posting notes for the "which versions?" question. **[`docs/LISTINGS.md`](docs/LISTINGS.md)**
  (new): exact ready-to-submit texts — awesome-mcp-devtools PR line+body, openapi.tools YAML
  entry, MCP directory forms, the Action-Marketplace UI step. **Done directly (repo metadata,
  not publication): 7 GitHub topics set** via `gh repo edit` (mcp, model-context-protocol,
  openapi, llm, token-efficiency, agents, linter — Glama etc. index by topics). **pyproject
  keywords 7→14** (context-window, token-cost, model-context-protocol, …) — lands on PyPI at
  the next release.  `[no key]`
- [x] **P6 — Engineering health.** Done. **PBT** (`tests/test_properties.py`, hypothesis in
  `[dev]`): 4 generative invariants — flat_schema / inline_refs / example_instance total on
  arbitrary schema-shaped garbage (incl. cyclic+dangling `$ref`s), and the whole pipeline
  (IR → all menu forms → counts → B/C estimates) total on generated mini-specs. **Found and
  fixed 7 real crash sites** the 175-spec fuzz corpus never hit: `parameters: null`,
  non-dict `properties`, non-list `enum`/`oneOf`/`anyOf`, `$ref: null`, boolean `items`,
  dict `type` (unhashable in `_placeholder`), int response codes. 64 tests green.
  **Perf pass = a finding, not a fix**: profiling Xero (4M tok) shows `inline_refs` at 0.19s
  — the backlog's suspect was innocent; the wall is tiktoken's ~1.6M tok/s encode (2.6s),
  and `encode_ordinary` measured **zero** speedup (0.30s = 0.30s on 2MB) — the ruler is at
  its floor, documented here instead of a fake optimization. **CI matrix**: ubuntu/windows/
  macos × Python 3.10/3.13, fail-fast off (spectral job unchanged).  `[no key]`

- [x] **R — Release 0.6.0. FULLY RELEASED, 2026-07-09** (P4 deferred by owner's call —
  "зарелизимся, остальное отложим"). Ships the composed-inputSchema fix (SEP-2106,
  `flat_schema`), rule D0 + `--discovery`, the PBT hardening (10 crash sites), 14 PyPI
  keywords. **PyPI:** https://pypi.org/project/lap-score/0.6.0/ (twine PASSED ×2; fresh-venv
  verified — `flat_schema` + `lap score` from the published wheel). **GitHub:** tag + release
  https://github.com/lCrazyblindl/lap/releases/tag/v0.6.0 (both dists). Action example at
  `@v0.6.0`.  `[release creds]`

Backlog unchanged (see Tracks above): Arazzo, x-lap extensions, MCPMark bridge,
progressive-disclosure live A/B, GitHub official MCP via Docker (hosted endpoint now scored,
P3), 1.0 criteria, badge adoption. **P4 (2nd real API, `[key]`) carries over → v0.9 W3.**

## Stages — v0.9 (drawn 2026-07-10 from a fresh state check)

**Why a new plan.** Three fresh signals reshape priorities. (1) **The referee role produced
its first upstream fix**: our mcp-compressor issue
([#236](https://github.com/atlassian-labs/mcp-compressor/issues/236), posted Jul 9) was closed
*"completed"* by a maintainer within 3 hours and
[PR #237](https://github.com/atlassian-labs/mcp-compressor/pull/237) ("Fix asymmetric
compression statistics in startup banner") merged — evidence-based upstream reports
**convert**, and that's a repeatable motion. (2) **The competitor threat was overestimated**:
agent-friend dormant since Mar 25 (4 stars), AgentDX quiet — the field is ours to lose to
*invisibility*, not to a rival (LAP still 5 stars; the owner's POST.md launch remains the top
lever and just got its strongest credibility line). (3) **The spec final lands Jul 28** —
a time-anchored measurement moment we're uniquely positioned for. The toolkit is
feature-complete for its niche; v0.9 tilts from *building* to **converting measurements into
ecosystem impact**.

Recommended order: **W1 (small, feeds POST) → W4 (the proven motion) → W2 (fires ~Jul 28) →
W3 `[key]` → W5 `[key]` → W6 → W7 → W8 (opportunistic)**.

- [x] **W1 — Cash the #236 win.** Done. The fix shipped as **0.31.5 thirteen minutes after
  the merge**; re-ran the banner capture against the released version: **the banner is now
  symmetric** — mcp-server-time@medium 103.8%→**90.8%** (sign flip gone; our symmetric
  measures 88.3% tokens / 99.4% chars), mcp-server-git@medium 54.5%→**41.9%** vs our 41.0%
  chars (near-exact), while the old asymmetric formula would still predict 111.6%/56.5% —
  proof the shipped banner no longer uses it. Honest residual: still characters, not tokens
  (our secondary suggestion; fine for a banner). `docs/MCP-COMPRESSOR.md` gained the
  "Upstream outcome" section (the referee loop closed end-to-end in ~a day), FIELD.md row
  flipped ✗→✅ fixed-after-our-report, POST.md all three drafts carry the win.  `[no key]`
- [ ] **W2 — Spec-day measurement** `[no key]` **(time-anchored: ~Jul 28, when the final
  spec publishes).** Diff final vs RC (did SEP-2106/2549 survive?); refresh `docs/SPEC-2808.md`
  + CACHE-ECONOMICS if mechanics moved; check #2812 for post-final replies; draft "the 2026
  spec shipped — what it changes about your token bill" as a POST.md section.
- [ ] **W3 — 2nd real API for Tool Search + code-exec** _(P4 carry-over)_ `[key]`. Do R5/R6
  generalize beyond DigitalOcean/pet-zoo? 100+-op leaderboard API, no paid account; extend
  `docs/TOOL-SEARCH.md`/`docs/CODE-EXEC.md`.
- [x] **W4 — Upstream fix drive. All three issues POSTED 2026-07-10** (owner said «публикуй
  все три»; duplicate-checked first): [servers#4507](https://github.com/modelcontextprotocol/servers/issues/4507)
  · [firecrawl#309](https://github.com/firecrawl/firecrawl-mcp-server/issues/309)
  · [notion#330](https://github.com/makenotion/notion-mcp-server/issues/330) — all three now
  on the twice-daily reply watch. Prepared as →
  [`docs/UPSTREAM-ISSUES.md`](docs/UPSTREAM-ISSUES.md)
  ([`experiments/upstream_issues.py`](experiments/upstream_issues.py), live-fetched,
  reproducible). Three measured what-ifs, three different pathologies:
  **sequential-thinking** (modelcontextprotocol/servers, 88k★) 921 → **463 tok (−50%)** by
  dropping the "Parameters explained" section that duplicates the schema's own param
  descriptions (all 9 params already carry one) + "Key features" fluff;
  **firecrawl-mcp** (6.9k★) 18,511 → **9,218 (−50%)** at first-paragraph-only descriptions
  (usage essays are docs, not selection signal — while 24/26 tools have UNdescribed params);
  **notion-mcp-server** (4.5k★) 21,411 → **~6,600 (−69%) from `$defs` dedupe alone** — one
  2,317-char subtree repeats in ALL 24 tools (SEP-2106 makes $refs first-class, killing the
  compatibility objection). Ready-to-paste texts in the doc, #236 tone, disclosure included.
  `[no key]`
- [ ] **W5 — MCPMark bridge** `[key]`. A small recognized-benchmark slice under naive vs
  compact forms — attaches *third-party* accuracy to our token findings (FIELD.md's "their
  accuracy × our cost" promise).
- [x] **W6 — Arazzo scoring + x-lap strawman.** Done. **Arazzo** →
  [`docs/ARAZZO.md`](docs/ARAZZO.md) ([`experiments/arazzo_score.py`](experiments/arazzo_score.py)):
  7 workflows from the OAI spec's own example documents (real artifacts), each scored as a
  *macro tool* (id + summary + `inputs` schema) vs the ad-hoc chain — **menu 50–97% below
  the naive API menu; bucket B splits by chain size** (7-step BNPL flow 174→69 tok/call,
  but 2 of 7 tiny oauth flows pay *more* — the workflow `inputs` schema outweighs the one
  or two small calls it replaces; the familiar below-threshold shape). The biggest effect
  is invisible to A/B accounting: **intermediate step results never enter context** —
  structural, like Tool Search, unlike code-exec. **x-lap** → [`docs/X-LAP.md`](docs/X-LAP.md):
  4 keys (`x-lap-page-max`, `x-lap-projection`, `x-lap-heavy`, `x-lap-workflow`), what
  score/lint/fix would do with each, explicit non-goals (absence is never a finding; keys
  retire if the specs standardize equivalents). Feedback invited via issues.  `[no key]`
- [x] **W7 — Stable API + 1.0 criteria.** Done. **Python API facade** in `lap/__init__.py`:
  `score_spec` / `lint_spec` / `grade_spec` / `diff_specs` (path/URL/dict in, the CLI's
  `--json` shapes out; `lap.Finding` lazily exported; `__version__` now from package
  metadata — was frozen at "0.1.0"), documented in lap/README's new "Python API" section
  and declared loose-semver-stable from 0.7. **`lap score --diff --git <ref> <spec>`**
  (`score.spec_at_git_ref` via `git show`, no temp files; runs from the file's own dir so
  any repo layout works) + **pre-commit recipe** in lap/README. **The 1.0 bar written**
  (ROADMAP section: 5 criteria — surface stability ×2 releases, frozen rule IDs with
  reproducing citations, regenerable numbers ±1%, green 3-OS PBT ×2 releases, and at least
  one external consumer holding the API). +2 tests (tests/ 62, full suite 66 green).
  CHANGELOG `[Unreleased]` reopened with both features → ready to cut **0.7.0** whenever
  the owner says the word.  `[no key]`
- [x] **R — Release 0.7.0. FULLY RELEASED, 2026-07-10.** Ships W7 (stable Python API,
  `--diff --git`, pre-commit recipe) — "the toolkit becomes a library". **PyPI:**
  https://pypi.org/project/lap-score/0.7.0/ (twine PASSED ×2; fresh-venv verified: facade
  returns the reference figures, `--diff --git` runs from the wheel). **GitHub:** tag +
  release https://github.com/lCrazyblindl/lap/releases/tag/v0.7.0. Action at `@v0.7.0`.
  `[release creds]`
- [x] **W9 (unplanned, community-driven) — grade navigation in `lint --mcp`.** Done. Born
  from the first r/mcp reply: the author of easy-notion-mcp (scored B 83 on request — first
  community-requested leaderboard row) needed to know *what to fix*, and the recipe I
  hand-computed (top-7 descriptions, ~730 tokens to A) wasn't reproducible from the CLI.
  Now it is: `lint --mcp` prints the heaviest definitions (desc/schema split,
  `lint.heaviest_tools()`) + a "to reach <letter>: shave ~N" budget
  (`grade.next_grade_menu_budget()`, binary search over the grade formula), or the honest
  hygiene-limited variant ("a lighter menu alone can't get there") — verified live on
  mcp-server-git, which correctly showed the *opposite* diagnosis to easy-notion (schema-fat
  + hygiene-capped vs description-fat). +2 tests (tests/ 64, full 68). CHANGELOG
  `[Unreleased]` reopened. _Backlog note: `lint --mcp` can't pass custom env vars to the
  spawned server (StdioTransport inherits only the SDK's safe-minimum env, so e.g.
  NOTION_TOKEN-gated servers can't be linted from the CLI; the library path can) — a
  `--env KEY=VAL` flag is a natural 0.8.0 item._  `[no key]`
- [x] **R2 — Release 0.8.0. FULLY RELEASED, 2026-07-10** (same-day follow-up: W9's grade
  navigation). **PyPI:** https://pypi.org/project/lap-score/0.8.0/ (twine ×2; fresh-venv
  verified — the wheel reproduces the easy-notion recipe, `menu_budget` 7,472 for an A).
  **GitHub:** https://github.com/lCrazyblindl/lap/releases/tag/v0.8.0. Action at `@v0.8.0`.
  `[release creds]`
- [x] **W10 (unplanned, community-driven #2) — rule M5: the whole menu is too heavy.** Done.
  Born from the Datadog dare on r/mcp: @us-all/datadog-mcp (166 tools / 28,835 tok) drew
  **zero findings** — disciplined per-tool, enormous in aggregate; the many-small-tools
  pathology had no rule. **M5** is the first *server-level* M-rule: info above ~10 tools &
  ~2k menu tokens, warn above ~10k; message carries the compact what-if; thresholds
  documented in the profile with receipts both ways (D2 measured ~90% live at scale,
  *negative* below ~10 tools — small servers exempt, and the prescribed fix is deferral/
  subsets, never deleting descriptions). Calibration on the leaderboard: warn = exactly the
  four servers we filed measured issues at (notion, firecrawl, @us-all, gcore); git/time/
  wikipedia stay silent; grade shifts ≤2 points (playwright 78→77, firecrawl 27→25).
  +1 test (tests/ 65, full 69). Leaderboard regenerated (23 servers incl. the Datadog pair).
  CHANGELOG `[Unreleased]` reopened. _Queued next to this: deferred-facade labeling — a
  small heuristic note so tool_search-style facades (gcore PR#13's 3 meta-tools) aren't
  misread as genuinely tiny servers, plus an x-lap self-declaration convention; awaiting the
  owner's go._  `[no key]`
- [ ] **W8 — Month-over-month trend content** `[no key]` **(after Aug 3 — second history
  snapshot).** "What changed in a month" on the live page + leaderboard diff — recurring
  content at zero marginal effort.

Owner actions standing: **the r/mcp post is PUBLISHED 2026-07-10**
(https://www.reddit.com/r/mcp/comments/1usyb34/i_scored_20_popular_mcp_servers_token_cost/ —
flair showcase; filled via the owner's browser session, owner-confirmed before submit; the
MCP-server-leaderboard title, per the refreshed draft). Still pending: the blog post + Show HN
(POST.md drafts 1–2), LISTINGS.md submissions, the Action-Marketplace click. The twice-daily
watch covers the 5 GitHub threads; Reddit replies arrive via the owner's native Reddit inbox.

## The 1.0 bar (written v0.9 W7 — what "stable" will mean)

`lap` tags 1.0 when ALL of these hold; until then, loose semver (minor = capability,
patch = fix), with the **Python API facade and CLI flags stable from 0.7** (breaking either
before 1.0 requires a deprecation release in between):

1. **Surface**: the documented Python API (`score_spec`/`lint_spec`/`grade_spec`/
   `diff_specs` + the MCP helpers) and every documented CLI flag survive two consecutive
   minor releases without breaking changes.
2. **Rules**: every profile rule cites a measurement that still reproduces from the repo,
   and rule IDs are frozen (new rules add IDs, never reuse).
3. **Numbers**: the published leaderboards regenerate from a clean checkout within
   tokenizer tolerance (±1%); grade constants change only with a major version.
4. **Robustness**: the PBT suite + fuzz corpus run green across the 3-OS matrix for two
   consecutive releases; malformed input never crashes (degrades to best-effort).
5. **Ecosystem check**: at least one external consumer (CI user, badge adopter, or a spec
   discussion citing the numbers) confirms the interfaces are load-bearing — 1.0 is a
   promise to *others*, so someone else must be holding the API when we freeze it.

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
page + JSON + monthly history, cron refresh). v0.6 N10 done — `docs/POST.md`: blog post +
Show HN + r/mcp drafts ready to paste (owner publishes). v0.6 N8 done — validation matrix v2
(Haiku k=5 complete: code_exec 50/50 AND cheapest right answer at 1977 tok, 2.9× cheaper than
naive; numbered measurably worst; DSL gap category-shaped). N8b done after credit top-up —
Sonnet complete (248/250): **cheapest right answer is model-dependent** (Sonnet's code runs
cost 5345/correct, near-naive; its query wins at 1902). **v0.6 COMPLETE. v0.7: C1 done
(CONTRIBUTING + templates), M1 done (projected bucket-C), V1 done (compressor banner
root-caused), M2 done (cache economics), S1 done (`lap fix` — lint findings as an applicable
OpenAPI Overlay; Bookstore B72 → A91 from its own patch), M3 done (query params in menu forms —
naive total +7.2% → 11.2M, compact save now 82%/search 86%, Spotify B→C; all generated docs
refreshed), M4 done (tokenizer sensitivity: τ ≥ 0.992), **0.5.0+0.5.1 RELEASED 2026-07-07**
(PyPI + GitHub; 0.5.1 = docs-only, PyPI page + root README rewritten useful-first), S2 done
(rule D0 + llms.txt scan: 47% adoption — discovery is getting solved, efficiency isn't).
**v0.8 plan drawn 2026-07-08** from a fresh landscape re-check (MCP spec final lands
**2026-07-28** → a real deadline, #2808 appears closed; Claude Code enabled Tool Search by
default; agent-friend/AgentDX appeared, both tiny; LAP still at 5 stars) — open v0.7 track
items folded in as P4/P5/P6. **P1 done** — #2808 → discussion #2812 (closed 2026-05-29,
converted); draft spec adopted none of its proposals; `lint.flat_schema()` fix shipped (composed
inputSchemas visible to M-rules/compact; 29% of real generated tools already carry 2020-12
constructs); SPEC-2808.md retargeted + comment rewritten for #2812; CACHE-ECONOMICS "transport
not context" section; 60 tests green. **The #2812
comment is POSTED (2026-07-08, owner-authorized; a twice-daily scheduled watch reports new
replies).** **P2 done** — MCP-server leaderboard: 20 popular servers scored credential-free
(Notion 21,411 tok F; ~64k total across 20; agent-friend cross-check: grades converge on
Notion, diverge on postgres/context7 — letters are formula artifacts, tokens are the
measurement); live-page link + monthly cron + FIELD.md updated. **P5 done** — POST.md
refreshed (MCP-leaderboard is the new r/mcp hook), docs/LISTINGS.md ready-to-submit texts,
7 GitHub topics set, pyproject keywords 14. **P3 done** — 35×-vs-CLI claim refereed
(docs/MCP-VS-CLI.md: naive-client magnitude real, 27× by 8 turns on menu alone; collapses
under Tool Search/compact; GitHub MCP scored directly at last: 44 tools/11,461/B). **P6 done** — PBT found+fixed 10
crash sites the fuzz corpus missed; perf verdict: tokenizer is the wall (inline_refs innocent);
CI now 3 OS × 2 Python, all green. **0.6.0 FULLY RELEASED 2026-07-09** (PyPI + GitHub,
fresh-venv verified; P4 deferred by owner's call). **2026-07-10: plan re-drawn → v0.9 W1–W8**
(trigger: our mcp-compressor report got **fixed upstream in a day** — issue #236 closed
"completed", PR #237 merged; agent-friend dormant; spec final Jul 28). P4 → W3. **W1 done** —
fix verified against released 0.31.5 (banner now symmetric: git@medium 41.9% vs our 41.0%
chars; sign flip gone), MCP-COMPRESSOR/FIELD/POST updated. **W4 done — all three issues POSTED
2026-07-10** (servers#4507, firecrawl#309, notion#330; seq-thinking −50%, firecrawl −50%,
Notion −69% from $defs dedupe alone; watch extended to 5 threads).
**W6 done** — Arazzo
macro-tools measured on the OAI examples (menu −50…97%; B wins grow with chain length,
tiny flows pay more; intermediate C never enters context — structural) + the x-lap strawman
(4 keys). **W7 done** — stable Python API (score_spec/lint_spec/grade_spec/diff_specs),
`--diff --git`, pre-commit recipe, the written 1.0 bar; 66 tests green.
**0.7.0 FULLY RELEASED 2026-07-10** (PyPI + GitHub, fresh-venv verified). ▶ **W2** fires
~Jul 28 (reminder scheduled); W3/W5 stay `[key]`; W8 after Aug 3; otherwise v0.9 is done
pending replies to the 5 watched threads. **The mcp-compressor issue is POSTED
(2026-07-09, owner-authorized): [atlassian-labs/mcp-compressor#236](https://github.com/atlassian-labs/mcp-compressor/issues/236).**
Owner actions still pending: POST.md publishing + LISTINGS.md submissions.**
Say "continue LAP" to keep going.
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
