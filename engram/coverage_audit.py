"""Coverage audit — catch under-extracted sources before a build is called done.

Usage:  python -m engram audit <brain-dir>

Reads the atom store + raw transcripts and reports words-per-atom per source. Flags any source
that fell below the density gate (or got ZERO atoms) — those must be re-mined. This is what
makes Engram give the SAME depth on any channel: the gate is calibrated to honest exhaustion at
the atom grain, not to a tidy summary.
"""
from __future__ import annotations

import collections
import sys

from .core import Brain, require_brain

GATE_LONGFORM = 58              # long-form (>=1500w): FAIL above this words/atom
GATE_DEFAULT = 70              # shorter sources: FAIL above this words/atom
FLOOR_WORDS_PER_ATOM = 25      # aspirational target grain (a careful human note-taker)
LONGFORM_WORDS = 1500


def audit(brain: Brain) -> tuple[list, list]:
    """Return (rows, flagged). Each row: (flag, longform, words, atoms, w/atom, src)."""
    per_src = collections.Counter()
    for a in brain.atoms():
        for s in a.get("sources", []):
            per_src[s] += 1
    words = brain.transcript_words()

    rows = []
    flagged = []
    for vid, w in words.items():
        c = per_src.get(vid, 0)
        wpa = (w / c) if c else float("inf")
        longform = w >= LONGFORM_WORDS
        gate = GATE_LONGFORM if longform else GATE_DEFAULT
        flag = (c == 0) or (wpa > gate)
        rows.append((flag, longform, w, c, wpa, vid))
        if flag:
            flagged.append(vid)
    rows.sort(key=lambda r: (-int(r[0]), -r[2]))
    return rows, flagged


def main(argv: list[str]) -> int:
    brain = require_brain(argv[0] if argv else ".")
    if brain is None:
        return 2
    n_atoms = len(brain.atoms())
    rows, flagged = audit(brain)
    total_words = sum(r[2] for r in rows)

    print(f"\nBRAIN: {brain.root}")
    print(f"atoms: {n_atoms} | transcripts: {len(rows)} | source words: {total_words:,}")
    if n_atoms and total_words:
        print(f"overall density: 1 atom / {total_words / n_atoms:.0f} words "
              f"(floor target <= {FLOOR_WORDS_PER_ATOM})")
    print()
    print(f"{'FLAG':<16}{'WORDS':>7}{'ATOMS':>7}{'W/ATOM':>9}  SOURCE")
    print("-" * 56)
    for flag, _lf, w, c, wpa, vid in rows:
        tag = ("ZERO-ATOMS" if c == 0 else "UNDER-EXTRACTED") if flag else "ok"
        if tag == "ok" and wpa > FLOOR_WORDS_PER_ATOM:
            tag = "thin"
        wpa_s = "inf" if c == 0 else f"{wpa:.0f}"
        print(f"{tag:<16}{w:>7}{c:>7}{wpa_s:>9}  {vid}")

    print()
    if flagged:
        print(f"[FAIL] {len(flagged)} source(s) UNDER-EXTRACTED — re-mine before finishing:")
        for v in flagged:
            print(f"   sources/transcripts/{v}.txt")
        return 1
    print("[OK] all sources clear the density gate.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
