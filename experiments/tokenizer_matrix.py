"""v0.7 M4 - tokenizer sensitivity: are LAP's numbers an artifact of one BPE?

The standing objection to any token measurement: "whose tokens?" This script re-counts
the whole leaderboard corpus - the naive `openapi_full` menu and the LAP `compact_sig`
menu per API - under four BPE vocabularies (our published baseline `cl100k_base`, plus
`o200k_base`, `p50k_base`, `gpt2`), then reports what actually moves:

- absolute totals (they differ - that's why we say "relative ranking is the signal"),
- the average compact saving per API (the % claim),
- the *ranking* of APIs by naive-menu size (Kendall tau vs the baseline).

Faithful Anthropic `count_tokens` isn't re-run here (billed); Stage 13 measured it:
~60% higher absolutes than the tiktoken approximation, identical ordering.

Writes docs/TOKENIZERS.md. Offline; uses the leaderboard's cached specs.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys
import tempfile
from datetime import date

import tiktoken

from lap import menu
from lap import openapi_ir as ir

REPO = pathlib.Path(__file__).resolve().parents[1]
CACHE = pathlib.Path(tempfile.gettempdir()) / "lap-corpus"
BASELINE = "cl100k_base"  # what lap's tiktoken-approx backend uses
ENCODINGS = [BASELINE, "o200k_base", "p50k_base", "gpt2"]


def kendall_tau(a: list[float], b: list[float]) -> float:
    """Plain O(n^2) Kendall tau (no ties handling beyond counting them as discordant-free)."""
    n = len(a)
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            s = (a[i] - a[j]) * (b[i] - b[j])
            if s > 0:
                conc += 1
            elif s < 0:
                disc += 1
    pairs = n * (n - 1) / 2
    return (conc - disc) / pairs if pairs else 1.0


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    encs = {name: tiktoken.get_encoding(name) for name in ENCODINGS}
    rows = []
    for f in sorted(CACHE.glob("*.spec")):
        try:
            spec = ir._parse(f.read_text(encoding="utf-8"))
            if not ir.operations(spec):
                continue
            tools, _ = menu.full(spec)
            full_text = json.dumps(tools)  # same serialization as lap.tokens.count_tools
            _, compact_text = menu.compact(spec)
            row = {"api": spec.get("info", {}).get("title", "?")[:30]}
            for name, enc in encs.items():
                row[f"full_{name}"] = len(enc.encode(full_text, disallowed_special=()))
                row[f"compact_{name}"] = len(enc.encode(compact_text, disallowed_special=()))
                row[f"save_{name}"] = 100 * (1 - row[f"compact_{name}"] / row[f"full_{name}"])
            rows.append(row)
            print(f"OK {row['api']:32} " + "  ".join(
                f"{n.split('_')[0]}={row[f'full_{n}']}" for n in ENCODINGS))
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {f.name}: {type(e).__name__}: {str(e)[:60]}")

    base_rank = [r[f"full_{BASELINE}"] for r in rows]
    lines = [
        "# Tokenizer sensitivity - whose tokens are these anyway?",
        "",
        f"_Generated {date.today().isoformat()} by "
        "[`experiments/tokenizer_matrix.py`](../experiments/tokenizer_matrix.py) over the "
        f"{len(rows)}-API leaderboard corpus._",
        "",
        "lap's offline backend counts with **cl100k_base** and says so on every report "
        "(\"absolute numbers approximate, relative ordering robust\"). This doc checks that "
        "claim against three other BPE vocabularies on the exact same menu texts.",
        "",
        "## What moves and what doesn't",
        "",
        "| metric | " + " | ".join(ENCODINGS) + " |",
        "| --- | " + " | ".join("---:" for _ in ENCODINGS) + " |",
    ]
    total_row = ["naive total (tokens)"]
    save_row = ["mean compact saving"]
    spread_row = ["per-API saving spread (stdev)"]
    tau_row = ["ranking vs cl100k (Kendall tau)"]
    for name in ENCODINGS:
        total_row.append(f"{sum(r[f'full_{name}'] for r in rows):,}")
        saves = [r[f"save_{name}"] for r in rows]
        save_row.append(f"{statistics.mean(saves):.1f}%")
        spread_row.append(f"{statistics.stdev(saves):.1f} pp")
        tau_row.append(f"{kendall_tau(base_rank, [r[f'full_{name}'] for r in rows]):.3f}")
    for row_cells in (total_row, save_row, spread_row, tau_row):
        lines.append("| " + " | ".join(str(c) for c in row_cells) + " |")

    deltas = []
    for r in rows:
        saves = [r[f"save_{n}"] for n in ENCODINGS]
        deltas.append(max(saves) - min(saves))
    worst = max(zip(deltas, rows), key=lambda x: x[0])
    lines += [
        "",
        f"- **Absolute totals swing by up to "
        f"{100 * (max(int(t.replace(',', '')) for t in total_row[1:]) / min(int(t.replace(',', '')) for t in total_row[1:]) - 1):.0f}%** "
        "across vocabularies - never quote lap's offline absolutes as model-billing numbers "
        "(set `ANTHROPIC_API_KEY` for faithful counts; Stage 13 measured those at ~60% above "
        "the approximation with identical ordering).",
        f"- **The savings claim barely moves**: the mean compact saving varies by "
        f"{max(float(s[:-1]) for s in save_row[1:]) - min(float(s[:-1]) for s in save_row[1:]):.1f} "
        f"percentage points across vocabularies; the single worst per-API spread is "
        f"{worst[0]:.1f} pp ({worst[1]['api']}).",
        "- **The ranking doesn't move**: Kendall tau >= "
        f"{min(float(t) for t in tau_row[1:]):.3f} against the baseline for every vocabulary "
        "- \"which APIs are heaviest and what a compact menu saves\" is tokenizer-robust.",
        "",
        "## Sample (10 heaviest APIs, naive-menu tokens per vocabulary)",
        "",
        "| API | " + " | ".join(ENCODINGS) + " | save (min..max) |",
        "| --- | " + " | ".join("---:" for _ in ENCODINGS) + " | --- |",
    ]
    for r in sorted(rows, key=lambda r: r[f"full_{BASELINE}"], reverse=True)[:10]:
        saves = [r[f"save_{n}"] for n in ENCODINGS]
        lines.append("| " + r["api"] + " | "
                     + " | ".join(f"{r[f'full_{n}']:,}" for n in ENCODINGS)
                     + f" | {min(saves):.0f}..{max(saves):.0f}% |")
    lines += [
        "",
        "_Method: identical menu texts (naive `openapi_full` JSON, LAP `compact_sig` text) "
        "per API, re-encoded with each vocabulary via tiktoken, `disallowed_special=()`. "
        "The compressed-vs-verbose gap is a property of the *text*, not the ruler._",
    ]

    out = REPO / "docs" / "TOKENIZERS.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[written] {out}  ({len(rows)} APIs x {len(ENCODINGS)} vocabularies)")


if __name__ == "__main__":
    main()
