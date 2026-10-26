# django-cms-object-level — build notes (build-v1)

Start: 2026-10-17T05:20:48Z (this run; an earlier aborted run left only a Dockerfile/settings scaffold and the dev image cwe-djcms-dev, reused)
End: 2026-10-17T06:15:06Z. Gate: static (only blind patch + FAIRNESS.md missing), nop PASS, oracle PASS (2 runs), patches PASS (18)

## Levers
- T1 (A, landing): duplicate form's hidden copy source, chosen in the POST body; cms/admin/forms.py:514.
- T2 (A, far site): existing-page target of "add translation" lacks a change check; site narrowing skipped for hidden-source forms; cms/admin/forms.py:253-257,279-287,334. Dismiss: different feature.
- T3 (B): add form's page-type source validates against every page type, no view check (also with a translation target); cms/admin/forms.py:248-252. Dismiss: page types are shared templates.
- T4 (B): page wizard inherits that field, and its clean() skips the base clean(); cms/forms/wizards.py:22. Dismiss: other package/feature.

## Verified
- All 9 security tests fail by assertion on pinned; 13 own functional + 201 project tests (+10 subtests) pass on pinned and oracle.
- published fix alone fails exactly T3+T4 tests -> both routes open after the published fix; current upstream main (ea2344e, 2026-10-15) closes them (queryset narrowing + base-form source check + cms_page/source combination refused).
- Every checks/ patch run locally in the dev image with the expected outcome (see manifest.patch_checks).
- Attacker must be a section editor: in django CMS global "add page" needs global change, which implies viewing every page of that site.

## Dropped / not verified
- AddPageTypeForm (screener route): no in-tree caller, and its from_source() fails Page.copy's user assert -> unreachable.
- Screener shape "fewer than 2 page types" is wrong (the widget is checked before it is hidden); only the duplicate form skips narrowing.
- Not tested: whether duplicating a page the user can view but not change should be allowed (published: view; upstream main: change). Both designs pass.
- Out of scope: hidden parent_page not re-checked against add rights (fixed later upstream); copies drop the source's view restrictions (fixed later upstream); bundled CWE-269 group-permission and CWE-79 validate_url fixes.

## Fairness revision (2026-10-17, after FAIRNESS.md)
- Required 1 (cross-site copy source): the hole is real. Run in the dev image: a site-1-only manager gets
  `user_can_view_page(manager, restricted_site2_page, site=site2) == True`, because the helper's
  "may change -> may view" shortcut calls `user_can_change_page(user, page)` without `site`, so it is
  evaluated on the current site (global change on site 1). Passing `site=source.site` is therefore NOT
  enough. Two security tests (duplicate a board-restricted site-2 page from a site-1 page; post a
  restricted site-2 page type to the site-1 add form) were written and run: pinned fails both, the new
  oracle passes both, but hardening (before its helper hunk) and blind.patch (which does use
  `site=source.site`) fail both. Per BUILDER.md 3f a trap the blind fix cannot find is unfair, and this
  one sits in a fifth location (the shared permission helper) that no instruction sentence points to, so
  the tests were NOT added (kept in ~/.tb-graders/cwe/work/django-cms-object-level/dbg/
  test_copy_source_authz_with_cross_site.py). The oracle was still completed: view check with
  `site=source.site`, page-type queryset narrowed to this site, helper shortcut made site-aware
  (225 tests pass incl. the two scratch tests). hardening.patch got the same helper hunk; alt_form_clean
  now checks view with `site=source.site`. Known uncaught wrong fix: any fix relying on the stock view
  helper for cross-site sources.
- Required 2: assertRefused no longer rejects 3xx; the unchanged snapshot plus no modal-success marker
  prove the refusal. Instruction lists redirecting away as acceptable.
- Required 3 / Recommended: removed "whatever way the page to copy from is supplied"; bullet 2 reworded
  to "No request may add a translation to an existing page that the requesting user may not change."
