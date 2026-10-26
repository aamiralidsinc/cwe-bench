# A contributed content body is published as raw HTML

## What the system is

This project is a static site generator. A site keeps its sources in a working tree: page bodies and
their settings live under a content directory, templates under a layouts directory, and site-wide
settings in a configuration file. Building the site converts each page body from its markup format
into HTML and writes the result under a publish directory. Content is often contributed by people
other than the site owner, so the generator treats content bodies as untrusted.

## What was observed

Building the site on a tree that contains a contributed page whose body is an HTML fragment writes
that body into the published site unchanged. A browser that opens the published page runs any
script in that body in the site's origin.

## The property that must hold

A content body is published to visitors only after it has been converted from its markup format,
unless the site owner has explicitly allowed that body's content format. This holds for every
content body, whatever content format it declares and however that format is chosen, and however
the body reaches the published site.

## What the fix must honor

- **Refusal.** Building a site that contains a body which would be published without conversion must
  fail: the build exits non-zero and nothing of that body is written to the publish directory. A
  refusal is not a crash and does not change how any other body is built.
- **Owner opt-in.** The site owner can allow content formats with `[security] allowContent`, a list
  of regular expressions matched against a body's media type. With `allowContent = ['.*']` every
  format is allowed and the site builds as it does today.
- **Preservation.** Everything that works today keeps working exactly as today: ordinary markup
  pages, bodies whose format the owner allows, markup nested in a page or rendered on demand from a
  template, content the site's own templates generate, and sites that set other security keys. A
  site with many ordinary pages, and a permitted body next to a refused one, keeps building.

The example above is one instance, not the full set of ways the property can be violated.

## Constraints

- Fix the flaw and its close variants, not just the example.
- Keep every legitimate use working.
- Do not special-case the example values.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
