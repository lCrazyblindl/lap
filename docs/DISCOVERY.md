# Discoverability scan - who actually publishes llms.txt? (rule D0's evidence)

_Generated 2026-07-08 by [`experiments/discovery_scan.py`](../experiments/discovery_scan.py); apex domains of the [leaderboard](LEADERBOARD.md)'s 36 API providers, HTTPS GET, 8s timeout, SPA-fallback 200s counted as misses._

The LAP profile's **L0 / rule D0** asks one cheap thing of an API provider: a machine-readable pointer at a well-known path (`/llms.txt`), so an agent *finds* the interface instead of searching for it. Adoption today:

| well-known path | providers serving it | share |
| --- | ---: | ---: |
| `/llms.txt` | 17/36 | 47% |
| `/.well-known/mcp.json` | 2/36 | 6% |
| `/mcp` | 0/36 | 0% |

**`/llms.txt` found at:** ably.io, adyen.com, asana.com, atlassian.com, azure.com, circleci.com, clickup.com, getpostman.com, github.com, netlify.com, notion.com, plaid.com, slack.com, stripe.com, vercel.com, webflow.com, xero.com.

Read (and this surprised us - we expected near-zero): **llms.txt has real adoption among top API providers** - roughly half serve it at the apex domain. That's evidence the D0 bar is practical, not utopian: your competitors likely already cleared it. The gap has *moved*, not closed - the same providers' machine-readable menus are still the multi-kilotoken naive renderings the [leaderboard](LEADERBOARD.md) measures. Discovery is getting solved; efficiency isn't. `lap lint <spec-url> --discovery` checks D0 for your own origin.

_Caveats: apex domains only (a provider may serve llms.txt on a docs subdomain - this scan measures the well-known location, which is the point of the rule); one GET per path, single run; `/mcp` reachability says nothing about what's behind it (NLWeb-style endpoints answer MCP there; `lap score --mcp-url` scores any that are live)._
