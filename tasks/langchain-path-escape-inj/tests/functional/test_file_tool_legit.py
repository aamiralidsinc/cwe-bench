"""Functional: ordinary in-bounds file-tool operations must keep working, so an
over-broad containment fix (one that also rejects the allowed directory itself,
its descendants, or legitimate copies/listings) is caught.
"""

from pathlib import Path

from langchain.tools import ToolRuntime


def _runtime(state=None):
    return ToolRuntime(
        state=state,
        context=None,
        config={},
        stream_writer=None,
        tool_call_id="tc-test",
        store=None,
    )


def _content(result) -> str:
    try:
        return result.update["messages"][0].content
    except Exception:
        return str(result)


def _call(mw, *, state=None, **kwargs):
    args = {k: v for k, v in kwargs.items() if v is not None}
    return mw.tools[0].func(_runtime(state), **args)


def _entry(lines):
    return {"content": lines, "created_at": "2020-01-01", "modified_at": "2020-01-01"}


def test_filesystem_create_and_view_in_allowed_dir(tmp_path: Path):
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(tmp_path / "root"), allowed_prefixes=["/memories"]
    )
    _call(mw, command="create", path="/memories/note.txt", file_text="remember this")
    out = _content(_call(mw, command="view", path="/memories/note.txt"))
    assert "remember this" in out


def test_filesystem_nested_descendant_allowed(tmp_path: Path):
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(tmp_path / "root"), allowed_prefixes=["/memories"]
    )
    _call(mw, command="create", path="/memories/sub/deep.txt", file_text="nested ok")
    out = _content(_call(mw, command="view", path="/memories/sub/deep.txt"))
    assert "nested ok" in out


def test_state_view_in_allowed_dir():
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {"memory_files": {"/memories/ok.txt": _entry(["present"])}}
    out = _content(_call(mw, state=state, command="view", path="/memories/ok.txt"))
    assert "present" in out


def test_copy_in_workspace(tmp_path: Path):
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


def test_state_glob_lists_in_prefix():
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
    assert "/memories/a.txt" in out and "/memories/b.txt" in out
