"""Security: the file-tool component must not let an agent-chosen path or
command argument reach outside the configured workspace or an allowed-directory
restriction, for reads and writes, on both the filesystem-backed and the
state-backed variant.

Each test marks its target with a random token, drives the real operation through
the component's public tool (its own command dispatch), and asserts the attack is
blocked: no out-of-bounds content or name surfaces and no out-of-bounds file is
created or changed. Assertions do not depend on a specific error type or message.
"""

import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC" + uuid.uuid4().hex


def _runtime(state=None):
    from langchain.tools import ToolRuntime

    return ToolRuntime(
        state={} if state is None else state,
        context=None,
        config={},
        stream_writer=None,
        tool_call_id="tc-test",
        store=None,
    )


def _content(result) -> str:
    """Textual result of a tool call: a returned string or the message it emits."""
    try:
        return result.update["messages"][0].content
    except Exception:  # noqa: BLE001 - a plain string result
        return str(result)


def _call(mw, *, state=None, **kwargs):
    args = {k: v for k, v in kwargs.items() if v is not None}
    return mw.tools[0].func(_runtime(state), **args)


def _entry(lines):
    return {"content": lines, "created_at": "2020-01-01", "modified_at": "2020-01-01"}


def _make_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError:  # pragma: no cover - platform without symlink support
        pytest.skip("symlinks unavailable")


# ---------------------------------------------------------------------------
# Allowed-directory boundary: a sibling whose name shares the leading characters
# ---------------------------------------------------------------------------


def test_filesystem_sibling_prefix_read_escape(tmp_path: Path) -> None:
    """A restricted filesystem tool must not read a same-prefix sibling's file."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    sibling = root / "memories_extra"
    sibling.mkdir(parents=True)
    (sibling / "note.txt").write_text(token, encoding="utf-8")

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    result = _call(mw, command="view", path="/memories_extra/note.txt")
    assert token not in _content(result)


def test_filesystem_sibling_prefix_write_escape(tmp_path: Path) -> None:
    """A restricted filesystem tool must not create a file under a same-prefix
    sibling directory."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    (root / "memories_extra").mkdir(parents=True)

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    _call(
        mw,
        command="create",
        path=f"/memories_extra/{token}.txt",
        file_text=token,
    )
    assert not (root / "memories_extra" / f"{token}.txt").exists()


def test_state_sibling_prefix_read_escape() -> None:
    """The state-backed variant must not read a same-prefix sibling's entry."""
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    token = _token()
    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/ok.txt": _entry(["fine"]),
            "/memories_extra/secret.txt": _entry([token]),
        }
    }
    result = _call(mw, state=state, command="view", path="/memories_extra/secret.txt")
    assert token not in _content(result)


def test_state_sibling_prefix_write_escape() -> None:
    """The state-backed variant must not create an entry under a same-prefix
    sibling directory."""
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    token = _token()
    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {"memory_files": {"/memories/ok.txt": _entry(["fine"])}}
    result = _call(
        mw,
        state=state,
        command="create",
        path=f"/memories_extra/{token}.txt",
        file_text=token,
    )
    try:
        update = result.update or {}
    except Exception:  # noqa: BLE001 - a refused call may return a plain string
        update = {}
    created = update.get("memory_files") or {}
    assert all(not str(path).startswith("/memories_extra") for path in created)
    assert token not in str(update)


# ---------------------------------------------------------------------------
# Operations that act on a path after resolving it
# ---------------------------------------------------------------------------


def test_filesystem_list_symlinked_directory_escape(tmp_path: Path) -> None:
    """Listing an in-root link to an outside directory must not name its entries."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / f"{token}.txt").write_text("secret", encoding="utf-8")
    _make_link(root / "linked", outside)

    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    result = _call(mw, command="list", path="/linked")
    assert token not in _content(result)


def test_filesystem_copy_symlinked_source_escape(tmp_path: Path) -> None:
    """Copying an in-root link to an outside file must not bring its content in."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text(token, encoding="utf-8")
    _make_link(root / "alias.txt", outside)

    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    copied = _call(mw, command="copy", path="/alias.txt", new_path="/stolen.txt")
    assert token not in _content(copied)
    viewed = _call(mw, command="view", path="/stolen.txt")
    assert token not in _content(viewed)
    stolen = root / "stolen.txt"
    if stolen.exists():
        assert token not in stolen.read_text(encoding="utf-8")


