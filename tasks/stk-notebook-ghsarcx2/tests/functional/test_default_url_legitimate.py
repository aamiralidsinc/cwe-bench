"""Ordinary landing addresses keep working."""

import re
from urllib.parse import urlparse

from traitlets.config import Config

from support.nbtest import NotebookServer, raw_get
from support.redirects import points_off_origin


class RootLanding(NotebookServer):
    port = 12413
    url_prefix = "/"
    config = Config()
    config.NotebookApp.default_url = "/tree"

    def test_root_redirects_to_the_landing_path(self):
        status, location = raw_get(self, "/")
        assert 300 <= status < 400, status
        assert location is not None
        assert urlparse(location).path == "/tree"
        assert not points_off_origin(location, self.port)


class PrefixedLanding(NotebookServer):
    port = 12414
    url_prefix = "/a%40b/"
    config = Config()
    config.NotebookApp.default_url = "tree"

    def test_landing_path_is_rebased_below_the_server_prefix(self):
        status, location = raw_get(self, "/a%40b/")
        assert 300 <= status < 400, status
        assert location is not None
        assert urlparse(location).path == "/a%40b/tree"

    def test_open_page_names_the_same_landing_path(self):
        text = open(self.notebook.browser_open_file, encoding="utf-8").read()
        match = re.search(r'content="1;url=([^"]+)"', text)
        assert match, "the page written for the user has no landing URL"
        assert urlparse(match.group(1)).path == "/a%40b/tree"
