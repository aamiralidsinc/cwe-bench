"""Security tests: an author-controlled path in a prompt document must never
read a file outside the prompt's own directory.

Each test writes a secret file outside the prompt directory, marks it with a
random token, drives a real public entry point that follows the path the prompt
author wrote, and asserts the attack is blocked: the operation either raises a
client error (no file is read) or completes without the secret token reaching
any observable output. These assertions do not depend on a specific error type
or status; they only require that the out-of-directory read does not succeed.

On the pinned code the token leaks; a correct containment fix blocks it.
"""

import json
import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC_" + uuid.uuid4().hex


def _blob(agent) -> str:
    """Everything a loaded prompt might carry the leaked content in."""
    try:
        body = agent.to_json()
    except Exception:
        body = getattr(agent, "__dict__", agent)
    return json.dumps(body, default=str)


def _assert_blocked(token, call, capture=None):
    """A read outside the prompt directory must not succeed.

    Either the operation refuses (any exception == a clean client error with no
    read), or it completes without the secret token appearing in anything it
    returns or sends on to a downstream service.
    """
    try:
        result = call()
    except Exception:
        return  # refused before reading — acceptable
    parts = [str(result)]
    if capture is not None:
        parts.append(json.dumps(capture, default=str))
    assert token not in "\n".join(parts), "secret file content leaked into the result"


def _register_fake(capture: list) -> None:
    """Register a connection stand-in that records the request it receives."""

    class _Completions:
        @staticmethod
        def create(**kwargs):
            capture.append(kwargs)

            class _R:
                choices = []
                usage = None
                model = "test"
                output_text = "ok"

            return _R()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    import prompty

    prompty.register_connection("sec-fake", client=_Client())


# ---------------------------------------------------------------------------
# T1 — the reported reference expansion, every path spelling
# ---------------------------------------------------------------------------


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


def test_frontmatter_file_among_several(tmp_path: Path):
    """The path is one entry among several in a list of structured items."""
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.txt").write_text(token, encoding="utf-8")
    p = prompt_dir / "d.prompty"
    p.write_text(
        "---\n"
        "name: d\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "tools:\n"
        "  - name: ok\n"
        "    kind: function\n"
        "    description: plain\n"
        "  - name: leak\n"
        "    kind: function\n"
        '    description: "${file:../secret.txt}"\n'
        "---\n"
        "Hello\n",
        encoding="utf-8",
    )

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


# ---------------------------------------------------------------------------
# S1 / S2 / S3 — other parts of a document that name a file
# ---------------------------------------------------------------------------


def test_included_fragment_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.md").write_text(token, encoding="utf-8")
    p = prompt_dir / "e.prompty"
    p.write_text('---\nname: e\ndescription: "${prompt:../secret.md}"\n---\nHello\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_inherited_document_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.prompty").write_text(
        f'---\nname: secret\ndescription: "{token}"\n---\nSecretBody\n', encoding="utf-8"
    )
    p = prompt_dir / "f.prompty"
    p.write_text('---\nname: f\nbase: ../secret.prompty\n---\nChildBody\n', encoding="utf-8")

    def call():
        return _blob(prompty.load(p))

    _assert_blocked(token, call)


def test_template_snippet_traversal(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.md").write_text(token, encoding="utf-8")
    p = prompt_dir / "g.prompty"
    p.write_text(
        "---\n"
        "name: g\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: sec-fake\n"
        "---\n"
        "system:\n{% include \"../secret.md\" %}\n",
        encoding="utf-8",
    )
    capture: list = []
    _register_fake(capture)

    def call():
        agent = prompty.load(p)
        return prompty.render(agent, {})

    _assert_blocked(token, call, capture)


# ---------------------------------------------------------------------------
# T3 — a companion prompt named by a tool, followed on the prompt's behalf
# ---------------------------------------------------------------------------


def test_companion_prompt_on_request_build(tmp_path: Path):
    """Building the model request reads the companion prompt to project its
    interface; that read must stay inside the prompt's directory."""
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.prompty").write_text(
        f'---\nname: secret\ndescription: "{token}"\n'
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: sec-fake\n"
        "---\nSecretBody\n",
        encoding="utf-8",
    )
    p = prompt_dir / "h.prompty"
    p.write_text(
        "---\n"
        "name: h\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: sec-fake\n"
        "tools:\n"
        "  - name: leak\n"
        "    kind: prompty\n"
        "    path: ../secret.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )
    capture: list = []
    _register_fake(capture)

    def call():
        agent = prompty.load(p)
        messages = prompty.prepare(agent, {})
        return prompty.run(agent, messages)

    _assert_blocked(token, call, capture)


def test_companion_prompt_on_tool_dispatch(tmp_path: Path):
    """Running a companion-prompt tool loads the companion; that read must
    stay inside the prompt's directory."""
    import prompty
    from prompty.core.tool_dispatch import dispatch_tool

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (tmp_path / "secret.prompty").write_text(
        f'---\nname: secret\ndescription: "{token}"\n'
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: sec-fake\n"
        f"---\n{token} body\n",
        encoding="utf-8",
    )
    p = prompt_dir / "i.prompty"
    p.write_text(
        "---\n"
        "name: i\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: sec-fake\n"
        "tools:\n"
        "  - name: leak\n"
        "    kind: prompty\n"
        "    path: ../secret.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )
    capture: list = []
    _register_fake(capture)

    def call():
        agent = prompty.load(p)
        return dispatch_tool("leak", "{}", {}, agent, {})

    _assert_blocked(token, call, capture)
