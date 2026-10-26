# Pre-trial fairness and leniency review — siyuan-ds

Read-only review (nothing executed): `tasks/siyuan-ds/instruction.md`, every file
under `tasks/siyuan-ds/tests/` (`score.py`, `test.sh`, `junit.py`, both harness
fixtures, both security tests, both functional tests, the five restored project
test files), `tasks/siyuan-ds/solution/fix.patch`, `build/siyuan-ds/manifest.json`,
`build/siyuan-ds/notes.md` and all ten `build/siyuan-ds/checks/*.patch`.
Docker, trials and gates were not run; the upstream fix was not consulted online.

The solver sees only `instruction.md` and the repository. The hidden tests drive
package-internal route-registration functions (`serveTemplates`, `serveExport`,
`serveWidgets`, `servePlugins`, `serveEmojis`, `serveSnippets`,
`serveSnippetPreview`, `servePublishPreview`) and the real API handlers with a
role on the gin context. That is normal for this repository's own tests and is
noted once here rather than repeated in every row.

Authority abbreviations used below:

- **I1** — "No template file, generated export artifact, or snippet that is not
  published to the visitor may be returned, under any request method."
- **I2** — "A plugin may be returned only when it is installed, enabled in this
  workspace, and not marked as excluded from publishing."
- **I3** — "A widget package or custom emoji file may be returned only when it is
  not marked as excluded from publishing and a document the visitor can read
  uses it."
- **I4** — "Anything the visitor may not receive must not be described either:
  listings and catalogs of these resources must expose only entries the visitor
  may receive."
- **I5** — the path/symlink/directory invariant.
- **C1** — "A refusal is a client error (a 4xx response, or a result object with
  a negative code and no file bytes)."
- **C2** — "A resource that is published to a reader keeps being served exactly
  as today, from the same address and with the same content; the same holds for
  its entry in any listing or catalog that already includes it."
- **C3** — "The workspace owner keeps unrestricted access … and keeps seeing
  complete listings."
- **C4** — "Apply the rules to every route that can return these resources and
  to every listing that describes them."
- **EK** — standard expert knowledge: the repository's existing tests must keep
  passing, and a correct fix does not change unrelated behaviour.

---

## 1. Test-by-test fairness

### Security tests (16)

