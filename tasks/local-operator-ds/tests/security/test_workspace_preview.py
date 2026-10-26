"""A workspace read may not leave the workspace through a look-alike prefix."""

import pytest

from harness import create_agent, open_app, unique_name

OUTSIDE = "outside private sentinel"


@pytest.mark.asyncio
async def test_workspace_read_is_confined_to_the_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "note.txt").write_text("workspace text")
    sibling = tmp_path / "workspace-other"
    sibling.mkdir()
    (sibling / "secret.txt").write_text(OUTSIDE)

    async with open_app(tmp_path / "config") as app:
        agent = await create_agent(app, name=unique_name("editor"), workspace=workspace)
        response = await app.client.get(
            f"/v1/chat/agents/{agent['id']}/files/content",
            params={"path": "../workspace-other/secret.txt"},
        )
        assert 400 <= response.status_code < 500, response.text
        assert OUTSIDE not in response.text
