"""V2 — the node will start with federation enabled but mTLS disabled
(explicit insecure opt-in) while bound to a NON-loopback address, exposing
unauthenticated federation over cleartext to the network.

Security property: the insecure/no-mTLS federation opt-in must be confined to a
loopback deployment; starting it on a public/non-loopback node_url must be
refused (a deliberate refusal, not a crash).
"""
from __future__ import annotations

import pytest

import conftest as H


def _boot(settings_guard, tmp_path, host, node_url):
    return H.start_node(
        settings_guard,
        lambda: H.Settings(
            db_path=str(tmp_path / "v2.db"),
            federation_enabled=True,
            federation_insecure=True,
            host=host,
            node_url=node_url,
        ),
    )


@pytest.mark.parametrize(
    ("host", "node_url"),
    [
        ("0.0.0.0", "http://stigmem.example.com:8765"),
        ("203.0.113.10", "http://203.0.113.10:8765"),
    ],
)
def test_insecure_federation_refused_on_non_loopback(settings_guard, tmp_path, host, node_url):
    booted = _boot(settings_guard, tmp_path, host, node_url)
    assert not booted, (
        f"node started insecure federation (no mTLS) on non-loopback {node_url!r}"
    )
