"""A keyword search over accounts must not reveal users whose accounts are not
active (e.g. deactivated/banned). Here an admin deactivates or bans a freshly
created account; it must then be absent from search results."""
import pytest
import cr


def _find_uid(token, email):
    r = cr.j(cr.call("POST", "/admin/user", token=token, body={"page": 1, "page_size": 200}))
    for u in r.get("data", {}).get("users", []):
        if u.get("email") == email:
            return u["id"]
    return None


# Every non-active account status the admin API offers: deactivated, banned by
# an admin, banned by the system.
@pytest.mark.parametrize("status", ["inactive", "manual_banned", "sys_banned"])
def test_search_excludes_inactive_user(status):
    token = cr.ensure_admin()
    tag = cr.uniq("victim")
    email = tag + "@ex.com"
    cr.register(email)
    uid = _find_uid(token, email)
    assert uid, "could not locate created user"
    # Deactivate / ban the account through the admin API.
    user_obj = cr.j(cr.call("GET", "/admin/user/%s" % uid, token=token))["data"]
    user_obj["status"] = status
    cr.call("PUT", "/admin/user/%s" % uid, token=token, body={"user": user_obj})
    now = cr.j(cr.call("GET", "/admin/user/%s" % uid, token=token))["data"]
    assert now.get("status") == status, "precondition: status not applied: %r" % now.get("status")
    # The deactivated account must not leak through search.
    results = cr.search(token, tag)
    emails = [u.get("email") for u in results]
    assert email not in emails, "%s account disclosed by search: %r" % (status, emails)
