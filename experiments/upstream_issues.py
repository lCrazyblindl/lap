"""v0.9 W4 — the upstream fix drive: evidence + measured what-ifs for the MCP-server
leaderboard's three worst offenders, and ready-to-paste upstream issues.

The motion is the one that already converted once (mcp-compressor #236 -> fix PR #237
merged in 3 hours, verified in docs/MCP-COMPRESSOR.md): a specific, measured, fix-suggesting
report. Three different pathologies:

- sequential-thinking (modelcontextprotocol/servers): ONE tool costing ~921 tokens - the
  description is an essay whose "Parameters explained" section duplicates the schema's own
  parameter descriptions (all 9 params already carry one).
- firecrawl-mcp (firecrawl/firecrawl-mcp-server): descriptions embed usage essays
  (~1,200-1,650 tokens each) while 24/26 tools have UNdescribed parameters.
- notion-mcp-server (makenotion/notion-mcp-server): terse descriptions (good!) but
  schemas inline whole Notion object trees per tool; the same subtrees repeat across
  tools - $defs hoisting (blessed by SEP-2106) is measurable.

Writes docs/UPSTREAM-ISSUES.md. The issue texts are PREPARED, NOT POSTED - the owner
reviews and authorizes each posting separately. Reuses mcp_leaderboard's fetch machinery.
"""

from __future__ import annotations

import json
import pathlib
import sys
from datetime import date

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "experiments"))

import mcp_leaderboard as lb  # noqa: E402
from lap import tokens  # noqa: E402

TARGETS = {
    "sequential-thinking": "modelcontextprotocol/servers (src/everything's sibling, `src/sequentialthinking`)",
    "notion-mcp-server": "makenotion/notion-mcp-server",
    "firecrawl-mcp": "firecrawl/firecrawl-mcp-server",
}

# The official Gcore server (uvx from git; PyPI absent). Scored 2026-07-11 on owner request:
# the heaviest MCP menu we've ever measured. Fetched in BOTH configs so the 90%-subset
# number is reproducible, not quoted.
GCORE_PKG = "gcore-mcp-server@git+https://github.com/G-Core/gcore-mcp-server.git"
GCORE = {"name": "gcore-mcp-server", "kind": "pip", "pkg": GCORE_PKG, "cmd": "gcore-mcp-server",
         "env": {"GCORE_API_KEY": "dummy-lap-scan", "GCORE_TOOLS": "*"}}
GCORE_SUBSET_ENV = {"GCORE_API_KEY": "dummy-lap-scan",
                    "GCORE_TOOLS": "instances,management,cloud.gpu_baremetal.clusters.*"}


def first_para(desc: str) -> str:
    for p in (desc or "").split("\n\n"):
        if p.strip():
            return p.strip()
    return ""


def seq_trimmed(desc: str) -> str:
    """Keep the intro + 'When to use this tool:' block; drop 'Key features' (fluff) and
    'Parameters explained' (pure duplication of the schema's own param descriptions)."""
    out = []
    for p in (desc or "").split("\n\n"):
        head = p.strip().lower()
        if head.startswith(("key features", "parameters explained", "you should")):
            break
        if p.strip():
            out.append(p.strip())
    return "\n\n".join(out)


def with_desc(tools: list[dict], fn) -> int:
    return tokens.count_tools([{**t, "description": fn(t["description"] or "")} for t in tools])


def subtree_dedupe_estimate(tools: list[dict], min_chars: int = 120) -> tuple[int, int, list]:
    """Estimate the saving from hoisting identical nested schema subtrees (>= min_chars,
    appearing >= 2x across the toolset) into shared $defs. Char-based estimate converted
    at the toolset's own tokens/char ratio; $ref replacement costed at ~30 chars."""
    seen: dict[str, int] = {}

    def walk(node):
        if isinstance(node, dict):
            s = json.dumps(node, sort_keys=True, separators=(",", ":"))
            if len(s) >= min_chars:
                seen[s] = seen.get(s, 0) + 1
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for t in tools:
        walk(t["input_schema"] or {})
    total_chars = sum(len(json.dumps(t["input_schema"] or {})) for t in tools)
    total_tok = tokens.count_tools(tools)
    ratio = total_tok / max(1, sum(len(json.dumps(t)) for t in tools))
    saved_chars, examples = 0, []
    # greedy: biggest repeated subtrees first; skip subtrees contained in already-counted ones
    counted: list[str] = []
    for s, k in sorted(seen.items(), key=lambda kv: -len(kv[0]) * (kv[1] - 1)):
        if k < 2 or any(s in big for big in counted):
            continue
        gain = (k - 1) * (len(s) - 30) - 30  # keep 1 copy in $defs, pay a $ref per use
        if gain <= 0:
            continue
        saved_chars += gain
        counted.append(s)
        if len(examples) < 3:
            examples.append((k, len(s), s[:80]))
    return round(saved_chars * ratio), total_chars, examples


