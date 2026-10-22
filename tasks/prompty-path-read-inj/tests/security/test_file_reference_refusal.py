"""Security tests: an escaping reference is refused with a client error *before*
the target outside the prompt directory is opened or read.

``test_file_reference_containment.py`` only requires that the secret never
reaches the loaded object, so a fix that silently drops an escaping reference,
or that reads the target and then raises, would pass it.  These tests tighten
the same invariants:

* loading raises (a silent no-op is not a client error), and
* no open/read of the out-of-directory target happens before that error.

The checks are behavioural: they drive the real public loader (and, for a
prompt-kind tool, the handler's own path resolution followed by the real load
of the resolved child).  They do not depend on the exception type or message.

On the pinned code the target is opened and no error is raised, so every test
here fails; a correct containment fix refuses before the read.
"""

import builtins
import io
import os
import uuid
from pathlib import Path

import pytest


def _token() -> str:
    return "SEC_" + uuid.uuid4().hex


class _OpenRecorder:
    """Record attempts to open one watched path through the reading APIs."""

    def __init__(self, watched: Path):
        self.watched = str(Path(watched).resolve())
        self.opened: list[str] = []
        self._saved: dict[object, object] = {}

    def _record(self, file):
        try:
            if str(Path(os.fspath(file)).resolve()) == self.watched:
                self.opened.append(str(file))
        except (TypeError, ValueError, OSError):
            pass

    def __enter__(self):
        def wrap(fn):
            def wrapper(file, *args, **kwargs):
                self._record(file)
                return fn(file, *args, **kwargs)

            return wrapper

        self._saved = {builtins: builtins.open, io: io.open, os: os.open}
        builtins.open = wrap(self._saved[builtins])
        io.open = wrap(self._saved[io])
        os.open = wrap(self._saved[os])
        return self

    def __exit__(self, *exc_info):
        builtins.open = self._saved[builtins]
        io.open = self._saved[io]
        os.open = self._saved[os]
        return False


def _assert_refused_without_reading(call, watched: Path):
    """The call must raise a client error and never open *watched*."""
    with _OpenRecorder(watched) as recorder:
        try:
            result = call()
        except Exception:
            raised = True
        else:
            raised = False
    assert raised, f"escaping reference was not refused; got {result!r}"
    assert not recorder.opened, f"escaping target was opened/read: {recorder.opened}"


def test_frontmatter_file_relative_traversal_raises_without_reading(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text(token, encoding="utf-8")
    p = prompt_dir / "a.prompty"
    p.write_text('---\nname: a\ndescription: "${file:../secret.txt}"\n---\nHello\n', encoding="utf-8")

    _assert_refused_without_reading(lambda: prompty.load(p), secret)


def test_frontmatter_file_absolute_path_raises_without_reading(tmp_path: Path):
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

    _assert_refused_without_reading(lambda: prompty.load(p), secret)


def test_frontmatter_file_symlink_escape_raises_without_reading(tmp_path: Path):
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

    _assert_refused_without_reading(lambda: prompty.load(p), secret)


def test_frontmatter_prompt_fragment_traversal_raises_without_reading(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.md"
    secret.write_text(token, encoding="utf-8")
    p = prompt_dir / "d.prompty"
    p.write_text('---\nname: d\ndescription: "${prompt:../secret.md}"\n---\nHello\n', encoding="utf-8")

    _assert_refused_without_reading(lambda: prompty.load(p), secret)


def test_base_template_traversal_raises_without_reading(tmp_path: Path):
    import prompty

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "base.prompty"
    secret.write_text(
        f'---\nname: base\ndescription: "{token}"\n---\nBaseBody\n', encoding="utf-8"
    )
    p = prompt_dir / "e.prompty"
    p.write_text('---\nname: e\nbase: ../base.prompty\n---\nChildBody\n', encoding="utf-8")

    _assert_refused_without_reading(lambda: prompty.load(p), secret)


def test_prompty_tool_child_path_traversal_raises_without_reading(tmp_path: Path):
    import prompty
    from prompty.providers.openai.executor import _project_prompty_tool

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.prompty"
    secret.write_text(f'---\nname: s\ndescription: "{token}"\n---\nbody\n', encoding="utf-8")
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
        return _project_prompty_tool(agent.tools[0], agent)

    _assert_refused_without_reading(call, secret)


def test_prompty_tool_child_path_traversal_via_dispatch_never_loads(
    tmp_path: Path, monkeypatch
):
    """Public tool dispatch must never hand an escaping child path to the loader."""
    import prompty
    import prompty.core.loader as loader_module
    from prompty.core.tool_dispatch import dispatch_tool

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.prompty"
    secret.write_text(f'---\nname: s\ndescription: "{token}"\n---\nbody\n', encoding="utf-8")
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

    loaded: list[str] = []
    real_load = loader_module.load

    def spy_load(path):
        loaded.append(str(path))
        return real_load(path)

    monkeypatch.setattr(loader_module, "load", spy_load)
    try:
        agent = prompty.load(parent)
        dispatch_tool("leak", "{}", user_tools={}, agent=agent, parent_inputs={})
    except Exception:
        pass  # an eager load-time refusal is acceptable too

    assert not loaded, f"dispatch loaded an out-of-directory child: {loaded}"


def test_prompty_tool_child_path_traversal_through_dispatch_raises_without_reading(
    tmp_path: Path,
):
    """The execution route must confine the child path too, not only wire projection."""
    import prompty
    from prompty.core.tool_dispatch import PromptyToolHandler

    token = _token()
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    secret = tmp_path / "secret.prompty"
    secret.write_text(f'---\nname: s\ndescription: "{token}"\n---\nbody\n', encoding="utf-8")
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
        child_path = PromptyToolHandler()._resolve_child_path(agent.tools[0], agent)
        return prompty.load(child_path)

    _assert_refused_without_reading(call, secret)
