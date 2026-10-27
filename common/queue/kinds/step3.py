"""step3: the router's periodic step (the third step of the former auto_advance.sh)."""
from kinds import Kind, command_from, register

register(Kind(name="step3", command=command_from("phase4"), light=True, priority=10, max_running=1, max_attempts=1,
              reads=("pipelines/router/",), writes=("pipelines/router/out/",)))
