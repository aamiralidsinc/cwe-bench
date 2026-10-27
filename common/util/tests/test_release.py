"""Versioned releases (common/util/release.py) and the code/data split in common/paths.py and common/paths.sh."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "common" / "util"))
sys.path.insert(0, str(REPO / "common"))
import release  # noqa: E402


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                            GIT_COMMITTER_EMAIL="t@t"))


@pytest.fixture
def world(tmp_path):
    """A source repo with code and tracked data, an (untracked) data root and a releases folder."""
    src = tmp_path / "src"
    (src / "common" / "util").mkdir(parents=True)
    (src / ".cwe-bench-root").write_text("root\n")
    shutil.copy(REPO / "common" / "paths.py", src / "common" / "paths.py")
    shutil.copy(REPO / "common" / "paths.sh", src / "common" / "paths.sh")
    (src / "common" / "util" / "hello.py").write_text("X = 1\n")
    (src / "build" / "t1").mkdir(parents=True)
    (src / "build" / "t1" / "rec.txt").write_text("tracked data\n")
    (src / "pipelines" / "router" / "out").mkdir(parents=True)
    (src / "pipelines" / "router" / "out" / "state.txt").write_text("data\n")
    (src / "pipelines" / "router" / "tool.sh").write_text("echo hi\n")
    subprocess.run(["git", "init", "-q", str(src)], check=True)
    git(src, "add", "-A")
    git(src, "commit", "-qm", "one")
    data = tmp_path / "data"
    (data / "build" / "t1").mkdir(parents=True)
    (data / "build" / "t1" / "live.txt").write_text("live data\n")
    rel = tmp_path / "releases"
    yield src, data, rel
    for d, dirs, files in os.walk(rel, followlinks=False):  # read-only trees: make them removable
        if not os.path.islink(d):
            os.chmod(d, 0o755)


def run(rel, data, *args):
    return release.main(["--releases", str(rel), "--data-root", str(data), *args])


def head(src):
    return subprocess.run(["git", "-C", str(src), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                          text=True).stdout.strip()


def test_build_is_code_only_read_only_and_links_data(world):
    src, data, rel = world
    assert run(rel, data, "build", "HEAD", "--repo", str(src)) == 0
    sha = head(src)
    dest = rel / sha
    assert (dest / "common" / "util" / "hello.py").is_file()
    assert (dest / "pipelines" / "router" / "tool.sh").is_file()
    # data folders are links to the data root, never the commit's tracked copies
    assert (dest / "build").is_symlink() and (dest / "build" / "t1" / "live.txt").is_file()
    assert not (dest / "build" / "t1" / "rec.txt").exists()
    assert (dest / "pipelines" / "router" / "out").is_symlink()
    meta = json.loads((dest / "RELEASE.json").read_text())
    assert meta["sha"] == sha and meta["data_root"] == str(data.resolve())
    assert (dest / ".cwe-data-root").read_text().strip() == str(data.resolve())
    with pytest.raises(PermissionError):
        (dest / "common" / "util" / "new.py").write_text("x")
    with pytest.raises(PermissionError):
        (dest / "common" / "util" / "hello.py").write_text("x")
    (dest / "build" / "t1" / "written.txt").write_text("data stays writable\n")
    assert (data / "build" / "t1" / "written.txt").is_file()
    assert any((dest / "common" / "util" / "__pycache__").iterdir())
    notes = []
    assert release.verify(dest, notes) == []
    assert any("sourcer/index" in n for n in notes)                       # absent in this data root: a note only
    assert run(rel, data, "build", "HEAD", "--repo", str(src)) == 0          # idempotent


def test_activate_and_rollback_are_atomic_link_swaps(world):
    src, data, rel = world
    run(rel, data, "build", "HEAD", "--repo", str(src))
    first = head(src)
    (src / "common" / "util" / "hello.py").write_text("X = 2\n")
    git(src, "commit", "-qam", "two")
    run(rel, data, "build", "HEAD", "--repo", str(src))
    second = head(src)
    assert run(rel, data, "activate", first) == 0
    assert os.readlink(rel / "current") == first
    assert run(rel, data, "activate", second) == 0
    assert os.readlink(rel / "current") == second
    assert (rel / "current" / "common" / "util" / "hello.py").read_text() == "X = 2\n"
    assert run(rel, data, "rollback") == 0
    assert os.readlink(rel / "current") == first
    rows = [line.split("\t") for line in (rel / "history.tsv").read_text().splitlines()]
    assert [r[2] for r in rows] == [first, second, first]
    with pytest.raises(SystemExit):
        run(rel, data, "activate", "0123456789ab")                         # not built: refused


def test_remove_keeps_current_and_previous(world):
    src, data, rel = world
    shas = []
    for i in range(3):
        (src / "common" / "util" / "hello.py").write_text(f"X = {i + 10}\n")
        git(src, "commit", "-qam", f"c{i}")
        run(rel, data, "build", "HEAD", "--repo", str(src))
        shas.append(head(src))
    run(rel, data, "activate", shas[1])
    run(rel, data, "activate", shas[2])
    with pytest.raises(SystemExit):
        run(rel, data, "remove", shas[2])                                  # current
    with pytest.raises(SystemExit):
        run(rel, data, "remove", shas[1])                                  # rollback target
    assert run(rel, data, "remove", shas[0]) == 0
    assert not (rel / shas[0]).exists()
    assert (data / "build" / "t1" / "live.txt").is_file()                  # removing never touches the data


def test_paths_default_and_override(tmp_path, monkeypatch):
    root = tmp_path / "plain"
    (root / "common").mkdir(parents=True)
    (root / ".cwe-bench-root").write_text("x\n")
    shutil.copy(REPO / "common" / "paths.py", root / "common" / "paths.py")
    shutil.copy(REPO / "common" / "paths.sh", root / "common" / "paths.sh")
    code = ("import sys; sys.path.insert(0, 'common'); import paths; "
            "print(paths.ROOT, paths.DATA_ROOT, paths.BUILD, paths.SIBLING_OUT, sep='|')")
    env = {k: v for k, v in os.environ.items() if k != "CWE_DATA_ROOT"}
    out = subprocess.run([sys.executable, "-I", "-c", code], cwd=root, capture_output=True, text=True, env=env)
    r = str(root.resolve())
    assert out.stdout.strip() == f"{r}|{r}|{r}/build|{r}/pipelines/sibling/out"     # a plain checkout: unchanged
    out = subprocess.run([sys.executable, "-I", "-c", code], cwd=root, capture_output=True, text=True,
                         env=dict(env, CWE_DATA_ROOT="/srv/data"))
    assert out.stdout.strip() == f"{r}|/srv/data|/srv/data/build|/srv/data/pipelines/sibling/out"
    sh = subprocess.run(["bash", "-c", '. common/paths.sh && echo "$CWE_ROOT|$CWE_DATA_ROOT|$CWE_BUILD"'],
                        cwd=root, capture_output=True, text=True, env=env)
    assert sh.stdout.strip() == f"{r}|{r}|{r}/build"


def test_paths_sh_pins_the_physical_release(world):
    """A script started through `current` keeps the release it started with when current is repointed."""
    src, data, rel = world
    run(rel, data, "build", "HEAD", "--repo", str(src))
    first = head(src)
    run(rel, data, "activate", first)
    sh = subprocess.run(["bash", "-c", '. common/paths.sh && echo "$CWE_ROOT"'], cwd=rel / "current",
                        capture_output=True, text=True,
                        env={k: v for k, v in os.environ.items() if k != "CWE_DATA_ROOT"})
    assert sh.stdout.strip() == str((rel / first).resolve())
