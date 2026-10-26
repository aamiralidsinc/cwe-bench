"""The server's configured landing address must not send the browser to another host."""

from traitlets.config import Config

from support.nbtest import NotebookServer, raw_get
from support.redirects import assert_raw_refused_or_in_server


class AuthorityShapedLanding(NotebookServer):
    port = 12405
    url_prefix = "/"
    config = Config()
    config.NotebookApp.default_url = "//redirect.invalid/start"

    def test_landing_address_does_not_leave_the_server(self):
        status, location = raw_get(self, "/")
        assert_raw_refused_or_in_server(status, location, self.port)


class BackslashShapedLanding(NotebookServer):
    port = 12406
    url_prefix = "/"
    config = Config()
    config.NotebookApp.default_url = "/\\redirect.invalid/start"

    def test_landing_address_does_not_leave_the_server(self):
        status, location = raw_get(self, "/")
        assert_raw_refused_or_in_server(status, location, self.port)
