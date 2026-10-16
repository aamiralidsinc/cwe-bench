"""Functional: legitimate startup configurations must keep working. A correct
fix confines the insecure opt-ins to loopback deployments; it must NOT refuse
the loopback/dev configurations themselves, the ordinary secure default, or a
secure node bound to a public address.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import conftest as H
from stigmem_node.main import create_app


def _boots_and_healthy(settings_guard, s) -> bool:
    settings_guard(s)
    app = create_app()
    with TestClient(app) as client:
        r = client.get("/healthz")
        return r.status_code == 200


def test_secure_default_node_boots(settings_guard, tmp_path):
    s = H.Settings(
        db_path=str(tmp_path / "secure.db"),
        auth_required=True,
        host="127.0.0.1",
        node_url="http://localhost:8765",
    )
    assert _boots_and_healthy(settings_guard, s)


@pytest.mark.parametrize(
    ("host", "node_url"),
    [
        ("0.0.0.0", "http://stigmem.example.com:8765"),
        ("203.0.113.10", "http://203.0.113.10:8765"),
    ],
)
def test_secure_node_boots_on_public_address(settings_guard, tmp_path, host, node_url):
    # Only the insecure opt-ins are to be refused on a public address; an
    # ordinary authenticated node with transport security left at its default
    # must still start there.
    s = H.Settings(
        db_path=str(tmp_path / "public.db"),
        auth_required=True,
        federation_insecure=False,
        host=host,
        node_url=node_url,
    )
    assert _boots_and_healthy(settings_guard, s)


def test_insecure_federation_allowed_on_loopback(settings_guard, tmp_path):
    s = H.Settings(
        db_path=str(tmp_path / "fedloop.db"),
        federation_enabled=True,
        federation_insecure=True,
        host="127.0.0.1",
        node_url="http://127.0.0.1:8765",
    )
    assert _boots_and_healthy(settings_guard, s)


def test_auth_disabled_allowed_on_loopback(settings_guard, tmp_path):
    s = H.Settings(
        db_path=str(tmp_path / "authloop.db"),
        auth_required=False,
        host="127.0.0.1",
        node_url="http://localhost:8765",
    )
    assert _boots_and_healthy(settings_guard, s)
