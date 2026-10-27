"""Work-queue settings: defaults here, overrides from a TOML file (common/queue/queue.toml unless --config/CWEQ_CONFIG)."""
import copy
import os
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "queue.toml"

DEFAULTS = {
    "db": "~/.tb-graders/cwe/queue.db",
    "log_dir": "~/.tb-graders/cwe/queue-logs",
    "jobs_dir": "~/.tb-graders/cwe/jobs",
    "enabled": True,
    "dispatch": {"tick_sec": 30, "start_spacing_sec": 20, "max_starts_per_tick": 2, "lease_sec": 600,
                 "aging_per_hour": 10, "max_running_total": 8, "max_running_per_task": 1},
    "reconcile": {"tick_sec": 120, "listing_prefixes": ["stk-"], "rehold_after_regate": True},
    "busy": {"patterns": ["regate", "regrade", "rescore", "postbuild.sh", "gate_one_ds.sh", "common/gate/gate.py",
                          "repair", "fairfix", "upgrade", "run_stack_pipeline.sh", "run_pipeline.sh", "run_build.sh",
                          "fingerprint.py"]},
    "limits": {"min_free_disk_gb": 150, "max_load": 250, "min_mem_available_gb": 30, "max_tmp_inode_pct": 90,
               "max_running": {"regate": 4, "regrade": 3, "rescore": 2}},
    "priority": {"regate": 50, "rescore": 40, "regrade": 30, "trial_run": 20},
    "max_attempts": {"regate": 2, "regrade": 2, "rescore": 2},
    "retry_exit_codes": {"regate": [2]},
    "commands": {},
}


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load(path=None):
    """Defaults merged with the TOML file. Paths are expanded (~)."""
    cfg = copy.deepcopy(DEFAULTS)
    path = Path(path or os.environ.get("CWEQ_CONFIG") or DEFAULT_FILE)
    if path.is_file():
        with open(path, "rb") as f:
            _merge(cfg, tomllib.load(f))
    for k in ("db", "log_dir", "jobs_dir"):
        cfg[k] = str(Path(os.path.expanduser(str(cfg[k]))))
    cfg["_file"] = str(path)
    return cfg
