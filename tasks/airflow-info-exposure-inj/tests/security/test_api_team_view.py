"""GET /config?team_name=... (the configuration a team runs with) must hide sensitive overrides."""
from __future__ import annotations

from conftest import marker

JSON = {"Accept": "application/json"}


def _team_view(client, team, section):
    r = client.get("/config", params={"team_name": team, "section": section}, headers=JSON)
    assert r.status_code < 500, r.text
    return r.text


def test_team_view_hides_override_of_unset_sensitive_option(client, team_sections):
    secret = marker("dsn")
    team_sections({"team_a=sentry": {"sentry_dsn": f"https://{secret}@o1.ingest.example/7"}})
    assert secret not in _team_view(client, "team_a", "sentry")


def test_team_view_hides_override_of_backend_kwargs(client, team_sections):
    secret = marker("tok")
    team_sections({"team_a=secrets": {"backend_kwargs": f'{{"token": "{secret}"}}'}})
    assert secret not in _team_view(client, "team_a", "secrets")
