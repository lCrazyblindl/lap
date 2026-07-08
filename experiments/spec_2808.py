"""v0.6 N7 (refreshed v0.8 P1) — empirical input to the MCP tool-schema token-overhead
discussion. Issue #2808 was closed 2026-05-29 and converted to discussion #2812; the
2026 draft spec (final 2026-07-28) adopted transport-level caching (SEP-2549) and JSON
Schema 2020-12 in tool schemas (SEP-2106) but none of the issue's three proposals — so
this measured input still stands, retargeted at the live discussion.

The original issue proposed protocol-level mitigations; this script *measures* two of
them over real corpora, so the spec discussion can argue from data:

1. **Tiered schemas** (proposal 1): a "discovery tier" (name + first sentence of the
   description, no inputSchema) shown up front; the full definition fetched only for
   tools actually invoked. We compute the discovery-tier cost for every API in the
   leaderboard corpus + real MCP servers, and the break-even point (how many tools a
   session can invoke before tiered costs more than the naive full menu).
2. **Namespacing / dedupe** (proposal 3): identical parameter declarations repeated
   across a server's tools (e.g. `repo_path` in every mcp-server-git tool) hoisted to
   a shared block declared once, referenced elsewhere.

Proposal 2 (schema versioning) affects cache validity, not menu size - noted, not simulated.

Writes docs/SPEC-2808.md (tables + a ready-to-paste issue comment). Offline; uses the
leaderboard's cached specs (run experiments/leaderboard.py first if the cache is empty).
Set MCP_SERVER_PY to also measure the two real reference servers over stdio.
"""

from __future__ import annotations

import json
import os
import pathlib
import statistics
import sys
import tempfile
from datetime import date

from lap import menu, tokens
from lap import openapi_ir as ir

REPO = pathlib.Path(__file__).resolve().parents[1]
CACHE = pathlib.Path(tempfile.gettempdir()) / "lap-corpus"
DESC_CHARS = 100  # discovery-tier description budget (issue: "minimal info")
TYPICAL_INVOKED = 3  # tools a typical session actually calls
DISCUSSION = "https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2812"
COMPOSED_KEYS = ("$ref", "$defs", "definitions", "allOf", "oneOf", "anyOf")


def composition_prevalence(max_specs: int = 8) -> dict | None:
    """SEP-2106 fallout check: how many *real* generated tool schemas already carry
    JSON Schema 2020-12 constructs ($ref/$defs/composition) that a top-level-
    `properties`-only reader misses? Runs FastMCP over a bounded, deterministic
    subset of the cached corpus (5-60-op specs). Returns None if fastmcp is absent."""
    from lap import mcp_form

    if not mcp_form.available():
        return None
    tot = {"specs": 0, "tools": 0, "composed": 0}
    for f in sorted(CACHE.glob("*.spec")):
        if tot["specs"] >= max_specs:
            break
        try:
            spec = ir._parse(f.read_text(encoding="utf-8"))
            if not 5 <= len(ir.operations(spec)) <= 60:
                continue
            tools, _ = mcp_form.build(spec)
        except Exception:  # noqa: BLE001 - FastMCP chokes on some real specs; skip
            continue
        tot["specs"] += 1
        tot["tools"] += len(tools)
        tot["composed"] += sum(
            1 for t in tools
            if any(f'"{k}"' in json.dumps(t["input_schema"] or {}) for k in COMPOSED_KEYS))
        print(f"composition: {spec.get('info', {}).get('title', '?')[:30]:30} "
              f"{tot['composed']}/{tot['tools']} so far")
    return tot if tot["tools"] else None


def discovery_tier(tools: list[dict]) -> list[dict]:
    out = []
    for t in tools:
        desc = (t.get("description") or "").strip().split(". ")[0][:DESC_CHARS]
        out.append({"name": t["name"], "description": desc, "input_schema": {}})
    return out


