# Showcase brain — CodeAesthetic (a real channel)

A real Engram brain built from a public YouTube channel
([**CodeAesthetic**](https://www.youtube.com/@CodeAesthetic)) — **141 atoms / 140 edges** across
five topics (functional programming, dependency injection, performance, philosophy, craft). It's
here so you can see what a brain from an actual channel looks like, beyond the tiny fictional
[`demo-brain`](../demo-brain).

**▶ [Open the interactive graph](https://lucasxcoder.github.io/engram/examples/codeaesthetic/graph.html)**
— search it, filter by confidence, click a node to read the atom and jump to the exact source video.

### What's included (and what isn't)
- **Included:** the distilled, **cited** knowledge — `atoms.jsonl`, `edges.jsonl`, the `references/`
  wiki, the generated `graph.html`, and `sources/manifest.json` (every atom links back to the
  source video).
- **Not included:** the raw video transcripts. The atoms are a transformative, cited distillation
  (like detailed notes), and every claim links back to the creator's original video — we don't
  republish their verbatim transcripts here. Build your own copy with
  `python -m engram fetch https://www.youtube.com/@CodeAesthetic <dir>`.

This is distilled public teaching for demonstration/education, with attribution — **not** a
replacement for watching the creator's excellent videos. Go subscribe to them.
