# Listing submissions (ready to send — owner submits under their account)

_v0.8 P5. Exact texts for getting `lap` listed where its users already look. Each entry is
self-contained: where, what to add, and the PR/submission text. Submit after (or alongside)
the POST.md publications — listing PRs land easier when the repo shows a little traction._

## 1. punkpeye/awesome-mcp-devtools (GitHub PR)

The de-facto tools list for the MCP ecosystem. Fork → add one line → PR.

**Where in the file:** the testing/linting/inspection section (named "Testing Tools" or
similar — match whatever heading holds MCP Inspector).

**The line:**

```markdown
- [lap](https://github.com/lCrazyblindl/lap) - Measure the token cost of MCP servers and OpenAPI specs: `lap lint --mcp` flags token-burning schema issues (CI gates included), `lap stack` totals what your installed servers cost per session, plus a monthly-refreshed token leaderboard of real APIs and servers.
```

**PR title:** `Add lap (token-cost measurement & linting for MCP servers)`

**PR body:**

> lap is an MIT, no-telemetry CLI that measures what MCP servers cost in context-window
> tokens: `lap lint --mcp "<command>"` lints a live server's tool definitions (missing
> descriptions, 600+-token tools, no `required` list) with CI gates; `lap stack` reads a
> Claude Desktop/Code config and totals the session-start cost of every installed server.
> It also maintains a monthly-refreshed token leaderboard of 50 public APIs and 20 popular
> MCP servers (https://lcrazyblindl.github.io/lap/). Fits next to MCP Inspector: Inspector
> is protocol-level testing, lap is token-cost measurement.

## 2. openapi.tools (GitHub PR to apisyouwonthate/openapi.tools)

The canonical OpenAPI tools directory. Entries are YAML; follow their CONTRIBUTING (one
tool per PR). Category: closest existing ones are "Description Validators" / "Linters".

**The entry (adjust key layout to the file's current schema):**

```yaml
- name: lap
  source: https://github.com/lCrazyblindl/lap
  language: Python
  v3_1: true
  v3: true
  v2: true
  categories:
    - linters
  description: >
    Measures what an OpenAPI description costs an LLM agent in tokens (menu / call /
    result), lints the token-burning patterns (no pagination, no field projection,
    undeclared errors), grades it 0-100, and emits fixes as an OpenAPI Overlay
    (`lap fix`). CI gate for menu-size regressions included.
```

**PR title:** `Add lap (LLM-agent token-cost measurement + lint for OpenAPI)`

## 3. MCP directory sites (web forms, not PRs)

- **mcp.so** and **mcpservers.org** list clients/tools via a submit form or a
  `Submit` issue — paste the awesome-mcp-devtools one-liner above.
- **Glama.ai** indexes from GitHub topics: make sure the repo has topics
  `mcp`, `model-context-protocol`, `openapi`, `llm`, `token-efficiency`
  (Settings → topics, or `gh repo edit --add-topic mcp --add-topic model-context-protocol
  --add-topic openapi --add-topic llm --add-topic token-efficiency`).

## 4. GitHub Action Marketplace (owner UI step, already release-ready)

From the latest release page: "Publish this Action to the Marketplace" — `action.yml` has
the required branding. Category: Continuous integration. One-time UI click; no CLI exists.
