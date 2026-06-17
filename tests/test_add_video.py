import json

from engram import add_video


def _stage(tmp_path, batch):
    p = tmp_path / "stage.json"
    p.write_text(json.dumps(batch), encoding="utf-8")
    return str(p)


def test_valid_batch_appends(brain, tmp_path):
    batch = {
        "atoms": [{"id": "n1", "type": "claim", "topic": "x", "confidence": "STATED",
                   "sources": ["v1"], "text": "new fact"}],
        "edges": [{"from": "n1", "to": "a1", "rel": "supports"}],
    }
    rc = add_video.main([brain.root, _stage(tmp_path, batch)])
    assert rc == 0
    assert len(brain.atoms()) == 3
    assert len(brain.edges()) == 2


def test_id_collision_aborts(brain, tmp_path):
    batch = {"atoms": [{"id": "a1", "type": "claim", "topic": "x", "confidence": "STATED",
                        "sources": ["v1"], "text": "dup"}], "edges": []}
    rc = add_video.main([brain.root, _stage(tmp_path, batch)])
    assert rc == 1
    assert len(brain.atoms()) == 2  # nothing written


def test_bad_type_rejected(brain, tmp_path):
    batch = {"atoms": [{"id": "z", "type": "nonsense", "topic": "x", "confidence": "STATED",
                        "sources": ["v1"], "text": "t"}], "edges": []}
    assert add_video.main([brain.root, _stage(tmp_path, batch)]) == 1


def test_bad_attribution_rejected(brain, tmp_path):
    batch = {"atoms": [{"id": "z", "type": "claim", "topic": "x", "confidence": "STATED",
                        "attribution": "fabricated", "sources": ["v1"], "text": "t"}], "edges": []}
    assert add_video.main([brain.root, _stage(tmp_path, batch)]) == 1


def test_unresolved_edge_rejected(brain, tmp_path):
    batch = {"atoms": [{"id": "z", "type": "claim", "topic": "x", "confidence": "STATED",
                        "sources": ["v1"], "text": "t"}],
             "edges": [{"from": "z", "to": "ghost", "rel": "supports"}]}
    assert add_video.main([brain.root, _stage(tmp_path, batch)]) == 1


def test_bad_rel_rejected(brain, tmp_path):
    batch = {"atoms": [{"id": "z", "type": "claim", "topic": "x", "confidence": "STATED",
                        "sources": ["v1"], "text": "t"}],
             "edges": [{"from": "z", "to": "a1", "rel": "vibes-with"}]}
    assert add_video.main([brain.root, _stage(tmp_path, batch)]) == 1
