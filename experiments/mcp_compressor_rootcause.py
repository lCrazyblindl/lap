"""v0.7 V1 - root-cause the mcp-compressor self-report discrepancy from S2.

S2 (`docs/MCP-COMPRESSOR.md`) found the tool's own startup banner claiming its default
`medium` level costs **103.8% of original** on `mcp-server-time`, while our tokenizer
measured the exact same compressed frontend at **+12% saved**. Somebody's ruler differs.

This script measures the same raw-vs-compressed toolsets under **several candidate
metrics** - tiktoken tokens (ours), JSON characters, and UTF-8 bytes, in both compact
and pretty serialization - and captures the compressor's own banner (via the stdio
transport's stderr log) next to them. Whichever metric reproduces the banner percentage
is what the banner measures.

    MCP_SERVER_PY=<venv-with-servers>/Scripts/python.exe \
    MCP_COMPRESSOR_EXE=<venv-with-compressor>/Scripts/mcp-compressor.exe \
    python experiments/mcp_compressor_rootcause.py

Appends the explanation to docs/MCP-COMPRESSOR.md manually afterwards (this script just
prints the comparison table + the captured banners).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import tempfile

from lap import mcp_client, tokens

REPO = pathlib.Path(__file__).resolve().parents[1]
PY = os.environ.get("MCP_SERVER_PY") or sys.executable
COMPRESSOR = os.environ.get("MCP_COMPRESSOR_EXE") or "mcp-compressor"
LEVELS = ["low", "medium", "high", "max"]
SERVERS = [
    ("mcp-server-time", ["-m", "mcp_server_time"]),
    ("mcp-server-git", ["-m", "mcp_server_git", "--repository", str(REPO)]),
]


def metrics(tools: list[dict]) -> dict:
    compact = json.dumps(tools, separators=(",", ":"), ensure_ascii=False)
    pretty = json.dumps(tools, indent=2, ensure_ascii=False)
    return {
        "tokens": tokens.count_tools(tools),
        "chars_compact": len(compact),
        "bytes_compact": len(compact.encode("utf-8")),
        "chars_pretty": len(pretty),
    }


def fetch(transport_args, log_path: pathlib.Path | None = None) -> list[dict]:
    from fastmcp.client.transports import StdioTransport

    kw = {"keep_alive": False}
    if log_path is not None:
        kw["log_file"] = log_path
    return mcp_client.fetch_tools(StdioTransport(transport_args[0], transport_args[1:], **kw),
                                  timeout=45)


def _dumps(v) -> str:
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


def banner_original_size(tools: list[dict]) -> int:
    """banner.rs `compression_stats()`: original = name + description + the JSON of the
    `properties` SUB-OBJECT only - `type`, `required` and the tool-object scaffolding are
    not counted. Character (byte) lengths; no tokenizer anywhere in the stats path."""
    total = 0
    for t in tools:
        props = (t["input_schema"] or {}).get("properties")
        total += len(t["name"]) + len(t["description"] or "")
        total += len(_dumps(props)) if props is not None else 0
    return total


def banner_compressed_size(tools: list[dict]) -> int:
    """banner.rs `compressed_frontend_size()`: descriptions + FULL wrapper schema JSONs
    (and no tool names) - the asymmetric counterpart of `banner_original_size`."""
    return sum(len(t["description"] or "") + len(_dumps(t["input_schema"] or {})) for t in tools)


def main() -> None:
    sys.stdout.reconfigure(errors="replace")  # banners use box-drawing chars; cp1251 consoles choke
    for name, backend in SERVERS:
        raw = fetch([PY, *backend])
        m_raw = metrics(raw)
        b_orig = banner_original_size(raw)
        print(f"\n=== {name}  raw: {m_raw}  banner-formula original: {b_orig}")
        for level in LEVELS:
            fd, log_name = tempfile.mkstemp(suffix=f"-{name}-{level}.log")
            os.close(fd)  # Windows: an open fd blocks the transport from writing the log
            log = pathlib.Path(log_name)
            comp = fetch([COMPRESSOR, "-c", level, "--", PY, *backend], log_path=log)
            m = metrics(comp)
            ratios = {k: round(100 * m[k] / m_raw[k], 1) for k in m}
            banner = ""
            try:
                text = log.read_text(encoding="utf-8", errors="replace")
                hits = re.findall(r".*(?:compress|reduc|origin|%|ratio).*", text, re.I)
                banner = " | ".join(h.strip()[:160] for h in hits[:6])
            except OSError:
                pass
            print(f"  {level:6}: {m}")
            print(f"          ratio vs raw (%): {ratios}")
            print(f"          banner-formula replication: "
                  f"{100 * banner_compressed_size(comp) / b_orig:.1f}% "
                  "(chars, asymmetric per banner.rs)")
            if banner:
                print(f"          banner: {banner}")


if __name__ == "__main__":
    main()
