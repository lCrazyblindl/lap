# Launch write-up (ready to publish)

_v0.6 N10, refreshed v0.8 P5. Three ready-to-paste drafts: a blog-style post, a Show HN, and
an r/mcp post. The owner publishes under their own account; adjust the personal voice ("I")
as you like. All numbers are reproducible from this repo at current main (0.5.1 + the
MCP-server leaderboard)._

---

## 1. The post (blog / dev.to / GitHub discussion)

# We measured the agent-menu tax of 50 real public APIs: 11.2M tokens

Every time an LLM agent connects to an API, it pays a hidden tax before doing anything:
the **tool definitions** — names, descriptions, JSON schemas — load into its context
window first. Vendors selling optimizations each publish their own percentage
(85%! 92.8%! 98.7%!), measured their own way, on their own workloads. Nobody neutral
was publishing comparable numbers.

So I built [**lap**](https://github.com/lCrazyblindl/lap) — an open, MIT-licensed
toolkit that measures the token cost of any agent-facing interface (OpenAPI or MCP) the
same way, decomposed into three buckets: **A** (the menu of definitions, paid once per
session), **B** (each call the model emits), **C** (each result that comes back). Then I
pointed it at 50 well-known public APIs. Highlights:

- **The naive menus total 11,175,074 tokens.** That's what generic OpenAPI→MCP bridges
  emit for these 50 APIs — what an agent would pay just to *see* them.
- **The heaviest single API menu is 4.04M tokens** (Xero Accounting; Kubernetes is 2.8M).
  These don't fit in *any* model's context window — an agent literally cannot load the
  API the way a naive bridge presents it.
- **~82% of that is recoverable with zero server changes.** Rendering the *same
  operations* as compact signatures saves +82% on average; a lazy tool-search menu saves
  +86%. Real OpenAPI→MCP generators we tested (FastMCP and two others) all emit menus
  *heavier* than naive — the savings are still on the table across the ecosystem.
- **Lazy loading flips negative on small APIs.** On 1–3-operation APIs, tool_search costs
  *more* than just showing the tools (NASA APOD: −311%). Anthropic's own "10+ tools"
  guidance, confirmed independently, in both directions.
- **The same ruler on 20 popular published MCP servers** (installed and run locally,
  zero credentials): menus run 42 → **21,411** tokens per session — the heaviest is
  Notion's official server; one reference server charges **921 tokens for a single tool**;
  connecting all 20 costs ~64k tokens before the first user message
  ([MCP-LEADERBOARD](https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-LEADERBOARD.md)).
- **Compression doesn't cost accuracy — but the cheapest *correct* answer is
  model-dependent.** A 500-run live matrix (2 models × 10 tasks × 5 menu forms × 5 repeats):
  every compact form matched or beat the naive menu's accuracy; on the small model,
  code-execution was the cheapest correct answer (2.9× cheaper than naive), on the stronger
  model a declarative query menu won and its own exploratory code cost near-naive
  ([validation.md](https://github.com/lCrazyblindl/lap/blob/main/experiments/token-bench/validation.md)).

The full ranking is a living page — regenerated monthly, history kept:
**https://lcrazyblindl.github.io/lap/**

## The part where vendor numbers didn't survive contact

The point of a neutral measurement layer is that sometimes it disagrees. Two cases so far
(all documented in [docs/FIELD.md](https://github.com/lCrazyblindl/lap/blob/main/docs/FIELD.md),
a registry of the field's headline claims marked *verified / plausible / disputed*):

- **Anthropic's Tool Search: verified.** Live, billed calls on a real 290-operation API:
  ~90% input-token reduction vs identical schemas without it — *better* than the headline,
  and server-enforced regardless of model behavior.
- **Code execution: disputed on our workload.** The famous "150k → 2k tokens" number is
  workload-specific. On a small live task, real code execution cost **more than the naive
  baseline in 5 of 5 repeats** — the model kept guessing the sandboxed file path wrong,
  and every retry re-sends the growing turn history. Code-mode savings are *behavioral*
  (the model must cooperate); Tool Search's are *structural* (the server enforces them).
  That distinction is now a rule in our profile.
- **A compression proxy's self-reported percentage disagreed with our tokenizer** on the
  same output (it claimed a >100% cost where we measured a +12% saving). We root-caused it
  in the vendor's own source — character counts with an asymmetric formula — **filed the
  issue upstream, and the maintainers merged a fix within 3 hours and shipped it the same
  evening**; our re-run of the released version confirms the banner now agrees with
  symmetric measurement. That's the loop this project exists to close: independent
  measurement → root cause → upstream fix → re-verification, in about a day.

We also fed the data upstream: the MCP spec's tool-schema-overhead thread (issue #2808, now
[discussion #2812](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2812))
proposed tiered definitions. Simulated over our corpus: a discovery tier saves a **mean 87%**
(the thread's 60–70% estimate is conservative), and the namespacing proposal only pays above
a schema-size threshold — repetition alone saves ~nothing
([full tables](https://github.com/lCrazyblindl/lap/blob/main/docs/SPEC-2808.md); the summary
is posted in the discussion). Meanwhile the 2026 spec draft added *transport* caching
(`ttlMs`/`cacheScope`) — which saves the re-listing round-trip, not the context window
([cache math](https://github.com/lCrazyblindl/lap/blob/main/docs/CACHE-ECONOMICS.md)).

One more adoption datapoint that surprised us: probing our 36 leaderboard providers' apex
domains found **`/llms.txt` at 47% adoption** (Stripe, GitHub, Slack, Notion…) while real MCP
discovery endpoints sit at ~0%
([DISCOVERY](https://github.com/lCrazyblindl/lap/blob/main/docs/DISCOVERY.md)). Discovery is
getting solved; efficiency isn't — the same providers' machine-readable menus are still the
leaderboard's naive kilotokens.

## Try it on your own stack

```bash
pip install "lap-score[mcp]"

lap stack                      # your installed MCP servers: "N tokens before you type a word"
lap score  your-openapi.json   # A/B/C decomposition + a 0-100 grade
lap lint   --mcp "python -m mcp_server_git"   # lint a live MCP server's tool definitions
lap badge  your-openapi.json   # a shields.io README badge with your grade
```

The grade is calibrated on the leaderboard corpus: LaunchDarkly rates **B**, Spotify **C**,
GitHub and DynamoDB **D**, Google Drive **F** — and no sampled API earned an **A**, which
requires real pagination, field projection, and declared errors on top of a lean menu.
There's a CI gate (`lap score --diff old.json new.json --max-growth 500`) so a PR that
bloats your agent menu fails the build.

Honest caveats: offline numbers use a tiktoken approximation (set `ANTHROPIC_API_KEY`
for faithful counts — ordering is unchanged, absolutes run ~60% higher); B/C estimates
are structural lower bounds; the live accuracy runs are one cheap model at small k so
far. Everything — scripts, corpus, methodology — is in the repo to rerun.

**Repo:** https://github.com/lCrazyblindl/lap · **Leaderboard:** https://lcrazyblindl.github.io/lap/ ·
MIT, no product, no telemetry. If you maintain an API or MCP server and want it scored
(or scored *fairly* — file an issue), I'd genuinely like the feedback.

---

## 2. Show HN draft

**Title:** `Show HN: Lap – measuring the token cost agents pay to see your API`

**URL:** `https://lcrazyblindl.github.io/lap/`

**First comment (post immediately after submitting):**

> Author here. lap is an MIT toolkit that measures what agent-facing interfaces cost in
> tokens — decomposed into the menu (paid every session), the call, and the result — the
> same way for any OpenAPI spec or live MCP server.
>
> Why: every optimization vendor publishes its own percentage, measured its own way.
> I wanted one neutral ruler. Pointing it at 50 real public APIs: their naive tool menus
> total 11.2M tokens; ~82% is recoverable by re-rendering the same operations compactly;
> the heaviest single menu (Xero, 4M tokens) can't fit any context window at all.
>
> The interesting part was verifying vendor claims live. Anthropic's Tool Search held up
> (~90% real, billed, server-enforced). Their code-execution headline didn't on my
> workload — it cost *more* than naive in 5/5 repeats (wrong sandboxed-path guesses,
> each retry re-sends the turn history). And one compression proxy's self-reported
> percentage disagreed with a direct token count of its own output — I root-caused it in
> their source, filed it, and they merged a fix within hours (shipped the same evening;
> re-verified). Details and a claims registry (verified / plausible / disputed) are in
> the repo.
>
> There's also an MCP-server twin of the leaderboard now: 20 popular published servers,
> installed and scored credential-free — Notion's official server charges 21,411 tokens
> per session (one reference server: 921 tokens for a single tool). Where another grader
> scored the same servers, our letters sometimes agree and sometimes flip — which is the
> argument for publishing raw token numbers plus the script, not just grades.
>
> `pip install lap-score` — `lap stack` tells you how many tokens your own MCP config
> burns before you type a word. Feedback and "score my API" requests welcome.

---

## 3. r/mcp draft — **POSTED 2026-07-10**: https://www.reddit.com/r/mcp/comments/1usyb34/i_scored_20_popular_mcp_servers_token_cost/ (flair: showcase; posted via the owner's browser session, owner-confirmed before submit)

**Title:** `I scored 20 popular MCP servers' token cost — Notion's charges 21k tokens before you type a word`

> Made an open-source CLI (`pip install lap-score`) that measures the context-window tax
> of agent-facing interfaces — live MCP servers over stdio/HTTP, OpenAPI specs, or your
> whole installed stack. Pointed it at 20 popular published servers, installed fresh,
> zero credentials
> ([full table + script](https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-LEADERBOARD.md)):
>
> - **Notion (official): 21,411 tokens** of tool definitions per session. Firecrawl: 18,511.
>   Connecting all 20 servers: ~64k tokens before the first user message.
> - **sequential-thinking is ONE tool that costs 921 tokens** (the description is an essay).
> - The same tools as compact signatures: 3,100 tokens total (−95%) — the compression is
>   sitting on the table server-side.
> - `lap stack` reads your own Claude Desktop/Code config and totals what *your* setup
>   burns at session start; `lap lint --mcp "<command>"` flags what burns tokens/accuracy:
>   missing tool descriptions, undescribed params, 600+-token definitions, no `required`
>   list. (mcp-server-git grades B — `repo_path` is undescribed in 11 of 12 tools;
>   mcp-server-time grades A.)
> - Plus a leaderboard of 50 real public APIs rendered as naive OpenAPI→MCP menus,
>   refreshed monthly: https://lcrazyblindl.github.io/lap/ — 11.2M tokens, ~82% recoverable.
>
> Also measured the tiered-schema proposal from the spec's token-overhead thread
> (discussion #2812) over the corpus — discovery tier saves a mean 87% — and posted the
> numbers there, so if you want that in the protocol, there's data now.
>
> It's MIT, no product attached. If you run an MCP server, `lap lint` takes ~10 seconds
> and usually finds something real — when we filed one of these findings upstream
> (mcp-compressor's banner stats), the maintainers merged a fix within hours.

---

## 4. Posting notes (owner)

- Best order: publish the blog post first (dev.to or a GitHub Discussion on the repo),
  then Show HN linking the **leaderboard page** (HN prefers content over repos), then
  r/mcp. Space them a day apart.
- The strongest r/mcp hook is now the **MCP-server table** (Notion 21k, one 921-token tool);
  expect "which server versions?" — honest answer: whatever `npx -y`/`uvx` served on the
  scan date (in `mcp-leaderboard-data.json`), rerunnable in minutes; the doc's caveats say so.
- Ready-to-submit listing PRs (awesome lists, openapi.tools) live in
  [LISTINGS.md](LISTINGS.md) — best submitted *after* the posts, when the repo shows traction.
- HN: submit morning US time, Tue–Thu. Don't repost the same URL within days; the
  first-comment context matters more than the submission text.
- Expect the two "disputed" claims to draw the most questions — the receipts are
  [CODE-EXEC.md](https://github.com/lCrazyblindl/lap/blob/main/docs/CODE-EXEC.md) and
  [MCP-COMPRESSOR.md](https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-COMPRESSOR.md);
  the honest framing ("workload-specific, k=5, one model, mechanism verified") is already
  in them.
- If someone asks "why should I trust your tokenizer": point at
  [TOKENIZERS.md](https://github.com/lCrazyblindl/lap/blob/main/docs/TOKENIZERS.md) — the
  whole corpus re-counted under 4 BPE vocabularies: absolutes swing ≤8%, the mean saving
  moves 3 pp, the ranking holds at Kendall tau ≥ 0.992; and with `ANTHROPIC_API_KEY` set,
  counts come from Anthropic's own `count_tokens` endpoint — same ordering, ~60% higher
  absolutes ([results-faithful.md](../experiments/token-bench/results-faithful.md)).
