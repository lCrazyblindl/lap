"""The composite LAP grade — one 0-100 number (and a letter) per API, plus `lap badge`.

The grade folds the three things `lap score`/`lap lint` already measure into one
at-a-glance figure, so an API can carry a README badge ("LAP A (92)") the way repos
carry coverage badges. Every constant is documented here and in the profile; the
letter is only a summary — the full token decomposition behind it is one
`lap score` away.

Sub-scores (each 0-100):

- **menu** — naive-menu (bucket A) tokens *per operation*: what the API's
  definitions cost an agent per unit of capability. Log-scaled between
  ~80 tok/op (excellent; Swagger Petstore is ~92) and ~2400 tok/op (0 points;
  Kubernetes-style inlined schemas run >3000).
- **result** — the heaviest estimated single response (bucket C) at the default
  page size: the recurring per-call cost. Log-scaled between ~300 tokens (fine)
  and ~30000 (0 points; unpaginated/enveloped monsters). APIs with no estimable
  responses skip this sub-score (weights renormalize).
- **hygiene** — LAP lint findings per operation, warnings double-weighted:
  100 at zero findings, 0 at >=2 weighted findings/op.

Composite = 0.45*menu + 0.30*result + 0.25*hygiene ->
A >=85, B >=70, C >=55, D >=40, F below.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib

MENU_BEST, MENU_WORST = 80, 2400        # naive-menu tokens per operation
RESULT_BEST, RESULT_WORST = 300, 30000  # heaviest estimated result, tokens/page
HYGIENE_WORST = 2.0                     # weighted lint findings per operation
WEIGHTS = {"menu": 0.45, "result": 0.30, "hygiene": 0.25}
LETTERS = [(85, "A"), (70, "B"), (55, "C"), (40, "D")]  # else F
COLORS = {"A": "brightgreen", "B": "green", "C": "yellow", "D": "orange", "F": "red"}


def _log_scale(value: float, best: float, worst: float) -> int:
    """100 at <=best, 0 at >=worst, log-linear between (sizes span orders of magnitude)."""
    if value <= best:
        return 100
    if value >= worst:
        return 0
    return round(100 * (math.log(worst) - math.log(value)) / (math.log(worst) - math.log(best)))


def compute_parts(operations: int, full_menu_tokens: int, c_max: int | None,
                  warn_count: int, info_count: int) -> dict:
    """Pure grade computation from already-measured parts (testable, no I/O)."""
    if not operations:
        return {"score": 0, "letter": "F", "subscores": {}, "note": "no operations found"}

    subs = {"menu": _log_scale(full_menu_tokens / operations, MENU_BEST, MENU_WORST)}
    if c_max:  # None or 0 = nothing estimable -> sub-score skipped, weights renormalize
        subs["result"] = _log_scale(c_max, RESULT_BEST, RESULT_WORST)
    weighted = (2 * warn_count + info_count) / operations
    subs["hygiene"] = round(100 * max(0.0, 1 - weighted / HYGIENE_WORST))

    total_w = sum(WEIGHTS[k] for k in subs)
    score = round(sum(subs[k] * WEIGHTS[k] for k in subs) / total_w)
    letter = next((let for cut, let in LETTERS if score >= cut), "F")
    return {"score": score, "letter": letter, "subscores": subs}


def compute(spec: dict, page_size: int = 20, string_len: int = 6) -> dict:
    """Grade a loaded OpenAPI spec (assembles the parts, then compute_parts)."""
    from . import estimate, lint
    from . import openapi_ir as ir
    from . import score as score_mod

    ops = ir.operations(spec)
    full = score_mod.score(spec)["openapi_full"] if ops else 0
    c_max = 0
    for op in ops:
        kind, _per, est = estimate.estimate(spec, op, page_size, string_len)
        if kind != "void":
            c_max = max(c_max, est)
    findings = lint.lint(spec)
    warns = sum(1 for f in findings if f.severity == "warn")
    infos = len(findings) - warns
    return compute_parts(len(ops), full, c_max, warns, infos)


def badge(grade: dict, label: str = "LAP") -> dict:
    """A shields.io endpoint document (https://shields.io/badges/endpoint-badge)."""
    return {
        "schemaVersion": 1,
        "label": label,
        "message": f"{grade['letter']} ({grade['score']})",
        "color": COLORS[grade["letter"]],
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="lap badge",
        description="Write a shields.io endpoint JSON with the API's LAP grade - "
                    "host it (repo raw URL, gist, Pages) and embed "
                    "https://img.shields.io/endpoint?url=<that-url> in your README.")
    ap.add_argument("source", help="OpenAPI spec: file path or http(s) URL")
    ap.add_argument("-o", "--out", default="lap-badge.json", help="output path (default lap-badge.json)")
    ap.add_argument("--label", default="LAP", help="badge label (default LAP)")
    ap.add_argument("--page-size", type=int, default=20)
    args = ap.parse_args()

    from . import openapi_ir as ir

    g = compute(ir.load_spec(args.source), args.page_size)
    doc = badge(g, args.label)
    pathlib.Path(args.out).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    subs = "  ".join(f"{k}={v}" for k, v in g["subscores"].items())
    print(f"LAP grade: {g['letter']} ({g['score']})   [{subs}]")
    print(f"[written] {args.out}")


if __name__ == "__main__":
    main()
