"""Author-named paths in a prompt document must stay inside its directory.

Each test loads a document that names a harmless marker file outside the
document's own directory, and asserts that the library refuses and never opens
the outside file — whichever part of the document or composition feature names
the path, however the path is spelled, and whichever public entry point is used.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from conftest import assert_never_opened, opened_files

from prompty import load, prepare
from prompty.core.loader import load_async
from prompty.core.tool_dispatch import dispatch_tool
from prompty.providers.openai.executor import OpenAIExecutor


# ---------------------------------------------------------------------------
# File references in frontmatter
# ---------------------------------------------------------------------------


def test_file_reference_relative_traversal(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${file:../outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_file_reference_absolute_path(tree):
    prompt = tree.write(
        "attack.prompty",
        f'---\nname: attack\ndescription: "${{file:{tree.outside.as_posix()}}}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_file_reference_symlink_escape(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${file:escape-file.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_file_reference_symlinked_directory_escape(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${file:escape-dir/outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.linked_dir_file)


def test_file_reference_prefix_sibling_directory(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${file:../prompts-extra/outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.prefix_sibling)


def test_file_reference_nested_in_pulled_file(tree):
    tree.write("model.json", '{"id": "${file:../outside-content.txt}", "provider": "openai"}')
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\nmodel: "${file:model.json}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_file_reference_array_element(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ninputs:\n  - name: q\n    kind: string\n'
        '    example: "${file:../outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_file_reference_async_entry_point(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${file:../outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            asyncio.run(load_async(prompt))
    assert_never_opened(seen, tree.outside)


# ---------------------------------------------------------------------------
# Child prompts declared as tools
# ---------------------------------------------------------------------------


def test_prompty_tool_projection_relative(tree):
    prompt = tree.write(
        "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        "    path: ../outside-child.prompty\n---\nparent body\n",
    )
    agent = load(prompt)
    with opened_files() as seen:
        with pytest.raises(Exception):
            OpenAIExecutor()._build_chat_args(agent, [])
    assert_never_opened(seen, tree.outside_child)


def test_prompty_tool_projection_responses_format(tree):
    prompt = tree.write(
        "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        "    path: ../outside-child.prompty\n---\nparent body\n",
    )
    agent = load(prompt)
    with opened_files() as seen:
        with pytest.raises(Exception):
            OpenAIExecutor()._build_responses_args(agent, [])
    assert_never_opened(seen, tree.outside_child)


def test_prompty_tool_dispatch_absolute(tree):
    prompt = tree.write(
        "parent.prompty",
        "---\nname: parent\nmodel: gpt-4\ntools:\n  - name: helper\n    kind: prompty\n"
        f"    path: {tree.outside_child.as_posix()}\n---\nparent body\n",
    )
    agent = load(prompt)
    with opened_files() as seen:
        with patch("prompty.core.pipeline.run", return_value="stub-run"):
            result = dispatch_tool("helper", "{}", {}, agent, {})
    assert_never_opened(seen, tree.outside_child)
    assert "PROMPTY-OUTSIDE-CONTENT" not in result


# ---------------------------------------------------------------------------
# Other composition features a document can use
# ---------------------------------------------------------------------------


def test_prompt_fragment_traversal(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\ndescription: "${prompt:../outside-content.txt}"\n---\nbody\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_base_template_traversal(tree):
    prompt = tree.write(
        "attack.prompty",
        "---\nbase: ../outside-base.prompty\nname: attack\n---\nbody\n",
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside_base)


def test_yaml_include_traversal(tree):
    prompt = tree.write(
        "attack.prompty",
        "---\nname: attack\nmetadata:\n  cfg: !include ../outside-content.txt\n---\nbody\n",
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_yaml_include_nested_in_pulled_file(tree):
    tree.write("fragment.yaml", "value: !include ../outside-content.txt\n")
    prompt = tree.write(
        "attack.prompty",
        "---\nname: attack\nmetadata:\n  cfg: !include fragment.yaml\n---\nbody\n",
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


def test_body_partial_traversal(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\n---\nsystem:\n@include "../outside-content.txt"\n',
    )
    with opened_files() as seen:
        with pytest.raises(Exception):
            load(prompt)
    assert_never_opened(seen, tree.outside)


# ---------------------------------------------------------------------------
# Fragments composed while the document is rendered
# ---------------------------------------------------------------------------


def test_template_fragment_symlink_escape(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\n---\nsystem:\n{% include "escape-file.txt" %}\n',
    )
    agent = load(prompt)
    with opened_files() as seen:
        with pytest.raises(Exception):
            prepare(agent, {})
    assert_never_opened(seen, tree.outside)


def test_template_fragment_symlinked_directory_escape(tree):
    prompt = tree.write(
        "attack.prompty",
        '---\nname: attack\n---\nsystem:\n{% include "escape-dir/outside-content.txt" %}\n',
    )
    agent = load(prompt)
    with opened_files() as seen:
        with pytest.raises(Exception):
            prepare(agent, {})
    assert_never_opened(seen, tree.linked_dir_file)
