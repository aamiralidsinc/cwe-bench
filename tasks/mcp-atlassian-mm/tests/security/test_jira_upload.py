"""Jira attachment upload must not read a file outside the workspace.

The upload helper reads the file at the caller-supplied path and hands it to
Atlassian. A path that resolves outside the working directory must be refused
with no attempt to read/send it (``add_attachment`` never reaches the client).

Covers the shapes a one-case fix misses: absolute vs relative spelling, a
symlink that lives inside the workspace, one bad path among several, and the
same path list arriving through the issue-update call under either of its
spellings — or tucked inside the call's field payload rather than the named
argument.
"""

import json
import os

import pytest

from conftest import (
    call_tool,
    make_jira_attachments_mixin,
    make_jira_fetcher,
    make_secret_outside,
)

pytestmark = pytest.mark.anyio


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


async def test_update_issue_attachments_json_array_string_blocked(workspace, tmp_path):
    """The issue-update tool takes a path list as a JSON-array string."""
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()
    from mcp_atlassian.servers.jira import update_issue

    err = await call_tool(
        "jira",
        update_issue,
        "jira_update_issue",
        {
            "issue_key": "TEST-1",
            "fields": json.dumps({"summary": "s"}),
            "attachments": json.dumps([secret]),
        },
        fetcher,
    )

    # Either the call is refused, or the file is never sent onward.
    assert not fetcher.jira.add_attachment.called


async def test_update_issue_attachments_comma_separated_blocked(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()
    from mcp_atlassian.servers.jira import update_issue

    err = await call_tool(
        "jira",
        update_issue,
        "jira_update_issue",
        {
            "issue_key": "TEST-1",
            "fields": json.dumps({"summary": "s"}),
            "attachments": secret,
        },
        fetcher,
    )

    assert not fetcher.jira.add_attachment.called


async def test_update_issue_attachments_smuggled_in_fields_blocked(
    workspace, tmp_path
):
    """A path list tucked inside the call's field payload must not slip past a
    fix that only guards the named argument."""
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()
    from mcp_atlassian.servers.jira import update_issue

    err = await call_tool(
        "jira",
        update_issue,
        "jira_update_issue",
        {
            "issue_key": "TEST-1",
            "fields": json.dumps({"summary": "s", "attachments": [secret]}),
        },
        fetcher,
    )

    assert not fetcher.jira.add_attachment.called


async def test_update_issue_attachments_smuggled_in_additional_fields_blocked(
    workspace, tmp_path
):
    secret, _ = make_secret_outside(tmp_path)
    fetcher = make_jira_fetcher()
    from mcp_atlassian.servers.jira import update_issue

    err = await call_tool(
        "jira",
        update_issue,
        "jira_update_issue",
        {
            "issue_key": "TEST-1",
            "fields": json.dumps({"summary": "s"}),
            "additional_fields": json.dumps({"attachments": [secret]}),
        },
        fetcher,
    )

    assert not fetcher.jira.add_attachment.called
