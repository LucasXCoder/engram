"""Engram core — shared schema, the Brain abstraction, and small utilities.

Every command operates on a *brain directory*: a self-contained folder that holds the
knowledge graph (`atoms.jsonl` + `edges.jsonl`), the distilled wiki (`references/`), the
preserved ground truth (`sources/`), and a generated `graph.html`. The Python tooling lives
here once and is shared by every brain — a brain is just data.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

# --- force UTF-8 stdout (Windows consoles default to cp1252 and crash on non-ASCII) -------
try:  # pragma: no cover - platform dependent
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass


# --- schema ------------------------------------------------------------------------------
#: An atom's `type` — capture EVERYTHING of value, not only "claims".
ATOM_TYPES = {
    "claim", "concept", "definition", "number", "result", "example", "analogy",
    "method", "caveat", "idea", "product", "opinion", "warning", "prediction",
    "bio", "resource", "style",
}

#: Typed reasoning links between atoms. The edges are what make it a brain, not a list.
EDGE_RELS = {
    "because", "defines", "part-of", "example-of", "analogy-for", "evidence-for",
    "qualifies", "contrast", "contradicts", "leads-to", "enables", "depends-on",
    "generalizes", "uses", "method-for", "supports", "about", "enabled-by",
}

#: Confidence in the distillation, strongest → weakest.
CONFIDENCE = {"CORE", "STATED", "INFERRED"}

#: WHO asserts an atom. This is the fidelity guardrail: a claim the creator *debunks* must
#: never be stored as if the creator believes it. Default is the creator's own voice.
ATTRIBUTION = {"creator", "quoted", "hypothetical"}

REQUIRED_ATOM_KEYS = {"id", "type", "topic", "confidence", "sources", "text"}

#: A stable, colour-blind-friendly palette. Topics are assigned colours deterministically
#: (by sorted first-appearance) so any brain gets a sensible legend with zero configuration.
PALETTE = [
    "#4da3ff", "#3ddc97", "#ff9f43", "#c792ea", "#ffd23f",
    "#ff5d5d", "#7fdbff", "#f78fb3", "#9ccc65", "#ff8a65",
    "#64b5f6", "#ba68c8", "#4db6ac", "#ffb74d", "#e57373",
]


def topic_colors(topics) -> dict:
    """Deterministically map topic names → palette colours."""
    return {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(sorted(set(topics)))}


# --- jsonl io ----------------------------------------------------------------------------
def read_jsonl(path: str) -> list:
    """Read a .jsonl file → list of dicts. Tolerates a UTF-8 BOM and blank lines."""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise ValueError(f"{path}:{n}: invalid JSON — {exc}") from exc
    return out


def append_jsonl(path: str, records) -> None:
    """Append records as one compact JSON object per line (no BOM, trailing newline)."""
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_jsonl(path: str, records) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# --- the Brain ---------------------------------------------------------------------------
@dataclass
class Brain:
    """A brain directory and the canonical paths inside it."""

    root: str

    def __post_init__(self):
        self.root = os.path.abspath(self.root)

    # files
    @property
    def atoms_path(self) -> str:
        return os.path.join(self.root, "atoms.jsonl")

    @property
    def edges_path(self) -> str:
        return os.path.join(self.root, "edges.jsonl")

    @property
    def graph_path(self) -> str:
        return os.path.join(self.root, "graph.html")

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.root, "sources", "manifest.json")

    @property
    def transcripts_dir(self) -> str:
        return os.path.join(self.root, "sources", "transcripts")

    @property
    def topics_dir(self) -> str:
        return os.path.join(self.root, "references", "topics")

    @property
    def name(self) -> str:
        return os.path.basename(self.root)

    # loaders
    def atoms(self) -> list:
        return read_jsonl(self.atoms_path)

    def edges(self) -> list:
        return read_jsonl(self.edges_path)

    def manifest(self) -> dict:
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, encoding="utf-8-sig") as f:
                return json.load(f)
        return {}

    def transcript_words(self) -> dict:
        """Map source-id → word count, for density gating."""
        words = {}
        if os.path.isdir(self.transcripts_dir):
            for fn in os.listdir(self.transcripts_dir):
                if fn.endswith(".txt"):
                    p = os.path.join(self.transcripts_dir, fn)
                    with open(p, encoding="utf-8", errors="ignore") as f:
                        words[fn[:-4]] = len(f.read().split())
        return words

    def ensure_dirs(self) -> None:
        for d in (self.transcripts_dir, self.topics_dir):
            os.makedirs(d, exist_ok=True)


def resolve_brain(arg: str | None) -> Brain:
    """Resolve a CLI path argument to a Brain (defaults to the current directory)."""
    return Brain(arg or ".")


def require_brain(arg: str | None) -> Brain | None:
    """Resolve a brain dir for a command, or print an error and return None if it is missing."""
    brain = Brain(arg or ".")
    if not os.path.isdir(brain.root):
        print(f"error: no such brain directory: {brain.root}", file=sys.stderr)
        return None
    return brain
