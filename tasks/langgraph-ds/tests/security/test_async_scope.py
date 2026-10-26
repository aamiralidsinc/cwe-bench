"""The asynchronous entry points must enforce the same namespace scope."""

import asyncio

from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.sqlite.aio import AsyncSqliteStore
from support import PG_URI, namespaces, unique


def test_postgres_async_search_does_not_cross_segments():
    own = unique("ateam")
    other = own + "x"

    async def run():
        async with AsyncPostgresStore.from_conn_string(PG_URI) as store:
            await store.setup()
            await store.aput((own,), "own", {"v": 1})
            await store.aput((other,), "other", {"v": 2})
            return namespaces(await store.asearch((own,)))

    got = asyncio.run(run())
    assert (other,) not in got
    assert (own,) in got


def test_sqlite_async_search_does_not_cross_segments(tmp_path):
    own = unique("ateam")
    other = own + "x"

    async def run():
        async with AsyncSqliteStore.from_conn_string(str(tmp_path / "async.db")) as store:
            await store.setup()
            await store.aput((own,), "own", {"v": 1})
            await store.aput((other,), "other", {"v": 2})
            return namespaces(await store.asearch((own,)))

    got = asyncio.run(run())
    assert (other,) not in got
    assert (own,) in got


def test_sqlite_async_list_wildcard_matches_one_segment(tmp_path):
    base = unique("acache")

    async def run():
        async with AsyncSqliteStore.from_conn_string(str(tmp_path / "async2.db")) as store:
            await store.setup()
            await store.aput((base, "a", "v1"), "one", {"v": 1})
            await store.aput((base, "a", "b", "v1"), "deep", {"v": 2})
            return [tuple(ns) for ns in await store.alist_namespaces(prefix=(base, "*", "v1"))]

    got = asyncio.run(run())
    assert (base, "a", "b", "v1") not in got
    assert (base, "a", "v1") in got
