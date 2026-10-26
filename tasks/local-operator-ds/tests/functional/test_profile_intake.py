"""Bringing a profile in still installs it, with its name and instructions."""

import io
import json
import uuid

import pytest

from harness import (
    agent_metadata,
    build_archive,
    create_agent,
    export_archive,
    open_app,
    unique_name,
    upload_archive,
)

PRIVATE_HISTORY = "private history that must not travel"
DISPLAY_NAME = "../Display name is not a path"
INSTRUCTIONS = "Answer in one short paragraph."


def _archive(tmp_path):
    return tmp_path / f"profile-{uuid.uuid4().hex[:8]}.zip"


@pytest.mark.asyncio
async def test_import_copies_a_profile_and_its_instructions(tmp_path):
    archive = build_archive(
        _archive(tmp_path),
        agent_metadata(unique_name("archive"), name=DISPLAY_NAME),
        {
            "system_prompt.md": INSTRUCTIONS,
            "conversation.jsonl": PRIVATE_HISTORY,
            "execution_history.jsonl": PRIVATE_HISTORY,
        },
    )
    async with open_app(tmp_path / "config") as app:
        existing = await create_agent(
            app, name=unique_name("existing"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        existing_metadata = (app.agents_dir / existing["id"] / "agent.yml").read_text()

        response = await upload_archive(app, archive)
        assert response.status_code in (200, 201), response.text
        imported = response.json()["result"]
        assert imported["name"] == DISPLAY_NAME

        fetched = await app.client.get(f"/v1/agents/{imported['id']}")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["result"]["name"] == DISPLAY_NAME

        row = app.agents_dir / imported["id"]
        assert (row / "system_prompt.md").read_text() == INSTRUCTIONS
        assert not (row / "conversation.jsonl").exists() or not (
            row / "conversation.jsonl"
        ).read_text().strip()

        assert (app.agents_dir / existing["id"] / "agent.yml").read_text() == existing_metadata
        assert (
            app.agents_dir / existing["id"] / "conversation.jsonl"
        ).read_text() == PRIVATE_HISTORY


@pytest.mark.asyncio
async def test_exported_profile_can_be_imported_elsewhere(tmp_path):
    async with open_app(tmp_path / "source") as source:
        agent = await create_agent(source, name=unique_name("shared"))
        (source.agents_dir / agent["id"] / "system_prompt.md").write_text(INSTRUCTIONS)
        archive_bytes = await export_archive(source, agent["id"])

    async with open_app(tmp_path / "target") as target:
        response = await target.client.post(
            "/v1/agents/import",
            files={"file": ("profile.zip", io.BytesIO(archive_bytes), "application/zip")},
        )
        assert response.status_code in (200, 201), response.text
        imported = response.json()["result"]
        assert imported["name"] == agent["name"]
        row = target.agents_dir / imported["id"]
        assert (row / "system_prompt.md").read_text() == INSTRUCTIONS


@pytest.mark.asyncio
async def test_install_a_shared_profile_document(tmp_path):
    async with open_app(tmp_path / "config") as app:
        document = {
            "id": str(uuid.uuid4()),
            "name": unique_name("shared"),
            "created_date": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "system_prompt": INSTRUCTIONS,
        }
        response = await app.client.post("/v1/agents/install", json=document)
        assert response.status_code in (200, 201), response.text
        installed = response.json()["result"]
        assert installed["name"] == document["name"]

        listed = await app.client.get("/v1/agents")
        names = [row["name"] for row in listed.json()["result"]["agents"]]
        assert document["name"] in names

        rows = [
            path
            for path in app.agents_dir.iterdir()
            if (path / "system_prompt.md").exists()
            and (path / "system_prompt.md").read_text() == INSTRUCTIONS
        ]
        assert len(rows) == 1


@pytest.mark.asyncio
async def test_legacy_manifest_imports_a_safe_row(tmp_path):
    manifest = [
        {
            "id": "legacy-agent-one",
            "name": "Legacy Agent",
            "created_date": "2024-01-01T00:00:00Z",
            "version": "0.1.0",
        }
    ]
    async with open_app(tmp_path / "config") as app:
        response = await app.client.post(
            "/v1/agents/legacy-import",
            files={"file": ("agents.json", json.dumps(manifest), "application/json")},
        )
        assert response.status_code in (200, 201), response.text

        fetched = await app.client.get("/v1/agents/legacy-agent-one")
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["result"]["name"] == "Legacy Agent"
