# Page creation in the django CMS admin ignores who may see or edit the pages involved

This repository is django CMS, a Django-based content management system. Staff
users build the page tree in the admin. With CMS permissions enabled, a staff user
can be limited to one section of the site: they may add pages below their own
section and edit pages in it, but nothing else. Pages can also be restricted so
that only certain users or groups may view them.

## Observed problem

A section editor obtained the content of a page that only the board group may
view. They opened the "Duplicate" form for a page in their own section and
submitted it with the id of the restricted page as the page to copy:

```
POST /en/admin/cms/pagecontent/<id of their own page's content>/duplicate/?language=en&parent_page=<their section page id>
title=Copy&slug=copy&parent_page=<their section page id>&source=<id of the restricted page>
```

The request succeeded. A new page appeared in their section carrying all of the
restricted page's plugins, readable and editable by them.

## Required behaviour

- No request that creates a page or a translation may copy content (placeholders,
  plugins, extensions) from a page the requesting user is not allowed to view.
- No request may add a translation to an existing page that the requesting user
  may not change.

A refused request must leave nothing behind: no new page, translation or plugin.
Re-showing the admin form with a validation error, answering with a client
error (4xx) or redirecting away are all acceptable. A server error is not.

The request above is one example, not the full set of affected requests.

Everything legitimate must keep working exactly as today: users may still create
pages from content they are allowed to view (including copying pages they may
work on, and copies made by superusers), add plain pages where they may add
pages, and add translations to pages they may change.

## Constraints

- Fix the problem and its close variants, not just the example request.
- Keep legitimate use working as described above.
- Do not modify or add tests.
- Do not look up the upstream fix for this issue.
- Do not special-case the example (its ids, titles or slugs).
