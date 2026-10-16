"""V3 — the node will start with authentication disabled (anonymous caller gets
full read/write/federate permissions) while bound to a NON-loopback address,
exposing a fully unauthenticated, fully privileged API to the network.

Security property: the auth-disabled mode must be confined to a loopback
deployment; starting it on a public/non-loopback node_url must be refused.
"""
from __future__ import annotations

import pytest

import conftest as H


def _boot(settings_guard, tmp_path, host, node_url):
    return H.start_node(
        settings_guard,
        lambda: H.Settings(
            db_path=str(tmp_path / "v3.db"),
            auth_required=False,
            host=host,
            node_url=node_url,
        ),
    )


@pytest.mark.parametrize(
    ("host", "node_url"),
    [
        ("0.0.0.0", "http://stigmem.example.com:8765"),
        ("198.51.100.7", "http://198.51.100.7:8080"),
    ],
)
def test_auth_disabled_refused_on_non_loopback(settings_guard, tmp_path, host, node_url):
    booted = _boot(settings_guard, tmp_path, host, node_url)
    assert not booted, (
        f"node started unauthenticated (anonymous full access) on non-loopback {node_url!r}"
    )
