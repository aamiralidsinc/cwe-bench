"""Security: the file-search tools must not let an agent-chosen glob pattern or
regex search reach a file outside the configured workspace directory.

Each test puts a uniquely-marked secret file outside the workspace, drives a
real search through the public tool, and asserts the attack is blocked: the tool
either finds nothing / errors, or returns a result that neither names nor
contains the out-of-workspace target. These checks never depend on a specific
error type or message.

On the pinned code the pattern/symlink escapes leak; a correct containment fix
blocks them while leaving in-workspace searches unchanged.
"""

import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC" + uuid.uuid4().hex


def _assert_blocked(needle: str, call):
    """An out-of-workspace result must not succeed.

    Either the tool refuses (any exception == a clean client error), or it
    returns a value that does not surface the out-of-workspace path/content.
    """
    try:
        result = call()
    except Exception:
        return
    assert needle not in str(result), "out-of-workspace target surfaced in result"


def test_glob_pattern_upward_traversal(tmp_path: Path):
    """A glob pattern that walks upward must not enumerate files above root."""
    from langchain.agents.middleware.file_search import FilesystemFileSearchMiddleware

    token = _token()
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "inside.txt").write_text("hello", encoding="utf-8")
    (tmp_path / f"{token}.txt").write_text("secret", encoding="utf-8")

    mw = FilesystemFileSearchMiddleware(root_path=str(ws))

    def call():
        return mw.glob_search.invoke({"pattern": f"../{token}.txt", "path": "/"})

    _assert_blocked(token, call)


def test_glob_symlink_file_escape(tmp_path: Path):
    """A glob match that is an in-workspace symlink pointing out must be dropped."""
    from langchain.agents.middleware.file_search import FilesystemFileSearchMiddleware

    token = _token()
    ws = tmp_path / "workspace"
    ws.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(token, encoding="utf-8")
    link = ws / f"{token}.txt"
    try:
        link.symlink_to(secret)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    mw = FilesystemFileSearchMiddleware(root_path=str(ws))

    def call():
        return mw.glob_search.invoke({"pattern": "*.txt", "path": "/"})

    _assert_blocked(token, call)


def test_grep_symlink_file_content_escape(tmp_path: Path):
    """A content search must not read through an in-workspace symlink to outside."""
    from langchain.agents.middleware.file_search import FilesystemFileSearchMiddleware

    token = _token()
    ws = tmp_path / "workspace"
    ws.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(f"marker {token} here", encoding="utf-8")
    link = ws / "notes.txt"
    try:
        link.symlink_to(secret)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")

    mw = FilesystemFileSearchMiddleware(root_path=str(ws), use_ripgrep=False)

    def call():
        return mw.grep_search.invoke(
            {"pattern": token, "path": "/", "output_mode": "content"}
        )

    _assert_blocked(token, call)