| file::name | what it asserts | instruction sentence / expert knowledge making it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `security/server_static_access_test.go::TestPubAccessTemplateRefusedToReader` | reader GET `/templates/tprivate.md` is 4xx and carries no `TEMPLATE_MARKER` | I1 (no template that is not published is returned); a bare `.md` file has no publish metadata | no. A fix that keys templates on package metadata still refuses a package-less file. Residual: a fix that treats unmarked bare files as published would fail (this is the same ambiguity as the row for the template listing) | medium |
| `…::TestPubAccessExportArtifactRefusedToReader` | reader GET `/export/artifact.txt` and `/export/temp/artifact2.txt` are 4xx, no markers | I1 ("generated export artifact") + C4 ("every route"); exports have no publish mechanism | no — a fix that admin-gates the export group, or the handler, passes. Guarding only plain `/export/` but not `/export/temp/` would fail (that is the trap, not a correct fix) | low |
| `…::TestPubAccessUnreferencedWidgetRefusedToReader` | reader GET **and HEAD** `/widgets/secretpkg/` are 4xx, no marker | I3 ("a document the visitor can read uses it") + I1 ("under any request method") | no | low |
| `…::TestPubAccessPublishDisabledWidgetRefusedToReader` | reader GET `/widgets/offpkg/index.html` (referenced but excluded) is 4xx | I3 ("not marked as excluded from publishing") | no | low |
| `…::TestPubAccessUnreferencedEmojiRefusedToReader` | reader GET `/emojis/refpack/b.png` (unreferenced) and `/emojis/offpack/c.png` are 4xx | I3 (custom-emoji clause, file-level: "custom emoji file") | no — pack-level gating would fail, but the invariant names the file, so that is a wrong fix | low |
| `…::TestPubAccessPublishDisabledPluginRefusedToReader` | reader GET `/plugins/hiddenpkg/index.js` is 4xx | I2 ("not marked as excluded from publishing") | no | low |
| `…::TestPubAccessUnloadedPluginRefusedToReader` | reader GET `/plugins/unloadedpkg/index.js` is 4xx | I2 ("enabled in this workspace") | no | low |
| `…::TestPubAccessPublishDisabledSnippetRefusedToReader` | reader GET `/snippets/hidden.js` (in snippet config, switch off) is 4xx | I1 + the snippet clause ("its publish switch is on") | no | low |
| `…::TestPubAccessFilesystemSnippetRefusedToReader` | reader GET `/snippets/fallback.css` (on disk, absent from config) is 4xx | I1 ("a file that merely exists on disk is not published") | no | low |
| `…::TestPubAccessNestedSymlinkEscapeRefusedToReader` | reader GET `/widgets/linkedpkg/escape/gone.txt` (nested symlink resolves outside) is 4xx | I5 ("symbolic links inside a package that resolve outside it") | no | low |
| `…::TestPubAccessPreviewResolverRefusedToReader` | reader gets 4xx, no body, through `/publish-preview/` for a template, a disabled snippet, a disk-only snippet, an unreferenced widget, an unreferenced emoji and an excluded plugin | C4 + the individual invariants; the route is registered from `Serve()` and visible in the repo | no — the only danger is admin-gating the whole route, which violates C2 and is caught by the paired functional test | medium |
| `…::TestPubAccessSnippetPreviewRefusedToReader` | reader GET `/snippet-preview?name=hidden&type=js` is 4xx, no content | I1 + C4 (a snippet returned by a query-param helper is still a snippet) | no — same C2/C4 qualification as the preview-resolver row | medium |
| `security/api_listing_access_test.go::TestPubAccessReaderPluginListingFiltered` | reader plugin listing is 200, omits `hiddenpkg` and `unloadedpkg`, keeps `openpkg` | I4 + I2 + C2 ("the same holds for its entry in any listing") | no — admin-gating the endpoint would remove `openpkg` and violate C2 | low |
| `…::TestPubAccessReaderWidgetListingFiltered` | reader widget listing is 200, omits `secretpkg` and `offpkg`, keeps `refpkg` | I4 + I3 + C2 | no | low |
| `…::TestPubAccessReaderTemplateListingFiltered` | reader template listing body does not contain `hiddentpl`; status is not checked | I4 ("only entries the visitor may receive") — but the instruction never says templates are never published, and the fixture's `hiddentpl/template.json` has `disabledInPublish:false` while the instruction says "packages can be marked as excluded from publishing" | **maybe** — a fix that applies the stated package-exclusion rule to template packages treats `hiddentpl` as published, lists it, and fails. Neither reading of the instruction is excluded by the text; no test disambiguates. See gate 5a | **high** |
| `…::TestPubAccessReaderEmojiConfFiltered` | reader emoji catalog is 200, omits `refpack/b.png` and `offpack/c.png`, keeps `refpack/a.png` | I4 + I3 + C2 | no — pack-level rather than file-level filtering fails, but that is a wrong fix | low |

### Functional tests (12)

