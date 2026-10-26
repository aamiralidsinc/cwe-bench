"""Shared fixtures for the hidden tests.

Each suite starts the real Glances web server (the product's own ``python -m
glances -w`` entry point) with a configuration file written here, then drives it
over HTTP. The credentials in that file are unique markers, so a leak is detected
wherever it appears in a response, whatever name it is reported under.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import pytest
import requests

MARK = uuid.uuid4().hex[:10]

# The restored submission lives at /workspace in the verifier; local development
# runs can point the same tests at a checkout elsewhere.
WORKSPACE = os.environ.get("GLANCES_TASK_ROOT", "/workspace")

# Credentials configured for the service under test. Unique per run so a marker
# cannot collide with an unrelated value in the response.
SECRET_PASSWORD = f"pw{MARK}"
SECRET_LOGIN = f"lg{MARK}"
URL_USER = f"uu{MARK}"
URL_PASSWORD = f"up{MARK}"
PROXY_USER = f"pu{MARK}"
PROXY_PASSWORD = f"pp{MARK}"
PLAIN_URL = "http://127.0.0.1:9/plain"
SECOND_URL = "http://127.0.0.1:9/second"

SECRETS = (
    SECRET_PASSWORD,
    SECRET_LOGIN,
    URL_USER,
    URL_PASSWORD,
    PROXY_USER,
    PROXY_PASSWORD,
)

CONFIG = f"""
[global]
check_update=false
refresh=5

[ip]
public_disabled=True
public_api=https://{URL_USER}:{URL_PASSWORD}@127.0.0.1:9/json/
public_username={SECRET_LOGIN}
public_password={SECRET_PASSWORD}
public_field=ip

[ports]
web_1_url=https://{URL_USER}:{URL_PASSWORD}@127.0.0.1:9/blog
web_1_description=first-blog
web_1_http_proxy=http://{PROXY_USER}:{PROXY_PASSWORD}@127.0.0.1:3128
web_2_url={PLAIN_URL}
web_2_description=plain-blog

[cpu]
user_careful=50
user_warning=70
user_critical=90
user_log=True

[load]
user_careful=2

[influxdb]
host=localhost
user={SECRET_LOGIN}
password={SECRET_PASSWORD}

[passthrough]
user={SECRET_LOGIN}
login={SECRET_LOGIN}
username={SECRET_LOGIN}
"""


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def api():
    """Start the product's web server and return its API base URL."""
    home = tempfile.mkdtemp(prefix="glances-home-")
    conf_dir = tempfile.mkdtemp(prefix="glances-conf-")
    conf_file = os.path.join(conf_dir, "glances.conf")
    with open(conf_file, "w", encoding="utf-8") as fh:
        fh.write(CONFIG)

    port = free_port()
    base = f"http://127.0.0.1:{port}/api/4"
    log_path = os.path.join(conf_dir, "server.log")
    env = dict(os.environ)
    env["HOME"] = home
    env["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    env.setdefault("PYTHONUNBUFFERED", "1")

    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "glances",
                "-B",
                "127.0.0.1",
                "-w",
                "--disable-webui",
                "-p",
                str(port),
                "-C",
                conf_file,
            ],
            cwd=WORKSPACE,
            stdout=log,
            stderr=subprocess.STDOUT,
            env=env,
        )

    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            try:
                response = requests.get(f"{base}/status", timeout=2)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.5)
        else:
            proc.terminate()
            raise RuntimeError("Glances web server did not become ready")

        if proc.poll() is not None:
            with open(log_path, encoding="utf-8", errors="replace") as fh:
                tail = fh.read()[-4000:]
            raise RuntimeError(f"Glances web server exited early:\n{tail}")

        yield base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


def assert_not_disclosed(response, secrets=SECRETS):
    """The response must not carry any configured credential marker."""
    assert response.status_code < 500, response.text
    for secret in secrets:
        assert secret not in response.text, f"credential {secret!r} disclosed in {response.url}"
