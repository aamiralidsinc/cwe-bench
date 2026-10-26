#!/usr/bin/env python3
"""Re-grade a trial's SAVED FINAL CODE with the task's current tests (no new model run).

    python3 common/audit/regrade_from_code.py <trial_dir> "<why>" [--from-patch] [--keep-image]

Two modes, chosen the way Harbor chooses them (task.toml [verifier]):

* Separate verifier (environment_mode = "separate", or a [verifier.environment] table; these
  tasks have tests/Dockerfile). This reproduces Harbor's separate verification
  (harbor/trial/trial.py _run_separate_verifier, trial/artifact_handler.py upload_artifacts,
  verifier/verifier.py; harbor/trial/regrade.py does the same from a trial record):
    1. build the verifier image from tasks/<task>/tests/ (build context = tests/, its
       Dockerfile, no build args); the image owns /tests (no tests are copied in);
    2. start it like Harbor's compose service: `sh -c "sleep infinity"`, cpus / memory_mb /
       network (no-network = --network none) / env from [verifier.environment], the result
       folder bind-mounted at /logs/verifier;
    3. as root: create + chmod 777 /logs/verifier; for /logs/artifacts and every task.toml
       `artifacts` entry: empty the target dir (chmod 777) and `docker cp <host>/. <target>`;
    4. as root: chmod +x /tests/test.sh; then run
       `bash -c "(/tests/test.sh) > /logs/verifier/test-stdout.txt 2>&1"` with -w = the
       verifier workdir, -e [verifier.env], -u [verifier].user (unset = the image's user, root),
       timeout = [verifier].timeout_sec x the trial's verifier timeout multiplier.
  The restored input is the run's own record, <trial>/artifacts/<path> (what Harbor collected
  from the agent container, with the task's excludes, and uploaded to the verifier; Harbor's
  own regrade replays exactly these bytes), when artifacts/manifest.json lists it as collected
  with the same excludes. Otherwise (or with --from-patch) the workspace is rebuilt: the
  environment image + final-code/changes.patch, then collected with Harbor's
  `tar czf --exclude=<pattern>... -C <path> .` and extracted with tarfile filter="data".

* Shared verifier (no separate verifier): build the task image from tasks/<task>/environment,
  start a fresh container, replay final-code/changes.patch onto it, copy in the task's
  current tests/, run tests/test.sh as root in that container.

Results are stored the same way in both modes (and like regrade.py):

    <trial>/regrade-<UTC>/verifier/     reward.json, results.json, test-stdout.txt, ...
    <trial>/regrade-<UTC>/tmp-logs/     the grader's /tmp logs
    <trial>/regrade-<UTC>/REGRADE.json  why, when, mode, image, input, reward (written last)

The patch is applied on the host to copies of the changed files (no tools needed in the
image) and copied back. Binary files the harvest did not diff are skipped and listed (e.g.
a database the grader itself created). The original verifier/ is never touched.
audit_results.py uses the newest regrade-* in place of the original grading.
"""
import os
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_code import save_tmp_logs  # noqa: E402

CONVENTION_ARTIFACTS = "/logs/artifacts"   # Harbor's implicit artifact entry (agent publish dir)
VERIFIER_LOGS = "/logs/verifier"


def sh(*a, **kw):
    return subprocess.run(a, capture_output=True, text=True, **kw)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_separate(cfg):
    """Harbor's resolve_task_verifier_mode: explicit mode, else a [verifier.environment] table."""
    v = cfg.get("verifier") or {}
    mode = v.get("environment_mode")
    return mode == "separate" if mode is not None else "environment" in v


def image_exists(image):
    return sh("docker", "image", "inspect", image).returncode == 0


def build(image, context):
    b = sh("docker", "build", "-q", "-t", image, str(context))
    if b.returncode != 0:
        sys.exit(f"image build failed ({context}):\n" + b.stderr[-2000:])


def start_env_container(name, image, mem, extra=()):
    sh("docker", "rm", "-f", name)
    r = sh("docker", "run", "-d", "--name", name, "--memory", f"{mem}m", "--memory-swap", f"{mem}m",
           *extra, image, "sleep", "infinity")
    if r.returncode != 0:
        sys.exit("container start failed:\n" + r.stderr)


