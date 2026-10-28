#!/usr/bin/env python3
"""Save a trial's final code: what the agent changed in /app, as proof of its fix.

    python3 common/audit/harvest_code.py <trial_dir> [--stage during-grading|after-run]

Uses Docker's own record of the container's changes (`docker diff`, i.e. against the
task image: the exact starting point the agent got), so no git history is needed.
Build output and caches are skipped. Works on a running or a stopped container.

Writes <trial_dir>/final-code/ (write-once; skipped if it already exists):
    changes.patch        unified diff of every changed / added / deleted source file
    changed_files.tsv    kind, path, bytes, note
    tmp-logs/            the grader's /tmp/*.log files, if present (setup evidence)
    HARVEST.json         container, image, stage, UTC time, counts
"""
import argparse
import difflib
import io
import json
import re
import subprocess
import tarfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOTS = ("/workspace/", "/app/")
SKIP = re.compile(r"/(node_modules|\.git|dist|build|\.turbo|target|__pycache__|\.pytest_cache|"
                  r"\.cache|\.next|coverage|\.gradle|\.m2|vendor|\.prisma|generated|\.phpunit\.cache|bootstrap/cache)(/|$)"
                  r"|\.(pyc|pyo|class|o|so|log|tsbuildinfo)$|/\.tbfixtures\.ts$")
MAX_FILES, MAX_BYTES, MAX_LOG = 500, 2_000_000, 2_000_000


def sh(*args, binary=False):
    r = subprocess.run(args, capture_output=True)
    return r.returncode, (r.stdout if binary else r.stdout.decode(errors="replace"))


def read_file(container, path):
    """File bytes from a container (running or stopped), or None if absent/not a file."""
    rc, out = sh("docker", "cp", f"{container}:{path}", "-", binary=True)
    if rc != 0:
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(out)) as tf:
            m = tf.next()
            if m is None or not m.isfile():
                return None
            return tf.extractfile(m).read()
    except tarfile.TarError:
        return None


def save_tmp_logs(out: Path, container: str) -> int:
    """Copy the grader's /tmp/*.log (setup evidence). Repeatable: newer copies overwrite.
    Only possible while the container is running."""
    rc, ls = sh("docker", "exec", container, "sh", "-c", "ls /tmp/*.log 2>/dev/null")
    n = 0
    if rc == 0:
        for p in ls.split():
            data = read_file(container, p)
            if data is not None:
                (out / "tmp-logs").mkdir(parents=True, exist_ok=True)
                (out / "tmp-logs" / Path(p).name).write_bytes(data[-MAX_LOG:])
                n += 1
    return n


def read_changes(container, image, changes):
    """(patch lines, rows, rewritten-but-identical count) for the docker diff entries of a container."""
    orig_ctr = f"harvest-orig-{uuid.uuid4().hex[:8]}"
    unchanged = 0
    sh("docker", "create", "--name", orig_ctr, image, "true")
    patch, rows = [], []
    try:
        for kind, path in changes[:MAX_FILES]:
            new = read_file(container, path) if kind in ("A", "C") else None
            old = read_file(orig_ctr, path) if kind in ("C", "D") else None
            if new is None and old is None:
                continue                                   # a directory entry
            if kind == "C" and new == old:
                unchanged += 1                             # rewritten by a build, same content
                continue
            note = ""
            if (new and len(new) > MAX_BYTES) or (old and len(old) > MAX_BYTES):
                note = "too large; not diffed"
            else:
                try:
                    a = (old or b"").decode().splitlines(keepends=True)
                    b = (new or b"").decode().splitlines(keepends=True)
                    # A last line without "\n" must be followed by the standard marker, or the next
                    # file's header is glued onto it (filament r11 regrade, 2026-10-16).
                    for line in difflib.unified_diff(a, b, "/dev/null" if old is None else f"a{path}",
                                                     "/dev/null" if new is None else f"b{path}"):
                        patch.append(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n")
                except UnicodeDecodeError:
                    note = "binary; not diffed"
            rows.append((kind, path, len(new or old or b""), note))
    finally:
        sh("docker", "rm", "-f", orig_ctr)
    return patch, rows, unchanged


def harvest(trial: Path, stage: str, container: str = None, out: Path = None) -> dict:
    out = out or trial / "final-code"
    if out.exists():
        return {"skipped": "final-code already exists"}
    container = container or f"{trial.name.lower()}__env-main-1"
    rc, image = sh("docker", "inspect", "-f", "{{.Image}}", container)
    if rc != 0:
        return {"error": f"container {container} not found"}
    image = image.strip()
    rc, diff = sh("docker", "diff", container)
    if rc != 0:                                            # never record "no changes" from a failed diff
        return {"error": f"docker diff {container} failed (exit {rc}); nothing written, retry later"}
    changes = []
    skipped = 0
    for line in diff.splitlines():
        kind, _, path = line.partition(" ")
        if not path.startswith(ROOTS):
            continue
        if SKIP.search(path):
            skipped += 1
            continue
        changes.append((kind, path))
    # A changed directory shows up as "C /app/src": keep files only (decided below).
    patch, rows, unchanged = read_changes(container, image, changes)
    retried = False
    if changes and not rows and not unchanged and any(k == "A" for k, _ in changes):
        # Added paths but not one file read back: docker cp failed (a loaded daemon), not "no edits".
        time.sleep(5)
        patch, rows, unchanged = read_changes(container, image, changes)
        retried = True
        if not rows and not unchanged:
            return {"error": f"{len(changes)} changed paths in docker diff but no file could be read from "
                             f"{container}; nothing written, retry later"}
    out.mkdir()
    (out / "changes.patch").write_text("".join(patch))
    (out / "changed_files.tsv").write_text("kind\tpath\tbytes\tnote\n" +
                                           "".join(f"{k}\t{p}\t{n}\t{x}\n" for k, p, n, x in rows))
    logs = save_tmp_logs(out, container)
    info = {"trial": str(trial), "container": container, "image": image, "stage": stage,
            "harvested_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files_changed": len(rows), "skipped_build_or_cache_paths": skipped,
            "rewritten_but_identical": unchanged, "diff_entries": len(changes), "retried": retried,
            "truncated": len(changes) > MAX_FILES, "tmp_logs_saved": logs}
    (out / "HARVEST.json").write_text(json.dumps(info, indent=1))
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("trial_dir")
    ap.add_argument("--stage", default="after-run")
    ap.add_argument("--container")
    ap.add_argument("--out", help="write here instead of <trial>/final-code (for tests)")
    a = ap.parse_args()
    print(json.dumps(harvest(Path(a.trial_dir), a.stage, a.container,
                             Path(a.out) if a.out else None), indent=1))
