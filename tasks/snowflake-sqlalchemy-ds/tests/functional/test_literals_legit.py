"""Legitimate literal values keep their current rendering."""

from sqlalchemy import Column, Integer, MetaData, Table

from conftest import compile_sql
from snowflake.sqlalchemy import AWSBucket, CopyIntoStorage, CSVFormatter, ExternalStage


def _copy_into(from_=None, **kwargs):
    if from_ is None:
        from_ = ExternalStage(name="raw_stage", path="incoming")
    return CopyIntoStorage(
        from_=Table("events", MetaData(), Column("id", Integer)),
        into=from_,
        **kwargs,
    )


def test_plain_file_names():
    sql = compile_sql(_copy_into().files(["data1.csv", "data2.csv"]))
    assert "FILES = ('data1.csv','data2.csv')" in sql


def test_plain_format_option():
    formatter = CSVFormatter().file_extension("csv")
    sql = compile_sql(_copy_into(formatter=formatter))
    assert "FILE_EXTENSION='csv'" in sql


def test_delimiter_escape_sequences_are_preserved():
    formatter = (
        CSVFormatter()
        .record_delimiter(r"\n")
        .field_delimiter(r"\t")
        .escape(r"\134")
    )
    sql = compile_sql(_copy_into(formatter=formatter))
    assert r"RECORD_DELIMITER='\n'" in sql
    assert r"FIELD_DELIMITER='\t'" in sql
    assert r"ESCAPE='\134'" in sql


def test_null_if_values_are_preserved():
    formatter = CSVFormatter().null_if(["null", "Null"])
    sql = compile_sql(_copy_into(formatter=formatter))
    assert "NULL_IF=('null', 'Null')" in sql


def test_plain_bucket_uri_and_credentials():
    bucket = AWSBucket("backup", "subdir/path").credentials(
        aws_role="arn:aws:iam::123456789012:role/load"
    )
    sql = compile_sql(_copy_into(from_=bucket))
    assert "'s3://backup/subdir/path'" in sql
    assert "AWS_ROLE='arn:aws:iam::123456789012:role/load'" in sql
