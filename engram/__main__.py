"""Engram CLI — `python -m engram <command> …`

Commands:
  new <dir>                     scaffold a new empty brain
  fetch <channel> <dir>         enumerate a channel + fetch transcripts (incremental)
  add <dir> <stage.json>        append a staged batch of atoms + edges (guarded)
  build <dir>                   validate + density gate + regenerate graph.html
  audit <dir>                   coverage audit (words-per-atom density)
  polarity <dir> [--strict]     fidelity audit (negation / attribution / "we love pies")
  topics <dir>                  regenerate references/topics/*.md from the atom store
  graph <dir>                   regenerate graph.html only
  check <dir>                   build + audit + polarity in one pass (CI-friendly)
"""
from __future__ import annotations

import sys

from . import (add_video, build_brain, build_graph, build_topic_index, coverage_audit,
               fetch, polarity_audit, scaffold)

COMMANDS = {
    "new": scaffold.main,
    "fetch": fetch.main,
    "add": add_video.main,
    "build": build_brain.main,
    "audit": coverage_audit.main,
    "polarity": polarity_audit.main,
    "topics": build_topic_index.main,
    "graph": build_graph.main,
}


def _check(argv: list[str]) -> int:
    """Run the full quality gate: build, then coverage + polarity audits."""
    rc = build_brain.main(argv)
    print("\n" + "=" * 56)
    rc |= coverage_audit.main(argv)
    print("\n" + "=" * 56)
    rc |= polarity_audit.main(argv)
    return rc


COMMANDS["check"] = _check


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        print(f"unknown command: {cmd}\n", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2
    return COMMANDS[cmd](rest)


def cli() -> None:
    """Console-script entry point (see pyproject.toml)."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
