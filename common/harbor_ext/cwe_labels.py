"""cwe_labels: Docker labels on every container Harbor starts for the pipeline.

The work queue's worker gives every process it starts CWE_* environment variables (common/queue/identity.py
job_env). Harbor runs inside that environment, and ReuseDockerEnvironment (cwe_reuse_env.py) adds one more compose
file to Harbor's list: a labels override for the `main` service, built here from those variables. Harbor itself is
not patched. Containers then map back to their job:

    cwe.job_id  cwe.kind  cwe.task  cwe.batch  cwe.model  cwe.run  cwe.code_version  cwe.started_by  cwe.session

cwe.started_by is `cweq` for a queue job and `script` for a run started by any other launcher (no CWE_JOB_ID);
cwe.task falls back to Harbor's environment name, so every pipeline container carries at least its task.
The same override sets json-file log rotation (50 MB x 3) on `main` and on Harbor's egress-control sidecar when that
compose file is in the list (CWE_LOG_ROTATE=0 leaves logging to the daemon default).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ENV_TO_LABEL = (
    ("CWE_JOB_ID", "cwe.job_id"),
    ("CWE_KIND", "cwe.kind"),
    ("CWE_TASK", "cwe.task"),
    ("CWE_BATCH", "cwe.batch"),
    ("CWE_MODEL", "cwe.model"),
    ("CWE_RUN", "cwe.run"),
    ("CWE_CODE_VERSION", "cwe.code_version"),
)
SAFE = re.compile(r"[^A-Za-z0-9._:/@+=-]")


def labels(environ, session_id: str = "", environment_name: str = "") -> dict[str, str]:
    """The labels for one Harbor environment, from the process environment."""
    out = {}
    for var, label in ENV_TO_LABEL:
        v = (environ.get(var) or "").strip()
        if v:
            out[label] = SAFE.sub("_", v)[:200]
    if "cwe.task" not in out and environment_name:
        out["cwe.task"] = SAFE.sub("_", environment_name)[:200]
    out["cwe.started_by"] = "cweq" if environ.get("CWE_JOB_ID") else "script"
    if session_id:
        out["cwe.session"] = SAFE.sub("_", session_id)[:200]
    return out


# Container log rotation for every pipeline container, set per container so it applies without restarting Docker
# (the daemon-wide default in /etc/docker/daemon.json needs a restart that stops all running work).
LOGGING = {"driver": "json-file", "options": {"max-size": "50m", "max-file": "3"}}
EGRESS_SIDECAR = "harbor-docker-egress-control-sidecar"   # Harbor's sidecar in docker-compose-egress-control.yaml


def write_compose(path: Path, lab: dict[str, str], service: str = "main", extra_services=(),
                  logging: dict | None = LOGGING) -> Path:
    """A compose override (JSON is valid compose YAML): `lab` on `service`, and log rotation on `service` and on
    every service in extra_services (only services the other compose files define: an override cannot add one)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    services = {service: {"labels": lab}}
    if logging:
        services[service]["logging"] = logging
        for s in extra_services:
            services[s] = {"logging": logging}
    path.write_text(json.dumps({"services": services}, sort_keys=True))
    return path
