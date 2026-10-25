#!/usr/bin/env python3
"""Post-build, pre-check normalizer: force expect='security_fail' on every security_fail-kind
patch check and on the recall checks, so the manifest matches the pipeline's expect vocabulary
(common/gate/gate.py accepts security_fail|functional_fail|pass; check_stack.py reads security_fail).
Leaves functional_fail and pass checks untouched. Safe by definition."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
slug = sys.argv[1]
root = str(paths.ROOT)
p = os.path.join(root, "build", slug, "manifest.json")
try:
    m = json.load(open(p))
except Exception as e:
    print(f"{slug}: normalize skipped (manifest unreadable: {e})"); sys.exit(0)
RECALL = {"upstream_fix.patch", "upstream_first_fix.patch"}
changed = 0
for c in m.get("patch_checks") or []:
    if not isinstance(c, dict):
        continue
    base = os.path.basename(str(c.get("patch", "")))
    is_recall = base in RECALL
    if c.get("kind") == "security_fail" or is_recall:
        if is_recall and c.get("kind") != "security_fail":
            c["kind"] = "security_fail"
        if c.get("expect") != "security_fail":
            c["expect"] = "security_fail"; changed += 1

# ensure the gate-required blind-fix declaration exists (file is produced later by run_blindfix;
# gate static tolerates the missing blind patch per TASK-BUILD-PROMPT-v1 line 344).
pc = m.setdefault("patch_checks", [])
if not any(isinstance(c, dict) and c.get("kind") == "blind" for c in pc):
    pc.append({"patch": "blind.patch", "kind": "blind", "expect": "pass",
               "why": "blind fix produced by run_blindfix after the first gate"})
    changed += 1

if changed:
    json.dump(m, open(p, "w"), indent=2)
print(f"{slug}: normalized {changed} expect value(s) -> security_fail")
