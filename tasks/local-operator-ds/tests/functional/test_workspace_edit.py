"""The edit endpoint keeps working for files an agent may edit."""

import pytest

from harness import create_agent, mock_operator, open_app, unique_name

WORKSPACE_TEXT = "workspace original text"


async def _edit(app, agent_id, file_path):
    return await app.client.post(
        f"/v1/chat/agents/{agent_id}/edit",
        json={
            "file_path": file_path,
            "edit_prompt": "Improve this file",
            "hosting": "test-hosting",
            "model": "test-model",
        },
    )


@pytest.mark.asyncio
async def test_edit_reads_an_absolute_path_inside_the_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    target.write_text(WORKSPACE_TEXT)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], str(target))
            assert response.status_code == 200, response.text
            assert WORKSPACE_TEXT in capture.transcript
            assert target.read_text() == WORKSPACE_TEXT


@pytest.mark.asyncio
async def test_edit_reads_through_a_link_inside_the_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    target.write_text(WORKSPACE_TEXT)
    link = workspace / "linked.txt"
    link.symlink_to(target)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], str(link))
            assert response.status_code == 200, response.text
            assert WORKSPACE_TEXT in capture.transcript


@pytest.mark.asyncio
async def test_edit_works_with_a_filesystem_root_workspace(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    target.write_text(WORKSPACE_TEXT)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace="/")
        with mock_operator(monkeypatch) as capture:
            response = await _edit(app, agent["id"], str(target))
            assert response.status_code == 200, response.text
            assert WORKSPACE_TEXT in capture.transcript


@pytest.mark.asyncio
async def test_edit_unknown_agent_is_a_client_error(tmp_path, monkeypatch):
    async with open_app(tmp_path / "config") as app:
        with mock_operator(monkeypatch):
            response = await _edit(app, unique_name("absent"), str(tmp_path / "note.txt"))
            assert 400 <= response.status_code < 500, response.text
