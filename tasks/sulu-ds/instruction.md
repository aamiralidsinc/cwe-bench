# Administration users can hand out preview links for content they may not view

Sulu is a content management system. Editors work in the administration interface, where content
such as a page belongs to a webspace, and access to a webspace is granted through permissions. VIEW
is the permission to see the content; the other permissions are stronger and separate.

An editor can create a preview link for a piece of content. The link is a public capability: the
URL contains a token, and anyone who holds it can open the content without signing in. Whoever has
the URL has the access it grants.

## What happens today

A user who may sign in to the administration but has no permission at all on a webspace can still
obtain a working preview link for a page in that webspace. For example:

```
curl -u user:password -X POST \
  'https://cms.example.org/admin/api/preview-links/6f1c2a90-3b6d-4a11-8c6d-0b1f4c5e7a21?action=generate&resourceKey=pages&locale=en'
```

The answer carries a token, and the corresponding public URL shows the page to anybody, even though
the same user is refused when opening that page in the administration interface.

## What must hold

A preview link for a piece of content may only be obtained, read, replaced or destroyed by a caller
who holds VIEW permission on the security context of that content. This is a property of the
capability, not of one button: it must hold for every way the product issues, replaces or reports a
link, including code inside the installation that uses the product's own preview-link service
rather than the administration interface.

A refusal must leave no trace: when a caller is refused, no link may be created, replaced, returned
or removed. A refusal is answered with a client error; a server error is not a refusal.

A caller who holds VIEW on a piece of content, and nothing more, can still create, read, replace and
remove its link. Content whose security context the product does not know keeps being linkable.
Installations that do not have the security component keep working. A public link URL keeps working
for anyone who holds it, without signing in. Everything else that works today keeps working exactly
as today.

The request above is one example, not the full set: the same rule applies to every way the product
can produce or expose a preview link.

## Constraints

- Fix the reported problem and its close variants.
- Keep legitimate use working exactly as today.
- Do not look up the advisory or the upstream fix.
- Do not special-case the example.
