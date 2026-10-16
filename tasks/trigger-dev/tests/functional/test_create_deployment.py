"""Functional: initializing a deployment via the API still works."""
import os, tr

def test_create_deployment_works():
    assert tr.PROD_KEY, "fixtures not provided by test.sh"
    r = tr.create_deployment(tr.PROD_KEY, "c" + os.urandom(8).hex())
    assert r["code"] == 200, f"deployment init failed (HTTP {r['code']}): {r['body'][:200]!r}"
    assert tr.deployment_id_of(r), "no deployment id returned"
