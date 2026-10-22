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


def test_config_list_hides_team_name_containing_separator(tmp_path):
    secret = marker("pw")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [a=b=database]
        sql_alchemy_conn = postgresql://a:{secret}@db/airflow
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert "[a=b=database]" in proc.stdout, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_config_list_hides_team_command_and_secret_entries(tmp_path):
    cmd_secret, path_secret = marker("cmd"), marker("path")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=database]
        sql_alchemy_conn_cmd = cat /run/secrets/{cmd_secret}
        sql_alchemy_conn_secret = teams/team_a/{path_secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert cmd_secret not in proc.stdout + proc.stderr
    assert path_secret not in proc.stdout + proc.stderr


def test_config_list_hides_team_per_key_backend_kwarg(tmp_path):
    secret = marker("sid")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=secrets]
        backend_kwarg__secret_id = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_config_list_team_per_key_backend_kwarg_hidden_with_listing(tmp_path):
    """Concealing keeps the entry listed with the exact hidden text and the command succeeds."""
    secret = marker("sid")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=secrets]
        backend_kwarg__secret_id = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "backend_kwarg__secret_id = < hidden >" in proc.stdout
    assert secret not in proc.stdout + proc.stderr


def test_config_list_hides_team_workers_per_key_backend_kwarg(tmp_path):
    secret = marker("role")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=workers]
        secrets_backend_kwarg__role_id = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_config_list_hides_team_name_containing_separator_per_key_backend_kwarg(tmp_path):
    secret = marker("sid")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [a=b=secrets]
        backend_kwarg__secret_id = {secret}
        """,
    )
    proc = run_airflow(cfg, "config", "list", "--show-values", "--hide-sensitive")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert secret not in proc.stdout + proc.stderr


def test_get_value_hide_sensitive_hides_team_per_key_backend_kwarg(tmp_path):
    secret = marker("sid")
    cfg = write_cfg(
        tmp_path,
        f"""\
        [team_a=secrets]
        backend_kwarg__secret_id = {secret}
        """,
    )
    proc = run_airflow(
        cfg, "config", "get-value", "team_a=secrets", "backend_kwarg__secret_id", "--hide-sensitive"
    )
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
