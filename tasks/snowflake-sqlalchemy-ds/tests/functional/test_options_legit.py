"""Legitimate CREATE TABLE option values keep their current rendering."""

from sqlalchemy import Column, Integer, MetaData, String, literal, select, text
from sqlalchemy.schema import CreateTable

from conftest import compile_sql
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


def test_dynamic_table_plain_warehouse():
    table = DynamicTable(
        "events",
        MetaData(),
        *_columns(),
        warehouse="analytics_wh",
        target_lag=TargetLagOption(1, TimeUnit.HOURS),
        as_query="SELECT 1",
    )
    sql = compile_sql(CreateTable(table))
    assert "WAREHOUSE = analytics_wh" in sql
    assert "TARGET_LAG = '1 hours'" in sql


def test_iceberg_plain_values():
    table = IcebergTable(
        "events",
        MetaData(),
        *_columns(),
        external_volume="corp_volume",
        base_location="root/path",
    )
    sql = compile_sql(CreateTable(table))
    assert "EXTERNAL_VOLUME = 'corp_volume'" in sql
    assert "BASE_LOCATION = 'root/path'" in sql
    assert "CATALOG = 'SNOWFLAKE'" in sql


def test_cluster_by_plain_names_and_expression():
    table = SnowflakeTable(
        "events",
        MetaData(),
        *_columns(),
        cluster_by=ClusterByOption("id", "name", text("id > 0")),
    )
    sql = compile_sql(CreateTable(table))
    assert "CLUSTER BY (id, name, id > 0)" in sql


def test_as_query_string_is_passed_through():
    table = SnowflakeTable(
        "events",
        MetaData(),
        *_columns(),
        as_query="SELECT * FROM source",
    )
    assert "AS SELECT * FROM source" in compile_sql(CreateTable(table))


def test_as_query_selectable_renders_plain_literals():
    table = SnowflakeTable(
        "events",
        MetaData(),
        *_columns(),
        as_query=select(literal("plain").label("v")),
    )
    sql = compile_sql(CreateTable(table))
    assert "AS SELECT 'plain' AS v" in sql
