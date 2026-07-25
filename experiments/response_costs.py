"""v0.9 W13 — bucket C, MEASURED: what real MCP tool responses cost in context.

LAP measures bucket A exhaustively and bucket C only as a *schema-based estimate* (OpenAPI)
or not at all (MCP servers: the grade's result sub-score is skipped because tool listings
don't declare response shapes). Meanwhile the response side is where the remaining money is:
every mitigation we've measured — compact menus, deferral, facades — touches the menu, not
the reply. Nobody has published what real MCP tool responses cost. This does.

Method: call read-only tools on credential-free published servers and tokenize what comes
back, exactly as a client feeds it into the model (`tool_result` content). No LLM, no keys —
deterministic and rerunnable. For JSON payloads it also reports a **projected** figure (each
item cut to its first `KEEP` fields, the same model `lap score`'s projected bucket-C uses),
i.e. what field selection would save. Non-JSON payloads are flagged as prose: they can't be
projected, which is itself the finding.

SAFETY: only the calls in `response_fixtures.json` are made — a committed, read-only
allowlist. This script never enumerates a server's tools and calls them; writes, deletes and
posts are out of scope by construction. Local targets (git log on this repo, a seeded temp
sqlite db, a temp text file) are preferred; network reads use fixed queries.

    python experiments/response_costs.py            # all fixtures
    python experiments/response_costs.py --only wikipedia-mcp,mcp-server-git

Writes docs/RESPONSE-COSTS.md + docs/response-costs-data.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sqlite3
import sys
import tempfile
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments"))

import mcp_leaderboard as lb  # noqa: E402  (spawn config + uvx/npx machinery)
from lap import tokens  # noqa: E402
from lap.estimate import _project  # noqa: E402  (same projection model as lap score)

KEEP = 3          # fields kept per item in the projected figure (identity-first, as in M1)
TIMEOUT = 180.0
FIXTURES = REPO / "experiments" / "response_fixtures.json"


def prepare_sandbox() -> dict[str, str]:
    """A temp dir with the small read targets the fixtures point at, so measurements
    don't depend on machine state. Returns the placeholder substitutions."""
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lap-respcost-"))
    (tmp / "notes.md").write_text(
        "# Release notes\n\n- Added the response-cost measurement.\n"
        "- Fixed the asymmetric ratio.\n\n## Details\n\nThree buckets: menu, call, result.\n",
        encoding="utf-8")
    db = tmp / "shop.sqlite"
    con = sqlite3.connect(db)
    con.executescript(
        "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, price REAL, tag TEXT, "
        "stock INTEGER, note TEXT);"
        + "".join(f"INSERT INTO items VALUES ({i}, 'item-{i}', {i * 1.5}, 'tag-{i % 3}', "
                  f"{i * 2}, 'a short note for item {i}');" for i in range(1, 11)))
    con.commit()
    con.close()
    return {"{TMP}": str(tmp).replace("\\", "/"), "{REPO}": str(REPO).replace("\\", "/"),
            "{DB}": str(db).replace("\\", "/"), "{FILE}": str(tmp / "notes.md").replace("\\", "/")}


def substitute(value, subs: dict[str, str]):
    if isinstance(value, str):
        for k, v in subs.items():
            value = value.replace(k, v)
        return value
    if isinstance(value, dict):
        return {k: substitute(v, subs) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, subs) for v in value]
    return value


def project_payload(data, keep: int = KEEP):
    """Apply the first-`keep`-fields projection to a parsed JSON payload: a list of
    objects item-wise, an enveloped list inside its envelope, a bare object directly."""
    if isinstance(data, list):
        return [_project(x, keep) for x in data]
    if isinstance(data, dict):
        arrays = [k for k, v in data.items() if isinstance(v, list) and v
                  and isinstance(v[0], dict)]
        if arrays:
            out = dict(data)
            for k in arrays:
                out[k] = [_project(x, keep) for x in data[k]]
            return out
        return _project(data, keep)
    return data


def classify(text: str):
    """(payload class, parsed value). Three classes, because the difference matters:

    - `json`   - the caller can parse it and pick fields out of it;
    - `repr`   - structured data in a NON-interoperable serialization (Python `repr()`:
                 single quotes, `None`/`True`). It carries fields, but a caller can't
                 `JSON.parse` it - a real interop finding, not prose;
    - `text`   - prose/free text: nothing to project, filter or paginate. Also a finding.
    """
    s = text.strip()
    if not s:
        return "empty", None
    try:
        return "json", json.loads(s)
    except ValueError:
        pass
    try:
        import ast

        value = ast.literal_eval(s)
        if isinstance(value, (dict, list)):
            return "repr", value
    except (ValueError, SyntaxError, MemoryError, RecursionError):
        pass
    return "text", None


