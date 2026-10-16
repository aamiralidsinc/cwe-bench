"""Functional: creating a webhook alert channel whose URL points at a legitimate
public host must still succeed (the SSRF fix must not block normal webhooks)."""
import tr

def test_public_webhook_channel_accepted():
    assert tr.PAT and tr.PROJREF, "fixtures not provided by test.sh"
    r = tr.create_alert_channel("http://8.8.8.8/my-webhook")
    assert r["code"] == 200, f"legit public webhook rejected (HTTP {r['code']}): {r['body'][:200]!r}"
