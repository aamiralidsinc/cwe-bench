import os

import harness as h


VOL = ["dkfk:dkfk:r.,u1:g,u2:c,dk,fk"]
FILES = {"dkfk/f.t1": b"f1", "dkfk/s1/f.t2": b"f2"}


def _open(root):
    for rel, data in FILES.items():
        h.mkdirs(root, {rel: data})
    return h.server(root, VOL)


def test_file_key_page_does_not_disclose_the_folder_key(tmp_path):
    """A caller holding one file's key must not leave with the folder's key."""
    root = str(tmp_path)
    s = _open(root)
    try:
        folder_key = h.dirkey(os.path.join(root, "dkfk"))
        own_key = h.filekey(os.path.join(root, "dkfk", "f.t1"))
        status, _, body = h.request(s.conn, "dkfk/f.t1?k=%s&v&ls" % own_key, "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the folder capability was disclosed"
    finally:
        s.close()


def test_file_key_page_does_not_disclose_the_folder_key_in_html(tmp_path):
    root = str(tmp_path)
    s = _open(root)
    try:
        folder_key = h.dirkey(os.path.join(root, "dkfk"))
        own_key = h.filekey(os.path.join(root, "dkfk", "f.t1"))
        status, _, body = h.request(s.conn, "dkfk/f.t1?k=%s&v" % own_key, "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the folder capability was disclosed"
    finally:
        s.close()


def test_nested_file_key_page_does_not_disclose_the_containing_folder_key(tmp_path):
    root = str(tmp_path)
    s = _open(root)
    try:
        folder_key = h.dirkey(os.path.join(root, "dkfk", "s1"))
        own_key = h.filekey(os.path.join(root, "dkfk", "s1", "f.t2"))
        status, _, body = h.request(s.conn, "dkfk/s1/f.t2?k=%s&v&ls" % own_key, "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the containing folder capability was disclosed"
    finally:
        s.close()


def test_each_of_two_file_keys_leaves_the_folder_key_hidden(tmp_path):
    root = str(tmp_path)
    s = _open(root)
    try:
        folder_key = h.dirkey(os.path.join(root, "dkfk"))
        for rel in ("dkfk/f.t1", "dkfk/s1/f.t2"):
            own_key = h.filekey(os.path.join(root, rel))
            status, _, body = h.request(s.conn, rel + "?k=%s&v&ls" % own_key, "u2")
            assert status and status < 500, (rel, status)
            assert not h.dk_in(body, folder_key), rel
    finally:
        s.close()
