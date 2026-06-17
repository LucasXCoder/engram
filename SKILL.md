---
name: engram
description: >-
  Factory skill that builds callable knowledge-base "brain" skills from a creator's entire public
  channel plus optional documents. Trigger whenever the user invokes /engram, asks to "build a
  brain", "make a knowledge base", ingest a YouTube channel / IG / TikTok profile, or add the most
  recent videos to an existing brain. Trigger generously.
---

# ENGRAM — Brain Factory

Engram holds no knowledge itself. Each run builds (or updates) **one** callable "brain" skill
distilled from a creator's entire public output. One brain per creator. Brains are **tiered**:
core distillation → topic deep-files → preserved raw sources → an atom/edge reasoning graph →
an interactive visualization.

**The tooling is shared and self-contained.** Every command is `python -m engram <cmd> <brain-dir>`
(see `python -m engram --help`). A *brain is just a data directory* the tooling operates on — you
never re-author build scripts per brain. Install once: `pip install -r requirements.txt`.

```
python -m engram new <dir> --creator NAME --channel URL   # scaffold an empty brain
python -m engram fetch <channel-url> <dir>                # enumerate + fetch transcripts (incremental)
python -m engram add <dir> <stage.json>                   # append a staged batch of atoms+edges (guarded)
python -m engram build <dir>                              # integrity + density gate + regenerate graph.html
python -m engram audit <dir>                              # words-per-atom coverage audit
python -m engram polarity <dir> [--strict]                # fidelity audit (the "we love pies" check)
python -m engram topics <dir>                             # regenerate references/topics/*.md
python -m engram check <dir>                              # build + audit + polarity in one pass
```

## Step 1 — ENUMERATE + FETCH the whole channel

`python -m engram fetch <channel-url> <brain-dir>` lists every video AND the `/shorts` tab via
yt-dlp, pulls auto-captions (json3 → text), writes them to `sources/transcripts/<id>.txt`, and
writes `sources/manifest.json`. **It is incremental** — ids already present are skipped — so the
same command is how you "add the most recent videos" later.

- **Process EVERY video that has a fetchable transcript — never subset to a sample.** The point is
  the COMPLETE brain. For a huge channel, work in batches across passes; views/recency is only the
  *order*, never a stopping point. The only videos left out are those with no captions — list them.
- Expect IP rate-limits (HTTP 429) on large channels; they persist for hours. Don't spin retrying.
- A JS runtime (deno/node) + ffmpeg improve yt-dlp extraction. IG/TikTok without login are usually
  blocked — capture what you can, note what was missed, never stall the whole build on one source.

## Step 2 — INGEST EXTRA MATERIAL

Read every provided report / PDF / article / pasted note and fold it into the same brain, copying
the raw file into `sources/` and tagging atoms with its source id.

## Step 3 — DISTILL (EXHAUSTIVE — this is the whole point of a brain)

> ⚠️ **You are cloning the creator's mind into a skill.** Capture EVERYTHING of value — results,
> ideas, things they're building, tools they use, who they criticize, how they work, what they
> believe, recurring phrases — not a tidy set of teachable claims. The #1 failure mode is
> summarizing: a "key points" pass collapses a 5,900-word video into a handful of records and
> throws away ~95% of the person. Mine like you are reconstructing a mind, not reviewing a lecture.

### 3a. Mine window-by-window
Process each transcript in **tiny windows of ~2–4 sentences**. For EACH window, capture every
distinct valuable thing as its own typed **atom** before moving on. Never read the whole transcript
then write a summary.

Atom `type` ∈ `claim · concept · definition · number · result · example · analogy · method ·
caveat · idea · product · opinion · warning · prediction · bio · resource · style`. If something is
valuable and fits none cleanly, use the closest type — never drop it because it isn't a "claim".

### 3b. One atom per assertion
- An atom is a **single irreducible fact** you could cite on its own. Split compound sentences.
- **Density target ≈ 1 atom per ~18–25 words** of substantive teaching. A 2,000-word video yields
  **~80–110 atoms, not ~15**. The bar is EXHAUSTION — but quality gates quantity: never split one
  idea into hollow fragments to hit a number. When two fragments are really one idea, keep them as
  one atom and join related atoms with an *edge* (3d).
- Pure filler (greetings, "smash like", bare self-promo) is the only thing you skip.

### 3c. Tag, cite, ANCHOR — and never invert the creator (the fidelity rule)
- `confidence`: `CORE` (foundational, repeated) / `STATED` (said once or twice) / `INFERRED` (your
  synthesis — use sparingly and honestly).
