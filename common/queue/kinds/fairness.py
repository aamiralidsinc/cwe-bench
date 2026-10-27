"""fairness: the fairness review of a both-model breaker candidate (pipelines/*/9-fairness)."""
from kinds import Kind, check_from, command_from, register

register(Kind(name="fairness", command=command_from("phase4"), check=check_from("c_fairness"), exclusive=True,
              foreign="fairness", count_foreign=True, priority=45, max_running=3, max_attempts=1,
              reads=("tasks/<slug>/", "build/<slug>/ build notes"), writes=("build/<slug>/FAIRNESS.md",)))
