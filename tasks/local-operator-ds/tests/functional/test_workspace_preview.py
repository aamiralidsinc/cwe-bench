"""The editor's workspace file view keeps working for files in the workspace."""

import pytest

from harness import create_agent, open_app, unique_name

WORKSPACE_TEXT = "workspace original text"


async def _read(app, agent_id, path):
    return await app.client.get(
        f"/v1/chat/agents/{agent_id}/files/content", params={"path": path}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", ["relative", "absolute"])
async def test_workspace_file_is_readable(tmp_path, shape):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    target.write_text(WORKSPACE_TEXT)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        path = "note.txt" if shape == "relative" else str(target)
        response = await _read(app, agent["id"], path)
        assert response.status_code == 200, response.text
        assert WORKSPACE_TEXT in response.text


@pytest.mark.asyncio
async def test_workspace_link_to_a_workspace_file_is_readable(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    target = workspace / "note.txt"
    target.write_text(WORKSPACE_TEXT)
    link = workspace / "linked.txt"
    link.symlink_to(target)
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        response = await _read(app, agent["id"], "linked.txt")
        assert response.status_code == 200, response.text
        assert WORKSPACE_TEXT in response.text


@pytest.mark.asyncio
async def test_missing_workspace_file_is_a_client_error(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        response = await _read(app, agent["id"], "absent.txt")
        assert 400 <= response.status_code < 500, response.text
