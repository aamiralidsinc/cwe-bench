"""Docker address-pool exhaustion (2026-10-29, reports/gate-compose-rca-20261029.md): the gate names the error and
retries the one trial in place after a 30-60 s backoff, instead of failing the whole stage.
Run: python3 -m pytest common/gate/tests/test_pool_retry.py"""
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "common" / "gate"))
import gate  # noqa: E402

SUBNET = ("Docker compose command failed for environment x. Stdout: Network t__abc__env_default Error "
          "failed to create network t__abc__env_default: Error response from daemon: all predefined address "
          "pools have been fully subnetted")
NO_POOL = "could not find an available, non-overlapping IPv4 address pool among the defaults to assign to the network"


def test_both_pool_messages_are_named():
    for msg in (SUBNET, NO_POOL):
        assert gate.infra_label(msg).startswith("docker address pool exhausted")
    assert gate.infra_label("network t__abc__env_default not found") == \
        "docker network vanished between create and attach"


@pytest.fixture
def harbor(tmp_path, monkeypatch):
    """A fake `harbor run`: each call takes the next outcome from `plan` (a dict for result.json, or None for no
    trial with the given stderr); the job folders land under a temp JOBS."""
    monkeypatch.setattr(gate, "JOBS", tmp_path / "jobs")
    clock = iter(range(1_800_000_000, 1_800_001_000, 7))           # distinct job names, without the real clock
    monkeypatch.setattr(gate, "time", SimpleNamespace(time=lambda: next(clock), sleep=lambda s: None))
    plan, names = [], []

    def run(cmd, **kw):
        name = cmd[cmd.index("--job-name") + 1]
        names.append(name)
        result, stderr = plan.pop(0)
        if result is not None:
            t = gate.JOBS / name / "t__abc"
            t.mkdir(parents=True)
            (t / "result.json").write_text(json.dumps(result))
        return subprocess.CompletedProcess(cmd, 1 if result is None else 0, "", stderr)
    monkeypatch.setattr(gate.subprocess, "run", run)
    return plan, names


def pool_exc():
    return {"exception_info": {"exception_type": "RuntimeError", "exception_message": SUBNET}}


def test_a_pool_exhausted_trial_is_retried_in_place_then_succeeds(harbor):
    plan, names = harbor
    plan += [(pool_exc(), ""), ({"exception_info": None}, "")]
    slept = []
    name, proc, trials = gate.harbor_attempt(Path("/x/t-s2"), "oracle", "oracle1", sleep=slept.append)
    assert len(names) == 2 and name == names[1] and len(trials) == 1
    assert len(slept) == 1 and 30 <= slept[0] <= 60


def test_no_trial_with_the_pool_message_on_stderr_is_retried(harbor):
    plan, names = harbor
    plan += [(None, NO_POOL), ({"exception_info": None}, "")]
    slept = []
    gate.harbor_attempt(Path("/x/t-s2"), "oracle", "oracle1", sleep=slept.append)
    assert len(names) == 2 and len(slept) == 1


def test_retries_stop_after_pool_retries_and_the_failure_is_labelled(harbor, monkeypatch):
    plan, names = harbor
    plan += [(pool_exc(), "")] * (gate.POOL_RETRIES + 1)
    monkeypatch.setattr(gate, "dockerfile_problems", lambda t: [])
    monkeypatch.setattr(gate, "wait_for_disk", lambda: None)
    monkeypatch.setattr(gate.ev, "collect", lambda *a, **k: {})
    with pytest.raises(gate.InfraError) as e:
        gate._run_harbor(Path("/x/t-s2"), "oracle", "oracle1")
    assert len(names) == gate.POOL_RETRIES + 1
    assert "[docker address pool exhausted" in str(e.value)


def test_other_failures_and_clean_trials_are_not_pool_retried(harbor):
    plan, names = harbor
    plan += [({"exception_info": {"exception_type": "RuntimeError", "exception_message": "boom"}}, SUBNET)]
    slept = []
    gate.harbor_attempt(Path("/x/t-s2"), "oracle", "oracle1", sleep=slept.append)   # stderr alone never counts
    plan += [({"exception_info": None}, "")]
    gate.harbor_attempt(Path("/x/t-s2"), "oracle", "oracle1", sleep=slept.append)
    assert len(names) == 2 and slept == []
