"""Legitimate configuration reads keep working exactly as before."""
from __future__ import annotations

from conftest import HIDDEN, marker, options_of

JSON = {"Accept": "application/json"}


def test_team_non_sensitive_option_readable(client, team_sections):
    team_sections({"team_a=core": {"parallelism": "77"}})
    r = client.get("/config/section/team_a=core/option/parallelism", headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json()) == {"team_a=core": {"parallelism": "77"}}


def test_team_with_dash_non_sensitive_option_readable(client, team_sections):
    team_sections({"data-eng=core": {"dag_concurrency_note": "kept-as-is"}})
    r = client.get("/config/section/data-eng=core/option/dag_concurrency_note", headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json())["data-eng=core"]["dag_concurrency_note"] == "kept-as-is"


def test_base_sensitive_option_still_hidden(client):
    r = client.get("/config/section/database/option/sql_alchemy_conn", headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json())["database"]["sql_alchemy_conn"] == HIDDEN


def test_base_non_sensitive_option_readable(client, team_sections):
    from airflow.configuration import conf

    r = client.get("/config/section/core/option/parallelism", headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json())["core"]["parallelism"] == conf.get("core", "parallelism")


def test_missing_option_still_404(client):
    r = client.get("/config/section/team_a=core/option/not_an_option_at_all", headers=JSON)
    assert r.status_code == 404


def test_listing_keeps_team_non_sensitive_values(client, team_sections, monkeypatch):
    value = marker("note")
    team_sections({"team_a=core": {"parallelism": "77"}})
    monkeypatch.setenv("AIRFLOW__TEAM_A___CORE__DEFAULT_TIMEZONE", value)
    r = client.get("/config", headers=JSON)
    assert r.status_code == 200
    sections = options_of(r.json())
    assert sections["team_a=core"]["parallelism"] == "77"
    assert value in r.text


def test_listing_keeps_base_values(client):
    from airflow.configuration import conf

    r = client.get("/config", headers=JSON)
    assert r.status_code == 200
    sections = options_of(r.json())
    assert sections["database"]["sql_alchemy_conn"] == HIDDEN
    assert sections["core"]["parallelism"] == conf.get("core", "parallelism")


def test_listing_keeps_team_non_kwarg_secrets_option(client, monkeypatch):
    monkeypatch.setenv("AIRFLOW__TEAM_A___SECRETS__USE_CACHE", "True")
    r = client.get("/config", headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json()).get("team_a", {}).get("_secrets__use_cache") == "True"


def test_team_view_shows_team_overrides(client, team_sections):
    team_sections({"team_a=core": {"parallelism": "77"}})
    r = client.get("/config", params={"team_name": "team_a", "section": "core"}, headers=JSON)
    assert r.status_code == 200
    core = options_of(r.json())["core"]
    assert core["parallelism"] == "77"


def test_team_view_keeps_values_not_overridden(client, team_sections):
    from airflow.configuration import conf

    team_sections({"team_a=core": {"parallelism": "77"}})
    r = client.get("/config", params={"team_name": "team_a", "section": "core"}, headers=JSON)
    assert r.status_code == 200
    core = options_of(r.json())["core"]
    assert core["dags_folder"] == conf.get("core", "dags_folder")
    assert core["fernet_key"] == HIDDEN


def test_team_view_for_team_without_overrides(client):
    from airflow.configuration import conf

    r = client.get("/config", params={"team_name": "nobody", "section": "core"}, headers=JSON)
    assert r.status_code == 200
    assert options_of(r.json())["core"]["parallelism"] == conf.get("core", "parallelism")