| file::name | what it asserts | instruction sentence / expert knowledge making it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `functional/server_static_use_test.go::TestPubUsePublishedResourcesServedToReader` | reader gets the referenced widget, referenced emoji, publish-enabled snippet and enabled plugin, 200 + content | C2 ("keeps being served exactly as today, from the same address and with the same content") | no | low |
| `…::TestPubUseDirectoryRequestServesIndex` | reader GET `/widgets/refpkg/` is 200 with the index content | I5 ("a request for a directory, keep working (the directory's index file is returned)") | no — explicitly stated | low |
| `…::TestPubUseSymlinkedPackageDirectoryServed` | reader GET `/widgets/sympkg/` (top-level package directory is a symlink outside `data/widgets`) is 200 | I5 ("A top-level package directory that is itself a symbolic link … keep working") | no — explicitly stated; a naive "resolved target must stay under `data/widgets`" check would fail, but the instruction forbids that | medium |
| `…::TestPubUseAdministratorKeepsStaticAccess` | owner gets template, plain and temp export, disk-only and disabled snippets, excluded widget, unreferenced emoji and excluded plugin | C3 ("keeps unrestricted access … to templates, exports, snippets, plugins, widgets and emoji") | no | low |
| `…::TestPubUsePreviewResolverServesPublishedResources` | reader gets the published widget/emoji/snippet/plugin through `/publish-preview/` | C2 ("from the same address") + C4 | no — admin-gating the preview route would violate C2; medium risk because the route's own comment invites that mistake | medium |
| `…::TestPubUseSnippetPreviewServesEnabledSnippet` | reader gets the publish-enabled snippet through `/snippet-preview` | C2 + C4 | no — same C2 qualification; medium risk because the injected comment calls it a settings-panel helper | medium |
| `…::TestPubUseAdministratorKeepsPreviewAccess` | owner gets a template and a disabled snippet through the two preview routes | C3 | no | low |
| `…::TestPubUseTraversalStaysRefused` | a `%2e%2e` request through `/snippets/` must not return the template marker (any status; a 200 with empty/redirected body passes) | I5 ("Path spellings that climb out … must never yield a file outside the served directory") | no — any refusal or non-marker response passes | low (weak assertion; leniency U4) |
| `functional/api_listing_use_test.go::TestPubUseAdministratorListingSeesEverything` | owner plugin/widget/template listings are 200 and contain every installed entry | C3 ("keeps seeing complete listings") | no | low |
| `…::TestPubUseReaderListingKeepsPublishedPackages` | reader plugin/widget listings are 200 and keep `openpkg` and `refpkg` | I4 + C2 | no | low |
| `…::TestPubUseAdministratorEmojiConfSeesEverything` | owner emoji catalog keeps all three custom emoji | C3 | no | low |
| `…::TestPubUseReaderEmojiConfKeepsReferencedEmoji` | reader emoji catalog keeps `refpack/a.png` | I4 + C2 | no | low |

### Restored repository tests (17; run as functional)

These are the pinned repository's own tests, restored from `/tests` because the
agent may edit `/app`. They are visible to the solver, exercise no publish-mode
access decision the fix needs to change, and are fair under EK and "Keep
legitimate use working".

| file::name | what it asserts | authority | correct fix could fail? | risk |
|---|---|---|---|---|
| `functional/project/serve_assets_test.go::TestIsValidAssetRequestPath` | existing asset-path validation (dot segments, encoded paths) | EK | no | low |
| `…::TestAssetRequestPathURLDecoding` | existing `/assets/` URL-decoding behaviour | EK | no | low |
| `functional/project/serve_svg_test.go::TestServeSVGSanitizesAndSetsSecurityHeaders` | SVG sanitisation and CSP/nosniff headers | EK | no | low |
| `…::TestServeSVGPreservesAllowSVGScriptBehavior` | `AllowSVGScript` still works | EK | no | low |
| `functional/project/publish_access_test.go::TestCheckBlockTreeAccessableByPublishAccess` | publish access for a document (disabled, password, hidden) | EK / pre-existing semantics | no | low |
| `…::TestCheckBlockTreeMetadataAccessableByPublishAccess` | metadata vs discoverability and inheritance | EK | no | low |
| `…::TestCheckAttributeViewItemIDAccessableByPublishAccess` | attribute-view item access | EK | no | low |
| `…::TestCheckAttributeViewBlockTreesAccessableByPublishAccess` | attribute-view mirror access | EK | no | low |
| `…::TestFilterAttributeViewRelatedValuesByPublishAccess` | response-only filtering of AV relations/rollups | EK | no | low |
| `…::TestFilterAttributeViewRelatedValuesKeepsPublicResponse` | fully public AV responses unchanged | EK | no | low |
| `…::TestFilterSearchDocsByPublishAccess` | search results filtered by publish access | EK | no | low |
| `…::TestFilterGraphByPublishAccess` | graph nodes/links filtered | EK | no | low |
| `…::TestFilterEmbedBlocksByPublishAccessRemovesInternalFields` | embed internal fields stripped | EK | no | low |
| `…::TestFilterEmbedBlocksByPublishAccessDropsInaccessibleResults` | inaccessible embeds dropped | EK | no | low |
| `functional/project/block_test.go::TestFilterBlockIDsByPublishAccess` | block-ID filtering for reader and owner | EK | no | low |
| `functional/project/filetree_test.go::TestFilterFileTreePublishAccess` | file-tree paths/IDs filtered, owner unfiltered | EK | no | low |
| `…::TestSetSortRejectsInvalidRequest` | unrelated `setSort` input validation | EK | no | low |

