"""common/markers.py: the marker readers keep the old call sites' behaviour, writes are atomic, and the contract
checker reports inconsistent task folders."""
import subprocess
import tomllib
from pathlib import Path

import markers
import taskstate

ROOT = Path(markers.__file__).resolve().parents[1]


def b_of(root, slug):
    b = root / "build" / slug
    b.mkdir(parents=True, exist_ok=True)
    return b


def codes(found):
    return {c for _s, c, _m in found}


def no_digest(slug):
    return "deadbeef"


def test_build_done_matches_old_rules(root):
    b = b_of(root, "t-s2")
    assert not markers.build_done(b)
    (b / "start_utc.txt").write_text("2026-10-27T01:00:00Z\n")
    assert markers.build_started(b) and not markers.build_done(b)          # running
    (b / "end_utc.txt").write_text("2026-10-27T02:00:00Z\n")
    assert markers.build_done(b)
    (b / "end_utc.txt").unlink()
    (b / "pipeline.log").write_text("x\nBUILD-INCOMPLETE (agent did not finish)\n")
    assert markers.build_done(b)
    b2 = b_of(root, "u-s2")
    (b2 / ".gate_passed").write_text("")
    assert markers.build_done(b2)
    assert taskstate.build_done(b2) is True                                  # the port delegates


def test_flags_last_result_and_fingerprint(root):
    b = b_of(root, "f-s2")
    for n in (".sound", ".hold-repair", ".blind_fail"):
        (b / n).write_text("")
    assert markers.flags(b) == [".hold-repair", ".sound"]                   # state flags only
    (b / "postbuild.log").write_text("2026-10-27T01:00:00Z f-s2 RESULT: not sound\n"
                                     "2026-10-27T02:00:00Z f-s2 RESULT: SOUND, ready for trials\n")
    ts, text = markers.last_result(b)
    assert text.startswith("SOUND") and ts > 0
    assert markers.fingerprint_sha(b) is None
    (b / "gate_fingerprint.json").write_text('{"sha256": "abc"}')
    assert markers.fingerprint_sha(b) == "abc"


def test_writes_are_atomic_and_verdict_exclusive(root):
    b = b_of(root, "w-s2")
    (b / ".unsound").write_text("")
    markers.set_gate_verdict(b, ".sound")
    assert markers.flags(b) == [".sound"]
    markers.write_atomic(b / "x.txt", "hello")
    assert (b / "x.txt").read_text() == "hello"
    assert not [p for p in b.iterdir() if p.name.startswith(".x.txt.")]    # no temp file left
    try:
        markers.set_gate_verdict(b, ".bogus")
        raise AssertionError("accepted a bad flag")
    except ValueError:
        pass


def test_human_decision_and_delivered(root):
    b = b_of(root, "d-s2")
    (b / "HUMAN-DECISION.md").write_text("DECISION: KEEP\nDATE: 2026-10-27\nDELIVERED: 2026-10-27 to x, commit abc\n")
    assert markers.human_decision(b)[:2] == ("KEEP", "2026-10-27")
    assert markers.delivered_line(b).startswith("2026-10-27")


def test_checker_finds_inconsistencies(root):
    b = b_of(root, "c-s2")
    for n in (".sound", ".unsound", ".gate_passed"):
        (b / n).write_text("")
    (b / "gate_fingerprint.json").write_text('{"sha256": "old"}')
    (b / "end_utc.txt").write_text("2026-10-27T02:00:00Z\n")
    (b / "HUMAN-DECISION.md").write_text("DECISION: DROP\nDATE: 2026-10-27\nDELIVERED: oops\n")
    (b / "removed-tests-20261027").mkdir()
    (b / "postbuild.log").write_text("2026-10-27T02:00:00Z c-s2 RESULT: not sound (gate exit 1)\n")
    found = codes(markers.check("c-s2", fp_digest=no_digest))
    assert {"verdict-not-exclusive", "gate-passed-and-sound", "sound-stale", "end-without-start",
            "delivered-without-keep", "repair-without-readme", "sound-but-result-not-sound"} <= found


def test_checker_clean_folder_and_waiver(root):
    b = b_of(root, "ok-s2")
    (b / ".sound").write_text("")
    (b / "gate_fingerprint.json").write_text('{"sha256": "deadbeef"}')
    (b / "start_utc.txt").write_text("2026-10-27T01:00:00Z\n")
    (b / "end_utc.txt").write_text("2026-10-27T02:00:00Z\n")
    (b / "postbuild.log").write_text("2026-10-27T03:00:00Z ok-s2 RESULT: SOUND, ready for trials\n")
    assert [x for x in markers.check("ok-s2", fp_digest=no_digest) if x[0] != "info"] == []
    (b / ".listing_fail").write_text("")
    assert "listing-fail-and-sound" in codes(markers.check("ok-s2", fp_digest=no_digest))
    (b / "LISTING_WAIVER.md").write_text("waived\n")
    found = codes(markers.check("ok-s2", fp_digest=no_digest))
    assert "listing-fail-and-sound" not in found and "listing-waived" in found


