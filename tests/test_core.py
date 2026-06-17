from engram import fetch
from engram.core import read_jsonl, topic_colors


def test_topic_colors_deterministic():
    a = topic_colors(["b", "a", "c"])
    b = topic_colors(["c", "a", "b"])
    assert a == b  # order-independent
    assert len(set(a.values())) == 3


def test_read_jsonl_tolerates_bom_and_blanks(tmp_path):
    p = tmp_path / "x.jsonl"
    p.write_bytes('﻿{"id": 1}\n\n{"id": 2}\n'.encode("utf-8"))
    rows = read_jsonl(str(p))
    assert [r["id"] for r in rows] == [1, 2]


def test_read_jsonl_missing_file_is_empty(tmp_path):
    assert read_jsonl(str(tmp_path / "nope.jsonl")) == []


def test_json3_parsing(tmp_path):
    j = tmp_path / "v.en.json3"
    j.write_text('{"events":[{"segs":[{"utf8":"hello "},{"utf8":"world"}]},'
                 '{"segs":[{"utf8":"\\n"}]}]}', encoding="utf-8")
    assert fetch._json3_to_text(str(j)) == "hello world"
