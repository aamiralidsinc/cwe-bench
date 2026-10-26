"""Shared harness for the hidden suites.

It starts one product core (pyload.Core) per test process, a few local HTTP
servers that record what reaches them, and a forward proxy that can serve fixed
responses or forward to a local target.  Every case is driven through the
product's own entry points: the public API call that adds a link, the plugin
lifecycle the download thread runs, and the API call that fetches a page to
extract links from it.
"""
import http.client
import http.server
import os
import shutil
import socket
import socketserver
import tempfile
import threading
import urllib.parse

#: bytes that only the simulated private services ever serve
PAYLOAD = b"CANARY-PAYLOAD-7f3a91"
#: link that only the simulated private services ever contain
SECRET_LINK = "http://internal.invalid/secret"
#: ordinary link a legitimate page contains
GOOD_LINK = "http://example.com/good"

#: addresses in the globally routable space, used without any name resolution
PUBLIC_IP = "93.184.216.34"
PUBLIC_IP2 = "8.8.8.8"
PUBLIC_V6 = "2606:2800:220:1:248:1893:25c8:1946"
#: names added to the hosts file of the verifier container
PRIVATE_V6_NAME = "ipv6only.pyload.test"
PUBLIC_V6_NAME = "cdn6.pyload.test"


class _Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Target:
    """A local service that records every request and serves fixed bytes."""

    def __init__(self, body=PAYLOAD, content_type="application/octet-stream", host="127.0.0.1"):
        self.hits = []
        self.body = body
        self.content_type = content_type
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                outer.hits.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", outer.content_type)
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()
                self.wfile.write(outer.body)

            def do_HEAD(self):
                outer.hits.append(self.path)
                self.send_response(200)
                self.send_header("Content-Type", outer.content_type)
                self.send_header("Content-Length", str(len(outer.body)))
                self.end_headers()

            def log_message(self, *args):
                pass

        server = _Server
        if ":" in host:
            class server(_Server):
                address_family = socket.AF_INET6

        self.srv = server((host, 0), Handler)
        self.host = host
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class Proxy:
    """A forward proxy that records the absolute URI of every request.

    ``routes`` maps (host, path) to a fixed response; ``forward`` maps
    (host, path) to a local Target that is fetched and returned.  A private
    destination therefore only shows up here (and at the target) when the
    product actually sends the request on.
    """

    def __init__(self):
        self.hits = []
        self.routes = {}
        self.forward = {}
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def do_GET(self):
                outer.hits.append(self.path)
                if not self.path.lower().startswith("http"):
                    self.send_response(400)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                url = urllib.parse.urlsplit(self.path)
                key = (url.hostname, url.path)
                if key in outer.routes:
                    route = outer.routes[key]
                    self.send_response(route.get("status", 200))
                    for name, value in route.get("headers", {}).items():
                        self.send_header(name, value)
                    body = route.get("body", b"")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                target = outer.forward.get(key)
                if target is not None:
                    conn = http.client.HTTPConnection("127.0.0.1", target.port, timeout=10)
                    conn.request("GET", url.path or "/", headers={"Host": url.netloc})
                    response = conn.getresponse()
                    body = response.read()
                    self.send_response(response.status)
                    for name, value in response.getheaders():
                        if name.lower() not in ("transfer-encoding", "connection", "content-length"):
                            self.send_header(name, value)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    conn.close()
                    return
                self.send_response(502)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        self.srv = _Server(("127.0.0.1", 0), Handler)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def hosts(self):
        """Hostnames of the destinations this proxy was asked for."""
        return [urllib.parse.urlsplit(hit).hostname for hit in self.hits]

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


class Env:
    """One product core plus helpers that drive its fetch paths."""

    def __init__(self, src):
        self.src = os.path.abspath(src)
        self._cwd = os.getcwd()
        #: the product sets the process-wide temporary directory when it is
        #: built; do not inherit one from a previous environment
        tempfile.tempdir = None
        self.base = tempfile.mkdtemp(prefix="pyload-env-")
        self.storage = os.path.join(self.base, "downloads")
        os.makedirs(self.storage, exist_ok=True)

        import sys

        if self.src not in sys.path:
            sys.path.insert(0, self.src)

        from pyload.core import Core
        from pyload.core.network import request_factory

        #: the product keeps one process-wide default request factory; point it
        #: at this environment so a second environment in the same process does
        #: not reuse a closed one
        request_factory.DEFAULT_REQUEST = None

        self.core = Core(
            os.path.join(self.base, "user"),
            os.path.join(self.base, "tmp"),
            self.storage,
            debug=0,
        )
        #: keep one connection per download so a redirect is seen on the first
        #: response instead of after the product has split the transfer
        self.core.config.set("download", "chunks", 1)

    # -- product configuration -------------------------------------------------
    def set_proxy(self, proxy):
        config = self.core.config
        if proxy is None:
            config.set("proxy", "enabled", False)
        else:
            config.set("proxy", "enabled", True)
            config.set("proxy", "type", "http")
            config.set("proxy", "host", "127.0.0.1")
            config.set("proxy", "port", proxy.port)

    def set_ipv6(self, enabled):
        self.core.config.set("download", "ipv6", bool(enabled))

    # -- product entry points --------------------------------------------------
    def download(self, url, name="package"):
        """Add the link through the public API and run the plugin the way the
        download thread does."""
        package_id = self.core.api.add_package(name, [url])
        package = self.core.api.get_package_data(package_id)
        file_id = package.links[0].fid
        pyfile = self.core.files.get_file(file_id)
        pyfile.init_plugin()
        plugin = pyfile.plugin
        plugin._initialize()
        plugin._setup()
        plugin.process(pyfile)

    def try_download(self, url, name="package"):
        try:
            self.download(url, name)
            return None
        except Exception as exc:  # a refusal may be reported as an error
            return exc

    def parse(self, url):
        return self.core.api.parse_urls(url=url)

    def try_parse(self, url):
        try:
            return self.parse(url), None
        except Exception as exc:
            return None, exc

    def parse_html(self, html):
        return self.core.api.parse_urls(html=html)

    def process_local_container(self, path):
        self.core.plugin_manager.parse_urls([path])  # the product's own routing
        package_id = self.core.api.add_package("container", [path])
        package = self.core.api.get_package_data(package_id)
        file_id = package.links[0].fid
        pyfile = self.core.files.get_file(file_id)
        pyfile.init_plugin()
        plugin = pyfile.plugin
        plugin._initialize()
        plugin._setup()
        plugin.process(pyfile)
        return plugin.packages

    # -- observations ----------------------------------------------------------
    def reset_downloads(self):
        shutil.rmtree(self.storage, ignore_errors=True)
        os.makedirs(self.storage, exist_ok=True)

    def payload_downloaded(self):
        for root, _dirs, files in os.walk(self.storage):
            for name in files:
                try:
                    with open(os.path.join(root, name), "rb") as handle:
                        if PAYLOAD in handle.read():
                            return True
                except OSError:
                    pass
        return False

    def close(self):
        try:
            self.core.terminate()
        except Exception:
            pass
        try:
            os.chdir(self._cwd)
        except OSError:
            pass
        tempfile.tempdir = None
        shutil.rmtree(self.base, ignore_errors=True)


def links_of(result):
    """Flatten the mapping returned by the product's link extraction."""
    out = []
    for values in (result or {}).values():
        out.extend(values)
    return out
