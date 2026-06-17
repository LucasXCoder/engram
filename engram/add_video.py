"""Append one source's atoms + edges to a brain's graph, atomically and guarded.

Usage:  python -m engram add <brain-dir> <stage.json>

A stage file is `{"atoms": [...], "edges": [...]}`. Guards (abort writing *anything* on any
error): required keys present, valid `type`/`confidence`/`attribution`, no id collisions
(within the batch or against the existing store), every edge endpoint resolves, valid `rel`.
"""
from __future__ import annotations

import json
import sys

from .core import (
    ATOM_TYPES, ATTRIBUTION, CONFIDENCE, EDGE_RELS, REQUIRED_ATOM_KEYS,
    append_jsonl, require_brain,
)


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
    try:
        with open(argv[1], encoding="utf-8") as f:
            batch = json.load(f)
    except FileNotFoundError:
        print(f"error: no such stage file: {argv[1]}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: {argv[1]} is not valid JSON — {exc}", file=sys.stderr)
        return 2
    if not isinstance(batch, dict) or "atoms" not in batch:
        print(f"error: {argv[1]} must be an object with an \"atoms\" key", file=sys.stderr)
        return 2

    existing = {a["id"] for a in brain.atoms()}
    errs = validate(batch, existing)
    if errs:
        print("ABORTED, nothing written:")
        for e in errs[:25]:
            print("  -", e)
        return 1

    append_jsonl(brain.atoms_path, batch.get("atoms", []))
    append_jsonl(brain.edges_path, batch.get("edges", []))
    srcs = sorted({s for a in batch["atoms"] for s in a["sources"]})
    print(f"added {len(batch['atoms'])} atoms + {len(batch.get('edges', []))} edges "
          f"(sources: {', '.join(srcs)})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
