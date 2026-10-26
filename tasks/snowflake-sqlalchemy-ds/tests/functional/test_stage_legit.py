"""Legitimate stage and COPY option rendering keeps working."""

from sqlalchemy import Column, Integer, MetaData, Table, text

from conftest import compile_sql
from snowflake.sqlalchemy import (
    AWSBucket,
    AzureContainer,
    CopyIntoStorage,
    CreateStage,
    CSVFormatter,
    ExternalStage,
)


def _source_table():
    return Table("events", MetaData(), Column("id", Integer))


def test_plain_stage_reference():
    stage = ExternalStage(
        name="raw_stage", path="incoming", namespace="db.sch", file_format="csv_fmt"
    )
    sql = compile_sql(CopyIntoStorage(from_=_source_table(), into=stage))
    assert "@db.sch.raw_stage/incoming (file_format => csv_fmt)" in sql


def test_plain_create_stage():
    stage = ExternalStage(name="AZURE_STAGE", namespace="MY_DB.MY_SCHEMA")
    container = AzureContainer("myaccount", "my-container").credentials("token")
    sql = compile_sql(CreateStage(stage=stage, container=container))
    assert sql == (
        "CREATE STAGE MY_DB.MY_SCHEMA.AZURE_STAGE "
        "URL='azure://myaccount.blob.core.windows.net/my-container' "
        "CREDENTIALS=(AZURE_SAS_TOKEN='token')"
    )


def test_pattern_and_storage_integration_pass_through():
    copy_into = (
        CopyIntoStorage(from_=_source_table(), into=AWSBucket("backup"))
        .storage_integration("corp_integration")
        .pattern("'.*csv'")
    )
    sql = compile_sql(copy_into)
    assert "STORAGE_INTEGRATION = corp_integration" in sql
    assert "PATTERN = '.*csv'" in sql


def test_partition_by_expression_passes_through():
    copy_into = CopyIntoStorage(
        from_=_source_table(),
        into=ExternalStage(name="raw_stage"),
        partition_by=text("('YEAR=' || year)"),
    )
    assert "PARTITION BY ('YEAR=' || year)" in compile_sql(copy_into)


def test_copy_options_plain_values():
    copy_into = (
        CopyIntoStorage(
            from_=_source_table(),
            into=ExternalStage(name="raw_stage"),
            formatter=CSVFormatter().field_delimiter(","),
        )
        .force(True)
        .maxfilesize(50000000)
    )
    sql = compile_sql(copy_into)
    assert "FORCE = true" in sql
    assert "MAX_FILE_SIZE = 50000000" in sql
    assert "FIELD_DELIMITER=','" in sql
