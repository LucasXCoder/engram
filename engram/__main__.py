"""Engram CLI — `python -m engram <command> …`

Commands:
  new <dir>                     scaffold a new empty brain
  fetch <channel> <dir>         enumerate a channel + fetch transcripts (incremental)
  add <dir> <stage.json>...     append staged batches of atoms + edges (guarded, multi-file)
  preview <dir> <stage.json>... validate + project density of stage files WITHOUT writing
  build <dir>                   validate + density gate + regenerate graph.html
  audit <dir>                   coverage audit (words-per-atom density)
  polarity <dir> [--strict]     fidelity audit (negation / attribution / "we love pies")
  topics <dir>                  regenerate references/topics/*.md from the atom store
  graph <dir>                   regenerate graph.html only
  check <dir>                   build + audit + polarity in one pass (CI-friendly)
  query <dir> [terms] [filters] search atoms by text/topic/type/tag/confidence (--edges --json)
  stats <dir>                   profile a brain: counts, distributions, most-connected atoms
  serve <dir>                   (re)build graph.html and open it in the browser
  register <dir>                upsert the brain into registry.json (auto counts + domains)
  which <term...>               'which brain knows about X?' across the registry
"""
from __future__ import annotations

import sys

from . import (add_video, build_brain, build_graph, build_topic_index, coverage_audit,
               fetch, polarity_audit, query, registry, scaffold, serve)

COMMANDS = {
    "new": scaffold.main,
    "fetch": fetch.main,
    "add": add_video.main,
    "preview": add_video.preview,
    "build": build_brain.main,
    "audit": coverage_audit.main,
    "polarity": polarity_audit.main,
    "topics": build_topic_index.main,
    "graph": build_graph.main,
    "query": query.query,
    "stats": query.stats,
    "serve": serve.main,
    "register": registry.register,
    "which": registry.which,
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
