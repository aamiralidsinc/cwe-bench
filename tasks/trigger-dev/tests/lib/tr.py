"""Thin HTTP client for driving a running trigger.dev webapp over its real API,
exactly as a dashboard browser / API-key client / CLI would. Stdlib only.

Config comes from the environment (set by test.sh after it seeds fixtures):
  TR_BASE       base origin, e.g. http://127.0.0.1:3030
  TR_PAT        a Personal Access Token (tr_pat_...) for /api/v1 PAT routes
  TR_PROJREF    hello-world project external ref (proj_...)
  TR_PROD_KEY   hello-world PRODUCTION env secret key (tr_prod_...)
  TR_DEV_KEY    hello-world DEVELOPMENT env secret key (tr_dev_...)
  TR_STAGING_KEY hello-world STAGING env secret key
  TR_RUN        friendlyId of a seeded TaskRun in the DEVELOPMENT env
  TR_EMAIL      an existing user's email for the magic-link login flow
  TR_BATCH      friendlyId of a seeded batch in the logged-in user's own org
  TR_BATCH_ANON, TR_BATCH_XORG
                friendlyIds of two more batches there (security-test targets)
  TR_OUTSIDER_EMAIL
                a user who belongs only to a DIFFERENT organization
"""
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("TR_BASE", "http://127.0.0.1:3030")
PAT = os.environ.get("TR_PAT", "")
PROJREF = os.environ.get("TR_PROJREF", "")
PROD_KEY = os.environ.get("TR_PROD_KEY", "")
DEV_KEY = os.environ.get("TR_DEV_KEY", "")
STAGING_KEY = os.environ.get("TR_STAGING_KEY", "")
RUN = os.environ.get("TR_RUN", "")
BATCH = os.environ.get("TR_BATCH", "")
BATCH_ANON = os.environ.get("TR_BATCH_ANON", "")
BATCH_XORG = os.environ.get("TR_BATCH_XORG", "")
OUTSIDER_EMAIL = os.environ.get("TR_OUTSIDER_EMAIL", "")
EMAIL = os.environ.get("TR_EMAIL", "local@trigger.dev")


def call(method, path, token=None, json_body=None, form=None, raw=None,
         headers=None, cookie=None, timeout=30, allow_redirects=False):
    """One HTTP request. Returns dict with code, body, location, set_cookie.
    Never follows redirects unless allow_redirects=True."""
    h = dict(headers or {})
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode()
        h.setdefault("Content-Type", "application/json")
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        h.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif raw is not None:
        data = raw
    if token:
        h["Authorization"] = "Bearer " + token
    if cookie:
        h["Cookie"] = cookie
    url = path if path.startswith("http") else BASE + path

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            return None

    opener = urllib.request.build_opener(
        *( [] if allow_redirects else [_NoRedirect] ))
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        resp = opener.open(req, timeout=timeout)
        return _wrap(resp.getcode(), resp)
    except urllib.error.HTTPError as e:
        return _wrap(e.code, e)
    except Exception as e:  # pragma: no cover
        return {"code": -1, "err": str(e), "body": b"", "location": None, "set_cookie": None}


def _wrap(code, resp):
    try:
        body = resp.read(1 << 16)
    except Exception:
        body = b""
    return {
        "code": code,
        "body": body,
        "location": resp.headers.get("Location"),
        "set_cookie": resp.headers.get("Set-Cookie"),
        "ct": resp.headers.get("Content-Type"),
    }


def j(resp):
    try:
        return json.loads(resp["body"])
    except Exception:
        return {}


# --- domain helpers -------------------------------------------------------

def create_alert_channel(url, project=None, token=None):
    """POST a WEBHOOK alert channel with the given delivery url (PAT auth)."""
    return call("POST", f"/api/v1/projects/{project or PROJREF}/alertChannels",
                token=token or PAT,
                json_body={"name": "t", "channel": "webhook",
                           "alertTypes": ["run_failure"],
                           "channelData": {"url": url}})


def create_email_channel(email="ops@example.com", project=None, token=None):
    return call("POST", f"/api/v1/projects/{project or PROJREF}/alertChannels",
                token=token or PAT,
                json_body={"name": "e", "channel": "email",
                           "alertTypes": ["run_failure"],
                           "channelData": {"email": email}})


def create_deployment(key, content_hash):
    return call("POST", "/api/v1/deployments", token=key,
                json_body={"contentHash": content_hash})


def cancel_deployment(deployment_id, key):
    return call("POST", f"/api/v1/deployments/{deployment_id}/cancel",
                token=key, json_body={})


def deployment_id_of(resp):
    body = resp.get("body", b"")
    try:
        return json.loads(body)["id"]
    except Exception:
        import re
        m = re.search(rb"deployment_[a-z0-9]+", body)
        return m.group(0).decode() if m else None


def stream_write(run_friendly_id, stream_id, data=b"INJECT", cookie=None, token=None,
                 target=None):
    """POST data into a run's realtime stream. Without `target` this is the
    /realtime/v1/streams/<run>/<stream> route (the anonymous write); with
    target="self" it is the API-key route /realtime/v1/streams/<run>/self/<stream>."""
    mid = f"/{target}" if target else ""
    return call("POST", f"/realtime/v1/streams/{run_friendly_id}{mid}/{stream_id}",
                raw=data, token=token, cookie=cookie,
                headers={"Content-Type": "application/octet-stream"})


def redis_keys_containing(text):
    """Every Redis key whose name contains `text` (the local Redis that backs
    realtime streams). Read straight from Redis, not through the app."""
    assert re.fullmatch(r"[A-Za-z0-9_-]+", text)
    out = subprocess.run(["redis-cli", "-h", "127.0.0.1", "--scan", "--pattern", f"*{text}*"],
                         capture_output=True, text=True, timeout=30)
    return [k for k in out.stdout.split() if k]


def batch_status(friendly_id):
    """The batch's status, read straight from Postgres (not through the app)."""
    assert re.fullmatch(r"[A-Za-z0-9_]+", friendly_id)
    out = subprocess.run(
        ["psql", "-h", "127.0.0.1", "-U", "postgres", "-d", "main", "-tAc",
         f"SELECT status FROM \"BatchTaskRun\" WHERE \"friendlyId\" = '{friendly_id}'"],
        capture_output=True, text=True, timeout=30)
    return out.stdout.strip()


def batch_refs(friendly_id):
    """Both forms a batch may be addressed by: its friendly id (batch_...) and
    its internal id. Neither the instruction nor the original endpoint fixes one."""
    return (friendly_id, friendly_id.split("_", 1)[-1])


def check_completion(batch_id, redirect_url="/orgs", cookie=None):
    return call("POST", f"/resources/batches/{batch_id}/check-completion",
                form={"redirectUrl": redirect_url}, cookie=cookie)


def login_session(email=None):
    """Complete the magic-link login flow (dev mode auto-redirects to the
    link) and return the session Cookie header value for an authenticated user."""
    email = email or EMAIL
    jar = {}

    def _store(resp):
        sc = resp.get("set_cookie")
        if sc:
            for part in sc.split(","):
                kv = part.strip().split(";")[0]
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if k.strip():
                        jar[k.strip()] = v

    def _hdr():
        return "; ".join(f"{k}={v}" for k, v in jar.items())

    r1 = call("POST", "/login/magic", form={"action": "send", "email": email},
              cookie=_hdr())
    _store(r1)
    link = r1.get("location")
    if not link:
        return None
    r2 = call("GET", link, cookie=_hdr())
    _store(r2)
    return _hdr()
