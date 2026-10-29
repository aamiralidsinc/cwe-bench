"""gate.py and the regrade tool read tasks/ and build/ under the data root, so CWE_DATA_ROOT=<scratch> gates a scratch
copy (the repair step validates its edits this way, 2026-10-28). Run: python3 -m pytest common/gate/tests"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_gate_reads_and_writes_under_cwe_data_root(tmp_path):
    slug = "scratch-only-task"
    (tmp_path / "build" / slug).mkdir(parents=True)
    (tmp_path / "tasks" / slug).mkdir(parents=True)
    (tmp_path / "build" / slug / "manifest.json").write_text("{not json")       # fails at setup, before Docker
    env = dict(os.environ, CWE_DATA_ROOT=str(tmp_path))
    p = subprocess.run([sys.executable, "-I", str(REPO / "common/gate/gate.py"), slug, "--only", "static"],
                       cwd=str(REPO), env=env, capture_output=True, text=True, timeout=300)
    assert p.returncode == 1, p.stdout + p.stderr
    rep = json.loads((tmp_path / "build" / slug / "gate_report.partial.json").read_text())
    assert "manifest.json is not valid JSON" in rep["failure"]                # it found the scratch task and build
    assert not (REPO / "build" / slug).exists()                               # nothing written under the code root


def test_gate_without_the_scratch_task_names_the_scratch_path(tmp_path):
    slug = "scratch-missing-task"
    (tmp_path / "build" / slug).mkdir(parents=True)
    env = dict(os.environ, CWE_DATA_ROOT=str(tmp_path))
    subprocess.run([sys.executable, "-I", str(REPO / "common/gate/gate.py"), slug, "--only", "static"],
                   cwd=str(REPO), env=env, capture_output=True, text=True, timeout=300)
    rep = json.loads((tmp_path / "build" / slug / "gate_report.partial.json").read_text())
    assert str(tmp_path / "tasks" / slug) in rep["failure"]


def test_regrade_tool_resolves_the_task_under_the_data_root():
    text = (REPO / "common/audit/regrade_from_code.py").read_text()
    assert "tdir = paths.TASKS / task" in text and 'info["tests_hash"] = tests_hash' in text
