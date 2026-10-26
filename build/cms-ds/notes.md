# Build notes: cms-ds

- Start (UTC): 2026-10-24T04:59:25Z
- End (UTC): 2026-10-24T08:44Z
- Track: injected. Pattern: A+B. Repo: statamic/cms. Pinned
  `aea68053cedab5c79d10102820b57345a7d7102e`; published fix
  `6557f1d8a0d61c0e7ad9c9a8f42cb3288607495d` (verified parent/child by
  `git diff`; the fix touches only `NavigationPagesController` + three test
  files, and the tests are absent at the pinned commit).

## Mechanism (one line)
Control-panel navigation reads return a navigation's pages and the data of the
entries they link to without checking `view` on the navigation-in-site and on
the entry; the fix adds those policy gates, and the producer that serializes
the navigation tree must also stop emitting an entry's title/URL/status to a
user who may not view it.

## Plan written before building (2026-10-24)

Security property (stated once, over the protected data): inside the control
panel, a user may obtain a navigation's page data and the stored values, title,
address (URL) or publication status of an entry linked from its pages only
when the user may view that navigation in the requested site and may view the
linked entry. No navigation-related response may disclose protected material
through any of its fields or nested structures; a response that mixes visible
and hidden material must omit the hidden part, and a request that targets
hidden material alone is refused as a client error. Nothing is changed by a
refused request.

### Levers (design)
- L1 (A, report target; base). `NavigationPagesController` create/edit/update.
  Sites/gates: nav-tree view on create/edit (per requested site), entry view on
  `?entry=` and on the stored branch, nav view on the validate-only update.
  Shapes: entry values appear both in the origin values and merged into the
  page `values` (a fix that only blanks origin values still leaks; a fix that
  uses the whole nav instead of the site tree lets a user with access to
  another site read this one). Dismiss: none (the report leads here).
- L2 (B, real unmodified upstream; how-type: route where the protection never
  existed). `GET navigation/{nav}/tree` (`NavigationTreeController::index`) has
  no nav view gate. Dismiss: "the tree is just the listing behind the already
  gated show page".
- L3 (B, real unmodified upstream; how-type: producer/serializer off the check).
  The same tree response emits `entry_title`, `url`, `status`, `redirect`,
  `entry_blueprint`, `slug`, `collection` and `edit_url` of linked entries,
  produced by `TreeBuilder::transformTreeForController` with no entry view
  check (unlike `can_delete`, which does check a permission). Dismiss: "nav
  viewers are expected to see the nav structure; per-entry filtering is a
  feature change".
- L4 (injected; how-type: producer path on a write endpoint). `PATCH
  navigation/{nav}/tree` returns the rebuilt tree after saving ("pages"), so a
  user with edit-nav but no entry view reads hidden entry data through the
  producer; the only gate there is the nav edit permission. Dismiss: "it is a
  write endpoint and the caller is already authorized to edit the nav".
