"""trial_run: trial runs of one model (common/trial/trial.py), early abort at a solve."""
import sys

from kinds import Kind, check_from, register


def command(row, cfg):
    import paths
    import qdb
    a = qdb.args_of(row)
    return [sys.executable, "-I", str(paths.TRIAL), row["task"], "--models", a["model"], "--no-verdict",
            "--first-run", str(a["first_run"]), "--max-runs", str(a["max_runs"])]


register(Kind(name="trial_run", command=command, check=check_from("c_trial"), foreign="trial", count_foreign=True,
              priority=20, max_running=40, max_attempts=1, ok_exit_codes=(0, 2),
              env={"CWE_AGENT_TIMEOUT_MULT": "1.5"}, disk_floor="DISK_MIN_FREE_GB_TRIAL",
              reads=("tasks/<slug>/",), writes=("build/<slug>/runs_<model>.log", "~/.tb-graders/cwe/jobs/<job>/")))
