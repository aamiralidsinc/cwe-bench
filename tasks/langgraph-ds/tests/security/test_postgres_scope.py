"""A read scoped to a namespace must not reach items stored under another namespace
(PostgreSQL backend)."""

from support import namespaces, unique


def test_prefix_does_not_cross_segments(pg_store):
    own = unique("team")
    other = own + "x"
    pg_store.put((own,), "own", {"v": 1})
    pg_store.put((other,), "other", {"v": 2})

    got = namespaces(pg_store.search((own,)))
    assert (other,) not in got
    assert (own,) in got


def test_prefix_with_underscore_label_is_literal(pg_store):
    tag = unique("u")
    own = f"user_{tag}"
    other = f"userX{tag}"
    pg_store.put((own,), "own", {"v": 1})
    pg_store.put((other, "sub"), "other", {"v": 2})

    got = namespaces(pg_store.search((own,)))
    assert (other, "sub") not in got


def test_prefix_with_percent_label_is_literal(pg_store):
    tag = unique("p")
    own = f"pct{tag}%"
    other = f"pct{tag}0"
    pg_store.put((own,), "own", {"v": 1})
    pg_store.put((other, "sub"), "other", {"v": 2})

    got = namespaces(pg_store.search((own,)))
    assert (other, "sub") not in got


def test_scope_with_period_is_not_reinterpreted(pg_store):
    outer = unique("dot")
    inner = unique("sub")
    pg_store.put((outer, inner), "k", {"v": 1})

    try:
        got = namespaces(pg_store.search((f"{outer}.{inner}",)))
    except Exception:
        got = None
    if got is not None:
        assert (outer, inner) not in got

    # the store keeps serving an ordinary in-scope read
    assert (outer, inner) in namespaces(pg_store.search((outer,)))
