"""Small in-process harness for the gateway configuration and invocation routes.

It starts a throwaway sqlite tracking store and a local TCP listener ("canary")
that records any connection a gateway call makes.  Everything runs in-process;
no external network is used.
"""

import json
import os
import socket
import sqlite3
import tempfile
import threading
import uuid

_TMP = tempfile.mkdtemp(prefix="mlflow-gw-")
_DB = os.path.join(_TMP, "mlflow.db")
_URI = "sqlite:///" + _DB

os.environ["MLFLOW_TRACKING_URI"] = _URI
os.environ["_MLFLOW_SERVER_FILE_STORE"] = _URI
os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = "file://" + _TMP + "/artifacts"
os.environ.setdefault("MLFLOW_CRYPTO_KEK_PASSPHRASE", "task-passphrase")
# The verifier runs with a clean environment; make sure no opt-in for internal
# upstreams leaks in from the host.
for _key in [k for k in os.environ if "ALLOW_PRIVATE" in k.upper()]:
    os.environ.pop(_key, None)

import flask  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

import mlflow  # noqa: E402

mlflow.set_tracking_uri(_URI)

from mlflow.server import handlers  # noqa: E402
from mlflow.server.gateway_api import gateway_router  # noqa: E402

_store = handlers._get_tracking_store()
_app = FastAPI()
_app.include_router(gateway_router)
client = TestClient(_app, raise_server_exceptions=False)
_flask = flask.Flask("gateway-tests")


def unique(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def call(func, body):
    with _flask.test_request_context(json=body, method="POST"):
        response = func()
        data = response.get_data(as_text=True)
        return response.status_code, (json.loads(data) if data else {})


def create_secret(secret_name, secret_value=None, provider=None, auth_config=None):
    body = {
        "secret_name": secret_name,
        "secret_value": secret_value if secret_value is not None else {"api_key": "sk-test"},
    }
    if provider:
        body["provider"] = provider
    if auth_config is not None:
        body["auth_config"] = auth_config
    return call(handlers._create_gateway_secret, body)


def update_secret(secret_id, secret_value=None, auth_config=None):
    body = {"secret_id": secret_id}
    if secret_value is not None:
        body["secret_value"] = secret_value
    if auth_config is not None:
        body["auth_config"] = auth_config
    return call(handlers._update_gateway_secret, body)


def get_secret(secret_id):
    return call(handlers._get_gateway_secret_info, {"secret_id": secret_id})


def list_secrets():
    return call(handlers._list_gateway_secrets, {})


def list_secret_names():
    status, data = list_secrets()
    if status != 200:
        return set()
    return {s.get("secret_name") for s in data.get("secrets", [])}


def create_model_definition(name, secret_id, provider, model_name):
    return call(
        handlers._create_gateway_model_definition,
        {"name": name, "secret_id": secret_id, "provider": provider, "model_name": model_name},
    )


def create_endpoint(name, model_definition_id):
    return call(
        handlers._create_gateway_endpoint,
        {
            "name": name,
            "model_configs": [
                {
                    "model_definition_id": model_definition_id,
                    "linkage_type": "PRIMARY",
                    "weight": 1.0,
                }
            ],
        },
    )


def get_endpoint(name):
    return call(handlers._get_gateway_endpoint, {"name": name})


def invoke(name, payload=None):
    payload = payload or {"messages": [{"role": "user", "content": "hi"}]}
    return client.post(
        "/gateway/mlflow/v1/chat/completions", json={"model": name, **payload}
    )


def raw_sql_set_auth_config(secret_id, auth_config):
    """Write a configuration row directly, as an operator with database access would."""
    connection = sqlite3.connect(_DB)
    try:
        connection.execute(
            "UPDATE secrets SET auth_config = ? WHERE secret_id = ?",
            (json.dumps(auth_config), secret_id),
        )
        connection.commit()
    finally:
        connection.close()


class Canary:
    """TCP listener that records connections and answers plain-HTTP POSTs."""

    def __init__(self, port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(16)
        self.port = self.sock.getsockname()[1]
        self.hits = []
        self._stop = False
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self):
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        try:
            conn.settimeout(2.0)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 65536:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            if not data:
                return
            head = data.split(b"\r\n\r\n", 1)[0]
            line = head.split(b"\r\n", 1)[0].decode("latin-1", "replace")
            self.hits.append({"line": line, "tls": data[:1] == b"\x16"})
            if data[:1] == b"\x16":
                return  # TLS ClientHello: the connection alone is the signal
            length = 0
            for header in head.split(b"\r\n")[1:]:
                if header.lower().startswith(b"content-length:"):
                    length = int(header.split(b":", 1)[1].strip())
            body = data.split(b"\r\n\r\n", 1)[1]
            while len(body) < length:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                body += chunk
            payload = json.dumps(
                {
                    "id": "canary",
                    "object": "chat.completion",
                    "created": 1,
                    "model": "m",
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": "ok"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
            ).encode()
            conn.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\nConnection: close\r\n\r\n"
                + payload
            )
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def close(self):
        self._stop = True
        try:
            self.sock.close()
        except Exception:
            pass

    def count(self):
        return len(self.hits)
