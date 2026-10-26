"""External volume DDL."""

from conftest import assert_identifier, assert_literal, compile_sql, payload_literal, payload_name, payload_plain_quote
from snowflake.sqlalchemy import CreateExternalVolume, ExternalVolumeLocation


def _volume(**overrides):
    location = ExternalVolumeLocation(
        overrides.pop("location_name", "primary"),
        overrides.pop("uri", "s3://corp-iceberg/warehouse"),
        credentials=overrides.pop("credentials", {"AWS_KEY_ID": "key"}),
    )
    return CreateExternalVolume(
        overrides.pop("name", "corp_volume"),
        [location],
        allowlist=overrides.pop("allowlist", None),
        comment=overrides.pop("comment", None),
        **overrides,
    )


def test_volume_name():
    value = payload_name("volume")
    sql = compile_sql(_volume(name=value))
    assert_identifier(sql, value)


def test_location_name():
    value = payload_name("location")
    sql = compile_sql(_volume(location_name=value))
    assert_identifier(sql, value)


def test_location_uri_quote():
    value = "s3://corp-iceberg/" + payload_plain_quote("prefix")
    sql = compile_sql(_volume(uri=value))
    assert_literal(sql, value)


def test_location_uri_backslash():
    value = "s3://corp-iceberg/" + payload_literal("prefix")
    sql = compile_sql(_volume(uri=value))
    assert_literal(sql, value)


def test_location_credential():
    value = payload_plain_quote("secret")
    sql = compile_sql(_volume(credentials={"AWS_SECRET_KEY": value}))
    assert_literal(sql, value)


def test_allowlist_entry():
    value = payload_plain_quote("host.example.com")
    sql = compile_sql(_volume(allowlist=[value]))
    assert_literal(sql, value)


def test_comment():
    value = payload_plain_quote("owned by data")
    sql = compile_sql(_volume(comment=value))
    assert_literal(sql, value)
