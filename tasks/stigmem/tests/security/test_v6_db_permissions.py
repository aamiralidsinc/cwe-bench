"""V6 — on startup the node creates its local SQLite database (which holds API
key hashes, facts and federation material) with default file permissions,
leaving it group/other-readable to other local users.

Security property: the local database artifacts must be created
owner-accessible only (no group/other permission bits).
"""
from __future__ import annotations

import os
import stat

import pytest
from fastapi.testclient import TestClient

import conftest as H
from stigmem_node.main import create_app


def test_sqlite_database_is_owner_only_after_startup(settings_guard, tmp_path):
    db_path = str(tmp_path / "node.db")
    s = H.Settings(
        db_path=db_path,
        auth_required=True,
        host="127.0.0.1",
        node_url="http://localhost:8765",
    )
    settings_guard(s)
    app = create_app()
    with TestClient(app):
        pass

    assert os.path.exists(db_path), "node did not create its database file"
    mode = stat.S_IMODE(os.stat(db_path).st_mode)
    group_other = mode & 0o077
    assert group_other == 0, (
        f"SQLite database is accessible to group/other (mode={oct(mode)}); "
        "it must be owner-only"
    )
