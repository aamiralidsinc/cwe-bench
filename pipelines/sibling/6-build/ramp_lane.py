#!/usr/bin/env python3
"""Stepped-concurrency build lane for the spike diagnosis: keeps <target> sibling2 builds in flight,
raising the target on a schedule (default 16 for 45 min, 24 for 45, 30 for 45, then 40 to the end),
starting one build at a time with jitter. Each build is sibling2/run_pipeline.sh (build -> gate).

Safety: if the monitor (/home/mara/spike/monitor.csv) shows docker ps or sshd stuck (> 10 s) for three
checks in a row, the ramp HOLDS: no new builds start, none are killed, and the level is logged as the
knee. A manual hold: touch /home/mara/spike/HOLD. The current target is written to
/home/mara/spike/target_c so the monitor records it.

  python3 -I sibling2/ramp_lane.py [--schedule 16:45,24:45,30:45,40:0]
"""
import argparse, os, random, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPIKE = "/home/mara/spike"
LOG = os.path.join(ROOT, "sibling2", "out", "pipeline", "ramp_lane.log")
STUCK_MS = 10000


def log(m):
    line = time.strftime("%FT%TZ ", time.gmtime()) + m
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def last_monitor_row():
    try:
        with open(os.path.join(SPIKE, "monitor.csv"), "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - 600))
            hdr = open(os.path.join(SPIKE, "monitor.csv")).readline().strip().split(",")
            row = f.read().decode(errors="replace").strip().splitlines()[-1].split(",")
        return dict(zip(hdr, row)) if len(row) == len(hdr) else {}
    except Exception:
        return {}


def stuck(r):
    try:
        return (float(r.get("ps_ms", 0)) > STUCK_MS or float(r.get("ps_inflight_s", 0)) * 1000 > STUCK_MS
                or float(r.get("sshd_ms", 0)) > STUCK_MS)
    except ValueError:
        return False


def running_slugs():
    """Slugs of every sibling2 deepseek pipeline running on the box, including ones a previous
    lane started (so a restarted lane counts them toward the target)."""
    out = set()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            a = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")
        except OSError:
            continue
        if len(a) >= 4 and a[0] == b"bash" and a[1] == b"sibling2/run_pipeline.sh" and a[2] == b"deepseek":
            out.add(a[3].decode())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", default="16:45,24:45,30:45,40:0")
    a = ap.parse_args()
    steps = [(int(c), int(m)) for c, m in (s.split(":") for s in a.schedule.split(","))]
    slugs = [s for s in open(os.path.join(ROOT, "sibling2", "out", "pipeline", "slugs_deepseek.txt")).read().split()
             if not os.path.exists(os.path.join(ROOT, "build", s, "pipeline.log"))]
    log(f"ramp lane start: {len(slugs)} slugs, schedule {steps}")
    t0, procs, held, bad, step_logged = time.time(), {}, None, 0, None
    while slugs or procs or running_slugs():
        for s, p in list(procs.items()):
            if p.poll() is not None:
                del procs[s]
                log(f"[finish] {s} rc={p.returncode} ({len(procs)} in flight)")
        el, target = (time.time() - t0) / 60, steps[-1][0]
        acc = 0
        for c, m in steps:
            acc += m
            if m == 0 or el < acc:
                target = c
                break
        if held is not None:
            target = held
        if target != step_logged:
            log(f"target -> {target}" + (" (HELD)" if held is not None else ""))
            step_logged = target
        open(os.path.join(SPIKE, "target_c"), "w").write(str(target))
        r = last_monitor_row()
        bad = bad + 1 if stuck(r) else 0
        running = running_slugs() | set(procs)
        slugs = [s for s in slugs if s not in running]
        if held is None and (bad >= 3 or os.path.exists(os.path.join(SPIKE, "HOLD"))):
            held = len(running)
            log(f"HOLD: knee at {held} in flight (target was {target}); ps_ms={r.get('ps_ms')} "
                f"inflight={r.get('ps_inflight_s')}s sshd_ms={r.get('sshd_ms')} load={r.get('load1')} "
                f"mem={r.get('mem_avail_gb')}G blocked={r.get('blocked')}")
            continue
        if slugs and len(running) < target:
            s = slugs.pop(0)
            procs[s] = subprocess.Popen(["bash", "sibling2/run_pipeline.sh", "deepseek", s], cwd=ROOT,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            log(f"[start] {s} ({len(running) + 1} in flight on box, target {target}, {len(slugs)} left)")
            time.sleep(random.uniform(8, 20))
            continue
        time.sleep(10)
    log("ramp lane: all builds finished")


if __name__ == "__main__":
    main()
