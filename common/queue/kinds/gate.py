"""gate: a kind name kept for the job table and the never-redo rule; it has no worker (gates run inside builds and
re-gates)."""
from kinds import Kind, register

register(Kind(name="gate", command=None, exclusive=True, reads=("tasks/<slug>/",), writes=("build/<slug>/ markers",)))
