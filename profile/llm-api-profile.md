# LLM-API Profile (LAP) — v1.0

**Status:** v1.0 — the rules and conformance levels are stable. Each rule is backed by
a measurement from [`experiments/token-bench`](../experiments/token-bench/README.md).
The numbers are **preliminary** but now include a small success-rate check. On Claude's real
tokenizer (faithful `count_tokens`) the relative ordering matches the tiktoken approximation
(~60% higher in absolute terms). On a live **success-rate matrix** (Claude Haiku, one task per
category × 3 repeats, `numbered` included), **compression did not cost accuracy**: `numbered`,
`code_exec` and `odata_query` scored 15/15, `compact_sig` 14/15, and the naive `openapi_full`
baseline came *last* at 13/15 (both misses on the aggregate-count task) — while the compact menu
used ~1.4× and the code/query forms ~3–4× fewer total tokens. **Caveats:** one cheap model, k=3
(noisy at n=3), one toy API (pet-zoo) — indicative, not a broad benchmark; raw table in
[`experiments/token-bench/validation.md`](../experiments/token-bench/validation.md). (Faithful
e.g.: a real MCP menu 2752 tokens vs 634 for compact signatures.)
**Tooling:** `python -m lap.score <openapi>` measures any API's menu cost;
`python -m lap.lint <openapi>` flags violations of the rules below.

**Purpose:** an opinionated convention for exposing an HTTP API so an LLM uses it
with the fewest tokens — *without inventing a new wire format*.

## Not a protocol — a profile

LAP is a set of conventions **on top of HTTP / JSON / OpenAPI** (plus OData and
RFC 7240 idioms). It adds no new wire format. Reason: an LLM's competence is
**distributional** — it is fluent in formats it saw a lot of in pretraining
(HTTP/JSON/REST/SQL) and poor at novel compact encodings. So we ride familiar
standards and constrain *how* they are used, rather than invent a terse dialect
(which loses on reliability and — since tokens ≠ characters — usually on tokens too).

## Principles

1. Optimize **tokens, not characters**.
2. **Ride standards the model already knows** (no cold-start).
3. Spend tokens on the **response, not the request** (the request is the cheapest part).
4. **Minimize round-trips** — each round-trip is a full inference pass.
5. **Minimal by default**, more on explicit opt-in.

## What we optimize: three token buckets

- **A** — definitions / menu in context (paid ~once per session, cacheable).
- **B** — the call the model emits (smallest; do not micro-optimize it).
- **C** — results fed back into context (largest at runtime, un-cacheable).

LAP targets **A** and **C**. (Compressing **B** — e.g. numbering endpoints — is a
measured net loss; see rule D3.)

## Conformance levels

| level | adds | targets |
|---|---|---|
| **L1 Compact** | compact familiar discovery + minimal-by-default writes + uniform errors | A, C (writes) |
| **L2 Shaped reads** | projection + filter + pagination + truncation count signal | C (reads) |
| **L3 Aggregation** | server-side count / group / basic stats | C (compute-over-many) |
| **L4 Escape hatch** | sandboxed code execution for what the query layer can't express | C (arbitrary compute) |

A provider adopts the highest level worth its task distribution.

## Rules

