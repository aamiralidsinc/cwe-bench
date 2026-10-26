"""A legacy profile manifest may not choose where its rows are written."""

import json

import pytest

from harness import agent_metadata, create_agent, open_app, unique_name, write_agent_row

PRIVATE_HISTORY = "private history of the local operator"


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", ["relative", "absolute"])
async def test_legacy_manifest_identifier_never_selects_a_destination(tmp_path, shape):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("keep")

    async with open_app(tmp_path / "config") as app:
        victim = await create_agent(
            app, name=unique_name("victim"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        identifier = "../../outside" if shape == "relative" else str(outside)
        manifest = [agent_metadata(identifier, name="Legacy Agent")]
        response = await app.client.post(
            "/v1/agents/legacy-import",
            files={"file": ("agents.json", json.dumps(manifest), "application/json")},
        )
        assert 400 <= response.status_code < 500, response.text
        assert sentinel.exists()
        assert sentinel.read_text() == "keep"
        assert not (outside / "agent.yml").exists()
        assert (app.agents_dir / victim["id"] / "conversation.jsonl").read_text() == PRIVATE_HISTORY
