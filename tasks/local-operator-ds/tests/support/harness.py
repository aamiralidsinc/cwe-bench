"""Shared harness for the profile-intake and agent-workspace read checks.

Everything here is bookkeeping: temporary stores, HTTP clients for the real
application, archive builders, and a stand-in for the model provider. Expected
values are computed from the files this module writes.
"""

from __future__ import annotations

import contextlib
import io
import json
import uuid
import zipfile
from pathlib import Path
from types import SimpleNamespace

import yaml
from httpx import ASGITransport, AsyncClient

SEARCH_TOKEN = "original text"


def unique_name(prefix="profile"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def agent_metadata(agent_id="shared-id", name="Shared Profile", **extra):
    data = {
        "id": agent_id,
        "name": name,
        "created_date": "2024-01-01T00:00:00Z",
        "version": "1.0.0",
    }
    data.update(extra)
    return data


def build_archive(path: Path, metadata, files=None) -> Path:
    """Write a profile archive. ``metadata`` may be any YAML-serialisable object."""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("agent.yml", yaml.safe_dump(metadata))
        for name, body in (files or {}).items():
            archive.writestr(name, body)
    return path


def write_agent_row(config_dir: Path, directory: str, metadata) -> Path:
    """Create an agent directory with the given agent.yml, as a build would have."""
    row = Path(config_dir) / "agents" / directory
    row.mkdir(parents=True, exist_ok=True)
    (row / "agent.yml").write_text(yaml.safe_dump(metadata), encoding="utf-8")
    return row


class AppClient:
    """A client for the real application bound to one config directory."""

    def __init__(self, client: AsyncClient, config_dir: Path, registry):
        self.client = client
        self.config_dir = Path(config_dir)
        self.registry = registry

    @property
    def agents_dir(self) -> Path:
        return Path(self.config_dir) / "agents"


@contextlib.asynccontextmanager
async def open_app(config_dir: Path):
    """Bind the application to ``config_dir`` and yield a client for it."""
    from local_operator.agents import AgentRegistry
    from local_operator.config import ConfigManager
    from local_operator.credentials import CredentialManager
    from local_operator.env import EnvConfig
    from local_operator.jobs import JobManager
    from local_operator.server.app import app
    from local_operator.server.utils.event_broker import EventBroker
    from local_operator.server.utils.websocket_manager import WebSocketManager

    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    registry = AgentRegistry(config_dir=config_dir, refresh_interval=3600.0)
    app.state.credential_manager = CredentialManager(config_dir=config_dir)
    app.state.config_manager = ConfigManager(config_dir=config_dir)
    app.state.agent_registry = registry
    app.state.job_manager = JobManager()
    app.state.websocket_manager = WebSocketManager()
    app.state.event_broker = EventBroker()
    app.state.env_config = EnvConfig()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://local.test") as client:
        yield AppClient(client, config_dir, registry)


def reload_registry(app_client: AppClient):
    """Re-open the registry over the same store, as a restarting service does."""
    from local_operator.agents import AgentRegistry

    registry = AgentRegistry(config_dir=app_client.config_dir, refresh_interval=3600.0)
    from local_operator.server.app import app

    app.state.agent_registry = registry
    app_client.registry = registry
    return registry


async def create_agent(app_client: AppClient, name=None, workspace=None, private_file=None):
    """Create an agent through the real route and return its metadata."""
    payload = {"name": name or unique_name("agent")}
    if workspace is not None:
        payload["current_working_directory"] = str(workspace)
    response = await app_client.client.post("/v1/agents", json=payload)
    assert response.status_code in (200, 201), response.text
    agent = response.json()["result"]
    if private_file:
        target = app_client.agents_dir / agent["id"] / private_file[0]
        target.write_text(private_file[1], encoding="utf-8")
    return agent


async def upload_archive(app_client: AppClient, archive: Path):
    body = Path(archive).read_bytes()
    return await app_client.client.post(
        "/v1/agents/import",
        files={"file": ("profile.zip", io.BytesIO(body), "application/zip")},
    )


async def export_archive(app_client: AppClient, agent_id: str) -> bytes:
    response = await app_client.client.get(f"/v1/agents/{agent_id}/export")
    assert response.status_code == 200, response.text
    return response.content


class OperatorCapture:
    """A stand-in for the model-backed operator that records the prompt text."""

    def __init__(self):
        self.records = []
        capture = self

        class Executor:
            def __init__(self):
                self.agent_state = SimpleNamespace(conversation=[])

            def initialize_conversation_history(self, *args, **kwargs):
                return None

            def append_to_history(self, record):
                capture.records.append(record)

            def get_conversation_history(self):
                return list(capture.records)

            async def invoke_model(self, history):
                # An empty replacement set keeps the route on its success path;
                # these checks read the prompt the route built, not the diff.
                return SimpleNamespace(content="<replacements>\n</replacements>")

        self.executor = Executor()
        self.calls = 0

    def factory(self, *args, **kwargs):
        self.calls += 1
        return SimpleNamespace(executor=self.executor)

    @property
    def transcript(self) -> str:
        return "\n".join(str(getattr(record, "content", "")) for record in self.records)


@contextlib.contextmanager
def mock_operator(monkeypatch):
    """Route the edit endpoint's model work to a capture instead of a provider."""
    from local_operator.server.routes import chat

    capture = OperatorCapture()
    monkeypatch.setattr(chat, "create_operator", capture.factory)
    yield capture


@contextlib.contextmanager
def stub_radient_download(monkeypatch, metadata, files=None):
    """Make the hub pull hand back a locally built archive instead of a download."""
    from local_operator.clients.radient import RadientClient

    def download(self, agent_id, dest_path):
        build_archive(Path(dest_path), metadata, files)

    monkeypatch.setattr(RadientClient, "download_agent_from_marketplace", download)
    yield
