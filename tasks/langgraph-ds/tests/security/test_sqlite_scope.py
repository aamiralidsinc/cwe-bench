"""A read scoped to a namespace must not reach items stored under another namespace
(SQLite backend)."""

from support import namespaces, unique


def test_prefix_does_not_cross_segments(sqlite_store):
    own = unique("team")
    other = own + "x"
    sqlite_store.put((own,), "own", {"v": 1})
    sqlite_store.put((other,), "other", {"v": 2})

    got = namespaces(sqlite_store.search((own,)))
    assert (other,) not in got
    assert (own,) in got


def test_prefix_with_underscore_label_is_literal(sqlite_store):
    tag = unique("u")
    own = f"user_{tag}"
    other = f"userX{tag}"
    sqlite_store.put((own,), "own", {"v": 1})
    sqlite_store.put((other, "sub"), "other", {"v": 2})

    got = namespaces(sqlite_store.search((own,)))
    assert (other, "sub") not in got


def test_prefix_with_percent_label_is_literal(sqlite_store):
    tag = unique("p")
    own = f"pct{tag}%"
    other = f"pct{tag}0"
    sqlite_store.put((own,), "own", {"v": 1})
    sqlite_store.put((other, "sub"), "other", {"v": 2})

    got = namespaces(sqlite_store.search((own,)))
    assert (other, "sub") not in got


def test_prefix_does_not_match_a_different_letter_case(sqlite_store):
    tag = unique("acct")
    lower = f"acct{tag}"
    upper = lower.upper()
    sqlite_store.put((lower,), "own", {"v": 1})
    sqlite_store.put((upper, "sub"), "other", {"v": 2})

    got = namespaces(sqlite_store.search((lower,)))
    assert (upper, "sub") not in got


def test_scope_with_period_is_not_reinterpreted(sqlite_store):
    outer = unique("dot")
    inner = unique("sub")
    sqlite_store.put((outer, inner), "k", {"v": 1})

    try:
        got = namespaces(sqlite_store.search((f"{outer}.{inner}",)))
    except Exception:
        got = None
    if got is not None:
        assert (outer, inner) not in got

    assert (outer, inner) in namespaces(sqlite_store.search((outer,)))
