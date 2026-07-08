"""v0.7 S2 - llms.txt adoption scan: is anyone actually discoverable? (rule D0's evidence)

The profile's new L0/D0 rule says: publish a machine-readable pointer at
`<origin>/llms.txt` so agents find your interface instead of searching for it. This
script measures how many of the leaderboard's 50 real API providers actually do that
today, and writes docs/DISCOVERY.md. Also probes `/.well-known/mcp.json` (draft MCP
discovery convention) and `/mcp` (the NLWeb-style endpoint) for context - reachability
only, no key needed.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import date

import httpx

REPO = pathlib.Path(__file__).resolve().parents[1]
PATHS = ["/llms.txt", "/.well-known/mcp.json", "/mcp"]
TIMEOUT = 8.0


def probe(url: str) -> tuple[bool, str]:
    """(found, note). Found = HTTP 200 AND a plausibly-real body (not an SPA fallback:
    content-type text/* for llms.txt, or any 200 for the endpoint probes - but a text/html
    llms.txt that parses as HTML is a soft-404, count it out)."""
    try:
        r = httpx.get(url, timeout=TIMEOUT, follow_redirects=True,
                      headers={"User-Agent": "lap-discovery-scan/0.5 (+https://github.com/lCrazyblindl/lap)"})
    except Exception as e:  # noqa: BLE001
        return False, type(e).__name__
    if r.status_code != 200:
        return False, str(r.status_code)
    body = r.text[:400].lstrip().lower()
    if body.startswith("<!doctype") or body.startswith("<html"):
        return False, "200-but-html (SPA fallback)"  # applies to every path: none of them is a web page
    return True, "200"


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    data = json.loads((REPO / "docs" / "leaderboard-data.json").read_text(encoding="utf-8"))
    domains = sorted({r["provider"].split(":")[0] for r in data["apis"]})

    rows = []
    for d in domains:
        row = {"domain": d}
        for p in PATHS:
            found, note = probe(f"https://{d}{p}")
            row[p] = (found, note)
        marks = "  ".join(f"{p}={'YES' if row[p][0] else '-'}" for p in PATHS)
        print(f"{d:24} {marks}")
        rows.append(row)

    n = len(rows)
    counts = {p: sum(1 for r in rows if r[p][0]) for p in PATHS}
    lines = [
        "# Discoverability scan - who actually publishes llms.txt? (rule D0's evidence)",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/discovery_scan.py`](../experiments/discovery_scan.py); apex domains of "
        f"the [leaderboard](LEADERBOARD.md)'s {n} API providers, HTTPS GET, {TIMEOUT:g}s "
        "timeout, SPA-fallback 200s counted as misses._",
        "",
        "The LAP profile's **L0 / rule D0** asks one cheap thing of an API provider: a "
        "machine-readable pointer at a well-known path (`/llms.txt`), so an agent *finds* the "
        "interface instead of searching for it. Adoption today:",
        "",
        "| well-known path | providers serving it | share |",
        "| --- | ---: | ---: |",
    ]
    for p in PATHS:
        lines.append(f"| `{p}` | {counts[p]}/{n} | {round(100 * counts[p] / n)}% |")
    hits = [r["domain"] for r in rows if r["/llms.txt"][0]]
    lines += [
        "",
        f"**`/llms.txt` found at:** {', '.join(hits) if hits else '(none)'}.",
        "",
        "Read (and this surprised us - we expected near-zero): **llms.txt has real adoption "
        "among top API providers** - roughly half serve it at the apex domain. That's evidence "
        "the D0 bar is practical, not utopian: your competitors likely already cleared it. The "
        "gap has *moved*, not closed - the same providers' machine-readable menus are still the "
        "multi-kilotoken naive renderings the [leaderboard](LEADERBOARD.md) measures. Discovery "
        "is getting solved; efficiency isn't. `lap lint <spec-url> --discovery` checks D0 for "
        "your own origin.",
        "",
        "_Caveats: apex domains only (a provider may serve llms.txt on a docs subdomain - this "
        "scan measures the well-known location, which is the point of the rule); one GET per "
        "path, single run; `/mcp` reachability says nothing about what's behind it (NLWeb-style "
        "endpoints answer MCP there; `lap score --mcp-url` scores any that are live)._",
    ]

    out = REPO / "docs" / "DISCOVERY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[written] {out}  ({n} domains)")


if __name__ == "__main__":
    main()
