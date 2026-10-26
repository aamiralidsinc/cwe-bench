#!/usr/bin/env python3
"""Lock every finished trial, every task version and the harness into a write-once archive.

    ~/.local/share/uv/tools/harbor/bin/python common/audit/archive_runs.py

(Harbor's Python, because task fingerprints use Harbor's own `dirhash`.)

Archive: ~/.tb-graders/cwe/archive  (outside the repo; ~1.5 GB, never pushed)

    README.md                      how to read it (rewritten each time)
    INDEX.tsv                      one row per archived run (rewritten each time)
    IMAGES.tsv                     per-task image facts (rewritten each time)
    image-sizes.log                every image size ever measured, append-only, UTC-stamped
    runs/<task>/<model>/<START-UTC>__<limit>m__<outcome>__<job>__<trial>/
        RUN.json                   facts computed from the raw files at archive time
        EXCLUDED.txt               regenerable build output left out (path, size)
        trial/                     the raw trial folder (agent stream, session transcript,
                                   trajectory, verifier output, result.json, config, logs)
        job/                       the job-level result.json, config.json, job.log, lock.json
    tasks/<task>/versions/<fingerprint12>/   exact task folder (Dockerfile + context,
                                   instruction, tests, solution, task.toml) + VERSION.json
    tasks/<task>/gate-runs/<START-UTC>__<kind>__<job>/   oracle / no-op / check runs
    tasks/<task>/build-metadata/   candidate, manifest, gate report, notes, checks
    harness/<sha12>/               the scripts that ran and graded the trials + versions.json
    docker/<UTC>-inventory.json    images, sizes and build-cache digests at that moment

Write-once: a run, task version or harness folder that already exists is never touched,
and every one is made read-only (chmod -R a-w). Runs still in progress are skipped; run
this again after they finish and they are added. Nothing is ever deleted.
"""
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from dirhash import dirhash

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
CWE = Path.home() / ".tb-graders" / "cwe"
JOBS, GATE = CWE / "jobs", CWE / "gate-jobs"
ARCH = Path(os.environ.get("CWE_ARCHIVE", CWE / "archive"))   # override only for test runs
NOW = datetime.now(timezone.utc)
STAMP = NOW.strftime("%Y%m%dT%H%MZ")
LIVE_WINDOW_S = 3 * 3600          # a trial with no result.json touched this recently may be live
# Regenerable build output agents wrote into their log folder (russh: 10+ GB of cargo targets).
EXCLUDE_DIR = re.compile(r"(^|[-_])target$|^node_modules$|^\.gradle$|^\.m2$|^priv-docker$|^dind-data$|^\.mypy_cache$|^__pycache__$")
# Known edits to task folders, newest first: (current text, older text, what changed).
# Used to recover the exact older version a run used, verified by Harbor's fingerprint.
KNOWN_EDITS = [("timeout_sec = 7200.0", "timeout_sec = 3600.0",
                "agent limit was 3600 s; changed to 7200 s on 2026-10-15 ~14:20 UTC")]
HARNESS_FILES = ["common/trial/run_trial.sh", "common/trial/trial.py", "attic/round1-2-driver/trial_fleet.py",
                 "common/audit/audit_results.py", "common/audit/time_breakdown.py", "common/audit/archive_runs.py",
                 "docs/history/TRIAL-PROCEDURE.md", "common/gate/gate.py", "common/builder/templates"]
