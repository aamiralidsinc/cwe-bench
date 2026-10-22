"""A body resolved from a named template must stay inside the workspace.

Issue creation accepts a template name that the server turns into a path by
joining it onto a fixed template directory inside the workspace, then reads.
A name that makes the resulting path escape the workspace must be refused and
the file content must never reach the fetcher.
"""

import os

import pytest

from conftest import call_tool, make_jira_fetcher_mock, make_secret_outside

pytestmark = pytest.mark.anyio


async def test_create_issue_template_absolute_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
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
            "template": secret,
        },
        fetcher,
    )

    assert err is not None or not fetcher.create_issue.called
    assert not fetcher.create_issue.called


async def test_create_issue_template_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    # The value is a template *name*: the server joins it onto a directory
    # inside the workspace before reading, so the traversal is relative to
    # that directory (which exists in normal use).
    (workspace / "templates").mkdir()
    template_dir = os.path.join(os.getcwd(), "templates")
    rel = os.path.relpath(secret, template_dir)
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
            "template": rel,
        },
        fetcher,
    )

    assert not fetcher.create_issue.called