def replay_patch(name, code):
    """Replay final-code/changes.patch onto running container `name`. Returns (applied, skipped)."""
    rows = [l.split("\t") for l in (code / "changed_files.tsv").read_text().splitlines()[1:] if l.strip()]
    applied, skipped = [], []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for kind, path, *_rest in rows:          # originals of changed files, mirrored at root/app/...
            if kind == "C":
                dst = root / path.lstrip("/")
                dst.parent.mkdir(parents=True, exist_ok=True)
                if sh("docker", "cp", f"{name}:{path}", str(dst)).returncode != 0:
                    skipped.append(f"{path}: not in image")
        # Apply file by file: one bad entry (e.g. a database the run created, stored as a short
        # text diff, which makes macOS patch abort) must not stop the remaining files.
        text = (code / "changes.patch").read_text(errors="replace")
        # Patches harvested before 2026-10-16 lack "\ No newline at end of file": a file whose last
        # line had no newline swallowed the next header ("+);--- /dev/null"). Split them apart again.
        text = re.sub(r"(?m)^([+ -][^\n]*?)(--- (?:a/|/dev/null))", r"\1\n\\ No newline at end of file\n\2", text)
        starts = [m.start() for m in re.finditer(r"(?m)^--- ", text)] + [len(text)]
        for s, e in zip(starts, starts[1:]):
            chunk = text[s:e]
            m = re.search(r"(?m)^\+\+\+ b/(\S+)", chunk)
            target = m.group(1) if m else "?"
            if re.search(r"(^|/)(vendor|node_modules|\.phpunit\.cache|bootstrap/cache|__pycache__|target|\.cache)/", target):
                skipped.append(f"/{target}: build/cache path, not replayed")
                continue
            if re.search(r"\.(db|sqlite|sqlite3)(-journal|-wal|-shm)?$", target):
                skipped.append(f"/{target}: database file, not replayed")
                continue
            cf = root / ".chunk.patch"
            cf.write_text(chunk)
            p = subprocess.run(["patch", "-p1", "-d", str(root), "--batch", "--forward", "-i", str(cf)],
                               capture_output=True, text=True)
            if p.returncode != 0:
                skipped.append(f"/{target}: patch failed: {(p.stdout + p.stderr)[-300:]}")
            cf.unlink()
        for kind, path, *rest in rows:
            note = rest[1] if len(rest) > 1 else ""
            src = root / path.lstrip("/")
            if kind == "D":
                sh("docker", "exec", "-u", "root", name, "rm", "-rf", path)
                applied.append(f"D {path}")
            elif "binary" in note or not src.is_file():
                skipped.append(f"{kind} {path} ({note or 'not produced by the patch'})")
            else:
                sh("docker", "exec", "-u", "root", name, "mkdir", "-p", str(Path(path).parent))
                if sh("docker", "cp", str(src), f"{name}:{path}").returncode == 0:
                    applied.append(f"{kind} {path}")
                else:
                    skipped.append(f"{kind} {path}: copy failed")
    return applied, skipped


def finish_run(out, name, rc, stdout, keep_stdout_file):
    """Collect /tmp logs, hand root-owned results back to this user, remove the container."""
    save_tmp_logs(out, name)
    # The grader runs as root, so files it wrote into the mounted /logs/verifier are root-owned;
    # hand them back to this user before writing test-stdout.txt and REGRADE.json (2026-10-24).
    sh("docker", "exec", "-u", "root", name, "chown", "-R", f"{os.getuid()}:{os.getgid()}", VERIFIER_LOGS)
    sh("docker", "rm", "-f", name)
    tso = out / "verifier" / "test-stdout.txt"
    if not (keep_stdout_file and tso.is_file()):
        tso.write_text(stdout if isinstance(stdout, str) else str(stdout))
    elif stdout:
        (out / "verifier" / "regrade-exec-output.txt").write_text(str(stdout))
    reward = None
    for f in ("reward.json", "reward.txt"):            # Harbor: reward.json first, else reward.txt
        p = out / "verifier" / f
        if p.is_file() and p.stat().st_size:
            try:
                reward = json.loads(p.read_text()).get("reward") if f == "reward.json" else float(p.read_text())
            except (ValueError, AttributeError):
                reward = None
            break
    if rc == "timeout":
        # Harbor records a verifier timeout as an error with no reward; keep any partial reward file
        # out of the ledger's way (audit_results.py reads verifier/reward.json).
        for f in ("reward.json", "reward.txt"):
            p = out / "verifier" / f
            if p.is_file():
                p.rename(p.with_name(f"after-timeout-{f}"))
        reward = None
    return reward


