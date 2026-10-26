import os

import harness as h


def test_file_key_viewer_still_works(tmp_path):
    """The documented file-key plus viewer combination keeps working."""
    root = str(tmp_path)
    h.mkdirs(root, {"dkfk/f.t1": b"f1"})
    s = h.server(root, ["dkfk:dkfk:r.,u1:g,u2:c,dk,fk"])
    try:
        fk = h.filekey(os.path.join(root, "dkfk", "f.t1"))

        status, _, body = h.request(s.conn, "dkfk/f.t1?k=%s&v" % fk, "u2")
        assert status == 200, status
        assert body == b"f1" or b"f.t1" in body, body[:200]

        status, _, body = h.request(s.conn, "dkfk/f.t1?k=%s&v&ls" % fk, "u2")
        assert status == 200, status
        z = h.parse_json(body)
        assert z is not None
        assert len(z["files"]) == 1, z
        assert z["files"][0]["href"].startswith("f.t1"), z["files"]
    finally:
        s.close()
