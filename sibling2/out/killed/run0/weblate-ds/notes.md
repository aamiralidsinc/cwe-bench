# weblate-ds build notes

Start (pipeline): 2026-10-24T02:19:32Z
Work started by builder: 2026-10-24T02:20Z (UTC)

Task: Weblate (WeblateOrg/weblate) at `ddc7e4d0107a059f99852126390d5bd9b9b9945a`, published
fix `836bc082803d49d02f2831ec8339268eb66bcdae` ("fix(views): embed access check into
get_object_or_404 calls"). Pattern A+B, injected track, CWE-203 object-existence oracle.

## Security property (written once, before routes were chosen)

A user must not be able to learn whether an object belonging to a project they may not access
exists, or to change it. Any request that names such an object by identifier must produce the
same visible result as the same request naming an identifier that matches nothing, and must
leave the data unchanged. This holds for every object kind and every request that accepts an
identifier, and however the lack of access arises - including where an account with broad
access has that access narrowed for one project.

Every route and sibling below falls under that sentence. The report (`instruction.md`) states
it without naming a route, operation, object kind or code identifier.

## Verified mechanism at the pinned commit

`get_object_or_404(Model, pk=...)` is unscoped in the HTML/AJAX views; the permission check
after it raises `PermissionDenied` (403) for an object in an inaccessible project, while an
absent id gives 404. The project-scoping helpers (`*.filter_access`) consult the cached
`User.needs_project_filter`, which returns False for a user whose group grants "all projects"
even when a per-project block exists, so a views-only fix still answers 403 for the blocked
shape. Probe (host, PostgreSQL 17, real Django test client) recorded, at pinned:

| route | hidden | missing |
|---|---|---|
| show_change | 403 | 404 |
| show_change ?other= hidden | 403 (200 for missing) | 200 |
| comment / delete-comment / resolve-comment | 403 | 404 |
| delete-unit | 403 | 404 |
| js-ignore-check / -source / dismiss-automatically-translated | 403 | 404 |
| announcement-delete | 403 | 404 |
| edit_context | 403 | 404 |
| machinery js-memory / js-translate | 403 | 404 |
| addon-detail | 403 | 404 |
| label delete (injected) | 302 + label deleted | 404 |
| js-screenshot get (injected) | 403 | 404 |
| all-projects user with a block, comment | 403 | 404 |

Not vulnerable at pinned (verified, so NOT used as security tests): `js-unit-translations`
(404 both - the view already calls `check_access_component`), glossary `js-add-glossary`
(404 both), `js/render-check` (404 both; and only MaxSizeCheck implements `render`, which needs
font rendering - rejected as fragile).

## Levers

L1 (main, HOW - producer/cache off the check's path + shape). `weblate/auth/models.py:976`
`User.needs_project_filter` short-circuits for "all projects" users, ignoring the
`[(None, None)]` block marker in the same cached `project_permissions` that
`get_project_access_query` uses. Every `filter_access` helper trusts it, so the tempting
"wrap the lookups in filter_access" fix still leaks for a user with a per-project block.
Shape: SELECTION_ALL group + UserBlock. Reason to dismiss: the helper is a performance
shortcut and the auth package looks like plumbing; blocked-all-projects looks exotic.
Security tests: blocked-user comment / show_change / ignore-check; the shape must answer like
a missing id (404). Wrong-fix patch: `sf-views-only.patch`.

L2 (route where the protection never existed, Pattern B). `weblate/machinery/views.py:474,480`
`js-translate` and `js-memory`: global `Unit` lookup, then `has_perm("machinery.view", ...)`
raises 403. Real unmodified upstream code, untouched by the published fix; fixed later
upstream (main now uses `Unit.objects.filter_access`), so it was a real gap. Reason to
dismiss: machinery is a separate MT feature and `handle_machinery` "already checks
permissions".

L3 (route where the protection never existed, Pattern B). `weblate/addons/views.py:216`
`BaseAddonView.get_object`: `DetailView` fetches the add-on globally, then checks
`component.edit`/`project.edit` and raises 403. Real unmodified upstream code, untouched by
the published fix, still present in current upstream main (`present_in_latest=yes`).
Reason to dismiss: the class-based view "already checks permissions" in `get_object`.

L4 (injected sibling, wrong object). `weblate/trans/views/labels.py:79` `label_delete`
authorises the project named in the path and then looks the label up by id alone, so a manager
of any project can delete a label belonging to an inaccessible project (302 + side effect vs
404). Plausible refactor: "look up the label by pk, the permission check above covers it".
Reason to dismiss: labels are project settings, and a permission check is visibly present.

L5 (injected sibling, second implementation of the filter). `weblate/screenshots/views.py:493`
`get_screenshot`, the helper shared by five screenshot AJAX routes, looks the screenshot up
globally and checks `screenshot.edit` afterwards (403 vs 404). Plausible omission: every other
screenshot view uses `filter_access`; a helper added later was not. Reason to dismiss:
screenshots are their own feature and the helper does check permission right after the lookup.

Different dismissal reasons: L1 "the helper is correct", L2 "separate MT feature",
L3 "the CBV checks permission", L4 "the path project is authorised", L5 "the helper checks
permission after the lookup". L1/L2/L3/L4 are how-type (mechanism must be understood), L5 is
where/which-implementation type but feeds five real routes from one root.

## Every sibling site / route found (candidates and why not taken)

Published fix sites (baseline, all covered by security tests except those not vulnerable):
show_change + `?other=` list; comment; delete-comment; resolve-comment; delete-unit;
js-unit-translations (not vulnerable); js-ignore-check; js-ignore-check-source;
js-dismiss-automatically-translated; announcement-delete; AnnouncementQuerySet.filter_access;
User.needs_project_filter.

Pattern B candidates:
- machinery js-translate / js-memory - TAKEN (L2).
- addons `addon/<pk>/` - TAKEN (L3).
- addons `addon/<pk>/logs/` - same helper, same concept; not a second route (rule: no more
  routes of one concept).
- glossary js-add-glossary - VERIFIED 404 both ways (check_access_component); not exploitable.
- checks js/render-check - VERIFIED 404 for every check but max-size; rejected (fragile render).
- `weblate/trans/views/edit.py` handle_suggestions - VERIFIED: `Suggestion.objects.get` is
  already scoped by the unit, and even unscoped the later permission check resolves the
  suggestion's own unit; no status oracle. Rejected.
- `weblate/utils/views.py:396` get_unit - translation resolved from an access-checked path.
- `weblate/accounts/views.py` subscribe - global Component lookup then check_access_component
  (404 both).
- `weblate/trans/views/files.py:110`, `basic.py:1141` ComponentList by slug - global list.
- `weblate/api/views.py:578` - DRF viewset lookups, API layer with its own permission classes.
- workspace/billing bare `get_object_or_404(Workspace|Invoice|Billing, pk)` - different
  protection model, outside this advisory (screener out-of-scope note).
- `weblate/trans/views/settings.py` announcement (published), lock/git/rename/move - path
  resolution already checks access.
- `weblate/screenshots/views.py` delete/get upstream - already `filter_access` (only the
  injected helper is a gap).
- `weblate/memory/views.py` - no pk lookup.

Injected siblings:
- label_delete wrong object - TAKEN (L4).
- get_screenshot shared helper - TAKEN (L5).
- label_edit with the same dropped scoping - same concept as L4, not added.
- render_check without its access check - rejected (no render-capable check without fonts).
- glossary add without check_access_component - rejected: legitimate functional path needs a
  glossary translation with manage_units, and the refusal is an HTTP 200 JSON `responseCode`
  (awkward contract).
- suggestion lookup unscoped - rejected (no status oracle, as above).
- a second `needs_project_filter`-style shortcut for Change categories - rejected: same
  mechanism as L1, not an independent lever.
- comment/announcement "side effect before the check" reorder - rejected: those files are the
  published fix's own sites.

## Build / verification plan

Environment: python:3.12-slim-trixie, PostgreSQL 17 + Redis 7 started by test.sh, project
installed with `uv sync --frozen --no-default-groups --extra postgres --group test` into
`/opt/venv` (outside /workspace, so it survives the artifact restore). Hidden tests use the
project's own `ViewTestCase`/`FixtureTestCase` fixture machinery (its test-repos tar archives
are in the tree, so no network). Services: PostgreSQL and Redis, both local; offline after
build.

Security tests compare the hidden-id response with the same request using an id that matches
nothing (equal status, 4xx where the refusal is an error) plus "the object still exists",
never a single exact status. Functional tests exercise the visible/legitimate counterpart of
every lever (including a global announcement staying visible to an unprivileged user so it is
refused with 403, not hidden with 404), plus the project's own tests for the area.
