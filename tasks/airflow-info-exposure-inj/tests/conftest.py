"""Shared fixtures for the hidden tests.

The REST API is driven in-process through the real FastAPI app; the CLI and the
process start-up path run as real ``airflow`` / ``python`` subprocesses with
their own configuration file. Values are unique markers so a leak is detected
anywhere in the output, whatever it is reported under.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import uuid

HOME = os.environ.setdefault("AIRFLOW_HOME", "/tmp/airflow-verify-home")
os.makedirs(HOME, exist_ok=True)
DB_URL = f"sqlite:///{HOME}/airflow.db"
os.environ.setdefault("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", DB_URL)
os.environ["AIRFLOW__CORE__AUTH_MANAGER"] = (
    "airflow.api_fastapi.auth.managers.simple.simple_auth_manager.SimpleAuthManager"
)
os.environ["AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS"] = "True"
os.environ["AIRFLOW__API__EXPOSE_CONFIG"] = "True"
os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"

import pytest  # noqa: E402

HIDDEN = "< hidden >"


def marker(tag: str = "v") -> str:
    return f"{tag}{uuid.uuid4().hex}"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from airflow.api_fastapi.app import create_app

    return TestClient(create_app(), base_url="http://testserver/api/v2")


@pytest.fixture
def team_sections():
    """Add config-file sections to the live configuration; removed again afterwards."""
    from airflow.configuration import conf

    added: list[str] = []

    def _add(sections: dict[str, dict[str, str]]) -> None:
        for name, options in sections.items():
            if not conf.has_section(name):
                conf.add_section(name)
                added.append(name)
            for key, value in options.items():
                conf.set(name, key, value)

    yield _add
    for name in added:
        conf.remove_section(name)


def options_of(response_json: dict) -> dict[str, dict[str, str]]:
    return {
        s["name"]: {o["key"]: o["value"] for o in s["options"]} for s in response_json.get("sections", [])
    }


def write_cfg(tmp_path, body: str) -> str:
    path = tmp_path / "airflow.cfg"
    path.write_text(
        textwrap.dedent(
            f"""\
            [database]
            sql_alchemy_conn = {DB_URL}

            [core]
            load_examples = False

            """
        )
        + textwrap.dedent(body)
    )
    return str(path)


def _env(cfg_path: str, extra: dict[str, str] | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AIRFLOW__")}
    env["AIRFLOW_HOME"] = HOME
    env["AIRFLOW_CONFIG"] = cfg_path
    env.update(extra or {})
    return env


def run_airflow(cfg_path: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["airflow", *args],
        env=_env(cfg_path, env),
        capture_output=True,
        text=True,
        timeout=300,
    )


def run_python(cfg_path: str, code: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        env=_env(cfg_path, env),
        capture_output=True,
        text=True,
        timeout=300,
    )


# Starts an Airflow process the normal way (importing the package runs the
# start-up initialisation) and prints what its log redaction makes of each value
# passed in argv.
REDACT_SNIPPET = textwrap.dedent(
    """\
    import sys
    import airflow  # noqa: F401  - process start-up
    from airflow._shared.secrets_masker import redact
    for value in sys.argv[1:]:
        print("LOGGED:" + str(redact("value=" + value)))
    """
)


def redacted_lines(cfg_path: str, values: list[str], env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", REDACT_SNIPPET, *values],
        env=_env(cfg_path, env),
        capture_output=True,
        text=True,
        timeout=300,
    )
    lines = [l for l in proc.stdout.splitlines() if l.startswith("LOGGED:")]
    assert len(lines) == len(values), proc.stdout + proc.stderr
    return "\n".join(lines)


# A worker process configures its logging the normal way (the worker-side logging entry
# point) and prints what its own log redaction makes of each value passed in argv. Airflow
# marks a re-executed worker process, and that process does not run the web/scheduler
# start-up that registers the deployment-wide secrets, so its logging configuration is
# responsible for registering them itself.
SDK_REDACT_SNIPPET = textwrap.dedent(
    """\
    import sys
    from airflow.sdk.log import configure_logging

    configure_logging()
    from airflow.sdk._shared.secrets_masker import redact
    for value in sys.argv[1:]:
        print("LOGGED:" + str(redact("value=" + value)))
    """
)


def sdk_redacted_lines(cfg_path: str, values: list[str], env: dict[str, str] | None = None) -> str:
    worker_env = {"_AIRFLOW__REEXECUTED_PROCESS": "1"}
    worker_env.update(env or {})
    proc = subprocess.run(
        [sys.executable, "-c", SDK_REDACT_SNIPPET, *values],
        env=_env(cfg_path, worker_env),
        capture_output=True,
        text=True,
        timeout=300,
    )
    lines = [l for l in proc.stdout.splitlines() if l.startswith("LOGGED:")]
    assert len(lines) == len(values), proc.stdout + proc.stderr
    return "\n".join(lines)
