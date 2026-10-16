"""CWE-862 missing authorization: the batch check-completion action runs with
no authentication and no organization-membership check, letting an
unauthenticated caller drive another tenant's batch completion/resume.

Exploit entry point: POST /resources/batches/<batchId>/check-completion.
Vulnerable: the action executes (the batch's completion state is advanced) and
redirects to the caller-supplied redirectUrl (HTTP 302 -> /orgs).

Fixed, for an anonymous caller: refused (any 4xx, or a redirect to the login
page; how is the fix's choice) and the batch is left untouched.
Fixed, for a logged-in member of a DIFFERENT organization (2026-10-16): the
batch is left untouched. The response form is the fix's choice (an error
redirect, 403, 404), so only the batch's state is checked.

The batch is tried under both forms it may be addressed by (friendly id and
internal id); the batch's state is read straight from the database.
"""
import tr


def _assert_untouched(batch, who):
    status = tr.batch_status(batch)
    assert status == "PENDING", (
        f"{who} advanced batch {batch}'s completion state (status now {status!r}); "
        f"only a logged-in member of the owning organization may do that."
    )


def test_unauthenticated_check_completion_blocked():
    assert tr.BATCH_ANON, "batch fixture not provided by test.sh"
    assert tr.batch_status(tr.BATCH_ANON) == "PENDING", "fixture batch not in its initial state"
    for ref in tr.batch_refs(tr.BATCH_ANON):
        r = tr.check_completion(ref, redirect_url="/orgs")
        loc = r.get("location") or ""
        refused = 400 <= r["code"] < 500 or (
            r["code"] in (301, 302, 303, 307, 308) and "/login" in loc)
        assert refused, (
            f"unauthenticated check-completion on {ref} was not refused (HTTP {r['code']}, "
            f"Location={loc!r}); it must require a logged-in member."
        )
    _assert_untouched(tr.BATCH_ANON, "an unauthenticated caller")


def test_other_org_member_check_completion_blocked():
    assert tr.BATCH_XORG and tr.OUTSIDER_EMAIL, "fixtures not provided by test.sh"
    assert tr.batch_status(tr.BATCH_XORG) == "PENDING", "fixture batch not in its initial state"
    cookie = tr.login_session(tr.OUTSIDER_EMAIL)
    assert cookie, "magic-link login of the other organization's user did not yield a session"
    # Sanity: the session really is logged in (else this would only re-test the anonymous case).
    me = tr.call("GET", "/account", cookie=cookie)
    assert "/login" not in (me.get("location") or ""), (
        f"the other organization's user is not logged in (GET /account -> {me['code']} "
        f"{me.get('location')!r})")
    for ref in tr.batch_refs(tr.BATCH_XORG):
        tr.check_completion(ref, redirect_url="/orgs", cookie=cookie)
    _assert_untouched(tr.BATCH_XORG, "a logged-in member of a different organization")
