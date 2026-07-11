"""`lap lint <openapi>` - check an API against the LAP profile rules.

Static, advisory checks over an OpenAPI spec for the LAP conventions that are
detectable without runtime: opaque names (D3), read shaping on collections
(projection R1 / filter R2 / pagination R3), aggregation (A1), minimal writes
(W1), and uniform errors (E1). Heuristic by nature - it flags likely token/clarity
costs for a human to confirm, each tied to a profile rule.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from . import openapi_ir as ir

PAGINATION = {"limit", "offset", "page", "page_size", "pagesize", "per_page", "perpage",
              "cursor", "top", "skip", "$top", "$skip"}
PROJECTION = {"fields", "field", "select", "$select", "include", "expand", "$expand"}
FILTER_HINTS = {"filter", "$filter", "q", "query", "where", "search"}


@dataclass
class Finding:
    rule: str
    severity: str  # "warn" | "info"
    where: str
    message: str


def _query_names(op: ir.Op) -> set[str]:
    return {p["name"].lower() for p in op.params if p.get("in") == "query"}


def _error_codes(op: ir.Op) -> list[str]:
    responses = op.raw.get("responses")
    return [c for c in (responses if isinstance(responses, dict) else {})
            if isinstance(c, str) and c[:1] in ("4", "5")]


def lint(spec: dict) -> list[Finding]:
    ops = ir.operations(spec)
    out: list[Finding] = []

    for op in ops:
        where = f"{op.method} {op.path}"

        # D3 - opaque operation name
        if re.fullmatch(r"\d+", op.name) or not re.search(r"[A-Za-z]", op.name) or len(op.name) < 3:
            out.append(Finding("D3", "warn", where,
                               f"opaque operation name '{op.name}' - LLMs ground on readable names"))

        # Read shaping on collection (array-returning) GETs
        if op.method == "GET" and op.returns.endswith("[]"):
            q = _query_names(op)
            if not (q & PAGINATION):
                out.append(Finding("R3", "warn", where,
                                   "collection GET has no pagination (limit/offset/cursor) - agents pull the whole list (big bucket C)"))
            if not (q & PROJECTION):
                out.append(Finding("R1", "info", where,
                                   "no field projection (fields/select) - responses carry every field"))
            if not (q & (FILTER_HINTS | (q - PAGINATION - PROJECTION))):
                out.append(Finding("R2", "info", where,
                                   "no server-side filter params - agents fetch then filter in-context"))

        # W1 - writes returning a full representation by default
        if op.method in ("POST", "PUT", "PATCH") and op.returns not in ("void", ""):
            out.append(Finding("W1", "info", where,
                               f"write returns a full representation ({op.returns}) by default - consider Prefer: return=minimal (server-generated fields only)"))

        # E1 - no error responses declared
        if not _error_codes(op):
            out.append(Finding("E1", "warn", where,
                               "no 4xx/5xx error response declared - agents can't distinguish success/empty/error"))

    # A1 - no aggregate/count endpoint anywhere
    if not any(re.search(r"count|aggregate|stats|summary", op.name + op.path, re.I) for op in ops):
        out.append(Finding("A1", "info", "(global)",
                           "no aggregate/count endpoint - 'how many...' questions force pulling the full list"))

    return out


HEAVY_TOOL_TOKENS = 600  # per-tool definition cost that dominates a session (spec issue #2808
#                          measured real production tools at 103-1024 tokens; ~1000 = heavy)

# M5 (server-level) - the whole advertised menu, the pathology M1-M4 can't see: 166
# disciplined ~174-token tools still cost ~29k every session. Thresholds with receipts:
# deferred loading pays above ~10 tools (Anthropic's guidance, confirmed live both ways -
# ~90% saved on a 290-op API, NEGATIVE below ~10 tools); >10k tokens = the band where every
# server we filed measured issues at sat (18.5k-488k).
DEFER_TOOL_COUNT = 10       # below this, deferral measured net-negative
DEFER_MENU_TOKENS = 2_000   # info: worth considering
HEAVY_MENU_TOKENS = 10_000  # warn: every session pays five figures before the first message


def discovery_findings(spec_url: str, probe=None) -> list[Finding]:
    """Rule D0 (profile L0, opt-in via `lap lint <url> --discovery`): an agent that has to
    *search* for your machine-readable interface burns more tokens than one that finds a
    pointer at a well-known path. Probes `<origin>/llms.txt`. `probe` is an injection point
    for tests: callable(url) -> HTTP status int (or raises)."""
    from urllib.parse import urlsplit

    parts = urlsplit(spec_url)
    if parts.scheme not in ("http", "https"):
        return []
    origin = f"{parts.scheme}://{parts.netloc}"
    if probe is None:
        import httpx

        def probe(url: str) -> int:  # noqa: F811 - default prober
            return httpx.get(url, timeout=10, follow_redirects=True).status_code

    try:
        ok = probe(f"{origin}/llms.txt") == 200
    except Exception:  # noqa: BLE001 - unreachable origin = not discoverable
        ok = False
    if ok:
        return []
    return [Finding("D0", "info", origin,
                    "no /llms.txt at the API origin - agents must search for your interface "
                    "instead of finding a pointer at the well-known path (profile rule D0)")]


def _deref(node, root, hops: int = 0):
    """Follow local `$ref`s (`#/$defs/...`, `#/definitions/...`). Bounded hops so a
    cyclic schema terminates; unresolvable or external refs are returned as-is."""
    while (isinstance(node, dict) and isinstance(node.get("$ref"), str)
           and node["$ref"].startswith("#/") and hops < 16):
        target = root
        for seg in node["$ref"][2:].split("/"):
            seg = seg.replace("~1", "/").replace("~0", "~")
            if isinstance(target, dict) and seg in target:
                target = target[seg]
            else:
                return node
        node, hops = target, hops + 1
    return node


def flat_schema(schema, _root=None, _depth: int = 0) -> tuple[dict, list]:
    """Flatten a tool inputSchema to `(properties, required)` as a reader would see it.

    The 2026 draft MCP spec (SEP-2106) loosens `inputSchema` to any JSON Schema 2020-12 -
    composition keywords and `$ref` into `$defs`/`definitions` become first-class, and
    OpenAPI->MCP generators already emit them today. Reading only top-level `properties`
    silently sees such a tool as parameterless, so this walks local composition instead:
    `allOf`/`oneOf`/`anyOf` branch properties are unioned (first declaration wins) and
    their `required` lists merged - a declared-requiredness view for linting/rendering,
    not a validator. Depth- and hop-bounded, mirroring SEP-2106's own resource bounds."""
    if not isinstance(schema, dict) or _depth > 8:
        return {}, []
    root = _root if _root is not None else schema
    schema = _deref(schema, root)
    if not isinstance(schema, dict):
        return {}, []
    raw_props = schema.get("properties")
    props = {k: (_deref(v, root) if isinstance(v, dict) else v)
             for k, v in (raw_props.items() if isinstance(raw_props, dict) else ())}
    raw_req = schema.get("required")
    required = [r for r in (raw_req if isinstance(raw_req, list) else []) if isinstance(r, str)]
    for key in ("allOf", "oneOf", "anyOf"):
        branches = schema.get(key)
        for branch in (branches if isinstance(branches, list) else []):
            b_props, b_req = flat_schema(branch, root, _depth + 1)
            for k, v in b_props.items():
                props.setdefault(k, v)
            required += [r for r in b_req if r not in required]
    return props, required