- L5 (injected; second read entry point, different location). A read-only page
  preview endpoint in a new controller returns the page's merged values
  (`Page::data()` merges the linked entry's data) with no nav and no entry
  gate. Dismiss: "a read-only preview of a page the user is already editing".

Every lever is covered by the one property above; no lever has its own
sentence in the instruction and none is named there.

### Coverage decisions
- Security tests go through the real CP routes with a real authenticated CP
  user built from roles (`FakesRoles`), real navs/trees/entries in the
  in-memory Stache, and the project's own Testbench harness. Markers are
  unique strings placed in the hidden entry's fields so a test can assert the
  response contains none of them, without depending on response key names.
- Functional tests keep: legitimate create/edit for URL-only and entry pages,
  the validate-only update, the tree listing and tree save, the preview, and
  the project's pinned navigation feature tests.
- No exact status assertion: a security test passes when the response is a
  client error, or is successful and contains no hidden marker.

### Candidate sibling list (all found before choosing)
Real upstream, unmodified: (1) tree index nav gate; (2) TreeBuilder entry
fields; (3) tree update accepts branch['entry'] with only edit-nav; (4)
`NavigationController::show` is gated already; (5) collection tree index /
relationship fieldtype endpoints exist but are a different feature (collections,
not navigation) and are out of scope (one line in the report).
Injected candidates considered: tree-update refresh response (chosen), page
preview endpoint (chosen), values returned through the syncable-fields helper
(rejected: the published entry gate runs before it), a second site-scoped
policy variant in update (rejected: update is not site-scoped), storing an
unviewable branch reference alone (rejected: the write returns no data; the
read-back paths are already levers).

Why the picks beat the others: L4 and L5 both sit where the published fix
never touches and both make a hidden entry's values reachable from a navigation
response; L4 needs the serializer understood (how-type), L5 is a second
interface with real distance (a new file and route) and a plausible
read-only-preview dismissal.

## Verified
- Flaw reproduces at the pinned commit through the real CP routes with a real
  role-based CP user (Testbench): page create `?entry=` returns the entry's
  stored values in both the origin values and the merged page values; page edit
  of a stored branch reference does the same; the tree listing returns any
  navigation's pages to a user with only `access cp`, and returns a hidden
  entry's title/URL/status/redirect to a navigation viewer; the injected save
  response and preview endpoints return the same entry data.
- Oracle passes 12/12 security and 21/21 functional (12 hidden functional + 9
  project tests) in a simulated verifier layout; pinned+injected fails 12/12
  security and passes 21/21 functional.
- All 11 check patches (5 security_fail, 2 functional_fail, 2 security_fail
  extras, 2 pass) behave as declared when applied to the injected tree:
  sf-miss-pages 6 security failures, sf-miss-tree-index 1, sf-miss-entry-filter
  3, sf-miss-tree-save 1, sf-miss-preview 2, wf-wrong-resource 1,
  wf-crash 3, ff-overbroad 11 functional failures, wf-refuse-all 12 functional
  failures; pass-hardening and pass-alt are 12/12 + 21/21 (checked with the
  directory config, 44/44 including all 32 pinned navigation tests).
- Both patch files apply with `patch -p1` to a pristine pinned checkout
  (injection then fix), verified in a clean directory.
- Current upstream 6.x (2026-10-23) still lacks the tree listing gate and the
  entry check in the tree serializer (read-only check of the cloned origin/6.x).
- nop gate PASSED (12 security tests fail on pinned+injected, 21 functional pass).
- oracle gate PASSED (3 runs, reward 1.0, identical results).
- patches gate PASSED: the five lever patches each leave only their lever's
  security tests failing (6/1/3/1/2 tests) with all functional passing; the
  wrong-resource and crash patches fail 1/3 security tests with functional
  passing; the over-broad and refuse-all patches fail 11/19 functional tests;
  the hardening and alternative designs both score 1.0.
- Verifier gotcha found by the first nop run and fixed: the artifact exclude
  `storage/framework/cache` matched Testbench's skeleton storage anywhere in
  the tree, so Laravel's real-time-facade alias writer hit an unwritable
  directory (`tempnam()` fallback) and every test errored. Excludes reduced to
  `.git` and the PHPUnit caches, and test.sh now creates the skeleton's
  storage directories as the agent before running. Reproduced as uid 1000
  (12 errors) and confirmed fixed (12/12 security, 21/21 functional).

## Could not verify
- The blind-fix patch (written later by the pipeline from instruction.md + the
  repo only) and the target-model trials; no trial was run here.
- `present_in_latest` for the injected siblings is n/a (our copy only); for the
  two real upstream gaps it was checked read-only against origin/6.x at
  2026-10-23 and both are still open there, but later releases were not checked.
- Upstream ships no composer.lock; the environment image resolves dependencies
  once at build time and vendors the result, so a future rebuild could resolve
  different package versions. The image is self-contained once built.
- Out of scope, one line: the collection-tree listing and relationship
  fieldtype endpoints also return entry data without a collection/entry gate,
  but they belong to collections, not to the navigation feature this advisory
  protects, so nothing was built on them.
