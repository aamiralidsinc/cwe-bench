# Frozen builder for the precision-validation experiment

Copied 2026-10-22T21:43:24Z from the LOCAL cwe-bench (the latest version, per Mara 2026-10-22), not
from the VM. The 10-21 VM snapshot is older: local adds shape traps, trap shapes 7-10 (wrong object,
ordering, never-protected route, merged/defaults route), the "list every sibling, pick the hardest
2-4" step in SELFDESIGN-PLAN, and an import-path fix in gate.py. See DIFF-vm20261021-vs-local.txt.
Both carry the instruction rule "never name or describe a sibling's surface".

The frozen files now live under `../root/` (the builder's project root): builder/, harness/,
pipeline/evidence.py, sourcer/build_prepare.py (paths changed only), screener_records/. The Dockerfile
snippet is the VM 10-21 version (newer than local: uid-1000 agent user). Used unchanged for BOTH arms (A and B). Do not edit; a builder change mid-experiment voids the A-vs-B
comparison. Still to copy at VM time: run_build.sh, prepare_lane.py, drive.sh, run_pipeline.sh,
gate_one_ds.sh, trial harness, trial.py, fairness/fairfix runners, postmortem.py, audit_results.py.
Hashes: HASHES.txt.
