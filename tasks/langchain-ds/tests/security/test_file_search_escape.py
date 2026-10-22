"""Security: the file-search tools must not let an agent-chosen pattern or regex
search reach a file outside the configured workspace directory.

Each test places a uniquely-marked file outside the workspace, drives a real
search through the public tool, and asserts the attack is blocked: the tool
either refuses (any exception is a clean client error) or returns a result that
neither names nor contains the out-of-workspace target. No test depends on one
particular error type, message or status.
"""

import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC" + uuid.uuid4().hex


def _middleware(root: Path, **kwargs):
    from langchain.agents.middleware.file_search import FilesystemFileSearchMiddleware

    return FilesystemFileSearchMiddleware(root_path=str(root), **kwargs)


def _assert_blocked(needle: str, call) -> None:
    """The out-of-workspace target must not surface in a search result."""
    try:
        result = call()
    except Exception:  # noqa: BLE001 - any raised error is a refusal
        return
    assert needle not in str(result), "out-of-workspace target surfaced in result"


def _make_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError:  # pragma: no cover - platform without symlink support
        pytest.skip("symlinks unavailable")


def test_glob_pattern_walks_up_from_root(tmp_path: Path) -> None:
    """A pattern that walks upward must not enumerate files above the root."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "inside.txt").write_text("hello", encoding="utf-8")
    (tmp_path / f"{token}.txt").write_text("secret", encoding="utf-8")

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.glob_search.invoke({"pattern": "../*.txt", "path": "/"}),
    )


def test_glob_pattern_walks_up_mid_pattern(tmp_path: Path) -> None:
    """An upward segment after a normal leading component is still an escape."""
    token = _token()
    root = tmp_path / "root"
    workspace = root / "workspace"
    (workspace / "sub").mkdir(parents=True)
    (root / f"{token}.txt").write_text("secret", encoding="utf-8")

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.glob_search.invoke(
            {"pattern": "sub/../../*.txt", "path": "/"}
        ),
    )


def test_glob_symlink_file_match_is_dropped(tmp_path: Path) -> None:
    """A glob match that is an in-root link to an outside file must be dropped."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / f"{token}.txt"
    outside.write_text("secret", encoding="utf-8")
    _make_link(workspace / f"{token}.link", outside)

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.glob_search.invoke({"pattern": "*.link", "path": "/"}),
    )


def test_glob_symlinked_directory_component_is_not_expanded(tmp_path: Path) -> None:
    """A pattern component that is an in-root link to an outside directory must
    not enumerate that directory's entries."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / f"{token}.txt").write_text("secret", encoding="utf-8")
    _make_link(workspace / "linked", outside_dir)

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.glob_search.invoke({"pattern": "linked/*", "path": "/"}),
    )


def test_grep_python_backend_does_not_read_through_link(tmp_path: Path) -> None:
    """The content-search implementation must not read a file reached through an
    in-root link to an outside target."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text(f"marker {token} here", encoding="utf-8")
    _make_link(workspace / "notes.txt", outside)

    mw = _middleware(workspace, use_ripgrep=False)
    _assert_blocked(
        token,
        lambda: mw.grep_search.invoke(
            {"pattern": "SEC[0-9a-f]{8,}", "path": "/", "output_mode": "content"}
        ),
    )


def test_grep_python_backend_link_with_include_filter(tmp_path: Path) -> None:
    """The same containment holds when an include filter is supplied."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text(token, encoding="utf-8")
    _make_link(workspace / "notes.txt", outside)

    mw = _middleware(workspace, use_ripgrep=False)
    _assert_blocked(
        token,
        lambda: mw.grep_search.invoke(
            {
                "pattern": "SEC[0-9a-f]{8,}",
                "path": "/",
                "include": "*.txt",
                "output_mode": "content",
            }
        ),
    )


def test_grep_default_backend_does_not_read_through_link(tmp_path: Path) -> None:
    """The content-search implementation used by default must not read a file
    reached through an in-root link to an outside target."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text(f"marker {token} here", encoding="utf-8")
    _make_link(workspace / "notes.txt", outside)

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.grep_search.invoke(
            {"pattern": "SEC[0-9a-f]{8,}", "path": "/", "output_mode": "content"}
        ),
    )


def test_grep_default_backend_does_not_follow_linked_directory(tmp_path: Path) -> None:
    """The default backend must not descend into an in-root link to an outside
    directory and surface its entries."""
    token = _token()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "notes.txt").write_text(f"marker {token} here", encoding="utf-8")
    _make_link(workspace / "linked", outside_dir)

    mw = _middleware(workspace)
    _assert_blocked(
        token,
        lambda: mw.grep_search.invoke(
            {"pattern": "SEC[0-9a-f]{8,}", "path": "/", "output_mode": "content"}
        ),
    )
