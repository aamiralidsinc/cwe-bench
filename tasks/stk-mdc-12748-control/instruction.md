# Unsafe link targets reach the rendered page

`@nuxtjs/mdc` turns Markdown — including raw HTML inside it — into a Vue component tree and renders that tree. Sites use it to publish content that end users submit.

A page that renders submitted Markdown containing a link whose target is an inline `data:` document gets a live link instead of an inert one: following it loads an attacker-authored document with scripts enabled. Harmless inputs show the same result.

## What must hold

No content that this library renders may produce a URL-carrying attribute carrying a scheme the library refuses. Such a value must be dropped from the rendered output; the element itself and every other part of the document still render normally.

Everything that works today must keep working exactly as today: ordinary links, images and every value the library already allows must still render unchanged.

The example above is an example, not the full set. Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream fix. Do not special-case the example.
