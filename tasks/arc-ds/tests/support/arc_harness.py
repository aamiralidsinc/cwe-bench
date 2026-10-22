"""Harness for the Arc task tests.

Every test drives the real Arc server binary over HTTP: the image is built
from the pinned (vulnerable) source plus the task's sibling code, the verifier
rebuilds that source at grading time, and this module starts it with a
throwaway configuration (local storage, auth enabled, no external services).
Nothing here knows about the fix; the tests only observe HTTP behaviour.
"""

import json
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

ADMIN_TOKEN = "arc-admin-bootstrap-0123456789abcdef0123"
NO_PERMISSION_NAME = "no-permission-token"


def free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Response:
    def __init__(self, status, body, headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    def json(self):
        try:
            return json.loads(self.body.decode("utf-8"))
        except Exception:
            return None

    def text(self):
        try:
            return self.body.decode("utf-8", "replace")
        except Exception:
            return ""

    def __repr__(self):
        return "Response(status=%s, body=%r)" % (self.status, self.body[:200])


def leaked(resp, marker):
    """True when a value derived from the attacked file reached the client.

    Error messages echo the query text (which the test itself wrote, including
    the file path), so only result-bearing fields are inspected: a refusal is
    allowed to say anything about the request it refused. For non-JSON
    responses (file downloads) the whole body is the result.
    """
    marker_bytes = marker.encode() if isinstance(marker, str) else marker
    payload = resp.json()
    if payload is None:
        return marker_bytes in resp.body
    if not isinstance(payload, dict):
        return marker_bytes in resp.body
    for key in ("data", "columns", "rows", "results"):
        if key in payload:
            try:
                if marker_bytes in json.dumps(payload[key]).encode():
                    return True
            except Exception:
                if marker_bytes in repr(payload[key]).encode():
                    return True
    return False


def is_refused(resp, marker):
    """True when the server refused an attack.

    The requirement is behavioural: no content derived from the target file may
    reach the client, and the request must be reported as an error rather than
    as a successful result. No exact status code is required — a 4xx from an
    input validator and a 5xx from the storage layer both count.
    """
    if leaked(resp, marker):
        return False
    if resp.status >= 400:
        return True
    payload = resp.json()
    if isinstance(payload, dict) and payload.get("success") is False:
        return True
    return False


class ArcServer:
    """A running Arc server with its own storage, auth database and temp dirs."""

    def __init__(self, auth=True, relative_storage=False, extra_config=None):
        self.auth = auth
        self.relative_storage = relative_storage
        self.extra_config = extra_config or {}
        self.root = tempfile.mkdtemp(prefix="arc-task-test-")
        self.port = free_port()
        self.proc = None
        self._restricted_token = None
        self.log_path = os.path.join(self.root, "server.log")

    # -- lifecycle ---------------------------------------------------------

    def _config(self):
        root = self.root
        if self.relative_storage:
            storage = "./data/arc"
            tmp = "./tmp"
            comp = "./comp"
        else:
            storage = os.path.join(root, "data")
            tmp = os.path.join(root, "tmp")
            comp = os.path.join(root, "comp")

        lines = [
            "[server]",
            "port = %d" % self.port,
            "read_timeout = 120",
            "write_timeout = 120",
            "idle_timeout = 120",
            "",
            "[auth]",
            "enabled = %s" % ("true" if self.auth else "false"),
            'db_path = "%s"' % os.path.join(root, "arc.db"),
            'bootstrap_token = "%s"' % ADMIN_TOKEN,
            "",
            "[storage]",
            'backend = "local"',
            'local_path = "%s"' % storage,
            "",
            "[database]",
            "max_connections = 8",
            'temp_directory = "%s"' % tmp,
            "",
            "[compaction]",
            "enabled = false",
            'temp_directory = "%s"' % comp,
            "",
            "[telemetry]",
            "enabled = false",
            "",
            "[retention]",
            "enabled = false",
            "",
            "[continuous_query]",
            "enabled = true",
            'db_path = "%s"' % os.path.join(root, "arc.db"),
            "",
            "[delete]",
            "enabled = true",
            "",
            "[log]",
            'level = "error"',
            'format = "json"',
            "",
        ]
        lines.extend(self.extra_config.get("lines", []))
        return "\n".join(lines)

    @property
    def base_url(self):
        return "http://127.0.0.1:%d" % self.port

    @property
    def storage_dir(self):
        if self.relative_storage:
            return os.path.join(self.root, "data", "arc")
        return os.path.join(self.root, "data")

    def start(self):
        binary = os.environ.get("ARC_BIN", "/workspace/.arcbuild/arc")
        if not os.path.isfile(binary):
            raise RuntimeError("Arc binary not found at %s" % binary)
        with open(os.path.join(self.root, "arc.toml"), "w") as fh:
            fh.write(self._config())
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.root, "exports"), exist_ok=True)

        env = os.environ.copy()
        env["ARC_AUTH_BOOTSTRAP_TOKEN"] = ADMIN_TOKEN
        log = open(self.log_path, "wb")
        self.proc = subprocess.Popen(
            [binary],
            cwd=self.root,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        deadline = time.time() + 120
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    "Arc server exited during startup (code %s):\n%s"
                    % (self.proc.returncode, self.log_tail())
                )
            try:
                resp = self.request("GET", "/health", timeout=2)
                if resp.status == 200:
                    return self
            except Exception:
                pass
            time.sleep(0.25)
        raise RuntimeError("Arc server did not become healthy:\n%s" % self.log_tail())

    def log_tail(self, limit=4000):
        try:
            with open(self.log_path, "rb") as fh:
                data = fh.read()
            return data[-limit:].decode("utf-8", "replace")
        except Exception:
            return "<no log>"

    def stop(self):
        if self.proc is not None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    self.proc.terminate()
                except Exception:
                    pass
            try:
                self.proc.wait(timeout=20)
            except Exception:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except Exception:
                    pass
            self.proc = None
        shutil.rmtree(self.root, ignore_errors=True)

    # -- HTTP --------------------------------------------------------------

    def request(self, method, path, body=None, token=None, raw=None,
                headers=None, timeout=60):
        url = self.base_url + path
        if raw is not None:
            data = raw
        elif body is not None:
            data = json.dumps(body).encode()
        else:
            data = None
        req = urllib.request.Request(url, data=data, method=method)
        if body is not None and raw is None:
            req.add_header("Content-Type", "application/json")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return Response(resp.status, resp.read(), dict(resp.headers))
        except urllib.error.HTTPError as exc:
            return Response(exc.code, exc.read(), dict(exc.headers or {}))
        except Exception as exc:  # connection reset after a crash counts as a refusal
            return Response(599, ("transport error: %s" % exc).encode())

    def admin_token(self):
        return ADMIN_TOKEN

    def no_permission_token(self):
        """A token created with permissions: [] (no read/write/admin)."""
        if self._restricted_token is None:
            resp = self.request(
                "POST",
                "/api/v1/auth/tokens",
                {"name": "%s-%s" % (NO_PERMISSION_NAME, uuid.uuid4().hex[:6]),
                 "permissions": []},
                token=ADMIN_TOKEN,
            )
            payload = resp.json()
            if resp.status >= 300 or not payload or not payload.get("token"):
                raise RuntimeError("failed to create no-permission token: %r" % resp)
            self._restricted_token = payload["token"]
        return self._restricted_token

    # -- convenience -------------------------------------------------------

    def query(self, sql, token=None, headers=None, timeout=60):
        return self.request(
            "POST",
            "/api/v1/query",
            {"sql": sql},
            token=token or ADMIN_TOKEN,
            headers=headers,
            timeout=timeout,
        )

    def ingest(self, database, measurement, lines, token=None):
        """Write line-protocol points and flush; returns after the data is queryable."""
        token = token or (ADMIN_TOKEN if self.auth else None)
        resp = self.request(
            "POST",
            "/api/v1/write/line-protocol",
            raw="\n".join(lines).encode(),
            token=token,
            headers={"x-arc-database": database, "Content-Type": "text/plain"},
        )
        if resp.status >= 300:
            raise RuntimeError("line-protocol write failed: %r" % resp)
        self.request(
            "POST",
            "/api/v1/write/line-protocol/flush",
            token=token,
            timeout=60,
        )
        deadline = time.time() + 45
        while time.time() < deadline:
            resp = self.query("SELECT * FROM %s.%s" % (database, measurement), token=token)
            payload = resp.json() or {}
            if payload.get("success") and payload.get("row_count", 0) >= 1:
                return
            time.sleep(0.5)
        raise RuntimeError(
            "ingested data for %s.%s never became queryable; last=%r\n%s"
            % (database, measurement, resp, self.log_tail())
        )

    def wait_rows(self, sql, minimum=1, token=None, timeout=45):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = self.query(sql, token=token)
            payload = last.json() or {}
            if payload.get("success") and payload.get("row_count", 0) >= minimum:
                return last
            time.sleep(0.5)
        return last

    def write_export_artifact(self, name, content):
        """Create a legitimate artifact inside the export area (test bookkeeping)."""
        export_dir = os.path.join(self.storage_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        path = os.path.join(export_dir, name)
        with open(path, "wb") as fh:
            fh.write(content.encode() if isinstance(content, str) else content)
        return path

    def write_secret(self, name, content):
        """Create a file outside Arc's storage area (test bookkeeping)."""
        path = os.path.join(self.root, name)
        with open(path, "wb") as fh:
            fh.write(content.encode() if isinstance(content, str) else content)
        return path
