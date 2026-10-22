"""Callers that ask for real values (display_sensitive=True) still receive them."""
from __future__ import annotations

from conftest import HIDDEN, marker


def test_display_sensitive_returns_real_team_values(team_sections, monkeypatch):
    from airflow.configuration import conf

    file_secret, env_secret = marker("fk"), marker("env")
    team_sections({"team_a=core": {"fernet_key": file_secret}})
    monkeypatch.setenv("AIRFLOW__TEAM_A___API__SECRET_KEY", env_secret)
    real = conf.as_dict(display_sensitive=True)
    assert real["team_a=core"]["fernet_key"] == file_secret
    assert env_secret in {v for options in real.values() for v in options.values()}


def test_masked_listing_still_marks_hidden(team_sections):
    from airflow.configuration import conf

    team_sections({"team_a=core": {"fernet_key": marker("fk"), "parallelism": "77"}})
    masked = conf.as_dict(display_sensitive=False)
    assert masked["team_a=core"]["parallelism"] == "77"
    assert masked["core"]["fernet_key"] in (HIDDEN, "")


def test_display_sensitive_returns_real_team_per_key_value(team_sections):
    from airflow.configuration import conf

    secret = marker("sid")
    team_sections({"team_a=secrets": {"backend_kwarg__secret_id": secret}})
    real = conf.as_dict(display_sensitive=True)
    assert real["team_a=secrets"]["backend_kwarg__secret_id"] == secret


def test_team_lookup_returns_real_value(team_sections):
    from airflow.configuration import conf

    secret = marker("pw")
    team_sections({"team_a=database": {"sql_alchemy_conn": f"postgresql://u:{secret}@h/db"}})
    assert conf.get("database", "sql_alchemy_conn", team_name="team_a") == f"postgresql://u:{secret}@h/db"
