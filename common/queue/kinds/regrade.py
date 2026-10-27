"""regrade: grade a run's saved code again on the current tests (common/audit/regrade_from_code.py)."""
import sys

from kinds import Kind, check_from, register, trial_dir


def command(row, cfg):
    import qdb
    a = qdb.args_of(row)
    return [sys.executable, "-I", "common/audit/regrade_from_code.py", trial_dir(cfg, a), a["why"]]


register(Kind(name="regrade", command=command, check=check_from("c_regrade"), exclusive=True, priority=30,
              max_running=3, max_attempts=2, reads=("<trial>/final-code/", "tasks/<slug>/tests/"),
              writes=("<trial>/regrade-<UTC>/",)))