---

## 2. Leniency (quality, non-blocking)

### 2a. Security properties vs the most plausible wrong fix

| property | most plausible wrong fix | caught by | residual gap |
|---|---|---|---|
| P1 templates/exports are owner-only | admin-gate `/templates/` only, or guard `/export/` but not `/export/temp/`; alternatively compare `role == RoleReader` only | `TestPubAccessTemplateRefusedToReader`, `TestPubAccessExportArtifactRefusedToReader`; `checks/sf-miss-templates-export.patch` removes both group gates (models the all-or-nothing miss, not the partial) | U1 (a reader-only gate leaves `RoleVisitor` open) |
| P2 snippets: config entry + switch on, no disk fallback | check `DisabledInPublish` only for names found in the config and leave the `c.File` fallback for readers | `TestPubAccessFilesystemSnippetRefusedToReader`; no check patch isolates exactly this miss — `sf-miss-snippets.patch` instead drops the snippet-preview toggle, caught by `TestPubAccessSnippetPreviewRefusedToReader` | U5 (no HEAD on `/snippets/`), U7 (name with no type match) |
| P3 plugins: installed + enabled + not excluded | check the package JSON only (ignore loaded state), or accept any loaded petal (ignore `disabledInPublish`) | `TestPubAccessUnloadedPluginRefusedToReader`, `TestPubAccessPublishDisabledPluginRefusedToReader`; `sf-miss-plugins.patch` removes both the static check and the plugin listing filter | U9 (`IsPetalsEnabled`, `disallowInstall` never exercised) |
| P4 widgets/emoji: not excluded + used by a readable document | check only `disabledInPublish` with no reference producer; or accept any reference without the exclusion flag; or deny all | `TestPubAccessUnreferencedWidgetRefusedToReader`, `TestPubAccessPublishDisabledWidgetRefusedToReader`, `TestPubAccessUnreferencedEmojiRefusedToReader`; `sf-miss-widgets-emojis.patch`; deny-all is caught functionally (`ff-overbroad.patch`, `TestPubUsePublishedResourcesServedToReader`) | U2 (reference producer not restricted to readable docs), U3 (reference spellings/node kinds/nested emoji) |
| P5 listings/catalogs describe only receivable entries | filter the static routes and leave `getInstalledPlugin`/`getInstalledWidget`/`getInstalledTemplate`/`getEmojiConf` untouched; or filter only plugins | four API security tests; `sf-miss-listings.patch` (the helper is defined but the call sites are removed) | U6 (template listing status/empty list not asserted), U10 (counts/totals) |
| P6 containment: no escape, top-level symlink and directory index keep working | lexical `gulu.File.IsSubPath(rootAbsPath, targetPath)` without resolving symlinks; or reject the top-level symlinked package; or do not map a directory to `index.html` | `TestPubAccessNestedSymlinkEscapeRefusedToReader`; `sf-miss-symlink.patch` replaces the resolved comparison with a lexical one; `TestPubUseSymlinkedPackageDirectoryServed`; `TestPubUseDirectoryRequestServesIndex` | U4 (no security traversal test on other routes) |
| P7 published resources and owner access survive | admin-gate all static routes; or blank the reader listings | functional suite; `ff-overbroad.patch` (its `FilterInstalledPackagesForPublishAccess` also has an early `return []*bazaar.Package{}`, which empties the reader listing), `TestPubUseReaderListingKeepsPublishedPackages` | none material |
| refusal form | panic or 500 as "denial" | `assertRefused` requires 4xx, so every security test fails a 5xx | none |

