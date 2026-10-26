#!/usr/bin/env python3
"""Convert jest --json reports into the JUnit XML the verifier scores.

Usage: jest2junit.py <out.xml> <report.json> [<report.json> ...]

Missing/unreadable reports mean jest itself failed to run; a synthetic failing
testcase is written so the grader records a real failure instead of an
infrastructure error.
"""
import glob
import json
import os
import re
import sys
import xml.sax.saxutils as sax


def esc(value):
    return sax.escape(str(value or ""), {'"': "&quot;"})


def main():
    if len(sys.argv) < 2:
        return 2
    out = sys.argv[1]
    reports = sys.argv[2:]

    cases = []          # (classname, name, status, message)
    seen = set()
    for path in reports:
        if not os.path.isfile(path):
            continue
        try:
            with open(path) as handle:
                data = json.load(handle)
        except Exception:
            continue
        for suite in data.get("testResults", []) or []:
            fname = suite.get("name") or suite.get("testFilePath") or "unknown"
            fname = re.sub(r"^/workspace/", "", fname)
            assertions = suite.get("assertionResults") or []
            for assertion in assertions:
                full = assertion.get("fullName") or assertion.get("title") or "test"
                status = assertion.get("status")
                message = "\n".join(assertion.get("failureMessages") or [])
                state = {"passed": "pass", "failed": "fail"}.get(status, "skipped")
                key = (fname, full)
                if key in seen:
                    continue
                seen.add(key)
                cases.append((fname, full, state, message))
            if not assertions and suite.get("status") == "failed":
                key = (fname, "suite")
                if key not in seen:
                    seen.add(key)
                    cases.append((fname, "suite", "error", suite.get("message", "")))

    if not cases:
        log = ""
        for path in glob.glob(os.path.join(os.path.dirname(out), "*.log")):
            try:
                with open(path, errors="replace") as handle:
                    log += handle.read()[-4000:]
            except OSError:
                pass
        cases.append(
            ("hidden-runner", "suite", "error",
             "no jest report was produced\n" + log[-3000:])
        )

    suites = {}
    for fname, name, state, message in cases:
        suites.setdefault(fname, []).append((name, state, message))

    parts = ['<?xml version="1.0" encoding="UTF-8"?>', "<testsuites>"]
    for fname, entries in suites.items():
        failures = sum(1 for _, state, _ in entries if state in ("fail", "error"))
        parts.append(
            f'<testsuite name="{esc(fname)}" tests="{len(entries)}" '
            f'failures="{failures}" errors="0">'
        )
        for name, state, message in entries:
            head = message.strip().splitlines()[0][:300] if message.strip() else ""
            if state in ("fail", "error"):
                tag = "failure" if state == "fail" else "error"
                parts.append(
                    f'<testcase classname="{esc(fname)}" name="{esc(name)}">'
                    f'<{tag} message="{esc(head)}">{esc(message[:4000])}</{tag}>'
                    f"</testcase>"
                )
            elif state == "skipped":
                parts.append(
                    f'<testcase classname="{esc(fname)}" name="{esc(name)}">'
                    f"<skipped/></testcase>"
                )
            else:
                parts.append(
                    f'<testcase classname="{esc(fname)}" name="{esc(name)}"/>'
                )
        parts.append("</testsuite>")
    parts.append("</testsuites>")

    with open(out, "w") as handle:
        handle.write("\n".join(parts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
