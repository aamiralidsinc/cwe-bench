"""Legitimate Jira uploads of files inside the workspace keep working."""

import os

from conftest import make_jira_attachments_mixin


def test_upload_relative_inside_workspace(workspace):
    (workspace / "report.txt").write_text("hello", encoding="utf-8")
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachment("TEST-1", "report.txt")

    assert result.get("success") is True
    assert mixin.jira.add_attachment.called


def test_upload_absolute_inside_workspace(workspace):
    p = workspace / "data" / "payload.bin"
    p.parent.mkdir()
    p.write_bytes(b"\x00\x01\x02")
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachment("TEST-1", str(p))

    assert result.get("success") is True
    assert mixin.jira.add_attachment.called


def test_upload_attachments_list_inside_workspace(workspace):
    (workspace / "a.txt").write_text("a", encoding="utf-8")
    (workspace / "b.txt").write_text("b", encoding="utf-8")
    mixin = make_jira_attachments_mixin()

    result = mixin.upload_attachments("TEST-1", ["a.txt", "b.txt"])

    assert len(result.get("uploaded", [])) == 2
    assert mixin.jira.add_attachment.call_count == 2