### 2b. Traps in `manifest.traps`

| trap | most plausible wrong fix | caught by test(s) and check patch |
|---|---|---|
| T1 widgets/emojis producer | flag-only check with no per-document reference producer; or deny all widgets/emoji | `TestPubAccessUnreferencedWidgetRefusedToReader`, `TestPubAccessUnreferencedEmojiRefusedToReader`; `sf-miss-widgets-emojis.patch`; deny-all caught by `TestPubUsePublishedResourcesServedToReader`. Gaps U2, U3 |
| T2 snippets fallback | keep the disk fallback for readers / treat a disk-only file as publishable | `TestPubAccessFilesystemSnippetRefusedToReader`. **Mismatch:** the declared `security_fail_patch` `sf-miss-snippets.patch` actually removes the snippet-preview toggle (T9), not the fallback; no check patch models the fallback miss itself |
| T3 templates/export | guard templates but not exports, or guard plain exports but not `/export/temp/` | `TestPubAccessTemplateRefusedToReader`, `TestPubAccessExportArtifactRefusedToReader`; `sf-miss-templates-export.patch`. Gap U1 |
| T4 plugins | package JSON only (ignore loaded state), or loaded only (ignore exclusion) | `TestPubAccessUnloadedPluginRefusedToReader`, `TestPubAccessPublishDisabledPluginRefusedToReader`; `sf-miss-plugins.patch`. Gap U9 |
| T5 path shapes | lexical containment; reject the top-level symlinked package; or no index mapping | `TestPubAccessNestedSymlinkEscapeRefusedToReader`; `sf-miss-symlink.patch`; `TestPubUseSymlinkedPackageDirectoryServed`; `TestPubUseDirectoryRequestServesIndex`. Gap U4 |
| T6 marketplace listings | leave the bazaar endpoints alone, or filter plugins only | `TestPubAccessReaderPluginListingFiltered`, `TestPubAccessReaderWidgetListingFiltered`, `TestPubAccessReaderTemplateListingFiltered`; `sf-miss-listings.patch`. Gaps U6, U10 |
| T7 emoji catalog | leave `getEmojiConf` unfiltered, or filter by pack rather than file | `TestPubAccessReaderEmojiConfFiltered` (`refpack/b.png` must be absent); `sf-miss-listings.patch` |
| T8 publish-preview resolver | patch only the static groups; the name makes the resolver look already guarded | `TestPubAccessPreviewResolverRefusedToReader`; `sf-miss-preview.patch` |
| T9 snippet-preview | patch only `/snippets/` and not the query-param helper | `TestPubAccessSnippetPreviewRefusedToReader`; `sf-miss-preview.patch` and `sf-miss-snippets.patch` |

The seven `security_fail` patches each leave at least one security test red,
`ff-overbroad` fails the functional suite, and the two `pass` patches
(`pass-hardening`, `pass-alt`) exercise a different correct design (decision at
the file-serving seam) and pass. That part of `manifest.patch_checks` is sound,
apart from the T2 patch mismatch noted above.

### 2c. Wrong fixes no test catches

- **U1 — role scope.** Every hidden test uses only `model.RoleReader` and
  `model.RoleAdministrator`. The instruction says "any visitor who is not the
  workspace owner". A fix that gates `role == RoleReader` only leaves
  `RoleVisitor` open and passes every test. `wrong_fix_catalogue.one_role_or_direction`
  is not "n/a"; its rationale is wrong. **Medium/high.**
- **U2 — readable-document restriction.** Both fixtures contain exactly one
  document and the publish-access map is empty. A fix that collects
  widget/emoji references from every document, never asking whether the
  visitor can read the referencing document, passes. The instruction says "a
  document the visitor can read uses it". No check patch models a hidden,
  password-protected or forbidden referencing document. **Medium/high.**
