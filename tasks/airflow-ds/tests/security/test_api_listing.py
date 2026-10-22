"""GET /config must not reveal team scoped sensitive values, however they are supplied."""
from __future__ import annotations

from conftest import marker

JSON = {"Accept": "application/json"}


def _listing(client, **params):
    r = client.get("/config", params=params, headers=JSON)
    assert r.status_code < 500, r.text
    return r.text


def test_team_section_value_not_in_listing(client, team_sections):
    secret = marker("pw")
    team_sections({"team_a=database": {"sql_alchemy_conn": f"postgresql://team_a:{secret}@db/airflow"}})
    assert secret not in _listing(client)


def test_team_section_value_not_in_section_filtered_listing(client, team_sections):
    secret = marker("fk")
    team_sections({"team_a=core": {"fernet_key": secret, "parallelism": "64"}})
    assert secret not in _listing(client, section="team_a=core")


def test_team_section_command_and_secret_entries_not_in_listing(client, team_sections):
    cmd_secret, path_secret = marker("cmd"), marker("path")
    team_sections(
        {
            "team_a=database": {
                "sql_alchemy_conn_cmd": f"cat /run/secrets/{cmd_secret}",
                "sql_alchemy_conn_secret": f"teams/team_a/{path_secret}",
            }
        }
    )
    text = _listing(client)
    assert cmd_secret not in text
    assert path_secret not in text


def test_team_name_with_dot_not_in_listing(client, team_sections):
    secret = marker("pw")
    team_sections({"data.eng=database": {"sql_alchemy_conn": f"postgresql://data:{secret}@db/airflow"}})
    assert secret not in _listing(client)


def test_team_name_containing_separator_not_in_listing(client, team_sections):
    secret = marker("pw")
    team_sections({"a=b=database": {"sql_alchemy_conn": f"postgresql://a:{secret}@db/airflow"}})
    assert secret not in _listing(client)


def test_team_name_containing_separator_section_filtered_not_in_listing(client, team_sections):
    secret = marker("fk")
    team_sections({"a=b=core": {"fernet_key": secret, "parallelism": "64"}})
    assert secret not in _listing(client, section="a=b=core")


def test_team_env_var_value_not_in_listing(client, monkeypatch):
    secret = marker("env")
    monkeypatch.setenv("AIRFLOW__TEAM_A___DATABASE__SQL_ALCHEMY_CONN", f"postgresql://u:{secret}@h/db")
    assert secret not in _listing(client)


def test_team_env_var_with_underscored_team_name_not_in_listing(client, monkeypatch):
    secret = marker("env")
    monkeypatch.setenv("AIRFLOW__ML_PLATFORM___CORE__FERNET_KEY", secret)
    assert secret not in _listing(client)


def test_team_env_var_command_not_in_listing(client, monkeypatch):
    secret = marker("cmd")
    monkeypatch.setenv("AIRFLOW__TEAM_A___API__SECRET_KEY_CMD", f"cat /run/secrets/{secret}")
    assert secret not in _listing(client)
