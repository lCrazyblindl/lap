# The Agentic-Web Landscape (June 2026) — and where LAP fits

## Why this doc

LAP is an open, neutral **token-efficiency measurement + guidance** layer for
agent-facing APIs. Before building more, we mapped what already exists, so LAP
**complements** the ecosystem instead of duplicating it. This is that map, with
sources, and an explicit statement of LAP's niche.

## The shared problem

As agents proliferate, two costs dominate: **token/context bloat** (tool definitions
and results eat the model's context — Anthropic has reported tool definitions alone
consuming ~134K tokens before the first question) and the **connective tissue** of
letting an agent reach an arbitrary API at all (discovery, auth, trust). The industry
is attacking both, hard.

## The landscape, by layer

### 1. Discovery — how an agent finds/understands a site's capabilities
- **llms.txt** — a `/llms.txt` file pointing LLMs at a site's key content. ~10% adoption
  (inflated by Shopify auto-enabling it); IDE agents (Claude Code, Cursor, Copilot) read it.
  The first widely-adopted "Business-to-Agent" file. Google declines to support it.
- **Microsoft NLWeb** — an open project/protocol that makes any site conversational and
  **agent-accessible**; each NLWeb instance acts as an MCP server exposing `/ask` + `/mcp`,
  built on Schema.org/RSS/sitemaps. "Agents don't need custom integrations for every site."
  Adopters: Shopify, Tripadvisor, Eventbrite, O'Reilly, Hearst.
- **A2A Agent Cards** — discoverable JSON declaring an agent's auth schemes + capabilities.

### 2. Interface / access — how the agent calls capabilities
- **MCP** — the de-facto standard for exposing tools to LLMs.
- **OpenAPI→MCP generators** — Speakeasy, Stainless, FastMCP, openapi-mcp: one command
  turns an OpenAPI spec into an MCP server.
- **Code execution** — Anthropic "Code execution with MCP" and Cloudflare "Code Mode" let
  the model write code against a typed API in a sandbox instead of many tool calls.
- **GraphQL / OData** — declarative query layers (Apollo MCP, WunderGraph) as the read shape.

### 3. Gateways + auth — who brokers access, credentials, policy
- **Open-source MCP gateways:** AWS MCP Gateway & Registry (OAuth DCR, biweekly releases),
  Hypr (1-click OAuth + DCR), atrawog/mcp-oauth-gateway ("OAuth 2.1 for any MCP server, no
  code changes"). They wrap auth + policy + discovery for you.
- MCP adopted **OAuth 2.1 + RFC 9728** (protected-resource metadata) so agents discover auth
  requirements dynamically.

### 4. Identity standards — who is this agent, on whose behalf
- **NIST AI Agent Standards Initiative** (Feb 2026); **IETF draft-klrc-aiagent-auth**; built
  on OAuth/OIDC/SPIFFE/WIMSE. Open problem: **multi-hop delegation** (A→B→C).

### 5. Efficiency patterns — making the above cheap in tokens
- Anthropic **code execution** (~98.7% token cut on a workflow), **Tool Search** (~85% via
  lazy tool loading), Cloudflare **Code Mode** (~99.9% on a 2,500-endpoint API), MCP
  **SEP-1576** (token-bloat mitigation: schema dedup, embedding tool-select, progressive
  disclosure).

## The gap LAP fills

Across all of the above, one thing is conspicuously absent: a **neutral, reproducible way
to measure how token-efficient a given agent-interface actually is**, decomposed and
comparable. Each vendor cites its own headline number on its own setup; SEP-1576 names the
problem but ships no measuring stick. There is no "is my agent-API efficient, and by how
much, versus the alternatives?" — per task, per bucket.

| layer | well-covered by | LAP |
|---|---|---|
| discovery | NLWeb, llms.txt, A2A | references, doesn't rebuild |
| interface / access | MCP, generators, code-exec, GraphQL | references, doesn't rebuild |
| gateways + auth | AWS / Hypr / atrawog, OAuth 2.1 + DCR | references, doesn't rebuild |
| identity | NIST, IETF, A2A | references, doesn't rebuild |
| **efficiency measurement** | **— (nobody, neutrally)** | **← LAP's niche** |

## LAP's niche

LAP is the **measurement + guidance** layer:
- **token-bench** — point it at an interface, get its cost in three buckets (**A**
  definitions, **B** call, **C** result), comparable across variants (plain/real MCP,
  compact, query, code…).
- **the LAP profile** ([`../profile/llm-api-profile.md`](../profile/llm-api-profile.md)) —
  measured, opinionated conventions (compact familiar discovery, minimal writes,
  shaped/aggregated reads, code escape hatch) for token-efficient APIs.
- planned: `lap score` / `lap lint` — a conformance score + concrete, measured fixes for any
  OpenAPI / MCP / NLWeb interface.

**Explicit non-goals:** LAP does not build auth brokers, gateways, discovery registries,
hosting, or agent identity — those are covered above. LAP measures and guides; it cites the rest.

## Why it helps everyone

Anyone building on MCP/NLWeb wants their agent-API fast and cheap, but has no neutral
yardstick. LAP gives the ecosystem a shared, reproducible one — a public good, not a product.

## Sources

- llms.txt (2026 state/adoption): https://codersera.com/blog/llms-txt-complete-guide-2026/ · https://caseyrb.com/blog/state-of-llms-txt-adoption/
- Microsoft NLWeb: https://news.microsoft.com/source/features/company-news/introducing-nlweb-bringing-conversational-interfaces-directly-to-the-web/
- MCP gateways: AWS https://aws.amazon.com/blogs/opensource/governing-ai-assets-at-scale-with-mcp-gateway-and-registry/ · Hypr https://github.com/hyprmcp/mcp-gateway · atrawog https://github.com/atrawog/mcp-oauth-gateway
- Agent identity: NIST https://workos.com/blog/nist-ai-agent-standards-initiative-explained · IETF https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/
- Efficiency: Anthropic code-exec https://www.anthropic.com/engineering/code-execution-with-mcp · Cloudflare Code Mode https://blog.cloudflare.com/code-mode-mcp/ · MCP SEP-1576 https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1576
- OpenAPI→MCP: Speakeasy https://www.speakeasy.com/blog/generate-mcp-from-openapi · FastMCP https://gofastmcp.com/integrations/openapi
- GraphQL for agents: Apollo https://www.apollographql.com/blog/building-efficient-ai-agents-with-graphql-and-apollo-mcp-server
