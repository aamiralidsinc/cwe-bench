#!/usr/bin/env python3
"""Pipeline driver: pick a mode, run a task through the steps, resume where left.

    run.py screen <mined|stacking> [--force]     # (re)run the right screener
    run.py <mode> <slug> [--force <step>]        # drive one task to completion
    run.py status <slug>                         # show per-step state

Modes (task-shape branches, see ALGORITHM.md):
    simple    = mined-only (Branch A)
    sibling   = mined + injected sibling(s) (Branch B)
    stacking  = several real co-present vulns in one checkout (Branch C)

Steps per mode: screen -> build -> gate -> trial.
Resumability: each step's completion is read from the filesystem, so re-running
the same command skips finished steps and continues from the first incomplete
one. --force <step> redoes that step (and everything depends on it staying valid).

What the driver does automatically (no Anthropic account needed):
    screen  -> runs sourcer screener (skips if output exists unless --force)
    gate    -> runs builder/gate.py
    trial   -> runs build/trial.py (sequential early-abort)
The BUILD step needs a builder sub-agent (DeepSeek/Opus), which a script cannot
spawn; for that step the driver prints the exact brief + launch instruction and
stops at 'awaiting-build'. Re-run after the build to continue into gate+trial.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # cwe-bench/
REQ = ["instruction.md", "task.toml", "environment/Dockerfile",
       "solution/solve.sh", "solution/fix.patch", "tests/test.sh", "tests/score.py"]
SCREEN_OUT = {"mined": ROOT / "sourcer" / "shortlist-20.tsv",
              "stacking": ROOT / "sourcer" / "stacking-shortlist.tsv"}
SCREEN_CMD = {"mined": [sys.executable, "-I", str(ROOT / "sourcer" / "osv_sourcer.py"), "propose"],
              "stacking": [sys.executable, "-I", str(ROOT / "sourcer" / "stacking_screener.py")]}
MODE_TRACK = {"simple": "mined", "sibling": "injection", "stacking": "stacking"}
MODE_SCREEN = {"simple": "mined", "sibling": "mined", "stacking": "stacking"}
BRIEF = {"simple": "builder/BUILDER.md",
         "sibling": "build/<slug>/BRIEF.md (+ builder/BUILDER.md)",
         "stacking": "builder/BUILDER-stacking.md (+ builder/BUILDER.md)"}


def build_done(slug):
    d = ROOT / "tasks" / slug
    return d.is_dir() and all((d / r).is_file() for r in REQ)


def gate_passed(slug):
    rep = ROOT / "build" / slug / "gate_report.json"
    if not rep.is_file():
        return False
    return json.loads(rep.read_text()).get("passed") is True


def trial_verdict(slug):
    q = json.loads((ROOT / "build" / "queue.json").read_text())["queue"]
    for item in q:
        if item["slug"] == slug and item.get("status") in ("accepted", "rejected"):
            return item.get("status"), item.get("result", "")
    return None, ""


def screen_done(kind):
    return SCREEN_OUT[kind].is_file()


def run(cmd):
    print(f"[run] $ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd).returncode


def do_screen(kind, force):
    if screen_done(kind) and not force:
        print(f"[run] screen({kind}): already done ({SCREEN_OUT[kind].name}); use --force to redo.")
        return 0
    return run(SCREEN_CMD[kind])


def status(slug):
    q_status, result = trial_verdict(slug)
    print(f"=== {slug} ===")
    print(f"  build : {'done' if build_done(slug) else 'MISSING'}")
    print(f"  gate  : {'PASSED' if gate_passed(slug) else 'not passed'}")
    print(f"  trial : {q_status or 'not run'}" + (f" — {result[:80]}" if result else ""))


def drive(mode, slug, force_step):
    track = MODE_TRACK[mode]
    sdir = ROOT / "build" / slug
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "state.json").write_text(json.dumps({"slug": slug, "mode": mode, "track": track}, indent=1))

    # 1. screen
    kind = MODE_SCREEN[mode]
    if do_screen(kind, force_step == "screen") != 0:
        print("[run] screen failed; stopping."); return 1

    # 2. build (needs a sub-agent; driver cannot spawn one)
    if not build_done(slug) or force_step == "build":
        print(f"\n[run] BUILD needed for {slug} (mode={mode}, track={track}).")
        print(f"[run] Launch a builder sub-agent with: {BRIEF[mode].replace('<slug>', slug)}")
        print(f"[run] Candidate row: build/{slug}/candidate.json (if present).")
        print(f"[run] After the build, re-run:  python3 build/run.py {mode} {slug}")
        print("[run] state: awaiting-build")
        return 2

    # 3. gate
    if not gate_passed(slug) or force_step == "gate":
        if run([sys.executable, "-I", str(ROOT / "builder" / "gate.py"), slug]) != 0:
            print("[run] gate did not pass; stopping (fix the task, then re-run)."); return 1

    # 4. trial
    v, result = trial_verdict(slug)
    if v is None or force_step == "trial":
        if run([sys.executable, str(ROOT / "build" / "trial.py"), slug]) != 0:
            print("[run] trial run errored; stopping."); return 1
        v, result = trial_verdict(slug)
    print(f"\n[run] {slug}: {mode} pipeline complete — verdict: {v or 'unknown'}")
    if result:
        print(f"[run] {result}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_argument_subparsers if False else None  # keep simple, parse positionally
    ap.add_argument("mode")
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--force", default=None, help="redo this step: screen|build|gate|trial")
    args = ap.parse_args()

    if args.mode == "screen":
        kind = args.slug  # second positional is the kind here
        if kind not in SCREEN_OUT:
            print("usage: run.py screen <mined|stacking> [--force]"); return 2
        return do_screen(kind, args.force is not None)
    if args.mode == "status":
        if not args.slug:
            print("usage: run.py status <slug>"); return 2
        status(args.slug); return 0
    if args.mode not in MODE_TRACK or not args.slug:
        print("usage: run.py <simple|sibling|stacking> <slug> [--force step]"); return 2
    return drive(args.mode, args.slug, args.force)


if __name__ == "__main__":
    sys.exit(main())
