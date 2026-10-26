"""Legitimate use of the external-volume and tag helpers keeps working."""

from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.schema import CreateTable

from conftest import compile_sql
from snowflake.sqlalchemy import (
    CreateExternalVolume,
    ExternalVolumeLocation,
    SnowflakeTable,
    TagOption,
)


def test_plain_external_volume():
    volume = CreateExternalVolume(
        "corp_volume",
        [
            ExternalVolumeLocation(
                "primary",
                "s3://corp-iceberg/warehouse",
                credentials={"AWS_KEY_ID": "key", "AWS_SECRET_KEY": "secret"},
            )
        ],
        allowlist=["corp-iceberg.s3.amazonaws.com"],
        comment="iceberg storage",
    )
    assert compile_sql(volume) == (
        "CREATE EXTERNAL VOLUME corp_volume STORAGE_LOCATIONS = "
        "((NAME = primary LOCATION = 's3://corp-iceberg/warehouse' "
        "STORAGE_PROVIDER = 'S3' CREDENTIALS=(AWS_KEY_ID='key' AWS_SECRET_KEY='secret'))) "
        "ALLOWLIST = ('corp-iceberg.s3.amazonaws.com') COMMENT = 'iceberg storage'"
    )


def test_plain_table_tags():
    table = SnowflakeTable(
        "events",
        MetaData(),
        Column("id", Integer),
        snowflake_tag=TagOption({"owner": "analytics", "env": "prod"}),
    )
    sql = compile_sql(CreateTable(table))
    assert "TAG (owner = 'analytics', env = 'prod')" in sql
