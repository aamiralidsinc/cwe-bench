import os

import harness as h


CFG = ["srcvol:srcvol:r,u1:g,u2:c,dk,fk", "::A,u1"]
SHARGS = dict(shr="/shr/", shr1="shr/", shr_db="a.db", shr_v=False)


def _make_share(root):
    h.mkdirs(
        root,
        {
            "srcvol/secret.txt": b"secret",
            "srcvol/other.txt": b"other",
            "srcvol/sub/deep.txt": b"deep",
        },
    )
    h.init_share_db(os.path.join(root, "a.db"))

    s = h.server(root, CFG, up2k=True, **SHARGS)
    try:
        h.create_share(s.conn, "s1", ["/srcvol/secret.txt"], ["read"])
    finally:
        s.close()

    return h.server(root, CFG, **SHARGS)


def test_single_file_share_does_not_disclose_the_source_folder_key(tmp_path):
    """A share for one file must not hand the recipient the source folder's key."""
    root = str(tmp_path)
    s = _make_share(root)
    try:
        source_key = h.dirkey(os.path.join(root, "srcvol"))

        status, _, body = h.request(s.conn, "shr/s1?ls", "u2")
        assert status and status < 500, status
        assert not h.dk_in(body, source_key), "the source folder capability was disclosed"
        assert b'"dk"' not in body, "a folder capability field was disclosed"

        # the shared file itself is still reachable through the share
        status, _, body = h.request(s.conn, "shr/s1/secret.txt", "u2")
        assert status == 200, status
        assert body == b"secret"
    finally:
        s.close()
