"""Post-run audit brief v2 (client audit PO-3, 2026-10-28): the conflict check is enforced on record, and the
evidence leaves earlier conclusions out."""
import importlib.util
import json
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("postmortem", AUDIT / "postmortem.py")
pm = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(AUDIT))
spec.loader.exec_module(pm)


def verdict(items, attribution="model-failed"):
    return {"trustworthy": attribution == "model-failed", "attribution": attribution, "confidence": "high",
            "summary": "s", "items": items, "lookup_or_leak": "none", "evidence": [], "recommended_action": "none"}


def item(test, kind="none", other=False, v="genuine-fail", sentences=()):
    return {"test": test, "outcome": "fail", "model_behaviour": "m", "stated_in_instruction": True,
            "correct_fix_would_pass": kind == "none", "verdict": v, "conflicting_sentences": list(sentences),
            "other_reading_fails": other, "unfair_kind": kind}


def test_old_folders_are_validated_as_before():
    old = verdict([{k: v for k, v in item("t1").items() if k not in ("unfair_kind", "conflicting_sentences",
                                                                      "other_reading_fails")}])
    assert pm.validate(old) == []
    assert pm.validate(old, conflict_check=True)          # new folders must carry the conflict fields


def test_conflict_rules():
    ok = verdict([item("t1"), item("t2", "conflict", True, "test-fault", ["Everything keeps working as today."])])
    assert pm.validate(ok, conflict_check=True) == []
    bad = verdict([item("t1", "conflict", True, "genuine-fail")])
    errs = pm.validate(bad, conflict_check=True)
    assert any("labelled conflict" in e for e in errs) and any("cannot be model-failed" in e for e in errs)
    assert any("cannot be none" in e for e in pm.validate(verdict([item("t1", other=True)]), conflict_check=True))
    assert pm.validate(verdict([item("t1", "one-implementation", True, "test-fault")], "test-fault"),
                       conflict_check=True) == []


def test_schema_lists_the_new_fields():
    props = pm.SCHEMA["properties"]["items"]["items"]["properties"]
    assert set(props["unfair_kind"]["enum"]) == {"none", *pm.UNFAIR_KINDS}
    json.dumps(pm.SCHEMA)


def test_build_notes_lose_earlier_conclusions():
    notes = ("# x build notes\n\n## Levers\n- T1 at a.go:3\n\n## Design decisions\nkeep\n\n"
             "## 2026-10-16 audit finding on DeepSeek r12\nlenient, judged untrusted\n### sub\nmore\n\n"
             "## Pre-trial fairness revision\n- New test `t9` drives the CLI.\n- FAIRNESS.md said GATE_A was READY.\n\n"
             "## Verified\nok\n")
    text, dropped, n = pm.strip_earlier_conclusions(notes)
    assert "T1 at a.go:3" in text and "Design decisions" in text and "## Verified\nok" in text
    assert "New test `t9` drives the CLI." in text                    # a change log keeps what changed
    for gone in ("untrusted", "more", "GATE_A"):
        assert gone not in text
    assert dropped == ["2026-10-16 audit finding on DeepSeek r12"] and n > 0


def test_brief_carries_the_conflict_check_and_no_earlier_verdicts():
    assert "conflicting_sentences" in pm.BRIEF and "other_reading_fails" in pm.BRIEF
    assert "leaves out earlier audits" in pm.BRIEF
