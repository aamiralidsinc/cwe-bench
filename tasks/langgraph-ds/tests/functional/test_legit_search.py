"""Ordinary in-scope reads must keep working exactly as before."""

import asyncio

from langgraph.store.postgres.aio import AsyncPostgresStore
from support import PG_URI, namespaces, unique


def test_postgres_prefix_returns_the_namespace_and_descendants(pg_store):
    base = unique("ok")
    pg_store.put((base,), "root", {"v": 1})
    pg_store.put((base, "a"), "child", {"v": 2})
    pg_store.put((base, "a", "b"), "grandchild", {"v": 3})

    got = namespaces(pg_store.search((base,)))
    assert (base,) in got
    assert (base, "a") in got
    assert (base, "a", "b") in got


def test_sqlite_prefix_returns_the_namespace_and_descendants(sqlite_store):
    base = unique("ok")
    sqlite_store.put((base,), "root", {"v": 1})
    sqlite_store.put((base, "a"), "child", {"v": 2})
    sqlite_store.put((base, "a", "b"), "grandchild", {"v": 3})

    got = namespaces(sqlite_store.search((base,)))
    assert (base,) in got
    assert (base, "a") in got
    assert (base, "a", "b") in got


def test_postgres_punctuation_labels_match_themselves(pg_store):
    tag = unique("u")
    literal = f"user_{tag}"
    percent = f"pct{tag}%"
    pg_store.put((literal,), "under", {"v": 1})
    pg_store.put((percent,), "percent", {"v": 2})

    assert (literal,) in namespaces(pg_store.search((literal,)))
    assert (percent,) in namespaces(pg_store.search((percent,)))


def test_sqlite_punctuation_labels_match_themselves(sqlite_store):
    tag = unique("u")
    literal = f"user_{tag}"
    percent = f"pct{tag}%"
    sqlite_store.put((literal,), "under", {"v": 1})
    sqlite_store.put((percent,), "percent", {"v": 2})

    assert (literal,) in namespaces(sqlite_store.search((literal,)))
    assert (percent,) in namespaces(sqlite_store.search((percent,)))


def test_sqlite_case_distinct_namespaces_keep_their_own_scope(sqlite_store):
    tag = unique("acct")
    lower = f"acct{tag}"
    upper = lower.upper()
    sqlite_store.put((lower,), "lower", {"v": 1})
    sqlite_store.put((upper,), "upper", {"v": 2})

    assert (lower,) in namespaces(sqlite_store.search((lower,)))
    assert (upper,) in namespaces(sqlite_store.search((upper,)))


def test_postgres_async_in_scope_read_returns_items():
    base = unique("aok")

    async def run():
        async with AsyncPostgresStore.from_conn_string(PG_URI) as store:
            await store.setup()
            await store.aput((base,), "root", {"v": 1})
            await store.aput((base, "a"), "child", {"v": 2})
            return namespaces(await store.asearch((base,)))

    got = asyncio.run(run())
    assert (base,) in got
    assert (base, "a") in got


def test_sqlite_similarity_read_returns_in_scope_items(sqlite_vector_store):
    base = unique("vok")
    sqlite_vector_store.put((base,), "root", {"text": "alpha"})
    sqlite_vector_store.put((base, "a"), "child", {"text": "alpha"})

    got = namespaces(sqlite_vector_store.search((base,), query="alpha", limit=10))
    assert (base,) in got
    assert (base, "a") in got
