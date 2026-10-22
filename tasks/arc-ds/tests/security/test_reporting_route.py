"""Stored report definitions are executed later, on an engine connection.

A report is a reusable aggregate query: one request stores the definition and
a later request runs it. Running a stored definition must not let a client
turn the report engine into a reader of local files outside Arc's storage.
"""

import pytest

from arc_harness import ArcServer, is_refused

MARKER = "arc-report-marker-6c2f18"


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    server.ingest(
        "rpdb",
        "m",
        [
            "m,host=a value=11 1700000000000000000",
            "m,host=b value=22 1700000000060000000",
        ],
    )
    yield server
    server.stop()


def _lit(path):
    return "'" + path.replace("'", "''") + "'"


def _create(server, name, query):
    return server.request(
        "POST",
        "/api/v1/reports/",
        {
            "name": name,
            "database": "rpdb",
            "measurement": "m",
            "query": query,
        },
        token=server.admin_token(),
    )


def _run_attack(server, name, query):
    """Store a definition, then run it; return the run response."""
    created = _create(server, name, query)
    if is_refused(created, MARKER):
        return created  # refused at definition time
    payload = created.json() or {}
    report_id = payload.get("id")
    assert report_id, created
    return server.request(
        "POST",
        "/api/v1/reports/%s/run" % report_id,
        {},
        token=server.admin_token(),
    )


def test_stored_report_cannot_read_local_text(arc):
    secret = arc.write_secret("arc-report-marker-6c2f18.txt", MARKER + "\n")
    resp = _run_attack(
        arc,
        "leak_text",
        "SELECT content AS c FROM read_text(%s)" % _lit(secret),
    )
    assert is_refused(resp, MARKER), resp


def test_stored_report_cannot_read_local_csv(arc):
    secret = arc.write_secret("arc-report-marker-6c2f18.csv", "%s,1\n" % MARKER)
    resp = _run_attack(
        arc,
        "leak_csv",
        "SELECT * FROM read_csv(%s, header=false)" % _lit(secret),
    )
    assert is_refused(resp, MARKER), resp
