"""Core account + file features must keep working."""
import cr


def test_login_and_me():
    token = cr.ensure_admin()
    assert token
    me = cr.j(cr.call("GET", "/user/me", token=token))
    assert me.get("code") == 0
    assert me["data"]["email"] == "admin@cloudreve.test"


def test_upload_and_list():
    token = cr.ensure_admin()
    name = cr.uniq("file") + ".txt"
    uri = "cloudreve://my/" + name
    up = cr.j(cr.upload(token, uri, b"hello world"))
    assert up.get("code") == 0, "upload failed: %r" % up
    assert uri in cr.listing(token, "cloudreve://my")


def test_search_finds_active_user():
    token = cr.ensure_admin()
    # The admin itself is an active account and must be found by search.
    results = cr.search(token, "admin")
    assert any(u.get("email") == "admin@cloudreve.test" for u in results), \
        "active user not returned by search: %r" % results
