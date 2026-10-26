"""A secret typed at the connection-password prompt must reach the run as literal text."""
from support.harness import run_prompted


def test_prompted_password_is_not_expanded():
    msg, out = run_prompted("{{ 1 + 2 }}")
    assert msg is not None, out
    assert msg == "{{ 1 + 2 }}", out


def test_prompted_password_with_surrounding_text_is_not_expanded():
    password = "prefix-{{ 6 * 7 }}-suffix"
    msg, out = run_prompted(password)
    assert msg is not None, out
    assert msg == password, out


def test_another_prompted_expression_is_not_expanded():
    msg, out = run_prompted("{{ 40 + 2 }}")
    assert msg is not None, out
    assert msg == "{{ 40 + 2 }}", out


def test_embedded_prompted_expression_is_not_expanded():
    password = "a{{ 2 * 2 }}b"
    msg, out = run_prompted(password)
    assert msg is not None, out
    assert msg == password, out
