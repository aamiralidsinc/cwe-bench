"""Functional: creating an email alert channel still works (alerting feature)."""
import tr

def test_email_channel_accepted():
    assert tr.PAT and tr.PROJREF, "fixtures not provided by test.sh"
    r = tr.create_email_channel("ops@example.com")
    assert r["code"] == 200, f"email alert channel rejected (HTTP {r['code']}): {r['body'][:200]!r}"
