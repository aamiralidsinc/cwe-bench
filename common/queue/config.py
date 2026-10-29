"""Work-queue settings: defaults here and in the kind declarations (kinds/), overrides from a TOML file
(common/queue/queue.toml unless --config/CWEQ_CONFIG). The file is the one source of the values in force; settings.py
records every version of it in the database."""
import copy
import hashlib
import os
import tomllib
from pathlib import Path

import kinds

HERE = Path(__file__).resolve().parent
DEFAULT_FILE = HERE / "queue.toml"

# Settings that are not per kind. Per-kind defaults (priority, max_running, max_attempts, retry/ok exit codes, env,
# disk floor, light_kinds, count_foreign) come from the kind declarations (kinds.defaults()).
DEFAULTS = {
    "db": "~/.tb-graders/cwe/queue.db",
    "log_dir": "~/.tb-graders/cwe/queue-logs",
    "jobs_dir": "~/.tb-graders/cwe/jobs",
    "enabled": True,
    "require_adoption": True,
    "dispatch": {"tick_sec": 30, "start_spacing_sec": [2, 8], "fill_spacing_sec": [15, 40], "max_starts_per_tick": 3,
                 "lease_sec": 600, "aging_per_hour": 10, "max_running_total": 69, "max_running_per_task": 6,
                 "trials_wait_builds": 20},
    "phase3": {"enabled": True, "batches": [], "max_launches": 3},
    "phase4": {"enabled": True, "audits": True, "fairness": True, "cleanup": True, "step3": True},
    "build_resume": {"auto_timeouts": False, "max_auto_resumes": 1},
    "reconcile": {"tick_sec": 120, "listing_prefixes": ["stk-"], "rehold_after_regate": True},
    "busy": {"patterns": ["regate", "regrade", "rescore", "postbuild.sh", "gate_one_ds.sh", "common/gate/gate.py",
                          "repair", "fairfix", "upgrade", "run_stack_pipeline.sh", "run_pipeline.sh", "run_build.sh",
                          "fingerprint.py"]},
    "limits": {"min_free_disk_gb": 150, "max_load": 250, "min_mem_available_gb": 30, "max_tmp_inode_pct": 90},
    "commands": {},
    "kinds": {"extra_dirs": []},
    "lint": {"enabled": True},
    "checks": {"enabled": True, "refuse_on_failed_selfcheck": True, "selfcheck_dir": "~/.tb-graders/cwe/selfcheck"},
}


def _merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def file_hash(data):
    """The settings version: first 16 hex digits of the sha256 of the file's bytes (b'' when there is no file)."""
    return hashlib.sha256(data).hexdigest()[:16]


def load(path=None):
    """Defaults, then the kind declarations' defaults, then the TOML file. Paths are expanded (~).
    cfg["_file"] is the file read, cfg["_settings_hash"] its version and cfg["_settings_text"] its text."""
    path = Path(path or os.environ.get("CWEQ_CONFIG") or DEFAULT_FILE)
    data = path.read_bytes() if path.is_file() else b""
    toml = tomllib.loads(data.decode()) if data else {}
    kinds.load((toml.get("kinds") or {}).get("extra_dirs", ()))
    cfg = copy.deepcopy(DEFAULTS)
    _merge(cfg, kinds.defaults())
    _merge(cfg, toml)
    for k in ("db", "log_dir", "jobs_dir"):
        cfg[k] = str(Path(os.path.expanduser(str(cfg[k]))))
    cfg["_file"] = str(path)
    cfg["_settings_hash"] = file_hash(data)
    cfg["_settings_text"] = data.decode(errors="replace")
    return cfg
