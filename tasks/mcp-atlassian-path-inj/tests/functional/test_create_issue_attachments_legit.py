"""Legitimate create-issue-with-attachments keeps working."""

from conftest import make_jira_fetcher


def test_create_issue_attachment_inside_workspace(workspace):
    (workspace / "spec.txt").write_text("spec", encoding="utf-8")
    fetcher = make_jira_fetcher()

    fetcher.create_issue(
        project_key="TEST",
        summary="s",
        issue_type="Task",
        attachments=["spec.txt"],
    )

    assert fetcher.jira.add_attachment.called


def test_create_issue_without_attachments_unaffected(workspace):
    fetcher = make_jira_fetcher()

    issue = fetcher.create_issue(project_key="TEST", summary="s", issue_type="Task")

    assert issue.key == "TEST-1"
    assert not fetcher.jira.add_attachment.called
