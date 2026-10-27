"""lint: the warning-only task-quality lint, once per task version (common/queue/lintstep.py run)."""
from kinds import Kind, check_from, command_from, register

register(Kind(name="lint", command=command_from("lintstep"), check=check_from("c_lint"), light=True, priority=15,
              max_running=2, max_attempts=1, reads=("tasks/<slug>/tests/",), writes=("build/<slug>/lint/<fp>.json",)))
