"""Legitimate comment bodies read from a file inside the workspace work."""

import pytest

from conftest import call_tool, make_confluence_fetcher_mock

pytestmark = pytest.mark.anyio


async def test_add_comment_body_file_inside_workspace(workspace):
    body = "This comment body came from a file."
    (workspace / "comment.md").write_text(body, encoding="utf-8")
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import add_comment

    err = await call_tool(
        "confluence",
        add_comment,
        "confluence_add_comment",
        {"page_id": "123", "body_file": "comment.md"},
        fetcher,
    )

    assert err is None
    assert fetcher.add_comment.called
    assert fetcher.add_comment.call_args.kwargs["content"] == body


async def test_add_comment_inline_body_unaffected(workspace):
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import add_comment

    err = await call_tool(
        "confluence",
        add_comment,
        "confluence_add_comment",
        {"page_id": "123", "body": "inline comment"},
        fetcher,
    )

    assert err is None
    assert fetcher.add_comment.call_args.kwargs["content"] == "inline comment"
