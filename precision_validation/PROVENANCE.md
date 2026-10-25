# Provenance of copied inputs

All inputs are COPIES. Nothing in this folder writes to, or reads from, the original pipeline.

- Source: VM snapshot `cwe-bench/reports/cwe-bench-share-20261021.tar.zst` (taken 2026-10-21),
  unpacked to a scratch dir; `repo-vm/` = the VM's ~/cwe-bench at that time.
- `inputs/pipeline/` <- repo-vm/build/pipeline/{pool.jsonl, selection_*.json, specs_deepseek/,
  abandoned_ds.txt, AUTO-STATE.md, HARDEN-RESET-*.md}; repo-vm/reports/BREAKERS.md (as BREAKERS-20261021.md)
- `inputs/TRIALS-INDEX.csv` <- snapshot root
- `inputs/13-VALIDITY-CONCERNS.md` <- cwe-bench/reports/breakers/ (local, internal)
- `inputs/built_tasks/<slug>/` <- repo-vm/build/<slug>/manifest.json, repo-vm/tasks/<slug>/instruction.md,
  tests/score.py; test_counts.json derived (test functions per group, vendored project/ copies excluded)
- Hashes (sha256, first 16 hex) of every copied file: PROVENANCE-hashes.txt
- Copied: 2026-10-22T21:21:19Z
- `inputs/stacking/` <- local cwe-bench/stacking/out/{batch1.txt, batch1.tsv, reader_jobs.jsonl} (the 30-item
  stacking batch as of 2026-10-22 15:03 local; the live VM queue may differ). Copied 2026-10-22T21:23:28Z