def projection_drops_substance(parsed, projected) -> bool:
    """True when the first-`KEEP`-fields projection removes the payload's LARGEST field —
    almost certainly the thing the caller invoked the tool for.

    A real limitation of the "first N fields" heuristic, caught on arxiv `get_abstract`:
    its reply is `{status, paper_id, title, authors, ..., abstract}`, so keeping three
    fields drops the abstract and reports a 94% "saving" for an answer that no longer
    answers. Rows flagged here are excluded from the aggregate saving and listed as a
    caveat instead."""
    if not isinstance(parsed, dict) or not isinstance(projected, dict) or not parsed:
        return False

    def size(value) -> int:
        return len(json.dumps(value, ensure_ascii=False, default=str))

    biggest = max(parsed, key=lambda k: size(parsed[k]))
    return biggest not in projected


def measure(text: str, structured) -> dict:
    """The cost a client actually pays for one tool_result, plus the projected what-if.

    The projection is always derived from the SAME payload the primary figure counts (the
    text content), never from `structured_content` - mixing the two would compare a text
    baseline against a JSON projection and manufacture a saving."""
    kind, parsed = classify(text)
    row = {"tokens": tokens.count(text), "chars": len(text), "payload": kind,
           "structured_tokens": tokens.count(json.dumps(structured, ensure_ascii=False))
           if structured is not None else None}
    if parsed is None:
        row["projected_tokens"] = None
        row["as_json_tokens"] = None
        return row
    projected = project_payload(parsed)
    row["projected_tokens"] = tokens.count(
        json.dumps(projected, ensure_ascii=False, separators=(",", ":")))
    row["projection_drops_substance"] = projection_drops_substance(parsed, projected)
    # for `repr` payloads: the same data serialized as JSON, unprojected - so the interop
    # cost and the projection saving stay separable
    row["as_json_tokens"] = tokens.count(
        json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))) if kind == "repr" else None
    return row


