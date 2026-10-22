"""Alert delivery must not let a request choose the address Arc contacts.

The alert receiver is operator configuration. A diagnostics request may ask
for a delivery, but a caller-supplied receiver address must never be
contacted: the server must refuse the attempt instead.
"""

import http.server
import threading

import pytest

from arc_harness import ArcServer, is_refused

MARKER = "arc-alert-marker-8d51e0"
ATTACK_PATH = "/caller-supplied"
CONFIGURED_PATH = "/configured"


class _Receiver(http.server.BaseHTTPRequestHandler):
    hits = []

    def do_POST(self):  # noqa: N802 (http.server API)
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        _Receiver.hits.append(self.path)
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        return


@pytest.fixture(scope="module")
def receiver():
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Receiver)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


@pytest.fixture(scope="module")
def arc(receiver):
    server = ArcServer(
        auth=True,
        extra_config={
            "lines": [
                "[alerts]",
                'webhook_url = "%s%s"' % (receiver, CONFIGURED_PATH),
            ]
        },
    ).start()
    yield server
    server.stop()


def test_caller_supplied_receiver_not_contacted(arc, receiver):
    _Receiver.hits = []
    resp = arc.request(
        "POST",
        "/api/v1/alerts/test",
        {
            "webhook_url": receiver + ATTACK_PATH,
            "message": MARKER,
        },
        token=arc.admin_token(),
    )
    assert is_refused(resp, MARKER), resp
    assert ATTACK_PATH not in _Receiver.hits, (
        "server contacted a caller-supplied address: %r" % _Receiver.hits
    )