- **`sources[]`** on every atom. Preserve ALL numbers/thresholds/conditions exactly.
- **`attribution`** — WHO asserts this: `creator` (default, the creator's own voice) · `quoted`
  (a claim the creator is reporting, quoting, or **debunking** — NOT their belief) · `hypothetical`
  (a strawman / "some people say" / sarcasm).
- **The "we love pies" guardrail.** When a creator says *"everyone thinks X, but that's wrong"*,
  the atom for X must NOT read as if the creator believes X. Do one of:
  1. write the atom in the creator's actual polarity (*"X is false because…"*), **or**
  2. set `attribution: "quoted"` (or `"hypothetical"`) **and** add a `verbatim` field with the
     exact words, so the stance is unambiguous and anchored to the transcript.
  Negation, sarcasm, and debunks are where meaning silently flips — handle them explicitly.
- **`verbatim`** (the creator's exact words) is **required** on any debunk/quoted/contested atom and
  encouraged on punchy CORE claims. It is the anchor `python -m engram polarity` checks against.

### 3d. CONNECT atoms into a reasoning graph
Atoms alone are a bag of facts; **edges make it a brain.** After a window's atoms are written, link
them with typed edges `{from, to, rel, note?}`, `rel` ∈ `because · defines · part-of · example-of ·
analogy-for · evidence-for · qualifies · contrast · contradicts · leads-to · enables · depends-on ·
generalizes · uses · method-for · supports · about · enabled-by`. Capture the ARGUMENT: which
number is evidence for which claim, which example illustrates which concept, what contradicts what.
**Most atoms should be touched by ≥1 edge.** Record contradictions with a `contradicts` edge —
never smooth them over.

### 3e. WRITE the batch, then ADD it (guarded)
Write each video's atoms+edges to a stage file `{"atoms": [...], "edges": [...]}` and run
`python -m engram add <brain-dir> stage.json`. It aborts writing anything on any error (id
collisions, bad type/confidence/attribution/rel, unresolved edge endpoints). See
`examples/demo-brain/_stage.json` for the exact shape.

## Step 4 — GATE (mandatory — a build is NOT done until this is green)

```
python -m engram check <brain-dir>
```

runs three gates and exits non-zero while anything is wrong:
1. **build** — integrity (unique ids, edges resolve) + per-source atom-density gate + regenerates
   `graph.html`. A flagged source was under-mined: re-mine it window-by-window until it clears.
2. **audit** — words-per-atom coverage across every transcript.
3. **polarity** — fidelity: flags atoms near a negation/attribution cue that lack a `verbatim`
   anchor or `attribution` tag. Review each; advisory by default, `--strict` to fail.

Then `python -m engram topics <brain-dir>` regenerates the `references/topics/*.md` index from the
atom store (the store is the single source of truth; the markdown is a generated view).

## Step 5 — WRITE THE BRAIN SKILL (tiered layout)

```
<brain>/
├── SKILL.md                  ← trigger + routing (scaffolded by `engram new`; flesh out routing)
├── atoms.jsonl               ← NODES: one typed atom per line {id,type,topic,confidence,sources[],text,verbatim?,attribution?,numbers?,tags?}
├── edges.jsonl               ← typed reasoning graph {from,to,rel,note?}
├── graph.html                ← interactive visualization (generated, never hand-edited)
├── references/
│   ├── knowledge.md          ← CORE distillation (always read first) + a Topic Map table
│   └── topics/*.md           ← deep files, generated index + your narrative above the marker
└── sources/
    ├── manifest.json         ← every item: id, type, title, url, coverage, upload_date
    └── transcripts/<id>.txt  ← raw ground truth (never distilled away)
```

`knowledge.md` carries the core philosophy + a Topic Map routing each question type to a topic file.
The brain's `SKILL.md` instructs Claude to: read knowledge.md first; route via the Topic Map; grep
`atoms.jsonl` and traverse `edges.jsonl`; drop to transcripts for exact wording; **respect
`confidence` and `attribution`** (a `quoted` atom is NOT the creator's belief); honor the limits
(distilled public teaching, current only as of the manifest's fetch date); surface contradictions.

## Step 6 — REGISTER the brain

Add/update the brain's entry in `registry.json` (copy `registry.example.json` on first run): name,
creator, handle, domains, path, trigger, coverage counts, atom/edge counts, built/last_updated. The
registry is the fleet index — "which brain knows about X?".

## Finishing & resuming (multi-pass builds)

A full channel usually can't be mined in one sitting. The state lives in the brain: `manifest.json`
lists all videos; `atoms.jsonl` records which are done; remaining = manifest videos with no atoms.
A re-run resumes automatically (the `add` path skips done videos). **If `check` is not green when a
run ends, do NOT pretend it's finished** — end with: `PARTIAL — N of M videos done. Run /engram
<name> again to continue.` Only when `python -m engram check <brain>` exits 0 is the build DONE.
