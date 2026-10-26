"""Drive the product's scanner modules directly, offline and with the real event objects.

The suites import the product from /workspace (the restored submission).  These helpers only
build a real Scanner, construct the real module classes and feed them real events; every piece
of behaviour under test is the product's own code.
"""
import asyncio
import importlib
import os
import tempfile
from pathlib import Path

# Keep the product offline and out of the repository while the suites run.
os.environ.setdefault("BBOT_TESTING", "True")
os.environ.setdefault("BBOT_CONFIG_DIR", tempfile.mkdtemp(prefix="bbot-config-"))

from bbot.scanner import Scanner  # noqa: E402


class FakeResponse:
    """Minimal stand-in for a remote service response (status + JSON body)."""

    def __init__(self, payload=None, status_code=200, headers=None, content=b"", url=""):
        self._payload = payload if payload is not None else {}
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.url = url

    def json(self):
        return self._payload


def new_scan(modules=(), module_config=None):
    """A real Scanner, constructed but not started (no dependency installation, no network)."""
    return Scanner(
        "127.0.0.1",
        modules=list(modules),
        output_modules=["python"],
        config=dict(module_config or {}),
    )


def load_module(dotted_path, name, scan):
    module = importlib.import_module(dotted_path)
    instance = getattr(module, name)(scan)
    instance._name = name
    return instance


def run(coro):
    return asyncio.run(coro)


def make_event(scan, data, event_type, tags=()):
    return scan.make_event(data, event_type, parent=scan.root_event, tags=list(tags))


def snapshot(root):
    return {str(p) for p in Path(root).rglob("*")}


def created_since(root, before):
    return sorted(snapshot(root) - set(before))


def is_under(path, directory):
    try:
        return Path(path).is_relative_to(Path(directory))
    except (OSError, ValueError):
        return False
