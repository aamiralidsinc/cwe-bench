"""Functional: an authenticated member may still invoke batch check-completion
on their own organization's batch (the authorization fix must not block
logged-in members). We assert the request is NOT bounced to login, the
action proceeds and redirects back into the app, and (2026-10-16) that it
really took effect: the seeded batch (a development batch with no pending
child runs) leaves its initial PENDING state, as it does on the original code.
A fix that answers every member with an error message fails here.

A batch id that does not exist (or is not the caller's) may be answered either
way a correct fix chooses: a redirect with an error message, 403 or 404, but
never a bounce to login for a logged-in user."""
import tr


def test_authenticated_check_completion_allowed():
    assert tr.BATCH, "batch fixture not provided by test.sh"
    cookie = tr.login_session()
    assert cookie, "magic-link login did not yield a session"
    # The batch may be addressed by its friendly id (batch_...) or its internal id; neither
    # the instruction nor the original endpoint fixes one form, so either may work (2026-10-16).
    assert tr.batch_status(tr.BATCH) == "PENDING", "fixture batch not in its initial state"
    for batch_ref in tr.batch_refs(tr.BATCH):
        r = tr.check_completion(batch_ref, redirect_url="/orgs", cookie=cookie)
        loc = r.get("location") or ""
        if r["code"] in (302, 200) and "/login" not in loc and tr.batch_status(tr.BATCH) != "PENDING":
            break
    assert "/login" not in loc, (
        f"an authenticated member was bounced to login (HTTP {r['code']}, "
        f"Location={loc!r}); check-completion must stay usable when logged in."
    )
    assert r["code"] in (302, 200), (
        f"a member's check-completion on their own batch was refused (HTTP {r['code']})"
    )
    status = tr.batch_status(tr.BATCH)
    assert status != "PENDING", (
        f"a member's check-completion on their own batch did not take effect (batch status "
        f"still {status!r} under both id forms); the endpoint must stay usable for members."
    )


def test_authenticated_check_completion_unknown_batch_not_bounced():
    cookie = tr.login_session()
    assert cookie, "magic-link login did not yield a session"
    r = tr.check_completion("batch_doesnotexist0001", redirect_url="/orgs", cookie=cookie)
    loc = r.get("location") or ""
    assert "/login" not in loc, (
        f"an authenticated user was bounced to login (HTTP {r['code']}, Location={loc!r})"
    )
    assert r["code"] in (302, 200, 403, 404), f"unexpected status {r['code']}"
