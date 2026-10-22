"""Shared helpers for the reference-containment security tests.

Every test builds a throwaway prompt tree: one directory holding the
``.prompty`` document, and harmless marker files outside it.  The tests assert
that loading (or using) the document never opens one of those outside files.
"""

from __future__ import annotations

import builtins
import contextlib
from pathlib import Path

import pytest

OUTSIDE_MARKER = "PROMPTY-OUTSIDE-CONTENT-9f3a2c"


@contextlib.contextmanager
def opened_files():
    """Record the canonical path of every file opened inside the block."""
    seen: list[str] = []
    real_open = builtins.open

    def _record(file, *args, **kwargs):
        try:
            seen.append(str(Path(file).resolve()))
        except (TypeError, ValueError, OSError):
            seen.append(str(file))
        return real_open(file, *args, **kwargs)

    builtins.open = _record
    try:
        yield seen
    finally:
        builtins.open = real_open


def assert_never_opened(seen, *targets):
    resolved = {str(Path(t).resolve()) for t in targets}
    opened = resolved.intersection(seen)
    assert not opened, f"a file outside the prompt directory was opened: {sorted(opened)}"


class PromptTree:
    """A prompt directory plus marker files that must stay unread."""

    def __init__(self, root: Path):
        self.root = root
        self.prompts = root / "prompts"
        self.outside = root / "outside-content.txt"
        self.prefix_sibling = root / "prompts-extra" / "outside-content.txt"
        self.linked_dir_file = root / "linked-dir" / "outside-content.txt"
        self.outside_base = root / "outside-base.prompty"
        self.outside_child = root / "outside-child.prompty"

    def write(self, name: str, text: str) -> Path:
        target = self.prompts / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target


@pytest.fixture
def tree(tmp_path):
    root = tmp_path.resolve()
    prompts = root / "prompts"
    prompts.mkdir()

    outside = root / "outside-content.txt"
    outside.write_text(OUTSIDE_MARKER, encoding="utf-8")

    prefix_dir = root / "prompts-extra"
    prefix_dir.mkdir()
    (prefix_dir / "outside-content.txt").write_text(OUTSIDE_MARKER, encoding="utf-8")

    linked_dir = root / "linked-dir"
    linked_dir.mkdir()
    (linked_dir / "outside-content.txt").write_text(OUTSIDE_MARKER, encoding="utf-8")

    (root / "outside-base.prompty").write_text(
        f"---\nname: outside-base\ndescription: {OUTSIDE_MARKER}\n---\nbase body\n",
        encoding="utf-8",
    )
    (root / "outside-child.prompty").write_text(
        f"---\nname: outside-child\nmodel: gpt-4\ndescription: {OUTSIDE_MARKER}\n---\nchild body\n",
        encoding="utf-8",
    )

    (prompts / "escape-file.txt").symlink_to(outside)
    (prompts / "escape-dir").symlink_to(linked_dir, target_is_directory=True)

    return PromptTree(root)
