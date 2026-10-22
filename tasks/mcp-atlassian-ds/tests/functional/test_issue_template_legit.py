"""A template that lives inside the workspace must keep working."""

import pytest

from conftest import call_tool, make_jira_fetcher_mock

pytestmark = pytest.mark.anyio


async def test_create_issue_template_inside_workspace(workspace):
    templates = workspace / "templates"
    templates.mkdir()
    body = "Steps to reproduce:\n1. open the page\n"
    (templates / "bug_report.md").write_text(body, encoding="utf-8")
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
            "template": "bug_report.md",
        },
        fetcher,
    )

    assert err is None
    assert fetcher.create_issue.called
    assert fetcher.create_issue.call_args.kwargs["description"] == body
