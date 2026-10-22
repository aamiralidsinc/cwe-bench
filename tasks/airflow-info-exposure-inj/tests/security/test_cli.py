"""`airflow config list --hide-sensitive` and `airflow config get-value --hide-sensitive`."""
from __future__ import annotations

from conftest import marker, run_airflow, write_cfg


def test_config_list_hides_team_section_value(tmp_path):
    secret = marker("pw")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn = postgresql://team_a:{secret}@db/airflow
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert "[team_a=database]" in proc.stdout, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_config_list_section_hides_team_section_value(tmp_path):
    secret = marker("fk")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=core]
        fernet_key = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--section", "team_a=core", "--show-values", "--hide-sensitive")
    assert "[team_a=core]" in proc.stdout, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_get_value_hide_sensitive_hides_team_section_value(tmp_path):
    secret = marker("pw")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn = postgresql://team_a:{secret}@db/airflow
        """,
    )
    proc = run_airflow(cfg, "config", "get-value", "team_a=database", "sql_alchemy_conn", "--hide-sensitive")
    assert secret not in proc.stdout + proc.stderr
