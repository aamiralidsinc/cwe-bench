"""Upstream's own fix as a gate check (gate.py upstream_review, WARN only; client audit PO-3, 2026-10-28)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gate  # noqa: E402

PKG = "github.com/rancher/rancher/pkg/auth"
TRAPS = [
    {"id": "T1", "origin": "advisory_route", "security_tests": ["githubapp::TestSec_TeamsForUserExcludesNonMemberTeams"]},
    {"id": "T4", "origin": "uncovered_upstream", "security_tests": ["requests::TestSec_TokenFallbackDoesNotGrantStaleTeams"]},
    {"id": "T9", "origin": "injected_sibling", "security_tests": ["hidden.security.ProxyPortSecurityTest::testPlainPortRejected"]},
]


def result(sec_fail=(), fun_fail=(), reward=0.75):
    sec = {f"{PKG}/providers/githubapp::TestSec_TeamsForUserExcludesNonMemberTeams": "pass",
           f"{PKG}/requests::TestSec_TokenFallbackDoesNotGrantStaleTeams": "pass",
           "hidden.security.ProxyPortSecurityTest::testPlainPortRejected()": "pass"}
    for t in sec_fail:
        sec[t] = "fail"
    fun = {"f::TestFunc_A": "pass"}
    for t in fun_fail:
        fun[t] = "fail"
    return {"security": sec, "functional": fun, "reward": reward}


def test_variants_failing_upstream_are_expected_not_warnings():
    r = result([f"{PKG}/requests::TestSec_TokenFallbackDoesNotGrantStaleTeams",
                "hidden.security.ProxyPortSecurityTest::testPlainPortRejected()"])
    rev = gate.upstream_review({"traps": TRAPS}, "upstream_fix.patch", r)
    assert rev["warnings"] == []
    assert [x["class"] for x in rev["security_failing"]] == ["expected", "expected"]
    assert [x["trap"] for x in rev["security_failing"]] == ["T4", "T9"]
    assert any("by design" in n for n in rev["notes"])


def test_original_site_or_functional_failure_warns():
    r = result([f"{PKG}/providers/githubapp::TestSec_TeamsForUserExcludesNonMemberTeams"], ["f::TestFunc_A"])
    rev = gate.upstream_review({"traps": TRAPS}, "upstream_fix.patch", r)
    assert len(rev["warnings"]) == 2
    assert "functional" in rev["warnings"][0] and "TestSec_TeamsForUserExcludesNonMemberTeams" in rev["warnings"][1]


def test_first_fix_alone_may_miss_the_original_site():
    r = result([f"{PKG}/providers/githubapp::TestSec_TeamsForUserExcludesNonMemberTeams"])
    rev = gate.upstream_review({"traps": TRAPS}, "upstream_first_fix.patch", r)
    assert rev["partial"] and rev["warnings"] == [] and any("first fix" in n for n in rev["notes"])


def test_unmapped_failures_are_reported_not_warned():
    r = result(["security/Other.php::test_new_route"])
    rev = gate.upstream_review({"traps": TRAPS}, "upstream_fix.patch", r)
    assert rev["warnings"] == [] and any("does not map" in n for n in rev["notes"])


def test_loose_manifest_names_map_to_their_trap():
    traps = [{"id": "T2", "origin": "published_fix_far_site", "security_tests": ["security/T2-pull"]},
             {"id": "T3", "origin": "uncovered_upstream", "security_tests": ["security/SecCoapTest#optionIgnored"]},
             {"id": "T4", "origin": "injected_sibling", "security_tests": ["SecRoleTest.testForeignRefused"]}]
    assert gate.trap_of_test("security/T2-pull::pull with a pack-program option", traps)["id"] == "T2"
    assert gate.trap_of_test("org.apache.camel.htests.SecCoapTest::optionIgnored", traps)["id"] == "T3"
    assert gate.trap_of_test("hidden.security.SecRoleTest::testForeignRefused", traps)["id"] == "T4"
    assert gate.trap_of_test("security/T2-push::push", traps) is None


def test_upstream_patches_listed_or_on_disk(tmp_path):
    (tmp_path / "checks").mkdir()
    (tmp_path / "checks" / "upstream_fix.patch").write_text("")
    assert gate.upstream_patches(tmp_path, {"patch_checks": []}) == [("upstream_fix.patch", False)]
    (tmp_path / "checks" / "upstream_first_fix.patch").write_text("")
    m = {"patch_checks": [{"patch": "upstream_fix.patch", "expect": "security_fail"},
                          {"patch": "upstream_first_fix.patch", "expect": "security_fail"},
                          {"patch": "alt.patch", "expect": "pass"}]}
    assert gate.upstream_patches(tmp_path, m) == [("upstream_fix.patch", True), ("upstream_first_fix.patch", True)]
    (tmp_path / "checks" / "upstream_fix.patch").unlink()
    (tmp_path / "checks" / "upstream_first_fix.patch").unlink()
    assert gate.upstream_patches(tmp_path, m) == []


def test_check_patches_reviews_upstream_and_never_fails_on_it(tmp_path, monkeypatch):
    task, build = tmp_path / "tasks" / "t", tmp_path / "build" / "t"
    (task / "solution").mkdir(parents=True)
    (build / "checks").mkdir(parents=True)
    for p in ("upstream_fix.patch", "miss.patch"):
        (build / "checks" / p).write_text("")
    runs = {"chk-miss": result([f"{PKG}/requests::TestSec_TokenFallbackDoesNotGrantStaleTeams"]),
            "chk-upstream_fix": result([f"{PKG}/providers/githubapp::TestSec_TeamsForUserExcludesNonMemberTeams"])}
    monkeypatch.setattr(gate, "run_harbor", lambda variant, agent, label: {**runs[label], "trial_dir": str(tmp_path)})
    m = {"traps": TRAPS, "patch_checks": [{"patch": "miss.patch", "expect": "security_fail"}]}   # upstream undeclared
    st = gate.check_patches(task, build, m)
    assert st["ok"] and list(st["checks"]) == ["miss.patch"]
    assert st["upstream_fix"][0]["patch"] == "upstream_fix.patch" and len(st["warnings"]) == 1
    json.dumps(st)                                                # the stage record must serialise


def test_scope_warnings_only_for_new_builds():
    traps = [{"id": "T4", "origin": "uncovered_upstream", "security_tests": ["a::b"]},
             {"id": "T1", "origin": "advisory_route", "security_tests": ["a::c"]}]
    assert gate.scope_warnings({"builder_prompt_version": "build-v1", "traps": traps}) == []
    got = gate.scope_warnings({"builder_prompt_version": "build-v1.1", "traps": traps})
    assert len(got) == 1 and "T4" in got[0]
    traps[0].update(entry_point="pkg/auth/requests/authenticate.go:Authenticate")
    assert gate.scope_warnings({"builder_prompt_version": "build-v1.1", "traps": traps}) == []
    # build-v1.2 (2026-10-30): no instruction_scope is asked for; an entry point alone clears the warning.
    assert gate.scope_warnings({"builder_prompt_version": "build-v1.2", "traps": traps}) == []
    del traps[0]["entry_point"]
    got = gate.scope_warnings({"builder_prompt_version": "build-v1.2", "traps": traps})
    assert len(got) == 1 and "entry_point" in got[0] and "instruction" not in got[0]


# ---------- the other-reading check (kind other_reading; the repair step, owner 2026-10-28)

OR_TEST = "functional/05_parser_legit.test.ts::keeps a control character after two dashes a comment"


def or_check(**kw):
    c = {"patch": "other_reading_del.patch", "kind": "other_reading", "expect": "other_reading", "tests": [OR_TEST],
         "follows": "Everything that works today keeps working exactly as it does today.",
         "flagged_by": "build/t/FAIRNESS.md"}
    c.update(kw)
    return c


def test_other_reading_declaration_is_checked_statically():
    assert gate.other_reading_problems({"patch_checks": [or_check()]}) == []
    bad = gate.other_reading_problems({"patch_checks": [or_check(tests=[], follows=" ")]})
    assert len(bad) == 2 and "'tests'" in bad[0] and "'follows'" in bad[1]


def test_other_reading_reports_pass_fail_missing():
    res = {"security": {"security/01.test.ts::refuses a write": "pass"},
           "functional": {f".htests/{OR_TEST}": "fail", "functional/02.test.ts::reads": "pass"}, "reward": 0.9}
    rec = gate.other_reading_result(or_check(tests=[OR_TEST, "functional/02.test.ts::reads", "nope::x"]), res)
    assert rec["tests"] == {OR_TEST: "FAIL", "functional/02.test.ts::reads": "PASS", "nope::x": "MISSING"}
    assert rec["other_failing"] == [] and rec["ok"] is True


def test_check_patches_records_a_proven_conflict_and_stays_sound(tmp_path, monkeypatch, capsys):
    task, build = tmp_path / "tasks" / "t", tmp_path / "build" / "t"
    (task / "solution").mkdir(parents=True)
    (build / "checks").mkdir(parents=True)
    for p in ("other_reading_del.patch", "miss.patch"):
        (build / "checks" / p).write_text("")
    runs = {"chk-miss": result([f"{PKG}/requests::TestSec_TokenFallbackDoesNotGrantStaleTeams"]),
            "chk-other_reading_del": {"security": {}, "functional": {OR_TEST: "fail"}, "reward": 0.0}}
    monkeypatch.setattr(gate, "run_harbor", lambda variant, agent, label: {**runs[label], "trial_dir": str(tmp_path)})
    m = {"traps": TRAPS, "patch_checks": [{"patch": "miss.patch", "expect": "security_fail"}, or_check()]}
    st = gate.check_patches(task, build, m)                    # a FAIL is a finding, never a gate failure
    assert st["ok"] and st["checks"]["other_reading_del.patch"]["tests"] == {OR_TEST: "FAIL"}
    assert st["conflict_proven"] == [{"test": OR_TEST, "result_test": OR_TEST, "patch": "other_reading_del.patch",
                                      "follows": or_check()["follows"]}]
    assert "[gate] CONFLICT-PROVEN: " + OR_TEST in capsys.readouterr().out
    runs["chk-other_reading_del"] = {"security": {}, "functional": {OR_TEST: "pass"}, "reward": 1.0}
    st = gate.check_patches(task, build, m)
    assert "conflict_proven" not in st and st["checks"]["other_reading_del.patch"]["tests"] == {OR_TEST: "PASS"}

    def boom(variant, agent, label):
        if label == "chk-other_reading_del":
            raise gate.InfraError("docker went away")
        return {**runs[label], "trial_dir": str(tmp_path)}
    monkeypatch.setattr(gate, "run_harbor", boom)
    st = gate.check_patches(task, build, m)                    # an infra error on it is recorded, not raised
    assert "docker went away" in st["checks"]["other_reading_del.patch"]["error"]


def test_other_reading_patch_is_not_an_upstream_patch(tmp_path):
    (tmp_path / "checks").mkdir()
    (tmp_path / "checks" / "other_reading_upstream_like.patch").write_text("")
    m = {"patch_checks": [or_check(patch="other_reading_upstream_like.patch")]}
    assert gate.upstream_patches(tmp_path, m) == []
