"""Jira attachment upload must not read a file outside the workspace.

The upload helper reads the file at the caller-supplied path and hands it to
Atlassian. A path that resolves outside the working directory must be refused
with no attempt to read/send it (``add_attachment`` never reaches the client).
"""

import os

from conftest import (
    make_jira_attachments_mixin,
    make_jira_fetcher,
    make_secret_outside,
)


def test_upload_attachment_absolute_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachment("TEST-1", secret)

    assert not mixin.jira.add_attachment.called
    assert result.get("success") is not True


def test_upload_attachment_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    rel = os.path.relpath(secret, os.getcwd())  # e.g. ../outside/secret.txt
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachment("TEST-1", rel)

    assert not mixin.jira.add_attachment.called
    assert result.get("success") is not True


def test_upload_attachments_list_contains_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachments("TEST-1", [secret])

    assert not mixin.jira.add_attachment.called
    # No file was successfully uploaded.
    assert not result.get("uploaded")


def test_upload_attachment_symlink_escape(workspace, tmp_path):
    # A symlink that lives inside the workspace but points at a file outside it
    # must not become a read of the outside file.
    secret, _ = make_secret_outside(tmp_path)
    link = workspace / "inside-link.txt"
    link.symlink_to(secret)
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachment("TEST-1", "inside-link.txt")

    assert not mixin.jira.add_attachment.called
    assert result.get("success") is not True


def test_update_issue_attachments_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()

    fetcher.update_issue("TEST-1", attachments=[secret])

    assert not fetcher.jira.add_attachment.called
