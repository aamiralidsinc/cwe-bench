"""Run a task's own tests/score.py against synthetic results and report the cases it scores wrongly.

Every scenario is one grading outcome a scorer must not turn into a better reward than the run earned. The scorer
runs in a temporary VERIFIER_DIR, isolated (`python3 -I`), with a time limit; the task folder is only read.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PASS = '<testcase classname="{g}" name="{n}"/>'
FAIL = '<testcase classname="{g}" name="{n}"><failure message="x"/></testcase>'
ERROR = '<testcase classname="{g}" name="{n}"><error message="setup"/></testcase>'
SKIP = '<testcase classname="{g}" name="{n}"><skipped/></testcase>'


def suite(g, cases, extra_attrs="", own=""):
    body = "".join(c.format(g=g, n=f"t{i}") for i, c in enumerate(cases))
    return (f'<?xml version="1.0"?><testsuites><testsuite name="{g}" tests="{len(cases)}" {extra_attrs}>'
            f"{own}{body}</testsuite></testsuites>")


OK3 = [PASS, PASS, PASS]

# name: (files {relative path: text}, check(reward) -> True when scored correctly, what a wrong score means)
SCENARIOS = {
    "all-pass": ({"security/r.xml": suite("security", OK3), "functional/r.xml": suite("functional", OK3)},
                 lambda r: r == 1.0, "a clean run is not scored 1.0"),
    "security-case-error": ({"security/r.xml": suite("security", [PASS, PASS, ERROR]),
                             "functional/r.xml": suite("functional", OK3)},
                            lambda r: r < 1.0, "an <error> test case counts as a pass"),
    "functional-case-error": ({"security/r.xml": suite("security", OK3),
                               "functional/r.xml": suite("functional", [PASS, ERROR])},
                              lambda r: r == 0.0, "a functional <error> does not zero the reward"),
    "skipped-security": ({"security/r.xml": suite("security", [PASS, SKIP]),
                          "functional/r.xml": suite("functional", OK3)},
                         lambda r: r < 1.0, "a skipped security test counts as a pass"),
    "unparseable-functional": ({"security/r.xml": suite("security", OK3), "functional/r.xml": "<testsuite"},
                               lambda r: r == 0.0, "an unreadable functional report is not a failure"),
    "empty-group": ({"security/r.xml": suite("security", OK3)},
                    lambda r: r == 0.0, "a group with no report is not a failure"),
    "suite-declared-errors": ({"security/r.xml": suite("security", OK3, 'errors="2"'),
                               "functional/r.xml": suite("functional", OK3)},
                              lambda r: r < 1.0, "errors a suite declares outside its test cases are ignored "
                                                 "(fixture or class setup that failed)"),
    "suite-own-error": ({"security/r.xml": suite("security", OK3, "", '<error message="setUpClass failed"/>'),
                         "functional/r.xml": suite("functional", OK3)},
                        lambda r: r < 1.0, "an <error> element directly in a <testsuite> is ignored"),
    "functional-setup-error": ({"security/r.xml": suite("security", OK3),
                                "functional/r.xml": suite("functional", OK3, 'errors="1"')},
                               lambda r: r == 0.0, "a functional suite's setup error does not zero the reward"),
    "runner-crash-clean-report": ({"security/r.xml": suite("security", OK3), "security.rc": "2\n",
                                   "functional/r.xml": suite("functional", OK3), "functional.rc": "0\n"},
                                  lambda r: r < 1.0, "a security runner that exited 2 with a clean report scores 1.0 "
                                                     "(a test file that never loaded is invisible)"),
    "runner-timeout-clean-report": ({"security/r.xml": suite("security", OK3), "security.rc": "0\n",
                                     "functional/r.xml": suite("functional", OK3), "functional.rc": "124\n"},
                                    lambda r: r == 0.0, "a functional runner that timed out with a clean report "
                                                        "is not a failure"),
}


def run_scenario(score_py, files, timeout=60):
    with tempfile.TemporaryDirectory(prefix="scorecheck-") as d:
        for g in ("security", "functional"):
            os.makedirs(os.path.join(d, g), exist_ok=True)
        for relp, text in files.items():
            Path(d, relp).write_text(text)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "VERIFIER_DIR": d, "LC_ALL": "C.UTF-8"}
        try:
            subprocess.run([sys.executable, "-I", str(score_py)], cwd=d, env=env, capture_output=True,
                           timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, "timed out"
        try:
            return float(json.loads(Path(d, "reward.json").read_text())["reward"]), ""
        except (OSError, ValueError, KeyError, TypeError):
            txt = Path(d, "reward.txt")
            try:
                return float(txt.read_text().strip()), ""
            except (OSError, ValueError):
                return None, "no reward written"


def check(score_py):
    """[(scenario, reward, problem)] for every scenario the scorer gets wrong."""
    score_py = Path(score_py).resolve()
    src = score_py.read_text(errors="replace") if score_py.is_file() else ""
    if "VERIFIER_DIR" not in src:
        return [("not-checkable", None, "score.py ignores VERIFIER_DIR, so it cannot be run against test results")]
    bad = []
    for name, (files, ok, problem) in SCENARIOS.items():
        reward, err = run_scenario(score_py, files)
        if reward is None:
            bad.append((name, None, err))
        elif not ok(reward):
            bad.append((name, reward, problem))
    return bad


if __name__ == "__main__":
    for p in sys.argv[1:]:
        res = check(p)
        print(f"{p}: " + ("ok" if not res else "; ".join(f"{n} -> {r}: {why}" for n, r, why in res)))
