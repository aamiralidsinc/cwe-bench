"""Recording HTTP servers and a URLFetch stand-in used by the hidden suites.

Nothing here imports the product under test: every test observes what an HTTP server (or
the platform's fetch service) actually received, so the expected values are computed here
and never by calling the code being graded.
"""

from __future__ import absolute_import

import email.message
import sys
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urljoin, urlsplit


class RecordingServer(object):
    """A local HTTP server that records every request it receives.

    ``routes`` maps a request target to ``(status, headers, body)``. The raw request target
    is tried first (an absolute URI when the server acts as a forward proxy) and the path
    second (ordinary origin-form requests).
    """

    def __init__(self):
        self.requests = []
        self.routes = {}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self):
                target = self.path
                headers = {}
                for name, value in self.headers.items():
                    headers[name.lower()] = value
                outer.requests.append({
                    "method": self.command,
                    "target": target,
                    "headers": headers,
                })
                route = outer.routes.get(target)
                if route is None:
                    route = outer.routes.get(urlsplit(target).path)
                if route is None:
                    route = (404, {}, b"not routed")
                status, extra, body = route
                if isinstance(body, str):
                    body = body.encode("utf-8")
                self.send_response(status)
                for name, value in extra.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()

    # -- routing ---------------------------------------------------------------------
    def route(self, target, status=200, location=None, body=b"", headers=None):
        extra = dict(headers or {})
        if location is not None:
            extra["Location"] = location
        self.routes[target] = (status, extra, body)

    def redirect(self, target, location, status=302):
        self.route(target, status=status, location=location)

    def ok(self, target, body=b"ok"):
        self.route(target, status=200, body=body)

    # -- observation -----------------------------------------------------------------
    def requests_to(self, target):
        return [r for r in self.requests if r["target"] == target]

    def headers_to(self, target):
        """Headers of the last request received for *target* (None when it was never made)."""
        hits = self.requests_to(target)
        return hits[-1]["headers"] if hits else None

    def received(self, target, header):
        headers = self.headers_to(target)
        if headers is None:
            return None
        return headers.get(header.lower())

    # -- lifecycle -------------------------------------------------------------------
    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class UrlFetchStub(object):
    """Stand-in for ``google.appengine.api.urlfetch``.

    ``fetch`` behaves like the platform service: with ``follow_redirects`` true it follows
    the chain itself and carries the request headers to every hop; with it false it returns
    the redirect response so the caller can follow it. Every hop is recorded in ``calls``.
    """

    def __init__(self):
        self.calls = []
        self.routes = {}

    def route(self, url, status=200, location=None, body=b"", headers=None):
        extra = dict(headers or {})
        if location is not None:
            extra["Location"] = location
        self.routes[url] = (status, extra, body if isinstance(body, bytes) else body.encode())

    def fetch(self, url, payload=None, method="GET", headers=None, allow_truncated=False,
              follow_redirects=True, deadline=None, validate_certificate=None):
        self.calls.append({
            "url": url,
            "method": method,
            "headers": dict(headers or {}),
            "follow_redirects": follow_redirects,
        })
        route = self.routes.get(url)
        if route is None:
            route = self.routes.get(urlsplit(url).path)
        if route is None:
            route = (404, {}, b"not routed")
        status, extra, body = route
        if follow_redirects and status in (301, 302, 303, 307, 308) and "Location" in extra:
            return self.fetch(urljoin(url, extra["Location"]), payload=payload, method=method,
                              headers=headers, allow_truncated=allow_truncated,
                              follow_redirects=True, deadline=deadline,
                              validate_certificate=validate_certificate)
        return _UrlFetchResponse(status, extra, body)

    def headers_for(self, url):
        for call in reversed(self.calls):
            if call["url"] == url:
                return call["headers"]
        return None

    def received(self, url, header):
        headers = self.headers_for(url)
        if headers is None:
            return None
        for name, value in headers.items():
            if name.lower() == header.lower():
                return value
        return None


class _UrlFetchResponse(object):
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = dict(headers)
        self.content = content if isinstance(content, bytes) else content.encode()
        message = email.message.Message()
        for name, value in self.headers.items():
            message[name] = value
        self.header_msg = message


def install_urlfetch_stub():
    """Register a fake ``google.appengine.api.urlfetch`` before the contrib module imports it.

    Idempotent: suites that import the contrib module share one stub, so calls made by one
    test module are visible to another.
    """
    existing = sys.modules.get("google.appengine.api.urlfetch")
    installed = getattr(existing, "_urllib3_stub", None)
    if installed is not None:
        return installed
    stub = UrlFetchStub()
    module = types.ModuleType("google.appengine.api.urlfetch")
    module.fetch = stub.fetch
    module._urllib3_stub = stub
    for name in ("DeadlineExceededError", "InvalidURLError", "DownloadError",
                 "ResponseTooLargeError", "SSLCertificateError", "InvalidMethodError"):
        setattr(module, name, type(name, (Exception,), {}))
    google = sys.modules.get("google") or types.ModuleType("google")
    google.__path__ = []
    appengine = types.ModuleType("google.appengine")
    appengine.__path__ = []
    api = types.ModuleType("google.appengine.api")
    api.__path__ = []
    api.urlfetch = module
    sys.modules["google"] = google
    sys.modules["google.appengine"] = appengine
    sys.modules["google.appengine.api"] = api
    sys.modules["google.appengine.api.urlfetch"] = module
    return stub
