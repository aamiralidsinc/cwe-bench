"""Tests for the task-quality lint, the scorer check and the refusal helper (python3 -m pytest common/lint/tests)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

LINT = Path(__file__).resolve().parents[1]
ROOT = LINT.parents[1]
sys.path.insert(0, str(LINT))
import checks  # noqa: E402
import score_check  # noqa: E402
import task_lint  # noqa: E402

TEMPLATE_SCORE = ROOT / "common" / "builder" / "templates" / "score.py"
REFUSAL_PY = ROOT / "common" / "builder" / "templates" / "support" / "refusal" / "refusal.py"


def make_task(tmp_path, files, instruction="A request for another host is refused with a client error."):
    t = tmp_path / "task"
    (t / "tests").mkdir(parents=True)
    (t / "instruction.md").write_text(instruction)
    for rel, text in files.items():
        p = t / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return t


def kinds(findings, severity=None):
    return {f.kind for f in findings if severity is None or f.severity == severity}


def test_hypothesis_without_deadline_is_flagged_even_in_project_copies(tmp_path):
    t = make_task(tmp_path, {"tests/functional/project/test_frames.py":
                             "from hypothesis import given\n@given(x=st.integers())\ndef test_x(x):\n    pass\n"})
    assert "hypothesis-deadline" in kinds(checks.run(t), "warn")


def test_hypothesis_profile_with_deadline_off_is_clean(tmp_path):
    t = make_task(tmp_path, {
        "tests/functional/project/test_frames.py": "@given(x=st.integers())\ndef test_x(x):\n    pass\n",
        "tests/functional/project/conftest.py": "from hypothesis import settings\n"
        "settings.register_profile('v', deadline=None)\nsettings.load_profile('v')\n"})
    assert "hypothesis-deadline" not in kinds(checks.run(t))


def test_fetch_only_network_standin_is_flagged(tmp_path):
    t = make_task(tmp_path, {"tests/support/net.js": "// dns.lookup is not patched here\n"
                             "const net = require('node:net');\nglobalThis.fetch = fake;\n"
                             "throw new TypeError('getaddrinfo ENOTFOUND x');\n"})
    assert "network-layer" in kinds(checks.run(t), "warn")


def test_network_standin_below_every_client_is_clean(tmp_path):
    t = make_task(tmp_path, {"tests/support/net.js": "globalThis.fetch = fake;\ndns.lookup = lookup;\n"})
    assert "network-layer" not in kinds(checks.run(t))


def test_hosts_mapping_of_a_functional_host_is_flagged(tmp_path):
    t = make_task(tmp_path, {
        "tests/test.sh": "echo '127.0.0.1 plain.invalid' >> /etc/hosts\n",
        "tests/functional/redirect.test.js": "it('follows', () => get('http://plain.invalid/a'));\n"})
    found = [f for f in checks.run(t) if f.kind == "hosts-loopback"]
    assert found and found[0].severity == "warn"


def test_workspace_project_tests_without_restore_are_flagged(tmp_path):
    t = make_task(tmp_path, {"tests/test.sh":
                             'bash -c "cd /workspace && javac -d out \\\n    test/org/x/BaseTest.java"\n'})
    assert "workspace-tests" in kinds(checks.run(t), "warn")


def test_workspace_project_tests_restored_from_tests_are_clean(tmp_path):
    t = make_task(tmp_path, {"tests/test.sh":
                             "cp /tests/functional/project/test_cfg.py /workspace/core/tests/unit/test_cfg.py\n"
                             "python3 -m pytest /workspace/core/tests/unit/test_cfg.py\n"})
    assert "workspace-tests" not in kinds(checks.run(t))


def test_inconsistent_refusal_handling_is_flagged(tmp_path):
    body = "<?php\nclass ReturnTest extends TestCase {\n  public function testStore() {\n" \
           "    $user->setReturnUrl($payload);\n    $this->assertSame('/', $user->getReturnUrl());\n  }\n}\n"
    other = "<?php\nclass ActionTest extends TestCase {\n  public function testInvoke() {\n" \
            "    try { Actions::invoke($a); } catch (HttpException $e) { $this->assertLessThan(500, $e->statusCode); }\n" \
            "  }\n}\n"
    t = make_task(tmp_path, {"tests/security/ReturnTest.php": body, "tests/security/ActionTest.php": other})
    flagged = [f.file for f in checks.run(t) if f.kind == "refusal-not-accepted"]
    assert flagged == ["tests/security/ReturnTest.php"]


def test_support_files_under_a_security_package_are_not_security_tests(tmp_path):
    t = make_task(tmp_path, {"tests/support/com/x/security/Util.java":
                             "package com.x.security;\npublic class Util { public static void a() {} }\n" * 3})
    assert "refusal-not-accepted" not in kinds(checks.run(t))


def test_standin_missing_members_of_the_real_class(tmp_path):
    repo = tmp_path / "repo" / "src" / "org" / "x" / "auth"
    repo.mkdir(parents=True)
    (repo / "AuthModule.java").write_text(
        "package org.x.auth;\npublic class AuthModule {\n  public static final String REST_TOKEN = \"t\";\n"
        "  public static final String REST_SERVER_NAME = \"serverName\";\n}\n")
    t = make_task(tmp_path, {"tests/support/org/x/auth/AuthModule.java":
                             "package org.x.auth;\npublic class AuthModule {\n"
                             "  public static final String REST_TOKEN = \"t\";\n}\n"})
    found = [f for f in checks.run(t, repo=tmp_path / "repo") if f.kind == "stand-in-class"]
    assert found and found[0].severity == "warn" and "REST_SERVER_NAME" in found[0].message


def test_harness_packages_are_not_standins(tmp_path):
    t = make_task(tmp_path, {"tests/support/htests/MarkerServlet.java":
                             "package htests;\npublic class MarkerServlet {}\n"})
    assert "stand-in-class" not in kinds(checks.run(t))


def test_mock_of_a_relative_product_module_is_a_layer_replacement(tmp_path):
    t = make_task(tmp_path, {"tests/security/gate.test.ts": "vi.mock('../../client.js', () => ({ x: 1 }));\n"})
    assert "layer-replaced" in kinds(checks.run(t), "warn")


def test_template_score_handles_every_scenario():
    assert score_check.check(TEMPLATE_SCORE) == []


def test_legacy_scorer_misses_setup_errors(tmp_path):
    legacy = subprocess.run(["git", "-C", str(ROOT), "show", "18d22464:common/builder/templates/score.py"],
                            capture_output=True, text=True)
    if legacy.returncode != 0:
        pytest.skip("legacy template not available in this checkout")
    p = tmp_path / "score.py"
    p.write_text(legacy.stdout)
    names = {n for n, _r, _w in score_check.check(p)}
    assert {"suite-declared-errors", "suite-own-error", "runner-crash-clean-report"} <= names


def test_lint_cli_writes_summary(tmp_path):
    make_task(tmp_path, {"tests/score.py": TEMPLATE_SCORE.read_text(), "tests/test.sh": "run_group x\n"})
    out = tmp_path / "out"
    assert task_lint.main(["--all", str(tmp_path), "--out", str(out)]) == 0
    assert (out / "SUMMARY.md").is_file() and (out / "task.json").is_file()


# ---------------------------------------------------------------- the Python refusal helper

def load_refusal():
    spec = importlib.util.spec_from_file_location("refusal", REFUSAL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Resp:
    def __init__(self, status):
        self.status_code = status


class HttpErr(Exception):
    def __init__(self, status):
        super().__init__(status)
        self.status_code = status


def test_refusal_helper_accepts_client_errors_and_declared_exceptions():
    r = load_refusal()
    assert r.refused_or(lambda: Resp(403)).refused
    assert r.refused_or(lambda: (_ for _ in ()).throw(HttpErr(422))).refused
    assert r.refused_or(lambda: (_ for _ in ()).throw(PermissionError("no")), refusals=(PermissionError,)).refused
    assert not r.refused_or(lambda: Resp(200), ok=lambda v: True).refused


def test_refusal_helper_rejects_crashes_and_unsafe_results():
    r = load_refusal()
    with pytest.raises(AssertionError):
        r.refused_or(lambda: Resp(500))
    with pytest.raises(HttpErr):
        r.refused_or(lambda: (_ for _ in ()).throw(HttpErr(503)))
    with pytest.raises(TypeError):
        r.refused_or(lambda: (_ for _ in ()).throw(TypeError("crash")), refusals=(PermissionError,))
    with pytest.raises(AssertionError):
        r.refused_or(lambda: Resp(200), ok=lambda v: False)
    with pytest.raises(AssertionError):
        r.must_refuse(lambda: Resp(200))
