"""Black-box harness for the Portainer task.

The tests drive the real server binary over loopback HTTP. They configure the
instance only through interfaces a user sees: command-line flags, the
PORTAINER_SETUP_TOKEN environment variable and the X-Setup-Token header.
Nothing here imports product code or relies on internal identifiers.
"""
import json
import os
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid

import pytest

BIN = os.environ.get("PORTAINER_BIN", "/opt/portainer-under-test")

# Values an operator configures for this task's tests.
SETUP_TOKEN = "task-setup-token-4f8c1d"
STRONG_PASSWORD = "Str0ngPassw0rd!23"
FI_FIXTURE_USER = "fixture-admin"
# bcrypt hash of STRONG_PASSWORD, used for the --admin-password startup path
ADMIN_PASSWORD_HASH = "$2a$10$DdI6OfRhJUg9nEf4Vo2PCOGu44OjA5ahQwduRmU4YiMhSxQIkdKgG"


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def http_request(base, method, path, body=None, headers=None, timeout=60):
    """Return (status, body). status is None when no HTTP response was received."""
    req = urllib.request.Request(base + path, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, exc.read()
        except Exception:
            return exc.code, b""
    except Exception:
        return None, b""


def json_payload(payload):
    return json.dumps(payload).encode()


def multipart_body(fields, files):
    """Encode a multipart/form-data body. files is [(name, filename, bytes)]."""
    boundary = "----task" + uuid.uuid4().hex
    out = bytearray()
    for name, value in fields:
        out += b"--" + boundary.encode() + b"\r\n"
        out += ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode()
        out += str(value).encode() + b"\r\n"
    for name, filename, content in files:
        out += b"--" + boundary.encode() + b"\r\n"
        out += ('Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (name, filename)).encode()
        out += b"Content-Type: application/octet-stream\r\n\r\n"
        out += content + b"\r\n"
    out += b"--" + boundary.encode() + b"--\r\n"
    return bytes(out), {"Content-Type": "multipart/form-data; boundary=" + boundary}


class Server:
    """A throwaway Portainer instance on loopback ports."""

    def __init__(self, token=SETUP_TOKEN, use_env_token=True, admin_password=None,
                 data_dir=None, startup_timeout=120):
        self.dir = tempfile.mkdtemp(prefix="portainer-task-")
        self.data = data_dir or os.path.join(self.dir, "data")
        self.assets = os.path.join(self.dir, "assets")
        os.makedirs(self.data, exist_ok=True)
        os.makedirs(self.assets, exist_ok=True)

        self.http_port = free_port()
        self.https_port = free_port()
        self.tunnel_port = free_port()
        self.base = "http://127.0.0.1:%d" % self.http_port

        env = dict(os.environ)
        env.pop("PORTAINER_SETUP_TOKEN", None)
        if use_env_token and token:
            env["PORTAINER_SETUP_TOKEN"] = token

        args = [
            BIN,
            "--data", self.data,
            "--assets", self.assets,
            "--bind", "127.0.0.1:%d" % self.http_port,
            "--bind-https", "127.0.0.1:%d" % self.https_port,
            "--tunnel-addr", "127.0.0.1",
            "--tunnel-port", str(self.tunnel_port),
            "--log-level", "ERROR",
        ]
        if admin_password:
            args.extend(["--admin-password", admin_password])

        self.log_path = os.path.join(self.dir, "server.log")
        self._log = open(self.log_path, "wb")
        self.proc = subprocess.Popen(
            args, cwd=self.dir, env=env,
            stdout=self._log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.wait_ready(startup_timeout)

    def log_tail(self, limit=2000):
        try:
            with open(self.log_path, "rb") as handle:
                return handle.read()[-limit:].decode("utf-8", "replace")
        except OSError:
            return ""

    def wait_ready(self, timeout=120):
        deadline = time.time() + timeout
        while time.time() < deadline:
            status, _ = http_request(self.base, "GET", "/api/system/status", timeout=3)
            if status == 200:
                return
            if self.proc.poll() is not None:
                raise RuntimeError(
                    "server exited during startup (code %s):\n%s"
                    % (self.proc.returncode, self.log_tail()))
            time.sleep(0.25)
        raise RuntimeError("server did not become ready in %ss:\n%s"
                           % (timeout, self.log_tail()))

    def request(self, method, path, body=None, headers=None, timeout=60):
        return http_request(self.base, method, path, body=body, headers=headers,
                            timeout=timeout)

    def post_json(self, path, payload, headers=None, timeout=60):
        merged = {"Content-Type": "application/json"}
        merged.update(headers or {})
        return self.request("POST", path, json_payload(payload), merged, timeout)

    def backup_dir(self):
        path = os.path.join(self.data, "backups")
        os.makedirs(path, exist_ok=True)
        return path

    def stop(self):
        try:
            if self.proc.poll() is None:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                    self.proc.wait(timeout=5)
        except (ProcessLookupError, PermissionError):
            pass
        finally:
            try:
                self._log.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.stop()
        return False


def wait_for_admin_state(server, timeout=90):
    """Return True when an administrator exists, False when none does.

    A successful restore restarts the server, so retry while it is unreachable."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, _ = server.request("GET", "/api/users/admin/check", timeout=3)
        if status is not None:
            return status != 404
        time.sleep(0.5)
    return True


def admin_init(server, token=None):
    headers = {}
    if token is not None:
        headers["X-Setup-Token"] = token
    return server.post_json(
        "/api/users/admin/init",
        {"Username": "attacker", "Password": STRONG_PASSWORD},
        headers=headers,
    )


def legacy_admin_init(server, token=None):
    headers = {}
    if token is not None:
        headers["X-Setup-Token"] = token
    return server.post_json(
        "/api/admin/init",
        {"Username": "attacker", "Password": STRONG_PASSWORD},
        headers=headers,
    )


def restore_backup(server, archive, token=None):
    body, headers = multipart_body([("password", "")],
                                   [("file", "backup.tar.gz", archive)])
    if token is not None:
        headers["X-Setup-Token"] = token
    return server.request("POST", "/api/restore", body, headers, timeout=120)


def restore_local(server, archive, token=None, filename="recovery.tar.gz"):
    with open(os.path.join(server.backup_dir(), filename), "wb") as handle:
        handle.write(archive)
    headers = {}
    if token is not None:
        headers["X-Setup-Token"] = token
    return server.post_json("/api/restore/local", {"FileName": filename},
                            headers=headers, timeout=120)


def automation_import(server, users, token=None):
    headers = {}
    if token is not None:
        headers["X-Setup-Token"] = token
    return server.post_json("/api/users/automation/import", {"Users": users},
                            headers=headers)


def demote_operator(server, username="admin", password=STRONG_PASSWORD):
    """Sign in as the operator and change that account to a regular user.

    Returns the status of the account change; the caller asserts on it."""
    status, body = login(server, username, password)
    assert status == 200, "the operator could not sign in: %s\n%s" % (
        status, server.log_tail())
    jwt = json.loads(body)["jwt"]
    status, body = server.request("GET", "/api/users/me",
                                  headers={"Authorization": "Bearer " + jwt})
    assert status == 200, "the operator account could not be read: %s" % status
    user_id = json.loads(body)["Id"]
    return server.request(
        "PUT", "/api/users/%d" % user_id, json.dumps({"Role": 2}).encode(),
        {"Content-Type": "application/json", "Authorization": "Bearer " + jwt},
    )[0]


def login(server, username, password):
    return server.post_json("/api/auth",
                            {"Username": username, "Password": password},
                            timeout=30)


def client_error(status):
    return status is not None and 400 <= status < 500


@pytest.fixture(scope="session")
def backup_archive():
    """A real backup archive containing an administrator we control.

    Produced through the legitimate first-run flow, so no product code is used
    to compute an expected value."""
    with Server() as server:
        status, _ = admin_init(server, token=SETUP_TOKEN)
        assert status == 200, "could not create the fixture administrator: %s\n%s" % (
            status, server.log_tail())
        status, body = login(server, "attacker", STRONG_PASSWORD)
        assert status == 200, "could not sign in as the fixture administrator: %s" % status
        jwt = json.loads(body)["jwt"]
        status, archive = server.request(
            "POST", "/api/backup", b'{"Password":""}',
            {"Content-Type": "application/json", "Authorization": "Bearer " + jwt},
            timeout=120,
        )
        assert status == 200 and archive, "could not create a backup archive: %s" % status
        return archive
