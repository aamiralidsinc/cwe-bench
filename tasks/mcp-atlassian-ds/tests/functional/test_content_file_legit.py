"""Legitimate page bodies read from a file inside the workspace keep working.

Also checks that inline content (no file) is unaffected.
"""

import pytest

from conftest import call_tool, make_confluence_fetcher_mock

pytestmark = pytest.mark.anyio


async def test_create_page_content_file_inside_workspace(workspace):
    body = "# Hello\n\nThis page body came from a file."
    (workspace / "body.md").write_text(body, encoding="utf-8")
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {"space_key": "DEV", "title": "t", "content_file": "body.md"},
        fetcher,
    )

    assert err is None
    assert fetcher.create_page.called
    assert fetcher.create_page.call_args.kwargs["body"] == body


async def test_create_page_content_file_absolute_inside_workspace(workspace):
    body = "absolute path inside the workspace"
    p = workspace / "pages" / "body.md"
    p.parent.mkdir()
    p.write_text(body, encoding="utf-8")
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {"space_key": "DEV", "title": "t", "content_file": str(p)},
        fetcher,
    )

    assert err is None
    assert fetcher.create_page.call_args.kwargs["body"] == body


async def test_create_page_inline_content_unaffected(workspace):
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import create_page

    err = await call_tool(
        "confluence",
        create_page,
        "confluence_create_page",
        {"space_key": "DEV", "title": "t", "content": "inline body"},
        fetcher,
    )

    assert err is None
    assert fetcher.create_page.call_args.kwargs["body"] == "inline body"
