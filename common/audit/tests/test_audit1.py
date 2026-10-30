"""Unit tests for audit 1's deterministic parts: quote_check.py and route.py."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit1"))
import quote_check  # noqa: E402
import route  # noqa: E402


def make(tmp, files, dossier, facts=None, qc=None):
    d = Path(tmp)
    for name, text in files.items():
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    (d / "DOSSIER.json").write_text(json.dumps(dossier))
    if facts is not None:
        (d / "FACTS.json").write_text(json.dumps(facts))
    if qc is not None:
        (d / "QUOTECHECK-1.json").write_text(json.dumps(qc))
    return d


INSTR = "# Title\n\nEverything that works today keeps\nworking exactly as today.\n\nA refusal is a client error.\n"
PATCH = "--- a/x.py\n+++ b/x.py\n@@ -1,2 +1,3 @@\n def f(x):\n+    if bad(x):\n+        raise ValueError\n"


class QuoteCheck(unittest.TestCase):
    def check(self, quote, line, file="evidence/instruction.md"):
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, {"evidence/instruction.md": INSTR, "evidence/final-code/changes.patch": PATCH},
                     {"q": [{"file": file, "line": line, "quote": quote}]})
            quote_check._cache.clear()
            return quote_check.check(d)

    def test_wrapped_sentence_passes(self):
        self.assertTrue(self.check("Everything that works today keeps working exactly as today.", 3)["pass"])

    def test_line_far_away_fails(self):
        r = self.check("A refusal is a client error.", 40)
        self.assertFalse(r["pass"])
        self.assertIn("not within", r["results"][0]["why"])

    def test_paraphrase_fails(self):
        self.assertFalse(self.check("Everything that works today keeps working as today.", 3)["pass"])

    def test_patch_marker_optional(self):
        self.assertTrue(self.check("if bad(x):", 5, "evidence/final-code/changes.patch")["pass"])
        self.assertTrue(self.check("+    if bad(x):", 5, "evidence/final-code/changes.patch")["pass"])

    def test_transcript_message_block(self):
        tr = "CALL Bash: {}\nAGENT: I changed the code.\nmore\nmore\nmore\nmore\nThis enforces the token.\nRESULT: ok\n"
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, {"evidence/transcript.md": tr},
                     {"q": [{"file": "evidence/transcript.md", "line": 2, "quote": "This enforces the token."}]})
            quote_check._cache.clear()
            quote_check._blocks.clear()
            self.assertTrue(quote_check.check(d)["pass"])
            self.assertFalse(quote_check.check(d, strict_lines=True)["pass"])

    def test_outside_folder_fails(self):
        self.assertFalse(self.check("root", 1, "../../etc/passwd")["pass"])


class Route(unittest.TestCase):
    def run_route(self, labels, infra=(), qc_pass=True, contamination=()):
        facts = {"failing_tests": [{"id": t} for t in labels], "infra_signals": list(infra)}
        dossier = {"failing": [{"tests": [t], "label": lab} for t, lab in labels.items()],
                   "run": {"contamination": list(contamination)}}
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, {}, dossier, facts, {"pass": qc_pass})
            return route.route(d)["route"]

    def test_all_unfair_holds(self):
        self.assertEqual(self.run_route({"a": "possibly-unfair:conflict", "b": "infra"}), "hold-unfair-deciding")

    def test_one_fair_is_note(self):
        self.assertEqual(self.run_route({"a": "possibly-unfair:conflict", "b": "fair"}), "note-unfair")

    def test_fair(self):
        self.assertEqual(self.run_route({"a": "fair"}), "provisional-fail")

    def test_unverified_keeps_hold(self):
        self.assertEqual(self.run_route({"a": "possibly-unfair:conflict"}, qc_pass=False), "hold-unfair-deciding")
        self.assertEqual(self.run_route({"a": "fair"}, qc_pass=False), "unverified")

    def test_provider_stop_is_infra(self):
        sig = {"id": "I1", "kind": "provider-stop", "infra": True}
        self.assertEqual(self.run_route({"a": "fair"}, infra=[sig]), "infra-rerun")

    def test_timeout_with_result_is_not_infra(self):
        sig = {"id": "I1", "kind": "agent-timeout", "infra": False}
        self.assertEqual(self.run_route({"a": "fair"}, infra=[sig]), "provisional-fail")

    def test_unfair_but_fair_version_fails_is_note(self):
        facts = {"failing_tests": [{"id": "a"}], "infra_signals": []}
        dossier = {"failing": [{"tests": ["a"], "label": "possibly-unfair:one-implementation",
                                "fair_version_passes": False}], "run": {}}
        with tempfile.TemporaryDirectory() as tmp:
            d = make(tmp, {}, dossier, facts, {"pass": True})
            self.assertEqual(route.route(d)["route"], "note-unfair")

    def test_contamination(self):
        self.assertEqual(self.run_route({"a": "fair"}, contamination=[{"hit": "C1", "real": True}]),
                         "hold-contamination")


if __name__ == "__main__":
    unittest.main()
