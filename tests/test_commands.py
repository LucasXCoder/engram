"""Tests for the v0.1.1 commands: query, stats, preview, register, which, multi-file add."""
import json
import os

from engram import add_video, query, registry


def _stage(tmp_path, name, batch):
    p = tmp_path / name
    p.write_text(json.dumps(batch), encoding="utf-8")
    return str(p)


def test_query_filters_by_text_and_type(brain, capsys):
    rc = query.query([brain.root, "alpha"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "a2" in out and "Alpha decay" in out

    query.query([brain.root, "--type", "claim"])
    assert "a1" in capsys.readouterr().out


def test_query_json_output(brain, capsys):
    query.query([brain.root, "--json", "--type", "definition"])
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 1 and data[0]["id"] == "a2"


def test_stats_runs(brain, capsys):
    assert query.stats([brain.root]) == 0
    out = capsys.readouterr().out
    assert "atoms: 2" in out and "connectivity" in out


def test_multifile_add(brain, tmp_path):
    b1 = {"atoms": [{"id": "m1", "type": "claim", "topic": "x", "confidence": "STATED",
                     "sources": ["v1"], "text": "one"}], "edges": []}
    b2 = {"atoms": [{"id": "m2", "type": "claim", "topic": "x", "confidence": "STATED",
                     "sources": ["v1"], "text": "two"}],
          "edges": [{"from": "m2", "to": "m1", "rel": "supports"}]}  # m1 from earlier file
    rc = add_video.main([brain.root, _stage(tmp_path, "a.json", b1), _stage(tmp_path, "b.json", b2)])
    assert rc == 0
    assert len(brain.atoms()) == 4


def test_preview_writes_nothing(brain, tmp_path, capsys):
    before = len(brain.atoms())
    batch = {"atoms": [{"id": "p1", "type": "claim", "topic": "x", "confidence": "STATED",
                        "sources": ["v1"], "text": "new"}], "edges": []}
    rc = add_video.preview([brain.root, _stage(tmp_path, "p.json", batch)])
    assert rc == 0
    assert len(brain.atoms()) == before  # nothing written
    assert "PROJECTED DENSITY" in capsys.readouterr().out


def test_register_and_which(brain, tmp_path, capsys):
    reg = str(tmp_path / "registry.json")
    assert registry.register([brain.root, "--registry", reg]) == 0
    data = json.loads(open(reg, encoding="utf-8").read())
    assert data["brains"][0]["name"] == os.path.basename(brain.root)
    assert data["brains"][0]["atoms_count"] == 2

    capsys.readouterr()
    assert registry.which(["--registry", reg, "x"]) == 0  # topic 'x' is an auto-derived domain
    assert registry.which(["--registry", reg, "nonexistent-zzz"]) == 1


def test_register_preserves_built_date(brain, tmp_path):
    reg = str(tmp_path / "r.json")
    registry.register([brain.root, "--registry", reg])
    first = json.loads(open(reg, encoding="utf-8").read())["brains"][0]["built"]
    registry.register([brain.root, "--registry", reg])
    data = json.loads(open(reg, encoding="utf-8").read())
    assert len(data["brains"]) == 1  # upsert, not duplicate
    assert data["brains"][0]["built"] == first
