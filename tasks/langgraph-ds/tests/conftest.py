"""Fixtures for the behavioural suites.

The verifier entry point starts a local PostgreSQL server before any group runs; the SQLite
stores are ordinary in-process databases under the test's temporary directory.
"""

from __future__ import annotations

import pytest

from langgraph.store.postgres import PostgresStore
from langgraph.store.sqlite import SqliteStore
from support import PG_URI


@pytest.fixture(scope="session")
def pg_store():
    with PostgresStore.from_conn_string(PG_URI) as store:
        store.setup()
        yield store


@pytest.fixture()
def sqlite_store(tmp_path):
    with SqliteStore.from_conn_string(str(tmp_path / "store.db")) as store:
        store.setup()
        yield store


def _constant_embedding(texts):
    return [[1.0] for _ in texts]


@pytest.fixture()
def sqlite_vector_store(tmp_path):
    with SqliteStore.from_conn_string(
        str(tmp_path / "vectors.db"),
        index={"dims": 1, "embed": _constant_embedding, "fields": ["text"]},
    ) as store:
        store.setup()
        yield store
