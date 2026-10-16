# Clients can set fields our schemas declare read-only

## The system

Our account service uses the serialization library in `/app` to load untrusted
JSON request bodies and to render responses. Server-controlled fields (roles,
approval flags, timestamps) are declared read-only (`dump_only`) and secrets are
declared write-only (`load_only`), using the library's documented ways of doing
so: on the field, in a schema's `class Meta` options, as arguments when a schema
is created, or from an enclosing schema with dotted names such as
`"profile.created"`. Our schemas are nested inside one another and reused across
endpoints.

## What we observed

```python
class ProfileSchema(Schema):
    class Meta:
        dump_only = ("role",)
    display_name = fields.Str()
    role = fields.Str()
    created = fields.DateTime()

class AccountSchema(Schema):
    class Meta:
        dump_only = ("profile.created",)
    username = fields.Str()
    profile = fields.Nested(ProfileSchema)

AccountSchema().load({"username": "eve", "profile": {"role": "admin"}})
# {'username': 'eve', 'profile': {'role': 'admin'}}
```

The client chose its own role. This is one example, not the whole problem:
other schemas of ours let read-only values in, or write-only values out.

## Required behaviour

- A field declared read-only, by any of the means above and at any depth, is
  never set from input, whichever way the input reaches it. Such input is
  handled exactly as the library already handles input for an ordinary
  read-only field (by default a validation error; dropped when unknown fields
  are excluded).
- A field declared write-only never appears in dumped output, whichever way the
  output is produced.
- Declarations add up: declaring further fields read-only or write-only, in any
  place, never lifts a declaration made elsewhere.
- A declaration made by an enclosing schema applies within that enclosing
  schema. The schema it encloses keeps behaving exactly as its own declarations
  say wherever else it is used, on its own or inside other schemas.
- Everything else loads and dumps exactly as it does today: unrestricted fields
  keep loading and dumping, read-only fields are still dumped and write-only
  fields are still loaded.

## Constraints

- Fix the flaw in the library itself, for every way it can be reached, not only
  the example above. Do not special-case the example's schemas, field names or
  values.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests will check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app` and is installed in editable mode. There is no
network. The project's own test suite runs with `python -m pytest tests` from
`/app`.
