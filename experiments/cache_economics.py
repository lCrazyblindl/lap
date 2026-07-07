"""v0.7 M2 - cache economics: does prompt caching make the menu (bucket A) free?

The most common objection to menu-size work is "the definitions are cached, so who
cares". This script answers it with the standard prompt-caching price model and the
real menu sizes from the leaderboard corpus, and writes docs/CACHE-ECONOMICS.md.

Model (Anthropic prompt caching; other vendors are within the same order):
- cache WRITE costs 1.25x the base input price (first call that establishes the prefix);
- cache READ costs 0.10x base (every later call whose prefix is byte-identical);
- the prefix is re-sent every assistant turn, so a T-turn session pays
    uncached:  A * T
    cached:    A * (1.25 + 0.10 * (T - 1))
  in billing-weighted tokens, best case (no invalidation, no >TTL idle gap).

Offline; reads docs/leaderboard-data.json (run experiments/leaderboard.py first).
"""

from __future__ import annotations

import json
import pathlib
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
WRITE, READ = 1.25, 0.10
TURNS = [1, 3, 8, 25, 100]
PICKS = ["Xero Accounting", "GitHub v3", "Notion"]  # huge / big / small
SONNET_IN = 3.00  # $ / 1M input tokens, for the dollar column


def cached(a: int, t: int) -> float:
    return a * (WRITE + READ * (t - 1))


def main() -> None:
    data = json.loads((REPO / "docs" / "leaderboard-data.json").read_text(encoding="utf-8"))
    rows = {p: next(r for r in data["apis"] if p.lower() in r["api"].lower()) for p in PICKS}

    lines = [
        "# Cache economics - does prompt caching make the menu free?",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/cache_economics.py`](../experiments/cache_economics.py) from the "
        "[leaderboard](LEADERBOARD.md) data; tokenizer as there "
        f"(**{data['tokenizer']}**)._",
        "",
        "**The objection.** \"Tool definitions are prompt-cached, so bucket A costs nothing "
        "- why optimize the menu?\" This doc prices that claim with the standard caching "
        "model: a cache **write** bills at **1.25x** base input, a cache **read** at "
        "**0.10x**, and the prefix is re-sent **every assistant turn**, so a T-turn session "
        "pays `A x T` uncached vs `A x (1.25 + 0.10(T-1))` cached - best case (prefix "
        "byte-identical throughout, no idle gap past the cache TTL).",
        "",
        "## What caching actually buys",
        "",
        "- **At best a 10x discount, asymptotically.** As T grows the cached cost tends to "
        "`0.10 x A` per turn - never zero. A compact rendering is a ~5x cut that "
        "**composes** with caching: compact+cached ~= 50x cheaper than naive uncached.",
        "- **Break-even vs a compact menu:** with compaction ratio `r = compact/naive`, an "
        "*uncached* compact menu beats a *cached* naive one while `T < 1.15 / (r - 0.10)` "
        "turns (and at **any** T once `r <= 0.10`). At the leaderboard-average r ~= 0.20 "
        "that's ~11 turns; on GitHub (r = 0.32) ~5 turns; on Xero (r = 0.002) - always. "
        "So even a caching refusenik wins with the leaner menu on typical sessions; and if "
        "you do cache, cache the leaner menu (the strategies compose, they don't compete).",
        "- **Caching pays in dollars, not context.** The cached definitions still occupy "
        "the context window and still tax the model's working memory - the reasoning-"
        "capacity concern in MCP spec issue #2808 is untouched by caching. Kubernetes' "
        "2.8M-token naive menu doesn't fit a 200K window at any discount. Tool Search / "
        "deferred loading is different in kind: the definitions are genuinely absent "
        "(saves dollars AND context).",
        "- **The best case is fragile.** Any change to any tool definition invalidates the "
        "prefix (that's what #2808's `schema_version` proposal protects); an idle gap "
        "longer than the cache TTL (minutes) triggers a full re-write; and the write "
        "premium means a cache used only once costs **125%** of not caching at all.",
        "",
        "## Worked examples (real menus, billing-weighted input tokens)",
        "",
        "Billing-weighted tokens = raw tokens x price multiplier; dollar column at Sonnet-"
        f"class input pricing (${SONNET_IN:.2f}/M).",
        "",
    ]

    for pick, r in rows.items():
        a_full, a_compact = r["full"], r["compact"]
        lines += [
            f"### {r['api']} - naive {a_full:,} tok, compact {a_compact:,} tok "
            f"({r['ops']} ops)",
            "",
            "| turns | naive uncached | naive cached | compact uncached | compact cached | "
            "cheapest |",
            "| ---: | ---: | ---: | ---: | ---: | --- |",
        ]
        for t in TURNS:
            opts = {
                "naive uncached": a_full * t,
                "naive cached": cached(a_full, t),
                "compact uncached": a_compact * t,
                "compact cached": cached(a_compact, t),
            }
            best = min(opts, key=opts.get)  # type: ignore[arg-type]
            cells = " | ".join(f"{v:,.0f}" for v in opts.values())
            lines.append(f"| {t} | {cells} | {best} |")
        d_naive = a_full * 8 / 1e6 * SONNET_IN
        d_cc = cached(a_compact, 8) / 1e6 * SONNET_IN
        lines += [
            "",
            f"At a typical 8-turn session: naive uncached ~${d_naive:.2f}, compact cached "
            f"~${d_cc:.3f} per session - **{d_naive / d_cc:,.0f}x** apart on this API.",
            "",
        ]

    lines += [
        "## Takeaway",
        "",
        "Caching is a *price multiplier* (>=0.10x, fragile); menu form is a *token "
        "multiplier* (~0.2x, robust, also frees context). They multiply. The order of "
        "operations for an API author is therefore: make the menu lean (D1), defer it where "
        "the platform can (D2), and *then* let callers cache what remains - not the other "
        "way around.",
    ]

    out = REPO / "docs" / "CACHE-ECONOMICS.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {out}")


if __name__ == "__main__":
    main()
