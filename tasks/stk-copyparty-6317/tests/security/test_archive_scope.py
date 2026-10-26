import io
import os
import zipfile

import harness as h


VOL = ["zv:zv:r,u1:g,u2:c,dk"]


def _names(body):
    try:
        return zipfile.ZipFile(io.BytesIO(body)).namelist()
    except Exception:
        return None


def _archive_is_clean(status, body):
    assert status and status < 500, status
    if 400 <= status < 500:
        return
    assert 200 <= status < 300, status
    names = _names(body)
    if names is None:
        return
    leaked = [n for n in names if n.endswith("sub/b.txt") or n.endswith("deeper/c.txt")]
    assert not leaked, "subfolder contents were archived: %r" % (leaked,)


def test_folder_key_cannot_archive_a_subfolder(tmp_path):
    """A key issued for one folder must not reach its subfolder through an archive."""
    root = str(tmp_path)
    h.mkdirs(
        root,
        {
            "zv/a.txt": b"A",
            "zv/sub/b.txt": b"B",
            "zv/sub/deeper/c.txt": b"C",
        },
    )
    s = h.server(root, VOL)
    try:
        folder_key = h.dirkey(os.path.join(root, "zv"))
        status, _, body = h.request_zip_sel(
            s.conn, "zv?zip&k=%s" % folder_key, "u2", ["sub"]
        )
        _archive_is_clean(status, body)
    finally:
        s.close()


def test_folder_key_mixed_selection_cannot_archive_a_subfolder(tmp_path):
    root = str(tmp_path)
    h.mkdirs(
        root,
        {
            "zv/a.txt": b"A",
            "zv/sub/b.txt": b"B",
            "zv/sub/deeper/c.txt": b"C",
        },
    )
    s = h.server(root, VOL)
    try:
        folder_key = h.dirkey(os.path.join(root, "zv"))
        status, _, body = h.request_zip_sel(
            s.conn, "zv?zip&k=%s" % folder_key, "u2", ["a.txt", "sub"]
        )
        _archive_is_clean(status, body)
    finally:
        s.close()
