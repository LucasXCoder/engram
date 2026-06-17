# Changelog

All notable changes to Engram are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Graph top-left overlap.** The centered search box could overlap the header on narrower
  viewports. Header + search now share one left-anchored flex row that wraps instead of overlapping.

### Changed
- **Richer demo brain.** Added a third source (debugging) with cross-topic edges, so the bundled
  showcase graph spans three connected topic clusters (25 atoms / 26 edges) instead of two.

## [0.1.1] — 2026-06-17

Makes a built brain usable and maintainable straight from the CLI, plus a richer graph. Proven
end-to-end by building a real brain from an unseen channel (3 videos → 141 atoms / 140 edges).

### Added
- **`query`** — search atoms by free text plus `--topic` / `--type` / `--tag` / `--confidence` /
  `--source` filters, with `--edges` to follow an atom's reasoning and `--json` for scripting.
  The payoff of mining is finally reachable without hand-grepping `atoms.jsonl`.
- **`stats`** — profile a brain: counts, distributions by topic/type/confidence/attribution,
  edge-relation breakdown, connectivity, and the most-connected atoms.
- **`serve`** — (re)build `graph.html` and open it in the browser in one command.
- **`preview`** — validate stage files and project per-source density against the gate *without
  writing*, so thin mining is caught before you commit.
- **`register`** / **`which`** — upsert a brain into `registry.json` with auto-computed counts and
  domains (derived from its topics), and answer "which brain knows about X?" across the fleet.
- **Multi-file `add`** — `add <brain> a.json b.json …`; later files see earlier files' ids.
- **Richer visualization** — confidence filter (CORE/STATED/INFERRED), a minimap with a draggable
  viewport, edge-relationship labels on the selected atom, and one-click PNG export.

### Fixed
- **Polarity audit on caption transcripts.** YouTube auto-captions have no punctuation, so the
  sentence-based cue matcher treated a whole transcript as one "sentence" and flagged nearly every
  atom. Switched to a local 14-word window with a stronger overlap threshold — verified on the
  real 3-video build where it cut false positives from 102 to 0 while still catching inversions.

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
