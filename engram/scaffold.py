"""Scaffold a new, empty brain directory.

Usage:  python -m engram new <brain-dir> [--creator "Name"] [--channel URL]

Creates the canonical layout (atoms.jsonl, edges.jsonl, references/, sources/transcripts/) and a
starter SKILL.md so the brain registers as a callable Claude Code skill. Fetch + distill fill it.
"""
from __future__ import annotations

import json
import os
import sys

from .core import Brain

SKILL_TEMPLATE = """---
name: {name}
description: >-
  Knowledge-base brain for {creator}, built by Engram from their public output. Trigger when the
  user invokes /{name}, references {creator} by name, or asks to apply their frameworks/claims.
  Trigger generously.
---

# {title} — Brain Skill

A tiered knowledge base distilled by Engram from {creator}'s public output.

## When invoked
1. **Read `references/knowledge.md` first** — core distillation + the Topic Map.
2. **Route via the Topic Map** to the matching `references/topics/*.md` files (usually one or two).
3. **Grep `atoms.jsonl`** for targeted lookups by `type`/`topic`/`confidence`/`tags`, and traverse
   `edges.jsonl` to follow the creator's reasoning, not just recall facts.
4. **Drop to `sources/transcripts/<id>.txt`** (indexed in `sources/manifest.json`) for exact
   wording or disputed claims.
5. **Respect `confidence`** (CORE > STATED > INFERRED) and **`attribution`** — an atom tagged
   `quoted`/`hypothetical` is something the creator reports or debunks, NOT their own position.
6. **Honor the limits:** distilled public teaching, current only as of the manifest's fetch date.
"""


def main(argv: list[str]) -> int:
    creator = channel = None
    args = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--creator", "--channel"):
            if i + 1 >= len(argv):
                print(f"error: {argv[i]} requires a value", file=sys.stderr)
                return 2
            if argv[i] == "--creator":
                creator = argv[i + 1]
            else:
                channel = argv[i + 1]
            i += 2
        else:
            args.append(argv[i]); i += 1
    if not args:
        print("usage: python -m engram new <brain-dir> [--creator NAME] [--channel URL]",
              file=sys.stderr)
        return 2

    brain = Brain(args[0])
    if os.path.exists(brain.atoms_path):
        print(f"refusing to overwrite existing brain at {brain.root}", file=sys.stderr)
        return 1
    brain.ensure_dirs()
    creator = creator or brain.name
    open(brain.atoms_path, "a", encoding="utf-8").close()
    open(brain.edges_path, "a", encoding="utf-8").close()

    skill = SKILL_TEMPLATE.format(name=brain.name, creator=creator,
                                  title=brain.name.replace("-", " ").title())
    with open(os.path.join(brain.root, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill)

    man = {"creator": creator, "channel": channel, "fetched": None,
           "counts": {"total": 0, "transcript": 0, "missed": 0}, "items": []}
    with open(brain.manifest_path, "w", encoding="utf-8") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)

    kn = os.path.join(brain.root, "references", "knowledge.md")
    with open(kn, "w", encoding="utf-8") as f:
        f.write(f"# Knowledge Base: {creator}\n\n**Built by Engram.** "
                f"Run `python -m engram fetch <channel> {brain.root}` then distill.\n\n"
                "## Topic Map\n\n_(populated as topics are mined)_\n")

    print(f"created brain '{brain.name}' at {brain.root}")
    print("  next: python -m engram fetch <channel-url> " + brain.root)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
