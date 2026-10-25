#!/usr/bin/env python3
"""Step 5 of the stacking pipeline: static check that a built stacked task meets STACKING-BUILD-ADDENDUM.md.

Runs before the container gate (builder/gate.py, which then executes every patch check with its
expected outcome). No Docker, no model. Exit 0 = conforming, 1 = problems (listed).

Checks:
  - manifest has a `stacking` block with pattern, concepts, history, control_slug, score_at_build;
  - at least 3 independent concepts; every trap id in the concepts exists in manifest.traps;
  - at least one DeepSeek-type and one MiMo-type trap (manifest.traps[].type);
  - one security_fail patch check per concept (a fix missing only that concept), expect fail;
  - recall checks: checks/upstream_fix.patch expect fail; for H3a/H3b also checks/upstream_first_fix.patch;
  - every hidden route has a coupled functional test listed;
  - the control task directory exists.

  python3 -I stacking/check_stack.py SLUG [--root <cwe-bench dir>]
"""
import argparse, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args()
    b = os.path.join(a.root, "build", a.slug)
    problems = []
    try:
        m = json.load(open(os.path.join(b, "manifest.json")))
    except Exception as e:
        print(f"{a.slug}: manifest unreadable: {e}")
        return 1
    st = m.get("stacking") or {}
    for k in ("pattern", "concepts", "history", "control_slug", "score_at_build"):
        if k not in st:
            problems.append(f"stacking.{k} missing")
    traps = {str(t.get("id")): t for t in (m.get("traps") or []) if isinstance(t, dict)}
    concepts = st.get("concepts") or []
    if len(concepts) < 3:
        problems.append(f"only {len(concepts)} independent concepts (need 3+)")
    for g in concepts:
        for tid in g:
            if tid not in traps:
                problems.append(f"concept member {tid} not in manifest.traps")
    types = {str(t.get("type", "")) for t in traps.values()}
    if not types & {"deepseek", "both"}:
        problems.append("no DeepSeek-type trap")
    if not types & {"mimo", "both"}:
        problems.append("no MiMo-type trap")
    checks = m.get("patch_checks") or []
    names = {os.path.basename(str(c.get("patch", ""))): c for c in checks if isinstance(c, dict)}
    for g in concepts:
        covered = any(c.get("expect") == "security_fail" and c.get("kind") == "security_fail" and
                      set(c.get("misses") or []) and set(c.get("misses") or []) <= set(g) for c in checks)
        if not covered:
            problems.append(f"no security_fail check that misses only concept {g} (set its `misses` to the concept's trap ids)")
    need = ["upstream_fix.patch"] + (["upstream_first_fix.patch"] if st.get("pattern") in ("H3a", "H3b") else [])
    for n in need:
        c = names.get(n)
        if not c:
            problems.append(f"recall check {n} missing from patch_checks")
        elif c.get("expect") != "security_fail":
            problems.append(f"recall check {n} must expect fail")
        elif not os.path.isfile(os.path.join(b, "checks", n)):
            problems.append(f"recall check file checks/{n} missing")
    for tid, t in traps.items():
        if t.get("origin") in ("uncovered_upstream", "published_fix_far_site", "injection_room") and not t.get("coupled_functional_tests"):
            problems.append(f"trap {tid}: hidden route without a coupled functional test")
    ctl = st.get("control_slug")
    if ctl and not os.path.isdir(os.path.join(a.root, "tasks", ctl)):
        problems.append(f"control task tasks/{ctl} missing")
    if problems:
        print(f"{a.slug}: NOT conforming")
        for p in problems:
            print("  - " + p)
        return 1
    print(f"{a.slug}: conforming ({len(concepts)} concepts, pattern {st.get('pattern')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
