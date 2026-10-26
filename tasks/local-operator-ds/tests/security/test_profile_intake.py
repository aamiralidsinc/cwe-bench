"""A profile archive may not choose where it is stored or what it replaces."""

import uuid

import pytest

from harness import (
    agent_metadata,
    build_archive,
    create_agent,
    open_app,
    stub_radient_download,
    unique_name,
    upload_archive,
)

PRIVATE_HISTORY = "private history of the local operator"


def _archive_path(tmp_path):
    return tmp_path / f"profile-{uuid.uuid4().hex[:8]}.zip"


@pytest.mark.asyncio
@pytest.mark.parametrize("shape", ["relative", "absolute", "empty"])
async def test_archive_identifier_never_selects_a_destination(tmp_path, shape):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("keep")
    config_dir = tmp_path / "config"
    async with open_app(config_dir) as app:
        victim = await create_agent(
            app, name=unique_name("victim"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        victim_dir = app.agents_dir / victim["id"]
        if shape == "relative":
            identifier = "../../outside"
        elif shape == "absolute":
            identifier = str(outside)
        else:
            identifier = ""
        archive = build_archive(
            _archive_path(tmp_path),
            agent_metadata(identifier, name="Shared Wallpapers"),
            {"system_prompt.md": "wallpapers"},
        )
        response = await upload_archive(app, archive)
        assert response.status_code < 500, response.text
        assert sentinel.exists()
        assert sentinel.read_text() == "keep"
        assert victim_dir.is_dir()
        assert (victim_dir / "conversation.jsonl").read_text() == PRIVATE_HISTORY


@pytest.mark.asyncio
async def test_archive_identifier_matching_an_existing_profile_keeps_it(tmp_path):
    async with open_app(tmp_path / "config") as app:
        victim = await create_agent(
            app, name=unique_name("victim"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        victim_dir = app.agents_dir / victim["id"]
        original_metadata = (victim_dir / "agent.yml").read_text()
        archive = build_archive(
            _archive_path(tmp_path),
            agent_metadata(victim["id"], name="Impostor Profile"),
            {"system_prompt.md": "impostor instructions"},
        )
        response = await upload_archive(app, archive)
        assert response.status_code < 500, response.text
        assert (victim_dir / "agent.yml").read_text() == original_metadata
        assert (victim_dir / "conversation.jsonl").read_text() == PRIVATE_HISTORY
        assert not (victim_dir / "system_prompt.md").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["file", "symlink", "dangling-symlink", "directory"])
async def test_archive_identifier_cannot_replace_an_existing_entry(tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("keep")
    async with open_app(tmp_path / "config") as app:
        identifier = unique_name("taken")
        target = app.agents_dir / identifier
        if kind == "file":
            target.write_text("keep")
        elif kind == "symlink":
            target.symlink_to(outside, target_is_directory=True)
        elif kind == "dangling-symlink":
            target.symlink_to(tmp_path / "absent", target_is_directory=True)
        else:
            target.mkdir()
            (target / "keep").write_text("keep")
        archive = build_archive(
            _archive_path(tmp_path),
            agent_metadata(identifier, name="Colliding Profile"),
            {"system_prompt.md": "collide"},
        )
        response = await upload_archive(app, archive)
        assert response.status_code < 500, response.text
        assert sentinel.exists()
        assert sentinel.read_text() == "keep"
        if kind == "file":
            assert target.is_file() and target.read_text() == "keep"
        elif kind == "symlink":
            assert target.is_symlink()
        elif kind == "dangling-symlink":
            assert target.is_symlink()
            assert not (tmp_path / "absent").exists()
        else:
            assert (target / "keep").read_text() == "keep"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metadata",
    [None, [], "plain text", {"id": []}, {"id": {}}, {"name": []}, {"id": "x", "name": []}],
)
async def test_malformed_profile_metadata_leaves_the_store_untouched(tmp_path, metadata):
    async with open_app(tmp_path / "config") as app:
        victim = await create_agent(
            app, name=unique_name("victim"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        before = sorted(path.name for path in app.agents_dir.iterdir())
        archive = build_archive(_archive_path(tmp_path), metadata)
        response = await upload_archive(app, archive)
        assert response.status_code < 500, response.text
        assert sorted(path.name for path in app.agents_dir.iterdir()) == before
        assert (app.agents_dir / victim["id"] / "conversation.jsonl").read_text() == PRIVATE_HISTORY


@pytest.mark.asyncio
async def test_pull_route_does_not_trust_the_archive_identity(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("keep")
    async with open_app(tmp_path / "config") as app:
        victim = await create_agent(
            app, name=unique_name("victim"), private_file=("conversation.jsonl", PRIVATE_HISTORY)
        )
        metadata = agent_metadata("../../outside", name="Pulled From The Hub")
        with stub_radient_download(monkeypatch, metadata, {"system_prompt.md": "pulled"}):
            response = await app.client.get(f"/v1/agents/{unique_name('hub')}/download")
        assert response.status_code < 500, response.text
        assert sentinel.exists()
        assert sentinel.read_text() == "keep"
        assert (app.agents_dir / victim["id"] / "conversation.jsonl").read_text() == PRIVATE_HISTORY
