"""Legitimate Confluence uploads keep working, including the base64 path.

The in-memory (base64 / bytes) upload path never touches the filesystem and
must not be affected by the file-path confinement.
"""

from conftest import make_confluence_attachments_mixin


def test_confluence_upload_relative_inside_workspace(workspace):
    (workspace / "diagram.png").write_bytes(b"\x89PNG")
    mixin = make_confluence_attachments_mixin()

    result = mixin.upload_attachment("123456", "diagram.png")

    assert result.get("success") is True
    assert mixin._upload_attachment_direct.called


def test_confluence_upload_absolute_inside_workspace(workspace):
    p = workspace / "img" / "logo.png"
    p.parent.mkdir()
    p.write_bytes(b"\x89PNG")
    mixin = make_confluence_attachments_mixin()

    result = mixin.upload_attachment("123456", str(p))

    assert result.get("success") is True
    assert mixin._upload_attachment_direct.called


def test_confluence_upload_from_content_bytes(workspace):
    mixin = make_confluence_attachments_mixin()

    result = mixin.upload_attachment_from_content(
        "123456", "inline.txt", b"raw bytes, no path"
    )

    assert result.get("success") is True
    assert mixin._upload_attachment_from_bytes.called
