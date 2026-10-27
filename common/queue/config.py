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
    "require_adoption": True,
    "dispatch": {"tick_sec": 30, "start_spacing_sec": [2, 8], "fill_spacing_sec": [15, 40], "max_starts_per_tick": 3,
                 "lease_sec": 600, "aging_per_hour": 10, "max_running_total": 69, "max_running_per_task": 6,
                 "count_foreign": ["build", "trial_run", "regate", "fairness"], "trials_wait_builds": 20,
                 "light_kinds": ["audit_prep", "audit_record", "cleanup", "step3"]},
    "phase3": {"enabled": True, "batches": [], "max_launches": 3},
    "phase4": {"enabled": True, "audits": True, "fairness": True, "cleanup": True, "step3": True},
    "reconcile": {"tick_sec": 120, "listing_prefixes": ["stk-"], "rehold_after_regate": True},
    "busy": {"patterns": ["regate", "regrade", "rescore", "postbuild.sh", "gate_one_ds.sh", "common/gate/gate.py",
                          "repair", "fairfix", "upgrade", "run_stack_pipeline.sh", "run_pipeline.sh", "run_build.sh",
                          "fingerprint.py"]},
    "limits": {"min_free_disk_gb": 150, "max_load": 250, "min_mem_available_gb": 30, "max_tmp_inode_pct": 90,
               "max_running": {"regate": 4, "regrade": 3, "rescore": 2, "build": 20, "trial_run": 40,
                               "audit_prep": 4, "audit_record": 1, "fairness": 3, "cleanup": 1, "step3": 1,
                               "delivery_prep": 1},
               "disk_floor": {"build": "DISK_MIN_FREE_GB_BUILD", "trial_run": "DISK_MIN_FREE_GB_TRIAL",
                              "regate": "DISK_MIN_FREE_GB_GATE"}},
    "priority": {"regate": 50, "rescore": 40, "regrade": 30, "build": 25, "trial_run": 20, "audit_record": 60,
                 "audit_prep": 55, "fairness": 45, "cleanup": 70, "step3": 10, "delivery_prep": 35},
    "max_attempts": {"regate": 2, "regrade": 2, "rescore": 2, "build": 1, "trial_run": 1, "audit_prep": 1,
                     "audit_record": 1, "fairness": 1, "cleanup": 1, "step3": 1, "delivery_prep": 1},
    "retry_exit_codes": {"regate": [2]},
    "ok_exit_codes": {"trial_run": [0, 2]},
    "env": {"trial_run": {"CWE_AGENT_TIMEOUT_MULT": "1.5"}},
    "commands": {},
    "checks": {"enabled": True, "refuse_on_failed_selfcheck": True, "selfcheck_dir": "~/.tb-graders/cwe/selfcheck"},
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
