"""The per-measurement read endpoint accepts filter text too.

The endpoint builds its own statement from the path and query string, so it is
a separate route into the same query engine. A filter supplied by the client
must not be able to read a local file.
"""

import urllib.parse

import pytest

from arc_harness import ArcServer, is_refused

MARKER = "arc-meas-marker-93d4a1"


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    server.ingest(
        "measdb",
        "m",
        [
            "m,host=a value=11 1700000000000000000",
            "m,host=b value=22 1700000000060000000",
        ],
    )
    yield server
    server.stop()


def _secret(server):
    return server.write_secret("arc-meas-marker-93d4a1.txt", MARKER + "\n")


def _measurement(server, where):
    query = urllib.parse.urlencode({"database": "measdb", "where": where})
    return server.request(
        "GET",
        "/api/v1/query/m?" + query,
        token=server.no_permission_token(),
    )


def test_filter_cannot_read_local_text(arc):
    path = _secret(arc)
    where = (
        "1=1 AND (SELECT count(*) FROM measdb.m, read_text('%s') "
        "WHERE content LIKE '%s%%') > 0" % (path, MARKER)
    )
    resp = _measurement(arc, where)
    assert is_refused(resp, MARKER), resp


def test_filter_cannot_read_local_csv(arc):
    path = arc.write_secret("arc-meas-marker-93d4a1.csv", "%s\nx\n" % MARKER)
    where = (
        "1=1 AND (SELECT count(*) FROM measdb.m, read_csv('%s') "
        "WHERE \"%s\" = 'x') > 0" % (path, MARKER)
    )
    resp = _measurement(arc, where)
    assert is_refused(resp, MARKER), resp
