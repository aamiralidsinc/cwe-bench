"""Legitimate password and template behaviour that must keep working."""
import tempfile

from support.harness import run_plain, run_prompted, write_password_file


def test_ordinary_prompted_password_is_used_verbatim():
    msg, out = run_prompted("correct-horse")
    assert msg == "correct-horse", out


def test_non_ascii_prompted_password_is_used_verbatim():
    msg, out = run_prompted("pässwörd")
    assert msg == "pässwörd", out


def test_password_file_trailing_newline_is_trimmed():
    with tempfile.TemporaryDirectory() as workdir:
        path = write_password_file(workdir, "hunter2\n")
        msg, out = run_plain(extra_args=["--connection-password-file", path])
    assert msg == "hunter2", out


def test_environment_password_surrounding_space_is_trimmed():
    msg, out = run_plain(extra_env={"ANSIBLE_CONNECTION_PASSWORD": "  hunter2  "})
    assert msg == "hunter2", out


def test_ordinary_template_still_renders():
    msg, out = run_plain(arg="msg={{ 1 + 2 }}")
    assert msg == "3", out


def test_ordinary_template_still_renders_next_to_a_password():
    msg, out = run_prompted("pass", arg="msg={{ 1 + 2 }}")
    assert msg == "3", out


def test_prompted_password_wins_over_password_file():
    with tempfile.TemporaryDirectory() as workdir:
        path = write_password_file(workdir, "filepass\n")
        msg, out = run_prompted("promptpass", extra_args=["--connection-password-file", path])
    assert msg == "promptpass", out


def test_password_file_wins_over_environment():
    with tempfile.TemporaryDirectory() as workdir:
        path = write_password_file(workdir, "filepass\n")
        msg, out = run_plain(
            extra_args=["--connection-password-file", path],
            extra_env={"ANSIBLE_CONNECTION_PASSWORD": "envpass"},
        )
    assert msg == "filepass", out
