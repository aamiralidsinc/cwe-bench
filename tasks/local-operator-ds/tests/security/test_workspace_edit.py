"""An edit request may only make the service read inside the agent workspace."""

import os

import pytest

from harness import create_agent, mock_operator, open_app, unique_name

OUTSIDE = "outside private sentinel"
WORKSPACE_TEXT = "workspace original text"


async def _edit(app, agent_id, file_path, **extra):
    return await app.client.post(
        f"/v1/chat/agents/{agent_id}/edit",
        json={
            "file_path": file_path,
            "edit_prompt": "Improve this file",
            "hosting": "test-hosting",
            "model": "test-model",
            **extra,
        },
    )


async def _workspace_case(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "note.txt").write_text(WORKSPACE_TEXT)
    outside = tmp_path / "outside.txt"
    outside.write_text(OUTSIDE)
    return workspace, outside


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", ["traversal", "absolute", "prefix-sibling", "symlink"])
async def test_edit_reads_only_the_agent_workspace(tmp_path, monkeypatch, shape):
    workspace, outside = await _workspace_case(tmp_path)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        if shape == "traversal":
            target = os.path.join(str(workspace), "..", "outside.txt")
        elif shape == "absolute":
            target = str(outside)
        elif shape == "prefix-sibling":
            sibling = tmp_path / "workspace-other"
            sibling.mkdir()
            (sibling / "note.txt").write_text(OUTSIDE)
            target = str(sibling / "note.txt")
        else:
            link = workspace / "linked.txt"
            link.symlink_to(outside)
            target = str(link)

        with mock_operator(monkeypatch) as capture:
            denied = await _edit(app, agent["id"], target)
            assert 400 <= denied.status_code < 500, denied.text
            allowed = await _edit(app, agent["id"], str(workspace / "note.txt"))
            assert allowed.status_code == 200, allowed.text
            transcript = capture.transcript
            assert WORKSPACE_TEXT in transcript
            assert OUTSIDE not in transcript


@pytest.mark.asyncio
@pytest.mark.parametrize("setting", ["none", "empty", "blank", "relative", "missing", "file"])
async def test_edit_fails_closed_without_a_usable_workspace(tmp_path, monkeypatch, setting):
    workspace, outside = await _workspace_case(tmp_path)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        if setting == "none":
            value = None
        elif setting == "empty":
            value = ""
        elif setting == "blank":
            value = "   "
        elif setting == "relative":
            value = "some/relative/place"
        elif setting == "missing":
            value = str(tmp_path / "missing-workspace")
        else:
            value = str(outside)
        app.registry._agents[agent["id"]].current_working_directory = value

        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], str(workspace / "note.txt"))
            assert 400 <= response.status_code < 500, response.text
            assert OUTSIDE not in capture.transcript


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["nul", "directory", "binary"])
async def test_edit_rejects_a_target_it_cannot_read_as_text(tmp_path, monkeypatch, kind):
    workspace, outside = await _workspace_case(tmp_path)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        if kind == "nul":
            target = str(workspace / "bad\x00name.txt")
        elif kind == "directory":
            target = str(workspace)
        else:
            binary = workspace / "picture.txt"
            binary.write_bytes(b"\xff\xfe\x00binary")
            target = str(binary)

        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], target)
            assert 400 <= response.status_code < 500, response.text
            assert OUTSIDE not in capture.transcript


@pytest.mark.asyncio
@pytest.mark.parametrize("buffer", ["", "unsaved editor buffer"])
async def test_edit_uses_a_supplied_buffer_without_reading_the_path(tmp_path, monkeypatch, buffer):
    workspace, outside = await _workspace_case(tmp_path)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], str(outside), file_content=buffer)
            assert response.status_code == 200, response.text
            assert OUTSIDE not in capture.transcript
