"""Drive copyparty's real HTTP request handler in-process.

The product's own test harness (tests/util.py) fakes only the socket; every request
below is parsed and dispatched by copyparty.httpcli.HttpCli exactly as a network
request would be.  Security tests build their expected capability values with the
product's public key function and the fixed test salts from tests/util.Cfg.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3

from copyparty.authsrv import AuthSrv
from copyparty.httpcli import HttpCli
from copyparty.util import absreal, gen_filekey
from tests import util as tu
from tests.util import Cfg

USERS = ["u1:u1", "u2:u2"]
DK_SALT = "b" * 16
FK_SALT = "a" * 16


def noop(src, msg, c=0):
    pass


def mkdirs(root: str, layout: dict) -> None:
    for rel, data in layout.items():
        ap = os.path.join(root, rel)
        d = os.path.dirname(ap)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(ap, "wb") as f:
            f.write(data)


def init_share_db(path: str) -> None:
    db = sqlite3.connect(path)
    with db:
        db.execute(
            r"create table sh (k text, pw text, vp text, pr text, st int, un text, t0 int, t1 int)"
        )
        db.execute(r"create table sf (k text, vp text)")
    db.close()


class Srv:
    def __init__(self, vcfg, up2k=False, **cfgkw):
        self.args = Cfg(v=vcfg, a=USERS, **cfgkw)
        self.asrv = AuthSrv(self.args, noop)
        self.conn = tu.VHttpConn(self.args, self.asrv, noop, b"", up2k)

    def reopen(self, up2k=False):
        self.close()
        self.__init__(self._vcfg, up2k, **self._cfgkw)
        return self

    def close(self):
        try:
            self.conn.shutdown()
        except Exception:
            pass


_TEMPLATE = None


def _template():
    global _TEMPLATE
    if _TEMPLATE is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "copyparty", "web", "browser.html")
        with open(p, "rb") as f:
            _TEMPLATE = tu.J2_ENV.from_string(f.read().decode("utf-8"))
    return _TEMPLATE


def server(cwd: str, vcfg, up2k=False, **cfgkw) -> Srv:
    os.chdir(cwd)
    s = Srv(vcfg, up2k, **cfgkw)
    s.conn.hsrv.j2["browser"] = _template()
    s._vcfg = vcfg
    s._cfgkw = cfgkw
    return s


def _reply(conn, raw: bytes):
    conn.setbuf(raw)
    HttpCli(conn).run()
    head, _, body = conn.s._reply.partition(b"\r\n\r\n")
    try:
        status = int(head.split(b" ", 2)[1])
    except Exception:
        status = 0
    return status, head, body


def request(conn, url: str, uname: str, extra: str = ""):
    raw = (
        "GET /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n%s\r\n"
        % (url, uname, extra)
    ).encode("utf-8")
    return _reply(conn, raw)


def request_body(conn, url: str, uname: str, body: bytes, ctype: str):
    raw = (
        "POST /%s HTTP/1.1\r\nPW: %s\r\nConnection: close\r\n"
        "Content-Type: %s\r\nContent-Length: %d\r\n\r\n"
        % (url, uname, ctype, len(body))
    ).encode("utf-8") + body
    return _reply(conn, raw)


def request_json(conn, url: str, uname: str, obj):
    body = json.dumps(obj).encode("utf-8")
    return request_body(conn, url, uname, body, "application/json")


def request_zip_sel(conn, url: str, uname: str, items, field: str = "zip"):
    zs = (
        '--XD\r\nContent-Disposition: form-data; name="act"\r\n\r\nzip\r\n'
        '--XD\r\nContent-Disposition: form-data; name="files"\r\n\r\n'
    )
    zs += "\r\n".join(items) + "\r\n--XD--\r\n"
    body = zs.encode("utf-8")
    return request_body(
        conn, url, uname, body, "multipart/form-data; boundary=XD"
    )


def parse_json(body: bytes):
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


def dirkey(path: str, n: int = 8) -> str:
    return gen_filekey(2, DK_SALT, absreal(path), 0, 0)[:n]


def filekey(path: str, alg: int = 1) -> str:
    st = os.stat(path)
    return gen_filekey(alg, FK_SALT, absreal(path), st.st_size, st.st_ino)[:8]


def dk_in(body: bytes, key: str) -> bool:
    return key.encode("ascii") in body


def create_share(conn, key: str, vps, perms):
    """Create a share through the product's share endpoint, then ignore its reply.

    The handler commits the row before asking the broker to reload; a test that needs
    the new share rebuilds AuthSrv (and the connection) from the same database.
    """
    obj = {"k": key, "vp": vps, "pw": "", "exp": "99", "perms": perms}
    return request_json(conn, "?share&pw=u1", "u1", obj)


def fresh_ramdisk():
    return tu.get_ramdisk()


def reset_ramdisk(path: str):
    shutil.rmtree(path, ignore_errors=True)
