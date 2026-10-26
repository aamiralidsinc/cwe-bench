"""Literal positions: a string value must stay inside its string literal."""

from sqlalchemy import Column, Integer, MetaData, Table

from conftest import (
    assert_literal,
    compile_sql,
    payload_literal,
    payload_plain_quote,
)
from snowflake.sqlalchemy import (
    AWSBucket,
    CopyIntoStorage,
    CSVFormatter,
    ExternalStage,
)


def _source_table():
    return Table("events", MetaData(), Column("id", Integer))


def _copy_into(from_=None, **kwargs):
    if from_ is None:
        from_ = ExternalStage(name="raw_stage", path="incoming")
    return CopyIntoStorage(from_=_source_table(), into=from_, **kwargs)


def test_file_names_backslash_before_quote():
    value = payload_literal("upload")
    sql = compile_sql(_copy_into().files([value]))
    assert_literal(sql, value)


def test_file_names_second_element_backslash_before_quote():
    value = payload_literal("second")
    sql = compile_sql(_copy_into().files(["first.csv", value]))
    assert_literal(sql, value)


def test_format_option_backslash_before_quote():
    value = payload_literal("csv")
    formatter = CSVFormatter().file_extension(value)
    sql = compile_sql(_copy_into(formatter=formatter))
    assert_literal(sql, value)


def test_format_option_plain_quote():
    value = payload_plain_quote("yyyy")
    formatter = CSVFormatter().date_format(value)
    sql = compile_sql(_copy_into(formatter=formatter))
    assert_literal(sql, value)


def test_storage_uri_quote():
    path = "incoming/" + payload_plain_quote("p")
    bucket = AWSBucket("corp-bucket", path)
    sql = compile_sql(_copy_into(from_=bucket))
    assert_literal(sql, "s3://corp-bucket/" + path)


def test_storage_credential_quote():
    value = payload_plain_quote("secret")
    bucket = AWSBucket("corp-bucket").credentials(
        aws_key_id="key", aws_secret_key=value
    )
    sql = compile_sql(_copy_into(from_=bucket))
    assert_literal(sql, value)
