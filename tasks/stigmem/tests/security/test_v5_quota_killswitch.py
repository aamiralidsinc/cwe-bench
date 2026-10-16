"""V5 — the node will start with BOTH the read and write rate-limit quotas set
to 0 (quota enforcement fully disabled) without any explicit operator
acknowledgement, silently accepting unbounded read/write traffic.

Security property: fully disabling quota enforcement must require an explicit
operator acknowledgement; without it the node must refuse to start (a deliberate
refusal, not a crash).
"""
from __future__ import annotations

import conftest as H


def test_quota_killswitch_refused_without_acknowledgement(settings_guard, tmp_path):
    booted = H.start_node(
        settings_guard,
        lambda: H.Settings(
            db_path=str(tmp_path / "v5.db"),
            host="127.0.0.1",
            node_url="http://localhost:8765",
            rate_limit_write_per_hour=0,
            rate_limit_read_per_hour=0,
        ),
    )

    assert not booted, (
        "node started with quota enforcement fully disabled (read=0, write=0) "
        "and no explicit operator acknowledgement"
    )
