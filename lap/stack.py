"""`lap stack` — how many tokens does YOUR installed MCP stack cost, before the first word?

Reads the agent's own MCP config (Claude Code project `.mcp.json`, Claude Code user
`~/.claude.json`, Claude Desktop `claude_desktop_config.json`, or any JSON file with an
`mcpServers` map), connects to every server it lists (stdio or HTTP), and totals the
bucket-A menu tokens the agent pays at session start — plus what compact / lazy
(`tool_search`) renderings of the *same* advertised tools would cost instead.

The 2026 headline number ("multi-server setups burn 100k+ tokens before the first
prompt") — personalized and reproducible. Optional: needs fastmcp (`pip install lap-score[mcp]`).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

DEFAULT_TIMEOUT = 30.0


# ---------------------------------------------------------------- config discovery

def default_config_paths() -> list[tuple[str, pathlib.Path]]:
    """Well-known agent-config locations that exist on this machine."""
    home = pathlib.Path.home()
    cands = [
        ("Claude Code (project .mcp.json)", pathlib.Path.cwd() / ".mcp.json"),
        ("Claude Code (~/.claude.json)", home / ".claude.json"),
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        cands.append(("Claude Desktop", pathlib.Path(appdata) / "Claude" / "claude_desktop_config.json"))
    cands += [
        ("Claude Desktop", home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"),
        ("Claude Desktop", home / ".config" / "Claude" / "claude_desktop_config.json"),
    ]
    return [(label, p) for label, p in cands if p.is_file()]


def load_servers(path: str | pathlib.Path) -> list[dict]:
    """Parse an `mcpServers` map into normalized server entries (stdio or http)."""
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    servers = data.get("mcpServers") if isinstance(data, dict) else None
    out = []
    for name, cfg in (servers or {}).items():
        if not isinstance(cfg, dict):
            continue
        url = cfg.get("url")
        if url:
            out.append({"name": name, "kind": "http", "url": url})
        elif cfg.get("command"):
            out.append({
                "name": name, "kind": "stdio",
                "command": os.path.expandvars(str(cfg["command"])),
                "args": [os.path.expandvars(str(a)) for a in cfg.get("args") or []],
                "env": {str(k): os.path.expandvars(str(v)) for k, v in (cfg.get("env") or {}).items()},
            })
    return out


# ---------------------------------------------------------------- scanning

def _target(server: dict):
    if server["kind"] == "http":
        return server["url"]
    from fastmcp.client.transports import StdioTransport

    # keep_alive=False: tear the subprocess down inside the event loop when the client
    # exits, instead of leaving it for GC (Windows Proactor teardown noise otherwise).
    return StdioTransport(server["command"], server["args"], env=server["env"] or None,
                          keep_alive=False)


def _ok_row(s: dict, tools: list[dict]) -> dict:
    from . import mcp_client

    m = mcp_client.score_tools(tools)["menu"]
    return {
        "server": s["name"], "kind": s["kind"], "tools": len(tools),
        "tool_names": [t["name"] for t in tools],
        "menu": m["mcp_live"], "compact_sig": m["compact_sig"],
        "tool_search": m["tool_search"], "error": None,
    }


def _err_row(s: dict, e: Exception) -> dict:
    return {
        "server": s["name"], "kind": s["kind"], "tools": 0, "tool_names": [],
        "menu": 0, "compact_sig": 0, "tool_search": 0,
        "error": f"{type(e).__name__}: {str(e)[:80]}",
    }


async def _scan_async(servers: list[dict], timeout: float) -> list[dict]:
    import asyncio

    from . import mcp_client

    rows = []
    for s in servers:
        try:
            tools = await asyncio.wait_for(mcp_client._fetch(_target(s)), timeout)
            rows.append(_ok_row(s, tools))
        except Exception as e:  # noqa: BLE001 — a dead server is a finding, not a crash
            rows.append(_err_row(s, e))
    return rows


def scan(servers: list[dict], fetch=None, timeout: float = DEFAULT_TIMEOUT) -> list[dict]:
    """One row per server: advertised-menu tokens + compact/tool_search what-ifs.

    Unreachable servers become rows with an `error` note instead of aborting the scan
    (a real stack usually has at least one server that needs creds or a missing binary).
    All servers share one event loop; `fetch` is an injection point for tests.
    """
    if fetch is not None:
        rows = []
        for s in servers:
            try:
                rows.append(_ok_row(s, fetch(s)))
            except Exception as e:  # noqa: BLE001
                rows.append(_err_row(s, e))
        return rows

    import asyncio

    return asyncio.run(_scan_async(servers, timeout))


def stack_tool_search(rows: list[dict]) -> int:
    """One lazy menu for the WHOLE stack: fixed search/call tools counted once + a
    name index across every server (unlike summing per-server tool_search menus)."""
    from . import menu, tokens

    names = [f"{r['server']}.{n}" for r in rows for n in r["tool_names"]]
    return tokens.count_tools([menu._SEARCH_TOOL, menu._CALL_TOOL]) + tokens.count(
        "# Lazy: search_tools(query)+call_tool(name,input). operations: " + ", ".join(names)
    )


def totals(rows: list[dict]) -> dict:
    ok = [r for r in rows if r["error"] is None]
    return {
        "servers": len(rows), "reachable": len(ok),
        "tools": sum(r["tools"] for r in ok),
        "menu": sum(r["menu"] for r in ok),
        "compact_sig": sum(r["compact_sig"] for r in ok),
        "tool_search_stack": stack_tool_search(ok) if any(r["tool_names"] for r in ok) else 0,
    }


# ---------------------------------------------------------------- CLI

def _saved(part: int, whole: int) -> str:
    return f"+{round(100 * (whole - part) / whole)}%" if whole else "-"


def _print_config(label: str, rows: list[dict], t: dict) -> None:
    print(f"\n{label}")
    print(f"  {'server':22} {'kind':6} {'tools':>5} {'menu tokens':>11} {'compact':>8} {'note'}")
    for r in rows:
        if r["error"]:
            print(f"  {r['server'][:22]:22} {r['kind']:6} {'-':>5} {'-':>11} {'-':>8} {r['error']}")
        else:
            print(f"  {r['server'][:22]:22} {r['kind']:6} {r['tools']:>5} {r['menu']:>11} {r['compact_sig']:>8}")
    if t["reachable"]:
        print(f"  {'TOTAL':22} {'':6} {t['tools']:>5} {t['menu']:>11} {t['compact_sig']:>8}")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="lap stack",
        description="Score your installed MCP stack: the menu (bucket A) tokens your agent "
                    "pays at session start, before you type a word.")
    ap.add_argument("config", nargs="?",
                    help="path to a JSON config with an mcpServers map "
                         "(default: auto-discover Claude Code / Claude Desktop configs)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                    help=f"per-server connect timeout in seconds (default {DEFAULT_TIMEOUT:g})")
    ap.add_argument("--only", help="comma-separated server names to include")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    from . import mcp_client, tokens

    if not mcp_client.available():
        print("lap stack needs fastmcp: pip install lap-score[mcp]", file=sys.stderr)
        sys.exit(2)

    if args.config:
        configs = [(args.config, pathlib.Path(args.config))]
    else:
        configs = default_config_paths()
        if not configs:
            print("no MCP config found (looked for ./.mcp.json, ~/.claude.json, "
                  "Claude Desktop claude_desktop_config.json) — pass a path explicitly",
                  file=sys.stderr)
            sys.exit(2)

    only = {s.strip() for s in args.only.split(",")} if args.only else None
    report, grand = [], {"servers": 0, "reachable": 0, "tools": 0, "menu": 0, "compact_sig": 0}
    all_rows: list[dict] = []
    for label, path in configs:
        servers = load_servers(path)
        if only:
            servers = [s for s in servers if s["name"] in only]
        if not servers:
            report.append({"config": str(path), "servers": [], "totals": totals([])})
            continue
        rows = scan(servers, timeout=args.timeout)
        t = totals(rows)
        report.append({"config": str(path), "servers": rows, "totals": t})
        all_rows += [r for r in rows if r["error"] is None]
        for k in grand:
            grand[k] += t[k]

    grand["tool_search_stack"] = stack_tool_search(all_rows) if all_rows else 0

    if args.json:
        print(json.dumps({"tokenizer": tokens.backend_name(),
                          "configs": report, "totals": grand}, indent=2))
        return

    print(f"LAP stack scan - tokenizer: {tokens.backend_name()}")
    for entry in report:
        if not entry["servers"]:
            print(f"\n{entry['config']}\n  (no MCP servers configured)")
            continue
        _print_config(entry["config"], entry["servers"], entry["totals"])

    if grand["menu"]:
        print(f"\nYour agent pays ~{grand['menu']:,} tokens of tool menus at session start - "
              f"before you type a word\n({grand['tools']} tools across {grand['reachable']} "
              f"reachable server(s)).")
        print(f"Compact signatures of the same tools would cost {grand['compact_sig']:,} "
              f"({_saved(grand['compact_sig'], grand['menu'])} saved); one lazy tool_search menu "
              f"over the whole stack, {grand['tool_search_stack']:,} "
              f"({_saved(grand['tool_search_stack'], grand['menu'])} saved).")
    elif grand["servers"]:
        print("\nNo reachable servers - nothing to total. (Servers that need missing "
              "binaries or credentials are listed with their error above.)")


if __name__ == "__main__":
    main()
