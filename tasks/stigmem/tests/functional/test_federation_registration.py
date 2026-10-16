"""Functional: legitimate federation peer registration must keep working. A
valid, correctly self-signed declaration must be accepted into the registration
pipeline (HTTP 201) and must NOT be wrongly rejected — a fix may hold the peer
for approval, but it must not break the registration feature outright.
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

import conftest as H
from stigmem_node.db import apply_migrations
from stigmem_node.main import create_app


def test_valid_declaration_is_accepted_not_rejected(settings_guard, tmp_path, monkeypatch):
    db = str(tmp_path / "fedreg.db")
    apply_migrations(db_path=db)
    node_pub, node_priv = H.gen_keypair()
    H.seed_node_identity(db, "stigmem://node-a", node_pub, node_priv)
    s = H.Settings(
        db_path=db,
        auth_required=False,
        host="127.0.0.1",
        node_url="http://localhost:8765",
        federation_enabled=True,
        federation_insecure=True,
        federation_pubkey=node_pub,
        federation_privkey=node_priv,
    )
    settings_guard(s)

    peer_pub, peer_priv = H.gen_keypair()
    peer_node = f"stigmem://partner-{uuid.uuid4()}"
    H.install_wellknown_mock(monkeypatch, peer_pub)
    fields = {
        "allowed_scopes": ["public"],
        "federation_pubkey": peer_pub,
        "node_id": peer_node,
        "node_url": "http://partner",
        "signed_at": "2026-05-02T00:00:00Z",
    }
    body = {**fields, "declaration_sig": H.sign_declaration(peer_priv, fields)}

    with TestClient(create_app(), raise_server_exceptions=False) as client:
        r = client.post("/v1/federation/peers", json=body)

    assert r.status_code == 201, r.text
    status = r.json().get("status")
    assert status != "rejected", (
        f"a valid self-signed declaration was rejected (status={status!r}); "
        "registration must still accept legitimate peers"
    )
