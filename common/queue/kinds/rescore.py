"""rescore: re-score a run from its recorded results with removed tests dropped (rescore_from_results.py)."""
import sys

from kinds import Kind, check_from, register, trial_dir


def command(row, cfg):
    import qdb
    a = qdb.args_of(row)
    drops = [x for d in a["drop"] for x in ("--drop", d)]
    return [sys.executable, "-I", "common/audit/rescore_from_results.py", trial_dir(cfg, a), *drops, "--why", a["why"]]


register(Kind(name="rescore", command=command, check=check_from("c_regrade", rescore=True), exclusive=True,
              priority=40, max_running=2, max_attempts=2, reads=("<trial>/verifier/results.json",),
              writes=("<trial>/regrade-<UTC>/",)))
