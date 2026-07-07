# Changelog

All notable changes to **lap** (PyPI package `lap-score`) are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/); loose semantic
versioning while pre-1.0.

## [Unreleased]

### Added
- **Projected bucket-C estimate** — for every list response, `lap score` now also reports
  what the page would cost under field projection (each item cut to its first 3 schema
  fields, envelope metadata kept), and whether the operation actually advertises a
  projection affordance (`fields=`/`$select`/sparse fieldsets). Rule R1's saving becomes a
  per-endpoint number: `~465 tokens (list) -> ~305 if projection were added (R1)`. In
  `--json` as `projected` + `has_projection` on list entries of `estimated_c`.

## [0.4.0] — 2026-07-06

The toolkit closes the loop: **A/B/C in one command**, a composite **LAP grade** with a README
badge, and full **MCP-side parity** (score, lint, and your whole installed stack).

### Added
- **Bucket-B (call) estimate in `lap score`** — the full A/B/C story in one command: for each
  operation a typical invocation is synthesized (tool name + **required** args — path params
  always, optional query params omitted, request-body `required` fields honored, real schema
  examples win) and counted in a minimal tool-use envelope; `lap score` reports the mean and the
  heaviest call (human + `--json` `estimated_b`). A structural lower bound, like the C estimate.