# ------------------------------------------------------------------ shared (environment image) mode
def env_mode(trial, task, tdir, cfg, out, why):
    code = trial / "final-code"
    if not (code / "changes.patch").is_file():
        sys.exit(f"no saved final code in {code}")
    mem = int((cfg.get("environment") or {}).get("memory_mb") or 4096)
    vtimeout = int((cfg.get("verifier") or {}).get("timeout_sec") or 1800)
    image = f"cwe-regrade-{task}:latest"
    build(image, tdir / "environment")
    (out / "verifier").mkdir(parents=True)
    name = f"regrade-{trial.name.lower()}"
    start_env_container(name, image, mem, ("-v", f"{out / 'verifier'}:{VERIFIER_LOGS}"))
    applied, skipped = replay_patch(name, code)

    sh("docker", "exec", "-u", "root", name, "rm", "-rf", "/tests")
    sh("docker", "cp", f"{tdir / 'tests'}/.", f"{name}:/tests/")
    started = now()
    try:
        run = sh("docker", "exec", "-u", "root", name, "bash", "/tests/test.sh", timeout=vtimeout)
        rc, stdout = run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as e:
        rc, stdout = "timeout", str(e.stdout or "")
    finished = now()
    reward = finish_run(out, name, rc, stdout, keep_stdout_file=False)
    return {"trial": str(trial), "task": task, "mode": "fresh container + saved final code",
            "image": image, "why": why, "memory_mb": mem, "started_utc": started,
            "finished_utc": finished, "exit": rc, "reward": reward,
            "test_sh_sha256": hashlib.sha256((tdir / "tests" / "test.sh").read_bytes()).hexdigest(),
            "files_applied": len(applied), "skipped": skipped}


# ------------------------------------------------------------------ separate verifier mode
def declared_artifacts(cfg):
    """task.toml artifacts + Harbor's convention entry, as dicts {source, destination, exclude}."""
    arts = [{"source": CONVENTION_ARTIFACTS, "destination": None, "exclude": []}]
    for a in cfg.get("artifacts") or []:
        a = {"source": a} if isinstance(a, str) else dict(a)
        if a.get("service"):
            sys.exit(f"artifact {a['source']} comes from service {a['service']}; not supported")
        arts.append({"source": a["source"], "destination": a.get("destination"), "exclude": list(a.get("exclude") or [])})
    return arts


def host_rel(a):
    """Harbor's artifact_host_path, relative to <trial>/artifacts."""
    p = a["destination"] or a["source"]
    return Path(*[x for x in Path(p).parts if x not in ("", "/", "..")])


def saved_inputs(trial, arts):
    """Map source -> saved host dir when the record holds every declared artifact as Harbor needs it.
    Returns (mapping or None, reason)."""
    mf = trial / "artifacts" / "manifest.json"
    if not mf.is_file():
        return None, "no artifacts/manifest.json"
    entries = json.loads(mf.read_text())
    found = {}
    for a in arts:
        dest = (Path("artifacts") / host_rel(a)).as_posix()
        e = next((e for e in reversed(entries) if e.get("source", "").rstrip("/") == a["source"].rstrip("/")
                  and e.get("destination") == dest and not e.get("service")), None)
        if e is None:
            return None, f"{a['source']}: not in the artifact manifest"
        if e.get("status") not in ("ok", "empty"):
            return None, f"{a['source']}: recorded as {e.get('status')}"
        if e.get("type") == "directory" and set(e.get("exclude") or []) != set(a["exclude"]):
            return None, f"{a['source']}: collected with excludes {e.get('exclude')}, task now declares {a['exclude']}"
        host = trial / dest
        if e.get("status") == "ok" and not host.exists():
            return None, f"{a['source']}: collected bytes missing at {dest}"
        found[a["source"]] = host if host.exists() else None   # None = recorded empty
    return found, "artifacts/ (as Harbor collected and restored it)"


