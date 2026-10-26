"""A directory-style request target must not become a redirect to another host."""

from support.nbtest import NotebookServer, raw_get
from support.redirects import assert_raw_refused_or_in_server


class AuthorityShapedTarget(NotebookServer):
    port = 12403
    url_prefix = "/"

    def test_authority_shaped_target_is_not_redirected_off_the_server(self):
        status, location = raw_get(self, "//redirect.invalid/some/dir/")
        assert_raw_refused_or_in_server(status, location, self.port)


class BackslashShapedTarget(NotebookServer):
    port = 12404
    url_prefix = "/"

    def test_backslash_shaped_target_is_not_redirected_off_the_server(self):
        status, location = raw_get(self, "/\\redirect.invalid/some/dir/")
        assert_raw_refused_or_in_server(status, location, self.port)
