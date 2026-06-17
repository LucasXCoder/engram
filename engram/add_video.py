"""Append staged atoms + edges to a brain's graph, atomically and guarded.

  python -m engram add     <brain-dir> <stage.json> [<stage2.json> ...]
  python -m engram preview <brain-dir> <stage.json> [<stage2.json> ...]

A stage file is `{"atoms": [...], "edges": [...]}`. `add` guards each file (abort writing *that
file* on any error): required keys present, valid `type`/`confidence`/`attribution`, no id
collisions (within the batch or against the store, cumulatively across the files in one run),
every edge endpoint resolves, valid `rel`. `preview` validates and projects per-source density
against the gate WITHOUT writing — catch thin mining before you commit.
"""
from __future__ import annotations

import collections
import json
import sys

from .core import (
    ATOM_TYPES, ATTRIBUTION, CONFIDENCE, EDGE_RELS, REQUIRED_ATOM_KEYS,
    append_jsonl, require_brain,
)

GATE_LONGFORM = 58
GATE_DEFAULT = 70
LONGFORM = 1500


def _load_stage(path: str):
    """Return (batch, error). batch is None on error."""
    try:
        with open(path, encoding="utf-8") as f:
            batch = json.load(f)
    except FileNotFoundError:
        return None, f"no such stage file: {path}"
    except json.JSONDecodeError as exc:
        return None, f"{path} is not valid JSON — {exc}"
    if not isinstance(batch, dict) or "atoms" not in batch:
        return None, f'{path} must be an object with an "atoms" key'
    return batch, None


def validate(batch: dict, existing_ids: set) -> list:
    """Return a list of human-readable errors (empty == valid)."""
    atoms = batch.get("atoms", [])
    edges = batch.get("edges", [])
    new_ids = {a.get("id") for a in atoms}
    valid_ids = existing_ids | new_ids

    errs: list[str] = []
    seen: set = set()
    for a in atoms:
        aid = a.get("id")
        miss = REQUIRED_ATOM_KEYS - set(a)
        if miss:
            errs.append(f"{aid}: missing keys {sorted(miss)}")
        if a.get("type") not in ATOM_TYPES:
            errs.append(f"{aid}: bad type {a.get('type')!r}")
        if a.get("confidence") not in CONFIDENCE:
            errs.append(f"{aid}: bad confidence {a.get('confidence')!r}")
        if a.get("attribution", "creator") not in ATTRIBUTION:
            errs.append(f"{aid}: bad attribution {a.get('attribution')!r}")
        if not a.get("sources"):
            errs.append(f"{aid}: empty sources")
        if aid in existing_ids:
            errs.append(f"{aid}: collides with existing store")
        if aid in seen:
            errs.append(f"{aid}: duplicate within batch")
        seen.add(aid)

    for e in edges:
        if e.get("from") not in valid_ids:
            errs.append(f"edge from {e.get('from')!r} unresolved")
        if e.get("to") not in valid_ids:
            errs.append(f"edge to {e.get('to')!r} unresolved")
        if e.get("rel") not in EDGE_RELS:
            errs.append(f"edge rel {e.get('rel')!r} not allowed")
    return errs


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m engram add <brain-dir> <stage.json>", file=sys.stderr)
        return 2
    brain = require_brain(argv[0])
    if brain is None:
        return 2
    files = argv[1:]
    if not files:
        print("usage: python -m engram add <brain-dir> <stage.json> [<stage2.json> ...]",
              file=sys.stderr)
        return 2

    existing = {a["id"] for a in brain.atoms()}
    load_err = val_err = False
    for path in files:
        batch, err = _load_stage(path)
        if err:
            print(f"error: {err}", file=sys.stderr)
            load_err = True
            continue
        errs = validate(batch, existing)
        if errs:
            print(f"ABORTED {path}, nothing written:")
            for e in errs[:25]:
                print("  -", e)
            val_err = True
            continue
        append_jsonl(brain.atoms_path, batch.get("atoms", []))
        append_jsonl(brain.edges_path, batch.get("edges", []))
        existing |= {a["id"] for a in batch["atoms"]}  # later files see these ids
        srcs = sorted({s for a in batch["atoms"] for s in a["sources"]})
        print(f"added {len(batch['atoms'])} atoms + {len(batch.get('edges', []))} edges "
              f"(sources: {', '.join(srcs)})")
    # input/load problems are usage errors (2); validation rejections are operation failures (1)
    return 2 if load_err else (1 if val_err else 0)


def preview(argv: list[str]) -> int:
    """Validate stage files and project per-source density against the gate, without writing."""
    brain = require_brain(argv[0] if argv else ".")
    if brain is None:
        return 2
    files = argv[1:]
    if not files:
        print("usage: python -m engram preview <brain-dir> <stage.json> [...]", file=sys.stderr)
        return 2

    words = brain.transcript_words()
    existing_per_src = collections.Counter()
    for a in brain.atoms():
        for s in a.get("sources", []):
            existing_per_src[s] += 1
    existing_ids = {a["id"] for a in brain.atoms()}

    rc = 0
    add_per_src = collections.Counter()
    for path in files:
        batch, err = _load_stage(path)
        if err:
            print(f"error: {err}", file=sys.stderr)
            rc = 1
            continue
        errs = validate(batch, existing_ids)
        tag = "OK" if not errs else f"{len(errs)} ERROR(S)"
        print(f"\n{path}: {len(batch.get('atoms', []))} atoms, "
              f"{len(batch.get('edges', []))} edges  [{tag}]")
        for e in errs[:10]:
            print("  -", e)
        if errs:
            rc = 1
        existing_ids |= {a.get("id") for a in batch.get("atoms", [])}
        for a in batch.get("atoms", []):
            for s in a.get("sources", []):
                add_per_src[s] += 1

    print(f"\n{'WORDS':>6}{'ATOMS':>6}{'w/atom':>8}  PROJECTED DENSITY")
    for src in sorted(add_per_src, key=lambda s: -words.get(s, 0)):
        n = existing_per_src[src] + add_per_src[src]
        w = words.get(src, 0)
        wpa = w / n if n else 999
        gate = GATE_LONGFORM if w >= LONGFORM else GATE_DEFAULT
        flag = "FLAG" if wpa > gate else "ok"
        print(f"{w:>6}{n:>6}{wpa:>8.0f}  [{flag}] {src} (gate <= {gate})")
    print("\n(preview only — nothing written. Run `add` when the projection looks good.)")
    return rc


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
