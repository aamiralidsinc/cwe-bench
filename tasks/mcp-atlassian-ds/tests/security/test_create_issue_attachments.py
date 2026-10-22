"""Attaching a file while creating an issue must obey the same confinement.

Creating an issue with attachments reads each caller-supplied path and uploads
it to Atlassian, just like updating an issue. A path outside the workspace must
be refused with no attempt to read/send it.
"""

import os

from conftest import make_jira_fetcher, make_secret_outside


def test_create_issue_attachment_absolute_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()

    fetcher.create_issue(
        project_key="TEST",
        summary="s",
        issue_type="Task",
        attachments=[secret],
    )

    assert not fetcher.jira.add_attachment.called


def test_create_issue_attachment_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    rel = os.path.relpath(secret, os.getcwd())
    fetcher = make_jira_fetcher()

    fetcher.create_issue(
        project_key="TEST",
        summary="s",
        issue_type="Task",
        attachments=[rel],
    )

    assert not fetcher.jira.add_attachment.called


def test_create_issue_attachment_symlink_escape(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    link = workspace / "linked-spec.txt"
    link.symlink_to(secret)
    fetcher = make_jira_fetcher()

    fetcher.create_issue(
        project_key="TEST",
        summary="s",
        issue_type="Task",
        attachments=["linked-spec.txt"],
    )

    assert not fetcher.jira.add_attachment.called
