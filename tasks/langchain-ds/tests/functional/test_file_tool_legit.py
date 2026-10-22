"""Functional: ordinary in-bounds file-tool operations must keep working, so an
over-broad containment fix (one that rejects the allowed directory itself, its
descendants, links that stay inside, or legitimate copies/listings/writes) is
caught.
"""

from pathlib import Path

import pytest


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


def test_filesystem_create_and_view_in_allowed_dir(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(tmp_path / "root"), allowed_prefixes=["/memories"]
    )
    _call(mw, command="create", path="/memories/note.txt", file_text="remember this")
    out = _content(_call(mw, command="view", path="/memories/note.txt"))
    assert "remember this" in out


def test_filesystem_nested_descendant_allowed(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(tmp_path / "root"), allowed_prefixes=["/memories"]
    )
    _call(mw, command="create", path="/memories/sub/deep.txt", file_text="nested ok")
    out = _content(_call(mw, command="view", path="/memories/sub/deep.txt"))
    assert "nested ok" in out


def test_filesystem_allowed_dir_itself_listed(tmp_path: Path) -> None:
    """The allowed directory itself is a permitted path and can be listed."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    root = tmp_path / "root"
    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    _call(mw, command="create", path="/memories/a.txt", file_text="1")
    _call(mw, command="create", path="/memories/b.txt", file_text="2")
    out = _content(_call(mw, command="list", path="/memories"))
    assert "a.txt" in out
    assert "b.txt" in out


def test_filesystem_copy_in_workspace(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    root.mkdir()
    (root / "src.txt").write_text("copy me", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    _call(mw, command="copy", path="/src.txt", new_path="/dst.txt")
    out = _content(_call(mw, command="view", path="/dst.txt"))
    assert "copy me" in out


def test_filesystem_list_in_workspace(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "one.txt").write_text("1", encoding="utf-8")
    (root / "sub" / "two.txt").write_text("2", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="list", path="/sub"))
    assert "one.txt" in out
    assert "two.txt" in out


def test_filesystem_append_in_workspace(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    root.mkdir()
    (root / "notes.txt").write_text("first\n", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    _call(mw, command="append", path="/notes.txt", file_text="second")
    out = _content(_call(mw, command="view", path="/notes.txt"))
    assert "first" in out
    assert "second" in out


def test_filesystem_find_in_workspace(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "one.txt").write_text("1", encoding="utf-8")
    (root / "two.txt").write_text("2", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="find", path="/", pattern="*.txt"))
    assert "/sub/one.txt" in out
    assert "/two.txt" in out


def test_filesystem_find_in_workspace_link_kept(tmp_path: Path) -> None:
    """A link whose target is inside the workspace must still be found."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    root.mkdir()
    target = root / "real.txt"
    target.write_text("inside data", encoding="utf-8")
    _make_link(root / "alias.txt", target)
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="find", path="/", pattern="*.txt"))
    assert "/alias.txt" in out
    assert "/real.txt" in out


def test_filesystem_find_in_workspace_directory_link_kept(tmp_path: Path) -> None:
    """A link to a directory inside the workspace must still be searched."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    real = root / "realdir"
    real.mkdir(parents=True)
    (real / "inside.txt").write_text("x", encoding="utf-8")
    _make_link(root / "linked", real)
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="find", path="/", pattern="*.txt"))
    assert "/linked/inside.txt" in out
    assert "/realdir/inside.txt" in out


def test_filesystem_find_allowed_dir_nested(tmp_path: Path) -> None:
    """Recursive name search must keep working on an allowed directory and its
    descendants."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    (root / "memories" / "sub").mkdir(parents=True)
    (root / "memories" / "sub" / "deep.txt").write_text("3", encoding="utf-8")
    (root / "memories" / "top.txt").write_text("4", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    out = _content(_call(mw, command="find", path="/memories", pattern="*.txt"))
    assert "/memories/sub/deep.txt" in out
    assert "/memories/top.txt" in out


def test_filesystem_find_no_matches_contract(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    root.mkdir()
    (root / "present.txt").write_text("x", encoding="utf-8")
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="find", path="/", pattern="*.nope"))
    assert out == "No files found"


def test_filesystem_link_inside_workspace_still_readable(tmp_path: Path) -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    root = tmp_path / "root"
    root.mkdir()
    target = root / "real.txt"
    target.write_text("inside data", encoding="utf-8")
    _make_link(root / "alias.txt", target)
    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    out = _content(_call(mw, command="view", path="/alias.txt"))
    assert "inside data" in out


def test_state_view_in_allowed_dir() -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {"memory_files": {"/memories/ok.txt": _entry(["present"])}}
    out = _content(_call(mw, state=state, command="view", path="/memories/ok.txt"))
    assert "present" in out


def test_state_create_in_allowed_dir() -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {"memory_files": {}}
    result = _call(
        mw, state=state, command="create", path="/memories/new.txt", file_text="kept"
    )
    update = result.update or {}
    assert "/memories/new.txt" in update.get("memory_files", {})


def test_state_allowed_dir_itself_listed() -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/a.txt": _entry(["1"]),
            "/memories/b.txt": _entry(["2"]),
            "/memories/sub/c.txt": _entry(["3"]),
        }
    }
    out = _content(_call(mw, state=state, command="view", path="/memories"))
    assert "/memories/a.txt" in out
    assert "/memories/b.txt" in out


def test_state_listing_in_prefix() -> None:
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/a.txt": _entry(["1"]),
            "/memories/b.txt": _entry(["2"]),
        }
    }
    out = _content(_call(mw, state=state, command="glob", path="/memories"))
    assert "/memories/a.txt" in out
    assert "/memories/b.txt" in out
