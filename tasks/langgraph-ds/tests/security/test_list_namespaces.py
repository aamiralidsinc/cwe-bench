"""Listing namespaces under a scope must not reveal namespaces outside it."""

from support import unique


def test_postgres_list_prefix_does_not_cross_segments(pg_store):
    own = unique("lt")
    other = own + "x"
    pg_store.put((own,), "a", {"v": 1})
    pg_store.put((other,), "b", {"v": 2})

    got = [tuple(ns) for ns in pg_store.list_namespaces(prefix=(own,))]
    assert (other,) not in got
    assert (own,) in got


def test_sqlite_list_prefix_does_not_cross_segments(sqlite_store):
    own = unique("lt")
    other = own + "x"
    sqlite_store.put((own,), "a", {"v": 1})
    sqlite_store.put((other,), "b", {"v": 2})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(prefix=(own,))]
    assert (other,) not in got
    assert (own,) in got


def test_postgres_list_suffix_does_not_start_mid_segment(pg_store):
    head = unique("ls")
    pg_store.put((head, "alice"), "a", {"v": 1})
    pg_store.put((head, "malice"), "b", {"v": 2})

    got = [tuple(ns) for ns in pg_store.list_namespaces(suffix=("alice",))]
    assert (head, "malice") not in got
    assert (head, "alice") in got


def test_sqlite_list_suffix_does_not_start_mid_segment(sqlite_store):
    head = unique("ls")
    sqlite_store.put((head, "alice"), "a", {"v": 1})
    sqlite_store.put((head, "malice"), "b", {"v": 2})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(suffix=("alice",))]
    assert (head, "malice") not in got
    assert (head, "alice") in got


def test_postgres_list_wildcard_matches_one_segment(pg_store):
    base = unique("lc")
    pg_store.put((base, "a", "v1"), "one", {"v": 1})
    pg_store.put((base, "a", "b", "v1"), "deep", {"v": 2})

    got = [tuple(ns) for ns in pg_store.list_namespaces(prefix=(base, "*", "v1"))]
    assert (base, "a", "b", "v1") not in got
    assert (base, "a", "v1") in got


def test_sqlite_list_wildcard_matches_one_segment(sqlite_store):
    base = unique("lc")
    sqlite_store.put((base, "a", "v1"), "one", {"v": 1})
    sqlite_store.put((base, "a", "b", "v1"), "deep", {"v": 2})

    got = [tuple(ns) for ns in sqlite_store.list_namespaces(prefix=(base, "*", "v1"))]
    assert (base, "a", "b", "v1") not in got
    assert (base, "a", "v1") in got
