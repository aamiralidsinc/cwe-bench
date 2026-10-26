import io
import os
import zipfile

import harness as h


def _names(body):
    return zipfile.ZipFile(io.BytesIO(body)).namelist()


def test_visible_files_can_still_be_archived(tmp_path):
    """Archiving the caller's own visible files keeps working."""
    root = str(tmp_path)
    h.mkdirs(root, {"zv/a.txt": b"A", "zv/sub/b.txt": b"B"})
    s = h.server(root, ["zv:zv:r,u1:g,u2:c,dk"])
    try:
        key = h.dirkey(os.path.join(root, "zv"))
        status, _, body = h.request_zip_sel(
            s.conn, "zv?zip&k=%s" % key, "u2", ["a.txt"]
        )
        assert status == 200, status
        assert "a.txt" in _names(body), _names(body)
    finally:
        s.close()


def test_read_caller_can_still_archive_a_subfolder(tmp_path):
    root = str(tmp_path)
    h.mkdirs(root, {"zv/a.txt": b"A", "zv/sub/b.txt": b"B"})
    s = h.server(root, ["zv:zv:r,u1:g,u2:c,dk"])
    try:
        status, _, body = h.request_zip_sel(s.conn, "zv?zip", "u1", ["sub"])
        assert status == 200, status
        assert any(n.endswith("sub/b.txt") for n in _names(body)), _names(body)
    finally:
        s.close()


def test_folder_key_with_subfolders_can_still_download_the_folder(tmp_path):
    root = str(tmp_path)
    h.mkdirs(root, {"zv/a.txt": b"A", "zv/sub/b.txt": b"B"})
    s = h.server(root, ["zv:zv:r,u1:g,u2:c,dk,dks"])
    try:
        key = h.dirkey(os.path.join(root, "zv"))
        status, _, body = h.request(s.conn, "zv?zip&k=%s" % key, "u2")
        assert status == 200, status
        names = _names(body)
        assert any(n.endswith("a.txt") for n in names), names
        assert any(n.endswith("sub/b.txt") for n in names), names
    finally:
        s.close()
