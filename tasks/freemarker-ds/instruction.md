# Keep template resolution inside the template folder

## The system

This project is a template engine for Java applications. The application configures a **template
root** — a directory on disk, a location on the class path, or another kind of template storage —
and asks the engine for a template by name. Along with the name it passes the **locale** to render
for, normally taken from the request's language preference, and it may pass another value that
selects a variant of the template set (a theme, a device class, and so on).

The engine picks the best matching template for that locale: a locale-specific version if one
exists, then progressively less specific locale forms, and finally the plain template. Rendering
can pull in other templates, and those are resolved by the same rules.

## Observed problem

A caller supplied the locale `en_US_sub/../../secret` and the engine rendered the contents of a
template source from outside the configured template root. The application had set that root up
for its own templates only, and nothing told it that content from elsewhere had been read and
rendered.

## Security property (invariant)

No template lookup may read or render a template source from outside the configured template
root, for any value a caller supplies to that lookup — the requested name, the locale, or any
other value the application passes to it — however that value is spelled and however it reaches
the engine. A lookup must either resolve a template source inside the root or fail; it must never
end up with content from outside the root.

## Keep working

Everything that works today must keep working exactly as today. In particular:

- localized selection keeps the same order and the same file names: the most specific
  locale-specific template, then progressively less specific locale forms, then the plain
  template, for language-only locales, language-and-country locales, locales with a variant, and
  locales with a script;
- ordinary template names under the configured root keep loading, including names in
  subdirectories;
- requested names that walk upward out of the root keep being rejected as they are today.

These are examples, not the full set.

## Constraints

- Fix the underlying problem and its close variants, not just the one example.
- Keep every legitimate use working.
- Do not consult any upstream fix, advisory, or changelog for this project.
- Do not special-case the example values.
