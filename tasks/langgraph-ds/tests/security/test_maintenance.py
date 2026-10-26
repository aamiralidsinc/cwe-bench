"""A namespace-scoped bulk operation must not touch items outside its scope."""

from support import namespaces, unique


def test_postgres_bulk_removal_does_not_cross_segments(pg_store):
    own = unique("pr")
    other = own + "x"
    pg_store.put((own,), "in", {"v": 1})
    pg_store.put((other,), "out", {"v": 2})

    pg_store.delete_namespace((own,))

    assert pg_store.get((other,), "out") is not None
    assert pg_store.get((own,), "in") is None


def test_sqlite_bulk_removal_does_not_cross_segments(sqlite_store):
    own = unique("pr")
    other = own + "x"
    sqlite_store.put((own,), "in", {"v": 1})
    sqlite_store.put((other,), "out", {"v": 2})

    sqlite_store.delete_namespace((own,))

    assert sqlite_store.get((other,), "out") is not None
    assert sqlite_store.get((own,), "in") is None


def test_postgres_bulk_export_does_not_cross_segments(pg_store):
    own = unique("pe")
    other = own + "x"
    pg_store.put((own,), "in", {"v": 1})
    pg_store.put((other,), "out", {"v": 2})

    got = namespaces(pg_store.export_namespace((own,)))
    assert (other,) not in got
    assert (own,) in got


def test_sqlite_bulk_export_does_not_cross_segments(sqlite_store):
    own = unique("pe")
    other = own + "x"
    sqlite_store.put((own,), "in", {"v": 1})
    sqlite_store.put((other,), "out", {"v": 2})

    got = namespaces(sqlite_store.export_namespace((own,)))
    assert (other,) not in got
    assert (own,) in got
