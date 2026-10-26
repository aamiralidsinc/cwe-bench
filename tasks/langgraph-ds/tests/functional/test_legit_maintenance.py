"""In-scope bulk reads and removals must keep affecting exactly the in-scope items."""

from support import namespaces, unique


def test_postgres_bulk_removal_removes_the_scope(pg_store):
    base = unique("rm")
    pg_store.put((base,), "root", {"v": 1})
    pg_store.put((base, "a"), "child", {"v": 2})
    unrelated = unique("other")
    pg_store.put((unrelated,), "keep", {"v": 3})

    pg_store.delete_namespace((base,))

    assert pg_store.get((base,), "root") is None
    assert pg_store.get((base, "a"), "child") is None
    assert pg_store.get((unrelated,), "keep") is not None


def test_sqlite_bulk_removal_removes_the_scope(sqlite_store):
    base = unique("rm")
    sqlite_store.put((base,), "root", {"v": 1})
    sqlite_store.put((base, "a"), "child", {"v": 2})
    unrelated = unique("other")
    sqlite_store.put((unrelated,), "keep", {"v": 3})

    sqlite_store.delete_namespace((base,))

    assert sqlite_store.get((base,), "root") is None
    assert sqlite_store.get((base, "a"), "child") is None
    assert sqlite_store.get((unrelated,), "keep") is not None


def test_postgres_bulk_export_returns_the_scope(pg_store):
    base = unique("ex")
    pg_store.put((base,), "root", {"v": 1})
    pg_store.put((base, "a"), "child", {"v": 2})

    got = namespaces(pg_store.export_namespace((base,)))
    assert (base,) in got
    assert (base, "a") in got


def test_sqlite_bulk_export_returns_the_scope(sqlite_store):
    base = unique("ex")
    sqlite_store.put((base,), "root", {"v": 1})
    sqlite_store.put((base, "a"), "child", {"v": 2})

    got = namespaces(sqlite_store.export_namespace((base,)))
    assert (base,) in got
    assert (base, "a") in got
