"""Functional: normal authenticated node operation must keep working. Creating
an API key and listing keys exercises a database write and read through the
HTTP surface — so a fix that over-restricts the database (e.g. makes it
inaccessible) is caught here.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import conftest as H
from stigmem_node.db import apply_migrations
from stigmem_node.main import create_app


def test_authenticated_key_listing_works(settings_guard, tmp_path):
    db = str(tmp_path / "op.db")
    apply_migrations(db_path=db)
    s = H.Settings(
        db_path=db,
        auth_required=True,
        host="127.0.0.1",
        node_url="http://localhost:8765",
    )
    settings_guard(s)

    from stigmem_node.auth import create_api_key

    raw = create_api_key("agent:operator", ["read", "write"])

    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        r = client.get("/v1/auth/keys", headers={"Authorization": f"Bearer {raw}"})
        assert r.status_code == 200, r.text
        assert any(k["entity_uri"] == "agent:operator" for k in r.json())