DERIVED_UNTRUSTED = {"runs_deepseek.log", "runs_mimo.log", "trial_detail.json",
                     "trial_detail_deepseek.json", "trial_detail_mimo.json"}


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def utc_compact(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")


def lock(path):
    subprocess.run(["chmod", "-R", "a-w", str(path)], check=True)


def copytree_filtered(src, dst, excluded, rel=""):
    dst.mkdir(parents=True, exist_ok=True)
    try:
        entries = sorted(src.iterdir())
    except PermissionError:
        excluded.append(f"{rel or src.name}\tunreadable")
        return
    for p in entries:
        r = f"{rel}/{p.name}" if rel else p.name
        if p.is_symlink():
            continue
        if p.is_dir():
            if EXCLUDE_DIR.search(p.name):
                size = subprocess.run(["du", "-sk", str(p)], capture_output=True, text=True).stdout.split()[0]
                excluded.append(f"{r}\t{int(size) // 1024} MB")
                continue
            copytree_filtered(p, dst / p.name, excluded, r)
        else:
            try:
                shutil.copy2(p, dst / p.name)
            except PermissionError:          # e.g. root-owned files a builder's private dockerd left behind
                excluded.append(f"{r}\tunreadable")


def fingerprint(path):
    return dirhash(path, "sha256")


# ---------------------------------------------------------------- task versions
def archive_task_versions(task, recorded):
    """Store the current task folder and any older version the runs used (if recoverable)."""
    out = {}
    src = ROOT / "tasks" / task
    tdir = ARCH / "tasks" / task / "versions"
    candidates = [(src, "current task folder at archive time")]
    tmp = Path(tempfile.mkdtemp())
    variant = tmp / task
    shutil.copytree(src, variant)
    for new, old, why in KNOWN_EDITS:
        for f in variant.rglob("*"):
            if f.is_file() and f.suffix in (".toml", ".md", ".sh", ".py", ""):
                try:
                    t = f.read_text()
                except Exception:
                    continue
                if new in t:
                    f.write_text(t.replace(new, old))
        candidates.append((variant, f"reconstructed: current folder with '{new}' -> '{old}' ({why}); "
                                    "fingerprint verified equal to the task_checksum Harbor recorded"))
    for path, how in candidates:
        fp = fingerprint(path)
        if path is not src and fp not in recorded:
            continue
        out[fp] = how
        dst = tdir / fp[:12]
        if dst.exists():
            continue
        shutil.copytree(path, dst / "task")
        (dst / "VERSION.json").write_text(json.dumps({
            "task": task, "fingerprint_sha256": fp, "how_obtained": how,
            "used_by_recorded_runs": fp in recorded, "archived_at_utc": NOW.isoformat(timespec="seconds")},
            indent=1))
        lock(dst)
    shutil.rmtree(tmp)
    return out


def archive_task_metadata(task):
    src = ROOT / "build" / task
    if not src.is_dir():
        return
    dst = ARCH / "tasks" / task / "build-metadata" / STAMP
    if (ARCH / "tasks" / task / "build-metadata").exists():
        prev = sorted((ARCH / "tasks" / task / "build-metadata").iterdir())
        if prev and _same_tree(src, prev[-1]):
            return
    dst.mkdir(parents=True)
    skipped = []
    for p in src.iterdir():
        if p.name in DERIVED_UNTRUSTED:
            continue                     # written by the buggy reader; see docs/history/RESULTS-AUDIT.md
        if p.is_symlink():
            continue
        if p.is_dir():
            if EXCLUDE_DIR.search(p.name):   # runtime data (a builder's private dockerd, caches), not metadata
                skipped.append(f"{p.name}\truntime data, not archived")
                continue
            copytree_filtered(p, dst / p.name, skipped, p.name)
        else:
            try:
                shutil.copy2(p, dst / p.name)
            except PermissionError:
                skipped.append(f"{p.name}\tunreadable")
    if skipped:
        (dst / "EXCLUDED.txt").write_text("\n".join(skipped) + "\n")
    lock(dst)


def _same_tree(src, dst):
    def digest(base):
        h = hashlib.sha256()
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.name not in DERIVED_UNTRUSTED:
                h.update(str(p.relative_to(base)).encode()); h.update(p.read_bytes())
        return h.hexdigest()
    return digest(src) == digest(dst)


def task_of_job(job):
    """The task a job ran, from its trial config (name prefixes collide: russh vs russh-sib)."""
    for t in (p for p in job.iterdir() if p.is_dir()):
        path = ((jload(t / "config.json") or {}).get("task") or {}).get("path")
        if path:
            return Path(path).name
    return None


def archive_gate_runs(task):
    for job in sorted(GATE.glob(f"{task}-*")):
        if task_of_job(job) != task:
            continue
        kind = job.name[len(task) + 1:].rsplit("-", 1)[0]
        trials = [p for p in job.iterdir() if p.is_dir()]
        res = jload(trials[0] / "result.json") if trials else None
        start = utc_compact(res["started_at"]) if res and res.get("started_at") else "start-unknown"
        dst = ARCH / "tasks" / task / "gate-runs" / f"{start}__{kind}__{job.name}"
        if dst.exists():
            continue
        excluded = []
        copytree_filtered(job, dst, excluded)
        lock(dst)


# ---------------------------------------------------------------- runs
def model_short(name):
    return "deepseek" if "deepseek" in name else "mimo" if "mimo" in name else None


def archive_run(job, trial, versions):
    res = jload(trial / "result.json")
    cfg = jload(trial / "config.json") or {}
    agent = cfg.get("agent") or {}
    model = model_short(agent.get("model_name", ""))
    task = Path((cfg.get("task") or {}).get("path", "")).name
    if not model or not (ROOT / "tasks" / task).is_dir():
        return None, "not a cwe task run"
    if not res and time.time() - os.path.getmtime(trial) < LIVE_WINDOW_S:
        return None, "live (no result.json yet)"
    env = agent.get("env") or {}
    limit = int(env.get("CWE_AGENT_LIMIT_SEC", 3600))
    if res:
        start, end = res.get("started_at"), res.get("finished_at")
        reward = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        exc = (res.get("exception_info") or {}).get("exception_type")
    else:
        jr = jload(job / "result.json") or {}
        start = (jr.get("started_at") or "") and jr["started_at"] + "-04:00"   # job files use local time
        end, reward, exc = None, None, "killed-no-result.json"
    if reward is None:
        reward = (jload(trial / "verifier" / "reward.json") or {}).get("reward")
    outcome = ("solved" if reward == 1.0 else f"failed-{reward:g}" if reward is not None
               else f"ungraded-{exc or 'unknown'}")
    if exc == "AgentTimeoutError" and reward is not None:
        outcome += "-at-timeout"
    start_c = utc_compact(start) if start else "start-unknown"
    run_id = f"{start_c}__{limit // 60}m__{outcome}__{job.name}__{trial.name}"
    dst = ARCH / "runs" / task / model / run_id
    tests = jload(trial / "verifier" / "results.json") or {}

    def frac(k):
        v = list((tests.get(k) or {}).values())
        return f"{sum(x == 'pass' for x in v)}/{len(v)}" if v else None

    ae = (res or {}).get("agent_execution") or {}
    agent_min = None
    if ae.get("started_at") and ae.get("finished_at"):
        agent_min = round((datetime.fromisoformat(ae["finished_at"].replace("Z", "+00:00")) -
                           datetime.fromisoformat(ae["started_at"].replace("Z", "+00:00"))).total_seconds() / 60, 1)
    fp = (res or {}).get("task_checksum")
    row = {"run_id": run_id, "task": task, "model": model, "model_name": agent.get("model_name"),
           "start_utc": start, "end_utc": end, "agent_limit_min": limit // 60, "outcome": outcome,
           "reward": reward, "security": frac("security"), "functional": frac("functional"),
           "exception": exc, "agent_minutes": agent_min, "agent_env": env,
           "claude_code_version": ((res or {}).get("agent_info") or {}).get("version"),
           "task_fingerprint": fp,
           "task_version_dir": (f"tasks/{task}/versions/{fp[:12]}" if fp and fp in versions else
                                "NOT RECOVERED" if fp else None),
           "source_path": str(trial), "path": str(dst.relative_to(ARCH))}
    if dst.exists():
        return row, "already archived"
    excluded = []
    copytree_filtered(trial, dst / "trial", excluded)
    (dst / "job").mkdir()
    for f in ("result.json", "config.json", "job.log", "lock.json"):
        if (job / f).is_file():
            shutil.copy2(job / f, dst / "job" / f)
    row["archived_at_utc"] = NOW.isoformat(timespec="seconds")
    (dst / "RUN.json").write_text(json.dumps(row, indent=1, default=str))
    (dst / "EXCLUDED.txt").write_text("\n".join(excluded) + ("\n" if excluded else "none\n"))
    lock(dst)
    return row, "archived"


# ---------------------------------------------------------------- harness + docker
def archive_harness():
    h = hashlib.sha256()
    files = []
    for rel in HARNESS_FILES:
        p = ROOT / rel
        for f in ([p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())):
            files.append(f); h.update(str(f.relative_to(ROOT)).encode()); h.update(f.read_bytes())
    dst = ARCH / "harness" / h.hexdigest()[:12]
    if dst.exists():
        return dst
    for f in files:
        t = dst / f.relative_to(ROOT)
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, t)

    def cmd(*a):
        try:
            return subprocess.run(a, capture_output=True, text=True, timeout=60).stdout.strip()
        except Exception as e:
            return f"unavailable: {e}"
    (dst / "versions.json").write_text(json.dumps({
        "archived_at_utc": NOW.isoformat(timespec="seconds"),
        "harbor": cmd("harbor", "--version"), "docker": cmd("docker", "version", "--format", "{{.Server.Version}}"),
        "colima": cmd("colima", "list", "--json"), "python_for_trials": sys.version}, indent=1))
    lock(dst)
    return dst


