"""delivery_prep: package a kept both-model breaker for delivery (common/queue/delivery.py prep)."""
from kinds import Kind, command_from, register

register(Kind(name="delivery_prep", command=command_from("delivery"), priority=35, max_running=1, max_attempts=1,
              reads=("build/<slug>/HUMAN-DECISION.md", "build/audit/delivered.tsv"),
              writes=("~/.tb-graders/cwe/deliveries/<UTC>-<slug>/",)))