### Discovery — bucket A
- **D1** Describe operations as compact, familiar signatures (TS-like) or trimmed OpenAPI, not full JSON-Schema dumps. *Evidence: 401 vs 1637 tokens (compact_sig vs openapi_full); a real FastMCP server is 1689, or 3762 with output schemas.*
- **D2** When endpoints are many, expose them lazily / searchably (a search-then-fetch step) instead of dumping all definitions up front. *Evidence: industry Tool Search ≈ −85% (vendor-reported); we independently verified this live on a real 290-operation API — Anthropic's real Tool Search cut billed tokens ~90% versus the identical schemas without it, server-enforced regardless of model behavior (`docs/TOOL-SEARCH.md`). Caveat: not worth it below ~10 tools, where the search round-trip itself costs more than it saves.*
- **D3** Do **not** encode operations as opaque codes/numbers. *Evidence: `numbered` total ≥ `compact_sig` total — a net loss, because the codebook still costs bucket A while saving only ~2 tokens of bucket B. The v2 validation matrix adds an accuracy penalty on small models (46/50 vs compact's 48/50, with a 2/5 collapse on an aggregate task).*

> **"But isn't the menu prompt-cached anyway?"** Caching is a *price* multiplier (≥0.10×,
> and fragile — any tool change or a TTL-length idle gap re-bills the 1.25× write), while
> menu form is a *token* multiplier (~0.2×, robust, and it also frees context-window
> capacity, which caching does not). They multiply rather than compete: lean menu (D1),
> defer where possible (D2), then cache what remains. Priced out with real menus in
> [`docs/CACHE-ECONOMICS.md`](../docs/CACHE-ECONOMICS.md) — compact+cached runs ~13–2000×
> cheaper per 8-turn session than naive uncached, depending on API size.

### MCP tools — bucket A (the MCP-side counterparts, checked by `lap lint --mcp-url/--mcp`)
D3 carries over to MCP tool names unchanged. What an MCP tool can get wrong that an
OpenAPI operation expresses differently:

- **M1** Every tool needs a real description (≥ a sentence): the model decides *when to
  call it* from that text — a wrong-tool call costs far more than the sentence.
- **M2** Every input parameter needs a description; otherwise argument semantics get
  guessed (`repo_path` on every tool of a well-known reference server ships undescribed).
- **M3** Keep a single tool's definition under ~600 tokens — every session pays it,
  used or not (MCP spec issue #2808 measured real production tools at 103–1024 tokens);
  trim the description/schema or defer it behind tool search (D2).
- **M4** If a tool declares parameters, mark which are `required` — the model can't
  tell mandatory from optional otherwise.

*(For MCP servers the LAP grade uses the menu + hygiene sub-scores only — result sizes
aren't declared in MCP tool listings, so that sub-score is skipped and weights
renormalize. Reference check, 2026-07: `mcp-server-time` grades **A (89)** — clean;
`mcp-server-git` grades **B (71)** — two short descriptions, `repo_path` undescribed
in 11 of 12 tools.)*

### Reads — bucket C
- **R1** Support field projection (`?fields=` / OData `$select`). Default to a small curated field set; full object on opt-in.
- **R2** Support server-side filtering (OData `$filter`-style).
- **R3** Support pagination; default to a **sane page size, not 1** (a default that is almost always insufficient guarantees an extra round-trip).
- **R4** When a response is truncated, include the **total count and a continuation cursor** (`@odata.count` / `nextLink`) so the model knows more exists — otherwise minimal defaults cause silent-truncation wrong answers.

### Aggregation — bucket C
- **A1** Support server-side aggregates (count, group-by-count, basic stats) so "compute over many" returns a small result instead of the whole list. *Evidence: T2/T3 result bucket ≈ 5–19 tokens vs ≈ 1161 for the full list.*

### Writes — bucket C
- **W1** Default to a **minimal response** (`Prefer: return=minimal`): status plus only server-generated fields (e.g. the new `id`); full representation on opt-in. *Evidence: T1 result 5 vs 22 tokens.*

### Errors — reliability
- **E1** Uniform, explicit outcomes: success-with-data, success-empty, and error must be unambiguously distinguishable (an empty body must not mean two different things).

### Escape hatch — bucket C, arbitrary compute
- **X1** For computations the query layer can't express, offer a **sandboxed code-execution** endpoint that returns only the final value. *Evidence: T5 (argmax over a computed property) — result 13 (code) vs 561 (query projection) vs 1161 (full list).*
  > **A real-world caveat, not just theory:** unlike R1/R3/A1 (enforced by the endpoint's own shape — the model can't opt back into a bigger response), X1's saving is **behavioral, not structural**. We tested Anthropic's own real code-execution tool live, repeated 5× (`docs/CODE-EXEC.md`): **every one of 5 runs** cost *more* tokens than both the naive baseline and our own hand-rolled sandbox — not a fluke. The verified mechanism: the model consistently needed 2-4 execution attempts to get the sandboxed file path right (a wrong guess, then a retry), and each extra attempt re-sends the growing turn history. Our own sandbox has no equivalent failure mode — an injected client object can't be given a wrong path, because there is no path to get wrong. Offering the escape hatch is necessary but not sufficient — nothing stops a calling agent's own mistakes from re-inflating the very cost the hatch exists to avoid. (Contrast with D2's Tool Search, `docs/TOOL-SEARCH.md`, which *is* server-enforced and held up at ~90% real savings regardless of model behavior.) The v2 validation matrix (`experiments/token-bench/validation.md`, 500 runs) reproduced this in **our own** sandbox: on Haiku, code was the cheapest correct answer (1977 tokens, 2.9× cheaper than naive) — on Sonnet the *same* sandbox cost 5345 tokens per correct answer, nearly naive-priced, because the stronger model writes exploratory multi-attempt code. The cheapest form is model-dependent; only the small-result guarantee is structural.

> The query layer (L2–L3) and the escape hatch (L4) are two points on one spectrum.
> Extending the query DSL covers more tasks but grows its menu (bucket A) toward a
> programming language; at the limit a maximally expressive DSL *is* code execution.
> Pick the point that covers your task distribution at the least A + risk.

## Conformance & scoring

Conformance is **measured, not asserted**. For a quick check on any spec,
`python -m lap.score <openapi>` reports the menu (bucket A) cost (incl. a real-MCP
baseline) and `python -m lap.lint <openapi>` flags rule violations (D3 / R1 / R2 / R3 /
W1 / E1 / A1). For a full A/B/C run with tasks, use
[`token-bench`](../experiments/token-bench/README.md); the LAP "score" is that profile
versus the naive OpenAPI→tools baseline. Use real-tokenizer mode (`ANTHROPIC_API_KEY`)
for quotable numbers, and `--live` to check that the savings don't cost accuracy.

### The LAP grade (composite 0–100 + letter)

For an at-a-glance summary — and a README badge (`lap badge`) — `lap score` folds its
measurements into one documented number. Three sub-scores, each 0–100:

- **menu (weight 0.45)** — naive-menu (bucket A) tokens **per operation**: definition
  cost per unit of capability. Log-scaled: 100 at ≤80 tok/op, 0 at ≥2400 tok/op
  (calibrated on the [50-API leaderboard](../docs/LEADERBOARD.md): Swagger Petstore ≈92
  tok/op; Kubernetes-style fully-inlined schemas run >3000).
- **result (weight 0.30)** — the heaviest estimated single response (bucket C) at the
  default page size — the recurring per-call cost. Log-scaled: 100 at ≤300 tokens, 0 at
  ≥30 000. APIs with no estimable responses skip this sub-score (weights renormalize).
- **hygiene (weight 0.25)** — lint findings per operation, warnings double-weighted:
  100 at zero findings, 0 at ≥2 weighted findings/op.

Composite = weighted mean → **A ≥85, B ≥70, C ≥55, D ≥40, F below**. The letter is
only a summary: the full token decomposition behind it is one `lap score` away, and
every constant lives in [`lap/grade.py`](../lap/grade.py). Calibration check (2026-07,
tiktoken backend): Spotify and LaunchDarkly grade **B**, Postman **C**, GitHub and
DynamoDB **D**, Google Drive **F** — no sampled real API reached **A**, which requires
genuine pagination/projection/error discipline on top of a lean menu, by design.

## Non-goals (explicitly out of scope)

LAP addresses only the **token-efficiency of the interface shape**. It does **not**
solve — and these, not interface shape, are the main reasons universal LLM↔site
access lags today:

- **authentication / authorization / secrets** (per-provider, irreducible);
- **discovery / trust** (which endpoint, and is it legit);
- **hosting / secure operation** of the code escape hatch;
- **task success / correctness** (LAP optimizes tokens; success must be measured separately).

## References

MCP; MCP SEP-1576 (token bloat); Anthropic *Code execution with MCP*; Anthropic
*Tool Search*; Cloudflare *Code Mode*; OData (`$select`/`$filter`/`$top`/`$count`/`$apply`);
RFC 7240 (`Prefer: return=minimal`); GraphQL; OpenAPI.
