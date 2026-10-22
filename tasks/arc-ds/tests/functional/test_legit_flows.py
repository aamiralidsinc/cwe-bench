"""Legitimate Arc behaviour that must survive the fix.

These are the flows a deployment uses every day. A fix that blocks the attack
by breaking file access for Arc's own data fails here.
"""

import http.server
import os
import subprocess
import threading
import time

import pytest

from arc_harness import ArcServer

PROFILE_HEADER = {"x-arc-profile": "true"}


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    server.ingest(
        "fdb",
        "m",
        [
            "m,host=a value=1 1700000000000000000",
            "m,host=b value=2 1700000000060000000",
        ],
    )
    yield server
    server.stop()


def _payload(resp):
    payload = resp.json()
    assert isinstance(payload, dict), resp
    return payload


def test_query_returns_rows(arc):
    resp = arc.query("SELECT * FROM fdb.m ORDER BY value")
    payload = _payload(resp)
    assert resp.status == 200 and payload.get("success") is True, resp
    assert payload.get("row_count") == 2, resp
    assert "value" in payload.get("columns", []), resp


def test_profile_query_returns_timings(arc):
    resp = arc.query("SELECT * FROM fdb.m", headers=PROFILE_HEADER)
    payload = _payload(resp)
    assert resp.status == 200 and payload.get("success") is True, resp
    profile = payload.get("profile")
    assert isinstance(profile, dict), "profile object missing: %r" % resp
    timings = [profile.get("execution_ms"), profile.get("planner_ms"), profile.get("latency_ms")]
    assert any(isinstance(v, (int, float)) and v > 0 for v in timings), (
        "profile carries no timing measurement: %r" % profile
    )


def test_measurement_endpoint_filter(arc):
    resp = arc.request(
        "GET",
        "/api/v1/query/m?database=fdb&where=value%20%3E%201",
        token=arc.admin_token(),
    )
    payload = _payload(resp)
    assert resp.status == 200 and payload.get("success") is True, resp
    assert payload.get("row_count") == 1, resp


def test_preview_returns_sample(arc):
    resp = arc.request(
        "POST",
        "/api/v1/query/preview",
        {"sql": "SELECT 42 AS value"},
        token=arc.admin_token(),
    )
    payload = _payload(resp)
    assert resp.status == 200 and payload.get("success") is True, resp
    assert payload.get("data") == [[42]], resp


def test_export_download_serves_artifact(arc):
    artifact = "daily-report.csv"
    content = "time,value\n2024-01-01T00:00:00Z,7\n"
    arc.write_export_artifact(artifact, content)
    resp = arc.request(
        "GET",
        "/api/v1/export/download?path=" + artifact,
        token=arc.admin_token(),
    )
    assert resp.status == 200, resp
    assert resp.body.decode() == content, resp


def test_legitimate_delete_removes_only_matching_rows(arc):
    arc.ingest(
        "fdel",
        "d",
        [
            "d,host=a value=1 1700000000000000000",
            "d,host=b value=2 1700000000060000000",
        ],
    )
    deleted = arc.request(
        "POST",
        "/api/v1/delete/",
        {"database": "fdel", "measurement": "d", "where": "value = 1", "confirm": True},
        token=arc.admin_token(),
    )
    payload = _payload(deleted)
    assert deleted.status == 200 and payload.get("success") is True, deleted
    assert payload.get("deleted_count") == 1, deleted

    remaining = _payload(arc.query("SELECT * FROM fdel.d ORDER BY value"))
    assert remaining.get("row_count") == 1, remaining
    columns = remaining.get("columns", [])
    assert "value" in columns, remaining
    assert remaining.get("data")[0][columns.index("value")] == 2, remaining


