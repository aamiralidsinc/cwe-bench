"""GET /config/section/{section}/option/{option} must not reveal a team scoped sensitive value."""
from __future__ import annotations

from conftest import HIDDEN, marker

JSON = {"Accept": "application/json"}


def _assert_not_revealed(response, secret: str) -> None:
    assert response.status_code < 500, response.text
    assert secret not in response.text


def test_team_section_sensitive_value_not_revealed(client, team_sections):
    secret = marker("pw")
    team_sections({"team_a=database": {"sql_alchemy_conn": f"postgresql://team_a:{secret}@db/airflow"}})
    r = client.get("/config/section/team_a=database/option/sql_alchemy_conn", headers=JSON)
    _assert_not_revealed(r, secret)


def test_team_section_sensitive_value_hidden_text_format(client, team_sections):
    secret = marker("fk")
    team_sections({"team_a=core": {"fernet_key": secret}})
    r = client.get("/config/section/team_a=core/option/fernet_key", headers={"Accept": "text/plain"})
    _assert_not_revealed(r, secret)


def test_team_name_with_dash_not_revealed(client, team_sections):
    secret = marker("sk")
    team_sections({"data-eng=api": {"secret_key": secret}})
    r = client.get("/config/section/data-eng=api/option/secret_key", headers=JSON)
    _assert_not_revealed(r, secret)


def test_team_section_command_entry_not_revealed(client, team_sections):
    secret = marker("cmd")
    team_sections({"team_a=database": {"sql_alchemy_conn_cmd": f"cat /run/secrets/{secret}"}})
    r = client.get("/config/section/team_a=database/option/sql_alchemy_conn_cmd", headers=JSON)
    _assert_not_revealed(r, secret)


def test_team_env_var_spelling_not_revealed(client, monkeypatch):
    secret = marker("env")
    monkeypatch.setenv("AIRFLOW__TEAM_A___API_AUTH__JWT_SECRET", secret)
    r = client.get("/config/section/team_a/option/_api_auth__jwt_secret", headers=JSON)
    _assert_not_revealed(r, secret)
