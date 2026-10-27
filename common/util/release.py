#!/usr/bin/env python3
"""Versioned releases: every deploy is a read-only copy of one commit; a `current` link names the active one.

    python3 common/util/release.py build <commit> [--repo PATH]   copy the commit's code into <releases>/<sha>/
    python3 common/util/release.py activate <sha>                 point <releases>/current at it (atomic)
    python3 common/util/release.py rollback                       point current back at the previous release
    python3 common/util/release.py list | current                 what is built, what is active
    python3 common/util/release.py verify <sha>                   read-only, data links, data root, imports
    python3 common/util/release.py remove <sha>                   delete a release that is neither current nor previous

Options before the command: --releases DIR (default $CWE_RELEASES or ~/cwe-bench-releases) and --data-root DIR
(default: the data root of the code running this tool, common/paths.py DATA_ROOT; on the VM ~/cwe-bench).

A release holds code only. Every data folder in paths.DATA_PATHS (build/, tasks/, reports/, the pipelines' out/
folders, ...) is left out of the copy and replaced by a link to the same folder under the data root, so scripts that
use repo-relative paths (`build/<slug>`) and modules that use paths.BUILD reach the same shared data from any release.
The release writes `.cwe-data-root` (read by common/paths.py and common/paths.sh) and RELEASE.json (commit, build time,
data root), byte-compiles its Python, and is made read-only. Processes keep the release they started from (paths.sh
pins the physical path); new processes started through `current` get the active one. Runbook: docs/RELEASES.md.
"""
import argparse
import getpass
import io
import json
import os
import py_compile
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

CURRENT = "current"
HISTORY = "history.tsv"


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def die(msg, code=1):
    print(f"release: {msg}", file=sys.stderr)
    sys.exit(code)


def git(repo, *args, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=not binary)
    if r.returncode != 0:
        die(f"git {' '.join(args)} failed: {(r.stderr if not binary else r.stderr.decode(errors='replace')).strip()}")
    return r.stdout


def releases_dir(a):
    return Path(a.releases or os.environ.get("CWE_RELEASES") or "~/cwe-bench-releases").expanduser()


def current_sha(rel):
    link = rel / CURRENT
    return os.readlink(link).rstrip("/").split("/")[-1] if link.is_symlink() else None


def read_history(rel):
    f = rel / HISTORY
    if not f.is_file():
        return []
    return [line.split("\t") for line in f.read_text().splitlines() if line.strip()]


# ---------- build

def make_read_only(root):
    """Remove write permission from every file and folder of the copy; data links (symlinks) are left alone."""
    for d, dirs, files in os.walk(root, topdown=False, followlinks=False):
        for name in files:
            p = os.path.join(d, name)
            if not os.path.islink(p):
                os.chmod(p, os.stat(p).st_mode & ~0o222)
        for name in dirs:
            p = os.path.join(d, name)
            if not os.path.islink(p):
                os.chmod(p, os.stat(p).st_mode & ~0o222)
    os.chmod(root, os.stat(root).st_mode & ~0o222)


def compile_code(root):
    """Byte-compile the release's own .py files (never through a data link): imports from a read-only tree stay fast."""
    n = 0
    for d, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(d, x))]
        for name in files:
            if name.endswith(".py"):
                try:
                    py_compile.compile(os.path.join(d, name), doraise=True, quiet=1)
                    n += 1
                except py_compile.PyCompileError:
                    pass                                 # a file that does not compile simply runs uncached
    return n