- **`lap lint --mcp-url <url>` / `--mcp "<stdio command>"`** — lint a *live MCP server's*
  advertised tools, not just OpenAPI: D3 (opaque names) carries over, plus new M-rules —
  M1 missing/short tool description, M2 undescribed input parameters, M3 heavy tool
  definition (>~600 tokens; MCP spec issue #2808 territory), M4 no `required` list — and
  the composite LAP grade (menu + hygiene; the result sub-score is skipped since MCP tool
  listings don't declare response shapes). Reference check: `mcp-server-time` **A (89)**,
  `mcp-server-git` **B (71)**. Also fixed a Windows-console crash (`✓` on cp1251) and
  stdio-subprocess teardown noise (`keep_alive=False`).
- **The composite LAP grade + `lap badge`** — `lap score` now prints one documented 0–100
  grade with a letter (A–F): menu tokens/operation (0.45) + heaviest estimated response (0.30)
  + lint findings/operation (0.25), log-scaled, constants in `lap/grade.py`, formula in the
  profile. `lap badge <spec> -o lap-badge.json` writes a shields.io endpoint JSON so any repo
  can carry an "LAP B (72)"-style README badge; the bundled GitHub Action gained a
  `badge-path` input. Calibrated on the 50-API leaderboard corpus (Spotify **B**, Postman
  **C**, GitHub **D**, Google Drive **F** — **A** requires real pagination/projection/error
  discipline, by design).
- **`lap stack`** — score *your installed MCP stack*: reads the agent's own config (Claude Code
  `.mcp.json` / `~/.claude.json`, Claude Desktop `claude_desktop_config.json`, or any JSON with
  an `mcpServers` map), connects to every listed server (stdio or HTTP), and totals the menu
  (bucket A) tokens the agent pays at session start — "N tokens before you type a word" — plus
  compact and stack-wide `tool_search` what-ifs. Unreachable servers become annotated rows, not
  crashes. Needs the `[mcp]` extra.
- **`lap score --diff <before> <after>`** — compare two versions of a spec: the menu (bucket A)
  token delta per interface form, plus which LAP lint findings were newly introduced or fixed.
  `--max-growth` turns it into a CI gate ("did this PR make the API worse for agents?").
- **`--string-len`** on `lap score` — configurable placeholder length for un-exampled string
  fields in the bucket-C estimate (default 6, unchanged).

### Fixed
- **Bucket-C estimate now prefers a schema's real `example`/`examples` value** over a synthetic
  placeholder wherever present — real data an API author wrote down, so strictly more accurate
  than a guess. Regenerated `docs/LEADERBOARD.md`: of 48 comparable rows, **41 grew, 1 shrank, 6
  were unchanged** (no examples in those schemas); the total heaviest-result estimate across the
  leaderboard rose ~41% (482,795 → 681,830 tokens) — the previous placeholder-only estimate was
  undercounting real payload sizes wherever specs actually documented example values.

## [0.3.0] — 2026-06-30

First public release of the full toolkit: a **scorer**, a **linter**, the **LAP
profile**, and a reproducible **token benchmark**.

### Added
- **`lap score <openapi>`** — bucket-A (menu) token cost across `openapi_full` /
  `compact_sig` / `numbered` / `tool_search`, a real-MCP baseline (via FastMCP), and a
  bucket-C result-size estimate. `--json`, `--mcp-url <url>`, and a CI gate
  (`--gate-form` + `--max-menu-tokens`).
- **`lap lint <openapi>`** — flags LAP rule violations (D3 / R1 / R2 / R3 / W1 / E1 / A1);
  `--json`, `--ignore` / `.lapignore`, and a `--fail-on` gate.
- **LAP profile v1.0** (`profile/llm-api-profile.md`) with conformance levels L1–L4.
- **token-bench** — 10 tasks across 5 categories (write / aggregate-read / peek-read /
  multi-step / beyond-DSL) with per-category averages, a code-exec sandbox self-check
  (`--check-code`), and an optional live **success-rate matrix** (`--matrix`).
- **`docs/LEADERBOARD.md`** — agent-menu token cost of 20 real public APIs.
- **`experiments/fuzz_corpus.py`** — parser fuzz harness over real APIs.guru specs.
- A composite **GitHub Action** (`action.yml`) to run `lap score` / `lap lint` in CI.
- A **Spectral ruleset** ([`spectral/`](spectral/README.md)) porting the lint rules
  (D3/R1/R2/R3/W1/E1/A1) for teams already linting OpenAPI with Spectral/vacuum; executed and
  asserted in CI on the bundled example.

### Fixed
- Parser now reads **Swagger/OpenAPI 2.0** (response `schema`, `in: body` params,
  type-on-parameter, `#/definitions`) and **non-JSON media types** (`*+json`, form, XML) —
  previously these specs produced empty/void output.
- `tiktoken` no longer crashes on control strings such as `<|endoftext|>` that appear
  verbatim in real specs (e.g. OpenAI's).
- **Bucket-C estimate is envelope-aware**: a list wrapped in an object (Stripe/JSON:API
  `{"data": [...]}`, Kubernetes `{"items": [...]}`, OData `{"value": [...]}`) is now scaled to
  a full page with its sibling fields kept, instead of being scored as a tiny "object" — the
  previous estimate undercounted real, enveloped API responses (15 of 20 leaderboard rows
  changed once this was fixed).

### Validated
- Faithful Anthropic `count_tokens`: same relative ordering as the tiktoken approximation.
- Live success-rate matrix (Claude Haiku, k=3): **compression did not cost accuracy**
  (compact/numbered/code/query ≥ the naive baseline, at far fewer tokens).
- Crash-free across **175+** real APIs.guru specs.
- **Real-tool validation track** (not just our own interface variants): three real
  OpenAPI→MCP generators and three real published MCP servers all emit menus heavier than
  naive and far heavier than compact (`docs/GENERATORS.md`, `docs/MCP-SERVERS.md`); a live
  end-to-end run on the hosted Swagger Petstore found compression **helped** accuracy, not
  just tokens (`experiments/token-bench/validation-real.md`); Anthropic's real **Tool Search**
  cut billed tokens ~90% at real scale, server-enforced regardless of model behavior
  (`docs/TOOL-SEARCH.md`); Anthropic's real **code-execution**, tested the same way, came in
  *heavier* than both naive and our own sandbox on one run — its saving is behavioral, not
  structural (`docs/CODE-EXEC.md`). See `docs/LEADERBOARD.md` for the 20-real-API dataset this
  release ships alongside the code.

[0.4.0]: https://github.com/lCrazyblindl/lap/releases/tag/v0.4.0
[0.3.0]: https://github.com/lCrazyblindl/lap/releases/tag/v0.3.0
