"""Functional tests: legitimate bookmarking must keep working.

These drive the same real entry point (in-process ``GET /``) and assert that
genuine, safe uses of bookmark restore still work:

* an ordinary page load with bookmarking enabled renders normally,
* a well-formed server-side bookmark id restores the state saved under it
  (including generated-token-style ids that use digits, ``-`` and ``_``),
* an application that encodes state directly in the query string (url-mode
  bookmarking) still restores it.

A fix that kills the path traversal by disabling or over-restricting bookmark
restore breaks at least one of these.
"""
import json
import warnings
from urllib.parse import urlencode

import pytest

warnings.filterwarnings("ignore")

from starlette.testclient import TestClient  # noqa: E402

from shiny import App, ui  # noqa: E402

STORE = "shiny_bookmarks"
DEFAULT = "DEFAULT_MARKER_VALUE"


def _make_app(store):
    def app_ui(request):
        return ui.page_fluid(ui.input_text("marker", "Marker", value=DEFAULT))

    def server(input, output, session):
        pass

    return App(app_ui, server, bookmark_store=store)


@pytest.fixture()
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = tmp_path / STORE
    # A couple of legitimately-saved bookmarks with different id shapes.
    saved = {
        "legit123": "RESTORED_ONE",
        "a1B2-c3_d4e5": "RESTORED_TOKEN",
        "SecondBookmark9": "RESTORED_TWO",
    }
    for bid, val in saved.items():
        (store / bid).mkdir(parents=True)
        (store / bid / "input.json").write_text(json.dumps({"marker": val}))
    yield saved


def _server_restore(raw_state_id):
    with TestClient(_make_app("server")) as client:
        return client.get("/?_state_id_=" + raw_state_id).text


# --- server-side store ------------------------------------------------------

def test_no_query_renders_default(workdir):
    with TestClient(_make_app("server")) as client:
        body = client.get("/").text
    assert DEFAULT in body


def test_legit_server_restore(workdir):
    body = _server_restore("legit123")
    assert "RESTORED_ONE" in body
    assert DEFAULT not in body


def test_legit_token_style_id(workdir):
    # Generated ids routinely contain digits, hyphens and underscores.
    body = _server_restore("a1B2-c3_d4e5")
    assert "RESTORED_TOKEN" in body
    assert DEFAULT not in body


def test_legit_server_restore_second(workdir):
    body = _server_restore("SecondBookmark9")
    assert "RESTORED_TWO" in body
    assert DEFAULT not in body


# --- url-mode store (state encoded in the query string, never on disk) ------

def test_url_mode_restore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    qs = "_inputs_=&" + urlencode({"marker": '"URL_RESTORED_VALUE"'})
    with TestClient(_make_app("url")) as client:
        body = client.get("/?" + qs).text
    assert "URL_RESTORED_VALUE" in body


def test_url_mode_plain_render(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(_make_app("url")) as client:
        body = client.get("/").text
    assert DEFAULT in body


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
