"""Shared fixtures/helpers for the hidden behavioural tests.

Everything here is self-contained: no product code is used to compute expected
values or to clean up, so a hardened helper cannot crash the harness. The tests
drive the server's real public surfaces:

  * the fetcher upload API (``JiraFetcher`` / ``ConfluenceFetcher`` attachment
    helpers and ``JiraFetcher.create_issue``), which is where the file bytes are
    read and handed to Atlassian, and
  * the MCP tools (``create_page`` / ``update_page`` / ``add_comment`` /
    ``create_issue``) through an in-memory FastMCP client, exactly as the
    project's own server tests do.

The Atlassian client is always a ``MagicMock`` so no network is touched.
"""

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Client, FastMCP
from fastmcp.client import FastMCPTransport
from starlette.requests import Request

from mcp_atlassian.confluence import ConfluenceFetcher
from mcp_atlassian.confluence.config import ConfluenceConfig
from mcp_atlassian.jira import JiraFetcher
from mcp_atlassian.jira.config import JiraConfig
from mcp_atlassian.servers.context import MainAppContext
from mcp_atlassian.servers.main import AtlassianMCP


@pytest.fixture
def anyio_backend():
    """FastMCP's in-memory client requires the asyncio backend."""
    return "asyncio"


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A clean workspace that is the process working directory for the test.

    The server confines caller-supplied file paths to the working directory, so
    tests make this directory the workspace and place attacker targets outside
    it.
    """
    ws = tmp_path / "workspace"
    ws.mkdir()
    monkeypatch.chdir(ws)
    return ws


def make_secret_outside(tmp_path):
    """Create a marked file OUTSIDE the workspace; return (path, marker).

    The returned path is a sibling of the workspace (under the test's tmp_path),
    so it exists on disk and can be read, but lies outside the working
    directory.
    """
    marker = f"SECRET-{uuid.uuid4().hex}"
    secret_dir = tmp_path / "outside"
    secret_dir.mkdir(exist_ok=True)
    secret = secret_dir / "secret.txt"
    secret.write_text(marker, encoding="utf-8")
    return str(secret), marker


# --------------------------------------------------------------------------- #
# Fetcher-layer helpers (attachment upload sink: open() + send to Atlassian).  #
# --------------------------------------------------------------------------- #
def make_jira_attachments_mixin():
    """A Jira attachment helper whose Atlassian client is a mock.

    Built without network/config: only ``self.jira`` is exercised by the upload
    helpers.
    """
    from mcp_atlassian.jira.attachments import AttachmentsMixin

    mixin = object.__new__(AttachmentsMixin)
    mixin.jira = MagicMock()
    mixin.jira.add_attachment.return_value = {"id": "10001"}
    return mixin


def make_confluence_attachments_mixin():
    """A Confluence attachment helper whose REST send is mocked out."""
    from mcp_atlassian.confluence.attachments import AttachmentsMixin

    mixin = object.__new__(AttachmentsMixin)
    mixin._upload_attachment_direct = MagicMock(return_value={"id": "att1"})
    mixin._upload_attachment_from_bytes = MagicMock(return_value={"id": "att1"})
    return mixin


def make_jira_fetcher():
    """A real ``JiraFetcher`` with a mocked Atlassian client (no network)."""
    cfg = JiraConfig(
        url="https://example.atlassian.net",
        auth_type="basic",
        username="user@example.com",
        api_token="token",
    )
    with patch("atlassian.Jira"):
        fetcher = JiraFetcher(config=cfg)
    fetcher.jira = MagicMock()
    fetcher.jira.create_issue.return_value = {"key": "TEST-1"}
    fetcher.jira.get_issue.return_value = {
        "key": "TEST-1",
        "fields": {
            "summary": "s",
            "issuetype": {"name": "Task"},
            "status": {"name": "Open"},
        },
    }
    fetcher.jira.get_all_fields.return_value = []
    fetcher.jira.add_attachment.return_value = {"id": "10001"}
    fetcher.jira.update_issue.return_value = None
    return fetcher


# --------------------------------------------------------------------------- #
# Server-layer helper: drive a single MCP tool through an in-memory client.    #
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def _tool_client(product, tool, fetcher):
    if product == "jira":
        cfg = MagicMock(spec=JiraConfig)
        cfg.url = "https://example.atlassian.net"
        cfg.auth_type = "basic"
        cfg.is_cloud = True
        ctx_kwargs = {"full_jira_config": cfg, "read_only": False}
        fetcher_target = "mcp_atlassian.servers.jira.get_jira_fetcher"
        prefix = "jira"
    else:
        cfg = MagicMock(spec=ConfluenceConfig)
        cfg.url = "https://example.atlassian.net/wiki"
        cfg.auth_type = "basic"
        cfg.is_cloud = True
        ctx_kwargs = {"full_confluence_config": cfg, "read_only": False}
        fetcher_target = "mcp_atlassian.servers.confluence.get_confluence_fetcher"
        prefix = "confluence"

    @asynccontextmanager
    async def lifespan(app):
        yield MainAppContext(**ctx_kwargs)

    app = AtlassianMCP(f"Test-{product}", instructions="test", lifespan=lifespan)
    sub = FastMCP(name=f"sub-{product}")
    sub.add_tool(tool)
    app.mount(sub, prefix=prefix)

    with (
        patch(fetcher_target, AsyncMock(return_value=fetcher)),
        patch(
            "mcp_atlassian.servers.dependencies.get_http_request",
            MagicMock(spec=Request, state=MagicMock()),
        ),
    ):
        async with Client(transport=FastMCPTransport(app)) as client:
            yield client


async def call_tool(product, tool, tool_name, args, fetcher):
    """Invoke a tool; return (error, fetcher). ``error`` is None on success."""
    async with _tool_client(product, tool, fetcher) as client:
        try:
            result = await client.call_tool(tool_name, args)
            err = getattr(result, "is_error", False) or None
        except Exception as exc:  # a refusal surfaces as a client/tool error
            err = exc
    return err


def make_confluence_fetcher_mock():
    fetcher = MagicMock(spec=ConfluenceFetcher)
    page = MagicMock()
    page.to_simplified_dict.return_value = {"id": "123", "title": "t"}
    fetcher.create_page.return_value = page
    fetcher.update_page.return_value = page
    comment = MagicMock()
    comment.to_simplified_dict.return_value = {"id": "c1"}
    fetcher.add_comment.return_value = comment
    return fetcher


def make_jira_fetcher_mock():
    fetcher = MagicMock(spec=JiraFetcher)
    issue = MagicMock()
    issue.to_simplified_dict.return_value = {"key": "TEST-1"}
    fetcher.create_issue.return_value = issue
    return fetcher
