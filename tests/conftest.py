import json
import os
import sys

import pytest

# make the repo root importable so `import engram` works from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engram.core import Brain  # noqa: E402


@pytest.fixture
def brain(tmp_path):
    """A tiny, valid brain on disk: 1 transcript, 2 atoms, 1 edge."""
    b = Brain(str(tmp_path / "t"))
    b.ensure_dirs()
    with open(os.path.join(b.transcripts_dir, "v1.txt"), "w", encoding="utf-8") as f:
        f.write("alpha decay means an edge stops working once it is public " * 4)
    atoms = [
        {"id": "a1", "type": "claim", "topic": "x", "confidence": "CORE",
         "sources": ["v1"], "text": "An edge stops working once it is public."},
        {"id": "a2", "type": "definition", "topic": "x", "confidence": "STATED",
         "sources": ["v1"], "text": "Alpha decay is the loss of predictive power over time."},
    ]
    with open(b.atoms_path, "w", encoding="utf-8") as f:
        for a in atoms:
            f.write(json.dumps(a) + "\n")
    with open(b.edges_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"from": "a2", "to": "a1", "rel": "defines"}) + "\n")
    return b