def main() -> None:
    sys.stdout.reconfigure(errors="replace")
    entries = {e["name"]: e for e in lb.SERVERS}
    data = {}
    for name in TARGETS:
        tools = lb.fetch(entries[name])
        data[name] = tools
        print(f"fetched {name}: {len(tools)} tools, {tokens.count_tools(tools)} tok")

    seq = data["sequential-thinking"]
    seq_now = tokens.count_tools(seq)
    seq_desc_tok = tokens.count(seq[0]["description"] or "")
    seq_after = with_desc(seq, seq_trimmed)
    seq_trim_tok = tokens.count(seq_trimmed(seq[0]["description"] or ""))

    fc = data["firecrawl-mcp"]
    fc_now = tokens.count_tools(fc)
    fc_after = with_desc(fc, first_para)
    fc_heavy = sorted(fc, key=lambda t: -tokens.count(t["description"] or ""))[:3]
    fc_undesc = 24  # M2 findings from lap lint (probe + MCP-LEADERBOARD data)

    nt = data["notion-mcp-server"]
    nt_now = tokens.count_tools(nt)
    nt_saved, nt_chars, nt_examples = subtree_dedupe_estimate(nt)
    nt_heavy = sorted(nt, key=lambda t: -tokens.count(json.dumps(t["input_schema"] or {})))[:3]

    gc = lb.fetch(GCORE)
    gc_now = tokens.count_tools(gc)
    gc_sub = lb.fetch({**GCORE, "env": GCORE_SUBSET_ENV})
    gc_sub_now = tokens.count_tools(gc_sub)
    gc_saved, _, gc_examples = subtree_dedupe_estimate(gc)
    gc_heavy = sorted(gc, key=lambda t: -tokens.count(json.dumps(t["input_schema"] or {})))[:3]
    from lap import lint as lint_mod
    gc_findings = lint_mod.lint_tools(gc)
    gc_by_rule: dict[str, int] = {}
    for f in gc_findings:
        gc_by_rule[f.rule] = gc_by_rule.get(f.rule, 0) + 1
    print(f"gcore *: {len(gc)} tools {gc_now} tok; subset: {len(gc_sub)} tools {gc_sub_now} tok; "
          f"dedupe est. saves {gc_saved}; rules {gc_by_rule}")

    d = date.today().isoformat()
    lines = [
        "# Upstream issues — prepared, measured, awaiting the owner's go-ahead",
        "",
        f"_Generated {d} by [`experiments/upstream_issues.py`](../experiments/upstream_issues.py); "
        f"tokenizer **{tokens.backend_name()}**; servers fetched live via `npx -y` (versions = "
        "registry latest on the scan date). **None of these has been posted** — the owner "
        "reviews and authorizes each one individually. The motion is the one that already "
        "converted: [mcp-compressor #236 → fixed & shipped in a day](MCP-COMPRESSOR.md)._",
        "",
        "| target | repo | today | measured what-if | saving |",
        "| --- | --- | ---: | ---: | ---: |",
        f"| sequential-thinking | modelcontextprotocol/servers | {seq_now:,} tok | {seq_after:,} tok | "
        f"{round(100 * (seq_now - seq_after) / seq_now)}% |",
        f"| firecrawl-mcp | firecrawl/firecrawl-mcp-server | {fc_now:,} tok | {fc_after:,} tok | "
        f"{round(100 * (fc_now - fc_after) / fc_now)}% |",
        f"| notion-mcp-server | makenotion/notion-mcp-server | {nt_now:,} tok | ~{nt_now - nt_saved:,} tok | "
        f"~{round(100 * nt_saved / nt_now)}% (dedupe alone) |",
        f"| gcore-mcp-server (`GCORE_TOOLS=*`) | G-Core/gcore-mcp-server | {gc_now:,} tok | "
        f"~{gc_now - gc_saved:,} tok | ~{round(100 * gc_saved / gc_now)}% (dedupe alone) |",
        "",
        "---",
        "",
        "## 1. modelcontextprotocol/servers — `sequentialthinking`",
        "",
        f"**Evidence.** One tool, **{seq_now:,} tokens** per session ({seq_desc_tok} description + "
        f"{tokens.count(json.dumps(seq[0]['input_schema']))} schema). All 9 parameters already "
        "carry `description`s in the inputSchema — yet the tool description's *\"Parameters "
        "explained\"* section restates every one of them in prose, and clients send both. "
        "\"Key features\" is marketing, not selection signal.",
        "",
        f"**Measured what-if:** keeping the intro + \"When to use this tool\" block (dropping the "
        f"two duplicating sections) → description {seq_desc_tok} → {seq_trim_tok} tok, tool "
        f"{seq_now:,} → **{seq_after:,} tok ({round(100 * (seq_now - seq_after) / seq_now)}% less, "
        "every session, no semantic loss** — the parameter semantics stay in the schema where "
        "they already live).",
        "",
        "**Ready-to-paste issue:**",
        "",
        "> **`sequentialthinking`'s tool definition costs ~921 tokens/session; about half "
        "duplicates the schema's own parameter descriptions**",
        ">",
        f"> The server advertises one tool whose definition costs **~{seq_now} tokens** (tiktoken "
        f"cl100k; ~{seq_desc_tok} of that is the description). Every session that connects the "
        "server pays this whether the tool is used or not.",
        ">",
        "> Two description sections look droppable at no semantic cost: *\"Parameters "
        "explained\"* restates the `description` that all 9 inputSchema parameters already "
        "carry (clients send both, so the text is paid twice), and *\"Key features\"* describes "
        "the tool's virtues rather than when to call it. Keeping the intro + \"When to use this "
        f"tool\" yields the same selection signal at **~{seq_after} tokens ("
        f"{round(100 * (seq_now - seq_after) / seq_now)}% less)** — measured on the published "
        "package, method + script: "
        "https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.",
        ">",
        "> Happy to send the trim as a PR if the direction sounds right. (Disclosure: I "
        "maintain `lap`, the measurement tool used; MIT, no product.)",
        "",
        "---",
        "",
        "## 2. firecrawl/firecrawl-mcp-server",
        "",
        f"**Evidence.** 26 tools, **{fc_now:,} tokens** of definitions per session. The cost "
        "is *descriptions as usage essays*: "
        + "; ".join(f"`{t['name']}` desc = {tokens.count(t['description'] or '')} tok"
                    for t in fc_heavy)
        + ". Sections like *\"Usage Example\"*, *\"CRITICAL - Format Selection\"*, *\"Common "
        "mistakes\"* are prompt-engineering docs, not tool-selection signal. Meanwhile **24 of "
        "26 tools have parameters with no description at all** (`lap lint --mcp` rule M2) — "
        "the guidance lives in the wrong layer.",
        "",
        f"**Measured what-if:** first paragraph only per description → **{fc_after:,} tok "
        f"({round(100 * (fc_now - fc_after) / fc_now)}% less)**. Realistic target is between "
        "the two (keep \"Best for\" one-liners; move parameter guidance into parameter "
        "descriptions).",
        "",
        "**Ready-to-paste issue:**",
        "",
        f"> **Tool descriptions embed usage essays (~{fc_now // 1000}k tokens of definitions "
        "per session) while 24/26 tools have undescribed parameters**",
        ">",
        f"> The server's 26 tool definitions cost **~{fc_now:,} tokens** (tiktoken cl100k) at "
        f"`tools/list` — paid by every session up front. The bulk is long-form description "
        "sections (`firecrawl_scrape` ~"
        f"{tokens.count(next(t for t in fc if t['name'] == 'firecrawl_scrape')['description'] or '')} "
        "tokens of description; \"Usage Example\", \"CRITICAL - Format Selection\", \"Common "
        "mistakes\"...). That's documentation, and models are good at *reading docs on "
        "demand* — but it's being paid per-session as selection metadata. At the same time, "
        "24 of 26 tools declare parameters with **no** `description`, so the layer models use "
        "for argument semantics is empty.",
        ">",
        f"> Measured what-if: trimming each description to its first paragraph alone puts the "
        f"menu at ~{fc_after:,} tokens (**{round(100 * (fc_now - fc_after) / fc_now)}% less**); "
        "a realistic middle (keep \"Best for\" lines, move format guidance into the relevant "
        "parameters' descriptions) lands close to that while *improving* argument-level "
        "clarity. Method + script: "
        "https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.",
        ">",
        "> Happy to draft the restructuring as a PR. (Disclosure: I maintain `lap`, the "
        "measurement tool; MIT, no product.)",
        "",
        "---",
        "",
        "## 3. makenotion/notion-mcp-server",
        "",
        f"**Evidence.** 24 tools, **{nt_now:,} tokens** — the leaderboard's heaviest. The "
        "descriptions are admirably terse (13–62 tok); the cost is **schemas**: "
        + "; ".join(f"`{t['name']}` schema = "
                    f"{tokens.count(json.dumps(t['input_schema'] or {}))} tok" for t in nt_heavy)
        + ". The same Notion object subtrees (rich-text, parent, annotations…) are inlined "
        "into tool after tool.",
        "",
        f"**Measured what-if:** hoisting identical repeated subtrees (≥120 chars, ≥2 uses) "
        f"into shared `$defs` saves **~{nt_saved:,} tokens (~{round(100 * nt_saved / nt_now)}%) "
        "by itself** — e.g. "
        + "; ".join(f"one {ln}-char subtree × {k}" for k, ln, _ in nt_examples)
        + ". The 2026 draft spec (SEP-2106) makes `$ref`/`$defs` in inputSchema first-class, "
        "so this no longer risks client compatibility. Plus 12 tools carry undescribed "
        "parameters (M2).",
        "",
        "**Ready-to-paste issue:**",
        "",
        f"> **Tool inputSchemas inline whole Notion object trees per tool — ~{nt_now // 1000}k "
        "tokens of definitions per session**",
        ">",
        f"> The server's 24 tools cost **~{nt_now:,} tokens** (tiktoken cl100k) at `tools/list` "
        "— the heaviest of 20 popular servers we measured "
        "(https://github.com/lCrazyblindl/lap/blob/main/docs/MCP-LEADERBOARD.md). The "
        "descriptions are terse (nice!); the weight is schemas: `API-update-page-markdown` "
        f"~{tokens.count(json.dumps(next(t for t in nt if t['name'] == 'API-update-page-markdown')['input_schema']))} "
        "tokens, `API-post-search` ~"
        f"{tokens.count(json.dumps(next(t for t in nt if t['name'] == 'API-post-search')['input_schema']))} "
        "— the same Notion object subtrees inlined into tool after tool.",
        ">",
        f"> Measured: hoisting identical repeated subtrees (≥120 chars, seen ≥2×) into shared "
        f"`$defs` saves **~{nt_saved:,} tokens (~{round(100 * nt_saved / nt_now)}%) on its "
        "own**, before any semantic slimming. The 2026-07-28 MCP spec explicitly allows "
        "`$ref`/`$defs` in `inputSchema` (SEP-2106), so the compatibility risk that used to "
        "argue for inlining is going away. Separately, 12 tools declare parameters without "
        "descriptions. Method + script: "
        "https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.",
        ">",
        "> Happy to contribute the $defs hoisting or the measurement harness. (Disclosure: I "
        "maintain `lap`, the measurement tool; MIT, no product.)",
        "",
        "---",
        "",
        "## 4. G-Core/gcore-mcp-server (added 2026-07-11)",
        "",
        f"**Evidence.** With `GCORE_TOOLS=*`: **{len(gc)} tools, {gc_now:,} tokens** of "
        f"definitions ({round(gc_now / len(gc))}/tool) — the heaviest MCP menu we have ever "
        "measured (22× the previous leaderboard maximum), and larger than a 200K context "
        "window: the full configuration cannot be loaded at all on most models. The schemas "
        "are SDK-generated and inline everything: "
        + "; ".join(f"`{t['name']}` schema = "
                    f"{tokens.count(json.dumps(t['input_schema'] or {}))} tok" for t in gc_heavy)
        + f". Findings: {gc_by_rule}. One tool fails to register outright "
        "(`fastedge.binaries.create`, pydantic can't schema `bytearray`). **Credit where due:** "
        f"the `GCORE_TOOLS` filter genuinely works — the README's suggested subset is "
        f"{len(gc_sub)} tools / {gc_sub_now:,} tokens (**{round(100 * (1 - gc_sub_now / gc_now))}% "
        "less**) — but even that subset is heavier than the leaderboard's worst full menu, at "
        f"{round(gc_sub_now / len(gc_sub))} tok/tool the per-tool density barely moves.",
        "",
        f"**Measured what-if:** hoisting identical repeated subtrees (≥120 chars, ≥2 uses) into "
        f"shared `$defs` saves **~{gc_saved:,} tokens (~{round(100 * gc_saved / gc_now)}%) by "
        "itself** — e.g. "
        + "; ".join(f"one {ln}-char subtree × {k}" for k, ln, _ in gc_examples)
        + ". Composable with the existing subset filter.",
        "",
        "**Ready-to-paste issue:**",
        "",
        f"> **`GCORE_TOOLS=*` advertises ~{gc_now // 1000}k tokens of tool definitions — "
        "larger than most context windows; `$defs` hoisting alone would cut ~"
        f"{round(100 * gc_saved / gc_now)}%**",
        ">",
        f"> Scored the server with the same open pipeline we use for a public MCP-server "
        f"leaderboard (fresh `uvx` from git, dummy key, tool listing only, tiktoken): with "
        f"`GCORE_TOOLS=*` it advertises **{len(gc)} tools / ~{gc_now:,} tokens** "
        f"({round(gc_now / len(gc))}/tool) — that exceeds a 200K context window on its own, so "
        "the full config can't actually be used with most models. Your `GCORE_TOOLS` filter is "
        f"a real mitigation (the README's suggested subset measures {len(gc_sub)} tools / "
        f"~{gc_sub_now:,} tokens, {round(100 * (1 - gc_sub_now / gc_now))}% less) — but the "
        "per-tool density stays ~600 tokens either way, because the SDK-generated schemas "
        "inline every nested object: `cdn_cdn_resources_new` alone is ~"
        f"{tokens.count(json.dumps(gc_heavy[0]['input_schema'] or {}))} tokens of schema.",
        ">",
        f"> Measured on the live listing: hoisting identical repeated subtrees (≥120 chars, "
        f"seen ≥2×) into shared `$defs` saves **~{gc_saved:,} tokens (~"
        f"{round(100 * gc_saved / gc_now)}%) on its own**, before any semantic slimming — and "
        "the 2026-07-28 MCP spec makes `$ref`/`$defs` in `inputSchema` first-class (SEP-2106), "
        "so client compatibility is no longer the blocker. Also: `fastedge.binaries.create` "
        f"fails to register (pydantic can't generate a schema for `bytearray`), and "
        f"{gc_by_rule.get('M2', 0)} of {len(gc)} tools have parameters with no description. "
        "Method + script: "
        "https://github.com/lCrazyblindl/lap/blob/main/docs/UPSTREAM-ISSUES.md.",
        ">",
        "> Happy to contribute the `$defs` hoisting pass or the measurement harness. "
        "(Disclosure: I maintain `lap`, the measurement tool; MIT, no product.)",
        "",
        "---",
        "",
        "_Posting checklist (owner): review each text → say the word → they get filed one at a "
        "time under your account (per the #236 precedent), each then joins the twice-daily "
        "reply watch._",
    ]
    out = REPO / "docs" / "UPSTREAM-ISSUES.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {out}")
    print(f"seq {seq_now}->{seq_after}  fc {fc_now}->{fc_after}  nt {nt_now}->~{nt_now - nt_saved}")


if __name__ == "__main__":
    main()
