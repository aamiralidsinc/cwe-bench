"""Per-key secrets backend parameters stay hidden when they are set for one team."""
from __future__ import annotations

from conftest import marker

JSON = {"Accept": "application/json"}


def test_team_env_backend_kwarg_not_in_listing(client, monkeypatch):
    secret = marker("role")
    monkeypatch.setenv("AIRFLOW__TEAM_A___SECRETS__BACKEND_KWARG__ROLE_ID", secret)
    r = client.get("/config", headers=JSON)
    assert r.status_code < 500, r.text
    assert secret not in r.text


def test_team_section_backend_kwarg_not_in_listing(client, team_sections):
    secret = marker("sid")
    team_sections({"team_a=secrets": {"backend_kwarg__secret_id": secret}})
    r = client.get("/config", headers=JSON)
    assert r.status_code < 500, r.text
    assert secret not in r.text


def test_team_env_workers_backend_kwarg_not_in_listing(client, monkeypatch):
    secret = marker("role")
    monkeypatch.setenv("AIRFLOW__TEAM_A___WORKERS__SECRETS_BACKEND_KWARG__ROLE_ID", secret)
    r = client.get("/config", headers=JSON)
    assert r.status_code < 500, r.text
    assert secret not in r.text


def test_team_section_workers_backend_kwarg_not_in_listing(client, team_sections):
    secret = marker("role")
    team_sections({"team_a=workers": {"secrets_backend_kwarg__role_id": secret}})
    r = client.get("/config", headers=JSON)
    assert r.status_code < 500, r.text
    assert secret not in r.text


def test_team_name_containing_separator_backend_kwarg_not_in_listing(client, team_sections):
    secret = marker("sid")
    team_sections({"a=b=secrets": {"backend_kwarg__secret_id": secret}})
    r = client.get("/config", headers=JSON)
    assert r.status_code < 500, r.text
    assert secret not in r.text