def heaviest_tools(tools: list[dict], top: int = 5) -> list[dict]:
    """The `top` most expensive tool definitions with a description/schema token split -
    the M3 rule only flags >600-token outliers, but on a disciplined server the remaining
    fat still concentrates somewhere; this shows where."""
    import json as _json

    from . import tokens

    rows = []
    for t in tools:
        rows.append({
            "tool": t.get("name", "(unnamed)"),
            "tokens": tokens.count_tools([t]),
            "description_tokens": tokens.count(t.get("description") or ""),
            "schema_tokens": tokens.count(_json.dumps(t.get("input_schema") or {})),
        })
    rows.sort(key=lambda r: -r["tokens"])
    return rows[:top]


def lint_tools(tools: list[dict]) -> list[Finding]:
    """Lint a live MCP server's advertised tools (name / description / inputSchema).

    The MCP-side counterpart of `lint(spec)`: D3 carries over unchanged; the M-rules
    cover what an MCP tool can get wrong that an OpenAPI op expresses differently.
    Expects the `fetch_tools()` shape: {name, description, input_schema}.
    """
    from . import tokens

    out: list[Finding] = []
    for t in tools:
        name, where = t.get("name", ""), t.get("name", "(unnamed)")
        desc = (t.get("description") or "").strip()
        schema = t.get("input_schema") or {}
        props, required = flat_schema(schema)

        # D3 - opaque tool name (same rule as OpenAPI operations)
        if re.fullmatch(r"\d+", name) or not re.search(r"[A-Za-z]", name) or len(name) < 3:
            out.append(Finding("D3", "warn", where,
                               f"opaque tool name '{name}' - LLMs ground on readable names"))

        # M1 - missing / too-short description
        if len(desc) < 20:
            out.append(Finding("M1", "warn", where,
                               "tool description missing or under 20 chars - the model must guess "
                               "when to call it (wrong-tool calls cost far more than a sentence)"))

        # M2 - undescribed input parameters
        undescribed = sorted(k for k, v in props.items()
                             if not (isinstance(v, dict) and str(v.get("description", "")).strip()))
        if undescribed:
            shown = ", ".join(undescribed[:4]) + ("..." if len(undescribed) > 4 else "")
            out.append(Finding("M2", "info", where,
                               f"{len(undescribed)}/{len(props)} input parameter(s) have no "
                               f"description ({shown}) - argument semantics get guessed"))

        # M3 - heavy tool definition (every session pays it, used or not)
        cost = tokens.count_tools([t])
        if cost > HEAVY_TOOL_TOKENS:
            out.append(Finding("M3", "warn", where,
                               f"tool definition costs ~{cost} tokens (> {HEAVY_TOOL_TOKENS}) - "
                               "every session pays this whether the tool is used or not; trim the "
                               "description/schema or defer via tool search"))

        # M4 - arguments declared but none marked required (composition branches count)
        if props and not required:
            out.append(Finding("M4", "info", where,
                               "inputSchema declares parameters but no 'required' list - the model "
                               "can't tell mandatory from optional arguments"))

    # M5 - the whole menu is heavy (server-level; the many-small-tools pathology the
    # per-tool rules can't see)
    total = tokens.count_tools(tools)
    if total > HEAVY_MENU_TOKENS or (len(tools) > DEFER_TOOL_COUNT and total > DEFER_MENU_TOKENS):
        from . import mcp_client

        compact = tokens.count(mcp_client._compact(tools))
        sev = "warn" if total > HEAVY_MENU_TOKENS else "info"
        out.append(Finding("M5", sev, "(entire menu)",
                           f"the menu costs ~{total} tokens for {len(tools)} tool(s), paid every "
                           "session - above ~10 tools deferred loading pays (rule D2, measured "
                           "live at ~90% saved); compact signatures of the same tools would be "
                           f"~{compact} tokens"))
    return out


