import os

import harness as h


def test_index_is_served_without_a_file_key(tmp_path):
    """Permission for the html index keeps meaning what it means today."""
    root = str(tmp_path)
    h.mkdirs(root, {"hv/index.html": b"<html>welcome</html>", "hv/other.txt": b"other"})
    s = h.server(root, ["hv:hv:r.,u1:h,u2:c,dk,fk"])
    try:
        status, _, body = h.request(s.conn, "hv/index.html", "u2")
        assert status == 200, status
        assert b"welcome" in body
    finally:
        s.close()
