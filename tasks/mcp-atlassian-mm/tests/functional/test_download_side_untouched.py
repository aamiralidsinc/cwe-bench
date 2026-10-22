"""The server's existing write-side confinement must keep working.

The server already confines caller-named *destination* paths for files it
writes to inside the working directory. That protection is not the subject of
this report, and a change must not disturb it: an in-workspace destination is
still written, an out-of-workspace destination is still refused.
"""

from unittest.mock import MagicMock

from conftest import make_jira_attachments_mixin


def _stub_response(payload: bytes = b"attachment-bytes"):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.iter_content.return_value = [payload]
    return resp


def test_download_to_inside_workspace_still_works(workspace):
    mixin = make_jira_attachments_mixin()
    mixin.jira._session.get.return_value = _stub_response()
    target = workspace / "downloads" / "file.bin"

    ok = mixin.download_attachment("https://example.atlassian.net/attach/1", str(target))

    assert ok is True
    assert target.read_bytes() == b"attachment-bytes"


def test_download_to_outside_workspace_still_refused(workspace, tmp_path):
    mixin = make_jira_attachments_mixin()
    mixin.jira._session.get.return_value = _stub_response()
    outside = tmp_path / "outside" / "stolen.bin"

    ok = mixin.download_attachment("https://example.atlassian.net/attach/1", str(outside))

    assert ok is False
    assert not outside.exists()
