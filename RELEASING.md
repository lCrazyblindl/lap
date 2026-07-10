# Releasing `lap`

The toolkit and artifacts are prepared in-repo; publishing needs credentials only the owner
holds (never pasted into chat — set as environment variables, or via `gh auth login`). Steps:

**v0.7.0 status (2026-07-10): FULLY RELEASED.** `lap-score` 0.7.0 is live:
https://pypi.org/project/lap-score/0.7.0/ (twine PASSED ×2; fresh-venv verified — the new
Python API facade returns the reference figures and `lap score --diff --git` runs from the
published wheel). Ships the stable Python API (`score_spec`/`lint_spec`/`grade_spec`/
`diff_specs`), `--diff --git <ref>`, the pre-commit recipe, and the written 1.0 bar.

**v0.6.0 status (2026-07-09): FULLY RELEASED.** `lap-score` 0.6.0 is live:
https://pypi.org/project/lap-score/0.6.0/ (`twine check` PASSED ×2, uploaded, fresh-venv
verified — `flat_schema` + `lap score` work from the published wheel). Ships the
composed-inputSchema fix (SEP-2106), rule D0/`--discovery`, the PBT hardening (10 crash
sites), and the 14-keyword PyPI metadata. Tag `v0.6.0` + GitHub release with both dists.

**v0.5.0 status (2026-07-07): FULLY RELEASED.** `lap-score` 0.5.0 is live:
https://pypi.org/project/lap-score/0.5.0/ (`twine check` PASSED ×2, uploaded, fresh-venv
verified — `lap fix --apply` + `lap score` work from the published package). Tag `v0.5.0` +
GitHub release with both dists: https://github.com/lCrazyblindl/lap/releases/tag/v0.5.0.
Ships `lap fix` (Overlay), projected bucket-C, and the query-param menu fix — the published
leaderboard is generated with this code, so the package reproduces the published numbers.

**v0.4.0 status (2026-07-06): FULLY RELEASED.** `lap-score` 0.4.0 is live:
https://pypi.org/project/lap-score/0.4.0/ (`twine check` PASSED ×2, uploaded, verified in a
fresh venv — `pip install "lap-score[mcp]"` + `lap score`/`lap badge`/`lap lint --mcp` all work
as documented). Tag `v0.4.0` pushed; GitHub release published with both dist files:
https://github.com/lCrazyblindl/lap/releases/tag/v0.4.0. Gotcha fixed en route: PowerShell 5.1
`Set-Content -Encoding utf8` writes a BOM, which breaks TOML parsing — strip it (or write via
`[IO.File]::WriteAllText` with `UTF8Encoding($false)`).

**v0.3.0 status (2026-07-01): FULLY RELEASED.** `lap-score` 0.3.0 is live:
https://pypi.org/project/lap-score/0.3.0/ (built, `twine check` PASSED, uploaded, and verified
in a fresh venv — `pip install lap-score` + `lap score <spec>` works). Git tag `v0.3.0` is
pushed, and the GitHub release is published with both dist files attached:
https://github.com/lCrazyblindl/lap/releases/tag/v0.3.0. (`gh` was initially unauthenticated in
the agent's shell due to a stale cached `PATH` from before install — the owner ran
`gh auth login` themselves, and refreshing `$env:Path` from the registry inside the next command
found it.) Only remaining, optional step: "Publish this Action to the Marketplace" from the
release page (UI-only, no `gh` command for it).

## 1. Pre-flight
```bash
pip install -e ".[dev]"
pytest -q                      # full suite green
python -m lap.lint lap/examples/bookstore.openapi.json   # smoke
```
Confirm `version` in `pyproject.toml` and the top section of `CHANGELOG.md` match the
release you intend to cut (currently **0.3.0**).

## 2. Build the distribution
```bash
python -m pip install --upgrade build twine
python -m build                # -> dist/lap_score-<version>.tar.gz + .whl
twine check dist/*
```

## 3. Publish to PyPI (owner) — ✅ done for 0.3.0
```bash
# optional dry run on TestPyPI first:
# twine upload -r testpypi dist/*
twine upload dist/*            # needs a PyPI API token (e.g. TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-...)
```
After this, `pip install lap-score` works for everyone (and the GitHub Action installs
from PyPI instead of falling back to git).

## 4. Cut the GitHub release (owner) — ✅ done for 0.3.0
```bash
git tag v0.3.0          # ✅ done and pushed
git push origin v0.3.0  # ✅ done
gh release create v0.3.0 dist/* --title "lap 0.3.0" \
  --notes-file <(awk '/^## \[0.3.0\]/{f=1;next} /^## \[/{f=0} f' CHANGELOG.md)
# ✅ published: https://github.com/lCrazyblindl/lap/releases/tag/v0.3.0
```
Needs `gh` CLI authenticated (`gh auth login`) or a `GH_TOKEN`/`GITHUB_TOKEN` — set these
yourself in your own terminal, never paste the token into chat. No `dist/*` on hand? Rebuild
with steps 1–2 first (the files aren't committed to git).

Tagging `v0.3.0` also makes the composite Action usable as `uses: lCrazyblindl/lap@v0.3.0`.
**Still open (owner, UI-only):** to list it on the GitHub Marketplace, open the release (or
`action.yml`) on GitHub and choose **"Publish this Action to the Marketplace"** — it requires
accepting the developer agreement and a repo with a single top-level `action.yml` (already
present); there's no `gh` command for this specific step.

## Versioning
Pre-1.0, loose semver: bump the minor for new capabilities, patch for fixes. Update
`pyproject.toml` **and** add a dated `CHANGELOG.md` section in the same commit.
