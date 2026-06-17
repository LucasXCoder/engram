import json
import os

from engram import build_brain, build_graph, build_topic_index, coverage_audit, polarity_audit


def test_build_passes_clean_brain(brain):
    assert build_brain.main([brain.root]) == 0
    assert os.path.exists(brain.graph_path)


def test_build_flags_underextracted(brain):
    # bloat the transcript so words/atom blows past the gate
    with open(os.path.join(brain.transcripts_dir, "v1.txt"), "w", encoding="utf-8") as f:
        f.write("word " * 5000)
    assert build_brain.main([brain.root]) == 1


def test_build_flags_integrity_error(brain):
    with open(brain.edges_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"from": "a1", "to": "ghost", "rel": "supports"}) + "\n")
    assert build_brain.main([brain.root]) == 1


def test_coverage_audit_clean(brain):
    assert coverage_audit.main([brain.root]) == 0


def test_graph_html_contains_data(brain):
    build_graph.build(brain)
    html = open(brain.graph_path, encoding="utf-8").read()
    assert "__DATA__" not in html and "__TITLE__" not in html
    assert '"atoms": 2' in html or '"atoms":2' in html
    assert "An edge stops working" in html


def test_topic_index_generated(brain):
    assert build_topic_index.main([brain.root]) == 0
    f = os.path.join(brain.topics_dir, "x.md")
    assert os.path.exists(f)
    assert "AUTO-INDEX:START" in open(f, encoding="utf-8").read()


def test_polarity_catches_inversion(brain):
    # transcript says the claim is a myth; atom asserts it bare as the creator's view
    with open(os.path.join(brain.transcripts_dir, "v2.txt"), "w", encoding="utf-8") as f:
        f.write("There is a myth that indicators are useless for serious traders.")
    with open(brain.atoms_path, "a", encoding="utf-8") as f:
        # bare inversion: stores the debunked belief as the creator's own claim, no anchor
        f.write(json.dumps({"id": "bad", "type": "claim", "topic": "x", "confidence": "STATED",
                            "sources": ["v2"], "text": "Indicators are useless for serious traders."}) + "\n")
    suspects = polarity_audit.audit(brain)
    assert any(s["id"] == "bad" for s in suspects)


def test_polarity_clean_when_attributed(brain):
    with open(os.path.join(brain.transcripts_dir, "v2.txt"), "w", encoding="utf-8") as f:
        f.write("There is a myth that indicators are useless.")
    with open(brain.atoms_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "ok2", "type": "opinion", "topic": "x", "confidence": "STATED",
                            "attribution": "quoted", "sources": ["v2"],
                            "text": "Some people claim indicators are useless.",
                            "verbatim": "indicators are useless"}) + "\n")
    suspects = polarity_audit.audit(brain)
    assert not any(s["id"] == "ok2" for s in suspects)
