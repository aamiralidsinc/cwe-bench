"""A stored profile identity may not name a location the profile did not own."""

import pytest

from harness import (
    agent_metadata,
    create_agent,
    open_app,
    reload_registry,
    unique_name,
    write_agent_row,
)

PRIVATE_HISTORY = "private history of the local operator"
SHARED_NAME = "Shared Photo Presets"


@pytest.mark.asyncio
async def test_installed_profile_cannot_claim_an_existing_identity(tmp_path):
    async with open_app(tmp_path / "config") as app:
        victim = await create_agent(
            app, name=unique_name("research"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        victim_dir = app.agents_dir / victim["id"]
        shared_document = {
            "id": victim["id"],
            "name": SHARED_NAME,
            "created_date": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "system_prompt": "presets and filters",
        }
        response = await app.client.post("/v1/agents/install", json=shared_document)
        if response.status_code >= 400:
            assert response.status_code < 500, response.text
            assert (victim_dir / "conversation.jsonl").read_text() == PRIVATE_HISTORY
            return

        reported = response.json()["result"]["id"]
        reload_registry(app)

        fetched = await app.client.get(f"/v1/agents/{reported}")
        assert fetched.status_code < 500, fetched.text
        assert fetched.json()["result"]["name"] == SHARED_NAME

        removed = await app.client.delete(f"/v1/agents/{reported}")
        assert removed.status_code < 500, removed.text
        assert victim_dir.is_dir()
        assert (victim_dir / "conversation.jsonl").read_text() == PRIVATE_HISTORY
        assert not (victim_dir / "system_prompt.md").exists()


@pytest.mark.asyncio
async def test_stored_profile_metadata_cannot_name_a_location(tmp_path):
    config_dir = tmp_path / "config"
    row = write_agent_row(config_dir, "victim-row", agent_metadata("..", name="Old Profile"))
    (row / "conversation.jsonl").write_text(PRIVATE_HISTORY, encoding="utf-8")

    async with open_app(config_dir) as app:
        fetched = await app.client.get("/v1/agents/%2E%2E")
        assert 400 <= fetched.status_code < 500, fetched.text

        removed = await app.client.delete("/v1/agents/%2E%2E")
        assert 400 <= removed.status_code < 500, removed.text

    assert config_dir.is_dir()
    assert row.is_dir()
    assert (row / "conversation.jsonl").read_text() == PRIVATE_HISTORY
