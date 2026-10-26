"""Fixtures for the pristine copy of the project's own compilation tests.

Only the pure-compilation fixture is provided; the project's own conftest opens a live
Snowflake connection in a session fixture, which these tests do not need.
"""

import pytest

from snowflake.sqlalchemy import dialect


@pytest.fixture(scope="session")
def sql_compiler():
    return lambda sql_command: str(
        sql_command.compile(
            dialect=dialect(),
            compile_kwargs={"literal_binds": True, "deterministic": True},
        )
    ).replace("\n", "")
