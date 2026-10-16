"""Security tests: a field declared read-only must never be set from input, and a
field declared write-only must never appear in output, whichever way the schemas
are composed. Every test goes through the public API (Schema.load / Schema.dump).

A refusal is the library's normal validation error, or silently dropping the
value; any other exception is a failure.
"""

import datetime as dt

from marshmallow import Schema, ValidationError, fields


def load_or_refuse(schema, data):
    """Load ``data``; return None when the library refuses it with a validation error."""
    try:
        return schema.load(data)
    except ValidationError:
        return None


def assert_not_set(result, *path):
    """The attacker's value must not be present at ``path`` in a loaded result."""
    if result is None:
        return
    node = result
    for key in path[:-1]:
        if not isinstance(node, dict) or key not in node:
            return
        node = node[key]
    assert not (isinstance(node, dict) and path[-1] in node), (
        f"restricted field {'.'.join(map(str, path))} was set from input: {result!r}"
    )


class MemberSchema(Schema):
    class Meta:
        dump_only = ("approved",)
        load_only = ("pin",)

    name = fields.Str()
    tier = fields.Str()
    approved = fields.Bool()
    joined = fields.Date()
    pin = fields.Str()


class PlainMemberSchema(Schema):
    name = fields.Str()
    tier = fields.Str()
    joined = fields.Date()
    pin = fields.Str()


# --- declarations made in a nested schema's own options must survive more declarations


def test_enclosing_declaration_keeps_nested_schema_options():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.joined",)

        title = fields.Str()
        member = fields.Nested(MemberSchema)

    result = load_or_refuse(
        TeamSchema(), {"title": "t", "member": {"name": "eve", "approved": True}}
    )
    assert_not_set(result, "member", "approved")


def test_constructor_declaration_keeps_schema_options_read_only():
    result = load_or_refuse(
        MemberSchema(dump_only=("joined",)), {"name": "eve", "approved": True}
    )
    assert_not_set(result, "approved")


def test_constructor_declaration_keeps_schema_options_write_only():
    out = MemberSchema(load_only=("tier",)).dump(
        {"name": "eve", "tier": "gold", "pin": "1234", "approved": False}
    )
    assert "pin" not in out


# --- declarations made by an enclosing schema must hold however the schema is nested


def test_enclosing_read_only_with_nested_schema_object():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        title = fields.Str()
        member = fields.Nested(PlainMemberSchema())

    result = load_or_refuse(
        TeamSchema(), {"title": "t", "member": {"name": "eve", "tier": "gold"}}
    )
    assert_not_set(result, "member", "tier")


def test_enclosing_read_only_with_nested_schema_factory():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        title = fields.Str()
        member = fields.Nested(lambda: PlainMemberSchema())

    result = load_or_refuse(
        TeamSchema(), {"title": "t", "member": {"name": "eve", "tier": "gold"}}
    )
    assert_not_set(result, "member", "tier")


def test_enclosing_read_only_in_list_of_nested():
    class TeamSchema(Schema):
        title = fields.Str()
        members = fields.List(fields.Nested(lambda: PlainMemberSchema()))

    result = load_or_refuse(
        TeamSchema(dump_only=("members.tier",)),
        {"title": "t", "members": [{"name": "a"}, {"name": "eve", "tier": "gold"}]},
    )
    if result is not None and "members" in result:
        for member in result["members"]:
            assert "tier" not in member, result


def test_enclosing_read_only_in_mapping_of_nested():
    class DirectorySchema(Schema):
        class Meta:
            dump_only = ("by_id.tier",)

        by_id = fields.Dict(keys=fields.Str(), values=fields.Nested(PlainMemberSchema()))

    result = load_or_refuse(
        DirectorySchema(), {"by_id": {"u1": {"name": "eve", "tier": "gold"}}}
    )
    assert_not_set(result, "by_id", "u1", "tier")


def test_enclosing_write_only_with_nested_schema_object():
    class TeamSchema(Schema):
        class Meta:
            load_only = ("member.pin",)

        title = fields.Str()
        member = fields.Nested(PlainMemberSchema())

    out = TeamSchema().dump(
        {"title": "t", "member": {"name": "eve", "tier": "gold", "pin": "1234"}}
    )
    assert "pin" not in out["member"], out


def test_enclosing_read_only_field_with_data_key():
    class KeyedMemberSchema(Schema):
        name = fields.Str()
        tier = fields.Str(data_key="memberTier")

    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        member = fields.Nested(lambda: KeyedMemberSchema())

    result = load_or_refuse(
        TeamSchema(), {"member": {"name": "eve", "memberTier": "gold"}}
    )
    assert_not_set(result, "member", "tier")
    assert_not_set(result, "member", "memberTier")


def test_enclosing_declaration_keeps_nested_object_own_declarations():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        member = fields.Nested(lambda: PlainMemberSchema(dump_only=("joined",)))

    data = {"member": {"name": "eve", "tier": "gold"}}
    assert_not_set(load_or_refuse(TeamSchema(), data), "member", "tier")
    data = {"member": {"name": "eve", "joined": dt.date(2020, 1, 1).isoformat()}}
    assert_not_set(load_or_refuse(TeamSchema(), data), "member", "joined")


# --- declarations reach further nested schemas through a schema object


class UnitSchema(Schema):
    name = fields.Str()
    lead = fields.Nested(PlainMemberSchema)
    deputies = fields.List(fields.Nested(PlainMemberSchema))


def test_enclosing_read_only_two_levels_through_schema_object():
    unit_schema = UnitSchema()

    class OrgSchema(Schema):
        class Meta:
            dump_only = ("unit.lead.tier",)

        unit = fields.Nested(unit_schema)

    result = load_or_refuse(
        OrgSchema(), {"unit": {"name": "u", "lead": {"name": "eve", "tier": "gold"}}}
    )
    assert_not_set(result, "unit", "lead", "tier")


def test_enclosing_read_only_two_levels_through_used_schema_object():
    unit_schema = UnitSchema()
    # the schema object is already in use on its own before the enclosing schema uses it
    data = {"name": "u", "lead": {"name": "bob", "tier": "gold"}, "deputies": [{"name": "d"}]}
    unit_schema.load(data)
    unit_schema.dump(data)

    class OrgSchema(Schema):
        class Meta:
            dump_only = ("unit.lead.tier", "unit.deputies.tier")

        unit = fields.Nested(unit_schema)

    result = load_or_refuse(
        OrgSchema(), {"unit": {"name": "u", "lead": {"name": "eve", "tier": "gold"}}}
    )
    assert_not_set(result, "unit", "lead", "tier")
    result = load_or_refuse(
        OrgSchema(), {"unit": {"name": "u", "deputies": [{"name": "eve", "tier": "gold"}]}}
    )
    if result is not None and "deputies" in result.get("unit", {}):
        for deputy in result["unit"]["deputies"]:
            assert "tier" not in deputy, result
