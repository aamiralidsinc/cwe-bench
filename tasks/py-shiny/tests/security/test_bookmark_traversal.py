"""Security tests: a client-supplied bookmark id must never read state from a
directory outside the bookmark store.

Each test drives the real entry point a browser uses: an in-process HTTP
``GET /`` against a small app configured with server-side bookmarking. The
app renders one text input whose value is populated from the restored bookmark
state, so whatever the server reads becomes visible in the returned HTML.

An attacker plants an ``input.json`` carrying a sentinel marker value in a
directory OUTSIDE the store, then asks the app to restore a bookmark id that
resolves to that directory (via ``..`` segments, percent-encoding, a nested
path, or an absolute path). On vulnerable code the sentinel is read and
appears in the HTML, so these assertions fail. A correct fix keeps every one
of them out: the id can only ever address a location inside the store, so the
sentinel is never read.
"""
import json
import os
import tempfile
import warnings
from pathlib import Path

import pytest

warnings.filterwarnings("ignore")

from starlette.testclient import TestClient  # noqa: E402

from shiny import App, ui  # noqa: E402

STORE = "shiny_bookmarks"
REL_SENTINEL = "PWNED_REL_SENTINEL"
ABS_SENTINEL = "PWNED_ABS_SENTINEL"
ABS_SENTINEL2 = "PWNED_ABS_SENTINEL2"
DEFAULT = "DEFAULT_MARKER_VALUE"


def _make_app():
    def app_ui(request):
        return ui.page_fluid(ui.input_text("marker", "Marker", value=DEFAULT))

    def server(input, output, session):
        pass

    return App(app_ui, server, bookmark_store="server")


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """A working dir with a bookmark store plus attacker-planted out-of-store
    directories, both relative (sibling of the store) and absolute."""
    monkeypatch.chdir(tmp_path)

    store = tmp_path / STORE
    (store / "legit123").mkdir(parents=True)
    (store / "legit123" / "input.json").write_text(json.dumps({"marker": "LEGIT"}))

    # Relative out-of-store target: shiny_bookmarks/../OUTSIDE == tmp_path/OUTSIDE
    outside = tmp_path / "OUTSIDE"
    outside.mkdir()
    (outside / "input.json").write_text(json.dumps({"marker": REL_SENTINEL}))

    # Absolute out-of-store targets, nowhere near the working directory.
    abs1 = Path(tempfile.mkdtemp(prefix="abs_evil_"))
    (abs1 / "input.json").write_text(json.dumps({"marker": ABS_SENTINEL}))
    abs2 = Path(tempfile.mkdtemp(prefix="abs_evil2_"))
    (abs2 / "input.json").write_text(json.dumps({"marker": ABS_SENTINEL2}))

    yield {"abs1": str(abs1), "abs2": str(abs2)}


def _restored_html(raw_state_id):
    """Issue GET /?_state_id_=<raw_state_id> and return the HTML body."""
    with TestClient(_make_app()) as client:
        return client.get("/?_state_id_=" + raw_state_id).text


def _assert_out_of_store_not_read(body, *sentinels):
    for s in sentinels:
        assert s not in body, f"out-of-store state was read (path traversal): {s!r} leaked into the page"


# --- relative-path family ---------------------------------------------------

def test_relative_dotdot(env):
    body = _restored_html("../OUTSIDE")
    _assert_out_of_store_not_read(body, REL_SENTINEL)


def test_percent_encoded_dotdot(env):
    # %2e%2e%2f decodes to "../" once the query string is parsed.
    body = _restored_html("%2e%2e%2fOUTSIDE")
    _assert_out_of_store_not_read(body, REL_SENTINEL)


def test_encoded_separator_only(env):
    body = _restored_html("..%2fOUTSIDE")
    _assert_out_of_store_not_read(body, REL_SENTINEL)


def test_nested_relative(env):
    # Climbs out from under a plausible-looking leading segment.
    body = _restored_html("legit123/../../OUTSIDE")
    _assert_out_of_store_not_read(body, REL_SENTINEL)


# --- absolute-path family (no ".." at all; defeats a dotdot-only block) ------

def test_absolute_path(env):
    body = _restored_html(env["abs1"])
    _assert_out_of_store_not_read(body, ABS_SENTINEL)


def test_absolute_path_second_location(env):
    body = _restored_html(env["abs2"])
    _assert_out_of_store_not_read(body, ABS_SENTINEL2)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
