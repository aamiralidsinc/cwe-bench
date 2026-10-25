#!/usr/bin/env python3
"""Start every resume job (sibling2/out/pipeline/resume_jobs.tsv: slug, stage, session) with a random
5-20 s stagger and no concurrency cap — the real-workload check of the Docker deadlock fix.
Writes /home/mara/spike/target_c (= number of jobs) so the monitor records the level.
  python3 -I sibling2/resume_lane.py
"""
import os, random, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "sibling2", "out", "pipeline", "resume_lane.log")


def log(m):
    line = time.strftime("%FT%TZ ", time.gmtime()) + m
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


jobs = [l.rstrip("\n").split("\t") for l in open(os.path.join(ROOT, "sibling2", "out", "pipeline", "resume_jobs.tsv"))
        if l.strip() and not l.startswith("slug\t")]
open("/home/mara/spike/target_c", "w").write(str(len(jobs)))
log(f"resume lane: {len(jobs)} jobs, stagger 5-20 s")
procs = {}
for slug, stage, sess in jobs:
    procs[slug] = subprocess.Popen(["bash", "sibling2/resume_pipeline.sh", slug, stage, sess], cwd=ROOT,
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
