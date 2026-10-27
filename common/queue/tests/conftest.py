"""Fixtures: a fake repo tree (build/, tasks/, jobs/) behind common/paths.py, a temp queue.db and a temp config."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

QUEUE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(QUEUE))

import config  # noqa: E402
import reconcile  # noqa: E402,F401  (puts common/ on sys.path)
import paths  # noqa: E402  (put on sys.path by the queue modules)
import qdb  # noqa: E402


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A fake repo root; paths.ROOT/BUILD/TASKS point at it for the duration of a test."""
    r = tmp_path / "repo"
    for d in ("build", "tasks", "jobs"):
        (r / d).mkdir(parents=True)
    (r / ".cwe-bench-root").write_text("test root\n")
    monkeypatch.setattr(paths, "ROOT", r)
    monkeypatch.setattr(paths, "BUILD", r / "build")
    monkeypatch.setattr(paths, "TASKS", r / "tasks")
    import reconcile
    import taskstate
    monkeypatch.setattr(taskstate.trial_state, "ROOT", r)
    monkeypatch.setattr(taskstate.fairness_verdict, "ROOT", r)
    monkeypatch.setattr(paths, "PIPELINES", r / "pipelines")
    import dispatch
    monkeypatch.setattr(dispatch.diskguard, "ok", lambda name: True)      # tests set disk floors explicitly
    reconcile._digest_cache.clear()
    return r


def write_config(tmp_path, root, extra=""):
    f = tmp_path / "queue.toml"
    f.write_text(f'db = "{tmp_path / "queue.db"}"\nlog_dir = "{tmp_path / "logs"}"\njobs_dir = "{root / "jobs"}"\n'
                 'require_adoption = false\n'
                 + extra)
    return config.load(f)


@pytest.fixture
def cfg(tmp_path, root):
    c = write_config(tmp_path, root, "[dispatch]\nstart_spacing_sec = 0\nfill_spacing_sec = 0\n"
                                     "max_starts_per_tick = 50\n")
    c["phase4"]["enabled"] = False                     # phase-4 rules are tested on their own (test_phase4.py)
    return c


@pytest.fixture
def conn(cfg):
    return qdb.connect(cfg["db"])


def set_mtime(p, t):
    os.utime(p, (t, t))


def make_task(root, slug, files):
    """tasks/<slug>/tests/<rel> = text for each item of files."""
    for rel, text in files.items():
        p = root / "tasks" / slug / "tests" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    (root / "build" / slug).mkdir(parents=True, exist_ok=True)
    return root / "tasks" / slug


def make_trial(root, slug, n, finished, results=None, code=True):
    """A finished, graded trial: jobs/<slug>-m-r<n>/<slug>__T<n>/."""
    t = root / "jobs" / f"{slug}-m-r{n}" / f"{slug}__T{n}"
    (t / "verifier").mkdir(parents=True)
    (t / "config.json").write_text(json.dumps({"task": {"path": f"/x/tasks/{slug}"}}))
    (t / "result.json").write_text(json.dumps({"finished_at": qdb.utc(finished),
                                               "verifier_result": {"rewards": {"reward": 0.0}}}))
    (t / "verifier" / "results.json").write_text(json.dumps(results or {"security": {}, "functional": {}}))
    if code:
        (t / "final-code").mkdir()
        (t / "final-code" / "changes.patch").write_text("")
    return t


def gate_log(root, slug, when, text):
    with open(root / "build" / slug / "postbuild.log", "a") as f:
        f.write(f"{qdb.utc(when)} {slug} RESULT: {text}\n")


def write_fingerprint(root, slug, sha=None):
    sys.path.insert(0, str(Path(paths.__file__).parent / "gate"))
    import fingerprint
    sha = sha or fingerprint.digest(slug)[0]
    (root / "build" / slug / "gate_fingerprint.json").write_text(json.dumps({"sha256": sha, "written_utc": qdb.utc()}))


def wait_for(pred, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False
