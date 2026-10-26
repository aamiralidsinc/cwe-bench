"""Table tag option."""

from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.schema import CreateTable

from conftest import assert_identifier, assert_literal, compile_sql, payload_plain_quote
from snowflake.sqlalchemy import SnowflakeTable, TagOption


def _table(tags):
    return SnowflakeTable(
        "events",
        MetaData(),
        Column("id", Integer),
        snowflake_tag=TagOption(tags),
    )


def test_tag_name_identifier():
    value = "owner, PWNED_MARKER"
    sql = compile_sql(CreateTable(_table({value: "analytics"})))
    assert_identifier(sql, value)


def test_tag_value_literal():
    value = payload_plain_quote("analytics")
    sql = compile_sql(CreateTable(_table({"owner": value})))
    assert_literal(sql, value)


def test_second_tag_value_literal():
    value = payload_plain_quote("prod")
    sql = compile_sql(CreateTable(_table({"owner": "analytics", "env": value})))
    assert_literal(sql, value)
