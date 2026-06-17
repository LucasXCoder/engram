# Contributing to Engram

Thanks for your interest! Engram is small and dependency-light on purpose — keep it that way.

## Setup

```bash
pip install -r requirements-dev.txt
pytest -q
```

The whole quality gate for the demo brain is:

```bash
python -m engram check examples/demo-brain
```

## Guidelines

- **Standard library only** for the core tooling (build/graph/audit/topics). `yt-dlp` is the single
  runtime dependency, used only by `fetch`. Don't add others without a strong reason.
- **A brain is data; the package is logic.** New behavior goes in `engram/`, operating on a brain
  directory — never hard-code a specific brain.
- **Add a test** for any new command or guardrail. Tests use a tmp-path brain fixture (see
  `tests/conftest.py`) and must not hit the network.
- **The store is the source of truth.** `graph.html` and `references/topics/*.md` are generated;
  never hand-edit them.
- Run `pytest -q` and `python -m engram check examples/demo-brain` before opening a PR.

## Ideas / good first issues

- A `engram serve` command that opens `graph.html` in the browser.
- Non-YouTube fetchers (podcast RSS, article lists) behind the same manifest shape.
- A cross-brain query in the registry ("which brain knows about X?").