def test_contracts_name_every_stage_and_known_markers():
    c = tomllib.loads((ROOT / "common" / "stage_contracts.toml").read_text())
    for stage in ("build", "gate", "regate", "blind_fix", "listing_check", "trial", "audit_prep", "audit_record",
                  "fairness", "delivery_prep", "lint", "cleanup"):
        assert {"script", "reads", "writes", "success"} <= set(c[stage]), stage
    doc = (ROOT / "docs" / "STAGE-CONTRACTS.md").read_text()
    for name in markers.MARKERS:
        assert f"`{name}`" in doc, f"{name} missing from docs/STAGE-CONTRACTS.md"


def test_shell_helpers(tmp_path):
    script = (f'. "{ROOT}/common/markers.sh"; B="{tmp_path}"; : > "$B/.unsound"; cwe_gate_verdict "$B" .sound; '
              'cwe_hold_after_gate "$B"; cwe_mark_sound "$B"; : > "$B/.listing_warn"; cwe_mark_listing_fail "$B"; '
              'ls -A "$B"')
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True).stdout.split()
    assert out == [".listing_fail"]


# ---------------------------------------------------------------- shell helpers and the readers moved to the library

import subprocess as _sp

_SH = Path(__file__).resolve().parents[2] / "markers.sh"


def _bash(script, cwd, env_extra=None):
    import os as _os
    env = dict(_os.environ, **(env_extra or {}))
    return _sp.run(["bash", "-c", f'. "{_SH}"; {script}'], cwd=cwd, env=env, capture_output=True, text=True)


def test_shell_read_stamp_has(tmp_path):
    b = tmp_path / "build" / "t-s2"
    b.mkdir(parents=True)
    r = _bash('cwe_has build/t-s2 end_utc.txt; echo "has=$?"; cwe_read build/t-s2 build-exit.txt || echo missing; '
              'cwe_stamp build/t-s2 end_utc.txt; echo 137 | cwe_write_atomic build/t-s2/build-exit.txt; '
              'cwe_has build/t-s2 end_utc.txt && echo has-now; cwe_read build/t-s2 build-exit.txt', tmp_path)
    out = r.stdout.split()
    assert out[:2] == ["has=1", "missing"]
    assert "has-now" in out and out[-1] == "137"
    import re as _re
    assert _re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\n", (b / "end_utc.txt").read_text())
    assert not list(b.glob(".end_utc.txt.*")) and not list(b.glob(".build-exit.txt.*"))   # no temp files left


def test_shell_tasks_with_and_unmark(tmp_path):
    for s in ("a-s2", "b-s2", "c-s2"):
        (tmp_path / "build" / s).mkdir(parents=True)
    (tmp_path / "build" / "a-s2" / ".hold-repair").write_text("")
    (tmp_path / "build" / "c-s2" / ".hold-repair").write_text("")
    (tmp_path / "build" / "b-s2" / ".listing_fail").write_text("")
    r = _bash("cwe_tasks_with .hold-repair | paste -sd'|' -; cwe_unmark build/b-s2 .listing_fail .listing_warn; "
              "cwe_has build/b-s2 .listing_fail || echo gone", tmp_path, {"CWE_BUILD": str(tmp_path / "build")})
    assert r.stdout.split() == ["a-s2|c-s2", "gone"]
    r = _bash("cwe_tasks_with .nothing | wc -l", tmp_path, {"CWE_BUILD": str(tmp_path / "build")})
    assert r.stdout.strip() == "0" and r.returncode == 0


def test_checks_readers_use_the_library(root):
    """The post-condition checks read RESULT lines, holds and runs logs through markers (same results as before)."""
    import checks
    b = root / "build" / "x-s2"
    b.mkdir(parents=True)
    (b / "postbuild.log").write_text("2026-10-27T10:00:00Z x-s2 RESULT: not sound\n2026-10-27T11:00:00Z x-s2 RESULT: SOUND, ready\n")
    ts, text = checks.last_result(b)
    assert text == "SOUND, ready" and ts == markers.last_result(b)[0]
    (b / "hold_mimo").write_text("")
    out = checks.c_trial("x-s2", {"model": "mimo"}, 0, {})
    assert out[0][1] is True and "hold_mimo" in out[0][2]
    assert checks.GATE_MARKERS == markers.STATE_FLAGS and checks.BUILD_STOP == markers.END_LINES
