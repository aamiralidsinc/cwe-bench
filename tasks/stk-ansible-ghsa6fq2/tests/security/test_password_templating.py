"""A secret supplied to the command line must reach the run as literal text."""
import os
import tempfile

from support.harness import run_plain, run_prompted, write_password_file


def test_prompted_password_is_not_expanded():
    msg, out = run_prompted("{{ 1 + 2 }}")
    assert msg is not None, out
    assert msg == "{{ 1 + 2 }}", out


def test_prompted_password_with_surrounding_text_is_not_expanded():
    password = "prefix-{{ 6 * 7 }}-suffix"
    msg, out = run_prompted(password)
    assert msg is not None, out
    assert msg == password, out


def test_file_password_is_not_expanded():
    with tempfile.TemporaryDirectory() as workdir:
        path = write_password_file(workdir, "{{ 1 + 2 }}\r\n")
        msg, out = run_plain(extra_args=["--connection-password-file", path])
    assert msg is not None, out
    assert msg.strip() == "{{ 1 + 2 }}", out


def test_file_password_with_non_ascii_text_is_not_expanded():
    password = "pä{{ 1 + 2 }}"
    with tempfile.TemporaryDirectory() as workdir:
        path = write_password_file(workdir, password + "\n")
        msg, out = run_plain(extra_args=["--connection-password-file", path])
    assert msg is not None, out
    assert msg == password, out


def test_environment_password_is_not_expanded():
    msg, out = run_plain(extra_env={"ANSIBLE_CONNECTION_PASSWORD": "  {{ 1 + 2 }}  "})
    assert msg is not None, out
    assert msg.strip() == "{{ 1 + 2 }}", out
