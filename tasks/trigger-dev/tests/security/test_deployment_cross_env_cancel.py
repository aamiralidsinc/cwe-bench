"""CWE-639 broken authorization: a deployment must only be cancelable with a
credential scoped to the SAME environment. The cancel lookup is scoped by
project only, so any environment's API key in the project (e.g. a low-trust
DEVELOPMENT key) can cancel another environment's (e.g. PRODUCTION) in-progress
deployment.

Exploit entry point: POST /api/v1/deployments/<id>/cancel.
Vulnerable: DEV key cancels a PROD deployment (HTTP 204). Fixed: not found for
the DEV env (HTTP 404), deployment stays live.
"""
import os
import tr


def test_cross_env_cancel_blocked():
    assert tr.PROD_KEY and tr.DEV_KEY, "fixtures not provided by test.sh"
    ch = "x" + os.urandom(8).hex()
    created = tr.create_deployment(tr.PROD_KEY, ch)
    assert created["code"] == 200, f"could not create PROD deployment: {created}"
    dep_id = tr.deployment_id_of(created)
    assert dep_id, f"no deployment id in {created['body'][:200]!r}"

    # Attacker uses the DEVELOPMENT env key to cancel the PRODUCTION deployment.
    r = tr.cancel_deployment(dep_id, tr.DEV_KEY)
    assert r["code"] != 204, (
        f"a DEVELOPMENT-scoped key canceled a PRODUCTION deployment "
        f"(HTTP {r['code']}); cross-environment cancel must be refused."
    )
    assert 400 <= r["code"] < 500, (
        f"cross-env cancel was not refused with a 4xx (HTTP {r['code']})"
    )
