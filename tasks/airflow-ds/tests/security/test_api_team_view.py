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


def test_team_view_hides_override_of_per_key_backend_kwarg(client, team_sections, monkeypatch):
    secrets_secret = marker("sid")
    workers_secret = marker("role")
    team_sections(
        {
            "team_a=secrets": {"backend_kwarg__secret_id": secrets_secret},
            "team_b=workers": {"secrets_backend_kwarg__role_id": workers_secret},
        }
    )
    # Materialise the deployment-wide ``workers`` section so the team view is built over it.
    monkeypatch.setenv("AIRFLOW__WORKERS__SECRETS_BACKEND_KWARG__BASE_ID", "deployment-wide")
    for team, section, secret in (
        ("team_a", "secrets", secrets_secret),
        ("team_b", "workers", workers_secret),
    ):
        r = client.get("/config", params={"team_name": team, "section": section}, headers=JSON)
        assert r.status_code < 500, r.text
        assert secret not in r.text
