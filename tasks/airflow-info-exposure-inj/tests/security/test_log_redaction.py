"""Log redaction set up at process start must cover team scoped sensitive values."""
from __future__ import annotations

from conftest import marker, redacted_lines, write_cfg


def test_team_section_value_redacted(tmp_path):
    value = "postgresql://team_a:" + marker("pw") + "@db/airflow"
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn = {value}
        """,
    )
    assert value not in redacted_lines(cfg, [value])


def test_team_env_var_value_redacted(tmp_path):
    value = marker("jwt")
    cfg = write_cfg(tmp_path, "")
    out = redacted_lines(cfg, [value], env={"AIRFLOW__TEAM_A___API_AUTH__JWT_SECRET": value})
    assert value not in out


def test_team_env_var_backend_kwarg_redacted(tmp_path):
    value = marker("role")
    cfg = write_cfg(tmp_path, "")
    out = redacted_lines(cfg, [value], env={"AIRFLOW__TEAM_A___SECRETS__BACKEND_KWARG__ROLE_ID": value})
    assert value not in out
