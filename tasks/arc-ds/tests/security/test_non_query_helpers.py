"""Two non-query helpers also touch the filesystem with caller input.

A preview helper runs ad-hoc SQL for the query builder, and the export
download helper serves a named file from the export area. Neither may reach a
file outside Arc's own directories.
"""

import urllib.parse

import pytest

from arc_harness import ArcServer, is_refused

MARKER = "arc-side-marker-1a77e3"


@pytest.fixture(scope="module")
def arc():
    server = ArcServer(auth=True).start()
    yield server
    server.stop()


def _lit(path):
    return "'" + path.replace("'", "''") + "'"


def test_preview_cannot_read_outside_file(arc):
    path = arc.write_secret("arc-side-marker-1a77e3.txt", MARKER + "\n")
    resp = arc.request(
        "POST",
        "/api/v1/query/preview",
        {"sql": "SELECT * FROM read_text(%s)" % _lit(path)},
        token=arc.no_permission_token(),
    )
    assert is_refused(resp, MARKER), resp


def test_export_download_cannot_escape_export_area(arc):
    secret_name = "arc-side-marker-1a77e3.txt"
    arc.write_secret(secret_name, MARKER + "\n")
    resp = arc.request(
        "GET",
        "/api/v1/export/download?path=" + urllib.parse.quote("../../" + secret_name),
        token=arc.no_permission_token(),
    )
    assert is_refused(resp, MARKER), resp
