#!/usr/bin/env python3
"""Print gate_report.json status per slug: passed, per-stage ok, and whether the only failure is
the blind check (policy (b): acceptable once fairness is addressed). Usage: gate_status.py SLUG..."""
import json, os, sys

for s in sys.argv[1:]:
    p = os.path.join("build", s, "gate_report.json")
    if not os.path.exists(p):
        print(f"{s:34} (no gate_report.json)")
        continue
    try:
        d = json.load(open(p))
    except Exception as e:
        print(f"{s:34} (unreadable: {e})")
        continue
    stages = d.get("stages", {})
    st = " ".join(k + ("=ok" if v.get("ok") else "=FAIL") for k, v in stages.items())
    badchecks = []
    pc = stages.get("patches", {})
    if not pc.get("ok"):
        for k, v in (pc.get("checks") or {}).items():
            if not v.get("ok"):
                badchecks.append(k)
    non_patch_ok = all(v.get("ok") for k, v in stages.items() if k != "patches")
    only_blind = (not d.get("passed")) and non_patch_ok and badchecks and all("blind" in b for b in badchecks)
    tag = "PASS" if d.get("passed") else ("ONLY-BLIND(b-ok)" if only_blind else "FAIL")
    extra = ("  badchecks=" + ",".join(badchecks)) if badchecks else ""
    print(f"{s:34} {tag:17} | {st}{extra}")
