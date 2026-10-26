"""CREATE TABLE option values rendered by the options subsystem."""

from sqlalchemy import Column, Integer, MetaData, String, literal, select, text
from sqlalchemy.schema import CreateTable

from conftest import assert_identifier, assert_literal, compile_sql, payload_literal, payload_name
from snowflake.sqlalchemy import (
    ClusterByOption,
    DynamicTable,
    IcebergTable,
    SnowflakeTable,
    TargetLagOption,
    TimeUnit,
)


def _columns():
    return Column("id", Integer), Column("name", String)


def test_dynamic_table_warehouse():
    value = payload_name("wh")
    table = DynamicTable(
        "events",
        MetaData(),
        *_columns(),
        warehouse=value,
        target_lag=TargetLagOption(1, TimeUnit.HOURS),
        as_query="SELECT 1",
    )
    sql = compile_sql(CreateTable(table))
    assert_identifier(sql, value)


def test_iceberg_external_volume_literal():
    value = payload_literal("vol")
    table = IcebergTable(
        "events", MetaData(), *_columns(), external_volume=value, base_location="root"
    )
    sql = compile_sql(CreateTable(table))
    assert_literal(sql, value)


def test_iceberg_base_location_literal():
    value = "root/" + payload_literal("loc")
    table = IcebergTable(
        "events", MetaData(), *_columns(), external_volume="vol", base_location=value
    )
    sql = compile_sql(CreateTable(table))
    assert_literal(sql, value)


def test_cluster_by_name():
    value = payload_name("col")
    table = SnowflakeTable(
        "events", MetaData(), *_columns(), cluster_by=ClusterByOption(value)
    )
    sql = compile_sql(CreateTable(table))
    assert_identifier(sql, value)


def test_as_query_compiles_a_bound_literal_with_the_dialect():
    value = payload_literal("q")
    table = SnowflakeTable(
        "events",
        MetaData(),
        *_columns(),
        as_query=select(literal(value).label("v")),
    )
    sql = compile_sql(CreateTable(table))
    assert_literal(sql, value)
