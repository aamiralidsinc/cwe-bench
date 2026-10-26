"""Shared helpers for the hidden suites.

Expected values are computed here from what the test itself supplies; no product
helper is trusted for bookkeeping.
"""
import json
import socket
import threading
import uuid

from lemur.authorities.models import Authority

GOOD_DIRECTORY = "https://acme-v02.api.letsencrypt.org/directory"
ATTACK_HTTP = "http://169.254.169.254/latest/meta-data/"
ATTACK_HTTPS = "https://169.254.169.254/latest/meta-data/"
ATTACK_SCHEME = "http://acme-v02.api.letsencrypt.org/directory"


def stored_options(session, authority_id):
    """The options value as it is stored right now, or None if the row is gone."""
    session.expire_all()
    authority = session.query(Authority).get(authority_id)
    if authority is None:
        return None
    return authority.options


def make_authority(session, name, options, plugin="acme-http-issuer", owner="joe@example.com"):
    from lemur.tests.factories import AuthorityFactory

    authority = AuthorityFactory(
        name="%s-%s" % (name, uuid.uuid4().hex[:8]),
        owner=owner,
        plugin={"slug": plugin},
        options=json.dumps(options),
    )
    session.commit()
    return authority


class _Canary:
    """A loopback listener that records every accepted connection."""

    def __init__(self):
        self.hits = []
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(64)
        self._sock.settimeout(0.2)
        self.port = self._sock.getsockname()[1]
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.hits.append(1)
            try:
                conn.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            finally:
                try:
                    conn.close()
                except OSError:
                    pass

    @property
    def http_url(self):
        return "http://127.0.0.1:%d/directory" % self.port

    @property
    def https_url(self):
        return "https://127.0.0.1:%d/directory" % self.port

    def close(self):
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass
        self._thread.join(timeout=2)
