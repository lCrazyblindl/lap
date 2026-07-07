"""Build `docs/LEADERBOARD.md` — a neutral, reproducible ranking of how many
tokens real public APIs' agent menus (bucket A) cost, and how much a LAP-style
compact menu would save.

For each API (resolved from the APIs.guru directory) we render the naive
OpenAPI->tools menu the way a generic MCP/OpenAPI bridge would, and the LAP
`compact_sig` and `tool_search` forms, and count their tokens. Offline by default
(tiktoken approximation — absolute numbers approximate, ranking is the signal);
set ANTHROPIC_API_KEY for faithful counts.

    python experiments/leaderboard.py            # writes docs/LEADERBOARD.md
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
from datetime import date

from lap import openapi_ir as ir, score, tokens, estimate, lint

LIST_URL = "https://api.apis.guru/v2/list.json"
CACHE = pathlib.Path(tempfile.gettempdir()) / "lap-corpus"
MAXBYTES = 16_000_000
PAGE_SIZE = 20  # assumed items/page for the bucket-C (result-size) estimate

# Well-known public APIs (resolved by substring against the APIs.guru directory).
# v0.5 S3: expanded from the original 20-ish (v0.3/v0.4) to 40+ — every entry below was
# verified present in APIs.guru's live directory before being added (unresolvable guesses
# from the first expansion pass were dropped rather than left as silent "skip"s).
CURATED = [
    "stripe.com", "github.com", "slack.com", "digitalocean.com", "box.com", "asana.com",
    "gitlab.com", "atlassian.com:jira", "kubernetes", "adyen.com:CheckoutService",
    "googleapis.com:calendar", "googleapis.com:gmail", "amazonaws.com:ec2",
    "amazonaws.com:dynamodb", "azure.com:compute", "spotify.com", "notion.com",
    "sendgrid.com", "openai.com", "zoom.us", "trello.com",
    # v0.5 S3 additions
    "amazonaws.com:s3", "amazonaws.com:lambda", "amazonaws.com:rds", "amazonaws.com:sns",
    "amazonaws.com:sqs", "googleapis.com:drive", "googleapis.com:sheets",
    "googleapis.com:youtube", "googleapis.com:firebase", "googleapis.com:bigquery",
    "azure.com:storage", "azure.com:keyvault", "vimeo.com", "plaid.com", "nasa.gov",
    "circleci.com", "docker.com", "linode.com", "clickup.com", "netlify.com", "vercel.com",
    "bitbucket.org", "1password.com", "getpostman.com", "xero.com:xero_accounting",
    "webflow.com", "launchdarkly.com", "gitea.io", "ably.io:platform",
]


def _fetch(url: str) -> str:
    import httpx

    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.md5(url.encode()).hexdigest()[:16] + ".spec")
    if f.exists():
        return f.read_text(encoding="utf-8")
    r = httpx.get(url, timeout=60, follow_redirects=True)
    r.raise_for_status()
    f.write_text(r.text, encoding="utf-8")
    return r.text


def _pct(part: int, whole: int) -> int:
    if not whole:
        return 0
    r = round(100 * (whole - part) / whole)
    return 99 if r >= 100 and part > 0 else r  # never imply "free" when tokens remain


def _signed(pct: int) -> str:
    return f"+{pct}%" if pct >= 0 else f"{pct}%"


def main() -> None:
    import httpx

    directory = httpx.get(LIST_URL, timeout=60).json()

    def url_of(key: str) -> str | None:
        vers = directory.get(key, {}).get("versions", {})
        ver = directory.get(key, {}).get("preferred") or (next(iter(vers)) if vers else None)
        return (vers.get(ver) or {}).get("swaggerUrl") if ver else None

    rows = []
    for want in CURATED:
        key = next((k for k in directory if want in k), None)
        url = url_of(key) if key else None
        if not url:
            print(f"skip (not found): {want}")
            continue
        try:
            text = _fetch(url)
            if len(text) > MAXBYTES:
                print(f"skip (too big): {key}")
                continue
            spec = ir._parse(text)
            ops = ir.operations(spec)
            if not ops:
                print(f"skip (no ops): {key}")
                continue
            a = score.score(spec)
            result_cs = [est_c for op in ops
                         for kind, _per, est_c in [estimate.estimate(spec, op, page_size=PAGE_SIZE)]
                         if kind != "void"]
            c_max = max(result_cs) if result_cs else 0
            unpaged = sum(1 for f in lint.lint(spec) if f.rule == "R3")
            title = spec.get("info", {}).get("title", key)[:36]
            rows.append({
                "api": title, "provider": key.split(":")[0], "ops": len(ops),
                "full": a["openapi_full"], "compact": a["compact_sig"],
                "tool_search": a["tool_search"],
                "save_compact": _pct(a["compact_sig"], a["openapi_full"]),
                "save_search": _pct(a["tool_search"], a["openapi_full"]),
                "c_max": c_max, "unpaged": unpaged,
            })
            print(f"OK {key:34} ops={len(ops):4} full={a['openapi_full']:6} "
                  f"compact={a['compact_sig']:6} Cmax={c_max}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {key}: {type(e).__name__}: {str(e)[:80]}")

    rows.sort(key=lambda r: r["full"], reverse=True)

    backend = tokens.backend_name()
    approx = backend != "anthropic"
    lines = [
        "# LAP efficiency leaderboard — agent-menu token cost of real public APIs",
        "",
        f"_Generated {date.today().isoformat()} by [`experiments/leaderboard.py`]"
        "(../experiments/leaderboard.py) over specs from [APIs.guru](https://apis.guru)._",
        "",
        f"**How to read it.** Each row is a real public API. **menu (full)** is the bucket-A token "
        "cost of the naive OpenAPI→tools menu a generic MCP/OpenAPI bridge emits — what an agent "
        "pays, once per session, just to *see* the API. **compact** and **tool_search** are the "
        "LAP-style menus (compact signatures; lazy search+execute) generated from the same spec, "
        "with the % saved vs full. Sorted by the naive menu cost (heaviest first): the APIs at the "
        "top cost agents the most tokens up front and have the most to gain from a leaner menu. "
        "**heaviest result (C)** is the largest single response (bucket C) the estimator finds for "
        "the API - the *recurring* per-call cost that field projection and pagination (LAP R1/R3) "
        f"target. It's a structural lower bound at ~{PAGE_SIZE} items/page, envelope-aware: a list "
        "wrapped in an envelope (`{data:[...]}`, k8s `items`) is scaled to a full page too, with its "
        "sibling fields (counts, cursors, kind/apiVersion, ...) counted once alongside it. Where a "
        "schema carries a real `example`/`examples` value, that's used instead of a synthetic "
        "placeholder - real data an API author wrote down beats a guess.",
        "",
        f"- tokenizer: **{backend}**" + ("  _(approximate — relative ranking is the signal; set "
        "`ANTHROPIC_API_KEY` for faithful counts)_" if approx else "  _(faithful)_"),
        f"- APIs scored: **{len(rows)}**",
        "",
        "| # | API | provider | ops | menu A (full) | compact | save | tool_search | save | heaviest result (C) |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['api']} | {r['provider']} | {r['ops']} | {r['full']} | {r['compact']} | "
            f"{_signed(r['save_compact'])} | {r['tool_search']} | {_signed(r['save_search'])} | {r['c_max'] or '-'} |"
        )

    if rows:
        avg_compact = round(sum(r["save_compact"] for r in rows) / len(rows))
        avg_search = round(sum(r["save_search"] for r in rows) / len(rows))
        total_full = sum(r["full"] for r in rows)
        n_unpaged = sum(1 for r in rows if r["unpaged"])
        lines += [
            "",
            f"**Across all {len(rows)} APIs:** the naive menus total **{total_full:,} tokens** (bucket "
            f"A); `compact_sig` saves **+{avg_compact}%** on average and `tool_search` **+{avg_search}%** "
            "(it wins most where operation counts are high). And that's before results come back: "
            f"**{n_unpaged} of {len(rows)}** have list endpoints with **no pagination**, so an agent can "
            "pull the *whole* collection into context (bucket C), not just a page. These APIs expose "
            "OpenAPI, which a generic bridge turns into the naive menu — so for an agent front-end the "
            "saving is mostly still on the table.",
            "",
            "_Methodology: **A** (menu) is measured; **heaviest result (C)** is estimated from response "
            f"schemas (structural lower bound; top-level AND envelope-wrapped lists scaled to "
            f"~{PAGE_SIZE} items/page; real schema `example`/`examples` values preferred over the "
            "6-char synthetic placeholder where present - `--string-len` on `lap score` raises the "
            "placeholder for un-exampled fields). **B** (the call) needs per-API tasks - see "
            "[`experiments/token-bench`](../experiments/token-bench/README.md). Regenerate with "
            "`python experiments/leaderboard.py`._",
        ]

    docs = pathlib.Path(__file__).resolve().parents[1] / "docs"
    out = docs / "LEADERBOARD.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[written] {out}  ({len(rows)} APIs)")
    _write_site(rows, backend, docs)


_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LAP efficiency leaderboard - agent-menu token cost of real public APIs</title>
<style>
 body{font:15px/1.5 system-ui,sans-serif;margin:2rem auto;max-width:70rem;padding:0 1rem;color:#1c2430}
 h1{font-size:1.5rem} .sub{color:#5a6572}
 table{border-collapse:collapse;width:100%;margin-top:1rem}
 th,td{padding:.35rem .6rem;text-align:right;border-bottom:1px solid #e3e7ec;white-space:nowrap}
 th{cursor:pointer;user-select:none;position:sticky;top:0;background:#fff}
 th:hover{background:#f2f5f8} td:nth-child(2),th:nth-child(2),td:nth-child(3),th:nth-child(3){text-align:left}
 .neg{color:#b03030} .pos{color:#207540}
 footer{margin:2rem 0;color:#5a6572;font-size:.9rem}
 a{color:#2059c0}
</style></head><body>
<h1>LAP efficiency leaderboard</h1>
<p class="sub">The <b>bucket-A menu tax</b> of real public APIs: what an agent pays in tokens,
once per session, just to <i>see</i> each API as naive OpenAPI&rarr;tools definitions - and what
LAP-style <b>compact</b> / lazy <b>tool_search</b> menus of the same operations would cost.
Generated <b id="gen"></b> &middot; tokenizer <b id="tok"></b> (relative ranking is the signal)
&middot; <a href="https://github.com/lCrazyblindl/lap">github.com/lCrazyblindl/lap</a> &middot;
<a href="leaderboard-data.json">raw data</a> &middot;
<a href="https://github.com/lCrazyblindl/lap/tree/main/docs/leaderboard-history">history</a>
&middot; click a column header to sort.</p>
<p id="totals"></p>
<table id="t"><thead><tr>
<th>#</th><th>API</th><th>provider</th><th>ops</th><th>menu A (full)</th><th>compact</th>
<th>saved</th><th>tool_search</th><th>saved</th><th>heaviest result (C)</th>
</tr></thead><tbody></tbody></table>
<footer>lap - measure &amp; improve the token-efficiency of agent-facing APIs (OpenAPI &amp; MCP):
scorer, linter, the LAP profile, and a reproducible token benchmark.
<code>pip install lap-score</code> &middot; MIT.</footer>
<script>
const DATA = __DATA__;
document.getElementById("gen").textContent = DATA.generated;
document.getElementById("tok").textContent = DATA.tokenizer;
const rows = DATA.apis, tb = document.querySelector("#t tbody");
const fmt = n => n.toLocaleString("en-US");
const sgn = p => `<span class="${p<0?"neg":"pos"}">${p>=0?"+":""}${p}%</span>`;
const total = rows.reduce((s,r)=>s+r.full,0);
const avgC = Math.round(rows.reduce((s,r)=>s+r.save_compact,0)/rows.length);
const avgS = Math.round(rows.reduce((s,r)=>s+r.save_search,0)/rows.length);
document.getElementById("totals").innerHTML =
 `<b>${rows.length} APIs</b> &middot; naive menus total <b>${fmt(total)} tokens</b> &middot; ` +
 `compact saves <b>+${avgC}%</b> avg &middot; tool_search <b>+${avgS}%</b> avg`;
function render(list){
 tb.innerHTML = list.map((r,i)=>`<tr><td>${i+1}</td><td>${r.api}</td><td>${r.provider}</td>`+
  `<td>${fmt(r.ops)}</td><td>${fmt(r.full)}</td><td>${fmt(r.compact)}</td><td>${sgn(r.save_compact)}</td>`+
  `<td>${fmt(r.tool_search)}</td><td>${sgn(r.save_search)}</td><td>${r.c_max?fmt(r.c_max):"-"}</td></tr>`).join("");
}
const keys = [null,"api","provider","ops","full","compact","save_compact","tool_search","save_search","c_max"];
let dir = -1;
document.querySelectorAll("th").forEach((th,i)=>{ if(!keys[i]) return;
 th.onclick = ()=>{ dir=-dir; const k=keys[i];
  rows.sort((a,b)=> typeof a[k]==="string" ? dir*a[k].localeCompare(b[k]) : dir*(a[k]-b[k]));
  render(rows); };});
render(rows);
</script></body></html>
"""


def _write_site(rows: list[dict], backend: str, docs: pathlib.Path) -> None:
    """The same data as LEADERBOARD.md, as a static sortable page (GitHub Pages serves
    /docs) + dated JSON snapshots so month-over-month trends stay diffable."""
    generated = date.today().isoformat()
    data = {"generated": generated, "tokenizer": backend, "apis": rows}
    (docs / "leaderboard-data.json").write_text(
        json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    hist = docs / "leaderboard-history"
    hist.mkdir(exist_ok=True)
    (hist / f"{generated[:7]}.json").write_text(
        json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (docs / "index.html").write_text(
        _HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(f"[written] {docs / 'index.html'} + leaderboard-data.json + history/{generated[:7]}.json")


if __name__ == "__main__":
    main()
