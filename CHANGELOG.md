# Changelog

All notable changes to Engram are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-17

First public release.

### Added
- **Self-contained tooling.** A shared `engram` package operates on any *brain directory* via a
  single CLI — `python -m engram <command> <brain>` — with commands `new`, `fetch`, `add`,
  `build`, `audit`, `polarity`, `topics`, `graph`, and `check`. A brain is just data; build logic
  lives in the package, never per-brain.
- **Knowledge-graph store.** Typed **atoms** (`atoms.jsonl`) connected by typed **edges**
  (`edges.jsonl`) into a reasoning graph, with a guarded `add` that aborts on id collisions, bad
  types/relations, or unresolved edge endpoints.
- **Fidelity guardrail.** Every atom carries an `attribution` field (`creator` / `quoted` /
  `hypothetical`) and an optional `verbatim` anchor. A `polarity` audit locates each atom in its
  source transcript and flags un-anchored claims sitting next to negation/attribution cues —
  defending against storing a debunked belief as if the creator endorsed it.
- **Quality gates.** `build` enforces integrity + a per-source atom-density gate; `audit` reports
  words-per-atom coverage; `check` runs build + audit + polarity in one pass (non-zero on failure).
- **Interactive visualization.** A self-contained `graph.html` with a live force simulation,
  search, click-to-isolate topic legend, a node detail panel with clickable neighbors, loading and
  empty states, full keyboard/touch support, and `prefers-reduced-motion` handling.
- **Transcript fetcher.** `fetch` enumerates a YouTube channel's videos *and* shorts via `yt-dlp`,
  pulls captions, and writes an incremental `manifest.json` — re-running adds only new uploads.
- **Tiered brain layout.** Distilled wiki (`references/knowledge.md` + generated `topics/*.md`),
  preserved raw transcripts under `sources/`, and a fleet `registry`.
- **Project scaffolding.** `pyproject.toml` (pip-installable `engram` command), 27 tests, GitHub
  Actions CI (Python 3.10 + 3.12), a bundled fictional demo brain that passes every gate, MIT
  license, and contributor docs.

[0.1.0]: https://github.com/LucasXCoder/engram/releases/tag/v0.1.0
