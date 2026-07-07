"""`lap fix` - emit LAP lint fixes as an OpenAPI Overlay (advice -> applicable patch).

Generates an [OpenAPI Overlay 1.0.0](https://spec.openapis.org/overlay/v1.0.0) document
whose actions fix the *structurally fixable* LAP findings:

- **R3** no pagination on a collection GET  -> add a `limit` query parameter
- **R1** no field projection               -> add a `fields` query parameter
- **R2** no server-side filter             -> add a `filter` query parameter
- **E1** no declared error responses       -> add a `4XX` error response

D3 (opaque names) and A1 (no aggregate endpoint) are reported but not auto-fixed -
renames and new endpoints are semantic decisions, not patches.

The overlay declares the *contract*; the server still has to implement the parameters
(the generated document says so in its own description). Apply with any Overlay-aware
tool, or `lap fix <spec> --apply patched.json` for the built-in structured merge.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import date

from . import lint as lint_mod
from . import openapi_ir as ir

FIXES = {
    "R3": {"name": "limit", "in": "query", "required": False,
           "description": "Maximum items per page (added by LAP R3 - pick a sane default, "
                          "never 1; agents pull the whole collection without it).",
           "schema": {"type": "integer", "minimum": 1}},
    "R1": {"name": "fields", "in": "query", "required": False,
           "description": "Comma-separated fields to include in each item (added by LAP R1 - "
                          "field projection keeps responses lean for agents).",
           "schema": {"type": "string"}},
    "R2": {"name": "filter", "in": "query", "required": False,
           "description": "Server-side filter expression (added by LAP R2 - filtering "
                          "server-side beats fetch-then-filter-in-context).",
           "schema": {"type": "string"}},
}
E1_RESPONSE = {"4XX": {"description": "Error - a machine-readable code and message, "
                                      "distinguishable from success-empty (added by LAP E1)."}}


def build_overlay(spec: dict) -> dict:
    """One Overlay action per operation that has fixable findings (params merged)."""
    findings = lint_mod.lint(spec)
    per_op: dict[str, dict] = {}
    skipped: set[str] = set()
    for f in findings:
        if f.rule not in FIXES and f.rule != "E1":
            skipped.add(f.rule)
            continue
        m = re.fullmatch(r"([A-Z]+) (.+)", f.where)
        if not m:
            continue
        method, path = m.group(1).lower(), m.group(2)
        entry = per_op.setdefault(f.where, {"method": method, "path": path, "update": {}})
        if f.rule in FIXES:
            entry["update"].setdefault("parameters", []).append(FIXES[f.rule])
        else:  # E1
            entry["update"].setdefault("responses", {}).update(E1_RESPONSE)

    actions = []
    for where, entry in per_op.items():
        rules = [r for r in ("R3", "R1", "R2")
                 if any(p is FIXES[r] for p in entry["update"].get("parameters", []))]
        if "responses" in entry["update"]:
            rules.append("E1")
        actions.append({
            "target": f"$.paths['{entry['path']}'].{entry['method']}",
            "description": f"LAP {'/'.join(rules)} fixes for {where}",
            "update": entry["update"],
        })

    title = spec.get("info", {}).get("title", "(untitled API)")
    note = ("Declares the agent-efficiency contract LAP lint found missing; the server must "
            "implement the added parameters for the contract to hold.")
    if skipped:
        note += f" Not auto-fixed (semantic, see lap lint): {', '.join(sorted(skipped))}."
    return {
        "overlay": "1.0.0",
        "info": {"title": f"LAP lint auto-fixes for {title}",
                 "version": date.today().isoformat(),
                 "description": note},
        "actions": actions,
    }


def apply_overlay(spec: dict, overlay: dict) -> dict:
    """Structured merge of *this module's* actions (targets of the form
    `$.paths['<path>'].<method>`): dicts merge recursively, lists append - the Overlay
    spec's update semantics, scoped to what `build_overlay` emits."""
    out = json.loads(json.dumps(spec))  # deep copy
    for action in overlay.get("actions", []):
        m = re.fullmatch(r"\$\.paths\['(.+)'\]\.(\w+)", action.get("target", ""))
        if not m:
            continue
        node = out.get("paths", {}).get(m.group(1), {}).get(m.group(2))
        if node is not None:
            _merge(node, action.get("update", {}))
    return out


def _merge(dst: dict, upd: dict) -> None:
    for k, v in upd.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _merge(dst[k], v)
        elif isinstance(v, list) and isinstance(dst.get(k), list):
            dst[k] = dst[k] + v
        else:
            dst[k] = json.loads(json.dumps(v))


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="lap fix",
        description="Emit LAP lint fixes as an OpenAPI Overlay 1.0.0 document.")
    ap.add_argument("source", help="OpenAPI spec: file path or http(s) URL")
    ap.add_argument("-o", "--out", default="lap-overlay.yaml",
                    help="overlay output path (.yaml or .json; default lap-overlay.yaml)")
    ap.add_argument("--apply", metavar="PATCHED",
                    help="also write the spec with the overlay applied (JSON)")
    args = ap.parse_args()

    spec = ir.load_spec(args.source)
    overlay = build_overlay(spec)
    out = pathlib.Path(args.out)
    if out.suffix in (".yaml", ".yml"):
        import yaml

        out.write_text(yaml.safe_dump(overlay, sort_keys=False, allow_unicode=True),
                       encoding="utf-8")
    else:
        out.write_text(json.dumps(overlay, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = len(overlay["actions"])
    print(f"[written] {out}  ({n} action(s))")
    if not n:
        print("No structurally fixable findings - nothing to overlay. OK")
        return

    if args.apply:
        patched = apply_overlay(spec, overlay)
        pathlib.Path(args.apply).write_text(json.dumps(patched, indent=2, ensure_ascii=False) + "\n",
                                            encoding="utf-8")
        before = {(f.rule, f.where) for f in lint_mod.lint(spec)}
        after = {(f.rule, f.where) for f in lint_mod.lint(patched)}
        print(f"[written] {args.apply}  (lint findings: {len(before)} -> {len(after)})")
        if not before > after:
            print("warning: applying the overlay did not reduce lint findings", file=sys.stderr)


if __name__ == "__main__":
    main()
