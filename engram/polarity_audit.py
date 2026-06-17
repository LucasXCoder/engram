"""Polarity & attribution audit — Engram's fidelity guardrail.

Usage:  python -m engram polarity <brain-dir> [--strict] [--limit N]

The #1 failure mode of any atomization system: a creator says "everyone thinks X, but that's
wrong" and the brain stores a bare atom "X" — inverting the meaning. Sarcasm, strawmen, and
debunks are where this hides.

This audit locates each atom in its source transcript and flags atoms that sit near negation or
attribution cues ("not", "myth", "they claim", "so-called", "wrong"…) yet are stored as the
creator's own voice (`attribution: "creator"`) with no `verbatim` anchor and no negation in the
atom text itself. Those are exactly the atoms a careless pass would invert — fix them by adding
`verbatim` (the exact words) or setting `attribution` to "quoted"/"hypothetical".

Heuristic, so it is advisory by default (exit 0). Pass --strict to fail the build on suspects.
"""
from __future__ import annotations

import os
import re
import sys

from .core import Brain, require_brain

NEG_CUES = (
    " not ", "n't ", " never ", " no ", " false", " wrong", " myth", " lie", " lying",
    " isn't", " aren't", " don't", " doesn't", " can't", " won't", " nobody", " nothing",
    " against", " debunk", " misconception", " incorrect", " untrue",
)
ATTR_CUES = (
    " they say", " they claim", " they tell", " gurus say", " gurus tell", " people think",
    " people say", " supposedly", " so-called", " claims to", " claim to", " told me",
    " told everybody", " told you", " sells you", " sell you", " convince",
)
STOP = set(
    "the a an and or of to in is are was were be been being that this it its for on with as "
    "you your they their he she his her we our i me my but if then so not no than from at by "
    "have has had do does did will would can could should about into over more most very just "
    "what which who whom when where why how all any some out up down off".split()
)


#: How many words around an atom's best match count as "near" it. Word-based (not sentence-
#: based) because auto-generated captions usually have no punctuation — one transcript would
#: otherwise be a single giant "sentence" and every atom would match it.
WINDOW = 14


def _salient(text: str) -> set:
    words = re.findall(r"[a-z']+", text.lower())
    return {w for w in words if len(w) > 3 and w not in STOP}


def _tokens(text: str) -> list:
    return re.findall(r"[a-z']+", text.lower())


def audit(brain: Brain) -> list:
    """Return a list of suspect dicts: {id, source, cue, sentence, text}."""
    tdir = brain.transcripts_dir
    transcripts = {}
    if os.path.isdir(tdir):
        for fn in os.listdir(tdir):
            if fn.endswith(".txt"):
                with open(os.path.join(tdir, fn), encoding="utf-8", errors="ignore") as f:
                    transcripts[fn[:-4]] = _tokens(f.read())

    cues = NEG_CUES + ATTR_CUES
    suspects = []
    for a in brain.atoms():
        # already anchored or attributed — the author handled the polarity explicitly
        if a.get("verbatim") or a.get("attribution", "creator") != "creator":
            continue
        atom_text = " " + a.get("text", "").lower() + " "
        # an atom that itself states the negation/attribution is fine (it captured the framing)
        if any(c in atom_text for c in cues):
            continue
        sal = _salient(a.get("text", ""))
        if not sal:
            continue
        for src in a.get("sources", []):
            toks = transcripts.get(src)
            if not toks:
                continue
            # slide a WINDOW-word window; find where the atom's salient words concentrate most
            best_i, best_ov = -1, 0
            for i in range(max(1, len(toks) - WINDOW + 1)):
                ov = len(sal.intersection(toks[i:i + WINDOW]))
                if ov > best_ov:
                    best_ov, best_i = ov, i
            # require the atom to be genuinely localized here (>= half its salient words)
            if best_i < 0 or best_ov < max(3, len(sal) // 2):
                continue
            window = " " + " ".join(toks[best_i:best_i + WINDOW]) + " "
            hit = next((c for c in cues if c in window), None)
            if hit:
                suspects.append({
                    "id": a["id"], "source": src, "cue": hit.strip(),
                    "sentence": window.strip(), "text": a["text"],
                })
                break
    return suspects


def main(argv: list[str]) -> int:
    strict = "--strict" in argv
    limit = 40
    if "--limit" in argv:
        i = argv.index("--limit")
        if i + 1 >= len(argv):
            print("error: --limit requires a value", file=sys.stderr)
            return 2
        try:
            limit = int(argv[i + 1])
        except ValueError:
            print(f"error: --limit must be an integer, got {argv[i + 1]!r}", file=sys.stderr)
            return 2
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    brain = require_brain(args[0] if args else ".")
    if brain is None:
        return 2

    suspects = audit(brain)
    n_atoms = len(brain.atoms())
    print(f"\nPOLARITY AUDIT: {brain.root}")
    print(f"scanned {n_atoms} atoms — {len(suspects)} near a negation/attribution cue "
          f"without a verbatim anchor or attribution tag\n")
    for s in suspects[:limit]:
        print(f"  [{s['id']}] cue={s['cue']!r}  ({s['source']})")
        print(f"     atom: {s['text'][:110]}")
        print(f"     near: …{s['sentence'][:120]}…\n")
    if len(suspects) > limit:
        print(f"  … and {len(suspects) - limit} more\n")

    if not suspects:
        print("[OK] no unanchored atoms near negation/attribution cues.")
        return 0
    print("Review each: add `verbatim` (exact words) or set `attribution` to "
          "\"quoted\"/\"hypothetical\" if the creator is reporting someone else's claim.")
    if strict:
        print(f"[FAIL] {len(suspects)} suspect atom(s) (--strict).")
        return 1
    print(f"[WARN] {len(suspects)} suspect atom(s) — advisory only.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
