"""CLI output for legitimate use stays as it is today."""
from __future__ import annotations

from conftest import marker, run_airflow, write_cfg


def test_config_list_shows_team_non_sensitive_values(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [team_a=core]
        parallelism = 77
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "parallelism = 77" in proc.stdout


def test_config_list_show_values_without_hiding_shows_team_value(tmp_path):
    secret = marker("fk")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=core]
        fernet_key = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert f"fernet_key = {secret}" in proc.stdout


def test_get_value_prints_value(tmp_path):
    secret = marker("pw")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn = postgresql://u:{secret}@h/db
        """,
    )
    proc = run_airflow(cfg, "config", "get-value", "team_a=database", "sql_alchemy_conn")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().splitlines()[-1] == f"postgresql://u:{secret}@h/db"


def test_get_value_hide_sensitive_keeps_non_sensitive(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [team_a=core]
        parallelism = 77
        """,
    )
    proc = run_airflow(cfg, "config", "get-value", "team_a=core", "parallelism", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().splitlines()[-1] == "77"


def test_config_list_keeps_deployment_wide_per_key_backend_kwarg(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [secrets]
        backend_kwarg__role_id = deployment-wide-note
        """,
    )
    proc = run_airflow(
        cfg, "config", "list", "--section", "secrets", "--show-values", "--hide-sensitive"
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "backend_kwarg__role_id = deployment-wide-note" in proc.stdout


def test_get_value_hide_sensitive_keeps_deployment_wide_per_key_value(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [secrets]
        backend_kwarg__role_id = deployment-wide-note
        """,
    )
    proc = run_airflow(
        cfg, "config", "get-value", "secrets", "backend_kwarg__role_id", "--hide-sensitive"
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().splitlines()[-1] == "deployment-wide-note"


def test_config_list_keeps_team_secrets_non_kwarg_values(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [team_a=secrets]
        note = kept-as-is
        """,
    )
    proc = run_airflow(
        cfg, "config", "list", "--section", "team_a=secrets", "--show-values", "--hide-sensitive"
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "note = kept-as-is" in proc.stdout


def test_get_value_hide_sensitive_keeps_team_non_kwarg_secrets_value(tmp_path):
    cfg = write_cfg(
        tmp_path,
        """\
        [team_a=secrets]
        note = kept-as-is
        """,
    )
    proc = run_airflow(
        cfg, "config", "get-value", "team_a=secrets", "note", "--hide-sensitive"
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().splitlines()[-1] == "kept-as-is"


def test_get_value_hide_sensitive_hides_base_value(tmp_path):
    cfg = write_cfg(tmp_path, "")
    proc = run_airflow(cfg, "config", "get-value", "database", "sql_alchemy_conn", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip().splitlines()[-1] == "< hidden >"
