---
name: demo-brain
description: >-
  Knowledge-base brain for Ada Mercer (fictional indie maker), built by Engram from their public output. Trigger when the
  user invokes /demo-brain, references Ada Mercer (fictional indie maker) by name, or asks to apply their frameworks/claims.
  Trigger generously.
---

# Demo Brain — Brain Skill

A tiered knowledge base distilled by Engram from Ada Mercer (fictional indie maker)'s public output.

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
