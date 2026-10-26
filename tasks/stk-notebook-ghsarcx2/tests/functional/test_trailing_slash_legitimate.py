"""Ordinary directory redirects keep working, with their query string."""

from support.nbtest import NotebookServer, raw_get
from support.redirects import points_off_origin


class DirectoryRedirects(NotebookServer):
    port = 12412
    url_prefix = "/"

    def test_directory_url_still_redirects(self):
        status, location = raw_get(self, "/some/dir/")
        assert 300 <= status < 400, status
        assert location is not None
        assert location.split("?")[0] in ("/some/dir", "/some/dir/")
        assert not points_off_origin(location, self.port)

    def test_query_string_is_preserved(self):
        status, location = raw_get(self, "/some/dir/?page=2")
        assert 300 <= status < 400, status
        assert location is not None
        assert location.startswith("/some/dir")
        assert "page=2" in location
        assert not points_off_origin(location, self.port)