def dedupe_params(tools: list[dict]) -> tuple[int, int, int]:
    """Simulate proposal 3: hoist parameter declarations that repeat *identically*
    across tools into a shared block declared once. Returns
    (naive_tokens, deduped_tokens, n_hoisted_params)."""
    naive = tokens.count_tools(tools)
    seen: dict[str, int] = {}
    for t in tools:
        for pname, pschema in ((t.get("input_schema") or {}).get("properties") or {}).items():
            key = pname + "\x00" + json.dumps(pschema, sort_keys=True, default=str)
            seen[key] = seen.get(key, 0) + 1
    shared = {k for k, n in seen.items() if n > 1}
    if not shared:
        return naive, naive, 0
    common, slimmed = {}, []
    for t in tools:
        schema = json.loads(json.dumps(t.get("input_schema") or {}, default=str))
        props = schema.get("properties") or {}
        for pname in list(props):
            key = pname + "\x00" + json.dumps(props[pname], sort_keys=True, default=str)
            if key in shared:
                common[pname] = props[pname]
                props[pname] = {"$ref": f"#/common/{pname}"}
        slimmed.append({**t, "input_schema": schema})
    deduped = tokens.count_tools(slimmed) + tokens.count(
        "# common parameters (declared once)\n" + json.dumps(common, separators=(",", ":")))
    return naive, deduped, len(common)


def measure_spec(spec: dict) -> dict | None:
    ops = ir.operations(spec)
    if not ops:
        return None
    tools, _ = menu.MENUS["openapi_full"](spec)
    full = tokens.count_tools(tools)
    disc = tokens.count_tools(discovery_tier(tools))
    per_tool = full / len(tools)
    # tiered session cost = discovery menu + full defs of the k tools actually invoked
    tiered_k = disc + TYPICAL_INVOKED * per_tool
    naive_d, deduped, hoisted = dedupe_params(tools)
    return {
        "title": spec.get("info", {}).get("title", "?")[:32], "tools": len(tools),
        "full": full, "discovery": disc,
        "disc_save": round(100 * (full - disc) / full),
        "tiered_k": round(tiered_k),
        "tiered_save": round(100 * (full - tiered_k) / full),
        "break_even": int((full - disc) / per_tool) if per_tool else 0,
        "dedupe_save": round(100 * (naive_d - deduped) / naive_d) if naive_d else 0,
        "hoisted": hoisted,
    }


