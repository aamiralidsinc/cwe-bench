# Hidden content can be told apart from content that does not exist

## System

Weblate is a web-based translation platform. Teams contribute translations to
projects. A project can be public, protected or private, and individual
components inside a project can be restricted to the teams that may work on
them. Accounts receive permissions through teams, either site-wide or for
particular projects, and an account can be explicitly excluded from a project
even when a broader team would otherwise include it.

## Observed impact

A user whose access is limited to a public project can open the activity entry
for a change id that belongs to another team's private project
(`GET /change/<id>/`). The server answers "permission denied"; the same request
for an id that does not exist answers "not found". That difference tells the
user that the hidden entry exists, and the same probe works on other object-id
pages and actions.

## Security property

No request may reveal whether content exists that the requester is not allowed
to access, and no such content may be read, changed or produced. Whenever a
request refers to content the requester may not access, the outcome must be
exactly the outcome for content that does not exist at all. This holds however
the content is named, for every kind of stored content and every action, and
whether the account lacks access because of the project, because a part of a
project is restricted, or because an explicit exclusion overrides a broader
grant.

When a request names both content the requester may access and content they may
not, the content they may not access must be treated exactly like content that
does not exist: the permitted part still works, and the request must not fail
differently because the hidden item is present.

## Contracts the fix must honor

- **Refusal form.** Content that is hidden must be refused like content that
  does not exist: a client error (a 4xx response, not a server error) when the
  request is about that content, with nothing created, changed or returned.
  When the request is about permitted content and only mentions the hidden item
  alongside, the hidden item is ignored.
- **Preservation.** Everything that works today keeps working exactly as today:
  content the requester may access is still shown and still accepts the same
  actions, with the same results. Refusing an action because the account lacks
  authority over content it *may* access stays that refusal and does not turn
  into "not found". Content that is visible to everyone stays visible to
  everyone. When a request covers permitted and hidden items together, the
  permitted items are still handled as they are today.
- **Mixed requests.** A permitted item named next to a hidden one must still be
  handled; a hidden item named next to a permitted one must behave as though it
  were not named at all.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the problem and its close variants, not just the request shown.
- Keep every legitimate use working as described above.
- Do not special-case the example (its ids, usernames or object types).
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
