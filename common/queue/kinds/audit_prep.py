"""audit_prep: prepare a failing run's evidence folder for its auditor (postmortem.py prepare)."""
from kinds import Kind, check_from, command_from, register

register(Kind(name="audit_prep", command=command_from("phase4"), check=check_from("c_audit_prep"), light=True,
              priority=55, max_running=4, max_attempts=1, reads=("build/audit/awaiting_audit.tsv", "<trial>/"),
              writes=("<trial>/postmortem-<UTC>/", "pipelines/router/out/queue/audit_ready.txt")))
