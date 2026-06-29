"""Unified `lap` command: `lap score <openapi>` / `lap lint <openapi>`.

Thin dispatcher so the toolkit is one console command after `pip install`. Each
subcommand reuses its module's own argument parsing.
"""

from __future__ import annotations

import sys

_USAGE = "usage: lap {score|lint} <openapi-file-or-url> [options]\n" \
         "  score  measure the menu (bucket A) token cost\n" \
         "  lint   flag LAP profile rule violations"


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(_USAGE)
        return
    cmd, rest = argv[0], argv[1:]
    sys.argv = [f"lap {cmd}", *rest]  # so each subcommand's argparse sees clean args
    if cmd == "score":
        from . import score

        score.main()
    elif cmd == "lint":
        from . import lint

        lint.main()
    else:
        print(f"lap: unknown command {cmd!r}\n{_USAGE}")
        sys.exit(2)


if __name__ == "__main__":
    main()
