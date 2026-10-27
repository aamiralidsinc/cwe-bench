"""cwe_reuse_tag: content-addressed image tags for task build contexts (no Harbor import).

Shared by the Harbor environment class (cwe_reuse_env.py, gate and trial runs) and by
common/audit/regrade_from_code.py, so all three start the SAME image for one task version:

    cwe-reuse/<task>:env-<hash20>        built from tasks/<task>/environment/
    cwe-reuse/<task>:verifier-<hash20>   built from tasks/<task>/tests/   (separate-verifier tasks)

<hash20> covers every file of the build context (path, exec bit, bytes; symlinks by target), so any
edit to the context gives a new tag and a rebuild. Last use = mtime of $CWE_REUSE_STATE/used/<tag file>
(read by common/util/hourly_cleanup.sh); builds of one tag are serialised by $CWE_REUSE_STATE/locks/.
"""
from __future__ import annotations

import fcntl
import hashlib
import os
import re
import subprocess
from pathlib import Path

REPO = "cwe-reuse"
STATE = Path(os.environ.get("CWE_REUSE_STATE", Path.home() / ".tb-graders/cwe/image-reuse"))
_IGNORE = {".DS_Store", ".git", "__pycache__"}       # the names Harbor's own content hash ignores


def context_hash(ctx: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(ctx.rglob("*"), key=lambda q: q.relative_to(ctx).as_posix()):
        rel = p.relative_to(ctx)
        if _IGNORE & set(rel.parts) or (p.is_dir() and not p.is_symlink()):
            continue
        h.update(rel.as_posix().encode() + b"\0")
        if p.is_symlink():
            h.update(b"L" + os.readlink(p).encode() + b"\0")
            continue
        h.update(b"X" if os.access(p, os.X_OK) else b"F")
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        h.update(b"\0")
    return h.hexdigest()


def reuse_tag(ctx: Path, task_name: str | None = None) -> str:
    ctx = Path(ctx).resolve()
    kind = "verifier" if ctx.name == "tests" else "env"
    name = re.sub(r"[^a-z0-9._-]+", "-", (task_name or ctx.parent.name).lower()).strip("-._")[:80] or "task"
    return f"{REPO}/{name}:{kind}-{context_hash(ctx)[:20]}"


def _key(tag: str) -> str:
    return re.sub(r"[/:]", "_", tag)


def touch_used(tag: str) -> None:
    d = STATE / "used"
    d.mkdir(parents=True, exist_ok=True)
    (d / _key(tag)).touch()


def lock_path(tag: str) -> Path:
    d = STATE / "locks"
    d.mkdir(parents=True, exist_ok=True)
    return d / (_key(tag) + ".lock")


def build_cmd(ctx: Path, tag: str) -> list[str]:
    return ["docker", "build", "-t", tag, "--label", f"cwe.reuse.context={ctx}", str(ctx)]


def image_exists(tag: str) -> bool:
    return subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", tag],
                          capture_output=True).returncode == 0


def ensure_image_sync(ctx: Path, tag: str) -> None:
    """Blocking twin of cwe_reuse_env.ensure_image (for scripts that do not run inside Harbor)."""
    touch_used(tag)
    if image_exists(tag):
        return
    with open(lock_path(tag), "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        if image_exists(tag):
            return
        r = subprocess.run(build_cmd(Path(ctx), tag), capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"cwe-reuse: docker build of {tag} failed:\n{(r.stdout + r.stderr)[-4000:]}")
