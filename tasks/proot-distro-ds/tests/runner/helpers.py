"""Hidden behavioural tests: shared helpers (also used by the functional suite)."""
import io
import os
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

WORKSPACE = os.environ.get("PD_WORKSPACE", "/workspace")
ENTRY = Path(__file__).resolve().parent / "pd_entry.py"


class PDEnv:
    """An isolated proot-distro runtime plus a harmless directory outside it."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.bin = self.root / "bin"
        self.home = self.root / "home"
        self.data = self.root / "data"
        self.cache = self.root / "cache"
        self.outside = self.root / "outside"
        for d in (self.bin, self.home, self.outside):
            d.mkdir(parents=True, exist_ok=True)
        # The CLI probes for the proot utility at startup. No operation these
        # tests drive executes it.
        proot = self.bin / "proot"
        proot.write_text("#!/bin/sh\nexit 0\n")
        proot.chmod(0o755)

    @property
    def containers(self) -> Path:
        return self.data / "proot-distro" / "containers"

    def rootfs(self, name: str) -> Path:
        return self.containers / name / "rootfs"

    def env(self) -> dict:
        return {
            "PATH": f"{self.bin}:/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.home),
            "XDG_DATA_HOME": str(self.data),
            "XDG_CACHE_HOME": str(self.cache),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TZ": "UTC",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PD_WORKSPACE": WORKSPACE,
        }

    def run(self, *args):
        """Run the real CLI entry point with an isolated runtime tree."""
        return subprocess.run(
            [sys.executable, str(ENTRY), *args],
            env=self.env(), cwd=str(self.root),
            capture_output=True, text=True, timeout=300,
        )


def make_tar(path, entries):
    """Write a tar from (kind, name, ...) tuples: d/s/l/f (dir/sym/hardlink/file)."""
    with tarfile.open(path, "w") as tf:
        for kind, name, *rest in entries:
            ti = tarfile.TarInfo(name)
            if kind == "d":
                ti.type = tarfile.DIRTYPE
                ti.mode = rest[0] if rest else 0o755
                tf.addfile(ti)
            elif kind == "s":
                ti.type = tarfile.SYMTYPE
                ti.linkname = rest[0]
                ti.mode = 0o777
                tf.addfile(ti)
            elif kind == "l":
                ti.type = tarfile.LNKTYPE
                ti.linkname = rest[0]
                ti.mode = 0o644
                tf.addfile(ti)
            elif kind == "f":
                data = rest[0]
                ti.size = len(data)
                ti.mode = rest[1] if len(rest) > 1 else 0o644
                tf.addfile(ti, io.BytesIO(data))
            else:
                raise ValueError(f"unknown entry kind {kind!r}")


def snapshot(root):
    """Record everything about a directory tree: type, mode, link target, bytes."""
    root = Path(root)
    out = {}
    if not root.exists():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        for name in sorted(dirnames) + sorted(filenames):
            p = Path(dirpath) / name
            rel = str(p.relative_to(root))
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                out[rel] = ("link", os.readlink(p))
            elif stat.S_ISDIR(st.st_mode):
                out[rel] = ("dir", stat.S_IMODE(st.st_mode))
            else:
                out[rel] = ("file", stat.S_IMODE(st.st_mode), p.read_bytes())
    return out


def write_marker(directory, name, marker):
    p = Path(directory) / name
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(marker, bytes):
        p.write_bytes(marker)
    else:
        p.write_text(marker)
    return p


def read_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError:
        return b""