- **U3 — reference input shapes.** The fixtures use only root-relative
  `/widgets/...` in an `ast.NodeWidget` and `/emojis/...` in an
  `ast.NodeEmojiImg`. Relative paths, localhost-absolute URLs, HTML-escaped
  attribute values, HTML block/inline-HTML nodes, and nested emoji
  subdirectories are claimed by `manifest.traps[T1].shape` and the notes but
  are not tested. **Medium.**
- **U4 — traversal.** The only traversal assertion is the functional
  no-marker check on `/snippets/`; a 200 with an empty or redirected body
  passes, and no security test requests a climbing spelling on `/widgets/`,
  `/plugins/`, `/emojis/`, `/templates/` or `/export/`. **Medium.**
- **U5 — request methods.** HEAD is tested only on `/widgets/`; there is no
  HEAD test for templates, export, snippets, plugins or emojis, and no
  non-GET method on the listing APIs. **Low/medium.**
- **U6 — template listing assertion.** `TestPubAccessReaderTemplateListingFiltered`
  never checks the status code or that the package list is empty; a 5xx or a
  negative result with an empty body passes. **Low/medium.**
- **U7 — snippet type match.** No fixture has one name with two types; a
  check that ignores `type` passes. **Low.**
- **U8 — publish-preview default.** Only the five known top-level resource
  directories are requested; returning `true` for an unknown first segment
  passes (the oracle delegates those to `CheckAbsPathAccessableByPublishAccess`).
  **Low.**
- **U9 — plugin global state.** `IsPetalsEnabled` and `disallowInstall` are
  never exercised; dropping either still passes. **Low.**
- **U10 — listing metadata.** The listing tests string-match names; a response
  that omits names but still reports a total count including hidden packages
  passes. **Low.**

---

## 3. Hints in `instruction.md`

Every sentence below is (or supports) an invariant the tests depend on, so it
cannot simply be deleted; the proposal neutralises the mechanism/shape wording
while keeping the rule. None of the proposals changes an asserted behaviour.

| quote | what it gives away | proposed neutral wording |
|---|---|---|
| "Besides documents, the workspace holds other resources: plugins, widgets, custom emoji packs, code snippets, document templates and generated export files." | the exact six-class variant list | "Besides documents, the workspace holds several other kinds of resource." (the invariants still name the classes the tests cover) |
| "The owner decides which of these are published: packages can be marked as excluded from publishing, snippets have their own publish switch, and a reader is meant to receive only the widgets and custom emoji that documents published to them actually use." | names the exclusion flag, the snippet switch and the hardest producer rule | "Publication state is recorded per resource; a reader receives only resources published to them, and widgets or custom emoji only when a document available to them uses them." |
| "A snippet may be returned only when the snippet configuration contains it and its publish switch is on; a file that merely exists on disk is not published." | names the configuration requirement and the disk-fallback trap (T2) | "A snippet is returned only when it is configured as published; mere presence on disk does not publish it." |
| "A plugin may be returned only when it is installed, enabled in this workspace, and not marked as excluded from publishing." | the exact three-part predicate (T4) | "A plugin is returned only when it is active in this workspace and not withheld from publishing." |
| "A widget package or custom emoji file may be returned only when it is not marked as excluded from publishing and a document the visitor can read uses it." | the per-document producer rule (T1) | "A widget or custom emoji is returned only when it is not withheld from publishing and a document available to the visitor uses it." |
| "Path spellings that climb out of a resource directory, and symbolic links inside a package that resolve outside it, must never yield a file outside the served directory. A top-level package directory that is itself a symbolic link, and a request for a directory, keep working (the directory's index file is returned)." | names traversal, symlink resolution and the index-file mechanism (T5) | "Requests must never resolve outside the served resource directory, while a directory request keeps returning the directory's default file and a supported symlinked-package layout keeps working." |
| "Anything the visitor may not receive must not be described either: listings and catalogs of these resources must expose only entries the visitor may receive." | names the listing/catalog levers (T6/T7) | "Metadata about a resource must not reveal a resource the visitor may not receive." |
| "**Observed impact.** A visitor … was able to download a document template, a generated export of a note, and a code snippet that the owner had explicitly excluded from publishing. The same visitor could enumerate installed packages that were excluded from publishing, and saw custom emoji that no published document used." | a near-complete flaw list: the tested resource classes and both metadata endpoints | "**Observed impact.** A reader could obtain resources the owner had withheld from publishing, and could learn about unpublished resources through metadata endpoints." |
| "The examples above are examples, not the full set. Apply the rules to every route that can return these resources and to every listing that describes them." | signals a non-exhaustive example set / extra routes (T6–T9) | "Apply the same rules to every route and every listing that exposes these resources." |
| "A refusal is a client error (a 4xx response, or a result object with a negative code and no file bytes). The tests accept any 4xx status." | test-facing phrasing; the solver cannot see the tests | "A refusal must be a 4xx response (or a negative result code with no file bytes); do not return 2xx or 5xx." |
| "The workspace owner keeps unrestricted access to templates, exports, snippets, plugins, widgets and emoji, and keeps seeing complete listings." | repeats the class list | "The workspace owner keeps unrestricted access to all of these resources and to complete listings." |

