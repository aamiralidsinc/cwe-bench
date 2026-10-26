# weblate-ds — build notes

Start: 2026-10-24T02:45:14Z
End: 2026-10-24T03:52:00Z (build; gate run follows)

## Task

Weblate (weblateorg/weblate) at `ddc7e4d0107a059f99852126390d5bd9b9b9945a`, the direct
parent of the published fix `836bc082803d49d02f2831ec8339268eb66bcdae`. The pinned commit
contains no regression tests for the advisory; the fix commit adds them.

## Levers (one line each)

- **T1 (main; pattern A far site, producer off the check's path, how-type)** — the cached
  `needs_project_filter` shortcut (`weblate/auth/models.py:976-984`) returns False for an
  all-projects account even when an explicit `UserBlock` excludes a project, so every
  `filter_access` queryset skips filtering. Reason to dismiss: broad access is trusted and
  the existing access helpers are presumed correct; the blocked+broad combination looks
  exotic. Fix needs the mechanism, not the site.
- **T2 (pattern B, real upstream; how-type)** — machinery `translate`/`memory`
  (`weblate/machinery/views.py:474-488`) look a unit up globally and only then run their own
  permission check, so hidden answers 403 and missing 404. Reason to dismiss: a separate
  feature whose own check looks like the right guard.
- **T3 (pattern B, real upstream; the protection exists but is ineffective)** —
  `screenshot-delete` / `screenshot-remove-source` (`weblate/screenshots/views.py:478-494`)
  already call `Screenshot.objects.filter_access`, but for blocked broad accounts the filter
  is skipped by T1 and the route answers 403 vs 404. Reason to dismiss: it already applies
  the access filter.
- **S1 (injected)** — added check-summary route scopes the lookup to the user's projects and
  ignores individually restricted components; hidden answers 403, missing 404. Reason to
  dismiss: "already limited to the user's projects".
- **S2 (injected)** — added bulk suggestion deletion validates every id and checks every
  item's permission but looks the ids up globally first, so a mixed batch of permitted and
  hidden items answers differently from the same batch with a missing id. Reason to dismiss:
  "every identifier is validated and every object's permission is checked".
- **S3 (injected)** — added suggestion acceptance checks authority on the caller-supplied
  translation and then acts on a separately named suggestion. Reason to dismiss: "permission
  is checked before the action".

## General property (written once, before choosing routes)

No request may reveal whether content exists that the requester may not access, and such
content may not be read, changed or produced; any reference to it must answer exactly like a
reference to content that does not exist, including in mixed batches, and regardless of
whether access is denied by project, by an individually restricted part, or by an explicit
exclusion overriding a broad grant. The instruction never names a route, file or mechanism of
a far site, an uncovered route or an added endpoint.

## Candidate sites considered, and why the picks won

Every global object lookup in the views, plus every consumer of the access querysets, was
listed before choosing:

- Real upstream routes: `show_change` and the repeated `other` list; `comment`,
  `delete-comment`, `resolve-comment`, `delete-unit`; `js-unit-translations`,
  `js-ignore-check`, `js-ignore-check-source`, `js-dismiss-automatically-translated`;
  `announcement-delete`; `edit_context`; machinery `translate`/`memory`; glossary add term;
  render-check; screenshot delete/remove/get/search/ocr/add; API lookups.
- Sibling candidates from the screener and my own search: the suggestion lookup by pk in
  `edit.py:587` (already unit-scoped, no gap); a second cached shortcut in `change.py`
  (would duplicate T1's concept, rejected); a bare screenshot AJAX lookup (the real code
  already uses the access queryset); glossary add term and render-check (both already answer
  404 for hidden and missing — verified with a behavioural test, rejected); workspace and
  billing lookups (different protection model, out of scope).

Picks and why:
- T1 beat the other lower-level candidates because it is the only lever that cannot be fixed
  by touching a view: the access querysets themselves are wrong for a user shape the report
  does not mention, and it silently reopens every route that already uses them (T3).
- T2 beat glossary/render-check because those are behaviourally indistinguishable at the
  pinned commit; machinery is a real 403/404 oracle in another package, untouched by the fix.
- T3 beat a planted screenshot sibling because the real endpoint is genuinely reachable and
  genuinely looks protected — the strongest "the protection is already there" dismissal.
- S1 beat the other injected candidates because its scoping is a plausible partial fix
  (project) that misses a second access dimension (component restriction), and it is a read
  route far from the reported write pages.
- S2 beat a per-object-only sibling because the bulk shape is a distinct input shape
  (several identifiers at once) that a per-identifier fix does not cover.
- S3 beat the O8b suggestion-scoping lead (which is already safe) because it is a genuine
  wrong-object decision: authority on one object, action on another.

All routes and siblings were confirmed behaviourally on the pinned+injection copy before the
tests were written. The published fix's own regression test for `js-unit-translations` was
found to pass at the pinned commit (hidden and missing both 404); that route is covered as a
functional test, never as a security test.

## Verified

- Pinned+injection (nop): 25 security tests fail, 12 functional tests pass, 88 project tests
  pass (the one upstream skip is deselected so the functional set has no skips).
- Oracle (published source fix + machinery + the three added endpoints): 25/25 security,
  12/12 functional, 88 project tests pass, three identical local runs.
- Gate: static PASSED; nop PASSED (25 security fail, 100 functional pass); oracle PASSED
  (three runs, every one reward 1.0 and identical).
- Wrong-fix patches, each run locally in full: `sf-published-only` 6 security failures;
  `sf-auth` 8 blocked-account security failures; `sf-machinery` 3; `sf-check-summary` 1;
  `sf-bulk-delete` 1; `sf-accept-suggestion` 1; `sf-reads-only` 15; `ff-deny-all` 30
  functional failures; `ff-crash` 4 security failures with every functional test passing;
  `ff-adjacent` the project test that states the cached fast path.
- Correct alternatives: `pass-hardening` (oracle plus a scoped comment queryset used by the
  views) and `pass-alternative` (keep the cached shortcut, test the explicit block marker in
  every access queryset) both score 1.0 locally.
- The suites run as uid 1000 against a user-owned PostgreSQL cluster that a per-group wrapper
  starts inside test.sh (the template's process reap would otherwise kill it); no Redis is
  needed because `settings_test` keeps the in-memory cache and Celery broker.
- Current upstream main: the machinery routes now use the access filter and the cached
  project filter includes the block check, so both uncovered routes are closed in latest
  code. They were real at the pinned commit and the advisory's published fix did not touch
  them.

## Could not verify

- Trials against the two target models (deferred to the trial stage).
- The `blind` patch (written by run_blindfix from instruction.md alone after the build).
- Whether any slower CI-only tests in the selected project modules depend on network; the
  selected classes were run offline here and passed.
- `repo_mb` was not recorded.

## Out of scope

- Workspace and billing views use bare `get_object_or_404` with a different protection model
  (`weblate/workspaces/views.py:87`, `weblate/billing/views.py:87,235,286`); not pursued.
