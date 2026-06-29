# lap — token-efficiency scorer for agent-facing APIs

`lap` is the open, neutral, standalone toolkit (no pet-zoo dependency) that measures
how many **tokens** an API's definitions cost an LLM. It answers: *is my agent-API
menu efficient, and by how much could it shrink?* — the reproducible number the
agentic-web ecosystem lacks (see [`../docs/LANDSCAPE.md`](../docs/LANDSCAPE.md)).

## Quickstart

```bash
# deps (or reuse the repo .venv): httpx, tiktoken, anthropic
python -m lap.score lap/examples/bookstore.openapi.json
python -m lap.score https://petstore3.swagger.io/api/v3/openapi.json
```

Example output:

```
LAP menu score - Bookstore API
operations: 6   referenced component schemas: 2

  variant       A tokens  saved vs full  form
  openapi_full  418       +0%            6 tool(s)
  compact_sig   205       +51%           manifest text
  numbered      168       +60%           manifest text

Menu efficiency: compact signatures are +51% vs naive OpenAPI->tools (418 -> 205 tokens).
```

- **Faithful counts:** set `ANTHROPIC_API_KEY` (uses the free Anthropic `count_tokens`
  endpoint; tool defs counted via the real `tools=` parameter). Without it, a GPT-style
  `tiktoken` approximation — absolute numbers approximate, **relative ordering robust**.

## What it measures (and what it doesn't)

It scores **bucket A** — the definitions/menu the model carries in context, which is
intrinsic to the interface and the biggest cacheable cost. **B** (the call) and **C**
(results) depend on per-API tasks; for a full A/B/C run see
[`../experiments/token-bench`](../experiments/token-bench/README.md). The conventions
behind the compact form are the [LAP profile](../profile/llm-api-profile.md).

## Files

| file | role |
| --- | --- |
| `openapi_ir.py` | load any OpenAPI (file/URL) → normalized operations + `inline_refs` |
| `menu.py` | render the menu forms (openapi_full / compact_sig / numbered) from the IR |
| `tokens.py` | token counting (Anthropic endpoint, or tiktoken approx) |
| `score.py` | the `lap score` CLI |
| `examples/` | sample specs (e.g. a non-pet-zoo Bookstore API) |
