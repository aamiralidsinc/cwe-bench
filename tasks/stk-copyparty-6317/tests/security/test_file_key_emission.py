import os

import harness as h


VOL = ["dkfk:dkfk:r.,u1:g,u2:c,dk,fk"]


def test_file_key_page_does_not_disclose_the_folder_key(tmp_path):
    """A caller holding one file's key must not leave with the folder's key."""
    root = str(tmp_path)
    h.mkdirs(root, {"dkfk/f.t1": b"f1", "dkfk/s1/f.t2": b"f2"})
    s = h.server(root, VOL)
    try:
        folder_key = h.dirkey(os.path.join(root, "dkfk"))
        own_key = h.filekey(os.path.join(root, "dkfk", "f.t1"))

        status, _, body = h.request(
            s.conn, "dkfk/f.t1?k=%s&v&ls" % own_key, "u2"
        )
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the folder capability was disclosed"

        # the file the caller did hold a key for is still served to that caller
        status, _, body = h.request(s.conn, "dkfk/f.t1?k=%s" % own_key, "u2")
        assert status == 200, status
        assert body == b"f1"
    finally:
        s.close()
