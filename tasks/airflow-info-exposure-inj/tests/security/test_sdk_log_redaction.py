"""A task worker's own log redaction must cover team scoped sensitive values too."""
from __future__ import annotations

from conftest import marker, sdk_redacted_lines, write_cfg


def test_team_section_value_redacted_in_worker_logs(tmp_path):
    value = "postgresql://team_a:" + marker("pw") + "@db/airflow"
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn = {value}
        """,
    )
    assert value not in sdk_redacted_lines(cfg, [value])


def test_team_env_var_value_redacted_in_worker_logs(tmp_path):
    value = marker("jwt")
    cfg = write_cfg(tmp_path, "")
    out = sdk_redacted_lines(cfg, [value], env={"AIRFLOW__TEAM_A___API__SECRET_KEY": value})
    assert value not in out
