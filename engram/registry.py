"""Maintain the brain-fleet registry, and answer 'which brain knows about X?'.

  python -m engram register <brain> [--registry registry.json]
  python -m engram which <term...>  [--registry registry.json]

`register` computes a brain's entry (counts, coverage, auto-derived domains from its topics) and
upserts it into the registry, so the bookkeeping the SKILL used to ask for by hand is automatic.
`which` searches the registry by name/creator/handle/domain for cross-brain routing.
"""
from __future__ import annotations

import collections
import datetime as _dt
import json
import os
import sys

from .core import require_brain

DEFAULT_REGISTRY = "registry.json"


def _flag(argv, name, default):
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            raise ValueError(f"{name} requires a value")
        return argv[i + 1], argv[:i] + argv[i + 2:]
    return default, argv


def _load_registry(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    return {"schema": 1,
            "description": "Engram brain fleet registry. One entry per brain built by engram.",
            "updated": None, "brains": []}


def register(argv: list[str]) -> int:
    try:
        reg_path, argv = _flag(argv, "--registry", DEFAULT_REGISTRY)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    pos = [a for a in argv if not a.startswith("--")]
    brain = require_brain(pos[0] if pos else ".")
    if brain is None:
        return 2

    atoms = brain.atoms()
    edges = brain.edges()
    man = brain.manifest()
    topics = collections.Counter(a.get("topic") for a in atoms)
    domains = [t for t, _ in topics.most_common()]

    reg = _load_registry(reg_path)
    brains = reg.setdefault("brains", [])
    entry = next((b for b in brains if b.get("name") == brain.name), None)
    today = _dt.date.today().isoformat()
    new = {
        "name": brain.name,
        "creator": man.get("creator"),
        "handle": (man.get("channel") or "").rstrip("/").rsplit("/", 1)[-1] or None,
        "domains": domains,
        "path": brain.root,
        "trigger": f"/{brain.name}",
        "coverage": man.get("counts", {}),
        "atoms_count": len(atoms),
        "edges_count": len(edges),
        "built": entry.get("built") if entry else today,
        "last_updated": today,
    }
    if entry:
        entry.update(new)
        action = "updated"
    else:
        brains.append(new)
        action = "added"
    reg["updated"] = today
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    print(f"{action} '{brain.name}' in {reg_path} "
          f"({len(atoms)} atoms, {len(edges)} edges, domains: {', '.join(domains) or '—'})")
    return 0


def which(argv: list[str]) -> int:
    try:
        reg_path, argv = _flag(argv, "--registry", DEFAULT_REGISTRY)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    terms = [a.lower() for a in argv if not a.startswith("--")]
    if not terms:
        print("usage: python -m engram which <term...> [--registry path]", file=sys.stderr)
        return 2
    if not os.path.exists(reg_path):
        print(f"error: no registry at {reg_path}; run `python -m engram register <brain>` first",
              file=sys.stderr)
        return 2
    reg = _load_registry(reg_path)

    hits = []
    for b in reg.get("brains", []):
        hay = " ".join(str(b.get(k, "")) for k in ("name", "creator", "handle")).lower()
        hay += " " + " ".join(b.get("domains", [])).lower()
        if all(t in hay for t in terms):
            hits.append(b)
    print(f"\n{len(hits)} brain(s) matching {' '.join(terms)!r}:\n")
    for b in hits:
        print(f"  {b.get('trigger', '/' + b.get('name', '?'))}  — {b.get('creator') or b.get('name')}")
        print(f"      domains: {', '.join(b.get('domains', [])) or '—'}")
        print(f"      {b.get('atoms_count', '?')} atoms · {b.get('path', '')}\n")
    return 0 if hits else 1
