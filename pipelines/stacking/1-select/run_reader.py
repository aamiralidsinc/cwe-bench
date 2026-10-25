#!/usr/bin/env python3
"""Run the stacking reader (step 2) on every job in pipelines/stacking/out/reader_jobs.jsonl.

Per job:
  1. reuse or create a blobless clone (~/.tb-graders/cwe/stacking/clones/);
  2. pin = parent of the EARLIEST commit in the job's `pin_from` (before any fix);
  3. check the pin out into a separate worktree (~/.tb-graders/cwe/stacking/worktrees/<id>/);
  4. fill STACKING-READER-PROMPT.md and run headless Claude Code with only Read/Grep/Glob/Write;
  5. the agent writes pipelines/stacking/out/reader/<id>.json. Jobs whose output already exists are skipped.
Progress: one line per job start/finish on stdout, and pipelines/stacking/out/reader/_run.log.

  python3 -I pipelines/stacking/1-select/run_reader.py [--parallel 2] [--model claude-opus-5-5] [--only ID ...] [--timeout-min 40]
Env: CLAUDE_BIN (default: the claude found on PATH).
"""
import argparse, json, os, shutil, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
ST = str(paths.STACKING)
OUTDIR = os.path.join(ST, "out", "reader")
CLONES = os.path.expanduser("~/.tb-graders/cwe/stacking/clones")
TREES = os.path.expanduser("~/.tb-graders/cwe/stacking/worktrees")
LOG_LOCK = threading.Lock()
DRY_RUN = False


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with LOG_LOCK:
        print(line, flush=True)
        with open(os.path.join(OUTDIR, "_run.log"), "a") as f:
            f.write(line + "\n")


def git(d, *args, timeout=1800):
    return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, timeout=timeout)


def clone(repo):
    d = os.path.join(CLONES, repo.replace("/", "__"))
    if not os.path.isdir(d):
        os.makedirs(CLONES, exist_ok=True)
        r = subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
                            f"https://github.com/{repo}.git", d], capture_output=True, text=True, timeout=3600)
        if r.returncode:
            raise RuntimeError("clone failed: " + r.stderr.strip()[:150])
    return d


def resolve_pin(d, pin_from):
    shas = []
    for c in pin_from:
        c = c.split()[0].strip().removeprefix("parent of ").strip()
        r = git(d, "rev-parse", "--verify", "--quiet", c + "^{commit}")
        if r.returncode == 0:
            shas.append(r.stdout.strip())
    if not shas:
        raise RuntimeError("no fix commit found in the clone: " + ";".join(pin_from)[:120])
    dated = []
    for s in shas:
        r = git(d, "show", "-s", "--format=%ct", s)
        dated.append((int(r.stdout.strip() or 0), s))
    earliest = min(dated)[1]
    r = git(d, "rev-parse", earliest + "^")
    if r.returncode:
        raise RuntimeError("earliest fix has no parent")
    return r.stdout.strip(), earliest


def worktree(d, jid, pin):
    w = os.path.join(TREES, jid)
    if os.path.isdir(w):
        return w
    os.makedirs(TREES, exist_ok=True)
    r = git(d, "worktree", "add", "--detach", "--force", w, pin, timeout=3600)
    if r.returncode:
        raise RuntimeError("worktree failed: " + r.stderr.strip()[:150])
    return w


def priors():
    t = open(os.path.join(ROOT, "docs", "STACKING-EXPLORATION.md")).read()
    a, b = t.find("### 2.2"), t.find("### 2.4")
    return t[a:b].strip() if a >= 0 and b > a else "(see STACKING-EXPLORATION.md §2.2-2.3)"


def prompt(job, wt, pin, out_path):
    tpl = open(os.path.join(ST, "1-select", "STACKING-READER-PROMPT.md")).read().split("---8<---", 1)[1]
    rec = open(job["screener_record"]).read() if job.get("screener_record") else "none"
    p = (tpl.replace("{{CANDIDATE}}", json.dumps(job["candidate"], indent=1))
            .replace("{{SCREENER_RECORD}}", rec).replace("{{REPO_DIR}}", wt).replace("{{PRIORS}}", priors()))
    return p + (f"\n\n## This run\n- candidate_id: `{job['id']}`; pattern: `{job['pattern']}`; repo: `{job['repo']}`;"
                f" pinned_commit: `{pin}`.\n- Read only under `{wt}`. Write exactly one file: `{out_path}`"
                " (valid JSON matching the Output schema). Do not write anywhere else.\n")


def run(job, model, timeout_min, claude):
    jid = job["id"]
    out_path = os.path.join(OUTDIR, f"{jid}.json")
    if os.path.isfile(out_path):
        log(f"[skip] {jid}: output exists")
        return
    t0 = time.time()
    try:
        d = clone(job["repo"])
        pin, earliest = resolve_pin(d, job["pin_from"])
        wt = worktree(d, jid, pin)
        log(f"[start] {jid} {job['repo']} pin={pin[:10]} (parent of {earliest[:10]})")
        if DRY_RUN:
            p = os.path.join(OUTDIR, f"{jid}.prompt.md")
            open(p, "w").write(prompt(job, wt, pin, out_path))
            log(f"[dry-run] {jid}: prompt written to {p} ({os.path.getsize(p)} bytes); model not called")
            return
        cmd = [claude, "-p", prompt(job, wt, pin, out_path), "--restricted", "--safe-mode", "--strict-mcp-config",
               "--no-session-persistence", "--tools", "Read,Grep,Glob,Write", "--permission-mode", "acceptEdits",
               "--add-dir", wt, "--add-dir", OUTDIR, "--output-format", "json"]
        if model:
            cmd += ["--model", model]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_min * 60, cwd=wt)
        open(os.path.join(OUTDIR, f"{jid}.run.json"), "w").write(r.stdout)
        ok = os.path.isfile(out_path)
        if ok:
            try:
                json.load(open(out_path))
            except Exception:
                ok = False
                log(f"[bad-json] {jid}")
        log(f"[{'done' if ok else 'no-output'}] {jid} rc={r.returncode} {time.time()-t0:.0f}s")
    except subprocess.TimeoutExpired:
        log(f"[timeout] {jid} after {timeout_min} min")
    except Exception as e:
        log(f"[error] {jid}: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parallel", type=int, default=2)
    ap.add_argument("--model", default=os.environ.get("READER_MODEL", ""))
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--timeout-min", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true", help="prepare clone, pin, worktree and prompt; do not call the model")
    a = ap.parse_args()
    global DRY_RUN
    DRY_RUN = a.dry_run
    claude = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
    if not claude:
        sys.exit("claude not found: set CLAUDE_BIN")
    os.makedirs(OUTDIR, exist_ok=True)
    jobs = [json.loads(l) for l in open(os.path.join(ST, "out", "reader_jobs.jsonl")) if l.strip()]
    if a.only:
        jobs = [j for j in jobs if j["id"] in a.only]
    log(f"reader: {len(jobs)} jobs, parallel {a.parallel}, model {a.model or '(CLI default)'}")
    with ThreadPoolExecutor(max_workers=a.parallel) as ex:
        for j in jobs:
            ex.submit(run, j, a.model, a.timeout_min, claude)
    log("reader: all jobs finished")


if __name__ == "__main__":
    main()