def cmd_build(a):
    rel, data_root = releases_dir(a), Path(a.data_root).expanduser().resolve()
    repo = Path(a.repo).expanduser().resolve()
    sha = git(repo, "rev-parse", "--short=12", f"{a.commit}^{{commit}}").strip()
    dest = rel / sha
    if (dest / "RELEASE.json").is_file():
        print(f"{sha}: already built at {dest}")
        return 0
    rel.mkdir(parents=True, exist_ok=True)
    tmp = rel / f".{sha}.partial-{os.getpid()}"
    if tmp.exists():
        shutil.rmtree(tmp)
    excludes = [f":(exclude){p}" for p in paths.DATA_PATHS]
    blob = git(repo, "archive", "--format=tar", sha, "--", ".", *excludes, binary=True)
    with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
        tf.extractall(tmp, filter="fully_trusted") if hasattr(tarfile, "data_filter") else tf.extractall(tmp)
    if not (tmp / ".cwe-bench-root").is_file():
        shutil.rmtree(tmp)
        die(f"{sha} has no .cwe-bench-root: not a cwe-bench commit")
    links = []
    for p in paths.DATA_PATHS:
        target, link = data_root / p, tmp / p
        if link.is_symlink() or link.exists():
            if link.is_dir() and not link.is_symlink():
                shutil.rmtree(link)
            else:
                link.unlink()
        if not target.exists() and a.create_missing_data:
            target.mkdir(parents=True, exist_ok=True)    # a data folder the data root does not have yet
        link.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target, link)
        links.append(p)
    (tmp / ".cwe-data-root").write_text(str(data_root) + "\n")
    meta = {
        "sha": sha,
        "commit": git(repo, "rev-parse", f"{sha}^{{commit}}").strip(),
        "commit_date": git(repo, "show", "-s", "--format=%cI", sha).strip(),
        "subject": git(repo, "show", "-s", "--format=%s", sha).strip(),
        "built_utc": utc(),
        "built_by": f"{getpass.getuser()}@{os.uname().nodename}",
        "repo": str(repo),
        "data_root": str(data_root),
        "data_links": links,
    }
    (tmp / "RELEASE.json").write_text(json.dumps(meta, indent=1) + "\n")
    n = compile_code(tmp)
    make_read_only(tmp)
    os.rename(tmp, dest)
    print(f"{sha}: built at {dest} ({n} Python files compiled, {len(links)} data links to {data_root}); "
          f"not active until `activate {sha}`")
    return 0


# ---------- activate / rollback

def activate(rel, sha, why):
    dest = rel / sha
    if not (dest / "RELEASE.json").is_file() or not (dest / ".cwe-bench-root").is_file():
        die(f"{sha}: not a built release in {rel} (run `build` first)")
    prev = current_sha(rel)
    if prev == sha:
        print(f"{sha}: already current")
        return 0
    tmp = rel / f".{CURRENT}.tmp-{os.getpid()}"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    os.symlink(sha, tmp)                                 # relative target: the folder can be moved as a whole
    os.replace(tmp, rel / CURRENT)                       # atomic: a reader sees the old or the new link, never none
    with open(rel / HISTORY, "a") as f:
        f.write(f"{utc()}\t{prev or '-'}\t{sha}\t{getpass.getuser()}\t{why}\n")
    print(f"current: {prev or '(none)'} -> {sha}. Running processes keep their release; new processes started "
          f"through {rel / CURRENT} get {sha}.")
    return 0


def cmd_activate(a):
    return activate(releases_dir(a), a.sha, "activate")


def cmd_rollback(a):
    rel = releases_dir(a)
    cur, hist = current_sha(rel), read_history(rel)
    for row in reversed(hist):
        if len(row) >= 3 and row[2] == cur and row[1] not in ("", "-"):
            return activate(rel, row[1], f"rollback from {cur}")
    die("no previous release recorded in history.tsv")


# ---------- list / current / verify / remove

def cmd_list(a):
    rel = releases_dir(a)
    cur = current_sha(rel)
    rows = []
    for d in sorted(rel.iterdir()) if rel.is_dir() else []:
        f = d / "RELEASE.json"
        if d.is_dir() and not d.is_symlink() and f.is_file():
            m = json.loads(f.read_text())
            rows.append((m.get("built_utc", ""), d.name, m.get("commit_date", "")[:10], m.get("subject", "")[:70]))
    for built, sha, cdate, subj in sorted(rows):
        print(f"{'*' if sha == cur else ' '} {sha}  built {built}  commit {cdate}  {subj}")
    if not rows:
        print(f"no releases in {rel}")
    return 0


def cmd_current(a):
    cur = current_sha(releases_dir(a))
    print(cur or "(none)")
    return 0 if cur else 1


