"""Legitimate references inside a prompt's own directory must keep working."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from prompty import load, prepare
from prompty.core.loader import load_async
from prompty.core.tool_dispatch import dispatch_tool
from prompty.providers.openai.executor import OpenAIExecutor


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def prompts(tmp_path):
    root = tmp_path.resolve() / "prompts"
    root.mkdir()
    _write(root / "inside.txt", "INSIDE-TEXT-OK")
    _write(root / "frags" / "desc.txt", "SUBDIR-TEXT-OK")
    _write(root / "partials" / "preamble.md", "PREAMBLE-OK")
    _write(root / "frag.md", "FRAGMENT-OK")
    _write(root / "shared.yaml", "answer: 42\n")
    _write(
        root / "shared_connection.json",
        json.dumps({"kind": "key", "endpoint": "https://shared.example/", "apiKey": "shared-key"}),
    )
    return root


def test_file_reference_returns_structured_data(prompts):
    prompt = _write(
        prompts / "structured.prompty",
        "---\nname: structured\nmodel:\n  id: gpt-4\n  apiType: chat\n"
        "  connection: ${file:shared_connection.json}\n---\nbody\n",
    )
    agent = load(prompt)
    assert agent.model.connection is not None
    assert agent.model.connection.endpoint == "https://shared.example/"
    assert agent.model.connection.api_key == "shared-key"


def test_file_reference_in_subdirectory(prompts):
    prompt = _write(
        prompts / "subdir.prompty",
        '---\nname: subdir\ndescription: "${file:frags/desc.txt}"\n---\nbody\n',
    )
    assert load(prompt).description == "SUBDIR-TEXT-OK"


def test_file_reference_absolute_path_inside(prompts):
    prompt = _write(
        prompts / "absolute.prompty",
        f'---\nname: absolute\ndescription: "${{file:{(prompts / "inside.txt").as_posix()}}}"\n---\nbody\n',
    )
    assert load(prompt).description == "INSIDE-TEXT-OK"


def test_file_reference_dotdot_inside(prompts):
    prompt = _write(
        prompts / "normalized.prompty",
        '---\nname: normalized\ndescription: "${file:frags/../inside.txt}"\n---\nbody\n',
    )
    assert load(prompt).description == "INSIDE-TEXT-OK"


def test_prompt_fragment_inlined(prompts):
    prompt = _write(
        prompts / "fragment.prompty",
        '---\nname: fragment\ndescription: "${prompt:frag.md}"\n---\nbody\n',
    )
    assert load(prompt).description == "FRAGMENT-OK"


def test_base_template_inherited(prompts):
    _write(prompts / "base.prompty", "---\nname: base\ndescription: BASE-DESCRIPTION\n---\nbase body\n")
    prompt = _write(
        prompts / "child.prompty",
        "---\nbase: base.prompty\nname: child\n---\nchild body\n",
    )
    agent = load(prompt)
    assert agent.name == "child"
    assert agent.description == "BASE-DESCRIPTION"


def test_yaml_include_structured(prompts):
    prompt = _write(
        prompts / "included.prompty",
        "---\nname: included\nmetadata:\n  cfg: !include shared.yaml\n---\nbody\n",
    )
    agent = load(prompt)
    assert agent.metadata["cfg"] == {"answer": 42}


def test_body_partial_inlined(prompts):
    prompt = _write(
        prompts / "partial.prompty",
        '---\nname: partial\n---\nsystem:\n@include "partials/preamble.md"\nuser: hi\n',
    )
    agent = load(prompt)
    assert "PREAMBLE-OK" in agent.instructions
    assert "user: hi" in agent.instructions


def test_async_file_reference_inside(prompts):
    prompt = _write(
        prompts / "async.prompty",
        '---\nname: async\ndescription: "${file:inside.txt}"\n---\nbody\n',
    )
    assert asyncio.run(load_async(prompt)).description == "INSIDE-TEXT-OK"


def test_prompty_tool_projection_inside(prompts):
    _write(
        prompts / "child.prompty",
        "---\nname: child\nmodel: gpt-4\ndescription: CHILD-DESCRIPTION\n"
        "inputs:\n  - name: text\n    kind: string\n---\nchild body\n",
    )
    parent = _write(
        prompts / "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        "    path: ./child.prompty\n---\nparent body\n",
    )
    agent = load(parent)
    args = OpenAIExecutor()._build_chat_args(agent, [])
    function = args["tools"][0]["function"]
    assert function["name"] == "helper"
    assert function["description"] == "CHILD-DESCRIPTION"
    assert "text" in function["parameters"]["properties"]


def test_prompty_tool_projection_responses_inside(prompts):
    _write(
        prompts / "child.prompty",
        "---\nname: child\nmodel: gpt-4\ndescription: CHILD-DESCRIPTION\n"
        "inputs:\n  - name: text\n    kind: string\n---\nchild body\n",
    )
    parent = _write(
        prompts / "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        "    path: ./child.prompty\n---\nparent body\n",
    )
    agent = load(parent)
    args = OpenAIExecutor()._build_responses_args(agent, [])
    tool = args["tools"][0]
    assert tool["name"] == "helper"
    assert tool["description"] == "CHILD-DESCRIPTION"
    assert "text" in tool["parameters"]["properties"]


def test_prompty_tool_dispatch_inside(prompts):
    _write(
        prompts / "child.prompty",
        "---\nname: child\nmodel: gpt-4\ninputs:\n  - name: text\n    kind: string\n    default: ''\n---\nchild body\n",
    )
    parent = _write(
        prompts / "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        "    path: ./child.prompty\n    mode: single\n---\nparent body\n",
    )
    agent = load(parent)
    with patch("prompty.core.pipeline.run", return_value="stub-run"):
        result = dispatch_tool("helper", "{}", {}, agent, {})
    assert result == "stub-run"


def test_template_fragment_inlined(prompts):
    prompt = _write(
        prompts / "template.prompty",
        '---\nname: template\n---\nsystem:\n{% include "partials/preamble.md" %}\nuser: hi\n',
    )
    agent = load(prompt)
    messages = prepare(agent, {})
    text = "\n".join(m.to_text_content() for m in messages)
    assert "PREAMBLE-OK" in text
    assert "hi" in text


def test_template_inheritance_applied(prompts):
    _write(prompts / "tpls" / "base.jinja", "BASE-OK {% block body %}{% endblock %} END-OK")
    prompt = _write(
        prompts / "inherit.prompty",
        '---\nname: inherit\n---\nsystem:\n{% extends "tpls/base.jinja" %}'
        "{% block body %}CHILD-OK{% endblock %}\n",
    )
    agent = load(prompt)
    messages = prepare(agent, {})
    text = "\n".join(m.to_text_content() for m in messages)
    assert "BASE-OK" in text
    assert "CHILD-OK" in text
    assert "END-OK" in text
