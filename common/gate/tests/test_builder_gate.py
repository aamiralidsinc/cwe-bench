"""Gate limits and builders (2026-10-28, pipeline fixes item 3): the limits file wins over the environment (h4), a
builder's nop runs use the builder lane (h2), and a builder may run only the static and nop stages (h1).
Run: python3 -m pytest common/gate/tests/test_builder_gate.py"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "common" / "gate"))
import gate  # noqa: E402


@pytest.fixture
def limits(tmp_path, monkeypatch):
    f = tmp_path / "limits.env"
    monkeypatch.setattr(gate, "GATE_LIMITS_FILE", f)
    monkeypatch.setattr(gate, "JOBS", tmp_path / "gate-jobs")      # evidence of a failed setup lands beside it
    if hasattr(gate, "paths"):                                      # data-root lookups (item3-repair), if present
        monkeypatch.setattr(gate.paths, "TASKS", tmp_path / "tasks", raising=False)
        monkeypatch.setattr(gate.paths, "BUILD", tmp_path / "build", raising=False)
    monkeypatch.setattr(gate, "_IGNORED_ENV", set())
    for k in ("GATE_GLOBAL_SLOTS", "GATE_PARALLEL", "GATE_BUILDER_RUN_SLOTS", "CWE_BUILD_RUN"):
        monkeypatch.delenv(k, raising=False)
    return f


def test_the_limits_file_wins_over_the_environment(limits, monkeypatch, capsys):
    limits.write_text("# comment\nGATE_GLOBAL_SLOTS=48\n")
    monkeypatch.setenv("GATE_GLOBAL_SLOTS", "0")                 # spinnaker-s2's bypass: 0 disabled the cap
    assert gate.gate_limit("GATE_GLOBAL_SLOTS", 60) == 48
    monkeypatch.setenv("GATE_GLOBAL_SLOTS", "5")                 # lower, or higher: the file decides either way
    assert gate.gate_limit("GATE_GLOBAL_SLOTS", 60) == 48
    out = capsys.readouterr().out
    assert out.count("ignoring GATE_GLOBAL_SLOTS=0 from the environment") == 1   # said once per name
    monkeypatch.setenv("GATE_GLOBAL_SLOTS", "48")                # the same value: nothing ignored
    assert gate.gate_limit("GATE_GLOBAL_SLOTS", 60) == 48


def test_the_environment_still_counts_where_the_file_is_silent_except_for_builders(limits, monkeypatch, capsys):
    limits.write_text("GATE_GLOBAL_SLOTS=48\n")
    monkeypatch.setenv("GATE_PARALLEL", "4")                     # re-gate throttles (regate_queue.py) keep working
    assert gate.gate_limit("GATE_PARALLEL", 0) == 4
    assert gate.gate_limit("GATE_TASK_SLOTS", 10) == 10
    monkeypatch.setenv("CWE_BUILD_RUN", "x-s2:1:2")              # a builder's environment is never read
    monkeypatch.setenv("GATE_BUILDER_RUN_SLOTS", "500")
    assert gate.gate_limit("GATE_PARALLEL", 0) == 0
    assert gate.gate_limit("GATE_BUILDER_RUN_SLOTS", 8) == 8
    assert "a builder never sets a gate limit" in capsys.readouterr().out


def slot_dirs(tmp_path, monkeypatch):
    shared, lane = tmp_path / "gate", tmp_path / "gate-builder"
    monkeypatch.setattr(gate, "GATE_SLOTS_DIR", shared)
    monkeypatch.setattr(gate, "GATE_BUILDER_SLOTS_DIR", lane)
    monkeypatch.setattr(gate.diskguard, "wait", lambda *a, **k: None)
    return shared, lane


def test_a_builder_takes_a_lane_slot_never_a_shared_one(limits, tmp_path, monkeypatch):
    shared, lane = slot_dirs(tmp_path, monkeypatch)
    limits.write_text("GATE_GLOBAL_SLOTS=1\nGATE_BUILDER_RUN_SLOTS=2\n")
    monkeypatch.setenv("CWE_BUILD_RUN", "x-s2:1:2")
    with gate.global_slot() as a, gate.global_slot() as b:      # two builder runs at once: both lane slots
        assert Path(a.f.name).parent == lane and Path(b.f.name).parent == lane
        assert Path(a.f.name).name != Path(b.f.name).name
    assert not any(shared.glob("slot-*.lock"))


def test_post_build_gates_keep_the_shared_slots_and_a_zero_lane_falls_back(limits, tmp_path, monkeypatch):
    shared, lane = slot_dirs(tmp_path, monkeypatch)
    limits.write_text("GATE_GLOBAL_SLOTS=3\n")
    with gate.global_slot() as a:                               # no build tag: the shared slots
        assert Path(a.f.name).parent == shared
    limits.write_text("GATE_GLOBAL_SLOTS=3\nGATE_BUILDER_RUN_SLOTS=0\n")
    monkeypatch.setenv("CWE_BUILD_RUN", "x-s2:1:2")
    with gate.global_slot() as a:                               # lane switched off: a builder uses the shared slots
        assert Path(a.f.name).parent == shared


@pytest.mark.parametrize("only,refused", [(None, True), ("oracle", True), ("patches", True),
                                          ("static", False), ("nop", False)])
def test_a_builder_runs_only_static_and_nop(limits, tmp_path, monkeypatch, capsys, only, refused):
    monkeypatch.setattr(gate, "ROOT", tmp_path)                 # no task here: an allowed stage fails at setup
    monkeypatch.setenv("CWE_BUILD_RUN", "x-s2:1:2")
    monkeypatch.setattr(sys, "argv", ["gate.py", "x-s2", *(["--only", only] if only else [])])
    rc = gate.main()
    out = capsys.readouterr().out
    if refused:
        assert rc == 3 and "REFUSED: a builder runs only --only static and --only nop" in out
        assert not (tmp_path / "build").exists()                # nothing written
    else:
        assert "REFUSED" not in out and rc == 1                 # reached the stage setup (no task directory)


def test_without_the_build_tag_every_stage_runs(limits, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["gate.py", "x-s2", "--only", "oracle"])
    assert gate.main() == 1 and "REFUSED" not in capsys.readouterr().out
