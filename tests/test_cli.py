"""CLI robustness — bad arguments must fail cleanly (non-zero), never crash."""
from engram import add_video, build_brain, coverage_audit, fetch, polarity_audit, scaffold
from engram.__main__ import main


def test_missing_brain_dir_is_clean(capsys):
    for fn in (build_brain.main, coverage_audit.main, polarity_audit.main):
        assert fn(["/no/such/brain/here"]) == 2


def test_add_missing_stage_file(brain):
    assert add_video.main([brain.root, "does-not-exist.json"]) == 2


def test_add_invalid_json(brain, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert add_video.main([brain.root, str(bad)]) == 2


def test_add_json_without_atoms_key(brain, tmp_path):
    p = tmp_path / "x.json"
    p.write_text('{"edges": []}', encoding="utf-8")
    assert add_video.main([brain.root, str(p)]) == 2


def test_limit_without_value(brain):
    assert polarity_audit.main([brain.root, "--limit"]) == 2
    assert fetch.main(["https://x", brain.root, "--limit"]) == 2


def test_limit_non_integer(brain):
    assert polarity_audit.main([brain.root, "--limit", "abc"]) == 2


def test_scaffold_flag_without_value(tmp_path):
    assert scaffold.main([str(tmp_path / "b"), "--creator"]) == 2


def test_unknown_command():
    assert main(["frobnicate", "x"]) == 2


def test_help_is_zero():
    assert main([]) == 0
    assert main(["--help"]) == 0
