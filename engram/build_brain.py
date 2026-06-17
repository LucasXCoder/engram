"""Validate a brain's atom/edge graph, report density + connectivity, regenerate the graph.

Usage:  python -m engram build <brain-dir>

Checks integrity (unique ids, required keys, every edge endpoint resolves), reports per-source
atom density against a calibrated gate, prints connectivity, then ALWAYS regenerates graph.html
from the store so the visualization can never drift. Exits non-zero if any source with atoms
falls below the density gate — treat that as "build NOT done".
"""
from __future__ import annotations

import collections
import sys

from . import build_graph
from .core import REQUIRED_ATOM_KEYS, require_brain

# atom-grain gate: a source mined to the atom standard sits well under these words/atom ceilings.
GATE_LONGFORM = 58   # >=1500 words
GATE_DEFAULT = 70    # shorter sources
LONGFORM = 1500


def check_integrity(atoms: list, edges: list) -> list:
    errs: list[str] = []
    byid: dict = {}
    for a in atoms:
        if a.get("id") in byid:
            errs.append(f"duplicate atom id {a.get('id')}")
        byid[a.get("id")] = a
        miss = REQUIRED_ATOM_KEYS - set(a)
        if miss:
            errs.append(f"atom {a.get('id')} missing {sorted(miss)}")
    for e in edges:
        if e.get("from") not in byid:
            errs.append(f"edge from missing: {e.get('from')}")
        if e.get("to") not in byid:
            errs.append(f"edge to missing: {e.get('to')}")
    return errs


def main(argv: list[str]) -> int:
    brain = require_brain(argv[0] if argv else ".")
    if brain is None:
        return 2
    atoms = brain.atoms()
    edges = brain.edges()
    byid = {a["id"]: a for a in atoms}

    errs = check_integrity(atoms, edges)
    print("INTEGRITY:", "OK" if not errs else errs[:10])

    per_src = collections.Counter()
    for a in atoms:
        for s in a.get("sources", []):
            per_src[s] += 1
    touched = {e["from"] for e in edges} | {e["to"] for e in edges}
    words = brain.transcript_words()

    print(f"\nATOMS {len(atoms)} | EDGES {len(edges)} | "
          f"connectivity {len(touched & set(byid))}/{len(atoms)} atoms linked")
    print("by type:", dict(collections.Counter(a.get("type") for a in atoms)))
    print("by rel: ", dict(collections.Counter(e.get("rel") for e in edges)))

    flagged = []
    print(f"\n{'WORDS':>6}{'ATOMS':>6}{'w/atom':>8}  SOURCE")
    for vid, n in sorted(per_src.items(), key=lambda x: -words.get(x[0], 0)):
        w = words.get(vid, 0)
        wpa = w / n if n else 999
        gate = GATE_LONGFORM if w >= LONGFORM else GATE_DEFAULT
        tag = "FLAG" if wpa > gate else "ok"
        if tag == "FLAG":
            flagged.append(vid)
        print(f"{w:>6}{n:>6}{wpa:>8.0f}  [{tag}] {vid}")

    print(f"\nrollout: {len(per_src)}/{len(words)} sources have atoms "
          f"({len(words) - len(per_src)} remaining)")

    # ALWAYS regenerate the graph so it can never go stale relative to the store.
    try:
        build_graph.build(brain)
    except Exception as exc:  # pragma: no cover - defensive
        print("  (graph rebuild failed:", exc, ")")

    if errs:
        print(f"\n[FAIL] {len(errs)} integrity error(s).")
        return 1
    if flagged:
        print(f"\n[FAIL] {len(flagged)} source(s) below atom-density gate: {flagged}")
        return 1
    print("\n[OK] integrity clean and every source with atoms clears the gate.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
