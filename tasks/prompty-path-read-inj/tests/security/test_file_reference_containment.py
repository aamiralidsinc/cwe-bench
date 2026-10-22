"""Security tests: an author-controlled path reference in a prompt definition
must never read a file outside the prompt's own directory.

Each test writes a secret file outside the prompt directory, marks it with a
random token, drives a real public load of a prompt that references it, and
asserts the attack is blocked: loading either raises a client error (no file is
read) or returns a benign result — but the secret token never reaches the
loaded definition. These assertions do not depend on a specific error type or
status; they only require that the out-of-directory read does not succeed.

On the pinned code the token leaks; a correct containment fix blocks it.
"""

import os
import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC_" + uuid.uuid4().hex


def _blob(agent) -> str:
    """Everything a loaded prompt might carry the leaked content in."""
    parts = [
        getattr(agent, "description", None),
        getattr(agent, "instructions", None),
        repr(getattr(agent, "inputs", None)),
        repr(getattr(agent, "metadata", None)),
        repr(getattr(agent, "model", None)),
        repr(getattr(agent, "sample", None)),
    ]
    return "\n".join(str(p) for p in parts)


def _assert_blocked(token, call):
    """A read outside the prompt directory must not succeed.

    Either the loader refuses (any exception == a clean client error with no
    read), or it returns something that does not contain the secret token.
    """
    try:
        result = call()
    except Exception:
        return  # refused before reading — acceptable
    assert token not in str(result), "secret file content leaked into the result"


def test_frontmatter_file_relative_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.txt").write_text(token, encoding="utf-8")
    p = prompt_dir / "a.prompty"
    p.write_text('---\nname: a\ndescription: "${file:../secret.txt}"\n---\nHello\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_frontmatter_file_absolute_path(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(token, encoding="utf-8")
    p = prompt_dir / "b.prompty"
    p.write_text(
        f'---\nname: b\ndescription: "${{file:{secret.as_posix()}}}"\n---\nHello\n',
        encoding="utf-8",
    )

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_frontmatter_file_symlink_escape(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(token, encoding="utf-8")
    link = prompt_dir / "link.txt"
    try:
        link.symlink_to(secret)
    except OSError as exc:
        pytest.skip(f"symlinks unavailable: {exc}")
    p = prompt_dir / "c.prompty"
    p.write_text('---\nname: c\ndescription: "${file:link.txt}"\n---\nHello\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_frontmatter_prompt_fragment_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.md").write_text(token, encoding="utf-8")
    p = prompt_dir / "d.prompty"
    p.write_text('---\nname: d\ndescription: "${prompt:../secret.md}"\n---\nHello\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_base_template_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "base.prompty").write_text(
        f'---\nname: base\ndescription: "{token}"\n---\nBaseBody\n', encoding="utf-8"
    )
    p = prompt_dir / "e.prompty"
    p.write_text('---\nname: e\nbase: ../base.prompty\n---\nChildBody\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_prompty_tool_child_path_traversal(tmp_path: Path):
    import prompty
    from prompty.providers.openai.executor import _project_prompty_tool

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.prompty").write_text(
        f'---\nname: s\ndescription: "{token}"\n---\nbody\n', encoding="utf-8"
    )
    parent = prompt_dir / "p.prompty"
    parent.write_text(
        "---\n"
        "name: p\n"
        "model:\n  id: gpt-4\n  apiType: chat\n"
        "tools:\n"
        "  - name: leak\n"
        "    kind: prompty\n"
        "    path: ../secret.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )
    def call():
        agent = prompty.load(parent)
        return repr(_project_prompty_tool(agent.tools[0], agent))

    _assert_blocked(token, call)
