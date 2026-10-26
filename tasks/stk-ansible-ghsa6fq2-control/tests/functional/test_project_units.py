"""The project's own unit tests for the affected area keep passing."""
from support.harness import run_project_unit_tests

PATHS = [
    "test/units/cli/test_cli.py",
    "test/units/playbook/test_base.py",
    "test/units/module_utils/test_text.py",
]


def test_project_unit_tests_for_affected_area():
    returncode, output = run_project_unit_tests(PATHS)
    assert returncode == 0, output[-4000:]
