"""Stage references in a COPY statement."""

from sqlalchemy import Column, Integer, MetaData, Table

from conftest import assert_identifier, compile_sql, payload_name
from snowflake.sqlalchemy import CopyIntoStorage, ExternalStage


def _source_table():
    return Table("events", MetaData(), Column("id", Integer))


def test_stage_name_in_copy_reference():
    value = payload_name("stage")
    copy_into = CopyIntoStorage(
        from_=_source_table(),
        into=ExternalStage(name=value, path="incoming"),
    )
    sql = compile_sql(copy_into)
    assert_identifier(sql, value)


def test_stage_namespace_in_copy_reference():
    value = payload_name("schema")
    copy_into = CopyIntoStorage(
        from_=_source_table(),
        into=ExternalStage(name="raw_stage", path="incoming", namespace=value),
    )
    sql = compile_sql(copy_into)
    assert_identifier(sql, value)
