# Contributing to lap

Thanks for looking. lap is a **neutral, reproducible measurement layer** for the token
cost of agent-facing APIs — that neutrality is the product, so a few policies below are
stricter than usual for a small project. Everything else is ordinary: issues and PRs
welcome, MIT licensed.

## Dev setup

```bash
git clone https://github.com/lCrazyblindl/lap && cd lap
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev,mcp]"
pytest -q                                        # tests/ must be green (45+)
lap score lap/examples/bookstore.openapi.json    # smoke
```

- Core deps are just `httpx` + `tiktoken` + `pyyaml`; `fastmcp`/`anthropic` are extras —
  keep it that way (new hard deps need a strong reason).
- Experiments that talk to live models read `ANTHROPIC_API_KEY` from the environment and
  spend real money; they're never run in CI and must stay opt-in.
- The benchmark corpus is cached under the OS temp dir (`lap-corpus`); leaderboard/spec
  scripts are rerunnable from scratch.

## Policies (the short version)

1. **Vendor neutrality.** The README and docs don't feature or link individual commercial
   APIs/products as examples — the [leaderboard](docs/LEADERBOARD.md) (built from the
   public APIs.guru directory) is the "real API" example. PRs adding promotional links
   will be closed (see PR #1). Adding your API to the *leaderboard corpus* is fine — it's
   data, not endorsement, and it needs to be in APIs.guru.
2. **Claims need receipts.** Any number in a doc must be reproducible: name the script,
   the corpus, and the tokenizer. If you dispute one of our numbers — great, that's the
   point; open an issue with your measurement and we'll rerun both sides.
3. **Honest reporting.** If a measurement contradicts our own thesis, it ships anyway
   (see `docs/CODE-EXEC.md` — our own escape-hatch rule got a counter-example and the
   profile says so). Don't smooth over inconvenient rows.
4. **Measured, not asserted.** New lint rules or profile rules need a measurement that
   justifies them, not just taste. A rule PR should cite (or add) the experiment.

## What's most useful right now

- **Run `lap score` / `lap lint` / `lap stack` on your own specs and servers** and file
  issues for crashes, silently-wrong parses (Swagger 2.0 / OpenAPI 3.1 edge cases), or
  numbers that look off. The fuzz corpus is 175+ specs, but the long tail is long.
- Leaderboard candidates: well-known public APIs present in APIs.guru that we're missing.
- The [ROADMAP](ROADMAP.md) tracks planned work (currently the v0.7 tracks) — grab an
  unclaimed bullet, comment on an issue first so we don't collide.

## PR checklist

- `pytest -q` green; new behavior has a test.
- Docs regenerated if your change affects them (`experiments/leaderboard.py` for the
  leaderboard/site; scripts note which docs they own in their headers).
- No new hard dependencies; no vendor links; numbers have receipts.
- One logical change per PR; reference the issue.

## Releases

Owner-driven; see [RELEASING.md](RELEASING.md). Version bumps + `CHANGELOG.md` entries
land in the release commit, not in feature PRs.
