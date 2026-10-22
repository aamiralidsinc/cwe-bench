"""A comment body read from a file must stay inside the workspace.

add_comment accepts a filesystem path to read the comment body from; the body
is sent to Atlassian as the comment content. A path outside the workspace must
be refused and the file content must never reach the fetcher.
"""

import os

import pytest

from conftest import call_tool, make_confluence_fetcher_mock, make_secret_outside

pytestmark = pytest.mark.anyio


async def test_add_comment_body_file_outside(workspace, tmp_path):
    secret, marker = make_secret_outside(tmp_path)
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import add_comment

    err = await call_tool(
        "confluence",
        add_comment,
        "confluence_add_comment",
        {"page_id": "123", "body_file": secret},
        fetcher,
    )

    assert err is not None or not fetcher.add_comment.called
    assert not fetcher.add_comment.called


async def test_add_comment_body_file_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    rel = os.path.relpath(secret, os.getcwd())
    fetcher = make_confluence_fetcher_mock()
    from mcp_atlassian.servers.confluence import add_comment

    err = await call_tool(
        "confluence",
        add_comment,
        "confluence_add_comment",
        {"page_id": "123", "body_file": rel},
        fetcher,
    )

    assert not fetcher.add_comment.called
