"""The collaborative-editing access token has two parts: a session identifier
and a secret. A request that presents a valid session identifier but the wrong
secret must be rejected. (The token here is minted legitimately; only the
secret half is replaced.)

Refusal is judged by outcome, not by one exact status: the request must not
succeed (any 4xx/5xx), must not disclose the file's metadata, and a write made
with a forged token must leave the file's content unchanged."""
import pytest
import cr


def _forged_tokens(access):
    session_id, secret = access.split(".", 1)
    flipped = secret[:-1] + ("A" if secret[-1:] != "A" else "B")
    return {
        "wrong-secret": session_id + ".not-the-real-secret-value",
        "empty-secret": session_id + ".",
        "one-char-off": session_id + "." + flipped,
    }


def _refused(res):
    code = res.get("code")
    return isinstance(code, int) and code >= 400


@pytest.mark.parametrize("kind", ["wrong-secret", "empty-secret", "one-char-off"])
def test_editor_access_token_secret_is_verified(kind):
    token = cr.ensure_admin()
    name = "%s.txt" % cr.uniq("doc")
    uri = "cloudreve://my/" + name
    fid = cr.j(cr.upload(token, uri, b"content"))["data"]["id"]
    access = cr.viewer_session(token, uri)
    tampered = _forged_tokens(access)[kind]
    res = cr.wopi_check(fid, tampered)
    assert _refused(res), \
        "editor endpoint accepted a token with a forged secret (%s): %r" % (kind, res.get("code"))
    body = res.get("body") or b""
    assert name.encode() not in body, \
        "file metadata disclosed with a forged secret (%s)" % kind


def test_editor_forged_secret_cannot_overwrite_file():
    token = cr.ensure_admin()
    uri = "cloudreve://my/%s.txt" % cr.uniq("doc")
    fid = cr.j(cr.upload(token, uri, b"original-content"))["data"]["id"]
    access = cr.viewer_session(token, uri)
    tampered = _forged_tokens(access)["wrong-secret"]
    res = cr.wopi_put_file(fid, tampered, b"FORGED-OVERWRITE")
    # Read back through a freshly issued, legitimate session.
    fresh = cr.viewer_session(token, uri)
    got = cr.wopi_get_file(fid, fresh)
    assert got.get("code") == 200, "could not read the file back: %r" % got.get("code")
    assert got.get("body") == b"original-content", \
        "a write with a forged secret changed the file (status %r)" % res.get("code")
    assert _refused(res), "write with a forged secret was not refused: %r" % res.get("code")