async def call_fixtures(entry: dict, calls: list[dict], subs: dict[str, str]) -> list[dict]:
    from fastmcp import Client

    from fastmcp.client.transports import StdioTransport  # noqa: F401 (via lb helpers)

    transport = lb_transport(entry)
    out = []
    async with Client(transport) as client:
        for call in calls:
            args = substitute(call.get("args") or {}, subs)
            rec = {"tool": call["tool"], "args": args, "note": call.get("note", "")}
            try:
                res = await asyncio.wait_for(client.call_tool(call["tool"], args), TIMEOUT)
                text = "\n".join(getattr(c, "text", "") for c in res.content)
                rec.update(measure(text, getattr(res, "structured_content", None)))
                rec["sample"] = text[:180]  # auditability: every row traceable to real output
            except Exception as exc:  # noqa: BLE001 - a failed call is a row, not a crash
                rec["error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
            out.append(rec)
        await asyncio.sleep(0.25)  # let stdio transports close inside the loop (Windows)
    return out


def lb_transport(entry: dict):
    """Build the same stdio transport `mcp_leaderboard.fetch` uses, without listing tools."""
    from fastmcp.client.transports import StdioTransport

    if entry["kind"] == "pip":
        cmd, args = lb._uvx(), []
        if entry.get("cmd"):
            args += ["--from", entry["pkg"], entry["cmd"]]
        else:
            args += [entry["pkg"]]
    else:
        npx = lb._npx()
        cmd, args = npx[0], npx[1:] + ["-y", entry["pkg"]]
    args += entry.get("args", [])
    env = {**os.environ, **entry.get("env", {})}
    node_dir = REPO / ".tools" / "node"
    if entry["kind"] == "npm" and node_dir.exists():
        env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
    return StdioTransport(cmd, args, env=env, keep_alive=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated server names to measure")
    ap.add_argument("--rerender", action="store_true",
                    help="rebuild docs/RESPONSE-COSTS.md from the saved data file, "
                    "no calls made (text edits without re-measuring)")
    args = ap.parse_args()
    sys.stdout.reconfigure(errors="replace")

    if args.rerender:
        saved = json.loads((REPO / "docs" / "response-costs-data.json")
                           .read_text(encoding="utf-8"))
        write_doc(saved["servers"])
        return

    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    by_name = {e["name"]: e for e in lb.SERVERS}
    subs = prepare_sandbox()
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    results = {}
    for server, spec in fixtures.items():
        if only and server not in only:
            continue
        entry = dict(by_name.get(server) or {})
        if not entry:
            print(f"SKIP {server}: not in mcp_leaderboard.SERVERS")
            continue
        # fixture-level overrides (e.g. point a server at the temp sandbox)
        if spec.get("args"):
            entry["args"] = substitute(spec["args"], subs)
        try:
            rows = asyncio.run(call_fixtures(entry, spec["calls"], subs))
        except Exception as exc:  # noqa: BLE001
            print(f"DEAD {server}: {type(exc).__name__}: {str(exc)[:90]}")
            continue
        # publish placeholders, not this machine's absolute paths (home dir, temp dir)
        unsub = {v: k for k, v in subs.items()}
        for r in rows:
            r["args"] = substitute(r["args"], unsub)
        results[server] = rows
        for r in rows:
            if "error" in r:
                print(f"  ERR  {server:26} {r['tool'][:26]:26} {r['error'][:50]}")
            else:
                proj = (f" -> {r['projected_tokens']:>6} projected" if r["projected_tokens"]
                        else f"  ({r['payload']}, not projectable)")
                print(f"  OK   {server:26} {r['tool'][:26]:26} {r['tokens']:>6} tok"
                      f"{proj}  [{r['payload']}]")

    write_doc(results)


def write_doc(results: dict) -> None:
    ok_rows = [(s, r) for s, rows in results.items() for r in rows if "error" not in r]
    total = sum(r["tokens"] for _, r in ok_rows)
    prose = [(s, r) for s, r in ok_rows if r["payload"] == "text"]
    reprs = [(s, r) for s, r in ok_rows if r["payload"] == "repr"]
    dropped = [(s, r) for s, r in ok_rows if r.get("projection_drops_substance")]
    # aggregate over projectable rows whose projection still keeps the payload's substance
    projectable = [(s, r) for s, r in ok_rows
                   if r["projected_tokens"] and not r.get("projection_drops_substance")]
    saved = (sum(r["tokens"] - r["projected_tokens"] for _, r in projectable)
             / max(1, sum(r["tokens"] for _, r in projectable)))
    heaviest = max(ok_rows, key=lambda x: x[1]["tokens"]) if ok_rows else None

    lines = [
        "# Bucket C, measured — a price list of real MCP tool responses",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/response_costs.py`](../experiments/response_costs.py); tokenizer "
        f"**{tokens.backend_name()}**. Real calls to read-only tools on credential-free "
        "published servers; the token figure is the `tool_result` content as a client feeds "
        "it back into the model. Calls come from a committed allowlist "
        "([`response_fixtures.json`](../experiments/response_fixtures.json)) — this script "
        "never enumerates and calls a server's tools. No LLM involved._",
        "",
        "**What this is.** Reference data, not a ranking. Our bucket-C figures were "
        "schema-based estimates for OpenAPI and absent for MCP servers ([the grade skips the "
        "result sub-score](MCP-LEADERBOARD.md)); as far as we know nobody had published "
        "measured response costs at all. Response size belongs to the *request* — a long "
        "article is long because we asked for an article — so a big number in this table is "
        "not by itself a finding. What the dataset supports: budgeting (what does a call of "
        "this shape put into context?), validating estimators, and the two structural "
        "observations below, which don't depend on any response being \"too big\".",
        "",
        f"**{len(ok_rows)} calls across {len({s for s, _ in ok_rows})} servers, "
        f"{total:,} tokens of replies** — ranging from {min(r['tokens'] for _, r in ok_rows)} "
        f"token(s) (`{min(ok_rows, key=lambda x: x[1]['tokens'])[1]['tool']}`) to "
        f"{heaviest[1]['tokens']:,} (`{heaviest[0]}`/`{heaviest[1]['tool']}`, a full article). "
        f"Payload form: {len(ok_rows) - len(prose) - len(reprs)} JSON, {len(prose)} free "
        f"text, {len(reprs)} Python-`repr()`. `projected` = the same payload with each item "
        f"cut to its first {KEEP} fields; treat it as a *ceiling* on what caller-side field "
        "selection could reclaim, not a saving (see the caveat on where the heuristic "
        "breaks).",
        "",
        "| server | tool | args | response tok | projected | payload |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    kinds = {"json": "JSON", "repr": "**repr** (not JSON)", "text": "**text**",
             "empty": "empty"}
    for s, r in sorted(ok_rows, key=lambda x: -x[1]["tokens"]):
        a = json.dumps(r["args"], ensure_ascii=False)
        a = (a[:40] + "…") if len(a) > 41 else a
        proj = f"{r['projected_tokens']:,}" if r["projected_tokens"] else "—"
        if r.get("projection_drops_substance"):
            proj += " ⚠"
        lines.append(f"| {s} | `{r['tool']}` | `{a}` | {r['tokens']:,} | {proj} | "
                     f"{kinds.get(r['payload'], r['payload'])} |")

    errs = [(s, r) for s, rows in results.items() for r in rows if "error" in r]
    if errs:
        lines += ["", "## Calls that didn't return", "",
                  "| server | tool | error |", "| --- | --- | --- |"]
        lines += [f"| {s} | `{r['tool']}` | `{r['error']}` |" for s, r in errs]

    lines += [
        "",
        "## What the dataset supports",
        "",
        "- **A price list.** Every row quotes its exact arguments because the cost belongs to "
        "the request; use the table to budget what a call of a given shape puts into context, "
        "the way the [leaderboard](MCP-LEADERBOARD.md) budgets menus. No row is an accusation.",
        "- **The affordance gap (structural — visible in the schemas, independent of any "
        "measured size).** Some tools give the caller a brake: `fetch` has "
        "`max_length`/`start_index`, `git_log` has `max_count`, `read_text_file` has "
        "`head`/`tail`, the search tools have `max_results`. Others don't: `get_article` "
        "accepts only `title`, `get_abstract` only `paper_id` — whatever comes back, comes "
        "back whole. And MCP itself has no standard caller-side field or page selection "
        "(OpenAPI has R1/R3 for exactly this), so where the author didn't add a limit "
        "parameter, no one downstream can add one. A protocol-shaped gap, not an author "
        "mistake.",
        f"- **Response form (structural).** {len(prose)} of {len(ok_rows)} replies are free "
        "text: whatever their size, the caller can't parse, filter or paginate them — the "
        "model pays for narrative formatting it may not need. Tools that return computed "
        "data leave the narrative to the model (a point MCP server authors have raised "
        "independently).",
        f"- **Projection ceiling, stated carefully.** Under the first-{KEEP}-fields heuristic, "
        f"{saved:.0%} of the projectable tokens would be cut ({len(projectable)} rows where "
        "the projection keeps the payload's largest field). This is an upper bound on what "
        "caller-side field selection *could* reclaim if MCP had such a mechanism — not a "
        "measured saving, and the heuristic itself fails on some shapes (next bullet).",
    ]
    if dropped:
        lines += [
            "- **⚠ Where our own projection model breaks down** — on "
            + ", ".join(f"`{s}`/`{r['tool']}`" for s, r in dropped)
            + " the first-"
            f"{KEEP}-fields projection removes the payload's largest field: `get_abstract` "
            "replies `{status, paper_id, title, authors, …, abstract}`, so \"projected\" would "
            "drop the abstract itself and claim a ~94% saving for an answer that no longer "
            "answers. Those rows are marked ⚠, excluded from the aggregate above, and stand as "
            "a limitation of the heuristic that `lap score`'s projected bucket-C shares: "
            "*field order is a proxy for importance, and sometimes it's a bad one.*",
        ]
    if reprs:
        lines += [
            f"- **{len(reprs)} replies serialize structured data as Python `repr()`** "
            "(single quotes, `None`/`True`) instead of JSON — e.g. "
            + ", ".join(f"`{s}`/`{r['tool']}`" for s, r in reprs[:3])
            + ". The data is all there, but a caller can't parse it, so it lands in the model's "
            "context as opaque text. Cost-wise it is close to the JSON of the same data "
            + ((lambda h: f"({h['tokens']:,} vs {h['as_json_tokens']:,} tokens on the heaviest "
                          f"such row, `{h['tool']}`)")(
                max((r for _, r in reprs if r.get("as_json_tokens")),
                    key=lambda r: r["tokens"], default={}))
               if any(r.get("as_json_tokens") for _, r in reprs) else "")
            + " — this is an interoperability finding, not a token one.",
        ]
    lines += [
        "",
        "_Caveats: one call per fixture (network-backed servers may vary run to run — local "
        "targets like git/sqlite/filesystem are deterministic); tool_result text is what most "
        "clients forward, but a client that forwards `structured_content` instead pays the "
        "figure in the JSON data file; and no LLM was involved, so this dataset says nothing "
        "about model behavior — e.g. whether models over-pick heavy tools when a cheaper one "
        "would do (`get_article` vs `get_summary`) is a plausible hypothesis this data cannot "
        "test; it would need a live experiment._",
    ]

    (REPO / "docs" / "RESPONSE-COSTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPO / "docs" / "response-costs-data.json").write_text(
        json.dumps({"generated": date.today().isoformat(), "tokenizer": tokens.backend_name(),
                    "keep": KEEP, "servers": results}, indent=1), encoding="utf-8")
    print(f"\n[written] docs/RESPONSE-COSTS.md  ({len(ok_rows)} calls, {len(errs)} errors)")


if __name__ == "__main__":
    main()
