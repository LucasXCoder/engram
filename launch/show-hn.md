# Show HN

> Post Tue–Thu, ~8–10am ET. Submit the **GitHub repo URL** as the link. Then immediately post the
> "first comment" below as a top-level comment from your own account.

## Title (≤ 80 chars)
```
Show HN: Engram – turn a creator's YouTube channel into a queryable knowledge graph
```

## URL
```
https://github.com/LucasXCoder/engram
```

## First comment (paste right after submitting)

Hi HN — I built Engram, a tool that distills a creator's entire YouTube channel into a queryable "brain": a graph of typed **atoms** (single ideas) connected by typed **edges** (the reasoning between them), plus a distilled wiki and an interactive visualization. You can then ask it questions and get answers in that creator's frameworks, each cited back to the exact source video.

Two things I cared about:

1. **Fidelity, not summary.** Most "summarize this channel" tools collapse hours of content into a paragraph and lose ~95% of the person. Engram mines transcripts window-by-window into thousands of atoms at a calibrated density, so the depth survives.

2. **It won't put words in their mouth.** The #1 failure mode of any atomization system is storing a claim the creator *debunks* as if they believe it. Every atom carries an `attribution` field (creator / quoted / hypothetical) + a verbatim anchor, and there's a "polarity audit" that flags un-anchored claims sitting next to negation/attribution cues. A live build on a real channel cut its false positives from 102 → 0.

It's a Claude Code skill + a small Python package (stdlib + yt-dlp only). The graph is a single self-contained HTML file — no build step, no deps, no network.

Live, in your browser:
- Interactive graph of a real 141-atom channel: https://lucasxcoder.github.io/engram/examples/codeaesthetic/graph.html
- A short trailer: https://lucasxcoder.github.io/engram/docs/trailer.html#clean

Honest limitations: the distillation is done by an LLM (it's a Claude skill), so it's not a one-click app yet; it's only as current as the last fetch; and a brain is distilled public teaching, not validated fact. Building a brain at full depth takes multiple passes for a big channel.

Would love feedback on the atom/edge schema and the polarity guardrail — and what creator you'd point it at.
