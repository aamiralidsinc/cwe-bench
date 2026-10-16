"""Functional: cancelling a deployment with its OWN environment's key still
works (the authorization fix must not block legitimate same-env cancels).

2026-10-16: runs in the STAGING environment, so it is that environment's only
deployment. The product numbers a new deployment from the environment's
latest-by-creation-time one; with three deployments in one environment, a
backwards step of the container clock (seen in a gate run: "-0.97s" test
session) made the third creation collide on the version and fail with 500
for the reference fix. One deployment per environment per test avoids that."""
import os, tr

def test_same_env_cancel_works():
    assert tr.STAGING_KEY, "fixtures not provided by test.sh"
    created = tr.create_deployment(tr.STAGING_KEY, "f" + os.urandom(8).hex())
    assert created["code"] == 200, f"deploy create failed: {created}"
    dep_id = tr.deployment_id_of(created)
    r = tr.cancel_deployment(dep_id, tr.STAGING_KEY)
    assert r["code"] == 204, f"legit same-env cancel failed (HTTP {r['code']})"
