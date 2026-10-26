"""Fixtures shared by the hidden suites.

Every helper drives the library's public save operation through a real Flask application and
configuration. Payloads are ordinary in-memory file submissions; the tests compute their own
expected names and inspect the filesystem themselves.
"""
import io
from pathlib import Path

from flask import Flask
from flask_uploads import configure_uploads
from flask_uploads import UploadSet
from werkzeug.datastructures import FileStorage


def make_set(tmp_path, extensions, allow=(), deny=(), create_destination=False):
    """Configure one upload set named ``files`` and return (app, set, destination)."""
    app = Flask("hidden-suite")
    destination = Path(tmp_path) / "uploads"
    if create_destination:
        destination.mkdir(parents=True, exist_ok=True)
    app.config["UPLOADED_FILES_DEST"] = str(destination)
    if allow:
        app.config["UPLOADED_FILES_ALLOW"] = tuple(allow)
    if deny:
        app.config["UPLOADED_FILES_DENY"] = tuple(deny)
    uset = UploadSet("files", extensions)
    configure_uploads(app, uset)
    return app, uset, destination


def upload(filename, data=b"harmless"):
    """An ordinary submitted file, created without touching the product code."""
    return FileStorage(stream=io.BytesIO(data), filename=filename)


def files_under(root):
    """Every regular file below ``root`` (empty when the directory was never created)."""
    root = Path(root)
    if not root.exists():
        return []
    return sorted(str(p) for p in root.rglob("*") if p.is_file())