def docker_inventory():
    def cmd(*a):
        return subprocess.run(a, capture_output=True, text=True, timeout=120).stdout
    images = [json.loads(l) for l in cmd("docker", "images", "--format", "{{json .}}").splitlines() if l]
    cache = cmd("docker", "buildx", "du", "--verbose")
    digests = sorted(set(re.findall(r"pulled from (\S+@sha256:[0-9a-f]{64})", cache)))
    inv = {"taken_at_utc": NOW.isoformat(timespec="seconds"), "images": images,
           "base_image_digests_in_build_cache": digests,
           "system_df": cmd("docker", "system", "df")}
    d = ARCH / "docker"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{STAMP}-inventory.json").write_text(json.dumps(inv, indent=1))
    return inv


def image_facts(task, inv):
    df = (ROOT / "tasks" / task / "environment" / "Dockerfile").read_text()
    bases = re.findall(r"^FROM\s+(\S+)", df, re.M)
    commit = (re.search(r"git fetch[^\n]*?\b([0-9a-f]{40})\b", df) or
              re.search(r"COMMIT=([0-9a-f]{40})", df))
    pinned = [d for b in bases for d in inv["base_image_digests_in_build_cache"]
              if d.split("/")[-1].split("@")[0] == b.split("/")[-1]]
    secs = []
    for root in (JOBS, GATE):
        for f in root.glob(f"{task}-*/*/result.json"):
            r = jload(f) or {}
            if Path(((r.get("config") or {}).get("task") or {}).get("path", "")).name != task:
                continue
            es = r.get("environment_setup") or {}
            if es.get("started_at") and es.get("finished_at"):
                secs.append((datetime.fromisoformat(es["finished_at"].replace("Z", "+00:00")) -
                             datetime.fromisoformat(es["started_at"].replace("Z", "+00:00"))).total_seconds())
    # Sizes can only be read while an image exists, so every reading is appended to
    # image-sizes.log and the latest one is reported after the image is deleted.
    log = ARCH / "image-sizes.log"
    present = [i for i in inv["images"] if i["Repository"].startswith(f"{task}__")
               or i["Repository"] == f"sizecheck-{task}"]
    if present:
        with open(log, "a") as f:
            for i in present:
                f.write(f"{NOW.isoformat(timespec='seconds')}\t{task}\t{i['Size']}\t{i['ID']}\t{i['Repository']}\n")
    seen = [l.split("\t") for l in (log.read_text().splitlines() if log.is_file() else [])
            if l.split("\t")[1:2] == [task]]
    last = seen[-1] if seen else None
    return {"task": task, "base_images": " ".join(bases), "base_digest_used": " ".join(pinned) or "not in cache",
            "source_commit": commit.group(1) if commit else "?",
            "builds_observed": len(secs),
            "build_typical_s": round(statistics.median(secs)) if secs else None,
            "build_longest_s": round(max(secs)) if secs else None,
            "image_size": last[2] if last else "not measured yet",
            "image_size_measured_at_utc": last[0] if last else None}


