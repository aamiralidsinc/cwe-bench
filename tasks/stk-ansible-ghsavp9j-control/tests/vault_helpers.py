"""Helpers for the hidden suites. They drive the product's public vault API to build fixtures
and hand the suites the paths they need; no expected value is computed with product internals."""
import os
import tempfile

from ansible.module_utils._text import to_bytes
from ansible.parsing import vault as vault_module
from ansible.parsing.vault import VaultEditor, VaultLib, VaultSecret

SECRET_TEXT = "test-vault-password"
PLAINTEXT = b"database_password: swordfish\n"


class TextSecret(VaultSecret):
    def __init__(self, text):
        super(TextSecret, self).__init__()
        self._bytes = to_bytes(text)

    @property
    def bytes(self):
        return self._bytes


def secret():
    return TextSecret(SECRET_TEXT)


def vault_editor():
    return VaultEditor(VaultLib([("default", secret())]))


def make_vault_file(directory, plaintext=PLAINTEXT, name="secrets.yml"):
    """Create an encrypted file in `directory` and return its path."""
    path = os.path.join(directory, name)
    with open(path, "wb") as handle:
        handle.write(plaintext)
    vault_editor().encrypt_file(path, secret())
    return path


def plaintext_files(marker=PLAINTEXT):
    """Return files under the usual temporary locations that still contain the marker.

    This is independent of how the product created the file, so a correct fix that uses a
    different temporary-file API is still accepted.
    """
    roots = [(tempfile.gettempdir(), 3), (os.path.expanduser("~/.ansible"), 6)]
    found = []
    for root, max_depth in roots:
        if not os.path.isdir(root):
            continue
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base_depth >= max_depth:
                dirnames[:] = []
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    if os.path.islink(path) or not os.path.isfile(path) or os.path.getsize(path) > 10 * 1024 * 1024:
                        continue
                    with open(path, "rb") as handle:
                        data = handle.read(1024 * 1024)
                except OSError:
                    continue
                if marker in data:
                    found.append(path)
    return found


def editor_writing(monkeypatch, content, after=None):
    """Install a stand-in editor that writes `content` to the working copy."""

    def fake_call(command):
        with open(command[-1], "wb") as handle:
            handle.write(to_bytes(content))
        if after is not None:
            after(command[-1])
        return 0

    monkeypatch.setattr(vault_module.subprocess, "call", fake_call)


def editor_doing_nothing(monkeypatch, during=None):
    """Install a stand-in editor that leaves the working copy untouched."""

    def fake_call(command):
        if during is not None:
            during(command[-1])
        return 0

    monkeypatch.setattr(vault_module.subprocess, "call", fake_call)