def verify(dest, notes=None):
    """Problems with a built release, as a list of strings (empty = OK). Data folders the data root does not have are
    appended to `notes` (information, not a problem)."""
    out = []
    notes = [] if notes is None else notes
    meta_f = dest / "RELEASE.json"
    if not meta_f.is_file():
        return [f"{dest}: no RELEASE.json"]
    meta = json.loads(meta_f.read_text())
    data_root = Path(meta["data_root"])
    if (dest / ".cwe-data-root").read_text().strip() != str(data_root):
        out.append(".cwe-data-root does not match RELEASE.json")
    for p in meta.get("data_links", []):
        link = dest / p
        if not link.is_symlink():
            out.append(f"{p}: not a link")
        elif Path(os.readlink(link)) != data_root / p:
            out.append(f"{p}: links to {os.readlink(link)}, expected {data_root / p}")
        elif not link.exists():
            notes.append(f"{p}: not in the data root (the link stays dangling until the folder exists)")
    writable = []
    for d, dirs, files in os.walk(dest, followlinks=False):
        dirs[:] = [x for x in dirs if not os.path.islink(os.path.join(d, x))]
        for name in [*dirs, *files]:
            p = os.path.join(d, name)
            if not os.path.islink(p) and os.stat(p).st_mode & 0o222:
                writable.append(os.path.relpath(p, dest))
    if writable:
        out.append(f"{len(writable)} writable entries, e.g. {writable[:3]}")
    r = subprocess.run([sys.executable, "-I", "-c",
                        "import sys; sys.path.insert(0, 'common'); import paths; "
                        "print(paths.CODE_ROOT); print(paths.DATA_ROOT); print(paths.BUILD)"],
                       cwd=dest, capture_output=True, text=True, env={k: v for k, v in os.environ.items()
                                                                       if k != "CWE_DATA_ROOT"})
    lines = r.stdout.split()
    if r.returncode != 0 or len(lines) != 3:
        out.append(f"importing paths from the release failed: {r.stderr.strip()[:200]}")
    else:
        if Path(lines[0]) != dest.resolve():
            out.append(f"paths.CODE_ROOT is {lines[0]}, expected {dest.resolve()}")
        if Path(lines[1]) != data_root or Path(lines[2]) != data_root / "build":
            out.append(f"paths.DATA_ROOT/BUILD are {lines[1]} / {lines[2]}, expected {data_root}")
    sh = subprocess.run(["bash", "-c", '. common/paths.sh && echo "$CWE_ROOT|$CWE_DATA_ROOT|$CWE_BUILD"'],
                        cwd=dest, capture_output=True, text=True,
                        env={k: v for k, v in os.environ.items() if k != "CWE_DATA_ROOT"})
    want = f"{dest.resolve()}|{data_root}|{data_root / 'build'}"
    if sh.stdout.strip() != want:
        out.append(f"common/paths.sh gives {sh.stdout.strip() or sh.stderr.strip()[:200]}, expected {want}")
    return out


def cmd_verify(a):
    dest = releases_dir(a) / a.sha
    notes = []
    problems = verify(dest, notes)
    for n in notes:
        print(f"  note: {n}")
    for p in problems:
        print(f"  {p}")
    print(f"{a.sha}: {'OK' if not problems else 'NOT OK'}")
    return 0 if not problems else 1


def cmd_remove(a):
    rel = releases_dir(a)
    cur = current_sha(rel)
    hist = read_history(rel)
    prev = next((row[1] for row in reversed(hist) if len(row) >= 3 and row[2] == cur), None)
    if a.sha in (cur, prev):
        die(f"{a.sha} is the current or the previous release (rollback target); not removed")
    dest = rel / a.sha
    if not (dest / "RELEASE.json").is_file():
        die(f"{a.sha}: not a built release")
    for d, dirs, files in os.walk(dest, followlinks=False):
        if not os.path.islink(d):
            os.chmod(d, os.stat(d).st_mode | stat.S_IWUSR)
    shutil.rmtree(dest)                                  # rmtree removes links, never follows them into the data
    print(f"{a.sha}: removed")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="release", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--releases")
    ap.add_argument("--data-root", default=str(paths.DATA_ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("commit")
    p.add_argument("--repo", default=str(paths.DATA_ROOT), help="git checkout holding the commit (default: data root)")
    p.add_argument("--create-missing-data", action="store_true",
                   help="create data folders the data root does not have yet (default: leave the link dangling)")
    p = sub.add_parser("activate")
    p.add_argument("sha")
    sub.add_parser("rollback")
    sub.add_parser("list")
    sub.add_parser("current")
    p = sub.add_parser("verify")
    p.add_argument("sha")
    p = sub.add_parser("remove")
    p.add_argument("sha")
    a = ap.parse_args(argv)
    return {"build": cmd_build, "activate": cmd_activate, "rollback": cmd_rollback, "list": cmd_list,
            "current": cmd_current, "verify": cmd_verify, "remove": cmd_remove}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
