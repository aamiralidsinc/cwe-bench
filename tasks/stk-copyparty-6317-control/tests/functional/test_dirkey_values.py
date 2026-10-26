import os

import harness as h


def test_dirkey_listing_keeps_the_values_a_recipient_needs(tmp_path):
    """A folder-key recipient keeps its file links and can enter subfolders."""
    root = str(tmp_path)
    h.mkdirs(
        root,
        {
            "dks/f.t1": b"f1",
            "dks/s1/f.t2": b"f2",
            "dks/s1/s2/f.t3": b"f3",
        },
    )
    s = h.server(root, ["dks:dks:r.,u1:g,u2:c,dk,dks,fk"])
    try:
        key = h.dirkey(os.path.join(root, "dks"))
        status, _, body = h.request(s.conn, "dks?ls&k=%s" % key, "u2")
        assert status == 200, status
        z = h.parse_json(body)
        assert z, body[:200]

        fk = [x["href"] for x in z["files"] if x["href"].startswith("f.t1")][0]
        assert "?k=" in fk, fk
        status, _, got = h.request(s.conn, "dks/" + fk, "u2")
        assert status == 200 and got == b"f1", (status, got[:20])

        sub = [x["href"] for x in z["dirs"] if x["href"].startswith("s1/")][0]
        assert "?k=" in sub, sub
        status, _, body = h.request(s.conn, "dks/%s&ls" % sub, "u2")
        assert status == 200, status
        z2 = h.parse_json(body)
        assert z2 and len(z2["files"]) == 1, body[:200]
        assert z2["files"][0]["href"].startswith("f.t2"), z2["files"]
    finally:
        s.close()
