"""Regrade network parity with Harbor's grading, the empty-patch guard, and harvest's failure handling."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

AUDIT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, AUDIT / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(AUDIT))
    spec.loader.exec_module(m)
    return m


rg = load("regrade_from_code")
hv = load("harvest_code")


class FakeDocker:
    def __init__(self, exists=False):
        self.exists, self.calls = exists, []

    def __call__(self, *a):
        self.calls.append(a)
        rc = 0
        if a[:3] == ("docker", "network", "inspect"):
            rc = 0 if self.exists else 1
        elif a[:3] == ("docker", "network", "create"):
            self.exists = True
        return subprocess.CompletedProcess(a, rc, "", "")


def test_no_network_uses_an_internal_network_not_none():
    d = FakeDocker()
    args = rg.network_args("no-network", run=d)
    assert args == ["--network", rg.NO_NETWORK] and "none" not in args
    create = [c for c in d.calls if c[:3] == ("docker", "network", "create")]
    assert create and "--internal" in create[0]          # a bridge address, no route out
    d2 = FakeDocker(exists=True)
    assert rg.network_args("no-network", run=d2) == ["--network", rg.NO_NETWORK]
    assert not [c for c in d2.calls if c[:3] == ("docker", "network", "create")]


def test_public_keeps_the_default_bridge_and_unknown_modes_stop():
    assert rg.network_args("public", run=FakeDocker()) == []
    with pytest.raises(SystemExit):
        rg.network_args("allowlist", run=FakeDocker())


def test_empty_patch_next_to_a_collected_workspace_is_refused(tmp_path):
    t = tmp_path / "task__abc"
    (t / "final-code").mkdir(parents=True)
    (t / "final-code" / "changes.patch").write_text("")
    rg.refuse_empty_patch(t)                              # no workspace: an empty patch can be a real no-op
    (t / "artifacts" / "workspace" / "core").mkdir(parents=True)
    (t / "artifacts" / "workspace" / "core" / "x.go").write_text("package core\n")
    with pytest.raises(SystemExit, match="harvest likely missed"):
        rg.refuse_empty_patch(t)
    (t / "final-code" / "changes.patch").write_text("--- a/x\n+++ b/x\n")
    rg.refuse_empty_patch(t)


def test_harvest_writes_nothing_when_docker_diff_fails(tmp_path, monkeypatch):
    def fake_sh(*a, binary=False):
        if a[:2] == ("docker", "inspect"):
            return 0, "sha256:img\n"
        if a[:2] == ("docker", "diff"):
            return 1, ""
        return 0, b"" if binary else ""
    monkeypatch.setattr(hv, "sh", fake_sh)
    r = hv.harvest(tmp_path / "t__x", "after-run", "ctr", tmp_path / "out")
    assert "error" in r and not (tmp_path / "out").exists()


def test_harvest_retries_then_refuses_when_no_added_file_can_be_read(tmp_path, monkeypatch):
    def fake_sh(*a, binary=False):
        if a[:2] == ("docker", "inspect"):
            return 0, "sha256:img\n"
        if a[:2] == ("docker", "diff"):
            return 0, "C /workspace/core\nA /workspace/core/x.go\n"
        return 0, b"" if binary else ""
    monkeypatch.setattr(hv, "sh", fake_sh)
    monkeypatch.setattr(hv, "read_file", lambda c, p: None)   # docker cp failing under load
    monkeypatch.setattr(hv.time, "sleep", lambda s: None)
    r = hv.harvest(tmp_path / "t__x", "after-run", "ctr", tmp_path / "out")
    assert "no file could be read" in r["error"] and not (tmp_path / "out").exists()


def test_regrade_check_flags_a_functional_test_lost_with_the_same_code(tmp_path):
    import json
    sys.path.insert(0, str(AUDIT.parent / "queue"))
    import checks
    o, n = tmp_path / "o.json", tmp_path / "n.json"
    o.write_text(json.dumps({"functional": {"f::TestA": "passed", "f::TestB": "passed", "f::TestC": "failed"}}))
    n.write_text(json.dumps({"functional": {"f::TestA": "failed", "f::TestB": {"status": "passed"}, "f::TestC": "failed"}}))
    assert checks.functional_drops(o, n) == ["f::TestA"]
    n.write_text(json.dumps({"functional": {"f::TestA": "passed", "f::TestB": "passed"}}))
    assert checks.functional_drops(o, n) == []


def test_harvest_keeps_the_source_diff_when_caches_and_build_output_crowd_the_cap(tmp_path, monkeypatch):
    """core-s2 / mollieplugin-s2 (var/cache under tests/) and deepseek-harness-s2 (a compiled lib/) lost their source
    diffs to the 500-file cap on 2026-10-28: caches are skipped first, and source edits are read before new folders."""
    cache = [f"A /workspace/tests/Fixtures/app/var/cache/test/c{i}.php" for i in range(700)]
    built = ["A /workspace/apps/cli/lib"] + [f"A /workspace/apps/cli/lib/m{i}.js" for i in range(600)] + \
        [f"A /workspace/apps/cli/lib/m{i}.js.map" for i in range(50)]
    src = ["C /workspace/src", "C /workspace/src/Serializer", "C /workspace/src/Serializer/AbstractItemNormalizer.php",
           "A /workspace/src/Serializer/Guard.php", "D /workspace/src/Old.php"]
    diff = "\n".join(cache + built + src) + "\n"

    def fake_sh(*a, binary=False):
        if a[:2] == ("docker", "inspect"):
            return 0, "sha256:img\n"
        if a[:2] == ("docker", "diff"):
            return 0, diff
        return 0, b"" if binary else ""
    reads = []

    def fake_read(container, path):
        reads.append(path)
        if path in ("/workspace/src", "/workspace/src/Serializer", "/workspace/apps/cli/lib"):
            return None                                      # a directory
        if container.startswith("harvest-orig"):
            return None if path.endswith("Guard.php") else b"old\n"
        return None if path.endswith("Old.php") else b"new\n"
    monkeypatch.setattr(hv, "sh", fake_sh)
    monkeypatch.setattr(hv, "read_file", fake_read)
    monkeypatch.setattr(hv, "save_tmp_logs", lambda out, c: 0)
    info = hv.harvest(tmp_path / "t__x", "after-run", "ctr", tmp_path / "out")
    patch = (tmp_path / "out" / "changes.patch").read_text()
    head = patch.split("lib/m0.js")[0]                       # everything diffed before the first build-output file
    for f in ("Serializer/AbstractItemNormalizer.php", "Serializer/Guard.php", "Old.php"):
        assert f"/workspace/src/{f}" in head
    assert "var/cache" not in patch and ".js.map" not in patch
    assert info["skipped_build_or_cache_paths"] == 750 and info["truncated"] and info["not_read"] == 103
    assert not any(p in reads for p in ("/workspace/src", "/workspace/src/Serializer"))   # directories never read
    assert reads.index("/workspace/src/Serializer/AbstractItemNormalizer.php") < reads.index("/workspace/apps/cli/lib/m0.js")


def test_prioritise_orders_edits_before_new_folders():
    ch = [("A", "/app/out"), ("A", "/app/out/a.js"), ("A", "/app/x.py"), ("C", "/app/y.py"), ("C", "/app")]
    assert hv.prioritise(ch) == [("C", "/app/y.py"), ("A", "/app/x.py"), ("A", "/app/out/a.js")]
