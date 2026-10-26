"""CREATE STAGE renders a storage container; every part must stay inert."""

from conftest import (
    assert_identifier,
    assert_literal,
    compile_sql,
    payload_literal,
    payload_name,
    payload_plain_quote,
)
from snowflake.sqlalchemy import AWSBucket, AzureContainer, CreateStage, ExternalStage


def _stage(**kwargs):
    return ExternalStage(name=kwargs.pop("name", "raw_stage"), **kwargs)


def test_create_stage_container_uri():
    path = "incoming/" + payload_plain_quote("p")
    container = AzureContainer("account", "container", path)
    sql = compile_sql(CreateStage(container, _stage()))
    assert_literal(sql, "azure://account.blob.core.windows.net/container/" + path)


def test_create_stage_container_credential():
    value = payload_plain_quote("token")
    container = AzureContainer("account", "container").credentials(value)
    sql = compile_sql(CreateStage(container, _stage()))
    assert_literal(sql, value)


def test_create_stage_container_path_backslash():
    path = "incoming/" + payload_literal("p")
    container = AWSBucket("corp-bucket", path)
    sql = compile_sql(CreateStage(container, _stage()))
    assert_literal(sql, "s3://corp-bucket/" + path)


def test_create_stage_name():
    value = payload_name("stage")
    container = AWSBucket("corp-bucket")
    sql = compile_sql(CreateStage(container, _stage(name=value)))
    assert_identifier(sql, value)
