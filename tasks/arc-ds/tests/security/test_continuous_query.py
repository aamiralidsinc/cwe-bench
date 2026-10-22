"""Stored query definitions run on the same engine as interactive queries.

A continuous query's SQL is stored by the server and executed later. Defining
one must not let a client smuggle a read of a local file into that execution.
"""

import time

import pytest

from arc_harness import ArcServer, is_refused, leaked

MARKER = "arc-cq-marker-44be07"


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    server.ingest(
        "cqdb",
        "src",
        [
            "src,host=a value=1 1700000000000000000",
            "src,host=b value=3 1700000000060000000",
        ],
    )
    yield server
    server.stop()


def _create(server, name, query):
    return server.request(
        "POST",
        "/api/v1/continuous_queries/",
        {
            "name": name,
            "database": "cqdb",
            "source_measurement": "src",
            "destination_measurement": name,
            "query": query,
            "interval": "1h",
            "is_active": True,
        },
        token=server.admin_token(),
    )


def test_stored_query_cannot_read_local_file(arc):
    secret = arc.write_secret("arc-cq-marker-44be07.txt", MARKER + "\n")
    query = (
        "SELECT content AS c FROM read_text('%s') "
        "WHERE {start_time} <> '' AND {end_time} <> ''" % secret
    )
    created = _create(arc, "cq_attack", query)
    if is_refused(created, MARKER):
        return  # refused at definition time
    payload = created.json() or {}
    query_id = payload.get("id")
    assert query_id, created

    executed = arc.request(
        "POST",
        "/api/v1/continuous_queries/%s/execute" % query_id,
        {},
        token=arc.admin_token(),
    )
    if is_refused(executed, MARKER):
        # Refused at execution time: the destination must not exist with data.
        dest = arc.query("SELECT * FROM cqdb.cq_attack")
        assert not leaked(dest, MARKER), dest
        return

    # The execution was allowed; the file's bytes must not appear in the
    # destination measurement that the query publishes.
    deadline = time.time() + 30
    last = None
    while time.time() < deadline:
        last = arc.query("SELECT * FROM cqdb.cq_attack")
        if leaked(last, MARKER):
            pytest.fail("stored query published a local file's contents: %r" % last)
        payload = last.json() or {}
        if payload.get("success") and payload.get("row_count", 0) > 0:
            break
        time.sleep(0.5)
