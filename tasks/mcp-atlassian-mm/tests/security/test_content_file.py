"""A page body read from a file must stay inside the workspace.

create_page / update_page accept a filesystem path to read the page body from.
The body is echoed back through the created/updated page, so an unconfined path
is an arbitrary-file-read primitive. A path outside the workspace must be
refused and the file content must never reach the fetcher.

Shapes: absolute outside, relative traversal, and a path the platform expands
on the caller's behalf (home directory) before it is used.
"""

import os

import pytest

from conftest import call_tool, make_confluence_fetcher_mock, make_secret_outside

pytestmark = pytest.mark.anyio


async def test_create_page_content_file_outside(workspace, tmp_path):
    secret, marker = make_secret_outside(tmp_path)
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {"space_key": "DEV", "title": "t", "content_file": secret},
        fetcher,
    )

    assert err is not None or not fetcher.create_page.called
    assert not fetcher.create_page.called


async def test_update_page_content_file_outside(workspace, tmp_path):
    secret, marker = make_secret_outside(tmp_path)
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import update_page

    err = await call_tool(
        "confluence",
        update_page,
        "confluence_update_page",
        {"page_id": "123", "title": "t", "content_file": secret},
        fetcher,
    )

    assert err is not None or not fetcher.update_page.called
    assert not fetcher.update_page.called


async def test_create_page_content_file_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    rel = os.path.relpath(secret, os.getcwd())
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {"space_key": "DEV", "title": "t", "content_file": rel},
        fetcher,
    )

    assert not fetcher.create_page.called


async def test_create_page_content_file_home_expansion(workspace, tmp_path, monkeypatch):
    """A path the platform expands before use must not become a read of an
    out-of-workspace file."""
    secret, _ = make_secret_outside(tmp_path)
    monkeypatch.setenv("HOME", os.path.dirname(secret))
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {
            "space_key": "DEV",
            "title": "t",
            "content_file": os.path.join("~", os.path.basename(secret)),
        },
        fetcher,
    )

    assert not fetcher.create_page.called
