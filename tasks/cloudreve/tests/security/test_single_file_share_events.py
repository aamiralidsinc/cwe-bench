"""A single-file share exposes only that one file. The server-side event stream
is a folder-level topic, so a holder of a single-file share must not be allowed
to subscribe to events through the share: doing so would leak activity about
other, unshared files in the owner's folder. Subscribing via a single-file
share URI must be refused up front."""
import cr


def test_single_file_share_event_subscription_refused():
    token = cr.ensure_admin()
    folder = "cloudreve://my/%s" % cr.uniq("box")
    cr.mkfolder(token, folder)
    doc = folder + "/doc.txt"
    cr.upload(token, doc, b"hi")
    cr.upload(token, folder + "/secret.txt", b"sibling-secret")
    share_url = cr.share(token, doc)
    share_id = share_url.rstrip("/").split("/")[-1]
    share_uri = "cloudreve://%s@share" % share_id
    res = cr.events(token, share_uri, timeout=5)
    # Refused => an immediate JSON error (non-zero code). Accepted => the SSE
    # stream is held open and the client read times out.
    assert not res.get("timeout"), "event subscription was accepted on a single-file share"
    assert cr.j(res).get("code") not in (0, None), \
        "event subscription was not refused: %r" % res
