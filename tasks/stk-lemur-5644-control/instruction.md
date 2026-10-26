# Lemur — ACME directory addresses

Lemur is a certificate-management service. An authority that issues certificates through the
ACME protocol stores a directory address in its plugin options, and Lemur's backend fetches
that address when the authority is used.

## Observed impact

A user who has a role on an existing ACME authority can send

    PUT /api/1/authorities/<id>

with a body such as

    {"owner": "joe@example.com", "description": "", "active": true, "roles": [],
     "options": "[{\"name\": \"acme_url\", \"value\": \"http://169.254.169.254/latest/meta-data/\"}]"}

and the address is saved. The next time the authority is used, the backend connects to the
saved address, so a user who should only be able to use an authority can make the server fetch
an internal or link-local endpoint.

## Required property

A directory address must be checked when it arrives in a user request, before it is stored or
fetched by the backend: it must be an HTTPS URL whose host is on the configured allowlist of
permitted directory hosts. A request carrying any other directory address must fail with a
client error and have no effect, leaving stored state unchanged.

Everything that works today keeps working.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
