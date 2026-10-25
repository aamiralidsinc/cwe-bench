# Page-level permissions are not enforced throughout the django CMS administration

This repository is django CMS, a Django-based content management system. Staff
users build the page hierarchy in the administration. With CMS permissions
enabled, a staff user can be limited to one section of the site: they may add
and change pages below their own section and edit pages in it, but nothing
else. Pages can also be restricted so that only certain users or groups may
view them, and a site administrator's rights stop at their own site.

## Observed problem

A staff user who was not allowed to view a restricted page was able to obtain
that page's content through the administration, and the content became readable
and editable by them.

## Required behaviour

No request may give a user access to the content of a page they are not allowed
to view, change a page they are not allowed to change, or create or place a page
in a location or on a site where they are not allowed to add pages. This holds
for every page a request refers to and is judged on the site where that page
lives: rights on one site give none on another.

A refused request must leave nothing behind: no record may be created and no
existing data may be changed. Re-showing the form with a validation error,
answering with a client error (4xx) or redirecting away are all acceptable; a
server error is not. When a request covers several pages and only some of them
are permitted, it is enough that nothing is taken from the pages the user may
not view.

Everything legitimate must keep working exactly as today: a user may still
obtain the content of a page they may view, change a page they may change, and
add a page in a location and on a site where they may add pages, and every
other part of the page administration must keep working wherever the user holds
the rights it needs. The situation described above is one example, not the full
set of affected requests.

## Constraints

- Fix the problem and its close variants, not just the example request.
- Keep legitimate use working as described above.
- Do not modify or add tests.
- Do not look up the upstream fix for this issue.
- Do not special-case the example (its ids, titles or slugs).
