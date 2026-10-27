"""cleanup: one pass of the hourly cleanup (common/util/hourly_cleanup.sh once)."""
from kinds import Kind, check_from, command_from, register

register(Kind(name="cleanup", command=command_from("phase4"), check=check_from("c_cleanup"), light=True,
              priority=70, max_running=1, max_attempts=1, reads=("docker state", "/tmp"),
              writes=("build/audit/hourly_cleanup.log",)))
