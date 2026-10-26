# FAIRNESS review: django-cms-object-level

Reviewer read: instruction.md, tests/ (cmsfix.py, security/, functional/, test.sh, score.py),
solution/fix.patch, manifest.json, notes.md, every checks/*.patch. Nothing was run. The repository
source is not checked out locally, so statements about `cms/utils/page_permissions.py` behaviour
come from the patches and notes and are marked **(inferred)**.

`assertRefused` = status < 500, not 3xx, no `cms-view-new-object`, (Page, PageContent, CMSPlugin)
counts unchanged. `assertCreated` = 200/302 with no `errornote`/`errorlist`.

## 1. Per-test table

### Security (tests/security/test_copy_source_authz.py)

| Test | Asserts | Instruction basis | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| DuplicateSourceTests::test_duplicate_own_page_with_restricted_source_in_body | editor POSTs duplicate of own page with `source=secret`: no secret text copied; assertRefused | Observed problem (this is the example request); bullet 1 | **maybe**: a fix that refuses with a redirect plus a `messages.error` (a common Django admin idiom, e.g. `_get_obj_does_not_exist_redirect`) fails the "not 3xx" assert even though nothing is written. The instruction lists two acceptable forms but never says a redirect is wrong | medium |
| DuplicateSourceTests::test_duplicate_restricted_page_from_its_url | duplicate URL is the secret page itself; refused | bullet 1 + "one example, not the full set" | same redirect caveat only | medium (redirect) |
| DuplicateSourceTests::test_duplicate_restricted_source_into_own_page_translation | duplicate with `source=secret` + `cms_page=team` (lang de): no copy; refused | bullet 1 "creates a page **or a translation**" | **maybe**: a fix that silently drops the unauthorised source and still creates an empty `de` translation fails the snapshot. "A refused request must leave nothing behind" covers this, but only if the solver treats this as a refusal. Narrowing the queryset or a field error passes | low |
| TranslationTargetTests::test_add_translation_to_page_user_cannot_change | editor adds `de` translation to `other` (cannot change it); none created; refused | bullet 2 | no | low |
| TranslationTargetTests::test_duplicate_into_page_user_cannot_change | duplicate own page into `cms_page=other`; no translation; refused | bullet 2 ("No request") | no | low |
| TranslationTargetTests::test_duplicate_into_page_of_another_site | site-1 manager, duplicate with `cms_page`=site-2 page; refused | bullet 2 "belongs to the site being administered" | no (stated explicitly) | low |
| PageTypeSourceTests::test_add_page_from_restricted_page_type | editor (not in board) adds page from board-restricted page type; no copy; refused | bullet 1 ("whatever way the page to copy from is supplied") | redirect caveat only | low |
| PageTypeSourceTests::test_add_translation_from_restricted_page_type | add `de` translation of own page with restricted page type as source; refused | bullet 1 | same "silently drop source" caveat as above | low |
| PageTypeSourceTests::test_wizard_page_from_restricted_page_type | "New page" wizard step 2 with restricted page type; refused | bullet 1 "No request that creates a page" | no. Re-rendering the wizard step with an error passes (200) | low |

### Functional (tests/functional/test_page_creation.py)

| Test | Asserts | Instruction basis | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| DuplicateTests::test_editor_duplicates_own_section_page | editor duplicates `team`; +1 page, +1 copy of team text | "copying pages they may work on" | no | low |
| DuplicateTests::test_editor_opens_duplicate_form_for_own_page | GET duplicate form → 200 | "keep working exactly as today" | no | low |
| DuplicateTests::test_superuser_duplicates_restricted_page | root duplicates `secret` | "copies made by superusers" | no | low |
| DuplicateTests::test_manager_duplicates_page_of_their_site | site-1 manager duplicates `other` | "copying pages they may work on" | no | low |
| PageTypeTests::test_add_form_offers_page_types_of_this_site | GET add form contains "open type" | keep working | no (a fix that only filters choices keeps it) | low |
| PageTypeTests::test_editor_creates_page_from_open_page_type | editor creates from open type; copied, parent=team, not a page type | "create pages from content they are allowed to view" | no | low |
| PageTypeTests::test_board_member_creates_page_from_board_page_type | editor in board creates from board type | same | no | low |
| PageTypeTests::test_wizard_creates_page_from_open_page_type | wizard with open type succeeds and copies | same | no | low |
| PageTypeTests::test_wizard_creates_plain_page | wizard without source succeeds | "add plain pages where they may add pages" | no | low |
| AddPageAndTranslationTests::test_editor_adds_plain_page_in_section | plain add under team | same | no | low |
| AddPageAndTranslationTests::test_editor_adds_translation_to_own_page | `de` translation of team | "add translations to pages they may change" | no | low |
| AddPageAndTranslationTests::test_manager_adds_translation_to_page_of_their_site | manager adds `de` to `other` | same | no | low |
| AddPageAndTranslationTests::test_manager_opens_add_translation_form | GET add-translation form → 200 | same | no | low |
| functional/project/* (pristine upstream test_forms, test_wizards, test_page_admin) | upstream behaviour | keep working | low: oracle, hardening and alt all pass them. A fix that requires *change* on every duplicate source is not caught by them either (alt does this and passes) | low |

The view-only-duplicate design choice is deliberately untested (notes.md). Good.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 hidden duplicate source | check the URL object only, or narrow the page-type queryset in `__init__` (skipped for hidden widgets) | yes: test_duplicate_own_page_with_restricted_source_in_body (url_object_and_type_queryset.patch) |
| T1 copy into a translation | guard only `from_source()` | yes: test_duplicate_restricted_source_into_own_page_translation / test_add_translation_from_restricted_page_type (check_in_from_source.patch) |
| T2 target change | site narrowing only | yes: test_add_translation_to_page_user_cannot_change, test_duplicate_into_page_user_cannot_change (target_site_only.patch, no_target_check.patch) |
| T2 cross-site | change check against the current site | yes: test_duplicate_into_page_of_another_site (target_check_current_site.patch) |
| T3 page-type source | fix only the duplicate form (published fix) / wizard only | yes: PageTypeSourceTests add tests (published_fix_only.patch, wizard_only_page_types.patch, tempting_duplicate_only.patch) |
| T4 wizard | check in the admin view or in base `clean()` | yes: test_wizard_page_from_restricted_page_type (admin_only_check.patch, check_in_base_clean.patch) |
| crash as refusal | `assert` → 500 | yes: assertRefused status < 500 (crash_on_unviewable.patch) |
| over-hardening | refuse all / require change on page types / refuse restricted types / refuse translations / check in `Page.copy` | yes: functional tests (the five functional_fail patches) |

**Wrong fixes no test catches:**

1. **Source view check evaluated against the current site, not the source's site (HIGH).**
   `user_can_view_page(user, source)` with no `site=` defaults to the current site **(inferred)**.
   A site-1 global manager has "view all pages" on site 1, so the helper returns True for a
   *view-restricted page on site 2*. That lets them duplicate it (hidden source spans all sites,
   per the oracle's own comment) or post a site-2 restricted page type in the add form/wizard
   (the oracle does not narrow that queryset to the site). This breaks bullet 1, "a page the
   requesting user is not allowed to view". **The oracle (fix.patch) and alt_form_clean.patch
   (page-type branch) appear to contain this hole.** Only hardening.patch (`site=source.site` plus
   the site-narrowed page-type queryset) closes it. It is the source-side twin of T2's cross-site
   shape, which *is* tested.
2. Refusing every translation+source combination (hardening.patch does this) removes a
   legitimate feature ("exactly as today") and passes. Upstream main does the same, so this is
   acceptable. Note it, but do not add a test.
3. Hidden `parent_page` not re-checked against add rights: out of scope per notes. Fine.

## 3. Hints

- "whatever way the page to copy from is supplied" paraphrases the variant list (body / URL /
  page-type dropdown / wizard). "No request that creates a page or a translation" already covers
  everything. **Remove the clause.**
- "unless that page belongs to the site being administered and the requesting user may change it"
  names the T2 cross-site shape outright and pre-empts T2's dismissal ("belongs to Add
  translation"). Bullet 2 itself is needed for fairness: no other sentence requires a change check
  on the target. Neutral wording: "No request may add a translation to an existing page that the
  requesting user may not change." The cross-site test stays fair under that wording, because a
  site-1 manager may not change site-2 pages. Recommended, not blocking.
- "(placeholders, plugins, extensions)": mild, describes the effect and not the fix. OK.
- "The request above is one example, not the full set of affected requests": standard. OK.
- No leak_terms appear (no "page type", "wizard", form/function/file names, flaw count).

## 4. Realism

All four traps are unmodified upstream code at the pinned commit: T1/T2 are published fix sites,
and T3/T4 stay open after the published fix and were closed later upstream. Every one is reached
through the real admin and wizard HTTP endpoints. Nothing looks planted. Minor: fix.patch also
bundles unrelated upstream CWE-269 (group permissions) and CWE-79 (`validate_url`) changes. They
are harmless to grading, but the oracle is not minimal.

## 5. Verdict: NOT READY

Required:
1. Add a security test: a site-1 manager duplicates a board-restricted **site-2** page (source in
   the body of a duplicate form on a site-1 page). If item 1 of §2 is confirmed, also test a
   restricted site-2 page type posted to the site-1 add form. Update fix.patch to check view on
   the source's own site (as hardening.patch does) and narrow the page-type queryset to the site.
   Fix alt_form_clean.patch the same way. Re-run all patch_checks; published_fix_only should
   still fail. If running shows the helper is *not* current-site-dependent for view, record that
   in notes.md and drop this item.
2. Redirects. Either add to instruction.md "Answering a refused request with a redirect is not
   acceptable.", or loosen `assertRefused` to accept 3xx when the snapshot is unchanged and there
   is no `cms-view-new-object`. Loosening is preferred: the snapshot already proves the refusal.
3. Remove "whatever way the page to copy from is supplied" from bullet 1.

Recommended: reword bullet 2 as in §3.
