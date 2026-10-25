#!/usr/bin/env python3
"""Frontier-SWE conformance check for a cwe-bench task directory.

The machinery (not a prompt) enforces the delivery format: this returns the list of ways a task
deviates from the frontier-swe template as adopted for cwe-bench (reports/FRONTIER-SWE-FORMAT-
COMPARISON.md + common/builder/FRONTIER-CONFORMANCE-SPEC.md). gate.py calls problems() in its static stage,
so a non-conforming task fails the gate regardless of what any build prompt said.

User-chosen deviations from a literal template copy (2026-10-21): name stays cwe-bench/<slug> and
author Mara Hassan; scoring keeps our threshold reward as primary (passed/total recorded alongside);
2-hour budget, no timer; workdir /workspace.

Usage: conformance_check.py <task-dir>   (exit 0 conforming, 1 otherwise)
"""
import re
import sys
from pathlib import Path

try:
    import tomllib

    def load(p):
        return tomllib.load(open(p, "rb"))
except ModuleNotFoundError:  # py<3.11
    import tomli

    def load(p):
        return tomli.load(open(p, "rb"))

CANARY = re.compile(r"#\s*harbor-canary GUID\s+([0-9a-fA-F-]{8,})")
PLACEHOLDER = "GENERATE-PER-TASK"
# instruction.md must never mention grading/tests/verification (B5).
INSTR_FORBIDDEN = [
    (re.compile(r"do not (modify|add|edit|change|touch|remove)[^.\n]{0,40}\btests?\b", re.I), "tells the agent not to touch tests"),
    (re.compile(r"\bhidden test", re.I), "mentions hidden tests"),
    (re.compile(r"\b(grading|grader|verifier|test suite|junit|pytest)\b", re.I), "mentions grading/tests"),
]
B7_META = ["author_name", "author_email", "difficulty", "difficulty_explanation",
           "solution_explanation", "verification_explanation"]


def _canary_ok(path):
    try:
        head = "\n".join(path.read_text(errors="replace").splitlines()[:3])
    except OSError:
        return False
    m = CANARY.search(head)
    return bool(m) and PLACEHOLDER not in m.group(1)


def problems(task: Path) -> list:
    task = Path(task)
    p = []
    tp = task / "task.toml"
    if not tp.is_file():
        return [f"missing {tp}"]
    try:
        d = load(tp)
    except Exception as e:
        return [f"task.toml does not parse: {e}"]

    if d.get("schema_version") != "1.4":
        p.append('schema_version must be "1.4"')

    arts = d.get("artifacts")
    if not (isinstance(arts, list) and arts and arts[0].get("source") == "/workspace"):
        p.append('artifacts must be [{ source = "/workspace", exclude = [...] }]')

    task_t = d.get("task", {})
    if not str(task_t.get("name", "")).startswith("cwe-bench/"):
        p.append('[task].name must start with "cwe-bench/"')
    authors = task_t.get("authors") or []
    if not (authors and authors[0].get("name") == "Mara Hassan"):
        p.append('[task].authors[0].name must be "Mara Hassan"')

    v = d.get("verifier", {})
    if v.get("environment_mode") != "separate":
        p.append('[verifier].environment_mode must be "separate"')
    if v.get("network_mode") != "no-network":
        p.append('[verifier].network_mode must be "no-network"')
    ve = v.get("environment", {})
    if ve.get("workdir") != "/workspace":
        p.append('[verifier.environment].workdir must be "/workspace"')
    if ve.get("network_mode") != "no-network":
        p.append('[verifier.environment].network_mode must be "no-network"')

    a = d.get("agent", {})
    if a.get("network_mode") != "no-network":
        p.append('[agent].network_mode must be "no-network" (no allowlist in the task file)')
    if "allowed_hosts" in a:
        p.append('[agent] must not set allowed_hosts (allow the model host at run time with --allow-agent-host)')
    if a.get("user") != "agent":
        p.append('[agent].user must be "agent" (unprivileged uid 1000)')

    e = d.get("environment", {})
    if e.get("workdir") != "/workspace":
        p.append('[environment].workdir must be "/workspace"')

    meta = d.get("metadata", {})
    for k in B7_META:
        if not str(meta.get(k, "")).strip():
            p.append(f"[metadata].{k} is empty (template delivery field)")

    # canary GUID in all four files (B8)
    for rel in ("task.toml", "environment/Dockerfile", "tests/Dockerfile", "tests/test.sh"):
        f = task / rel
        if not f.is_file():
            p.append(f"missing {rel}")
        elif not _canary_ok(f):
            p.append(f"{rel} lacks a filled-in '# harbor-canary GUID <uuid>' line")

    # instruction.md says nothing about grading/tests (B5)
    instr = task / "instruction.md"
    if instr.is_file():
        text = instr.read_text(errors="replace")
        for rx, why in INSTR_FORBIDDEN:
            if rx.search(text):
                p.append(f"instruction.md {why} (B5: the report must not mention grading/tests)")

    # separate-mode test.sh must NOT carry the shared-mode kill-the-agent block
    ts = task / "tests/test.sh"
    if ts.is_file() and "@anthropic-ai/claude-code" in ts.read_text(errors="replace"):
        p.append("tests/test.sh still has the shared-mode kill-the-agent block (not needed in a separate verifier)")

    return p


def main():
    if len(sys.argv) != 2:
        print("usage: conformance_check.py <task-dir>", file=sys.stderr)
        return 2
    probs = problems(Path(sys.argv[1]))
    if probs:
        print("NOT CONFORMING:")
        for x in probs:
            print("  - " + x)
        return 1
    print("conforming")
    return 0


if __name__ == "__main__":
    sys.exit(main())
