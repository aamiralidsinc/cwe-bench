# Private configuration leaks into rendered page content

## System

This project is a flat-file CMS. Site operators write themes, plugins and
layouts; separately, less-trusted **page authors** edit the body of individual
pages through the editor. A page body may contain small templating expressions
that are evaluated when the page is rendered, so that an author can display page
data and a limited, explicitly-permitted slice of site information. Other
editor-supplied text that the site evaluates as a template is treated the same
way as a page body.

Because page-body templating is author-controlled, it is treated as untrusted
and is deliberately restricted: it may read only the data and settings that have
been designated safe to expose to content. The site's broader configuration —
plugin settings (SMTP credentials, API keys), security settings, and other
operational configuration — is meant to be invisible to page-body templating.

## Observed impact

A user who can only edit a page's body (no operator access) can save a page
whose body contains a templating expression and then view that page; the
rendered output discloses private configuration values that page content is
supposed to never see — for example a configured plugin credential. The author
never gains operator rights, but reads secrets back through the page they
themselves published.

## Security properties that must hold

- No templating expression in page-body content may cause any configuration
  value that is hidden from page content to appear in the rendered page. This
  holds regardless of which template construct is used to reach it, and
  whether the value is read singly, in bulk, or by any indirect route.
- Page-body templating must keep working for its legitimate uses: reading the
  data a page is allowed to read (its own front-matter fields and the settings
  explicitly exposed to content), and formatting, serializing or displaying
  those ordinary values.
- Templates authored by the site operator (themes, plugins, layouts) are
  trusted and must keep full, unredacted access to configuration and to every
  formatting/serialization/display helper, exactly as today.

## Contracts the fix must honor

- **Refusal form.** When page content tries to reach something hidden, the page
  must simply not disclose it. A blocked expression may render as nothing or may
  raise a handled error; either way, no hidden value appears and the rest of the
  page still renders. No specific error code or message is required.
- **Preservation.** Legitimate formatting and display of a page's own data, the
  reading of settings designated as exposable, and the full access that trusted
  operator templates enjoy, must all behave exactly as before.
- **Magnitudes.** A legitimate page might display its own title or a front-matter
  field, or render that data in another format; the attack reads operational
  secrets such as a plugin credential. Both go through the same page-rendering
  path.

The examples above are illustrations, not the full set of ways the property can
be violated.

## Constraints

- Fix the flaw and its close variants, not just the exact expression shown.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
