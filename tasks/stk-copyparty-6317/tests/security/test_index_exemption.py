import os

import harness as h


VOL = ["hv:hv:r.,u1:h,u2:c,dk,fk"]


def test_keyless_index_page_does_not_disclose_the_folder_key(tmp_path):
    """The index.html exemption must not turn into a folder capability."""
    root = str(tmp_path)
    h.mkdirs(
        root,
        {
            "hv/index.html": b"<html>welcome</html>",
            "hv/other.txt": b"other",
            "hv/s1/f2": b"f2",
        },
    )
    s = h.server(root, VOL)
    try:
        folder_key = h.dirkey(os.path.join(root, "hv"))

        status, _, body = h.request(s.conn, "hv/index.html?v&ls", "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, folder_key), "the folder capability was disclosed"

        status, _, body = h.request(s.conn, "hv/index.html", "u2")
        assert status == 200, status
        assert b"welcome" in body
    finally:
        s.close()
