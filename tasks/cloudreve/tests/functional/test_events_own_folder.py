"""A user must still be able to subscribe to the event stream of a folder they
own. The subscription is accepted and the SSE stream is held open (so a short
client read times out rather than returning an immediate error)."""
import cr


def test_owner_can_subscribe_to_own_folder_events():
    token = cr.ensure_admin()
    folder = "cloudreve://my/%s" % cr.uniq("box")
    cr.mkfolder(token, folder)
    res = cr.events(token, folder, timeout=5)
    if res.get("timeout"):
        return  # stream held open == accepted
    # If it returned immediately, it must not be a permission/param refusal.
    assert cr.j(res).get("code") in (0, None), \
        "owner was refused subscription to their own folder: %r" % res
