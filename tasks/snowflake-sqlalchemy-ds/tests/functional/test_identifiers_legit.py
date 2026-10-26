"""Legitimate identifiers keep their current rendering."""

from sqlalchemy import Column, Integer, MetaData, String, Table, literal, select
from sqlalchemy.sql import quoted_name

from conftest import compile_sql
from snowflake.sqlalchemy import (
    CopyFormatter,
    CopyIntoStorage,
    CreateFileFormat,
    CSVFormatter,
    ExternalStage,
    MergeInto,
)


def test_lowercase_alias_stays_bare():
    sql = compile_sql(select(literal(1).label(quoted_name("myalias", quote=False))))
    assert "AS myalias" in sql
    assert '"myalias"' not in sql


def test_quoted_alias_stays_quoted():
    sql = compile_sql(select(literal(1).label(quoted_name("myalias", quote=True))))
    assert 'AS "myalias"' in sql


def test_dotted_schema_stays_bare():
    table = Table(
        "report",
        MetaData(),
        Column("c", Integer),
        schema=quoted_name("analytics.public", quote=False),
    )
    sql = compile_sql(select(table))
    assert "analytics.public.report" in sql


def test_uppercase_schema_stays_bare():
    table = Table(
        "report",
        MetaData(),
        Column("c", Integer),
        schema=quoted_name("TENANT1", quote=False),
    )
    sql = compile_sql(select(table))
    assert "TENANT1.report" in sql
    assert '"TENANT1"' not in sql


def test_schema_translate_token_passes_through():
    token = quoted_name("__[SCHEMA_tenant_key]", quote=False)
    sql = compile_sql(
        select(Table("report", MetaData(), Column("c", Integer), schema=token))
    )
    assert "__[SCHEMA_tenant_key].report" in sql
    assert '"__[SCHEMA_tenant_key]"' not in sql


def test_plain_merge_keys_stay_bare():
    users = Table(
        "users", MetaData(), Column("id", Integer), Column("name", String)
    )
    staging = Table(
        "staging_users", MetaData(), Column("id", Integer), Column("name", String)
    )
    merge = MergeInto(users, staging, users.c.id == staging.c.id)
    merge.when_not_matched_then_insert().values(id=staging.c.id, name=staging.c.name)
    sql = compile_sql(merge)
    assert "INSERT (id, name) VALUES" in sql
    assert '"name"' not in sql


def test_plain_format_names_stay_bare():
    sql = compile_sql(CreateFileFormat("csv_format", CSVFormatter()))
    assert "CREATE FILE FORMAT csv_format " in sql
    copy_into = CopyIntoStorage(
        from_=Table("events", MetaData(), Column("id", Integer)),
        into=ExternalStage(name="s", path="p", file_format="csv_format"),
    )
    assert "(file_format => csv_format)" in compile_sql(copy_into)
    copy_into = CopyIntoStorage(
        from_=Table("events", MetaData(), Column("id", Integer)),
        into=ExternalStage(name="s", path="p"),
        formatter=CopyFormatter(format_name="csv_format"),
    )
    assert "(format_name = csv_format)" in compile_sql(copy_into)
