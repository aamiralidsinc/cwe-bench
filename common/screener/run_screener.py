#!/usr/bin/env python3
"""Grow the H4 pool: run the UNCHANGED sibling screener prompt (builder/SCREENER-PROMPT-v2.md, read as is)
on more candidate advisories, writing records into stacking/out/screener/ (never into sourcer/review/).

Selection (--pick N): the next N candidates by index score (sourcer/index/candidates.sqlite, read-only),
one per repo, skipping repos already screened (sourcer/review/screener-v2 and stacking/out/screener)
or already built (--built dirs), DoS-only CWEs, repos over 1.5 GB, and entries without a fix commit.
Writes the list to stacking/out/screener_jobs.jsonl (merged, like make_reader_jobs.py).

Run (--run): per job, blobless clone, worktree at the parent commit, fix diff saved beside it, slots
filled (lessons-v2, candidate row, code location, LATEST=none, output path, 20-minute time box), then
headless Claude Code with only Read/Grep/Glob/Write. Jobs with an existing output are skipped.

  python3 -I stacking/run_screener.py --pick 100 --built <tasks dirs...>
  CLAUDE_BIN=... python3 -I stacking/run_screener.py --run [--parallel 3] [--model claude-opus-5-5] [--dry-run]
Then: python3 -I stacking/h4_rank.py --recs sourcer/review/screener-v2 stacking/out/screener --built ...
"""
import argparse, glob, json, os, re, shutil, sqlite3, subprocess, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(ROOT, "stacking")
OUTDIR = os.path.join(ST, "out", "screener")
JOBS = os.path.join(ST, "out", "screener_jobs.jsonl")
DB = os.path.join(ROOT, "sourcer", "index", "candidates.sqlite")
PROMPT = os.path.join(ROOT, "builder", "SCREENER-PROMPT-v2.md")
CLONES = os.path.expanduser("~/.tb-graders/cwe/stacking/clones")
TREES = os.path.expanduser("~/.tb-graders/cwe/stacking/screen-trees")
DOS = {"CWE-400", "CWE-770", "CWE-1333", "CWE-674", "CWE-834", "CWE-407", "CWE-606"}
LOCK = threading.Lock()
DRY = False


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    with LOCK:
        print(line, flush=True)
        with open(os.path.join(OUTDIR, "_run.log"), "a") as f:
            f.write(line + "\n")


def norm(repo):
    return str(repo or "").lower().rstrip("/").replace("https://github.com/", "")


def screened_repos():
    repos = set()
    for d in (os.path.join(ROOT, "sourcer", "review", "screener-v2"), OUTDIR):
        for f in glob.glob(os.path.join(d, "*.json")):
            if os.path.basename(f).startswith(("._", "_")) or f.endswith(".run.json"):
                continue
            try:
                repos.add(norm(json.load(open(f)).get("repo")))
            except Exception:
                pass
    return repos


def built_repos(dirs):
    repos = set()
    for d in dirs:
        for t in glob.glob(os.path.join(d, "*", "task.toml")):
            m = re.search(r'^\s*repo\s*=\s*"([^"]+)"', open(t, errors="replace").read(), re.M)
            if m:
                repos.add(norm(m.group(1)))
    return repos


def pick(n, built_dirs):
    skip = screened_repos() | built_repos(built_dirs)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out, seen = [], set()
    for r in con.execute("select * from entries where status='candidate' order by score desc"):
        repo = norm(r["repo"])
        cwes = set((r["cwe_ids"] or "").split())
        if not repo or repo in skip or repo in seen or not (r["fix_commits"] or r["fix_commit"]):
            continue
        if cwes and cwes <= DOS:
            continue
        if (r["repo_size_kb"] or 0) > 1_500_000:
            continue
        row = {k: r[k] for k in r.keys() if k in ("entry_id", "ids", "cve", "repo", "cwe_ids", "summary", "parent_commit",
                                                 "fix_commits", "language", "score", "published")
               or k.startswith("c_")}
        out.append(dict(id=f"scr-{r['entry_id']}", entry_id=str(r["entry_id"]), repo=repo, row=row))
        seen.add(repo)
        if len(out) >= n:
            break
    merged = {}
    if os.path.isfile(JOBS):
        for l in open(JOBS):
            if l.strip():
                j = json.loads(l)
                merged[j["id"]] = j
    new = [j for j in out if j["id"] not in merged]
    for j in out:
        merged[j["id"]] = j
    os.makedirs(os.path.dirname(JOBS), exist_ok=True)
    open(JOBS, "w").write("".join(json.dumps(j) + "\n" for j in merged.values()))
    print(f"picked {len(out)} (new {len(new)}); {len(merged)} screener jobs in file")
    for j in out[:15]:
        print(f"  {j['id']:12} {j['repo']:45} score={j['row'].get('score')}")


