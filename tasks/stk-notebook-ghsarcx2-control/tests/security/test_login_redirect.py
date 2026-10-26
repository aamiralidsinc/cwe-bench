"""A login destination that a browser resolves to another host must not be honoured."""

from support.nbtest import NotebookServer, login
from support.redirects import assert_refused_or_in_server


class ExtraLeadingSlashes(NotebookServer):
    port = 12401
    url_prefix = "/"

    def test_extra_leading_slashes_do_not_leave_the_server(self):
        response = login(self, "///redirect.invalid/landing")
        assert_refused_or_in_server(response, self.port)


class BackslashDestination(NotebookServer):
    port = 12402
    url_prefix = "/"

    def test_backslash_destination_does_not_leave_the_server(self):
        response = login(self, "/\\redirect.invalid/landing")
        assert_refused_or_in_server(response, self.port)
