"""File-time leak rollout (2026-10-28): transformer, static rule, leak judge, harness reset script, ledger notes,
delivery refusal, gate warnings. Run: python3 -m pytest common/gate/tests/test_tsleak.py"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
for p in ("common/gate", "common/builder", "common/harbor_ext", "common/audit", "common/util", "common"):
    sys.path.insert(0, str(REPO / p))

import cwe_tree_reset  # noqa: E402
import env_leak_check  # noqa: E402
import static_leak  # noqa: E402
import tree_time_reset as ttr  # noqa: E402

TEMPLATE = (REPO / "common/builder/templates/environment.Dockerfile").read_text()

OLD_B2 = """FROM node:22-bookworm-slim
WORKDIR /workspace
RUN git init -q . && git fetch -q --depth 1 origin abc && git checkout -q FETCH_HEAD
COPY injection.patch /tmp/injection.patch
RUN patch -p1 -d /workspace < /tmp/injection.patch && rm -f /tmp/injection.patch
# --- fixed boilerplate: uid-1000 agent user (B2) ---
RUN if getent passwd 1000 >/dev/null; then \\
        u=$(getent passwd 1000 | cut -d: -f1); \\
    else useradd -m -d /home/agent -u 1000 -U -s /bin/bash agent; fi; \\
    mkdir -p /home/agent && chown -R agent:agent /home/agent /workspace /go
USER agent
ENV HOME=/home/agent
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \\
    && test -x /home/agent/.local/bin/claude
USER root
RUN ln -sf /home/agent/.local/bin/claude /usr/local/bin/claude \\
    && su agent -c 'claude --version'
USER agent
WORKDIR /workspace
RUN rm -rf /workspace/.git \\
    && git init -q -b main \\
    && git -c user.name=task -c user.email=task@localhost add -A \\
    && git -c user.name=task -c user.email=task@localhost commit -qm "Starting project"
