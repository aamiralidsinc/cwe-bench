#!/usr/bin/env python3
"""Signs that a trial's GRADING setup broke, so its score may not reflect the model.

A run that did not solve and shows any of these is "needs review", not a model
failure: we cannot tell from the score whether the model's code or our environment
broke the setup. Decide from the saved evidence (final-code/, tmp-logs/,
verifier/test-stdout.txt) and record the decision in build/audit/reviews.tsv.

    python3 build/review_flags.py <trial_dir>      # print the flags of one trial
"""
import json
import re
import sys
from pathlib import Path

STDOUT_SIGNS = [
    (r"(?m)^WARNING: .*(fail|timed out)", "grader setup step failed or timed out"),
    (r"server did not come up", "app server did not start"),
    (r"error: could not compile|error\[E\d{4}\]", "compile error"),
    (r"(?m)^(FAIL|ok)\s+\S+\s+\[build failed\]", "Go build failed"),
    (r"COMPILATION ERROR|BUILD FAILURE", "Java build failed"),
    (r"moved core dump\(s\) out of /app", "a process crashed during the run (core dump left in /app)"),
]


def setup_flags(trial: Path, verifier: Path = None) -> list:
    """verifier: the grading to inspect (default <trial>/verifier; a regrade passes its own)."""
    flags = []
    verifier = verifier or trial / "verifier"
    out = verifier / "test-stdout.txt"
    text = out.read_text(errors="replace") if out.is_file() else ""
    for pat, why in STDOUT_SIGNS:
        m = re.search(pat, text)
        if m:
            flags.append(f"{why}: {m.group(0).strip()[:120]}")
    res = verifier / "results.json"
    if not res.is_file():
        flags.append("no verifier/results.json (tests did not report)")
        return flags
    data = json.loads(res.read_text())
    for group in ("security", "functional"):
        g = data.get(group) or {}
        if not g:
            flags.append(f"{group} tests produced no results")
    fun = data.get("functional") or {}
    if fun and not any(v == "pass" for v in fun.values()):
        flags.append(f"every functional test failed ({len(fun)}/{len(fun)}): app likely never worked")
    return flags


if __name__ == "__main__":
    print("\n".join(setup_flags(Path(sys.argv[1]))) or "no flags")
