# lap — how many tokens does your API cost an LLM agent?

Point `lap` at any OpenAPI spec, live MCP server, or your own agent config and get the
**token cost decomposed** (definitions / call / result), a **0–100 grade**, the concrete
**rule violations** driving the cost — and an **applicable patch** for the fixable ones.
Neutral, offline-capable, MIT.

```bash
pip install "lap-score[mcp]"
```

## The five commands

```bash
lap stack                                  # YOUR installed MCP servers: "N tokens before you type a word"
lap score  openapi.json                    # A/B/C token decomposition + the LAP grade
lap lint   openapi.json                    # which rule violations drive the cost (CI-gateable; --discovery probes /llms.txt)
lap lint   --mcp "python -m mcp_server_git"   # ...same for a live MCP server (stdio or --mcp-url)
lap fix    openapi.json --apply patched.json  # the fixable findings as an OpenAPI Overlay patch
```

What that looks like:

```
$ lap stack
  server        kind   tools  menu tokens  compact
  time          stdio      2          283       31
  git           stdio     12         1418      153
  TOTAL                    14         1701      184
Your agent pays ~1,701 tokens of tool menus at session start - before you type a word.
Compact signatures of the same tools would cost 184 (+89% saved).

$ lap score api/openapi.json
LAP grade: B (72/100)   [menu 100  result 90  hygiene 0]
  variant       A tokens  saved vs full
  openapi_full  418       +0%
  compact_sig   205       +51%
  tool_search   163       +61%
Estimated call size (bucket B): mean ~18 tokens/call ...
Estimated result size (bucket C): GET /books ~465 tokens (list) -> ~305 if projection were added (R1)

$ lap fix api/openapi.json --apply patched.json
[written] lap-overlay.yaml  (6 action(s))
[written] patched.json  (lint findings: 15 -> 3)      # grade: B (72) -> A (91)
```

`lap fix` emits a standard [OpenAPI Overlay 1.0.0](https://spec.openapis.org/overlay/v1.0.0)
(R3 → `limit` param, R1 → `fields`, R2 → `filter`, E1 → declared `4XX`) — it declares the
contract; your server still implements it. `lap badge <spec>` writes a shields.io endpoint
JSON so your README can carry the grade.

## CI gates

Every command is `--json`-able and can fail a build:

```bash
lap score openapi.json --gate-form compact_sig --max-menu-tokens 800   # menu too heavy
lap score --diff old.json new.json --max-growth 500                    # this PR bloated the menu
lap lint  openapi.json --fail-on warn                                  # rule violations (--ignore R2,A1 / .lapignore)
```

…or the bundled composite Action:

```yaml
- uses: lCrazyblindl/lap@v0.5.0
  with:
    spec: api/openapi.json
    max-menu-tokens: "800"
    fail-on: warn
    badge-path: docs/lap-badge.json   # optional: grade badge JSON
```

(Prefer Spectral? The same rules ship as a
[Spectral ruleset](https://github.com/lCrazyblindl/lap/tree/main/spectral).)

## Reading the numbers

- **Bucket A** (measured) — the tool-definition menu the model carries *every session*,
  under four renderings: naive OpenAPI→tools, compact signatures, numbered, lazy
  `tool_search`. With `fastmcp` installed, a real-MCP baseline row too.
- **Buckets B / C** (estimated from the schemas) — the call the model emits (required args
  in a tool-use envelope) and the result that comes back (per response schema, page-size
  aware, envelope-aware, real `example` values honored). Structural lower bounds. List
  responses also get a **projected** figure — what field projection would save, per endpoint.
- **The grade** — menu tokens/operation (weight 0.45) + heaviest result (0.30) + lint
  findings/operation (0.25), log-scaled;
  [formula](https://github.com/lCrazyblindl/lap/blob/main/profile/llm-api-profile.md).
  Calibration: LaunchDarkly **B**, Spotify **C**, GitHub **D**, Google Drive **F**.
- **Tokenizer** — offline = tiktoken approximation (absolutes ≈, ordering robust: checked
  under [4 BPE vocabularies](https://github.com/lCrazyblindl/lap/blob/main/docs/TOKENIZERS.md),
  Kendall τ ≥ 0.992). Set `ANTHROPIC_API_KEY` for faithful `count_tokens` figures.
- Parses OpenAPI 3.x **and** Swagger 2.0, YAML, `allOf/oneOf/anyOf`, `$ref`s, non-JSON media
  types; crash-free across 175+ real APIs.guru specs.

## The receipts

Every number and rule has a reproducible measurement behind it:
the [live leaderboard of 50 real APIs](https://lcrazyblindl.github.io/lap/) (naive menus
total ~11.2M tokens; ~82% recoverable),
the [LAP profile](https://github.com/lCrazyblindl/lap/blob/main/profile/llm-api-profile.md)
(every rule cites its experiment), and the
[state of the field](https://github.com/lCrazyblindl/lap/blob/main/docs/FIELD.md) —
which vendor claims we verified live, and which our measurements dispute.
Issues/PRs: [CONTRIBUTING](https://github.com/lCrazyblindl/lap/blob/main/CONTRIBUTING.md)
(there's a "Score my API" issue template — disputes welcome).

## Module map

| file | role |
| --- | --- |
| `openapi_ir.py` | any OpenAPI (file/URL) → normalized operations |
| `menu.py` | the menu forms (naive / compact / numbered / tool_search) |
| `estimate.py` | bucket B/C estimates (+ projection what-ifs) |
| `lint.py` / `overlay.py` | rules (OpenAPI + live-MCP M-rules) / `lap fix` Overlay |
| `grade.py` | the composite grade + `lap badge` |
| `stack.py` / `mcp_client.py` / `mcp_form.py` | your MCP stack / live servers / real-MCP baseline |
| `tokens.py` / `score.py` | counting backends / the `lap score` CLI |
| `examples/` | bundled sample specs (Bookstore, gnarly 3.1, Swagger 2.0) |
