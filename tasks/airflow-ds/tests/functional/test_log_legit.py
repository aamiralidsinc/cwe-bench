"""Log redaction keeps masking base values and leaves non-sensitive values readable."""
from __future__ import annotations

from conftest import marker, redacted_lines, write_cfg


def test_base_sensitive_value_still_redacted(tmp_path):
    value = marker("fernet")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [api]
        secret_key = {value}
        """,
    )
    assert value not in redacted_lines(cfg, [value])


def test_team_non_sensitive_value_not_redacted(tmp_path):
    value = marker("tz")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=core]
        default_timezone = {value}
        """,
    )
    assert value in redacted_lines(cfg, [value])


def test_base_per_key_backend_kwarg_env_value_still_redacted(tmp_path):
    value = marker("role")
    cfg = write_cfg(tmp_path, "")
    out = redacted_lines(
        cfg, [value], env={"AIRFLOW__SECRETS__BACKEND_KWARG__ROLE_ID": value}
    )
    assert value not in out


def test_team_non_sensitive_env_value_not_redacted(tmp_path):
    value = marker("tz")
    cfg = write_cfg(tmp_path, "")
    out = redacted_lines(
        cfg, [value], env={"AIRFLOW__TEAM_A___CORE__DEFAULT_TIMEZONE": value}
    )
    assert value in out
