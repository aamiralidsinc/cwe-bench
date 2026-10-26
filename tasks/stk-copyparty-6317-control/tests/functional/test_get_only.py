import os

import harness as h


def test_get_only_caller_can_still_download_a_named_file(tmp_path):
    """Permission to get a folder's files by name keeps working."""
    root = str(tmp_path)
    h.mkdirs(root, {"d3/f.t1": b"f1", "d3/s1/f.t2": b"f2"})
    s = h.server(root, ["d3:d3:r.,u1:g,u2:c,dk,dks"])
    try:
        for url, want in (("d3/f.t1", b"f1"), ("d3/s1/f.t2", b"f2")):
            status, _, body = h.request(s.conn, url, "u2")
            assert status == 200, (url, status)
            assert body == want, (url, body[:20])
    finally:
        s.close()
