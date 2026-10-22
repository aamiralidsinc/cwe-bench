"""Security: the file-tool component must not let an agent-chosen path escape the
configured workspace or an allowed directory restriction.

Covered here, each through the public tool (the tool's own command dispatch):
  * a restricted (filesystem-backed) tool must not reach a sibling directory
    whose name merely shares the allowed directory's leading characters;
  * the state-backed variant must not either, for the same sibling shape;
  * a copy/move-style operation must not read a source that resolves outside the
    workspace via an in-workspace symlink;
  * a directory listing must not enumerate entries belonging to a sibling
    directory outside the restriction.

Each test marks a secret with a random token, drives the real operation, and
asserts the token (the out-of-bounds path or its content) never surfaces and no
out-of-bounds file is written. Assertions do not depend on a specific error.
"""

import uuid
from pathlib import Path

from langchain.tools import ToolRuntime


def _token() -> str:
    return "SEC" + uuid.uuid4().hex


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


def _call_tool(mw, *, state=None, **kwargs):
    """Invoke the component's public tool through its command dispatch."""
    tool = mw.tools[0]
    args = {k: v for k, v in kwargs.items() if v is not None}
    return tool.func(_runtime(state), **args)


def _file_entry(lines):
    return {"content": lines, "created_at": "2020-01-01", "modified_at": "2020-01-01"}


def test_filesystem_sibling_prefix_escape(tmp_path: Path):
    """A tool limited to /memories must not reach /memories<suffix>/... ."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeMemoryMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    sibling = root / "memories_sibling"
    sibling.mkdir(parents=True)
    (sibling / "note.txt").write_text(token, encoding="utf-8")

    mw = FilesystemClaudeMemoryMiddleware(
        root_path=str(root), allowed_prefixes=["/memories"]
    )
    result = _call_tool(mw, command="view", path="/memories_sibling/note.txt")
    assert token not in _content(result)


def test_state_sibling_prefix_escape():
    """The state-backed variant must not reach a same-prefix sibling either."""
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    token = _token()
    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/ok.txt": _file_entry(["fine"]),
            "/memories_sibling/secret.txt": _file_entry([token]),
        }
    }
    result = _call_tool(mw, state=state, command="view", path="/memories_sibling/secret.txt")
    assert token not in _content(result)


def test_copy_source_symlink_escape(tmp_path: Path):
    """A copy must not read a source that resolves outside the workspace."""
    from langchain_anthropic.middleware.anthropic_tools import (
        FilesystemClaudeTextEditorMiddleware,
    )

    token = _token()
    root = tmp_path / "root"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(token, encoding="utf-8")
    link = root / "link.txt"
    try:
        link.symlink_to(secret)
    except OSError:
        import pytest

        pytest.skip("symlinks unavailable")

    mw = FilesystemClaudeTextEditorMiddleware(root_path=str(root))
    copy_result = _call_tool(mw, command="copy", path="/link.txt", new_path="/stolen.txt")
    view_result = _call_tool(mw, command="view", path="/stolen.txt")

    assert token not in _content(copy_result)
    assert token not in _content(view_result)
    # No out-of-bounds content may have been written into the workspace.
    stolen = root / "stolen.txt"
    if stolen.exists():
        assert token not in stolen.read_text(encoding="utf-8")


def test_list_sibling_prefix_escape():
    """A directory listing must not enumerate a same-prefix sibling's entries."""
    from langchain_anthropic.middleware.anthropic_tools import (
        StateClaudeMemoryMiddleware,
    )

    token = _token()
    mw = StateClaudeMemoryMiddleware(allowed_path_prefixes=["/memories"])
    state = {
        "memory_files": {
            "/memories/ok.txt": _file_entry(["fine"]),
            f"/memories_sibling/{token}.txt": _file_entry(["x"]),
        }
    }
    result = _call_tool(mw, state=state, command="glob", path="/memories")
    assert token not in _content(result)
