"""Shared helpers for the hidden suites.

Every suite drives the product the way a client does: through the documented
Python API and through the tool functions the MCP server registers.  Only the
external Stata executable is replaced, by fake_stata.py, which records what the
product sends to the session.  No product code is stubbed.
"""
import os
import shutil
import tempfile
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ROOT = Path(tempfile.mkdtemp(prefix="stata-mcp-suite-"))
HOME = ROOT / "home"
WORK = ROOT / "work"
BIN = ROOT / "bin"
CAPTURE = ROOT / "stata-session.log"
CONFIG = HOME / ".statamcp" / "config.toml"
CLI = BIN / "stata"
CHUNK = "@@STATA_CHUNK:"
END = "@@STATA_END@@"


def _bootstrap():
    HOME.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    BIN.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_HERE / "fake_stata.py", CLI)
    CLI.chmod(0o755)
    (HOME / ".statamcp").mkdir(parents=True, exist_ok=True)
    CONFIG.write_text('[STATA]\nSTATA_CLI = "%s"\n' % CLI.as_posix(), encoding="utf-8")
    os.environ["HOME"] = str(HOME)
    os.environ["STATA_MCP__CWD"] = str(WORK)
    os.environ["STATA_MCP_TEST_CAPTURE"] = str(CAPTURE)


_bootstrap()


# ----------------------------------------------------------------- helpers

def marker():
    """A fresh token so two tests can never collide in a cache or a file name."""
    return "STATA_MCP_" + uuid.uuid4().hex[:12].upper()


def command(token):
    """The harmless Stata command an injected value would run."""
    return 'display "%s"' % token


def new_dofile(name=None, content="display 1\n"):
    name = name or ("run_%s.do" % uuid.uuid4().hex[:8])
    path = WORK / name
    if path.parent != WORK:
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def reset_capture():
    try:
        CAPTURE.unlink()
    except FileNotFoundError:
        pass


def clean_state():
    """Drop cached help output so a later lookup cannot answer from disk."""
    for directory in (HOME / ".statamcp" / "help", WORK / ".statamcp" / "stata-mcp-tmp"):
        if directory.is_dir():
            for path in directory.iterdir():
                if path.is_file():
                    try:
                        path.unlink()
                    except OSError:
                        pass


def chunks():
    if not CAPTURE.exists():
        return []
    out, kind, body = [], None, []
    for line in CAPTURE.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(CHUNK):
            kind, body = line[len(CHUNK):].split("@@", 1)[0], []
        elif line == END:
            if kind is not None:
                out.append((kind, "\n".join(body)))
            kind = None
        elif kind is not None:
            body.append(line)
    return out


def lines():
    """Every command line the product sent to the Stata session."""
    out = []
    for _kind, body in chunks():
        for line in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            stripped = line.strip()
            if stripped:
                out.append(stripped)
    return out


def injected(token):
    """Command lines that are the caller value rather than something the tool issued."""
    return [line for line in lines() if line.startswith("display") and token in line]


def assert_no_injected_command(token):
    bad = injected(token)
    assert not bad, "a caller value reached Stata as a command line: %r" % (bad,)
