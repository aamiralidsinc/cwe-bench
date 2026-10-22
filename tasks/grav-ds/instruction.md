# Private configuration leaks into rendered page content

## System

This project is a flat-file CMS. Site operators author the site's trusted
templates; separately, less-trusted page authors edit the body of individual
pages, and some author-supplied text is evaluated by the site's templating
engine when a page is rendered. Author-controlled templating is deliberately
restricted: it may read only the data and settings that have been designated
safe to expose to content. The site's broader configuration — secrets and other
operational settings — is meant to be invisible to it.

## Observed impact

A user who can edit only a page's body (no operator access) saves content that
the site later evaluates as a template. When the page is rendered, the output
discloses a private configuration value that content is never supposed to see.
The author never gains operator rights, yet reads secrets back through the
content they published.

## Security property

No templating input controlled by a less-trusted author may cause any
configuration value that is hidden from content to appear in rendered output,
however that input is supplied and however the value is reached or rendered.

## Contracts the fix must honor

- **Preservation of legitimate content.** Content keeps working for its
  legitimate uses: reading the data and settings designated safe to expose, and
  processing those ordinary values exactly as it does today.
- **Trusted operator templates.** Templates authored by the site operator are
  trusted and keep full, unredacted access to configuration and to every
  helper, exactly as today.
- **Refusal form.** When content tries to reach something hidden, no hidden
  value may appear. A blocked expression may render as nothing or may raise a
  handled error; either way the rest of the page still renders, and no specific
  error code or message is required.
- **Preservation of behaviour.** Legitimate use by both content and operator
  templates behaves exactly as before.

This impact is an illustration, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just one expression.
- Keep every legitimate use working.
- Do not special-case any input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
