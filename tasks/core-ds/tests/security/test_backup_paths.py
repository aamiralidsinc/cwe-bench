"""Security tests: values carried in a backup must not divert writes outside its folder."""

from __future__ import annotations

from dataclasses import replace
import io
import json
from pathlib import Path
import tarfile

from aiohttp import FormData
import pytest

from homeassistant.components import onboarding
from homeassistant.components.backup import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import LOCAL_AGENT_ID, TEST_BACKUP_ABC123, setup_backup_integration
from tests.common import register_auth_provider
from tests.typing import ClientSessionGenerator, WebSocketGenerator


def _backup_json(name: str, slug: str = "abc123") -> bytes:
    """Return the metadata payload of a backup archive."""
    return json.dumps(
        {
            "compressed": True,
            "date": "2024-12-02T07:23:58.261875-05:00",
            "homeassistant": {
                "exclude_database": True,
                "version": "2024.12.0.dev0",
            },
            "name": name,
            "protected": False,
            "slug": slug,
            "type": "partial",
            "version": 2,
        }
    ).encode()


def _backup_tar(name: str, slug: str = "abc123") -> bytes:
    """Return an (uncompressed) backup archive containing the metadata."""
    payload = _backup_json(name, slug)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo("./backup.json")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    return buffer.getvalue()


async def _upload(
    client: ClientSessionGenerator,
    payload: bytes,
    *,
    agent_id: str = LOCAL_AGENT_ID,
    url: str = "/api/backup/upload",
):
    form = FormData(quote_fields=False)
    form.add_field(
        "file",
        payload,
        filename="backup.tar",
        content_type="application/octet-stream",
    )
    return await client.post(f"{url}?agent_id={agent_id}", data=form)


@pytest.mark.parametrize(
    "name",
    [
        "{config}/abs_escape",
        "../parent_escape",
    ],
)
async def test_upload_metadata_name_cannot_escape(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    name: str,
) -> None:
    """A name stored inside an uploaded archive must not place a file outside backups."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_client()

    resp = await _upload(client, _backup_tar(name.format(config=config_dir)))

    assert 400 <= resp.status < 500, resp.status
    assert not list(config_dir.glob("*escape*.tar"))


async def test_onboarding_upload_metadata_name_cannot_escape(
    hass: HomeAssistant,
    hass_storage: dict,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """The unauthenticated setup upload applies the same protection."""
    await register_auth_provider(hass, {"type": "homeassistant"})
    hass_storage[onboarding.STORAGE_KEY] = {
        "version": onboarding.STORAGE_VERSION,
        "data": {"done": []},
    }
    assert await async_setup_component(hass, "onboarding", {})
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()
    config_dir = Path(hass.config.config_dir)
    client = await hass_client_no_auth()

    resp = await _upload(
        client,
        _backup_tar("../onb_parent_escape"),
        url="/api/onboarding/backup/upload",
    )

    assert 400 <= resp.status < 500, resp.status
    assert not list(config_dir.glob("*onb_*escape*.tar"))


@pytest.mark.parametrize(
    "name",
    [
        "{config}/gen_abs_escape",
        "../gen_parent_escape",
    ],
)
async def test_created_backup_name_cannot_escape(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    name: str,
) -> None:
    """A name supplied for a new backup must not place a file outside backups."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/generate",
            "agent_ids": [LOCAL_AGENT_ID],
            "include_database": False,
            "name": name.format(config=config_dir),
        }
    )
    # The refusal may be synchronous (command error) or asynchronous (failed job).
    await client.receive_json()
    await hass.async_block_till_done()

    assert not list(config_dir.glob("*escape*.tar"))

    await client.send_json_auto_id({"type": "backup/info"})
    result = await client.receive_json()
    assert result["success"] is True
    assert result["result"]["backups"] == []


@pytest.mark.parametrize(
    "name",
    [
        "{config}/stored_abs_escape",
        "../stored_parent_escape",
    ],
)
async def test_stored_backup_name_cannot_escape(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    name: str,
) -> None:
    """A name saved earlier for automatic backups must not place a file outside backups."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/config/update",
            "create_backup": {
                "agent_ids": [LOCAL_AGENT_ID],
                "name": name.format(config=config_dir),
            },
        }
    )
    result = await client.receive_json()
    if result["success"]:
        await client.send_json_auto_id(
            {"type": "backup/generate_with_automatic_settings"}
        )
        # The refusal may be synchronous (command error) or asynchronous (failed job).
        await client.receive_json()
    await hass.async_block_till_done()

    assert not list(config_dir.glob("*escape*.tar"))

    await client.send_json_auto_id({"type": "backup/info"})
    result = await client.receive_json()
    assert result["success"] is True
    assert result["result"]["backups"] == []


@pytest.mark.parametrize(
    "backup_id",
    [
        "{config}/restore_abs_escape",
        "../restore_parent_escape",
    ],
)
async def test_restored_backup_identifier_cannot_escape(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    backup_id: str,
) -> None:
    """An identifier stored with a backup must not place a staging file outside its folder."""
    config_dir = Path(hass.config.config_dir)
    backup = replace(
        TEST_BACKUP_ABC123,
        backup_id=backup_id.format(config=config_dir),
        name="Normal name",
    )
    await setup_backup_integration(
        hass,
        remote_agents=["test.remote"],
        backups={"test.remote": [backup]},
    )
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/restore",
            "backup_id": backup.backup_id,
            "agent_id": "test.remote",
        }
    )
    result = await client.receive_json()
    assert result["success"] is False
    await hass.async_block_till_done()

    assert not list(config_dir.glob("*restore_*escape*.tar"))


@pytest.mark.parametrize(
    "slug",
    [
        "{config}/meta_abs_escape",
        "../meta_parent_escape",
    ],
)
async def test_received_backup_identifier_cannot_escape(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    slug: str,
) -> None:
    """An identifier inside an uploaded archive must not place its stored metadata outside backups."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_client()

    resp = await _upload(
        client, _backup_tar("Normal name", slug.format(config=config_dir))
    )

    assert 400 <= resp.status < 500, resp.status
    assert not list(config_dir.glob("*meta_*escape*.json"))