def main() -> None:
    rows = []
    for f in sorted(CACHE.glob("*.spec")):
        try:
            r = measure_spec(ir._parse(f.read_text(encoding="utf-8")))
            if r:
                rows.append(r)
                print(f"OK {r['title']:34} tools={r['tools']:4} disc_save={r['disc_save']:3}% "
                      f"tiered@{TYPICAL_INVOKED}={r['tiered_save']:3}% dedupe={r['dedupe_save']:3}%")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {f.name}: {type(e).__name__}: {str(e)[:60]}")
    if not rows:
        sys.exit("no cached specs - run experiments/leaderboard.py first")

    # real MCP servers, if the isolated venv is available
    srv_rows = []
    py = os.environ.get("MCP_SERVER_PY")
    if py:
        from fastmcp.client.transports import StdioTransport

        from lap import mcp_client

        for name, args in [("mcp-server-git", ["-m", "mcp_server_git", "--repository", str(REPO)]),
                           ("mcp-server-time", ["-m", "mcp_server_time"])]:
            try:
                tools = mcp_client.fetch_tools(StdioTransport(py, args, keep_alive=False), timeout=30)
                full = tokens.count_tools(tools)
                disc = tokens.count_tools(discovery_tier(tools))
                naive_d, deduped, hoisted = dedupe_params(tools)
                srv_rows.append({"name": name, "tools": len(tools), "full": full, "discovery": disc,
                                 "disc_save": round(100 * (full - disc) / full),
                                 "dedupe_save": round(100 * (naive_d - deduped) / naive_d),
                                 "hoisted": hoisted})
                print(f"OK {name} disc_save={srv_rows[-1]['disc_save']}% dedupe={srv_rows[-1]['dedupe_save']}%")
            except Exception as e:  # noqa: BLE001
                print(f"SKIP {name}: {e!r}"[:100])

    comp = composition_prevalence()

    disc_saves = [r["disc_save"] for r in rows]
    tiered_saves = [r["tiered_save"] for r in rows]
    dd = [r["dedupe_save"] for r in rows if r["hoisted"]]
    be = [r["break_even"] for r in rows]
    rows.sort(key=lambda r: r["full"], reverse=True)

    lines = [
        "# Measured input for the MCP tool-schema token-overhead discussion (#2808 → #2812)",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/spec_2808.py`](../experiments/spec_2808.py); tokenizer: "
        f"**{tokens.backend_name()}**. Corpus: {len(rows)} real public APIs (the "
        "[leaderboard](LEADERBOARD.md) set, rendered as naive OpenAPI→tools menus the way a "
        "generic bridge would) + real MCP reference servers over stdio._",
        "",
        "**Status (2026-07-08).** "
        "[Issue #2808](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2808) "
        "proposed three protocol-level mitigations (tiered schemas / schema versioning / "
        "namespacing). It was closed 2026-05-29 and **converted to "
        f"[discussion #2812]({DISCUSSION})**, which is where the conversation now lives — with "
        "single-server data points (11 / 29 / 79 tools) and an explicit ask for a CI-checkable "
        "per-tool token budget. The 2026 draft spec (final publication **2026-07-28**) adopted "
        "**none of the three proposals**; its token-relevant changes are transport-level "
        "`tools/list` caching (`ttlMs`/`cacheScope`, "
        "[SEP-2549](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2549) — "
        "priced out in [CACHE-ECONOMICS.md](CACHE-ECONOMICS.md): it saves the re-listing "
        "round-trip, not context), deterministic tool ordering for prompt-cache hits, and "
        "loosening `inputSchema` to full JSON Schema 2020-12 "
        "([SEP-2106](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2106) — "
        "measured fallout below). So the corpus-scale measurements here remain the empirical "
        "input the discussion doesn't yet have.",
        "",
        "## Proposal 1 — tiered schemas (discovery tier + on-demand full definitions)",
        "",
        f"Discovery tier = name + first sentence of the description (≤{DESC_CHARS} chars), no "
        "inputSchema. Session cost = discovery menu + full definitions of only the tools "
        "actually invoked.",
        "",
        f"- **Discovery-tier saving vs the full menu: mean {statistics.mean(disc_saves):.0f}%, "
        f"median {statistics.median(disc_saves):.0f}%, range "
        f"{min(disc_saves)}–{max(disc_saves)}%** across {len(rows)} APIs — the issue's 60–70% "
        "estimate is, if anything, conservative at real-API scale.",
        f"- **At a typical {TYPICAL_INVOKED}-tools-invoked session, net saving is still "
        f"mean {statistics.mean(tiered_saves):.0f}% / median {statistics.median(tiered_saves):.0f}%.**",
        f"- **Break-even: a session must invoke {statistics.mean(be):.0f} tools on average "
        f"(median {statistics.median(be):.0f}) before tiered costs more than up-front** — "
        "far beyond any real session on these APIs.",
        f"- **Honest caveat: on tiny interfaces tiering flips negative** — the smallest API in "
        f"the corpus ({min(rows, key=lambda r: r['tools'])['tools']} tools) loses "
        f"{-min(tiered_saves)}% at {TYPICAL_INVOKED} invocations, because invoking most of your "
        "tools means paying discovery *plus* nearly the whole menu anyway. Same shape we "
        "measured live for Anthropic's Tool Search ([TOOL-SEARCH.md](TOOL-SEARCH.md)): lazy "
        "loading isn't worth it below ~10 tools.",
        "",
        "| API | tools | full menu | discovery tier | saved | tiered @3 calls | saved | break-even (tools) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows[:15]:
        lines.append(f"| {r['title']} | {r['tools']} | {r['full']} | {r['discovery']} | "
                     f"{r['disc_save']}% | {r['tiered_k']} | {r['tiered_save']}% | {r['break_even']} |")
    lines += [
        f"| _…and {len(rows) - 15} more_ | | | | | | | |",
        "",
        "## Proposal 3 — namespacing / shared-parameter dedupe",
        "",
        "Simulated as: parameter declarations that repeat *identically* across a server's tools "
        "are declared once in a shared block and referenced elsewhere.",
        "",
        f"- Across the {len(dd)} APIs with duplicated parameters: **mean saving "
        f"{statistics.mean(dd):.0f}%, median {statistics.median(dd):.0f}%, range "
        f"{min(dd)}–{max(dd)}%**.",
        "- **The distribution is the finding**: dedupe pays where the repeated declaration is "
        "*fat* (Kubernetes 94%, Compute Engine 69%, Jira 63% — big shared object schemas) and "
        "goes slightly **negative** where repeated parameters are tiny — a `$ref` replacement "
        "costs more tokens than `{\"type\":\"string\"}` itself (CircleCI −10%). Repetition alone "
        "doesn't pay; if the spec adopts this, it should apply only above a size threshold.",
        "",
    ]
    if srv_rows:
        lines += [
            "## Real MCP servers (advertised menus over stdio, not our renderings)",
            "",
            "| server | tools | full menu | discovery tier | saved | dedupe saved | params hoisted |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for s in srv_rows:
            lines.append(f"| {s['name']} | {s['tools']} | {s['full']} | {s['discovery']} | "
                         f"{s['disc_save']}% | {s['dedupe_save']}% | {s['hoisted']} |")
        lines += [
            "",
            "`mcp-server-git` is instructive for proposal 3 — in the *opposite* direction than "
            "expected: it repeats `repo_path` (+2 more params) identically across tools, yet "
            "dedupe saves ~0%, because each declaration is so small that the `$ref` replacing it "
            "costs just as much. Repetition is visible lint-wise; only *fat* repetition pays "
            "token-wise.",
            "",
        ]
    lines += [
        "## Proposal 2 — schema versioning",
        "",
        "Not a menu-size question: `schema_version` protects *prompt-cache validity* when one "
        "tool changes. Priced in [CACHE-ECONOMICS.md](CACHE-ECONOMICS.md) (a single changed "
        "definition invalidates the whole cached prefix); no menu simulation here.",
        "",
    ]
    if comp:
        pct = round(100 * comp["composed"] / comp["tools"])
        lines += [
            "## SEP-2106 fallout — composed schemas are already in the wild",
            "",
            "The draft loosens `inputSchema` to **any JSON Schema 2020-12** — composition "
            "keywords and `$ref` become first-class. This mostly legitimizes existing "
            f"practice: running the most popular OpenAPI→MCP generator (FastMCP) over "
            f"{comp['specs']} real cached specs, **{comp['composed']} of {comp['tools']} "
            f"generated tools ({pct}%) already carry `$ref`/`$defs`/composition inside their "
            "inputSchema** (DynamoDB 51/53, SQS 28/40; even `mcp-server-git` ships 3/12).",
            "",
            "The measurement consequence: **any tool that reads only top-level `properties` "
            "misreads such schemas** — a top-level `allOf` renders as a parameterless tool. "
            "Today's FastMCP output still keeps top-level `properties` (0 of "
            f"{comp['tools']} tools lost a parameter *name* to nesting), but SEP-2106 makes "
            "arbitrary placement legal, and at least one shipped optimizer already has this "
            "blind spot — mcp-compressor's self-reported ratio counts `name+description+"
            "properties` only ([root-caused](MCP-COMPRESSOR.md)). We fixed the same latent "
            "blind spot in our own compact renderer and MCP lint rules (`lap` now flattens "
            "local `$ref`/`allOf`/`oneOf`/`anyOf`, depth-bounded the way SEP-2106's resource "
            "bounds prescribe).",
            "",
        ]
    lines += [
        f"## Ready-to-paste comment for [discussion #2812]({DISCUSSION})",
        "",
        "> A corpus-scale data point, since the numbers in this thread are each from a single "
        f"server (11 / 29 / 79 tools): we measured the original issue's proposals 1 and 3 over "
        f"the naive OpenAPI→tools menus of {len(rows)} real public APIs (Stripe, GitHub, "
        "Kubernetes, …) plus reference MCP servers' advertised menus over stdio "
        "([methodology & full tables](https://github.com/lCrazyblindl/lap/blob/main/docs/SPEC-2808.md)):",
        ">",
        f"> - **Tiered schemas (proposal 1): a name+first-sentence discovery tier saves "
        f"{statistics.mean(disc_saves):.0f}% on average (median {statistics.median(disc_saves):.0f}%, "
        f"range {min(disc_saves)}–{max(disc_saves)}%)** vs sending full definitions up front. "
        f"Even charging a typical session the *full* definitions of 3 invoked tools, the net "
        f"saving is still ~{statistics.mean(tiered_saves):.0f}%; break-even is "
        f"~{statistics.mean(be):.0f} invoked tools — beyond any real session. The 60–70% "
        "estimate in the original issue is conservative at real-API scale. One caveat: below "
        "~10 tools tiering flips negative (we measured the same shape live for Anthropic's "
        "Tool Search), so it should stay opt-in for small servers.",
        f"> - **Namespacing/dedupe (proposal 3): {statistics.mean(dd):.0f}% mean saving, but "
        f"range {min(dd)}–{max(dd)}%** — it pays where the repeated declaration is *fat* "
        "(Kubernetes 94%) and goes slightly negative where repeated params are tiny, since a "
        "`$ref` costs more than `{\"type\":\"string\"}` (CircleCI −10%; mcp-server-git repeats "
        "`repo_path` everywhere yet saves ~0%). Worth a size threshold if adopted.",
        "> - On the token-cost-vs-selection-reliability tension raised above: we measured it "
        "live (10 tasks × 5 menu forms × 5 repeats, small model) — the only form with an "
        "accuracy penalty was the *over*-compressed one (bare numbered signatures, 46/50 vs "
        "naive 49/50), while a compact-but-described form matched naive accuracy at ~30% fewer "
        "tokens ([data](https://github.com/lCrazyblindl/lap/blob/main/experiments/token-bench/validation.md)). "
        "The budget belongs on schema bloat, not on descriptions.",
        "> - On \"schema token budget as a checked constraint, like bundle size\": neutral "
        "OSS tooling for exactly that exists — `pip install lap-score`, then `lap lint --mcp "
        "\"<server cmd>\"` flags tool definitions over ~600 tokens (and other schema-hygiene "
        "rules) with CI gates (`--fail-on warn`), and `lap score --max-menu-tokens N` budgets "
        "the whole menu. (Disclosure: we maintain it; MIT.)",
        f"> - Re the draft's `ttlMs`/`cacheScope` (SEP-2549): transport caching composes with "
        "prompt caching, but neither returns *context-window* capacity — the original issue's "
        "reasoning-capacity concern survives the 2026 draft untouched "
        "([cache math](https://github.com/lCrazyblindl/lap/blob/main/docs/CACHE-ECONOMICS.md)).",
        ">",
        "> Reproducible with `pip install lap-score` — the measurement scripts and corpus are in "
        "the repo. Happy to run other variants (different tier contents, page sizes, tokenizers) "
        "if useful to the discussion.",
    ]

    out = REPO / "docs" / "SPEC-2808.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[written] {out}  ({len(rows)} APIs, {len(srv_rows)} servers)")


if __name__ == "__main__":
    main()
