"""build: one task's build pipeline (the same command pipelines/router/scale_queue.py used)."""
from kinds import Kind, builder_exit_file, check_from, register


def command(row, cfg):
    task = row["task"]
    if task.startswith("stk-"):
        return ["bash", "pipelines/stacking/3-build-gate/run_stack_pipeline.sh", task]
    return ["bash", "pipelines/sibling/6-build/run_pipeline.sh", "deepseek", task]


register(Kind(name="build", command=command, check=check_from("c_build"), exclusive=True, foreign="build",
              count_foreign=True, priority=25, max_running=20, max_attempts=1, disk_floor="DISK_MIN_FREE_GB_BUILD",
              exit_of=builder_exit_file,             # the job records the builder's exit, not run_pipeline.sh's 0
              reads=("build/<slug>/BUILD-PROMPT.md",),
              writes=("tasks/<slug>/", "build/<slug>/ (end_utc.txt, gate markers, pipeline logs)")))
