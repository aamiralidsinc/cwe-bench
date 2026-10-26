"""Ordinary in-scope namespace listings must keep working exactly as before."""

from support import unique


def test_sqlite_list_prefix_returns_scope_members(sqlite_store):
    base = unique("lok")
    sqlite_store.put((base,), "root", {"v": 1})
    sqlite_store.put((base, "a"), "child", {"v": 2})
    sqlite_store.put((base, "a", "b"), "grandchild", {"v": 3})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(prefix=(base,))]
    assert (base,) in got
    assert (base, "a") in got
    assert (base, "a", "b") in got


def test_postgres_list_prefix_returns_scope_members(pg_store):
    base = unique("lok")
    pg_store.put((base,), "root", {"v": 1})
    pg_store.put((base, "a"), "child", {"v": 2})
    pg_store.put((base, "a", "b"), "grandchild", {"v": 3})

    got = [tuple(ns) for ns in pg_store.list_namespaces(prefix=(base,))]
    assert (base,) in got
    assert (base, "a") in got
    assert (base, "a", "b") in got


def test_sqlite_list_suffix_returns_the_match(sqlite_store):
    head = unique("sok")
    sqlite_store.put((head, "public"), "a", {"v": 1})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(suffix=("public",))]
    assert (head, "public") in got


def test_postgres_list_suffix_returns_the_match(pg_store):
    head = unique("sok")
    pg_store.put((head, "public"), "a", {"v": 1})

    got = [tuple(ns) for ns in pg_store.list_namespaces(suffix=("public",))]
    assert (head, "public") in got


def test_sqlite_list_wildcard_returns_the_single_segment_match(sqlite_store):
    base = unique("cok")
    sqlite_store.put((base, "x", "v1"), "one", {"v": 1})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(prefix=(base, "*", "v1"))]
    assert (base, "x", "v1") in got


def test_sqlite_list_max_depth_truncates(sqlite_store):
    base = unique("mok")
    sqlite_store.put((base, "a", "b", "c"), "deep", {"v": 1})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(prefix=(base,), max_depth=2)]
    assert (base, "a") in got


def test_postgres_list_without_scope_returns_stored_namespaces(pg_store):
    base = unique("all")
    pg_store.put((base, "one"), "a", {"v": 1})

    got = [tuple(ns) for ns in pg_store.list_namespaces()]
    assert (base, "one") in got