def git(d, *a, timeout=1800):
    return subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def prepare(job):
    d = os.path.join(CLONES, job["repo"].replace("/", "__"))
    if not os.path.isdir(d):
        os.makedirs(CLONES, exist_ok=True)
        r = subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
                            f"https://github.com/{job['repo']}.git", d], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
        if r.returncode:
            raise RuntimeError("clone failed: " + r.stderr.strip()[:150])
    fixes = [c for c in re.split(r"[\s,;]+", str(job["row"]["fix_commits"]).strip("[]\"' ")) if re.fullmatch(r"[0-9a-f]{7,40}", c)]
    parent = job["row"].get("parent_commit")
    if not parent:   # the index rarely has it: pin = parent of the EARLIEST fix commit (as the reader does)
        dated = []
        for c in fixes:
            r = git(d, "show", "-s", "--format=%ct %H", c)
            if r.returncode == 0 and r.stdout.strip():
                ts, sha = r.stdout.split()[:2]
                dated.append((int(ts), sha))
        if not dated:
            raise RuntimeError("no fix commit found in the clone")
        r = git(d, "rev-parse", min(dated)[1] + "^")
        if r.returncode:
            raise RuntimeError("earliest fix commit has no parent")
        parent = r.stdout.strip()
        job["row"]["parent_commit"] = parent
    if git(d, "rev-parse", "--verify", "--quiet", parent + "^{commit}").returncode:
        raise RuntimeError(f"parent commit {parent[:12]} not in clone")
    w = os.path.join(TREES, job["id"])
    if not os.path.isdir(w):
        os.makedirs(TREES, exist_ok=True)
        r = git(d, "worktree", "add", "--detach", "--force", w, parent, timeout=3600)
        if r.returncode:
            raise RuntimeError("worktree failed: " + r.stderr.strip()[:150])
    diff_path = os.path.join(TREES, job["id"] + ".fix.diff")
    if not os.path.isfile(diff_path):
        parts = []
        for c in fixes:
            r = git(d, "show", "--format=commit %H%n%s%n", c, timeout=1800)
            parts.append(r.stdout if r.returncode == 0 else f"(fix commit {c} not found)\n")
        open(diff_path, "w").write("\n".join(parts))
    return w, diff_path


def prompt(job, w, diff_path, out_path):
    t = open(PROMPT, encoding="utf-8").read()
    body = t.split("---8<---")[1]
    sec = t[t.find("## lessons-v2"):]
    m = re.search(r"```\n(.*?)\n```", sec, re.S)
    lessons = m.group(1) if m else ""
    return (body.replace("{{LESSONS_VERSION}}", "lessons-v2").replace("{{LESSONS_DIGEST}}", lessons)
                .replace("{{CANDIDATE}}", json.dumps(job["row"], indent=1, default=str))
                .replace("{{CODE_LOCATION}}", f"the code at parent_commit is checked out at `{w}`; the fix diff is `{diff_path}`")
                .replace("{{LATEST_LOCATION}}", "none").replace("{{OUTPUT_PATH}}", out_path)
                .replace("{{TIME_BOX_MIN}}", "20"))


def run_one(job, model, claude, timeout_min):
    out_path = os.path.join(OUTDIR, f"{job['entry_id']}.json")
    if os.path.isfile(out_path):
        log(f"[skip] {job['id']}: output exists")
        return
    t0 = time.time()
    try:
        w, diff_path = prepare(job)
        p = prompt(job, w, diff_path, out_path)
        left = re.findall(r"\{\{[A-Z_]+\}\}", p)
        if left:
            raise RuntimeError(f"unfilled slots {left}")
        log(f"[start] {job['id']} {job['repo']}")
        if DRY:
            open(os.path.join(OUTDIR, f"{job['entry_id']}.prompt.md"), "w").write(p)
            log(f"[dry-run] {job['id']}: prompt written; model not called")
            return
        cmd = [claude, "-p", p, "--restricted", "--safe-mode", "--strict-mcp-config", "--no-session-persistence",
               "--tools", "Read,Grep,Glob,Write", "--permission-mode", "acceptEdits",
               "--add-dir", w, "--add-dir", TREES, "--add-dir", OUTDIR, "--output-format", "json"]
        if model:
            cmd += ["--model", model]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_min * 60, cwd=w)
        open(os.path.join(OUTDIR, f"{job['entry_id']}.run.json"), "w").write(r.stdout)
        ok = os.path.isfile(out_path)
        if ok:
            try:
                json.load(open(out_path))
            except Exception:
                ok = False
        log(f"[{'done' if ok else 'no-output'}] {job['id']} rc={r.returncode} {time.time()-t0:.0f}s")
    except subprocess.TimeoutExpired:
        log(f"[timeout] {job['id']}")
    except Exception as e:
        log(f"[error] {job['id']}: {e}")


def main():
    global DRY
    ap = argparse.ArgumentParser()
    ap.add_argument("--pick", type=int, default=0)
    ap.add_argument("--built", nargs="*", default=[])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--model", default="")
    ap.add_argument("--timeout-min", type=int, default=30)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    if a.pick:
        pick(a.pick, a.built)
    if a.run:
        DRY = a.dry_run
        claude = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
        if not claude:
            sys.exit("claude not found: set CLAUDE_BIN")
        jobs = [json.loads(l) for l in open(JOBS) if l.strip()]
        if a.only:
            jobs = [j for j in jobs if j["id"] in a.only]
        log(f"screener: {len(jobs)} jobs, parallel {a.parallel}, model {a.model or '(CLI default)'}")
        with ThreadPoolExecutor(max_workers=a.parallel) as ex:
            for j in jobs:
                ex.submit(run_one, j, a.model, claude, a.timeout_min)
        log("screener: all jobs finished")


if __name__ == "__main__":
    main()
