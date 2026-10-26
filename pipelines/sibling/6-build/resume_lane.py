#!/usr/bin/env python3
"""Start every resume job (pipelines/sibling/out/pipeline/resume_jobs.tsv: slug, stage, session) with a random
5-20 s stagger and no concurrency cap — the real-workload check of the Docker deadlock fix.
Writes $CWE_SPIKE_DIR/target_c (default ~/spike/target_c) (= number of jobs) so the monitor records the level.
  python3 -I pipelines/sibling/6-build/resume_lane.py
"""
import os, random, subprocess, time
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
SPIKE = os.environ.get("CWE_SPIKE_DIR", str(Path.home() / "spike"))  # monitor scratch folder
LOG = os.path.join(str(paths.SIBLING_OUT / "pipeline"), "resume_lane.log")


def log(m):
    line = time.strftime("%FT%TZ ", time.gmtime()) + m
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


jobs = [l.rstrip("\n").split("\t") for l in open(os.path.join(str(paths.SIBLING_OUT / "pipeline"), "resume_jobs.tsv"))
        if l.strip() and not l.startswith("slug\t")]
open(os.path.join(SPIKE, "target_c"), "w").write(str(len(jobs)))
log(f"resume lane: {len(jobs)} jobs, stagger 5-20 s")
procs = {}
for slug, stage, sess in jobs:
    procs[slug] = subprocess.Popen(["bash", "pipelines/sibling/6-build/resume_pipeline.sh", slug, stage, sess], cwd=ROOT,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    log(f"[start] {slug} stage={stage} ({len(procs)} started)")
    time.sleep(random.uniform(5, 20))
while procs:
    for s, p in list(procs.items()):
        if p.poll() is not None:
            del procs[s]
            log(f"[finish] {s} rc={p.returncode} ({len(procs)} running)")
    time.sleep(10)
log("resume lane: all jobs finished")
