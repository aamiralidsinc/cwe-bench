"""A similarity read scoped to a namespace must not reach another namespace."""

from support import namespaces, unique


def test_similarity_search_does_not_cross_segments(sqlite_vector_store):
    own = unique("vec")
    other = own + "x"
    sqlite_vector_store.put((own,), "own", {"text": "alpha"})
    sqlite_vector_store.put((other,), "other", {"text": "alpha"})

    got = namespaces(sqlite_vector_store.search((own,), query="alpha", limit=10))
    assert (other,) not in got
    assert (own,) in got