def test_continuous_query_legitimate_aggregation(arc):
    created = arc.request(
        "POST",
        "/api/v1/continuous_queries/",
        {
            "name": "hourly_avg",
            "database": "fdb",
            "source_measurement": "m",
            "destination_measurement": "m_hourly",
            "query": (
                "SELECT avg(value) AS avg_v, "
                "time_bucket(INTERVAL '1 hour', time) AS time "
                "FROM fdb.m WHERE time >= {start_time} AND time <= {end_time} GROUP BY 2"
            ),
            "interval": "1h",
            "is_active": True,
        },
        token=arc.admin_token(),
    )
    payload = _payload(created)
    query_id = payload.get("id")
    assert query_id, created

    executed = arc.request(
        "POST",
        "/api/v1/continuous_queries/%s/execute" % query_id,
        {"start_time": "2023-11-14T22:00:00Z", "end_time": "2023-11-14T23:00:00Z"},
        token=arc.admin_token(),
    )
    executed_payload = _payload(executed)
    assert executed.status == 200, executed
    assert executed_payload.get("records_written", 0) >= 1, executed

    deadline = time.time() + 30
    last = None
    while time.time() < deadline:
        last = _payload(arc.query("SELECT * FROM fdb.m_hourly"))
        if last.get("success") and last.get("row_count", 0) >= 1:
            return
        time.sleep(0.5)
    pytest.fail("aggregate was never written to the destination: %r" % last)


def test_stored_report_returns_rows(arc):
    """A saved aggregate report still runs and returns its rows."""
    created = arc.request(
        "POST",
        "/api/v1/reports/",
        {
            "name": "avg_by_host",
            "database": "fdb",
            "measurement": "m",
            "query": (
                "SELECT host, avg(value) AS avg_value FROM fdb.m "
                "GROUP BY host ORDER BY host"
            ),
        },
        token=arc.admin_token(),
    )
    payload = _payload(created)
    report_id = payload.get("id")
    assert report_id, created

    run = arc.request(
        "POST",
        "/api/v1/reports/%s/run" % report_id,
        {},
        token=arc.admin_token(),
    )
    run_payload = _payload(run)
    assert run.status == 200 and run_payload.get("success") is True, run
    assert run_payload.get("row_count") == 2, run
    assert "host" in run_payload.get("columns", []), run


class _AlertReceiver(http.server.BaseHTTPRequestHandler):
    hits = []

    def do_POST(self):  # noqa: N802 (http.server API)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        _AlertReceiver.hits.append((self.path, body))
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        return


def test_alert_delivery_uses_configured_receiver():
    """A diagnostics delivery still reaches the configured receiver."""
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _AlertReceiver)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/configured" % httpd.server_address[1]
    _AlertReceiver.hits = []
    server = ArcServer(
        auth=True,
        extra_config={"lines": ["[alerts]", 'webhook_url = "%s"' % url]},
    )
    try:
        server.start()
        resp = server.request(
            "POST",
            "/api/v1/alerts/test",
            {"message": "arc-alert-legit"},
            token=server.admin_token(),
        )
        payload = _payload(resp)
        assert resp.status == 200 and payload.get("success") is True, resp
        assert payload.get("delivered") is True, resp
        assert _AlertReceiver.hits, "configured receiver was not contacted"
    finally:
        server.stop()
        httpd.shutdown()
        httpd.server_close()


def test_relative_storage_path_keeps_working():
    """The default configuration uses a relative storage path."""
    server = ArcServer(auth=True, relative_storage=True)
    try:
        server.start()
        server.ingest(
            "reldb",
            "relm",
            ["relm,host=a value=5 1700000000000000000"],
        )
        payload = _payload(server.query("SELECT * FROM reldb.relm"))
        assert payload.get("success") is True, payload
        assert payload.get("row_count") == 1, payload
    finally:
        server.stop()


def test_project_query_api_tests_pass():
    """The project's own tests for the query API still pass."""
    proc = subprocess.run(
        [
            "go",
            "test",
            "-tags=duckdb_arrow",
            "./internal/api/",
            "-run",
            "^(TestValidateSQLRequest.*|TestExtractCTENames|TestShowDatabasesPattern|"
            "TestShowTablesPattern|TestMaskStringLiterals|TestDBTablePattern)$",
            "-count=1",
        ],
        cwd=os.environ.get("PRODUCT_ROOT", "/workspace"),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, (proc.stdout[-4000:] + proc.stderr[-4000:])
