import os

import harness as h


VOL = ["d3:d3:r.,u1:g,u2:c,dk,dks"]


def test_keyless_get_volume_page_does_not_disclose_the_folder_key(tmp_path):
    """Where no file keys are configured, the page must not hand out a folder key."""
    root = str(tmp_path)
    h.mkdirs(
        root,
        {"d3/f.t1": b"f1", "d3/s1/f.t2": b"f2", "d3/s1/s2/f.t3": b"f3"},
    )
    s = h.server(root, VOL)
    try:
        folder_key = h.dirkey(os.path.join(root, "d3"))

        status, _, body = h.request(s.conn, "d3/f.t1?v&ls", "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the folder capability was disclosed"

        # a get-only caller can still download a file it knows the name of
        status, _, body = h.request(s.conn, "d3/f.t1", "u2")
        assert status == 200, status
        assert body == b"f1"
    finally:
        s.close()