# ---------------------------------------------------------------- main
def main():
    ARCH.mkdir(parents=True, exist_ok=True)
    recorded = {}
    for f in JOBS.glob("*/*/result.json"):
        r = jload(f) or {}
        t = Path(((r.get("config") or {}).get("task") or {}).get("path", "")).name
        if r.get("task_checksum"):
            recorded.setdefault(t, set()).add(r["task_checksum"])
    tasks = sorted(p.name for p in (ROOT / "tasks").iterdir() if (p / "task.toml").is_file())
    versions = {}
    for t in tasks:
        versions.update(archive_task_versions(t, recorded.get(t, set())))
        archive_task_metadata(t)
        archive_gate_runs(t)
    # A version counts as recovered if it was archived now or by any earlier run of this tool.
    have = {(p.parent.parent.name, p.name) for p in ARCH.glob("tasks/*/versions/*")}
    unrecovered = {t: [c[:12] for c in cs if c not in versions and (t, c[:12]) not in have]
                   for t, cs in recorded.items() if t in tasks}

    rows, skipped, counts = [], [], {}
    for job in sorted(JOBS.iterdir()):
        if not job.is_dir():
            continue
        for trial in sorted(p for p in job.iterdir() if p.is_dir()):
            row, status = archive_run(job, trial, versions)
            counts[status] = counts.get(status, 0) + 1
            if row:
                rows.append(row)
            elif status.startswith("live"):
                skipped.append(f"{job.name}/{trial.name}")
    rows.sort(key=lambda r: (r["task"], r["model"], r["start_utc"] or ""))
    cols = ["start_utc", "task", "model", "agent_limit_min", "outcome", "reward", "security", "functional",
            "exception", "agent_minutes", "task_fingerprint", "path"]
    with open(ARCH / "INDEX.tsv", "w") as f:
        f.write(f"# generated {NOW.isoformat(timespec='seconds')} by common/audit/archive_runs.py; "
                f"{len(rows)} runs; times are UTC\n" + "\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join("" if r[c] is None else str(r[c])[:12] if c == "task_fingerprint" else str(r[c])
                              for c in cols) + "\n")

    harness = archive_harness()
    inv = docker_inventory()
    facts = [image_facts(t, inv) for t in tasks]
    with open(ARCH / "IMAGES.tsv", "w") as f:
        f.write(f"# generated {NOW.isoformat(timespec='seconds')}; build times are Harbor's environment-setup "
                "phase over all runs (cached builds are seconds; the longest is the closest to a full build)\n")
        f.write("\t".join(facts[0].keys()) + "\n")
        for x in facts:
            f.write("\t".join("" if v is None else str(v) for v in x.values()) + "\n")

    (ARCH / "README.md").write_text(README.format(
        now=NOW.isoformat(timespec="seconds"), n=len(rows), live="\n".join(f"- {s}" for s in skipped) or "- none",
        unrecovered=json.dumps({k: v for k, v in unrecovered.items() if v}) or "{}", harness=harness.name))
    print(json.dumps({"runs_indexed": len(rows), "status_counts": counts, "live_skipped": skipped,
                      "task_versions": len(versions), "unrecovered_versions": {k: v for k, v in unrecovered.items() if v},
                      "harness": harness.name}, indent=1))


