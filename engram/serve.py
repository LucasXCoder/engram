"""Open a brain's graph in the default browser.

  python -m engram serve <brain> [--no-build]

Regenerates graph.html from the current store (unless --no-build) and opens it. A built brain's
visualization is one command away instead of hunting for the file.
"""
from __future__ import annotations

import os
import sys
import webbrowser

from . import build_graph
from .core import require_brain


def main(argv: list[str]) -> int:
    no_build = "--no-build" in argv
    args = [a for a in argv if not a.startswith("--")]
    brain = require_brain(args[0] if args else ".")
    if brain is None:
        return 2

    if not no_build:
        try:
            build_graph.build(brain)
        except FileNotFoundError as exc:
            print(f"error: could not build graph — {exc}", file=sys.stderr)
            return 1
    if not os.path.exists(brain.graph_path):
        print(f"error: no graph at {brain.graph_path}; run `python -m engram build {brain.root}`",
              file=sys.stderr)
        return 1

    uri = "file:///" + os.path.abspath(brain.graph_path).replace(os.sep, "/").lstrip("/")
    print(f"opening {brain.graph_path}")
    webbrowser.open(uri)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
