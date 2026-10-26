#!/usr/bin/env python3
"""pipelines/router/regate_queue.py <slugs-file> <P>: throttled re-gate of a list of slugs: up to P at a time, each only after its post-build step has ended
(postbuild.log has a RESULT line: the blind fix and listing review are finished)."""
import os, subprocess, sys, time
os.chdir(os.path.expanduser("~/cwe-bench"))
lst, P = sys.argv[1], int(sys.argv[2])
env = dict(os.environ, GATE_PARALLEL="4", GATE_STAGES_PARALLEL="0")
todo = [l.strip() for l in open(lst) if l.strip()]; running = {}
log = open("pipelines/router/out/queue/regate-b1.log", "a")
def say(m): log.write(time.strftime("%FT%TZ ", time.gmtime()) + m + "\n"); log.flush()
say(f"regate queue: {len(todo)} slugs, {P} at a time, GATE_PARALLEL=4, stages one at a time")
while todo or running:
    for s, p in list(running.items()):
        if p.poll() is not None:
            say(f"[finish] {s} rc={p.returncode}"); del running[s]
    for s in list(todo):
        if len(running) >= P: break
        pb = f"build/{s}/postbuild.log"
        if os.path.isfile(pb) and "RESULT" in open(pb).read():
            todo.remove(s)
            out = open(f"build/{s}/regate.out", "a")
            running[s] = subprocess.Popen(["bash", "common/gate/regate.sh", s] + (["--listing"] if s.startswith("stk-") else []),
                                          stdout=out, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            say(f"[start] {s}"); time.sleep(20)
    time.sleep(15)
say("regate queue: done")
