"""Functional: ordinary searches inside the workspace must behave exactly as
before, so an over-broad containment fix is caught.
"""

from pathlib import Path

import pytest


def _middleware(root: Path, **kwargs):
    from langchain.agents.middleware.file_search import FilesystemFileSearchMiddleware

    return FilesystemFileSearchMiddleware(root_path=str(root), **kwargs)


def _make_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError:  # pragma: no cover - platform without symlink support
        pytest.skip("symlinks unavailable")


def test_glob_simple_pattern(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("y", encoding="utf-8")
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "*.py", "path": "/"})
    assert "/a.py" in out
    assert "b.txt" not in out


def test_glob_recursive_pattern(tmp_path: Path) -> None:
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "mod.py").write_text("x", encoding="utf-8")
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "**/*.py", "path": "/"})
    assert "/pkg/mod.py" in out


def test_glob_under_subdirectory_path(tmp_path: Path) -> None:
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "mod.py").write_text("x", encoding="utf-8")
    (tmp_path / "top.py").write_text("x", encoding="utf-8")
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "*.py", "path": "/pkg"})
    assert "/pkg/mod.py" in out
    assert "/top.py" not in out


def test_glob_filename_with_dotted_substring(tmp_path: Path) -> None:
    """A dotted version string in a name is not an upward segment and must match."""
    (tmp_path / "v1..2.py").write_text("x", encoding="utf-8")
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "*.py", "path": "/"})
    assert "v1..2.py" in out


def test_glob_in_workspace_link_kept(tmp_path: Path) -> None:
    """A link whose target is inside the workspace must still be enumerated."""
    target = tmp_path / "real.txt"
    target.write_text("data", encoding="utf-8")
    _make_link(tmp_path / "alias.txt", target)
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "*.txt", "path": "/"})
    assert "/alias.txt" in out


def test_glob_no_matches_contract(tmp_path: Path) -> None:
    out = _middleware(tmp_path).glob_search.invoke({"pattern": "*.nope", "path": "/"})
    assert out == "No files found"


def test_grep_content_python_backend(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("alpha NEEDLE omega", encoding="utf-8")
    out = _middleware(tmp_path, use_ripgrep=False).grep_search.invoke(
        {"pattern": "NEEDLE", "path": "/", "output_mode": "content"}
    )
    assert "NEEDLE" in out
    assert "/f.txt" in out


def test_grep_content_default_backend(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("alpha NEEDLE omega", encoding="utf-8")
    out = _middleware(tmp_path).grep_search.invoke(
        {"pattern": "NEEDLE", "path": "/", "output_mode": "content"}
    )
    assert "NEEDLE" in out
    assert "/f.txt" in out


def test_grep_python_backend_include_filter(tmp_path: Path) -> None:
    (tmp_path / "code.py").write_text("NEEDLE", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("NEEDLE", encoding="utf-8")
    out = _middleware(tmp_path, use_ripgrep=False).grep_search.invoke(
        {"pattern": "NEEDLE", "path": "/", "include": "*.py", "output_mode": "content"}
    )
    assert "/code.py" in out
    assert "notes.txt" not in out


def test_grep_in_workspace_link_kept(tmp_path: Path) -> None:
    target = tmp_path / "real.txt"
    target.write_text("has NEEDLE", encoding="utf-8")
    _make_link(tmp_path / "alias.txt", target)
    out = _middleware(tmp_path, use_ripgrep=False).grep_search.invoke(
        {"pattern": "NEEDLE", "path": "/", "output_mode": "files_with_matches"}
    )
    assert "/alias.txt" in out


def test_grep_default_backend_in_workspace_link_kept(tmp_path: Path) -> None:
    """A link whose target is inside the workspace must still be searched by the
    backend used by default."""
    target = tmp_path / "real.txt"
    target.write_text("has NEEDLE", encoding="utf-8")
    _make_link(tmp_path / "alias.txt", target)
    out = _middleware(tmp_path).grep_search.invoke(
        {"pattern": "NEEDLE", "path": "/", "output_mode": "files_with_matches"}
    )
    assert "/alias.txt" in out


def test_grep_no_matches_contract(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("nothing here", encoding="utf-8")
    out = _middleware(tmp_path, use_ripgrep=False).grep_search.invoke(
        {"pattern": "ABSENT", "path": "/", "output_mode": "content"}
    )
    assert out == "No matches found"
