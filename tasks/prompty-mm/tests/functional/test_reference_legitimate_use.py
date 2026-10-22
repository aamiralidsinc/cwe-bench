"""Functional tests: legitimate reference resolution inside the prompt
directory keeps working exactly as before, and structured references still
return structured data.
"""

import json
from pathlib import Path


def test_file_reference_in_prompt_dir_returns_structured_data(tmp_path: Path):
    """A structured reference inside the prompt directory is parsed and
    injected as structured data (not a plain string)."""
    import prompty

    (tmp_path / "shared_connection.json").write_text(
        json.dumps({"kind": "key", "endpoint": "https://shared.example/", "apiKey": "shared-key"}),
        encoding="utf-8",
    )
    p = tmp_path / "a.prompty"
    p.write_text(
        "---\n"
        "name: a\n"
        "model:\n  id: gpt-4\n  apiType: chat\n  connection: ${file:shared_connection.json}\n"
        "---\n"
        "Hello\n",
        encoding="utf-8",
    )
    agent = prompty.load(p)
    conn = agent.model.connection
    assert conn is not None
    assert getattr(conn, "kind", None) == "key"
    assert getattr(conn, "endpoint", None) == "https://shared.example/"


def test_file_reference_in_subdirectory_works(tmp_path: Path):
    """A reference into a sub-directory of the prompt directory is allowed."""
    import prompty

    sub = tmp_path / "frags"
    sub.mkdir()
    (sub / "desc.txt").write_text("subdir description", encoding="utf-8")
    p = tmp_path / "b.prompty"
    p.write_text('---\nname: b\ndescription: "${file:frags/desc.txt}"\n---\nHello\n', encoding="utf-8")
    agent = prompty.load(p)
    assert agent.description == "subdir description"


def test_included_fragment_in_prompt_dir_inlined(tmp_path: Path):
    """A text fragment inside the prompt directory is inlined."""
    import prompty

    (tmp_path / "frag.md").write_text("shared fragment text", encoding="utf-8")
    p = tmp_path / "c.prompty"
    p.write_text('---\nname: c\ndescription: "${prompt:frag.md}"\n---\nHello\n', encoding="utf-8")
    agent = prompty.load(p)
    assert agent.description == "shared fragment text"


def test_inherited_document_in_prompt_dir_inherited(tmp_path: Path):
    """A related document in the prompt directory contributes inherited fields."""
    import prompty

    (tmp_path / "shared.prompty").write_text(
        '---\nname: shared\ndescription: "inherited description"\n---\nBaseBody\n', encoding="utf-8"
    )
    p = tmp_path / "d.prompty"
    p.write_text('---\nname: d\nbase: shared.prompty\n---\nChildBody\n', encoding="utf-8")
    agent = prompty.load(p)
    assert agent.description == "inherited description"


def test_template_snippet_in_prompt_dir_renders(tmp_path: Path):
    """A template snippet inside the prompt directory is pulled into the body."""
    import prompty

    sub = tmp_path / "partials"
    sub.mkdir()
    (sub / "footer.md").write_text("INLINED FOOTER", encoding="utf-8")
    p = tmp_path / "e.prompty"
    p.write_text(
        "---\n"
        "name: e\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: fun-fake\n"
        "---\n"
        'system:\nHello {% include "partials/footer.md" %}\n',
        encoding="utf-8",
    )

    class _Completions:
        @staticmethod
        def create(**kwargs):
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

    prompty.register_connection("fun-fake", client=_Client())
    agent = prompty.load(p)
    rendered = prompty.render(agent, {})
    assert "INLINED FOOTER" in rendered


def test_companion_prompt_in_prompt_dir_projects(tmp_path: Path):
    """A companion prompt that lives beside the prompt still projects."""
    import prompty

    (tmp_path / "child.prompty").write_text(
        "---\n"
        "name: child\n"
        'description: "child tool description"\n'
        "inputs:\n  - name: text\n    kind: string\n"
        "---\n"
        "system:\nsummarize\n",
        encoding="utf-8",
    )
    parent = tmp_path / "p.prompty"
    parent.write_text(
        "---\n"
        "name: p\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: fun-fake\n"
        "tools:\n"
        "  - name: summarize\n"
        "    kind: prompty\n"
        "    path: child.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )
    captured: list = []

    class _Completions:
        @staticmethod
        def create(**kwargs):
            captured.append(kwargs)

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

    prompty.register_connection("fun-fake", client=_Client())
    agent = prompty.load(parent)
    messages = prompty.prepare(agent, {})
    prompty.run(agent, messages)
    assert captured, "request was not built"
    tools = captured[0].get("tools") or []
    names = [t.get("function", {}).get("name") for t in tools]
    assert "summarize" in names


def test_companion_prompt_in_prompt_dir_dispatches(tmp_path: Path):
    """A companion prompt that lives beside the prompt still runs as a tool."""
    import prompty
    from prompty.core.tool_dispatch import dispatch_tool

    (tmp_path / "child.prompty").write_text(
        "---\n"
        "name: child\n"
        'description: "child tool description"\n'
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: fun-fake\n"
        "---\n"
        "system:\nchild body\n",
        encoding="utf-8",
    )
    parent = tmp_path / "p.prompty"
    parent.write_text(
        "---\n"
        "name: p\n"
        "model:\n  id: gpt-4\n  provider: openai\n  apiType: chat\n"
        "  connection:\n    kind: reference\n    name: fun-fake\n"
        "tools:\n"
        "  - name: summarize\n"
        "    kind: prompty\n"
        "    path: child.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )

    class _Completions:
        @staticmethod
        def create(**kwargs):
            class _R:
                choices = []
                usage = None
                model = "test"
                output_text = "child ran"

                def __str__(self):
                    return self.output_text

            return _R()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    prompty.register_connection("fun-fake", client=_Client())
    agent = prompty.load(parent)
    out = dispatch_tool("summarize", "{}", {}, agent, {})
    assert "child ran" in str(out)
