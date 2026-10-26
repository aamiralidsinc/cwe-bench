"""Functional tests: ordinary backup names and identifiers keep working."""

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


def _backup_tar(name: str, slug: str = "abc123") -> bytes:
    """Return an (uncompressed) backup archive containing the metadata."""
    payload = json.dumps(
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
    url: str = "/api/backup/upload",
):
    form = FormData(quote_fields=False)
    form.add_field(
        "file",
        payload,
        filename="backup.tar",
        content_type="application/octet-stream",
    )
    return await client.post(f"{url}?agent_id={LOCAL_AGENT_ID}", data=form)


async def _list_backups(client: WebSocketGenerator) -> list[dict]:
    await client.send_json_auto_id({"type": "backup/info"})
    result = await client.receive_json()
    assert result["success"] is True
    return result["result"]["backups"]


async def test_upload_keeps_spaces_and_dots_in_name(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Uploading a backup with a normal name stores it under the usual derived filename."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_client()

    resp = await _upload(client, _backup_tar("Automatic backup 2026.7.0"))

    assert resp.status == 201
    stored = list((config_dir / "backups").glob("Automatic_backup_2026.7.0_*.tar"))
    assert len(stored) == 1

    ws_client = await hass_ws_client(hass)
    names = [backup["name"] for backup in await _list_backups(ws_client)]
    assert "Automatic backup 2026.7.0" in names


async def test_create_backup_with_default_name(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Creating a backup without a name uses the default composition and is stored."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/generate",
            "agent_ids": [LOCAL_AGENT_ID],
            "include_database": False,
        }
    )
    result = await client.receive_json()
    assert result["success"] is True
    await hass.async_block_till_done()

    stored = list((config_dir / "backups").glob("Custom_backup_*.tar"))
    assert len(stored) == 1

    backups = await _list_backups(client)
    assert len(backups) == 1
    assert backups[0]["name"].startswith("Custom backup ")


async def test_create_backup_keeps_unicode_name(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Creating a backup with spaces, dots and non-ASCII characters keeps the name."""
    await setup_backup_integration(hass)
    config_dir = Path(hass.config.config_dir)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/generate",
            "agent_ids": [LOCAL_AGENT_ID],
            "include_database": False,
            "name": "Café backup 2026.7.0",
        }
    )
    result = await client.receive_json()
    assert result["success"] is True
    await hass.async_block_till_done()

    stored = list((config_dir / "backups").glob("Caf*_backup_2026.7.0_*.tar"))
    assert len(stored) == 1
    backups = await _list_backups(client)
    assert backups[0]["name"] == "Café backup 2026.7.0"


async def test_onboarding_upload_with_normal_name(
    hass: HomeAssistant,
    hass_storage: dict,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """The unauthenticated onboarding upload keeps working for a normal name."""
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
        client, _backup_tar("Onboarding backup"), url="/api/onboarding/backup/upload"
    )

    assert resp.status == 201
    assert len(list((config_dir / "backups").glob("Onboarding_backup_*.tar"))) == 1


async def test_restore_with_normal_identifier_stages_inside(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Restoring a backup with a normal identifier stages the archive in the temp folder."""
    await setup_backup_integration(
        hass,
        remote_agents=["test.remote"],
        backups={"test.remote": [TEST_BACKUP_ABC123]},
    )
    temp_dir = Path(hass.config.path("tmp_backups"))
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "backup/restore",
            "backup_id": TEST_BACKUP_ABC123.backup_id,
            "agent_id": "test.remote",
        }
    )
    result = await client.receive_json()
    assert result["success"] is False
    await hass.async_block_till_done()

    assert (temp_dir / f"{TEST_BACKUP_ABC123.backup_id}.tar").is_file()


async def test_listing_skips_an_unusable_archive(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """One archive with an unusable name already on disk does not break the backup list."""
    config_dir = Path(hass.config.config_dir)
    backups_dir = config_dir / "backups"
    backups_dir.mkdir(exist_ok=True)
    (backups_dir / "unusable.tar").write_bytes(_backup_tar("../not usable"))
    await setup_backup_integration(hass)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "backup/info"})
    result = await client.receive_json()

    assert result["success"] is True