def filter_ignored(findings: list[Finding], ignore) -> list[Finding]:
    ignore = {r.upper() for r in ignore}
    return [f for f in findings if f.rule.upper() not in ignore]


def _load_ignore_file() -> set[str]:
    if not os.path.exists(".lapignore"):
        return set()
    with open(".lapignore", encoding="utf-8") as fh:
        toks = re.split(r"[,\s]+", fh.read())
    return {t.strip().upper() for t in toks if t.strip() and not t.startswith("#")}


def _print_human(title: str, source: str, findings: list[Finding], warns: int, infos: int) -> None:
    print(f"\nLAP lint - {title}\nsource: {source}\n")
    if not findings:
        print("  No LAP rule violations detected. OK\n")  # ASCII: ✓ breaks cp1251 consoles
        return
    order = {"warn": 0, "info": 1}
    by_rule: dict[str, list[Finding]] = {}
    for f in sorted(findings, key=lambda f: (order[f.severity], f.rule)):
        by_rule.setdefault(f"{f.severity.upper()} {f.rule}", []).append(f)
    for header, items in by_rule.items():
        print(f"  [{header}] {items[0].message.split(' - ')[0]}")
        for f in items[:6]:
            print(f"      {f.where}")
        if len(items) > 6:
            print(f"      ... +{len(items) - 6} more")
        print()
    print(f"  {warns} warning(s), {infos} suggestion(s). See profile/llm-api-profile.md for the rules.\n")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Lint an OpenAPI spec - or a live MCP server's "
                                             "advertised tools - against the LAP profile rules.")
    ap.add_argument("source", nargs="?", help="OpenAPI spec: file path or http(s) URL "
                                              "(omit if --mcp-url/--mcp)")
    ap.add_argument("--mcp-url", help="lint a live MCP server's advertised tools (HTTP URL)")
    ap.add_argument("--mcp", help="lint a live MCP server over stdio: the full command, "
                                  "e.g. --mcp \"python -m mcp_server_git\"")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="MCP connect timeout in seconds (default 30)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--ignore", default="", help="comma-separated rule codes to suppress (also reads ./.lapignore)")
    ap.add_argument("--discovery", action="store_true",
                    help="also probe the spec URL's origin for /llms.txt (rule D0; URL sources only)")
    ap.add_argument("--fail-on", choices=["none", "info", "warn"], default="none",
                    help="CI gate: exit 1 if any finding at/above this severity remains")
    args = ap.parse_args()

    ignore = _load_ignore_file() | {r.strip() for r in args.ignore.split(",") if r.strip()}

    if args.mcp_url or args.mcp:
        import shlex
        import sys

        from . import grade as grade_mod
        from . import mcp_client, tokens

        if not mcp_client.available():
            print("--mcp-url/--mcp needs fastmcp: pip install 'lap-score[mcp]'", file=sys.stderr)
            raise SystemExit(2)
        if args.mcp:
            parts = [p.strip('"') for p in shlex.split(args.mcp, posix=(os.name != "nt"))]
            from fastmcp.client.transports import StdioTransport

            target = StdioTransport(parts[0], parts[1:], keep_alive=False)
            source = args.mcp
        else:
            target = source = args.mcp_url
        tools = mcp_client.fetch_tools(target, timeout=args.timeout)
        findings = filter_ignored(lint_tools(tools), ignore)
        warns = sum(1 for f in findings if f.severity == "warn")
        infos = len(findings) - warns
        menu_tokens = tokens.count_tools(tools)
        g = grade_mod.compute_parts(len(tools), menu_tokens, 0, warns, infos)
        heaviest = heaviest_tools(tools)
        gap = grade_mod.next_grade_menu_budget(len(tools), menu_tokens, 0, warns, infos)
        title = f"MCP server ({len(tools)} advertised tool(s))"
        if args.json:
            print(json.dumps({
                "api": title, "source": source, "grade": g,
                "menu_tokens": menu_tokens,
                "heaviest_tools": heaviest, "next_grade": gap,
                "findings": [{"rule": f.rule, "severity": f.severity, "where": f.where,
                              "message": f.message} for f in findings],
                "warnings": warns, "suggestions": infos,
            }, indent=2))
        else:
            _print_human(title, source, findings, warns, infos)
            subs = "  ".join(f"{k} {v}" for k, v in g["subscores"].items())
            print(f"  LAP grade: {g['letter']} ({g['score']}/100)   [{subs}]")
            print(f"  menu: {menu_tokens:,} tokens for {len(tools)} tool(s); heaviest "
                  "(total = description/schema):")
            for h in heaviest:
                print(f"    {h['tokens']:>6}  {h['tool'][:40]:40} = "
                      f"{h['description_tokens']}/{h['schema_tokens']}")
            if gap:
                if gap["menu_budget"] is not None:
                    shave = menu_tokens - gap["menu_budget"]
                    print(f"  to reach {gap['letter']} (>={gap['threshold']}): menu <= "
                          f"~{gap['menu_budget']:,} tokens - shave ~{shave:,} "
                          "(the heaviest definitions above are where it lives)")
                else:
                    print(f"  to reach {gap['letter']} (>={gap['threshold']}): a lighter menu "
                          "alone can't get there - fix the findings above first")
            print()
    else:
        if not args.source:
            ap.error("provide an OpenAPI source or --mcp-url/--mcp")
        spec = ir.load_spec(args.source)
        found = lint(spec)
        if args.discovery:
            found += discovery_findings(args.source)
        findings = filter_ignored(found, ignore)
        title = spec.get("info", {}).get("title", "(untitled API)")
        warns = sum(1 for f in findings if f.severity == "warn")
        infos = len(findings) - warns

        if args.json:
            print(json.dumps({
                "api": title, "source": args.source,
                "findings": [{"rule": f.rule, "severity": f.severity, "where": f.where, "message": f.message}
                             for f in findings],
                "warnings": warns, "suggestions": infos,
            }, indent=2))
        else:
            _print_human(title, args.source, findings, warns, infos)

    if (args.fail_on == "warn" and warns) or (args.fail_on == "info" and findings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
