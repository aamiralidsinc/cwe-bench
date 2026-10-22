"""The server must not become a filesystem/URL reader for its callers.

Every case sends a statement through a real server entry point and checks that
a value taken from a file (or a URL) outside Arc's storage never reaches the
client. The statements name only harmless test files created by the test
itself.
"""

import concurrent.futures
import http.server
import os
import shutil
import threading

import pytest

from arc_harness import ArcServer, is_refused, leaked

MARKER = "arc-io-marker-7f31c2"
OUTSIDE = "outside"


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    # A measurement whose parquet file is used as the "outside" file for the
    # parquet-shaped functions.
    server.ingest(
        "iosrc",
        "m",
        ["m,host=%s,kind=pq value=42 1700000000000000000" % MARKER],
    )
    yield server
    server.stop()


def _outside_dir(server):
    path = os.path.join(server.root, OUTSIDE)
    os.makedirs(path, exist_ok=True)
    return path


def _txt(server):
    path = os.path.join(_outside_dir(server), "arc-io-marker-7f31c2.txt")
    with open(path, "w") as fh:
        fh.write(MARKER + "\n")
    return path


def _csv(server):
    path = os.path.join(_outside_dir(server), "arc-io-marker-7f31c2.csv")
    with open(path, "w") as fh:
        fh.write("%s,1\n" % MARKER)
    return path


def _json(server):
    path = os.path.join(_outside_dir(server), "arc-io-marker-7f31c2.json")
    with open(path, "w") as fh:
        fh.write('{"k": "%s"}\n' % MARKER)
    return path


def _parquet(server):
    """Copy a measurement parquet file outside Arc's storage area."""
    source = None
    for root, _dirs, files in os.walk(server.storage_dir):
        for name in files:
            if name.endswith(".parquet"):
                source = os.path.join(root, name)
                break
        if source:
            break
    assert source, "fixture parquet file not found"
    dest = os.path.join(_outside_dir(server), "%s.parquet" % MARKER)
    shutil.copyfile(source, dest)
    return dest


def _lit(path):
    return "'" + path.replace("'", "''") + "'"


def _cases(server):
    txt = _txt(server)
    csv = _csv(server)
    js = _json(server)
    pq = _parquet(server)
    return [
        ("read_text", "SELECT * FROM read_text(%s)" % _lit(txt)),
        ("read_csv", "SELECT * FROM read_csv(%s, header=false)" % _lit(csv)),
        ("read_csv_auto", "SELECT * FROM read_csv_auto(%s, header=false)" % _lit(csv)),
        ("read_json", "SELECT * FROM read_json(%s)" % _lit(js)),
        ("read_json_auto", "SELECT * FROM read_json_auto(%s)" % _lit(js)),
        ("read_blob", "SELECT * FROM read_blob(%s)" % _lit(txt)),
        ("glob", "SELECT * FROM glob(%s)" % _lit(os.path.join(_outside_dir(server), "arc-io-marker-*"))),
        ("parquet_scan", "SELECT * FROM parquet_scan(%s)" % _lit(pq)),
        ("parquet_metadata", "SELECT * FROM parquet_metadata(%s)" % _lit(pq)),
        ("quoted_identifier", 'SELECT * FROM "read_text"(%s)' % _lit(txt)),
        ("uppercase_spacing", "SELECT * FROM READ_CSV_AUTO ( %s , header=false )" % _lit(csv)),
    ]


def test_io_function_family_refused(arc):
    token = arc.no_permission_token()
    for name, sql in _cases(arc):
        resp = arc.query(sql, token=token)
        assert is_refused(resp, MARKER), "%s was not refused: %r" % (name, resp)


def test_admin_token_cannot_read_outside_file(arc):
    """The restriction does not depend on the caller's token being limited."""
    path = _txt(arc)
    resp = arc.query("SELECT * FROM read_text(%s)" % _lit(path))
    assert is_refused(resp, MARKER), resp


class _LeakHandler(http.server.BaseHTTPRequestHandler):
    hits = []
    body = b""

    def do_GET(self):  # noqa: N802 (http.server API)
        _LeakHandler.hits.append(self.path)
        payload = _LeakHandler.body
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


def test_remote_url_refused(arc):
    """A caller-supplied URL must not make the server fetch it."""
    marker = "arc-ssrf-marker-5b81d0"
    _LeakHandler.hits = []
    _LeakHandler.body = ("%s,1\n" % marker).encode()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _LeakHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        url = "http://127.0.0.1:%d/leak.csv" % httpd.server_address[1]
        resp = arc.query(
            "SELECT * FROM read_csv_auto(%s, header=false)" % _lit(url),
            token=arc.no_permission_token(),
        )
        assert is_refused(resp, marker), resp
        assert _LeakHandler.hits == [], "server fetched a caller-supplied URL: %r" % _LeakHandler.hits
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_other_entry_points_refuse_outside_read(arc):
    """Every caller-SQL entry point is exposed to the same filesystem.

    Two further endpoints run a caller's statement on the same engine. A fix
    that only covers the one endpoint shown in the report leaves these open.
    """
    path = arc.write_secret("arc-io-marker-7f31c2.txt", MARKER + "\n")
    sql = "SELECT * FROM read_text(%s)" % _lit(path)
    token = arc.no_permission_token()
    for endpoint in ("/api/v1/query/arrow", "/api/v1/query/estimate"):
        resp = arc.request("POST", endpoint, {"sql": sql}, token=token)
        assert is_refused(resp, MARKER), "%s was not refused: %r" % (endpoint, resp)


def test_every_pooled_connection_refused(arc):
    """The restriction is process-wide, not attached to one pooled session."""
    path = _txt(arc)
    sql = "SELECT * FROM read_text(%s)" % _lit(path)
    token = arc.no_permission_token()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        responses = list(pool.map(lambda _: arc.query(sql, token=token), range(16)))
    bad = [r for r in responses if not is_refused(r, MARKER)]
    assert not bad, "some pooled connections served the file: %r" % bad[:3]