def test_filesystem_append_symlinked_target_escape(tmp_path: Path) -> None:
    """Appending through an in-root link must not change the outside target."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("ORIGINAL\n", encoding="utf-8")
    _make_link(root / "alias.txt", outside)

    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    _call(mw, command="append", path="/alias.txt", file_text=token)
    assert token not in outside.read_text(encoding="utf-8")


def test_state_listing_sibling_entries_not_enumerated() -> None:
    """Listing an allowed directory must not enumerate a same-prefix sibling."""
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    token = _token()
    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/ok.txt": _entry(["fine"]),
            f"/memories_extra/{token}.txt": _entry(["secret"]),
        }
    }
    result = _call(mw, state=state, command="glob", path="/memories")
    text = _content(result)
    assert token not in text
    assert "/memories_extra/" not in text


# ---------------------------------------------------------------------------
# Allowed-directory boundary on operations that also touch a second path
# ---------------------------------------------------------------------------


def test_filesystem_copy_source_outside_allowed_dir(tmp_path: Path) -> None:
    """A restricted filesystem tool must not read a copy source that lies
    outside the allowed directories, whichever path the check is applied to."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    (root / "memories").mkdir(parents=True)
    sibling = root / "memories_extra"
    sibling.mkdir()
    (sibling / "secret.txt").write_text(token, encoding="utf-8")

    mw = FilesystemClaudeTextEditorMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    copied = _call(
        mw,
        command="copy",
        path="/memories_extra/secret.txt",
        new_path="/memories/stolen.txt",
    )
    assert token not in _content(copied)
    stolen = root / "memories" / "stolen.txt"
    if stolen.exists():
        assert token not in stolen.read_text(encoding="utf-8")


def test_filesystem_list_outside_allowed_dir(tmp_path: Path) -> None:
    """Listing a directory outside the allowed directories must not name its
    entries."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    (root / "memories").mkdir(parents=True)
    sibling = root / "memories_extra"
    sibling.mkdir()
    (sibling / f"{token}.txt").write_text("secret", encoding="utf-8")

    mw = FilesystemClaudeTextEditorMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    result = _call(mw, command="list", path="/memories_extra")
    assert token not in _content(result)


def test_filesystem_append_outside_allowed_dir(tmp_path: Path) -> None:
    """Appending to a file outside the allowed directories must not create or
    change it."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    (root / "memories").mkdir(parents=True)
    sibling = root / "memories_extra"
    sibling.mkdir()
    target = sibling / "note.txt"

    mw = FilesystemClaudeTextEditorMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    _call(mw, command="append", path="/memories_extra/note.txt", file_text=token)
    assert not target.exists() or token not in target.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Recursive name search: a link met during the walk
# ---------------------------------------------------------------------------


def test_filesystem_find_symlinked_directory_escape(tmp_path: Path) -> None:
    """A recursive name search must not descend through an in-root link to an
    outside directory and surface that directory's file names."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / f"{token}.txt").write_text("secret", encoding="utf-8")
    _make_link(root / "linked", outside)

    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    result = _call(mw, command="find", path="/", pattern="*.txt")
    assert token not in _content(result)


def test_filesystem_find_outside_allowed_dir(tmp_path: Path) -> None:
    """A recursive name search started at an allowed directory must not surface
    entries reached through a link that resolves outside the allowed
    directories."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    (root / "memories").mkdir(parents=True)
    (root / "memories" / "ok.txt").write_text("fine", encoding="utf-8")
    sibling = root / "memories_extra"
    sibling.mkdir()
    (sibling / f"{token}.txt").write_text("secret", encoding="utf-8")
    _make_link(root / "memories" / "linked", sibling)

    mw = FilesystemClaudeTextEditorMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    result = _call(mw, command="find", path="/memories", pattern="*.txt")
    assert token not in _content(result)