Sentences that should stay as-is: "under any request method" (needed by the HEAD
test), "Keep legitimate use working", "Do not special-case the examples", "Fix
the reported problem and its close variants". No sentence names a file,
function, route, field, CVE/GHSA, flaw count or line number.

---

## 4. Realism

- **T1–T5** are the published fix's own sites (`kernel/server/serve.go`,
  `kernel/model/publish_resource_access.go`). The fixtures use the real
  kernel data directory layout, `treenode`/`filesys`, the snippet config and
  the petal storage. These are code a maintainer could have written, and they
  are reachable through the real `Serve()` registration functions. The
  top-level symlinked package (`sympkg`) is an explicitly supported install
  layout, not a contrivance. Realistic.
- **T6–T7** (`kernel/api/bazaar.go`, `kernel/api/system.go`) are real,
  unmodified upstream code at the pinned commit, driven through the real
  `CheckAuth` handlers. Realistic.
- **T8 (`servePublishPreview`) and T9 (`serveSnippetPreview`)** are injected.
  Both are registered from `Serve()`, use the real middleware, and match the
  file's style and Chinese comments, so a maintainer could have written them.
  Two smells: (a) no in-repo caller exists, so an auditor may read them as dead
  code; (b) the `serveSnippetPreview` comment calls it a settings-panel
  preview, which in the real product would invite `CheckAdminRole` — exactly the
  `ff-overbroad` mistake. The contract C2 resolves the ambiguity, but the
  comment pulls the other way. Mildly contrived; add a caller/comment or a
  frontend-contract note.
- **Template fixture smell.** The reader template-listing test uses a package
  whose `template.json` says `disabledInPublish:false` but requires it to be
  hidden. That is the gate-5a ambiguity. It looks like a deliberate fixture
  choice to force the "templates are never published" rule that the
  instruction does not state.
- **Harness placement.** The fixtures build their own gin engines and call the
  per-route registration functions, not `Serve()` or the API router. A correct
  fix implemented only as `Serve()`-level or router-level middleware would not
  be exercised. This is a synthetic-harness limitation, not a planted trap; the
  `pass-alt` patch shows at least two handler-level designs are accepted.
- **Reference-shape claims.** The fixtures' single root-relative reference in
  two node types is realistic as far as it goes, but it does not match the
  shape list in `manifest.traps[T1].shape` and `notes.md`. That is a coverage
  overclaim, not planted code (see U3).

---

## 5. Verdict — two gates

### 5a. Unfairness gate (the only blocking gate): **NOT READY**

**Reason.** `security/api_listing_access_test.go::TestPubAccessReaderTemplateListingFiltered`
requires the reader's installed-template listing to omit `hiddentpl`, while the
fixture's `templates/hiddentpl/template.json` is written with
`disabledInPublish:false`. The instruction says (a) "packages can be marked as
excluded from publishing" and (b) "No template file … that is not published to
the visitor may be returned". A competent engineer can read that as: a template
package that is not marked excluded is published, so its entry belongs in the
reader's listing. That fix is otherwise consistent with every other sentence
and every other test, but it fails this one. The instruction never says
templates (or exports) have no publish mechanism, and no test supplies a
positive/negative pair that resolves the ambiguity. This is an unresolved
"maybe" in the step-1 column — an ambiguous spec — so the task is not ready.

