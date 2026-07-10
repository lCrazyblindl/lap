"""LAP - an open, neutral token-efficiency toolkit for agent-facing APIs.

CLI: `lap score|lint|fix|stack|badge` (see lap/README.md).

Stable Python API (documented in lap/README.md "Python API"; covered by loose
semver from 0.7 - these signatures only break at a major version):

    import lap
    report   = lap.score_spec("openapi.json")          # dict, = `lap score --json`
    findings = lap.lint_spec("openapi.json")           # list[lap.Finding]
    grade    = lap.grade_spec("openapi.json")          # {"score", "letter", ...}
    delta    = lap.diff_specs("old.json", "new.json")  # dict, = `lap score --diff --json`

Each accepts a file path, an http(s) URL, or an already-parsed spec dict.
MCP-side helpers (need the `[mcp]` extra): `lap.mcp_client.fetch_tools`,
`lap.lint.lint_tools`, `lap.mcp_client.score_tools`.
"""

from __future__ import annotations

try:  # single source of truth for the version: pyproject metadata
    from importlib.metadata import version as _version

    __version__ = _version("lap-score")
except Exception:  # noqa: BLE001 - not installed (e.g. run from a checkout)
    __version__ = "0.0.0.dev"


def _load(source) -> dict:
    if isinstance(source, dict):
        return source
    from . import openapi_ir as ir

    return ir.load_spec(str(source))


def score_spec(source, *, page_size: int = 20, string_len: int = 6,
               mcp_baseline: bool = True) -> dict:
    """Full A/B/C report for an OpenAPI spec - the same dict `lap score --json` emits.

    `mcp_baseline=False` skips the real-MCP (FastMCP) row even when fastmcp is
    installed. Keys prefixed with `_` are internal and excluded, as in the CLI."""
    from types import SimpleNamespace

    from . import score as _score

    args = SimpleNamespace(page_size=page_size, string_len=string_len,
                           no_mcp=not mcp_baseline,
                           source=source if isinstance(source, str) else "<dict>")
    res = _score.gather(_load(source), args)
    return {k: v for k, v in res.items() if not k.startswith("_")}


def lint_spec(source) -> list:
    """LAP rule findings for an OpenAPI spec - a list of `lap.Finding` records."""
    from . import lint as _lint

    return _lint.lint(_load(source))


def grade_spec(source) -> dict:
    """The composite LAP grade (0-100 + letter + sub-scores) for an OpenAPI spec."""
    from . import grade as _grade

    return _grade.compute(_load(source))


def diff_specs(before, after) -> dict:
    """Menu-token delta per form + added/removed findings between two spec versions -
    the same dict `lap score --diff --json` emits."""
    from . import score as _score

    return _score.diff(_load(before), _load(after))


def __getattr__(name):  # lap.Finding without importing lint eagerly
    if name == "Finding":
        from .lint import Finding

        return Finding
    raise AttributeError(name)
