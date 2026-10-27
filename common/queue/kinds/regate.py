"""regate: re-run a task's gate after its files changed (common/gate/regate.sh; --listing for stacked tasks)."""
from kinds import Kind, check_from, register


def command(row, cfg):
    import qdb
    return ["bash", "common/gate/regate.sh", row["task"]] + (["--listing"] if qdb.args_of(row).get("listing") else [])


register(Kind(name="regate", command=command, check=check_from("c_regate"), exclusive=True, foreign="regate",
              count_foreign=True, priority=50, max_running=4, max_attempts=2, retry_exit_codes=(2,),
              disk_floor="DISK_MIN_FREE_GB_GATE", reads=("tasks/<slug>/", "build/<slug>/checks/"),
              writes=("build/<slug>/postbuild.log RESULT", "build/<slug>/gate_fingerprint.json", "gate markers")))
