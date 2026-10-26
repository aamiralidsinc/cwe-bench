# External sign-in can open another person's account

Poweradmin is a web control panel for PowerDNS. People can sign in through the panel's configured
external identity provider instead of a local password. The panel records which external identity
belongs to which local account and uses that record on later sign-ins.

We received a report from an operator. A person signed in with an external identity whose subject
property differed from an existing user's only by letter case, and the panel opened, updated and
signed them in to that existing user's account.

The rule we need is this: an external identity is the exact character sequence that the provider
asserts as the subject, together with the provider it came from. Two identities are the same only
when both strings are identical character for character. Every sign-in must resolve to the one
local account bound to that exact identity. It must never resolve to, update, or take over an
account or a binding that belongs to a different identity, and one identity's sign-in must never
move or overwrite another identity's record. The rule applies to accounts and bindings that
already exist in the database, however they were created, and repeated sign-ins with the same
exact identity must always reach the same account.

Everyday sign-in must keep working exactly as it does today. An identity that matches an existing
binding still signs in to its account; an identity with no binding is still provisioned, or linked
to an existing account through the configured email linking, as the configuration says; and users
whose identifiers are legitimate still sign in normally. The panel supports more than one database
backend, and installations are created with different database character sets; sign-in must keep
working on each of them.

The example above is one trigger, not the full set of ways this can happen.

## Constraints

- Fix the problem and its close variants; do not change unrelated behaviour.
- Keep legitimate use working exactly as it does today.
- Do not look up or copy the upstream fix.
- Do not special-case the example; apply the rule generally.
