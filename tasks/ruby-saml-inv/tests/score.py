#!/usr/bin/env python3
"""Turn JUnit XML results into the task reward.

Reads every *.xml under /logs/verifier/security and /logs/verifier/functional.
Writes /logs/verifier/results.json (per-test outcomes) and reward.json/reward.txt.

Reward: 1.0 only when every security and every functional test passes.
Otherwise the share of security tests passing, forced to 0 when any functional
test fails (a fix that breaks the feature earns nothing), and capped below 1.
A group with no results counts as failed, so a crashed runner cannot pass.
"""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.environ.get("VERIFIER_DIR", "/logs/verifier")


def collect(group):
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, group, "*.xml"))):
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            out[f"{os.path.basename(path)}::unparseable"] = "fail"
            continue
        for case in tree.iter("testcase"):
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            bad = any(case.find(tag) is not None for tag in ("failure", "error"))
            skipped = case.find("skipped") is not None
            # A skipped test proves nothing, so it does not count as a pass.
            out[name] = "fail" if (bad or skipped) else "pass"
    return out


def main():
    sec, fun = collect("security"), collect("functional")
    sec_ok = sum(v == "pass" for v in sec.values())
    fun_ok = sum(v == "pass" for v in fun.values())
    all_sec = bool(sec) and sec_ok == len(sec)
    all_fun = bool(fun) and fun_ok == len(fun)
    if all_sec and all_fun:
        reward = 1.0
    elif not all_fun:
        reward = 0.0
    else:
        reward = round(min(sec_ok / len(sec), 0.99), 4) if sec else 0.0
    with open(os.path.join(ROOT, "results.json"), "w") as f:
        json.dump({"security": sec, "functional": fun, "reward": reward}, f, indent=1)
    with open(os.path.join(ROOT, "reward.json"), "w") as f:
        json.dump({"reward": reward}, f)
    with open(os.path.join(ROOT, "reward.txt"), "w") as f:
        f.write(f"{reward}\n")
    print(f"security {sec_ok}/{len(sec)}  functional {fun_ok}/{len(fun)}  reward {reward}")
    return 0 if reward == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