README = """# CWE-bench run archive

Generated {now} UTC by `common/audit/archive_runs.py`. **{n} runs archived.** Everything under
`runs/`, `tasks/*/versions/`, `tasks/*/gate-runs/`, `tasks/*/build-metadata/` and `harness/`
is write-once and read-only. Unlock deliberately with `chmod -R u+w <folder>`.

## How to read it without getting confused
- **Every run folder name starts with its UTC start time**, then the agent time limit, outcome,
  job and trial: `runs/<task>/<model>/<START-UTC>__<limit>m__<outcome>__<job>__<trial>/`.
  Sort by name to get chronological order. The 60-minute era and the 120-minute era are
  told apart by the `60m` / `120m` field; never pool them without saying so.
- `outcome` uses the rules in `cwe-bench/common/audit/audit_results.py`: `solved` = reward 1.0;
  `failed-<reward>` = graded below 1.0; `-at-timeout` = graded when the agent limit cut it;
  `ungraded-<reason>` = never graded (not a model failure).
- `RUN.json` holds the facts; `trial/` holds the raw evidence: `agent/claude-code.txt`
  (agent stream), `agent/sessions/**.jsonl` (Claude Code transcript with timestamps on every
  tool call), `agent/trajectory.json`, `verifier/results.json` (every test, pass/fail),
  `verifier/test-stdout.txt`, `result.json` (timings, reward, exception).
- `EXCLUDED.txt` lists regenerable build output (cargo targets etc.) that was not copied.
- `INDEX.tsv` and `IMAGES.tsv` are regenerated each time and list everything archived.
- Each run's `task_fingerprint` points to `tasks/<task>/versions/<fingerprint12>/`: the exact
  task folder (Dockerfile and build context, instruction, tests, solution) that run used.
  Fingerprints that could not be recovered: {unrecovered}
- Not copied on purpose: `runs_<model>.log` and `trial_detail_*.json` from build metadata.
  A reader bug wrote them and they are wrong for many runs.
- The harness that ran and graded these trials is in `harness/{harness}/`.

## Rebuilding an image later
Use `tasks/<task>/versions/<fp>/task/environment/Dockerfile`. Repos are pinned to exact
commits. Base images are pinned by tag only; the digest each build actually used is in
`IMAGES.tsv` (`base_digest_used`) when Docker's build cache still held it. apt/pip/npm
package versions inside the Dockerfiles are not pinned, so a rebuild may differ slightly.

## Runs not yet archived (still running when this was generated)
{live}
"""

if __name__ == "__main__":
    main()
