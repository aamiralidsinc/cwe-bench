import os

import harness as h


CFG = ["srcvol:srcvol:r,u1:g,u2:c,dk,dks,fk", "::A,u1"]
SHARGS = dict(shr="/shr/", shr1="shr/", shr_db="a.db", shr_v=False)


def test_folder_share_still_navigates_its_subfolders(tmp_path):
    """A share of a whole folder keeps its subfolder navigation."""
    root = str(tmp_path)
    h.mkdirs(
        root,
        {
            "srcvol/one.txt": b"one",
            "srcvol/sub/deep.txt": b"deep",
        },
    )
    h.init_share_db(os.path.join(root, "a.db"))
    s = h.server(root, CFG, up2k=True, **SHARGS)
    try:
        h.create_share(s.conn, "s2", ["/srcvol/"], ["read"])
    finally:
        s.close()

    s = h.server(root, CFG, **SHARGS)
    try:
        status, _, body = h.request(s.conn, "shr/s2?ls", "u2")
        assert status == 200, status
        z = h.parse_json(body)
        assert z, body[:200]
        subs = [x["href"] for x in z["dirs"] if x["href"].startswith("sub/")]
        assert subs, z["dirs"]
        status, _, body = h.request(s.conn, "shr/s2/%s&ls" % subs[0], "u2")
        assert status == 200, status
        z2 = h.parse_json(body)
        assert z2 and len(z2["files"]) == 1, body[:200]
        assert z2["files"][0]["href"].startswith("deep.txt"), z2["files"]
        status, _, body = h.request(s.conn, "shr/s2/sub/deep.txt", "u2")
        assert status == 200 and body == b"deep", (status, body[:20])
    finally:
        s.close()
