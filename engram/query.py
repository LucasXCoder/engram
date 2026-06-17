"""Query and summarize a built brain from the command line.

  python -m engram query <brain> [terms...] [--topic T] [--type TY] [--tag TG]
                                 [--confidence C] [--source S] [--edges] [--json] [--limit N]
  python -m engram stats <brain>

`query` filters atoms by free-text terms (matched against text + verbatim) AND any of the
structured flags, then prints each hit with its source link — so the payoff of all that mining
is reachable without hand-grepping atoms.jsonl. `stats` prints a quick profile of the brain.
"""
from __future__ import annotations

import collections
import json
import re
import sys

from .core import require_brain

REL_ARROW = "->"


def _flag(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 >= len(argv):
            raise ValueError(f"{name} requires a value")
        return argv[i + 1], argv[:i] + argv[i + 2:]
    return default, argv


def _source_url(brain, sid):
    for item in brain.manifest().get("items", []):
        if item.get("id") == sid and item.get("url"):
            return item["url"]
    return f"https://youtu.be/{sid}" if re.fullmatch(r"[A-Za-z0-9_-]{11}", sid or "") else sid


def query(argv: list[str]) -> int:
    want_json = "--json" in argv
    want_edges = "--edges" in argv
    argv = [a for a in argv if a not in ("--json", "--edges")]
    try:
        topic, argv = _flag(argv, "--topic")
        typ, argv = _flag(argv, "--type")
        tag, argv = _flag(argv, "--tag")
        conf, argv = _flag(argv, "--confidence")
        source, argv = _flag(argv, "--source")
        limit_s, argv = _flag(argv, "--limit", "50")
        limit = int(limit_s)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    pos = [a for a in argv if not a.startswith("--")]
    brain = require_brain(pos[0] if pos else ".")
    if brain is None:
        return 2
    terms = [t.lower() for t in pos[1:]]

    atoms = brain.atoms()
    edges = brain.edges()
    out = []
    for a in atoms:
        hay = (a.get("text", "") + " " + a.get("verbatim", "")).lower()
        if terms and not all(t in hay for t in terms):
            continue
        if topic and a.get("topic") != topic:
            continue
        if typ and a.get("type") != typ:
            continue
        if conf and a.get("confidence") != conf:
            continue
        if tag and tag not in (a.get("tags") or []):
            continue
        if source and source not in a.get("sources", []):
            continue
        out.append(a)

    if want_json:
        print(json.dumps(out[:limit], ensure_ascii=False, indent=2))
        return 0

    print(f"\n{len(out)} match(es)" + (f", showing {limit}" if len(out) > limit else "") + ":\n")
    nbrs = collections.defaultdict(list)
    if want_edges:
        byid = {a["id"]: a for a in atoms}
        for e in edges:
            if e["from"] in byid and e["to"] in byid:
                nbrs[e["from"]].append((e["rel"], REL_ARROW, byid[e["to"]]))
                nbrs[e["to"]].append((e["rel"], "<-", byid[e["from"]]))
    for a in out[:limit]:
        attr = "" if a.get("attribution", "creator") == "creator" else f" ({a['attribution']})"
        src = a.get("sources", [""])[0]
        print(f"  [{a['id']}] {a.get('type')}/{a.get('topic')} [{a.get('confidence')}]{attr}")
        print(f"      {a.get('text')}")
        if a.get("verbatim"):
            print(f"      “{a['verbatim']}”")
        print(f"      {_source_url(brain, src)}")
        if want_edges and nbrs.get(a["id"]):
            for rel, arrow, other in nbrs[a["id"]][:8]:
                print(f"        {arrow} {rel}: {other.get('text', '')[:70]}")
        print()
    return 0


def stats(argv: list[str]) -> int:
    brain = require_brain(argv[0] if argv and not argv[0].startswith("--") else ".")
    if brain is None:
        return 2
    atoms = brain.atoms()
    edges = brain.edges()
    byid = {a["id"]: a for a in atoms}
    edges = [e for e in edges if e["from"] in byid and e["to"] in byid]

    deg = collections.Counter()
    for e in edges:
        deg[e["from"]] += 1
        deg[e["to"]] += 1
    touched = set(deg)

    def dist(key):
        return dict(collections.Counter(a.get(key) for a in atoms).most_common())

    print(f"\nBRAIN: {brain.name}  ({brain.root})")
    man = brain.manifest()
    if man.get("creator"):
        print(f"creator: {man['creator']}")
    print(f"\natoms: {len(atoms)}   edges: {len(edges)}   "
          f"connectivity: {len(touched)}/{len(atoms)} linked")
    print(f"sources with atoms: {len({s for a in atoms for s in a.get('sources', [])})}"
          f" / {len(man.get('items', []))} in manifest")
    print("\nby topic:     ", dist("topic"))
    print("by type:      ", dist("type"))
    print("by confidence:", dist("confidence"))
    attrs = dict(collections.Counter(a.get("attribution", "creator") for a in atoms))
    print("by attribution:", attrs)
    print("by edge rel:  ", dict(collections.Counter(e["rel"] for e in edges).most_common()))
    if deg:
        print("\nmost connected atoms:")
        for aid, d in deg.most_common(5):
            print(f"  ({d}) [{aid}] {byid[aid].get('text', '')[:72]}")
    return 0
