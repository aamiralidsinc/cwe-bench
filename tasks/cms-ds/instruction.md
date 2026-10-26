# Control-panel navigation discloses entries a user may not view

## System

This project is a content management system. Editors work in a control panel
where a **navigation** is an ordered set of pages. A page is either a
free-form link with its own title and address, or a link to an entry in a
collection. Entries hold the actual content and belong to collections;
navigation pages link to entries and may display or override some of their
field values.

Control-panel users are not all equal. A user may be allowed to see a
navigation but not the entries of a particular collection, and a user may be
allowed into one site of a multi-site installation but not another.

## Observed impact

A control-panel user who is allowed to view a navigation but not the entries of
one of its collections can open a new page in that navigation that links to
such an entry — the page editor requests the navigation page and passes the
entry's identifier — and reads back the entry's stored field values in the
response. The same data comes back through other navigation responses, and a
user with no navigation rights at all can read a navigation's pages.

## Security properties that must hold

1. A user may read a navigation's pages, or have a page validated against it,
   only when the user is allowed to view that navigation in the site being
   read. Saving a navigation's structure continues to require the edit right it
   requires today.
2. No control-panel response may disclose an entry's stored values, its title,
   its address (URL) or its publication status unless the user is allowed to
   view that entry. This holds for every field and every nested structure of
   every response, however the response is assembled.
3. Where a response necessarily covers several pages and only some of the
   linked entries are visible to the user, the values the user may see must
   keep appearing exactly as they do today, and the values the user may not see
   must be absent. Where a request targets a single page or entry the user may
   not view, the request is refused with a client error.

## Contracts the fix must honor

- **Refusal form.** A refused request returns a client error (any 4xx) and
  carries no protected value; a server error is not a refusal. Nothing is
  changed by a refused request.
- **Preservation.** Everything that works today keeps working: users who may
  view both the navigation and the entry keep receiving all the values they
  receive today, in every field and nested structure where those values
  appear; free-form link pages keep opening; and no legitimate navigation
  response loses data that it returns today.
- **Magnitudes.** A permitted user may read a navigation page next to an entry
  whose title, address, status and field values are all visible; the attack is
  the same read performed by a user who may not view that entry, who must
  receive none of those values, not even the title.

The examples above are illustrations, not the full set of ways the property can
be violated.

## Constraints

- Fix the flaw and its close variants, not just the exact example shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
