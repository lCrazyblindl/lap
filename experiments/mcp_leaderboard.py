"""v0.8 P2 — the MCP-server leaderboard: what do popular *published* MCP servers
actually charge your context window, before you type a word?

The OpenAPI leaderboard's twin. Each server is installed and run locally in an
isolated environment (`uvx` for PyPI servers, `npx -y` for npm ones — no global
installs), its advertised tool list is fetched over stdio with NO credentials
(dummy env vars where a server refuses to boot without them), and the menu is
scored with the same machinery as `lap lint --mcp`: bucket-A tokens, compact
what-if, M-rule findings, composite grade (menu + hygiene; the result sub-score
is skipped — MCP listings don't declare response shapes).

Servers that need real credentials/binaries to even *list* tools become annotated
rows, not crashes — that's a finding too. Writes docs/MCP-LEADERBOARD.md +
docs/mcp-leaderboard-data.json.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys
import tempfile
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from lap import grade, lint, mcp_client, tokens  # noqa: E402

TIMEOUT = 150  # first run downloads the package into the uvx/npx cache


def _uvx() -> str | None:
    local = REPO / ".venv" / "Scripts" / "uvx.exe"
    return str(local) if local.exists() else shutil.which("uvx")


def _npx() -> list[str] | None:
    local = REPO / ".tools" / "node" / "npx.cmd"
    if local.exists():  # .cmd needs the cmd shell on Windows
        return ["cmd", "/c", str(local)]
    found = shutil.which("npx")
    return [found] if found else None


TMP = pathlib.Path(tempfile.mkdtemp(prefix="lap-mcp-lb-"))

# Curated: popular, published, and runnable without real credentials for tools/list.
# kind=pip -> uvx <pkg> [cmd overrides the entrypoint]; kind=npm -> npx -y <pkg>.
SERVERS: list[dict] = [
    {"name": "mcp-server-git", "kind": "pip", "pkg": "mcp-server-git",
     "args": ["--repository", str(REPO)], "by": "official reference"},
    {"name": "mcp-server-time", "kind": "pip", "pkg": "mcp-server-time", "by": "official reference"},
    {"name": "mcp-server-fetch", "kind": "pip", "pkg": "mcp-server-fetch", "by": "official reference"},
    {"name": "mcp-server-sqlite", "kind": "pip", "pkg": "mcp-server-sqlite",
     "args": ["--db-path", str(TMP / "lb.sqlite")], "by": "community"},
    {"name": "markitdown-mcp", "kind": "pip", "pkg": "markitdown-mcp", "by": "Microsoft"},
    {"name": "mcp-atlassian", "kind": "pip", "pkg": "mcp-atlassian", "by": "community (Atlassian ecosys)"},
    {"name": "duckduckgo-mcp-server", "kind": "pip", "pkg": "duckduckgo-mcp-server", "by": "community"},
    {"name": "wikipedia-mcp", "kind": "pip", "pkg": "wikipedia-mcp", "by": "community"},
    {"name": "arxiv-mcp-server", "kind": "pip", "pkg": "arxiv-mcp-server",
     "args": ["--storage-path", str(TMP)], "by": "community"},
    {"name": "mcp-server-calculator", "kind": "pip", "pkg": "mcp-server-calculator", "by": "community"},
    {"name": "aws-documentation-mcp", "kind": "pip", "pkg": "awslabs.aws-documentation-mcp-server",
     "cmd": "awslabs.aws-documentation-mcp-server", "by": "AWS Labs"},
    {"name": "excel-mcp-server", "kind": "pip", "pkg": "excel-mcp-server",
     "args": ["stdio"], "by": "community"},
    {"name": "yfmcp (Yahoo Finance)", "kind": "pip", "pkg": "yfmcp", "by": "community"},
    {"name": "server-everything", "kind": "npm", "pkg": "@modelcontextprotocol/server-everything",
     "by": "official reference"},
    {"name": "server-filesystem", "kind": "npm", "pkg": "@modelcontextprotocol/server-filesystem",
     "args": [str(TMP)], "by": "official reference"},
    {"name": "server-memory", "kind": "npm", "pkg": "@modelcontextprotocol/server-memory",
     "by": "official reference"},
    {"name": "sequential-thinking", "kind": "npm",
     "pkg": "@modelcontextprotocol/server-sequential-thinking", "by": "official reference"},
    {"name": "server-postgres", "kind": "npm", "pkg": "@modelcontextprotocol/server-postgres",
     "args": ["postgresql://user:pass@localhost:5432/db"], "by": "official (archived)"},
    {"name": "context7", "kind": "npm", "pkg": "@upstash/context7-mcp", "by": "Upstash"},
    {"name": "playwright-mcp", "kind": "npm", "pkg": "@playwright/mcp", "by": "Microsoft"},
    {"name": "firecrawl-mcp", "kind": "npm", "pkg": "firecrawl-mcp",
     "env": {"FIRECRAWL_API_KEY": "fc-dummy-lap-scan"}, "by": "Firecrawl"},
    {"name": "notion-mcp-server", "kind": "npm", "pkg": "@notionhq/notion-mcp-server",
     "env": {"NOTION_TOKEN": "ntn_dummy_lap_scan"}, "by": "Notion"},
    # community alternative that showed up in the r/mcp thread claiming token savings -
    # scored on request, same rules as everyone
    {"name": "easy-notion-mcp", "kind": "npm", "pkg": "easy-notion-mcp",
     "env": {"NOTION_TOKEN": "ntn_dummy_lap_scan"}, "by": "community (Grey-Iris)"},
]

# agent-friend's published grades (dev.to, 2026-03; 156 static checks, 40/30/30 formula)
# for the cross-check section. Keyed by our row name.
AGENT_FRIEND = {
    "context7": "F (7.5/100)",
    "server-postgres": "100/100 (\"perfect\")",
    "notion-mcp-server": "F (19.8/100); 4,483 tok / 22 tools",
}


def fetch(entry: dict):
    from fastmcp.client.transports import StdioTransport

    if entry["kind"] == "pip":
        uvx = _uvx()
        if not uvx:
            raise RuntimeError("uvx not available")
        cmd, args = uvx, []
        if entry.get("cmd"):
            args += ["--from", entry["pkg"], entry["cmd"]]
        else:
            args += [entry["pkg"]]
    else:
        npx = _npx()
        if not npx:
            raise RuntimeError("npx not available")
        cmd, args = npx[0], npx[1:] + ["-y", entry["pkg"]]
    args += entry.get("args", [])
    env = {**os.environ, **entry.get("env", {})}
    node_dir = REPO / ".tools" / "node"
    if entry["kind"] == "npm" and node_dir.exists():
        # npx re-spawns `node` for the package binary via PATH, not %~dp0
        env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
    transport = StdioTransport(cmd, args, env=env, keep_alive=False)
    return mcp_client.fetch_tools(transport, timeout=TIMEOUT)


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    rows, dead = [], []
    for entry in SERVERS:
        try:
            tools = fetch(entry)
            if not tools:
                raise RuntimeError("advertised 0 tools")
            s = mcp_client.score_tools(tools)
            found = lint.lint_tools(tools)
            warns = sum(1 for f in found if f.severity == "warn")
            infos = len(found) - warns
            g = grade.compute_parts(len(tools), s["menu"]["mcp_live"], 0, warns, infos)
            heaviest = max(tools, key=lambda t: tokens.count_tools([t]))
            rows.append({
                "name": entry["name"], "pkg": entry["pkg"], "kind": entry["kind"],
                "by": entry["by"], "tools": len(tools),
                "menu": s["menu"]["mcp_live"], "compact": s["menu"]["compact_sig"],
                "per_tool": round(s["menu"]["mcp_live"] / len(tools)),
                "warn": warns, "info": infos,
                "grade": g["letter"], "score": g["score"],
                "heaviest": heaviest["name"],
                "heaviest_tok": tokens.count_tools([heaviest]),
            })
            print(f"OK   {entry['name']:26} tools={len(tools):3} menu={s['menu']['mcp_live']:6} "
                  f"grade={g['letter']} ({g['score']})")
        except Exception as e:  # noqa: BLE001 - dead servers are rows, not crashes
            note = f"{type(e).__name__}: {str(e) or repr(e)}"[:90].replace("\n", " ")
            dead.append({"name": entry["name"], "pkg": entry["pkg"], "kind": entry["kind"], "note": note})
            print(f"DEAD {entry['name']:26} {note}")

    rows.sort(key=lambda r: r["menu"], reverse=True)
    total_menu = sum(r["menu"] for r in rows)
    total_compact = sum(r["compact"] for r in rows)

    lines = [
        "# MCP-server leaderboard — what popular published servers charge your context window",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/mcp_leaderboard.py`](../experiments/mcp_leaderboard.py); tokenizer: "
        f"**{tokens.backend_name()}**. Each server was installed and run locally in an isolated "
        "env (`uvx` / `npx -y`), its advertised tool list fetched over stdio with **no "
        "credentials** (dummy env vars only where a server refuses to boot without them), and "
        "scored exactly like `lap lint --mcp`: menu (bucket A) tokens + M-rule hygiene + the "
        "composite grade (result sub-score skipped - tool listings don't declare response "
        "shapes). Same method as the [OpenAPI leaderboard](LEADERBOARD.md)._",
        "",
        f"**{len(rows)} servers reachable, {sum(r['tools'] for r in rows)} tools; their menus "
        f"total {total_menu:,} tokens per session before the first user message** - a compact "
        f"rendering of the same tools would cost {total_compact:,} "
        f"({round(100 * (total_menu - total_compact) / total_menu)}% less). Every session with "
        "these servers connected pays the menu whether the tools are used or not "
        "([cache math](CACHE-ECONOMICS.md): caching discounts the price, not the context).",
        "",
        "| server | by | tools | menu tok | tok/tool | compact | saved | findings (warn/info) | grade |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        saved = round(100 * (r["menu"] - r["compact"]) / r["menu"]) if r["menu"] else 0
        lines.append(f"| {r['name']} | {r['by']} | {r['tools']} | {r['menu']:,} | "
                     f"{r['per_tool']} | {r['compact']:,} | {saved}% | "
                     f"{r['warn']}/{r['info']} | **{r['grade']}** ({r['score']}) |")
    lines += [
        "",
        "_`saved` = compact signatures of the same tools (what [rule D1]"
        "(../profile/llm-api-profile.md) asks for). Grades: menu weight 0.45 + hygiene 0.25, "
        "renormalized; A >= 85 ... F < 40._",
        "",
    ]
    if dead:
        lines += [
            "## Not reachable without credentials / extra runtime",
            "",
            "These wouldn't even list tools in a clean environment - noted, not scored:",
            "",
            "| server | kind | error |",
            "| --- | --- | --- |",
        ]
        lines += [f"| {d['name']} | {d['kind']} | `{d['note']}` |" for d in dead]
        lines += [""]

    overlap = [r for r in rows if r["name"] in AGENT_FRIEND]
    if overlap:
        lines += [
            "## Cross-check: agent-friend's published grades",
            "",
            "[agent-friend](https://github.com/0-co/agent-friend) (MCP-only static linter, 156 "
            "checks, 40% correctness / 30% efficiency / 30% quality) published grades for 201 "
            "servers (2026-03). On the servers both tools scored:",
            "",
            "| server | agent-friend | lap | lap menu tok |",
            "| --- | --- | --- | ---: |",
        ]
        for r in overlap:
            lines.append(f"| {r['name']} | {AGENT_FRIEND[r['name']]} | "
                         f"{r['grade']} ({r['score']}) | {r['menu']:,} |")
        lines += [
            "",
            "Read: the graders *converge on Notion* (both F, scores within a point) yet "
            "*diverge hard on server-postgres* (their \"perfect 100\" vs our C - one tiny tool, "
            "but its 42-token menu hides an inputSchema with no descriptions, which our M-rules "
            "charge) and on context7 (D vs F). And even where the letters agree, the token "
            "counts don't (Notion: our 21,411 vs their 4,483 - different server versions, "
            "tokenizers, and what counts as \"the schema\"). The lesson is the referee point: "
            "**letters are formula artifacts; raw, reproducible token numbers are the "
            "measurement.** This leaderboard publishes both, plus the script.",
            "",
        ]
    lines += [
        "_Caveats: tool listing only (no calls billed or executed); one run per server; a "
        "server's menu can differ per version and per advertised capabilities; npm servers ran "
        "via `npx -y` (whatever version the registry serves today). Reproduce: "
        "`python experiments/mcp_leaderboard.py` - needs `uv` (pip) and Node for the npm rows._",
    ]

    (REPO / "docs" / "MCP-LEADERBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (REPO / "docs" / "mcp-leaderboard-data.json").write_text(json.dumps(
        {"generated": date.today().isoformat(), "tokenizer": tokens.backend_name(),
         "servers": rows, "unreachable": dead}, indent=1), encoding="utf-8")
    print(f"\n[written] docs/MCP-LEADERBOARD.md + mcp-leaderboard-data.json "
          f"({len(rows)} scored, {len(dead)} dead)")


if __name__ == "__main__":
    main()
