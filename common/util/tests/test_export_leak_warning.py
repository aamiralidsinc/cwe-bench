"""export_delivery.py: the file-time leak check is a WARNING, never a refusal (owner standing rule 2026-10-28: "the leak
check stays a WARNING permanently"). The result is written to <out>/leak_check.json and the report."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import export_delivery as ed  # noqa: E402


@pytest.fixture
def fake_tools(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    (tasks / "k-s2" / "environment").mkdir(parents=True)
    (tasks / "k-s2" / "task.toml").write_text('[task]\nname = "cwe-bench/k-s2"\n')
    audit = tmp_path / "audit"
    audit.mkdir()
    (audit / "trials.tsv").write_text("task\tmodel\tjob\ttrial\treward\tgrading\n")
    monkeypatch.setattr(ed.paths, "TASKS", tasks)
    monkeypatch.setattr(ed.paths, "AUDIT_DIR", audit)
    monkeypatch.setattr(ed.fairness_verdict, "delivery_blockers", lambda slug: [])
    monkeypatch.setattr(ed.cwe_reuse_tag, "reuse_tag", lambda env: "cwe-reuse/k-s2:agent-x")
    monkeypatch.setattr(ed.cwe_reuse_tag, "ensure_image_sync", lambda env, tag: None)
    monkeypatch.setattr(ed, "secret_values", lambda: ["v" * 24])
    return tmp_path


def test_leak_results_report_every_status(fake_tools, monkeypatch):
    seen = iter([{"status": "leak", "summary": "LEAK (injection files: 4)", "leaks": ["src/a.py"]}])
    monkeypatch.setattr(ed.env_leak_check, "check", lambda task, tag: next(seen))
    r = ed.leak_results(["k-s2"])
    assert r["k-s2"]["status"] == "leak" and r["k-s2"]["leaks"] == ["src/a.py"]

    def boom(task, tag):
        raise RuntimeError("no docker")
    monkeypatch.setattr(ed.env_leak_check, "check", boom)
    assert ed.leak_results(["k-s2"])["k-s2"]["status"] == "error"


def test_a_leak_is_exported_with_a_warning(fake_tools, monkeypatch, capsys):
    monkeypatch.setattr(ed.env_leak_check, "check",
                        lambda task, tag: {"status": "leak", "summary": "LEAK (injection files: 4)", "leaks": []})
    out = fake_tools / "pkg"
    monkeypatch.setattr(sys, "argv", ["export_delivery.py", str(out), "k-s2", "--name", "k-s2=k-task"])
    ed.main()                                            # no SystemExit: never a refusal
    assert (out / "tasks" / "k-task" / "task.toml").is_file()
    assert json.loads((out / "leak_check.json").read_text())["k-s2"]["status"] == "leak"
    rep = (out / "EXPORT-REPORT.md").read_text()
    assert "## File-time leak check (a warning, never a refusal)" in rep and "WARNING k-s2: leak check leak" in rep
    assert "WARNING: k-s2: file-time leak check leak" in capsys.readouterr().err
