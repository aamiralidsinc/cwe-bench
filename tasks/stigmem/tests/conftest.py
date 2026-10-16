"""Self-contained test harness for the stigmem reference node.

IMPORTANT: these tests never import anything from /app/node/tests (the solver
may edit those). Every helper here drives the node only through its installed
public surface: `stigmem_node.main.create_app` (the FastAPI app / HTTP surface),
`stigmem_node.db.apply_migrations` (node startup DB init), the plugin
registration entry point, and the settings object.
"""
from __future__ import annotations

import base64
import contextlib
import importlib
import json
import sqlite3
import sys
import time
import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

import stigmem_node.settings as settings_module

Settings = settings_module.Settings


# ---------------------------------------------------------------------------
# Crypto helpers (Ed25519 peer declarations and peer tokens, spec §3.5/§6.1)
# ---------------------------------------------------------------------------
def gen_keypair() -> tuple[str, str]:
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pr = (
        base64.urlsafe_b64encode(
            priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        )
        .decode()
        .rstrip("=")
    )
    pb = base64.urlsafe_b64encode(pub.public_bytes(Encoding.Raw, PublicFormat.Raw)).decode().rstrip(
        "="
    )
    return pb, pr


def sign_declaration(priv_b64: str, signed_fields: dict) -> str:
    raw = base64.urlsafe_b64decode(priv_b64 + "=" * (-len(priv_b64) % 4))
    k = Ed25519PrivateKey.from_private_bytes(raw)
    canonical = json.dumps(signed_fields, sort_keys=True, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(k.sign(canonical)).decode().rstrip("=")


def make_peer_token(priv_b64: str, iss: str, sub: str, scopes: list[str]) -> str:
    import jwt

    raw = base64.urlsafe_b64decode(priv_b64 + "=" * (-len(priv_b64) % 4))
    k = Ed25519PrivateKey.from_private_bytes(raw)
    now = int(time.time() * 1000)
    payload = {
        "iss": iss,
        "sub": sub,
        "iat": now,
        "exp": now + 3_600_000,
        "nonce": str(uuid.uuid4()),
        "scopes": scopes,
    }
    return jwt.encode(payload, k, algorithm="EdDSA")


# ---------------------------------------------------------------------------
# Global settings patching. Many node modules capture `settings` at import via
# `from .settings import settings`, so swapping the one object is not enough;
# we reassign the attribute on every already-imported stigmem_node module that
# holds a Settings instance, matching how the node is configured at process
# start.
# ---------------------------------------------------------------------------
def apply_settings(s: Settings) -> None:
    settings_module.settings = s
    for name, mod in list(sys.modules.items()):
        if not name.startswith("stigmem_node"):
            continue
        cur = getattr(mod, "settings", None)
        if isinstance(cur, Settings):
            try:
                mod.settings = s
            except Exception:
                pass
    # A few modules that may not yet be imported but are needed by create_app.
    for name in (
        "stigmem_node.auth",
        "stigmem_node.db",
        "stigmem_node.main",
        "stigmem_node.routes.wellknown",
        "stigmem_node.rate_limit",
    ):
        with contextlib.suppress(ImportError):
            m = importlib.import_module(name)
            if hasattr(m, "settings"):
                m.settings = s


# ---------------------------------------------------------------------------
# Startup outcome. The instruction asks the node to REFUSE some startup
# configurations but does not say how, so any deliberate refusal counts: an
# error raised while the settings are validated, while the app is built, or
# during service startup (a RuntimeError, a ValueError / validation error, a
# custom error class, or an exit). A crash does not count: an exception type
# that signals a programming error (e.g. an AttributeError from reading a
# setting that does not exist) only breaks startup by accident.
# ---------------------------------------------------------------------------
CRASH_TYPES = (
    NameError,
    AttributeError,
    ImportError,
    TypeError,
    LookupError,
    ArithmeticError,
    NotImplementedError,
    RecursionError,
    SyntaxError,
    sqlite3.Error,
)


def _leaves(exc: BaseException):
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            yield from _leaves(sub)
    else:
        yield exc


def start_node(settings_guard, make_settings) -> bool:
    """Validate the settings, build the app and run its startup.

    Returns True when the node started and False when it refused to start.
    Fails the calling test when startup crashed instead of refusing.
    """
    import asyncio

    from fastapi.testclient import TestClient

    try:
        s = make_settings()
        settings_guard(s)
        from stigmem_node.main import create_app

        app = create_app()
        with TestClient(app):
            return True
    # SystemExit raised inside the startup hook reaches the caller as CancelledError.
    except (Exception, SystemExit, asyncio.CancelledError) as exc:
        leaves = list(_leaves(exc))
        if all(isinstance(x, CRASH_TYPES) for x in leaves):
            pytest.fail(
                "startup crashed instead of refusing: "
                + "; ".join(f"{type(x).__name__}: {x}" for x in leaves)
            )
        return False


@pytest.fixture()
def settings_guard():
    """Restore the original global settings after each test that mutates it."""
    original = settings_module.settings
    yield apply_settings
    apply_settings(original)


def seed_node_identity(db_path: str, node_id: str, pub_b64: str, priv_b64: str) -> None:
    """Persist this node's own federation identity in node_meta."""
    conn = sqlite3.connect(db_path)
    for k, v in (
        ("node_id", node_id),
        ("federation_pubkey", pub_b64),
        ("federation_privkey", priv_b64),
    ):
        conn.execute("INSERT OR REPLACE INTO node_meta (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


class _MockWellKnown:
    """Stand-in httpx.AsyncClient that serves a peer's published pubkey over the
    well-known fetch the registration flow performs (keeps the test offline)."""

    def __init__(self, pubkey: str) -> None:
        self._pubkey = pubkey

    def __call__(self, **_: Any) -> "_MockWellKnown":
        return self

    async def __aenter__(self) -> "_MockWellKnown":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, url: str):  # noqa: ANN001
        import httpx

        return httpx.Response(200, json={"federation_pubkey": self._pubkey})


def install_wellknown_mock(monkeypatch: pytest.MonkeyPatch, pubkey: str) -> None:
    import stigmem_node.routes._federation_impl as fed_impl

    monkeypatch.setattr(fed_impl.httpx, "AsyncClient", _MockWellKnown(pubkey))