def rebuild_inputs(trial, task, tdir, cfg, arts, tmp):
    """Environment image + changes.patch, collected like Harbor's download_dir_with_exclusions."""
    code = trial / "final-code"
    if not (code / "changes.patch").is_file():
        sys.exit(f"no saved workspace usable and no saved final code in {code}")
    mem = int((cfg.get("environment") or {}).get("memory_mb") or 4096)
    image = f"cwe-regrade-{task}:latest"
    build(image, tdir / "environment")
    name = f"regrade-ws-{trial.name.lower()}"
    start_env_container(name, image, mem)
    applied, skipped = replay_patch(name, code)
    found = {}
    try:
        for a in arts:
            if a["source"] == CONVENTION_ARTIFACTS:
                found[a["source"]] = None              # nothing published; Harbor records it empty
                continue
            ex = " ".join(f"--exclude={shlex.quote(p)}" for p in a["exclude"])
            r = sh("docker", "exec", "-u", "root", name, "bash", "-c",
                   f"tar czf /tmp/regrade-artifact.tgz {ex} -C {shlex.quote(a['source'])} .")
            if r.returncode != 0:
                sys.exit(f"collecting {a['source']} from the rebuilt container failed: {r.stderr[-1000:]}")
            tgz = tmp / "artifact.tgz"
            if sh("docker", "cp", f"{name}:/tmp/regrade-artifact.tgz", str(tgz)).returncode != 0:
                sys.exit(f"copying {a['source']} out of the rebuilt container failed")
            host = tmp / "artifacts" / host_rel(a)
            host.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tgz, "r:gz") as tf:
                tf.extractall(path=host, filter="data")
            tgz.unlink()
            found[a["source"]] = host
    finally:
        sh("docker", "rm", "-f", name)
    return found, image, applied, skipped


def run_verifier(name, found, arts, workdir, exec_env, user, vtimeout, out):
    """Steps 3-4 inside the started verifier container. Returns (exit, started, finished, reward, restored)."""
    def root(cmd):
        return sh("docker", "exec", "-u", "root", name, "bash", "-c", cmd)

    def empty_dir(p):                                      # Harbor's _empty_dirs_command (chmod)
        q = shlex.quote(p)
        return root(f"if [ -L {q} ] || {{ [ -e {q} ] && [ ! -d {q} ]; }}; then rm -rf {q}; fi && mkdir -p {q}"
                    f" && find {q} -mindepth 1 -maxdepth 1 -exec rm -rf -- {{}} + && chmod 777 {q}")

    root(f"mkdir -p {VERIFIER_LOGS} && chmod 777 {VERIFIER_LOGS}")   # ensure_dirs(mount targets)
    empty_dir(VERIFIER_LOGS)
    restored = []
    for a in arts:
        host = found.get(a["source"])
        if host is None:
            # Recorded empty: Harbor's regrade materialises an empty dir and uploads it.
            empty_dir(a["source"])
            restored.append(f"{a['source']} (empty)")
            continue
        if host.is_dir():
            if empty_dir(a["source"]).returncode != 0:
                sys.exit(f"could not prepare {a['source']} in the verifier container")
            c = sh("docker", "cp", f"{host}/.", f"{name}:{a['source']}")
        else:
            root(f"mkdir -p {shlex.quote(str(Path(a['source']).parent))} && chmod 777 {shlex.quote(str(Path(a['source']).parent))}")
            c = sh("docker", "cp", str(host), f"{name}:{a['source']}")
        if c.returncode != 0:
            sys.exit(f"restoring {a['source']} failed:\n{c.stderr[-1000:]}")
        restored.append(f"{a['source']} <- {host}")

    root("chmod +x /tests/test.sh")
    cmd = ["docker", "exec"]
    if workdir:
        cmd += ["-w", workdir]
    for k, val in exec_env.items():
        cmd += ["-e", f"{k}={val}"]
    if user is not None:
        cmd += ["-u", str(user)]
    cmd += [name, "bash", "-c", f"(/tests/test.sh) > {VERIFIER_LOGS}/test-stdout.txt 2>&1"]
    started = now()
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=vtimeout)
        rc, stdout = run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as e:
        rc, stdout = "timeout", str(e.stdout or "")
    finished = now()
    reward = finish_run(out, name, rc, stdout, keep_stdout_file=True)
    return rc, started, finished, reward, restored


