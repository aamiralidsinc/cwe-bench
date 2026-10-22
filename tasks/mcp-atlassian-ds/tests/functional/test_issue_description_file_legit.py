"""Legitimate issue descriptions read from a file inside the workspace work."""

import pytest

from conftest import call_tool, make_jira_fetcher_mock

pytestmark = pytest.mark.anyio


async def test_create_issue_description_file_inside_workspace(workspace):
    body = "Steps to reproduce:\n1. do a thing\n2. observe"
    (workspace / "desc.md").write_text(body, encoding="utf-8")
    fetcher = make_jira_fetcher_mock()
    from mcp_atlassian.servers.jira import create_issue

    err = await call_tool(
        "jira",
        create_issue,
        "jira_create_issue",
        {
            "project_key": "TEST",
            "summary": "s",
            "issue_type": "Task",
            "description_file": "desc.md",
        },
        fetcher,
    )

    assert err is None
    assert fetcher.create_issue.called
    assert fetcher.create_issue.call_args.kwargs["description"] == body


async def test_create_issue_inline_description_unaffected(workspace):
    fetcher = make_jira_fetcher_mock()
    from mcp_atlassian.servers.jira import create_issue

    err = await call_tool(
        "jira",
        create_issue,
        "jira_create_issue",
        {
            "project_key": "TEST",
            "summary": "s",
            "issue_type": "Task",
            "description": "inline description",
        },
        fetcher,
    )

    assert err is None
    assert fetcher.create_issue.call_args.kwargs["description"] == "inline description"
