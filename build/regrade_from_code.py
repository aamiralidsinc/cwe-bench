#!/usr/bin/env python3
"""Re-grade a trial's SAVED FINAL CODE with the task's current tests (no new model run).

    python3 build/regrade_from_code.py <trial_dir> "<why>"

For runs whose container is gone (released after review) but whose final code was harvested
(<trial>/final-code/, by harvest_code.py): build the task image from tasks/<task>/environment,
start a fresh container, replay final-code/changes.patch onto /app, copy in the task's current
tests/, run tests/test.sh, and store the result exactly like regrade.py does:

    <trial>/regrade-<UTC>/verifier/     reward.json, results.json, test-stdout.txt, ...
    <trial>/regrade-<UTC>/tmp-logs/     the grader's /tmp logs
    <trial>/regrade-<UTC>/REGRADE.json  why, when, mode, image, applied/skipped files, reward

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
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest_code import save_tmp_logs  # noqa: E402


def sh(*a, **kw):
    return subprocess.run(a, capture_output=True, text=True, **kw)


def toml_num(text, table, key):
    cur = None
    for line in text.splitlines():
        m = re.match(r"\s*\[(.+)\]", line)
        cur = m.group(1) if m else cur
        m = re.match(rf"\s*{key}\s*=\s*([0-9.]+)", line)
        if m and cur == table:
            return int(float(m.group(1)))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial_dir")
    ap.add_argument("why")
    a = ap.parse_args()
    trial = Path(a.trial_dir).resolve()
    code = trial / "final-code"
    if not (code / "changes.patch").is_file():
        sys.exit(f"no saved final code in {code}")
    res = json.loads((trial / "result.json").read_text())
    task = Path(res["config"]["task"]["path"]).name
    tdir = ROOT / "tasks" / task
    toml = (tdir / "task.toml").read_text()
    mem = toml_num(toml, "environment", "memory_mb") or 4096
    vtimeout = toml_num(toml, "verifier", "timeout_sec") or 1800

    image = f"cwe-regrade-{task}:latest"
    b = sh("docker", "build", "-q", "-t", image, str(tdir / "environment"))
    if b.returncode != 0:
        sys.exit("image build failed:\n" + b.stderr[-2000:])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = trial / f"regrade-{stamp}"
    (out / "verifier").mkdir(parents=True)
    name = f"regrade-{trial.name.lower()}"
    sh("docker", "rm", "-f", name)
    r = sh("docker", "run", "-d", "--name", name, "--memory", f"{mem}m", "--memory-swap", f"{mem}m",
           "-v", f"{out / 'verifier'}:/logs/verifier", image, "sleep", "infinity")
    if r.returncode != 0:
        sys.exit("container start failed:\n" + r.stderr)

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

    sh("docker", "exec", "-u", "root", name, "rm", "-rf", "/tests")
    sh("docker", "cp", f"{tdir / 'tests'}/.", f"{name}:/tests/")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        run = sh("docker", "exec", "-u", "root", name, "bash", "/tests/test.sh", timeout=vtimeout)
        rc, stdout = run.returncode, run.stdout + run.stderr
    except subprocess.TimeoutExpired as e:
        rc, stdout = "timeout", str(e.stdout or "")
    finished = datetime.now(timezone.utc).isoformat(timespec="seconds")
    save_tmp_logs(out, name)
    # The grader runs as root, so files it wrote into the mounted /logs/verifier are root-owned;
    # hand them back to this user before writing test-stdout.txt and REGRADE.json (2026-10-24).
    sh("docker", "exec", "-u", "root", name, "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/logs/verifier")
    sh("docker", "rm", "-f", name)
    (out / "verifier" / "test-stdout.txt").write_text(stdout if isinstance(stdout, str) else str(stdout))

    reward = None
    rj = out / "verifier" / "reward.json"
    if rj.is_file():
        reward = json.loads(rj.read_text()).get("reward")
    info = {"trial": str(trial), "task": task, "mode": "fresh container + saved final code",
            "image": image, "why": a.why, "memory_mb": mem, "started_utc": started,
            "finished_utc": finished, "exit": rc, "reward": reward,
            "test_sh_sha256": hashlib.sha256((tdir / "tests" / "test.sh").read_bytes()).hexdigest(),
            "files_applied": len(applied), "skipped": skipped}
    (out / "REGRADE.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
