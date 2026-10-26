"""Identifier positions in the preparer, MERGE keys and format names."""

from sqlalchemy import Column, Integer, MetaData, String, Table, literal, select
from sqlalchemy.sql import quoted_name

from conftest import assert_identifier, compile_sql, payload_name
from snowflake.sqlalchemy import (
    CopyFormatter,
    CopyIntoStorage,
    CreateFileFormat,
    CSVFormatter,
    ExternalStage,
    MergeInto,
)


def test_label_wrapped_in_quote_false():
    value = payload_name("alias")
    sql = compile_sql(select(literal(1).label(quoted_name(value, quote=False))))
    assert_identifier(sql, value)


def test_schema_wrapped_in_quote_false():
    value = payload_name("tenant")
    table = Table(
        "report",
        MetaData(),
        Column("c", Integer),
        schema=quoted_name(value, quote=False),
    )
    sql = compile_sql(select(table))
    assert_identifier(sql, value)


def _merge():
    users = Table(
        "users",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    staging = Table(
        "staging_users",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("name", String),
    )
    return users, staging


def test_merge_insert_column_key():
    users, staging = _merge()
    value = payload_name("col")
    merge = MergeInto(users, staging, users.c.id == staging.c.id)
    merge.when_not_matched_then_insert().values(**{value: staging.c.id})
    sql = compile_sql(merge)
    assert_identifier(sql, value)


def test_merge_update_column_key():
    users, staging = _merge()
    value = payload_name("col")
    merge = MergeInto(users, staging, users.c.id == staging.c.id)
    merge.when_matched_then_update().values(**{value: staging.c.id})
    sql = compile_sql(merge)
    assert_identifier(sql, value)


def test_create_file_format_name():
    value = payload_name("fmt")
    sql = compile_sql(CreateFileFormat(value, CSVFormatter()))
    assert_identifier(sql, value)


def test_copy_format_name():
    value = payload_name("fmt")
    copy_into = CopyIntoStorage(
        from_=ExternalStage(name="s", path="p"),
        into=Table("events", MetaData(), Column("id", Integer)),
        formatter=CopyFormatter(format_name=value),
    )
    sql = compile_sql(copy_into)
    assert_identifier(sql, value)


def test_external_stage_file_format_name():
    value = payload_name("fmt")
    stage = ExternalStage(name="s", path="p", file_format=value)
    copy_into = CopyIntoStorage(
        from_=Table("events", MetaData(), Column("id", Integer)),
        into=stage,
    )
    sql = compile_sql(copy_into)
    assert_identifier(sql, value)