"""

OLD_APP = """FROM python:3.12-slim
WORKDIR /app
RUN git clone -q https://example.invalid/x.git /app && cd /app && git checkout -q abc
COPY injection.patch /tmp/i.patch
RUN patch -p1 -d /app < /tmp/i.patch
RUN pip install -e .
USER app
CMD ["bash"]
"""


def test_template_is_already_normalised():
    assert ttr.plan(TEMPLATE)["action"] == "none"
    assert 'find /workspace -xdev -exec touch -h -d "@${TREE_EPOCH}" {} +' in TEMPLATE
    assert "--no-backup-if-mismatch" in TEMPLATE


def test_b2_mode_appends_to_the_chown_and_is_idempotent(tmp_path):
    new, p = ttr.apply(OLD_B2)
    assert p["action"] == "b2" and p["root"] == "/workspace" and not p["after_a6"]
    assert "chown -R agent:agent /home/agent /workspace /go \\\n" \
           '    && find /workspace -xdev -exec touch -h -d "@${TREE_EPOCH}" {} +\n' in new
    assert new.index("ARG TREE_EPOCH=1704067200") < new.index("RUN if getent passwd")
    assert ttr.apply(new)[0] == new
    df = tmp_path / "Dockerfile"
    df.write_text(OLD_B2)
    assert static_leak.classify(df)["static_leak"] == "yes"
    df.write_text(new)
    assert static_leak.classify(df)["static_leak"] == "no-normalised"


def test_own_step_for_an_app_task_runs_as_root_and_restores_the_user():
    new, p = ttr.apply(OLD_APP)
    assert p["action"] == "own" and p["root"] == "/app"
    tail = new[new.index("RUN pip install"):]
    # inserted after the last write, as root, then back to the earlier USER? (USER app comes after: nothing to restore)
    assert 'RUN find /app -xdev -exec touch -h -d "@${TREE_EPOCH}" {} +' in tail
    assert ttr.apply(new)[0] == new


def test_own_step_before_the_last_baseline_with_a_write_after_b2():
    text = OLD_B2.replace("USER agent\nENV HOME", "RUN cd /workspace && npm ci\nUSER agent\nENV HOME", 1)
    new, p = ttr.apply(text)
    assert p["action"] == "own"
    block = new[:new.index('RUN rm -rf /workspace/.git')]
    assert block.rstrip().endswith("USER agent")            # USER root ... RUN find ... USER agent, then A6
    assert "USER root\nARG TREE_EPOCH=1704067200\nRUN find /workspace" in new


def test_two_baselines_use_the_last_one():
    text = OLD_B2.replace("RUN patch -p1 -d /workspace < /tmp/injection.patch && rm -f /tmp/injection.patch",
                          'RUN patch -p1 -d /workspace < /tmp/injection.patch && rm -rf /workspace/.git && git init -q '
                          '&& git -c user.name=t -c user.email=t@l commit -qm "Starting project"')
    new, p = ttr.apply(text)
    assert p["action"] == "b2"


def test_postbuild_refuses_when_a_fingerprint_exists(tmp_path, monkeypatch):
    import paths
    monkeypatch.setattr(paths, "TASKS", tmp_path / "tasks")
    monkeypatch.setattr(paths, "BUILD", tmp_path / "build")
    env = tmp_path / "tasks" / "t-s2" / "environment"
    env.mkdir(parents=True)
    (env / "Dockerfile").write_text(OLD_B2)
    (tmp_path / "build" / "t-s2").mkdir(parents=True)
    (tmp_path / "build" / "t-s2" / "gate_fingerprint.json").write_text("{}")
    assert ttr.postbuild("t-s2") == 0
    assert (env / "Dockerfile").read_text() == OLD_B2
    (tmp_path / "build" / "t-s2" / "gate_fingerprint.json").unlink()
    assert ttr.postbuild("t-s2") == 0
    assert "TREE_EPOCH" in (env / "Dockerfile").read_text()
    assert (tmp_path / "build" / "t-s2" / "environment.Dockerfile.pre-b2b").read_text() == OLD_B2
    assert list(env.iterdir()) == [env / "Dockerfile"]      # nothing new in the build context
    log = (tmp_path / "build" / "t-s2" / "postbuild.log").read_text()
    assert "skipped: the task already has a gate fingerprint" in log and "inserted the file-time reset" in log


def test_static_warnings(tmp_path):
    env = tmp_path / "t" / "environment"
    env.mkdir(parents=True)
    (env / "Dockerfile").write_text(OLD_B2)
    (env / "injection.patch").write_text("")
    assert len(static_leak.warnings(tmp_path / "t")) == 1
    (env / "Dockerfile").write_text(ttr.apply(OLD_B2)[0])
    assert static_leak.warnings(tmp_path / "t") == []


def _probe(**kw):
    d = {"n_injected": 4, "n_tracked": 100, "git_baseline": True,
         "mtime": {"cohort": {"pure_recall": 0, "distinct_values": 1, "injected_cohorts": []}},
         "atime": {"cohort": {"pure_recall": 0}}, "ctime": {"cohort": {"pure_recall": 0}},
         "dir_mtime_cohort": {"pure_recall": 0}, "index_mtime_cohort": {"pure_recall": 0},
         "git": {"status_sample": [], "diff_names": [], "commits": 1, "stash": 0, "branches": ["*", "main"]},
         "leftovers_workspace": [], "pristine_copies": []}
    d.update(kw)
    return d


def test_judge():
    assert env_leak_check.judge(_probe()) == ([], [])
    leaks, _ = env_leak_check.judge(_probe(index_mtime_cohort={"pure_recall": 1.0}))
    assert [l[:2] for l in leaks] == ["T4"]
    leaks, warns = env_leak_check.judge(_probe(mtime={"cohort": {"pure_recall": 1.0, "distinct_values": 2,
                                                                 "injected_cohorts": []}}))
    assert [l[:2] for l in leaks] == ["T1"] and warns
    leaks, _ = env_leak_check.judge(_probe(leftovers_workspace=["/workspace/a.js.orig"]))
    assert [l[:2] for l in leaks] == ["L1"]


def test_check_never_raises_without_docker(monkeypatch, tmp_path):
    monkeypatch.setattr(env_leak_check, "_docker", lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "no"))
    r = env_leak_check.check(tmp_path, "img:tag")
    assert r["status"] == "error" and "not found" in r["summary"]


def test_reset_scripts():
    root = cwe_tree_reset.root_script()
    assert "@1704067200" in root and "ls-files -z" in root and "update-index" not in root
    assert "stat -c %u:%g" in root                      # %% unescaped
    assert "/workspace" in cwe_tree_reset.refresh_script("/workspace")
    assert cwe_tree_reset.parse_summary("x\nroot=/workspace owner=1000:1000 files=3 dirs=2 mode=git fail=0\n") == \
        {"root": "/workspace", "owner": "1000:1000", "files": "3", "dirs": "2", "mode": "git", "fail": "0"}
    assert cwe_tree_reset.parse_summary("cwe-tree-reset: skipped (no /workspace or /app)") == {}
    assert cwe_tree_reset.is_agent_context("/x/tasks/t/environment")
    assert not cwe_tree_reset.is_agent_context("/x/tasks/t/tests")
    assert cwe_tree_reset.enabled({}) and not cwe_tree_reset.enabled({"CWE_TREE_RESET": "0"})


def test_reset_script_runs_on_a_real_tree(tmp_path):
    """Runs part 1 on a temp git tree (the script's /workspace replaced by the temp path), then part 2."""
    if subprocess.run(["bash", "-c", "touch --version && stat --version"], capture_output=True).returncode:
        pytest.skip("needs GNU touch/stat")
    w = tmp_path / "workspace"
    (w / "src").mkdir(parents=True)
    for n in ("a.js", "src/b.js", "src/c.js"):
        (w / n).write_text(n)
    subprocess.run("git init -q && git add -A && git -c user.name=t -c user.email=t@l commit -qm x", shell=True,
                   cwd=w, check=True)
    subprocess.run(["touch", "-d", "@1800000000", str(w / "src/c.js")], check=True)
    r = subprocess.run(["bash", "-c", cwe_tree_reset.root_script().replace("/workspace /app", str(w))],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    info = cwe_tree_reset.parse_summary(r.stdout)
    assert info["files"] == "3" and info["mode"] == "git"
    r = subprocess.run(["bash", "-c", cwe_tree_reset.refresh_script(info["root"])], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    times = {p.stat().st_mtime for p in (w / "a.js", w / "src/b.js", w / "src/c.js", w / "src", w)}
    assert times == {1704067200}
    dbg = subprocess.run(["git", "ls-files", "--debug"], cwd=w, capture_output=True, text=True).stdout
    assert dbg.count("mtime: 1704067200:") == 3


def test_ledger_notes(tmp_path, monkeypatch):
    import audit_results as ar
    monkeypatch.setattr(ar, "OUT", tmp_path)
    assert ar.ledger_notes() == []
    (tmp_path / "ledger_notes.tsv").write_text("# c\ntask\tmodel\tjob\ttrial\tkind\tnote\n"
                                               "praisonai-s2\tDeepSeek\tj\tt\tleak-aided solve\tused | times\n")
    n = ar.ledger_notes()
    assert n == [{"task": "praisonai-s2", "model": "DeepSeek", "job": "j", "trial": "t", "kind": "leak-aided solve",
                  "note": "used | times"}]


def test_export_refuses_a_leaking_task(tmp_path, monkeypatch):
    import paths
    import export_delivery as ed
    monkeypatch.setattr(paths, "TASKS", tmp_path / "tasks")
    (tmp_path / "tasks" / "k-s2" / "environment").mkdir(parents=True)
    (tmp_path / "tasks" / "k-s2" / "task.toml").write_text("")
    monkeypatch.setattr(ed.cwe_reuse_tag, "ensure_image_sync", lambda ctx, tag: None)
    monkeypatch.setattr(ed.fairness_verdict, "delivery_blockers", lambda slug: [])   # the leak check alone
    monkeypatch.setattr(ed.env_leak_check, "check", lambda task, tag: {"status": "leak", "summary": "LEAK (x)",
                                                                        "leaks": ["T1 mtime"]})
    monkeypatch.setattr(sys, "argv", ["export_delivery.py", str(tmp_path / "out"), "k-s2"])
    with pytest.raises(SystemExit) as e:
        ed.main()
    assert e.value.code == 4 and not (tmp_path / "out").exists()
    monkeypatch.setattr(ed.env_leak_check, "check", lambda task, tag: {"status": "error", "summary": "no python3",
                                                                        "leaks": []})
    assert ed.leak_refusals(["k-s2"])                          # could not check: refused too


def test_gate_leak_check_is_warning_only(monkeypatch, capsys):
    import gate

    def boom(task):
        raise RuntimeError("docker gone")
    monkeypatch.setattr(gate.env_leak_check, "check", boom)
    r = gate.leak_check(Path("/nonexistent/t"))
    assert r["status"] == "error"
    monkeypatch.setattr(gate.env_leak_check, "check", lambda task: {"status": "leak", "summary": "LEAK", "leaks":
                                                                    ["T1 mtime"], "warns": [], "image": "i"})
    assert gate.leak_check(Path("/x"))["status"] == "leak"
    assert "WARNING (leak check, not blocking): T1 mtime" in capsys.readouterr().out
