"""Ledger labels (owner 2026-10-28): a model the provider refused is blocked, never solved or failed; the owner's
confidence label shows after the verdict."""
import importlib.util
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AUDIT))
spec = importlib.util.spec_from_file_location("audit_results", AUDIT / "audit_results.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)
markers = ar.markers


def test_verdicts():
    v = ar.task_verdict
    assert v({"deepseek": "failed", "mimo": "failed"}) == "**BREAKER candidate**"
    assert v({"deepseek": "failed", "mimo": "failed"}, confidence="thin") == "**BREAKER candidate** (thin)"
    assert v({"deepseek": "failed", "mimo": "blocked"}, ["mimo"]) == "rejected (DeepSeek-only; MiMo blocked)"
    assert v({"deepseek": "solved", "mimo": "blocked"}, ["mimo"]) == "rejected (DeepSeek solved; MiMo blocked)"
    assert v({"deepseek": "open", "mimo": "blocked"}, ["mimo"]) == "rejected (DeepSeek open; MiMo blocked)"
    assert v({"deepseek": "blocked", "mimo": "blocked"}, ["deepseek", "mimo"]) == "rejected (both blocked)"
    assert v({"deepseek": "solved", "mimo": "failed"}) == "rejected (DeepSeek solved)"
    assert ar.BLOCKED_CELL == "**blocked** (provider safety filter)"


def test_blocked_reader(tmp_path):
    b = tmp_path / "git-js-s3"
    b.mkdir()
    assert markers.blocked(b, "mimo") is None
    (b / "hold_mimo").write_text("Paused 2026-10-28: the repo ships its own .claude/settings.json.\n")
    assert markers.blocked(b, "mimo") is None                     # a pause is not a block
    (b / "hold_mimo").write_text("MiMo blocked by the provider security classifier (owner rule 2026-10-28).\n")
    assert markers.blocked(b, "mimo") == "hold_mimo"
    (b / "hold_mimo").unlink()
    (b / "MIMO-BLOCKED.md").write_text("# MiMo verdict: blocked\n")
    assert markers.blocked(b, "mimo") == "MIMO-BLOCKED.md" and markers.blocked(b, "deepseek") is None


def test_confidence_reader(tmp_path):
    b = tmp_path / "katex-s2"
    b.mkdir()
    assert markers.confidence(b) is None
    (b / "HUMAN-DECISION.md").write_text("DECISION: KEEP\nDATE: 2026-10-28\n\n## Client audit PO-3\n\n"
                                         "CLIENT-AUDIT: KEEP, CONFIDENCE: THIN\n")
    assert markers.confidence(b) == "thin"
    (b / "HUMAN-DECISION.md").write_text("DECISION: KEEP\nCONFIDENCE: THIN\nlater:\nCONFIDENCE: medium\n")
    assert markers.confidence(b) == "medium"                      # the last one wins
