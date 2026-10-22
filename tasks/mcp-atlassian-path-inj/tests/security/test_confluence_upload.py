"""Confluence attachment upload must not read a file outside the workspace.

Same confinement contract as the Jira attachment upload, in the Confluence
product package: a path resolving outside the working directory is refused and
the file is never opened/sent (``_upload_attachment_direct`` is never reached).
"""

import os

from conftest import make_confluence_attachments_mixin, make_secret_outside


def test_confluence_upload_absolute_outside(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    mixin = make_confluence_attachments_mixin()

    result = mixin.upload_attachment("123456", secret)

    assert not mixin._upload_attachment_direct.called
    assert result.get("success") is not True


def test_confluence_upload_relative_traversal(workspace, tmp_path):
    secret, _ = make_secret_outside(tmp_path)
    rel = os.path.relpath(secret, os.getcwd())
    mixin = make_confluence_attachments_mixin()

    result = mixin.upload_attachment("123456", rel)

    assert not mixin._upload_attachment_direct.called
    assert result.get("success") is not True
