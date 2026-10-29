"""common/launch/run_build.sh (2026-10-28): the brief goes in on stdin with the project root of the release that runs
it, the builder carries its build tag in the environment (not the arguments), and the pipeline alone stamps the
start, exit and end. Runs the real script against a fake claude in a copy of the scripts it needs."""
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FILES = (".cwe-bench-root", "common/paths.sh", "common/paths.py", "common/markers.sh", "common/launch/run_build.sh",
         "common/util/build_procs.py")
FAKE_CLAUDE = """#!/bin/sh
d="$HOME/calls"; mkdir -p "$d"
printf '%s\\n' "$@" > "$d/argv"
cat > "$d/stdin"
printf 'RUN=%s\\nSLUG=%s\\n' "$CWE_BUILD_RUN" "$CWE_BUILD_SLUG" > "$d/env"
echo '{"type":"result","subtype":"success","result":"done"}'
exit "${FAKE_RC:-0}"
"""


def world(tmp_path):
    root = tmp_path / "rel"
    for f in FILES:
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / f, root / f)
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    claude = home / ".local" / "bin" / "claude"
    claude.write_text(FAKE_CLAUDE)
    claude.chmod(0o755)
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "timeout").write_text('#!/bin/sh\nshift\nexec "$@"\n')    # macOS has no timeout(1)
    (shim / "timeout").chmod(0o755)
    b = root / "build" / "x-s2"
    b.mkdir(parents=True)
    (b / "BUILD-PROMPT.md").write_text("# Build one security-fix benchmark task\nProject root: `/old/rel/591de221a3d4`."
                                       " Task: `x-s2`.\nRun /old/rel/591de221a3d4/common/gate/gate.py; worker-service.cjs\n")
    env = dict(os.environ, HOME=str(home), PATH=f"{shim}:{os.environ['PATH']}", FAKE_RC="7")
    env.pop("CWE_DATA_ROOT", None)
    return root, home, b, env


def run(root, env, *args):
    return subprocess.run(["bash", str(root / "common/launch/run_build.sh"), "x-s2", *args], env=env,
                          capture_output=True, text=True, timeout=60)


def test_fresh_build_brief_on_stdin_with_the_running_root(tmp_path):
    root, home, b, env = world(tmp_path)
    r = run(root, env)
    assert r.returncode == 0, r.stderr
    real = str(root.resolve())
    calls = home / "calls"
    argv = (calls / "argv").read_text()
    assert "Build one security-fix" not in argv and "worker-service.cjs" not in argv and "x-s2" not in argv
    assert "--resume" not in argv and "--output-format" in argv
    brief = (calls / "stdin").read_text()
    assert f"Project root: `{real}`" in brief and f"Run {real}/common/gate/gate.py" in brief
    assert "/old/rel" not in brief
    env_seen = dict(l.split("=", 1) for l in (calls / "env").read_text().split())
    assert env_seen["SLUG"] == "x-s2" and env_seen["RUN"].startswith("x-s2:")
    assert (b / "build-exit.txt").read_text().strip() == "7"
    assert (b / "start_utc.txt").is_file() and (b / "end_utc.txt").is_file()
    assert "x-s2: builder exit 7" in r.stdout and "project root /old/rel/591de221a3d4 ->" in r.stdout
    assert (b / "BUILD-PROMPT.md").read_text().count("/old/rel") == 2    # the prepared prompt stays as it was


def test_resume_sends_the_message_on_stdin_and_stamps_the_resume_start(tmp_path):
    root, home, b, env = world(tmp_path)
    (b / "start_utc.txt").write_text("2026-10-28T00:00:00Z\n")
    msg = tmp_path / "msg.md"
    msg.write_text("Note from the operator: continue.\n")
    r = run(root, dict(env, FAKE_RC="0"), "--resume", "sess-123", "--msg-file", str(msg))
    assert r.returncode == 0, r.stderr
    calls = home / "calls"
    argv = (calls / "argv").read_text().split("\n")
    assert argv[argv.index("--resume") + 1] == "sess-123"
    assert (calls / "stdin").read_text() == "Note from the operator: continue.\n"
    assert (b / "start_utc.txt").read_text() == "2026-10-28T00:00:00Z\n"
    assert (b / "resume_start_utc.txt").is_file() and (b / "build-exit.txt").read_text().strip() == "0"
    assert run(root, env, "--resume", "s").returncode == 2                 # a resume needs its message
