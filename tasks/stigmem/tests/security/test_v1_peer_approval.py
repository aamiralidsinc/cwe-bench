"""V1 — a remote node can self-register as a federation peer and become fully
active with NO operator approval, then use its peer token against federation
data endpoints. Driven entirely through the HTTP surface.

Security property: a freshly self-registered peer must NOT be `active`; its
peer token must be refused at federation endpoints until an operator approves
it out of band. (The exact non-active state name is left to the implementation.)
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

import conftest as H
from stigmem_node.db import apply_migrations
from stigmem_node.main import create_app


def _fed_app(tmp_path, apply):
    db = str(tmp_path / "v1.db")
    apply_migrations(db_path=db)
    node_pub, node_priv = H.gen_keypair()
    node_id = "stigmem://node-a"
    H.seed_node_identity(db, node_id, node_pub, node_priv)
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
    apply(s)
    import stigmem_node.federation.peer_token as tok

    tok._cached_pub = node_pub
    tok._cached_priv = node_priv
    return db, node_id, create_app()


def _self_signed_declaration(peer_pub, peer_priv, node_id, node_url):
    fields = {
        "allowed_scopes": ["public"],
        "federation_pubkey": peer_pub,
        "node_id": node_id,
        "node_url": node_url,
        "signed_at": "2026-05-02T00:00:00Z",
    }
    return {**fields, "declaration_sig": H.sign_declaration(peer_priv, fields)}


def test_self_registration_does_not_auto_activate(settings_guard, tmp_path, monkeypatch):
    _db, _node_id, app = _fed_app(tmp_path, settings_guard)
    peer_pub, peer_priv = H.gen_keypair()
    peer_node = f"stigmem://attacker-{uuid.uuid4()}"
    H.install_wellknown_mock(monkeypatch, peer_pub)
    body = _self_signed_declaration(peer_pub, peer_priv, peer_node, "http://attacker")

    with TestClient(app, raise_server_exceptions=False) as client:
        r = client.post("/v1/federation/peers", json=body)
        assert r.status_code == 201, r.text
        status = r.json().get("status")

    # On vulnerable code the peer is immediately "active". A correct fix leaves
    # it in some non-active, approval-pending state.
    assert status != "active", (
        f"self-registered peer was activated without operator approval (status={status!r})"
    )


def test_unapproved_peer_token_is_refused_at_federation_endpoint(
    settings_guard, tmp_path, monkeypatch
):
    db, node_id, app = _fed_app(tmp_path, settings_guard)
    peer_pub, peer_priv = H.gen_keypair()
    peer_node = f"stigmem://attacker-{uuid.uuid4()}"
    H.install_wellknown_mock(monkeypatch, peer_pub)
    body = _self_signed_declaration(peer_pub, peer_priv, peer_node, "http://attacker")

    with TestClient(app, raise_server_exceptions=False) as client:
        reg = client.post("/v1/federation/peers", json=body)
        assert reg.status_code == 201, reg.text
        token = H.make_peer_token(peer_priv, peer_node, node_id, ["public"])
        pull = client.get(
            "/v1/federation/facts", headers={"Authorization": f"Bearer {token}"}
        )

    # On vulnerable code the self-activated peer's token is accepted (200). A
    # correct fix keeps the peer non-active so its token is rejected (any 4xx,
    # e.g. 401 or 403).
    assert 400 <= pull.status_code < 500, (
        f"unapproved peer's token was accepted at a federation endpoint "
        f"(status={pull.status_code})"
    )