**Exact changes to remove the unfairness (either one is sufficient).**

- **Preferred — clarify the spec.** In `instruction.md`, rewrite the mechanism
  sentence to exclude templates from the exclusion-flag rule, e.g. "Plugin and
  widget packages can be marked as excluded from publishing; snippets have
  their own publish switch; a reader is meant to receive only the widgets and
  custom emoji that documents published to them actually use." and add to the
  invariants: "Template files and generated export artifacts have no publish
  mechanism in this workspace: no template file or export artifact is ever
  returned to, or described for, a visitor who is not the owner." This makes
  the oracle's admin-only template/export design explicit and keeps the test.
- **Alternative — fix the fixture.** In
  `tasks/siyuan-ds/tests/harness/api_pub_fixture_test.go` change
  `writeAPIPackage(t, "templates", "hiddentpl", "template.json", false)` to
  `true`, so the hidden template is explicitly excluded. Then both readings
  pass the listing test (the bare `.md` in the server fixture has no package
  metadata and is refused under either reading). This removes the unfairness
  without changing the oracle, but leaves the "templates never published"
  rule under-tested; combine it with the instruction sentence if that rule is
  intended.
- If the intended design is actually "non-excluded template packages are
  published", the **solution** and the template static route must change, and a
  positive reader-template test must be added. That is a larger change than the
  two above and conflicts with the published fix, so it is not recommended.

No other test meets the unfairness bar. The `/snippet-preview` and
`/publish-preview` admin-gating temptation is real (hence "medium" risk), but
C2 explicitly requires a published snippet/plugin/widget/emoji to keep being
served from the same address, so a fix that gates those routes is wrong, not
merely different. The top-level-symlink requirement is explicitly stated in
I5.

### 5b. Quality findings (recorded; NOT reasons for NOT READY)

See sections 2–4. The priority tightenings are in the companion summary below.

---

## Quality to tighten (non-blocking)

1. **U1 role scope.** Add `model.RoleVisitor` coverage for one static route and
   one listing, or narrow the invariant to the reader role and change
   `wrong_fix_catalogue.one_role_or_direction` from `n/a` to an explicit
   exemption.
2. **U2 readable-document rule.** Add a hidden/password-protected document that
   references a new widget and emoji; assert the reader is refused both while
   the public document's resources still serve.
3. **U3 reference shapes.** Extend `writeReferencingDocument` for a relative
   path, a localhost-absolute URL, an HTML-escaped attribute, an HTML
   block/inline-HTML node and a nested emoji directory — or delete those
   claims from `manifest.traps[T1].shape` and `notes.md`.
4. **U4 traversal.** Add a security test for `/widgets/%2e%2e/…` and
   `/snippets/%2e%2e/…` requiring 4xx and no marker; keep the functional test
   as the positive control.
5. **U5 methods.** Add HEAD refusals for plugins/emojis (and templates/export/
   snippets where registered).
6. **U6 template listing.** Assert `Code == 200` and an empty package list;
   reject 5xx and zero-body responses.
7. **U7 snippet type.** Add one name with two types and assert the type match.
8. **U8–U10.** Exercise the preview fallback for an unknown first segment,
   `IsPetalsEnabled`/`disallowInstall`, and listing totals/counts.
9. **T2 check patch.** `sf-miss-snippets.patch` models the snippet-preview miss,
   not the disk-fallback miss; add a dedicated fallback check patch or correct
   the manifest.
10. **Hints.** Neutralise the quotes in section 3; at minimum drop "The tests
    accept any 4xx status", the "examples are not the full set" sentence and
    the per-class impact list.
11. **Realism.** Give the two injected preview routes an in-repo caller or a
    frontend-contract comment, and soften the "settings panel" comment that
    invites `CheckAdminRole`.
12. **Template ambiguity.** Apply one of the 5a changes; this one is blocking,
    the rest are quality.
