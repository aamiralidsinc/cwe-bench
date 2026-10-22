"""An issue description read from a file must stay inside the workspace.

create_issue accepts a filesystem path to read the description from; the
description is sent to Atlassian as the new issue's body. A path outside the
workspace must be refused and the file content must never reach the fetcher.
"""

import pytest

from conftest import call_tool, make_jira_fetcher_mock, make_secret_outside

pytestmark = pytest.mark.anyio


async def test_create_issue_description_file_outside(workspace, tmp_path):
    secret, marker = make_secret_outside(tmp_path)
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
            "description_file": secret,
        },
        fetcher,
    )

    assert err is not None
    assert not fetcher.create_issue.called
