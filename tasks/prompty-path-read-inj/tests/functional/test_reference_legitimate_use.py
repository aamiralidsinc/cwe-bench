"""Functional tests: legitimate reference resolution inside the prompt
directory keeps working exactly as before, and structured references still
return structured data.
"""

import json
from pathlib import Path


def test_file_reference_in_prompt_dir_returns_structured_data(tmp_path: Path):
    """A ${file:...json} reference inside the prompt directory is parsed and
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


def test_prompt_fragment_in_prompt_dir_inlined(tmp_path: Path):
    """A ${prompt:...} fragment inside the prompt directory is inlined."""
    import prompty

    (tmp_path / "frag.md").write_text("shared fragment text", encoding="utf-8")
    p = tmp_path / "c.prompty"
    p.write_text('---\nname: c\ndescription: "${prompt:frag.md}"\n---\nHello\n', encoding="utf-8")
    agent = prompty.load(p)
    assert agent.description == "shared fragment text"


def test_base_template_in_prompt_dir_inherited(tmp_path: Path):
    """A base template in the prompt directory contributes inherited fields."""
    import prompty

    (tmp_path / "base.prompty").write_text(
        '---\nname: base\ndescription: "inherited description"\n---\nBaseBody\n', encoding="utf-8"
    )
    p = tmp_path / "d.prompty"
    p.write_text("---\nname: d\nbase: base.prompty\n---\nChildBody\n", encoding="utf-8")
    agent = prompty.load(p)
    assert agent.description == "inherited description"


def test_prompty_tool_child_in_prompt_dir_projects(tmp_path: Path):
    """A PromptyTool whose child lives in the prompt directory projects fine."""
    import prompty
    from prompty.providers.openai.executor import _project_prompty_tool

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
        "model:\n  id: gpt-4\n  apiType: chat\n"
        "tools:\n"
        "  - name: summarize\n"
        "    kind: prompty\n"
        "    path: child.prompty\n"
        "---\n"
        "system:\nhi\n",
        encoding="utf-8",
    )
    agent = prompty.load(parent)
    func_def = _project_prompty_tool(agent.tools[0], agent)
    assert func_def["name"] == "summarize"
    assert func_def["description"] == "child tool description"
