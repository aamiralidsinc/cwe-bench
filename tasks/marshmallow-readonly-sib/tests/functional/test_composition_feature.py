"""Functional tests: legitimate loading and dumping keeps working exactly as today
while read-only / write-only declarations are honoured. Public API only."""

import pytest
from marshmallow import EXCLUDE, Schema, ValidationError, fields


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


def test_unrestricted_nesting_binds_everything():
    class TeamSchema(Schema):
        title = fields.Str()
        a = fields.Nested(PlainMemberSchema)
        b = fields.Nested(PlainMemberSchema())
        c = fields.Nested(lambda: PlainMemberSchema())
        d = fields.List(fields.Nested(lambda: PlainMemberSchema()))

    m = {"name": "eve", "tier": "gold", "pin": "1"}
    assert TeamSchema().load({"title": "t", "a": m, "b": m, "c": m, "d": [m]}) == {
        "title": "t", "a": m, "b": m, "c": m, "d": [m]
    }


def test_enclosing_read_only_still_restricts_and_siblings_bind():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        title = fields.Str()
        member = fields.Nested(PlainMemberSchema)

    assert TeamSchema().load({"title": "t", "member": {"name": "eve"}}) == {
        "title": "t", "member": {"name": "eve"}
    }
    with pytest.raises(ValidationError):
        TeamSchema().load({"member": {"name": "eve", "tier": "gold"}})


@pytest.mark.parametrize("make", [lambda: PlainMemberSchema(), None], ids=["factory", "object"])
def test_restricted_nested_object_other_fields_bind_and_dump(make):
    nested = fields.Nested(make) if make else fields.Nested(PlainMemberSchema())

    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)
            load_only = ("member.pin",)

        title = fields.Str()
        member = nested

    loaded = TeamSchema().load(
        {"title": "t", "member": {"name": "eve", "pin": "1234", "joined": "2020-01-02"}}
    )
    assert loaded["member"]["name"] == "eve"
    assert loaded["member"]["pin"] == "1234"  # write-only fields still load
    assert str(loaded["member"]["joined"]) == "2020-01-02"
    out = TeamSchema().dump({"title": "t", "member": {"name": "eve", "tier": "gold"}})
    assert out == {"title": "t", "member": {"name": "eve", "tier": "gold"}}  # read-only still dumped


def test_shared_schema_object_keeps_its_own_behaviour_elsewhere():
    shared = PlainMemberSchema()

    class PublicTeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        member = fields.Nested(shared)

    class StaffTeamSchema(Schema):
        member = fields.Nested(shared)

    try:
        PublicTeamSchema().load({"member": {"name": "eve", "tier": "gold"}})
    except ValidationError:
        pass
    assert StaffTeamSchema().load({"member": {"name": "bob", "tier": "gold"}}) == {
        "member": {"name": "bob", "tier": "gold"}
    }
    assert shared.load({"name": "bob", "tier": "gold"}) == {"name": "bob", "tier": "gold"}


def test_shared_schema_object_under_two_different_restrictions():
    shared = PlainMemberSchema()

    class PublicTeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)
            load_only = ("member.pin",)

        member = fields.Nested(shared)

    class AuditSchema(Schema):
        class Meta:
            dump_only = ("member.joined",)

        member = fields.Nested(shared)

    PublicTeamSchema().load({"member": {"name": "eve"}})
    PublicTeamSchema().dump({"member": {"name": "eve", "pin": "1"}})
    assert AuditSchema().load({"member": {"name": "bob", "tier": "gold"}}) == {
        "member": {"name": "bob", "tier": "gold"}
    }
    assert AuditSchema().dump({"member": {"name": "bob", "pin": "1"}}) == {
        "member": {"name": "bob", "pin": "1"}
    }


def test_schema_options_and_constructor_declarations_still_restrict():
    with pytest.raises(ValidationError):
        MemberSchema().load({"name": "eve", "approved": True})
    with pytest.raises(ValidationError):
        PlainMemberSchema(dump_only=("tier",)).load({"name": "eve", "tier": "gold"})
    assert MemberSchema().load({"name": "eve", "pin": "1"}) == {"name": "eve", "pin": "1"}
    assert MemberSchema().dump({"name": "eve", "approved": True, "pin": "1"}) == {
        "name": "eve", "approved": True
    }
    assert PlainMemberSchema(load_only=("pin",)).dump({"name": "eve", "pin": "1"}) == {
        "name": "eve"
    }


def test_exclude_unknown_drops_restricted_input_silently():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier",)

        member = fields.Nested(PlainMemberSchema, unknown=EXCLUDE)

    assert TeamSchema().load({"member": {"name": "eve", "tier": "gold"}}) == {
        "member": {"name": "eve"}
    }


def test_list_of_restricted_nested_objects_binds_visible_fields():
    class TeamSchema(Schema):
        members = fields.List(fields.Nested(lambda: PlainMemberSchema()))

    loaded = TeamSchema(dump_only=("members.tier",)).load(
        {"members": [{"name": "a"}, {"name": "b", "pin": "2"}]}
    )
    assert loaded == {"members": [{"name": "a"}, {"name": "b", "pin": "2"}]}
    out = TeamSchema(dump_only=("members.tier",)).dump({"members": [{"name": "a", "tier": "x"}]})
    assert out == {"members": [{"name": "a", "tier": "x"}]}


def test_nested_object_keeps_its_own_options_under_restriction():
    class TeamSchema(Schema):
        class Meta:
            dump_only = ("member.tier", "members.tier", "brief.tier")

        member = fields.Nested(PlainMemberSchema(unknown=EXCLUDE))
        members = fields.Nested(PlainMemberSchema(many=True))
        brief = fields.Nested(PlainMemberSchema(only=("name", "tier")))

    loaded = TeamSchema().load(
        {
            "member": {"name": "eve", "nickname": "e"},
            "members": [{"name": "a"}, {"name": "b"}],
            "brief": {"name": "c"},
        }
    )
    assert loaded == {
        "member": {"name": "eve"},
        "members": [{"name": "a"}, {"name": "b"}],
        "brief": {"name": "c"},
    }
    out = TeamSchema().dump({"brief": {"name": "c", "tier": "t", "pin": "1"}})
    assert out == {"brief": {"name": "c", "tier": "t"}}


def test_schema_object_unaffected_by_deeper_restriction_elsewhere():
    class UnitSchema(Schema):
        name = fields.Str()
        lead = fields.Nested(PlainMemberSchema)

    unit_schema = UnitSchema()

    class OrgSchema(Schema):
        class Meta:
            dump_only = ("unit.lead.tier",)

        unit = fields.Nested(unit_schema)

    class StaffSchema(Schema):
        unit = fields.Nested(unit_schema)

    OrgSchema().load({"unit": {"name": "u", "lead": {"name": "eve"}}})
    data = {"name": "u", "lead": {"name": "bob", "tier": "gold"}}
    assert unit_schema.load(data) == data
    assert StaffSchema().load({"unit": data}) == {"unit": data}