def verifier_mode(trial, task, tdir, cfg, out, why, from_patch, keep_image):
    v = cfg.get("verifier") or {}
    venv = v.get("environment") or cfg.get("environment") or {}   # Harbor: [verifier.environment] else a copy of [environment]
    if (v.get("environment") is None) and not (tdir / "tests" / "Dockerfile").is_file():
        sys.exit(f"{task}: separate verifier without [verifier.environment] or tests/Dockerfile; not supported")
    tconf = json.loads((trial / "config.json").read_text()) if (trial / "config.json").is_file() else {}
    tv = tconf.get("verifier") or {}
    base = float(tv.get("override_timeout_sec") or v.get("timeout_sec") or 600)
    if tv.get("max_timeout_sec"):
        base = min(base, float(tv["max_timeout_sec"]))
    mult = tconf.get("verifier_timeout_multiplier")
    mult = float(mult if mult is not None else tconf.get("timeout_multiplier") or 1.0)
    vtimeout = base * mult
    cpus, mem = venv.get("cpus"), venv.get("memory_mb")
    net = venv.get("network_mode") or v.get("network_mode") or "public"
    workdir = venv.get("workdir")
    user = v.get("user")
    exec_env = {**(v.get("env") or {}), **(tv.get("env") or {})}
    start_env = venv.get("env") or {}
    for k, val in {**exec_env, **start_env}.items():
        if "${" in str(val):
            sys.exit(f"env {k} references a host variable ({val}); not supported")
    arts = declared_artifacts(cfg)

    with tempfile.TemporaryDirectory(prefix="regrade-ws-") as tmpd:
        tmp = Path(tmpd)
        found, input_note, env_image, applied, skipped = None, None, None, [], []
        if not from_patch:
            found, input_note = saved_inputs(trial, arts)
        if found is not None:
            mode = "verifier image + saved workspace"
        else:
            why_rebuild = "requested (--from-patch)" if from_patch else input_note
            env_image_existed = image_exists(f"cwe-regrade-{task}:latest")
            found, env_image, applied, skipped = rebuild_inputs(trial, task, tdir, cfg, arts, tmp)
            input_note = f"rebuilt from {env_image} + final-code/changes.patch ({why_rebuild})"
            if env_image_existed:
                env_image = None                               # not ours to remove
            mode = "verifier image + rebuilt workspace (environment image + changes.patch)"

        image = f"cwe-regrade-verifier-{task}:latest"
        image_existed = image_exists(image)
        build(image, tdir / "tests")
        (out / "verifier").mkdir(parents=True)
        name = f"regrade-v-{trial.name.lower()}"
        sh("docker", "rm", "-f", name)
        run_args = ["--name", name, "-v", f"{out / 'verifier'}:{VERIFIER_LOGS}"]
        if cpus:
            run_args += ["--cpus", str(float(cpus))]
        if mem:
            run_args += ["--memory", f"{int(mem)}m"]            # compose mem_limit (no swap override)
        if net == "no-network":
            run_args += ["--network", "none"]
        for k, val in start_env.items():
            run_args += ["-e", f"{k}={val}"]
        r = sh("docker", "run", "-d", *run_args, image, "sh", "-c", "sleep infinity")
        if r.returncode != 0:
            sys.exit("verifier container start failed:\n" + r.stderr)
        try:
            info = run_verifier(name, found, arts, workdir, exec_env, user, vtimeout, out)
        finally:
            sh("docker", "rm", "-f", name)
            if not keep_image and not image_existed:
                sh("docker", "rmi", image)
            if env_image:
                sh("docker", "rmi", env_image)
    rc, started, finished, reward, restored = info

    return {"trial": str(trial), "task": task, "mode": mode,
            "image": image, "why": why, "memory_mb": mem, "started_utc": started,
            "finished_utc": finished, "exit": rc, "reward": reward,
            "test_sh_sha256": hashlib.sha256((tdir / "tests" / "test.sh").read_bytes()).hexdigest(),
            "files_applied": len(applied), "skipped": skipped,
            "verifier": {"build_context": str(tdir / "tests"), "cpus": cpus, "network": net,
                         "workdir": workdir, "user": user if user is not None else "image default",
                         "timeout_sec": vtimeout, "exec_env": sorted(exec_env)},
            "input": input_note, "restored": restored,
            "task_checksum_run": (json.loads((trial / "result.json").read_text()).get("task_checksum") or "")[:12]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial_dir")
    ap.add_argument("why")
    ap.add_argument("--from-patch", action="store_true",
                    help="separate-verifier tasks: rebuild /workspace from the environment image + changes.patch "
                         "instead of restoring the saved artifacts/")
    ap.add_argument("--keep-image", action="store_true", help="keep the verifier image tag afterwards")
    a = ap.parse_args()
    trial = Path(a.trial_dir).resolve()
    res = json.loads((trial / "result.json").read_text())
    task = Path(res["config"]["task"]["path"]).name
    tdir = ROOT / "tasks" / task
    cfg = tomllib.loads((tdir / "task.toml").read_text())

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = trial / f"regrade-{stamp}"
    if is_separate(cfg):
        info = verifier_mode(trial, task, tdir, cfg, out, a.why, a.from_patch, a.keep_image)
    else:
        info = env_mode(trial, task, tdir, cfg, out, a.why)
    (out / "REGRADE.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
