#!/usr/bin/env python3
"""Turn JUnit XML results into the task reward, and record BOTH scoring views.

Reads every *.xml under /logs/verifier/security and /logs/verifier/functional, plus each group's runner record
(<group>*.rc: the runner's exit code, and <group>*.log: its output) when test.sh wrote them.
Writes:
  results.json  — per-test outcomes, setup errors, both rewards
  reward.json   — {"reward": <threshold>}     (PRIMARY: what trials/breaker detection read)
  reward.txt    — <threshold>
  metrics.json  — {scoring_mode, status, reward (threshold), passed_total (template ratio),
                   passed, failed, errors, skipped, total}

PRIMARY reward (threshold): 1.0 only when every security and every functional test passes; 0 if any functional
test fails (a fix that breaks the feature earns nothing); otherwise the share of security tests passing, capped
below 1. A group with no results counts as failed.

A test that errors during setup counts as failed in every result format. Besides an <error> or <failure> inside a
<testcase>, these count as one failed entry each ("<group>::setup error ..."):
  - a <testsuite> that declares more errors/failures than its failing <testcase>s show, or holds an <error> or
    <failure> element of its own (fixture, class or module setup that failed outside any test case);
  - a runner that exited non-zero, or timed out, while its report shows no failing test case (a test file that
    never loaded leaves no test case behind);
  - where test.sh recorded no exit code: a runner log line that states a load or setup failure (collection error,
    build failure, failed suite) while the report shows no failing test case.
passed_total (template view): passed / total across both groups (reported alongside, not primary).
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.environ.get("VERIFIER_DIR", "/logs/verifier")

# Runner log lines that mean a test file or suite never ran. Precise on purpose: an assertion message that
# merely contains "error" must not match.
SETUP_MARKERS = [
    re.compile(r"^ERROR collecting ", re.M),                                   # pytest
    re.compile(r"^E\s+(ImportError|ModuleNotFoundError|SyntaxError)\b", re.M),  # pytest import failure
    re.compile(r"^=+ .*\b\d+ errors? (in|during)\b", re.M),                   # pytest summary "N errors in"
    re.compile(r"^FAIL\s+\S+\s+\[(build|setup) failed\]", re.M),               # go test
    re.compile(r"^#\s+\S+\n(?:.*\n){0,20}?.*\.go:\d+:\d+: ", re.M),            # go build errors under "# pkg"
    re.compile(r"Test suite failed to run", re.M),                            # jest
    re.compile(r"^\s*Failed Suites \d+", re.M),                               # vitest
    re.compile(r"^\s*(?:FAIL|×)\s+\S+\s+\[\s*\S+\s*\]\s*$", re.M),             # vitest file-level failure line
    re.compile(r"COMPILATION ERROR", re.M),                                   # maven
    re.compile(r"^\S+\.java:\d+: error: ", re.M),                             # javac
    re.compile(r"^PHP (Fatal|Parse) error: ", re.M),                          # php
    re.compile(r"^There (?:was|were) \d+ errors?:", re.M),                    # phpunit
    re.compile(r"^error(\[E\d+\])?: could not compile", re.M),                # cargo
]


def leaf_suites(root):
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    return [s for s in suites if s.find("testsuite") is None]


def collect(group):
    """Return {name: status} with status in {pass, fail, error, skipped}, setup errors included."""
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, group, "*.xml"))):
        base = os.path.basename(path)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            out[f"{base}::unparseable"] = "error"
            continue
        for case in root.iter("testcase"):
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            if case.find("error") is not None:
                out[name] = "error"
            elif case.find("failure") is not None:
                out[name] = "fail"
            elif case.find("skipped") is not None:
                out[name] = "skipped"  # proves nothing, not a pass
            else:
                out[name] = "pass"
        for i, suite in enumerate(leaf_suites(root)):
            cases = suite.findall("testcase")
            failing = sum(1 for c in cases if c.find("error") is not None or c.find("failure") is not None)
            declared = sum(int(suite.get(k, 0) or 0) for k in ("errors", "failures") if
                           str(suite.get(k, 0) or 0).isdigit())
            own = [ch for ch in suite if ch.tag in ("error", "failure")]
            if own or declared > failing:
                label = suite.get("name") or f"{base}#{i}"
                out[f"{label}::setup error ({max(declared - failing, len(own), 1)} outside test cases)"] = "error"
    return out


def runner_record(group, results):
    """Setup failures the report itself cannot show: a non-zero or timed-out runner, or a load failure in its log,
    while no test case of the group failed."""
    if any(v in ("fail", "error") for v in results.values()):
        return {}
    extra = {}
    for rc_file in sorted(glob.glob(os.path.join(ROOT, f"{group}*.rc"))):
        try:
            rc = int(open(rc_file).read().strip() or 0)
        except ValueError:
            rc = 0
        tag = os.path.basename(rc_file)[:-3]
        if rc in (124, 137):
            extra[f"{group}::setup error ({tag}: runner timed out, exit {rc})"] = "error"
        elif rc != 0:
            extra[f"{group}::setup error ({tag}: runner exit {rc} with no failing test case)"] = "error"
    # The runner's exit code is the precise signal. The log is read only where test.sh recorded no exit code.
    logs = [] if glob.glob(os.path.join(ROOT, f"{group}*.rc")) else sorted(glob.glob(os.path.join(ROOT, f"{group}*.log")))
    for log_file in logs:
        text = open(log_file, errors="replace").read()[-2_000_000:]
        for rx in SETUP_MARKERS:
            m = rx.search(text)
            if m:
                line = m.group(0).strip().splitlines()[0][:80]
                extra[f"{group}::setup error ({os.path.basename(log_file)}: {line})"] = "error"
                break
    return extra


def main():
    sec, fun = collect("security"), collect("functional")
    setup = {}
    for group, res in (("security", sec), ("functional", fun)):
        extra = runner_record(group, res)
        res.update(extra)
        setup.update(extra)
    setup.update({f"security/{k}": v for k, v in sec.items() if "::setup error" in k and k not in setup})
    setup.update({f"functional/{k}": v for k, v in fun.items() if "::setup error" in k and k not in setup})

    def n(d, *st):
        return sum(v in st for v in d.values())

    sec_ok, fun_ok = n(sec, "pass"), n(fun, "pass")
    all_sec = bool(sec) and sec_ok == len(sec)
    all_fun = bool(fun) and fun_ok == len(fun)

    # PRIMARY: threshold reward
    if all_sec and all_fun:
        reward = 1.0
    elif not all_fun:
        reward = 0.0
    else:
        reward = round(min(sec_ok / len(sec), 0.99), 4) if sec else 0.0

    # SECONDARY: template passed/total view + raw counts
    both = {**{f"security/{k}": v for k, v in sec.items()},
            **{f"functional/{k}": v for k, v in fun.items()}}
    total = len(both)
    passed = n(both, "pass")
    failed = n(both, "fail")
    errors = n(both, "error")
    skipped = n(both, "skipped")
    passed_total = round(passed / total, 10) if total else 0.0

    with open(os.path.join(ROOT, "results.json"), "w") as f:
        json.dump({"security": sec, "functional": fun, "setup_errors": sorted(setup),
                   "reward": reward, "passed_total": passed_total}, f, indent=1)
    with open(os.path.join(ROOT, "reward.json"), "w") as f:
        json.dump({"reward": reward}, f)
    with open(os.path.join(ROOT, "reward.txt"), "w") as f:
        f.write(f"{reward}\n")
    with open(os.path.join(ROOT, "metrics.json"), "w") as f:
        json.dump({"scoring_mode": "threshold+passed_total", "status": "scored",
                   "reward": reward, "passed_total": passed_total,
                   "passed": passed, "failed": failed, "errors": errors,
                   "skipped": skipped, "total": total}, f)
    print(f"security {sec_ok}/{len(sec)}  functional {fun_ok}/{len(fun)}  "
          f"reward {reward}  passed_total {passed}/{total}"
          + (f"  setup errors {len(setup)}" if setup else ""))
    return 0 if reward == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
