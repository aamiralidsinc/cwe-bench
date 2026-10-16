"""Thin HTTP client for driving a running Cloudreve server over its real API,
exactly as a browser/WOPI-client/WebDAV-client would. Stdlib only."""
import json, os, socket, struct, zlib, urllib.request, urllib.error, urllib.parse, uuid

BASE = os.environ.get("CR_BASE", "http://127.0.0.1:5212/api/v4")
PW = "Passw0rd!"


def call(method, path, token=None, body=None, raw=None, headers=None, timeout=60):
    h = {}
    if body is not None:
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = "Bearer " + token
    if headers:
        h.update(headers)
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return {"code": resp.getcode(), "ct": resp.headers.get("Content-Type"),
                "body": resp.read(1 << 16),
                "wopi_invalid": resp.headers.get("X-WOPI-InvalidFileNameError")}
    except urllib.error.HTTPError as e:
        return {"code": e.code, "body": e.read(1 << 16), "ct": e.headers.get("Content-Type"),
                "wopi_invalid": e.headers.get("X-WOPI-InvalidFileNameError")}
    except socket.timeout:
        return {"timeout": True}
    except Exception as e:  # pragma: no cover
        return {"err": str(e)}


def j(resp):
    try:
        return json.loads(resp["body"])
    except Exception:
        return {}


def register(email, pw=PW):
    return call("POST", "/user", body={"email": email, "password": pw})


def login(email, pw=PW):
    r = call("POST", "/session/token", body={"email": email, "password": pw})
    return j(r)["data"]["token"]["access_token"]


def ensure_admin():
    """admin@cloudreve.test is registered first by test.sh, so it is user id 1
    (admin). Registration here is a harmless no-op if it already exists."""
    register("admin@cloudreve.test")
    return login("admin@cloudreve.test")


def upload(token, uri, data):
    return call("PUT", "/file/content?uri=" + urllib.parse.quote(uri), token=token, raw=data)


def mkfolder(token, uri):
    return call("POST", "/file/create", token=token, body={"uri": uri, "type": "folder"})


def listing(token, uri):
    r = j(call("GET", "/file?uri=" + urllib.parse.quote(uri), token=token))
    return [f["path"] for f in r.get("data", {}).get("files", [])]


def search(token, keyword):
    return j(call("GET", "/user/search?keyword=" + urllib.parse.quote(keyword), token=token)).get("data", [])


def thumb(token, uri):
    return j(call("GET", "/file/thumb?uri=" + urllib.parse.quote(uri), token=token))


def viewer_session(token, uri, viewer_id="monaco", action="edit"):
    # A precondition, not an assertion: retry a transient refusal (seen once in
    # an oracle run right after an upload) and report the response if it persists.
    import time
    r = {}
    for attempt in range(5):
        r = j(call("PUT", "/file/viewerSession", token=token,
                   body={"uri": uri, "viewer_id": viewer_id, "preferred_action": action}))
        tok = (((r.get("data") or {}).get("session") or {}).get("access_token"))
        if tok:
            return tok
        time.sleep(1)
    raise AssertionError("precondition: could not open an editor session: %r" % r)


def wopi_check(file_id, access_token):
    return call("GET", "/file/wopi/%s?access_token=%s" % (file_id, access_token))


def wopi_put_relative(file_id, access_token, suggested_target, data=b"x"):
    h = {"X-WOPI-Override": "PUT_RELATIVE", "X-WOPI-SuggestedTarget": suggested_target,
         "Content-Type": "application/octet-stream"}
    return call("POST", "/file/wopi/%s?access_token=%s" % (file_id, access_token), headers=h, raw=data)


def wopi_put_file(file_id, access_token, data):
    h = {"X-WOPI-Override": "PUT", "Content-Type": "application/octet-stream"}
    return call("POST", "/file/wopi/%s/contents?access_token=%s" % (file_id, access_token),
                headers=h, raw=data)


def wopi_get_file(file_id, access_token):
    return call("GET", "/file/wopi/%s/contents?access_token=%s" % (file_id, access_token))


def share(token, uri):
    return j(call("PUT", "/share", token=token, body={"uri": uri}))["data"]


def events(token, uri, timeout=4):
    return call("GET", "/file/events?uri=" + urllib.parse.quote(uri), token=token,
                headers={"X-Cr-Client-Id": str(uuid.uuid4())}, timeout=timeout)


def pixel_bomb_png(w, h):
    """Valid PNG declaring a WxH image whose pixel data is a run of zeros, so a
    tiny file decompresses to W*H*bytesPerPixel in memory (a decompression
    bomb). 9000x9000 = 81 MP."""
    def chunk(typ, dat):
        c = typ + dat
        return struct.pack(">I", len(dat)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    rows = (b"\x00" + b"\x00\x00\x00" * w) * h  # filter byte + RGB zeros per row
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 1))
            + chunk(b"IEND", b""))


def photo_like_png(w, h, seed=b"cr"):
    """Valid RGB PNG of WxH whose pixel data is pseudo-random sparse noise, so it
    compresses only moderately (roughly 15:1, like a real image) rather than as a
    run of zeros. Built row by row to keep the test process's memory small."""
    import hashlib
    table = bytes(0xD0 if b < 32 else 0x40 for b in range(256))
    comp = zlib.compressobj(6)
    out = []
    block = b""
    ctr = 0
    for _ in range(h):
        need = 3 * w
        while len(block) < need:
            block += hashlib.shake_256(seed + ctr.to_bytes(8, "big")).digest(1 << 16)
            ctr += 1
        row, block = block[:need], block[need:]
        out.append(comp.compress(b"\x00" + row.translate(table)))
    out.append(comp.flush())

    def chunk(typ, dat):
        c = typ + dat
        return struct.pack(">I", len(dat)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", b"".join(out))
            + chunk(b"IEND", b""))


def uniq(prefix="f"):
    return "%s_%s" % (prefix, uuid.uuid4().hex[:8])
