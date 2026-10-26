"""Legitimate login destinations keep working."""

from traitlets.config import Config

from support.nbtest import NotebookServer, login


class LoginDestinations(NotebookServer):
    port = 12411
    url_prefix = "/"
    config = Config()
    config.NotebookApp.allow_origin = "https://allowed.invalid"

    def test_configured_cross_origin_destination_is_honoured(self):
        response = login(self, "https://allowed.invalid/landing")
        assert 300 <= response.status_code < 400, response.status_code
        assert response.headers.get("Location") == "https://allowed.invalid/landing"

    def test_internal_doubled_slashes_are_preserved(self):
        response = login(self, "/tree//something")
        assert 300 <= response.status_code < 400, response.status_code
        assert response.headers.get("Location") == "/tree//something"

    def test_ordinary_in_server_path_is_used(self):
        response = login(self, "/tree/notebook.ipynb")
        assert 300 <= response.status_code < 400, response.status_code
        assert response.headers.get("Location") == "/tree/notebook.ipynb"
