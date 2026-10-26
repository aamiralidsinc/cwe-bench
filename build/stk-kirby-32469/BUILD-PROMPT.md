# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-kirby-32469`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 32469; authorization / missing permission check (CWE-862) on file upload, wit
- Pinned (vulnerable) commit: 58f819988436b31969078bc4655452dd48546451. Published fix: 37e206f3ed40ad3fab2e47e055ccb19e9c207dab.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-32469",
 "pattern": "H4",
 "repo": "getkirby/kirby",
 "pinned_commit": "58f819988436b31969078bc4655452dd48546451",
 "protections": [
  "Before any chunk byte is appended to site/cache/.uploads, the acting API user must be authorized for the operation the upload will perform: file `create` on a File built from the target parent and the declared template (files create route and field uploads), file `replace` on the target file (files replace route), or user `update` on the target user (avatar route); this must hold for every caller of the uploader, including a direct call to Upload::processChunk().",
  "The file template that selects the blueprint (and therefore the FilePermissions blueprint-`options` override and the maxsize/extension rules) must be the same value for the authorization decision, for chunk validation and for the final create - the constructor template argument wins over the request body (src/Api/Upload.php:243), and for field uploads the template exists only as that argument.",
  "The declared template and Upload-Length of the first chunk must be pinned for the lifetime of a chunked upload so that later requests cannot re-declare them for the same buffered upload.",
  "Chunk-time validation must judge the same filename that will be created; at the pinned commit it judges the id-prefixed tmp name instead (src/Api/Upload.php:234,356)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/Api/Upload.php:156",
    "src/Api/Upload.php:181",
    "src/Api/Upload.php:221",
    "src/Api/Upload.php:246",
    "src/Api/Upload.php:334"
   ],
   "reason_to_dismiss": "FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/Api/Upload.php:156-190",
    "src/Api/Upload.php:181-183",
    "src/Api/Upload.php:238-250",
    "src/Api/Upload.php:334-337",
    "src/Api/Upload.php:386-389",
    "src/Cms/FileRules.php:137-141",
    "src/Cms/FileRules.php:171-175",
    "src/Cms/UserRules.php:227-244",
    "src/Cms/UserRules.php:301-318",
    "config/api/authentication.php:18-24"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "src/Api/Upload.php:243",
    "src/Api/Upload.php:189",
    "config/fields/mixins/upload.php:82",
    "config/api/routes/files.php:56"
   ],
   "reason_to_dismiss": "The template looks like a normal request field, so an authorization check is naturally written against $this->api->requestBody('template'); but for field uploads the body never carries it - it arrives only as the Api::upload(template:) argument, so the check silently falls back to the default file blueprint while the constructor-argument template is the one the uploader and the create callback use.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "src/Api/Upload.php:34-40",
    "src/Api/Upload.php:243",
    "src/Api/Upload.php:187-190",
    "config/fields/mixins/upload.php:62-82",
    "config/fields/files.php:112-130",
    "config/fields/textarea.php:100-112",
    "config/api/routes/files.php:49-59",
    "tests/Api/UploadTest.php:650-681"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "config/api/routes/files.php:110-118",
    "src/Api/Upload.php:221-250"
   ],
   "reason_to_dismiss": "The replace route calls the same $this->upload() helper as the create route, so a fix written for the create path is assumed to cover it; and FileRules::replace() already enforces `replace` at commit, which reads as sufficient because replace acts on a file the user can already see.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "config/api/routes/files.php:110-118",
    "src/Cms/FileRules.php:169-175",
    "src/Cms/FileActions.php:419-448",
    "src/Cms/Api.php:94-99"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "config/api/routes/users.php:88-102",
    "src/Cms/UserActions.php:229-243",
    "src/Cms/UserActions.php:395-420"
   ],
   "reason_to_dismiss": "The advisory is about file uploads to page/site/account parents; avatars are a user property whose commit path already checks user `update` (src/Cms/UserRules.php:229,303) and whose template is hardcoded to 'avatar' (src/Cms/UserActions.php:235), so there is no declared template and no file `create` permission to check.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "config/api/routes/users.php:88-102",
    "src/Cms/UserRules.php:227-244",
    "src/Cms/UserRules.php:301-318",
    "src/Cms/UserActions.php:229-243",
    "src/Cms/UserPermissions.php:42-55",
    "src/Cms/UserPermissions.php:62-67"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M10",
   "origin": "published_fix_far_site",
   "locations": [
    "src/Cms/FilePermissions.php:16",
    "src/Cms/FilePermissions.php:21-24",
    "src/Cms/ModelPermissions.php:26-30",
    "src/Cms/ModelPermissions.php:93-119",
    "config/fields/mixins/upload.php:42-48"
   ],
   "reason_to_dismiss": "The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/Cms/FilePermissions.php:14-33",
    "src/Cms/ModelPermissions.php:24-30",
    "src/Cms/ModelPermissions.php:63-120",
    "src/Cms/File.php:158-165",
    "src/Cms/File.php:529-532",
    "config/fields/mixins/upload.php:42-48"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "src/Api/Upload.php:230-234",
    "src/Api/Upload.php:243",
    "src/Api/Upload.php:257",
    "src/Api/Upload.php:347-409"
   ],
   "reason_to_dismiss": "Chunk requests are stateless, so each request validating itself looks correct, and createFile() re-validates the finished file against its real template (src/Cms/FileRules.php:143-146); nothing at the pinned commit records the first chunk's template or Upload-Length, yet every later chunk re-reads both from its own headers/body and the completing request's values are the ones that reach the create callback.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "src/Api/Upload.php:226-250",
    "src/Api/Upload.php:232",
    "src/Api/Upload.php:243",
    "src/Api/Upload.php:252-259",
    "src/Api/Upload.php:347-353",
    "src/Api/Upload.php:364-374",
    "src/Api/Upload.php:376-401",
    "src/Cms/FileRules.php:143-146",
    "tests/Api/UploadTest.php:408-441"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Api/Upload.php:234",
    "src/Api/Upload.php:354-358",
    "src/Api/Upload.php:386-389",
    "src/Cms/FileRules.php:275-302"
   ],
   "reason_to_dismiss": "FileRules::create() re-runs validFile() on the real final filename at commit (src/Cms/FileRules.php:143), so the chunk-time check on the id-prefixed tmp name can be dismissed as an early best-effort check even though position-sensitive rules such as the leading-dot / '.ht' block cannot match a name like 'abcd-.htaccess'.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Api/Upload.php:230-234",
    "src/Api/Upload.php:354-358",
    "src/Api/Upload.php:386-389",
    "src/Api/Upload.php:264-267",
    "src/Cms/FileRules.php:285-301"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/Api/Upload.php:221-270",
    "src/Api/Upload.php:238-244"
   ],
   "reason_to_dismiss": "Upload::processChunk() is an internal helper whose only production caller is Upload::process() (src/Api/Upload.php:182), so an authorization check added one frame above it is assumed to cover every path - even though processChunk() is public, writes into site/cache/.uploads and is called directly by the existing unit tests (tests/Api/UploadTest.php:340-441).",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Api/Upload.php:221-270",
    "src/Api/Upload.php:246-250",
    "tests/Api/UploadTest.php:325-346",
    "tests/Api/UploadTest.php:348-441"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M3",
   "origin": "injection_room",
   "locations": [
    "src/Api/Api.php:638-652",
    "config/api/routes/files.php:49",
    "config/api/routes/files.php:114",
    "config/api/routes/users.php:89",
    "config/fields/mixins/upload.php:65"
   ],
   "reason_to_dismiss": "Api::upload() is a generic helper that receives an opaque closure and has no target model, so leaving authorization to its callers looks correct; the consequence is that the decision lives in four separate route closures instead of the shared lower layer, and every new or plugin caller of the public Api::upload() has to remember the same preflight.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/Api/Api.php:638-652",
    "src/Api/Upload.php:32-40",
    "config/api/routes/files.php:49-59",
    "config/api/routes/files.php:110-118",
    "config/api/routes/users.php:88-102",
    "config/fields/mixins/upload.php:55-83",
    "tests/Api/ApiTest.php:629-670"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T5",
   "T9"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "Once the first chunk's template is pinned (T6), a preflight that still resolves the template from the current request body (T2) becomes visibly inconsistent with the uploader, so T2's failure mode is easiest to observe only after T6 is fixed."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "A single generic authorization check in the shared uploader is the natural fix for T1, but a role that has files.replace without files.create (or a blueprint whose options grant replace but not create for the template) must still be able to finish the replace route; a create-only check placed in Upload::process() denies legitimate replaces."
  },
  {
   "a": "T1",
   "b": "T4",
   "what": "The same generic file-create check cannot serve the avatar route, whose authorization is user `update` on Find::user($id); applying it breaks every legitimate avatar upload."
  },
  {
   "a": "T2",
   "b": "T5",
   "what": "Resolving the template only from the request body (the easy way to build the permission subject) makes the check run against the default file blueprint for field uploads, so a template whose blueprint options grant create while the role does not will be refused - the coupled value and the permission subject must be taken together."
  },
  {
   "a": "T9",
   "b": "T1",
   "what": "Making Api::upload() fail closed (required preflight) closes T9 but breaks the existing library contract: tests/Api/ApiTest.php:629-670 calls Api::upload() with no authorization and tests/Form/Field/FilesFieldTest.php:17-29 overrides Api::upload() with the current four-parameter signature, so an added parameter must stay optional or that override becomes signature-incompatible."
  }
 ],
 "fairness_risks": [
  "Authorized chunked uploads must still complete unchanged, including the first-chunk-already-completes-the-file shortcut (tests/Api/UploadTest.php:325-346) and multi-request assembly (tests/Api/UploadTest.php:408-441); a preflight that refuses chunked requests outright denies every real chunked upload.",
  "Field uploads declare their template only as the Api::upload(template:) argument (config/fields/mixins/upload.php:82); a check that reads requestBody('template') denies or mis-decides them, and the existing test testValidateChunkTemplatePriority (tests/Api/UploadTest.php:650-681) pins the constructor argument as the winning value.",
  "A null/omitted template is legitimate and means the default file blueprint (config/api/routes/files.php:56, src/Cms/File.php:158-165); treating 'no template' as a refusal breaks default-template uploads.",
  "Library callers and test doubles call Api::upload() and Upload::process()/processChunk() with no target model (tests/Api/ApiTest.php:629-670, tests/Api/UploadTest.php:340-441, tests/Form/Field/FilesFieldTest.php:17-29); a mandatory or fail-closed preflight turns these into hard failures.",
  "Self-service permissions differ from other-user permissions (UserPermissions::category() returns 'user' for the acting user and 'users' otherwise, src/Cms/UserPermissions.php:62-67); a preflight that always checks the 'users' category refuses a role that may update its own account.",
  "A file blueprint can grant create for a role whose files category denies it (ModelPermissions::can() consults blueprint options first, src/Cms/ModelPermissions.php:93-116), so a role-only check refuses uploads that the commit path would allow.",
  "Non-chunked uploads (no Upload-Length header) never touch processChunk() (src/Api/Upload.php:181-183) and must keep their current behaviour; requiring chunk headers or a template on every request breaks them."
 ],
 "effort_minutes": 75,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T6"
  ],
  "why": "Five traps over four independent fix sites. T1 is the deepseek-type core: the protection is absent exactly where the buffer is written and there is a strong in-code reason to dismiss it (FileRules::create already throws at commit, and the uploader comment says the chunk will be validated again by createFile). T2 is the mimo-type coupled value: the template exists in three places (constructor argument, request body, default blueprint) and the existing test fixes the priority, so an over-hardened or body-only check breaks field uploads. T3 and T4 extend the same sink to the replace route (action `replace` on the target file, no template at all) and the avatar route (action `update` on the target user) - each needs its own preflight subject, so a fix that only wires the create route leaves them open while the diff looks complete. T6 is the second mimo-type trap: no state pins the first chunk's template and Upload-Length, so the values that drive chunk validation and the eventual create can be re-declared by a later request. All five are grounded in the pinned code, none depends on the advisory text, and the set forces four distinct judgements (where the check runs, which value it reads, which action/model it decides on, which request's declaration is authoritative) while the must-keep-working values (first-chunk shortcut, field uploads, self-avatar, replace-only roles) sit directly next to them. T5 is folded into the same fix site as T1/T2 and is covered by the T2 conflict; T7, T8 and T9 are recorded but left out of the design because they are outside the published permission fix (T7, T8) or are a public seam whose fail-closed variant collides with the existing test contract (T9)."
 },
 "unverified": [
  "The published fix commit 37e206f3ed40ad3fab2e47e055ccb19e9c207dab and the GHSA/CVE text were not available offline; every fix_sites, landing_point and sidecar claim is the screener's lead, checked only for consistency with the pinned code (no preflight, no Upload-Length persistence, readonly class, no authorization parameter on Api::upload()).",
  "No build or test run was possible (shell disabled in this session), so vendor/ completeness, PHP version and the PHPUnit result of the pinned suite are untaken from the screener record; the candidate record also reports built=False.",
  "Whether the hidden tests cover the replace route, the avatar route or a direct Upload::processChunk() call could not be determined; T3/T4/T8 are included on the assumption that the published fix touches them (screener fix_sites) rather than on observed tests.",
  "O8 present_in_latest for the public processChunk() path is unknown (no later upstream tree available).",
  "No H3 pair could be established: the two immediately preceding commits in this checkout are unrelated path-containment/disguise fixes, so a_fix_leaves_b_open and b_in_code_a_wrote are left null.",
  "Repository size in MB was not measured; no tiny_repo/giant_repo flag is implied.",
  "The claim that Api::upload() is used by plugins is the screener's; only the four in-repo call sites (config/api/routes/files.php x2, config/api/routes/users.php, config/fields/mixins/upload.php) were verified."
 ]
}
  ```
- Published fix sites:   - src/Api/Upload.php:156 — T1 M4 (reason to dismiss: FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).)
  - src/Api/Upload.php:181 — T1 M4 (reason to dismiss: FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).)
  - src/Api/Upload.php:221 — T1 M4 (reason to dismiss: FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).)
  - src/Api/Upload.php:246 — T1 M4 (reason to dismiss: FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).)
  - src/Api/Upload.php:334 — T1 M4 (reason to dismiss: FileRules::create() (src/Cms/FileRules.php:137-141), FileRules::replace() (src/Cms/FileRules.php:171-175) and UserRules::createAvatar()/replaceAvatar() (src/Cms/UserRules.php:229,303) already throw PermissionException at commit time, so the report can be read as an ordering detail about a temporary buffer that is never published; the uploader's own comment says the chunk is validated again by createFile() (src/Api/Upload.php:386-389).)
  - src/Api/Upload.php:243 — T2 M11 (reason to dismiss: The template looks like a normal request field, so an authorization check is naturally written against $this->api->requestBody('template'); but for field uploads the body never carries it - it arrives only as the Api::upload(template:) argument, so the check silently falls back to the default file blueprint while the constructor-argument template is the one the uploader and the create callback use.)
  - src/Api/Upload.php:189 — T2 M11 (reason to dismiss: The template looks like a normal request field, so an authorization check is naturally written against $this->api->requestBody('template'); but for field uploads the body never carries it - it arrives only as the Api::upload(template:) argument, so the check silently falls back to the default file blueprint while the constructor-argument template is the one the uploader and the create callback use.)
  - config/fields/mixins/upload.php:82 — T2 M11 (reason to dismiss: The template looks like a normal request field, so an authorization check is naturally written against $this->api->requestBody('template'); but for field uploads the body never carries it - it arrives only as the Api::upload(template:) argument, so the check silently falls back to the default file blueprint while the constructor-argument template is the one the uploader and the create callback use.)
  - config/api/routes/files.php:56 — T2 M11 (reason to dismiss: The template looks like a normal request field, so an authorization check is naturally written against $this->api->requestBody('template'); but for field uploads the body never carries it - it arrives only as the Api::upload(template:) argument, so the check silently falls back to the default file blueprint while the constructor-argument template is the one the uploader and the create callback use.)
  - config/api/routes/files.php:110-118 — T3 M1 (reason to dismiss: The replace route calls the same $this->upload() helper as the create route, so a fix written for the create path is assumed to cover it; and FileRules::replace() already enforces `replace` at commit, which reads as sufficient because replace acts on a file the user can already see.)
  - src/Api/Upload.php:221-250 — T3 M1 (reason to dismiss: The replace route calls the same $this->upload() helper as the create route, so a fix written for the create path is assumed to cover it; and FileRules::replace() already enforces `replace` at commit, which reads as sufficient because replace acts on a file the user can already see.)
  - config/api/routes/users.php:88-102 — T4 M1 (reason to dismiss: The advisory is about file uploads to page/site/account parents; avatars are a user property whose commit path already checks user `update` (src/Cms/UserRules.php:229,303) and whose template is hardcoded to 'avatar' (src/Cms/UserActions.php:235), so there is no declared template and no file `create` permission to check.)
  - src/Cms/UserActions.php:229-243 — T4 M1 (reason to dismiss: The advisory is about file uploads to page/site/account parents; avatars are a user property whose commit path already checks user `update` (src/Cms/UserRules.php:229,303) and whose template is hardcoded to 'avatar' (src/Cms/UserActions.php:235), so there is no declared template and no file `create` permission to check.)
  - src/Cms/UserActions.php:395-420 — T4 M1 (reason to dismiss: The advisory is about file uploads to page/site/account parents; avatars are a user property whose commit path already checks user `update` (src/Cms/UserRules.php:229,303) and whose template is hardcoded to 'avatar' (src/Cms/UserActions.php:235), so there is no declared template and no file `create` permission to check.)
  - src/Cms/FilePermissions.php:16 — T5 M10 (reason to dismiss: The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.)
  - src/Cms/FilePermissions.php:21-24 — T5 M10 (reason to dismiss: The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.)
  - src/Cms/ModelPermissions.php:26-30 — T5 M10 (reason to dismiss: The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.)
  - src/Cms/ModelPermissions.php:93-119 — T5 M10 (reason to dismiss: The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.)
  - config/fields/mixins/upload.php:42-48 — T5 M10 (reason to dismiss: The acting user's role carries a files.create / files.replace permission, so checking that role permission (or the permissions of the parent page/site/user) looks equivalent; it is not, because the decision must be made on a File object built from the target parent plus the declared template so that the file blueprint's `options` block, keyed by template, takes priority over the role defaults.)
  - src/Api/Upload.php:230-234 — T6 M6 (reason to dismiss: Chunk requests are stateless, so each request validating itself looks correct, and createFile() re-validates the finished file against its real template (src/Cms/FileRules.php:143-146); nothing at the pinned commit records the first chunk's template or Upload-Length, yet every later chunk re-reads both from its own headers/body and the completing request's values are the ones that reach the create callback.)
  - src/Api/Upload.php:243 — T6 M6 (reason to dismiss: Chunk requests are stateless, so each request validating itself looks correct, and createFile() re-validates the finished file against its real template (src/Cms/FileRules.php:143-146); nothing at the pinned commit records the first chunk's template or Upload-Length, yet every later chunk re-reads both from its own headers/body and the completing request's values are the ones that reach the create callback.)
  - src/Api/Upload.php:257 — T6 M6 (reason to dismiss: Chunk requests are stateless, so each request validating itself looks correct, and createFile() re-validates the finished file against its real template (src/Cms/FileRules.php:143-146); nothing at the pinned commit records the first chunk's template or Upload-Length, yet every later chunk re-reads both from its own headers/body and the completing request's values are the ones that reach the create callback.)
  - src/Api/Upload.php:347-409 — T6 M6 (reason to dismiss: Chunk requests are stateless, so each request validating itself looks correct, and createFile() re-validates the finished file against its real template (src/Cms/FileRules.php:143-146); nothing at the pinned commit records the first chunk's template or Upload-Length, yet every later chunk re-reads both from its own headers/body and the completing request's values are the ones that reach the create callback.)
- Uncovered routes to confirm (pattern B):   - src/Api/Upload.php:234 — T7 M8 (reason to dismiss: FileRules::create() re-runs validFile() on the real final filename at commit (src/Cms/FileRules.php:143), so the chunk-time check on the id-prefixed tmp name can be dismissed as an early best-effort check even though position-sensitive rules such as the leading-dot / '.ht' block cannot match a name like 'abcd-.htaccess'.)
  - src/Api/Upload.php:354-358 — T7 M8 (reason to dismiss: FileRules::create() re-runs validFile() on the real final filename at commit (src/Cms/FileRules.php:143), so the chunk-time check on the id-prefixed tmp name can be dismissed as an early best-effort check even though position-sensitive rules such as the leading-dot / '.ht' block cannot match a name like 'abcd-.htaccess'.)
  - src/Api/Upload.php:386-389 — T7 M8 (reason to dismiss: FileRules::create() re-runs validFile() on the real final filename at commit (src/Cms/FileRules.php:143), so the chunk-time check on the id-prefixed tmp name can be dismissed as an early best-effort check even though position-sensitive rules such as the leading-dot / '.ht' block cannot match a name like 'abcd-.htaccess'.)
  - src/Cms/FileRules.php:275-302 — T7 M8 (reason to dismiss: FileRules::create() re-runs validFile() on the real final filename at commit (src/Cms/FileRules.php:143), so the chunk-time check on the id-prefixed tmp name can be dismissed as an early best-effort check even though position-sensitive rules such as the leading-dot / '.ht' block cannot match a name like 'abcd-.htaccess'.)
  - src/Api/Upload.php:221-270 — T8 M4 (reason to dismiss: Upload::processChunk() is an internal helper whose only production caller is Upload::process() (src/Api/Upload.php:182), so an authorization check added one frame above it is assumed to cover every path - even though processChunk() is public, writes into site/cache/.uploads and is called directly by the existing unit tests (tests/Api/UploadTest.php:340-441).)
  - src/Api/Upload.php:238-244 — T8 M4 (reason to dismiss: Upload::processChunk() is an internal helper whose only production caller is Upload::process() (src/Api/Upload.php:182), so an authorization check added one frame above it is assumed to cover every path - even though processChunk() is public, writes into site/cache/.uploads and is called directly by the existing unit tests (tests/Api/UploadTest.php:340-441).)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T6. Why: Five traps over four independent fix sites. T1 is the deepseek-type core: the protection is absent exactly where the buffer is written and there is a strong in-code reason to dismiss it (FileRules::create already throws at commit, and the uploader comment says the chunk will be validated again by createFile). T2 is the mimo-type coupled value: the template exists in three places (constructor argument, request body, default blueprint) and the existing test fixes the priority, so an over-hardened or body-only check breaks field uploads. T3 and T4 extend the same sink to the replace route (action `replace` on the target file, no template at all) and the avatar route (action `update` on the target user) - each needs its own preflight subject, so a fix that only wires the create route leaves them open while the diff looks complete. T6 is the second mimo-type trap: no state pins the first chunk's template and Upload-Length, so the values that drive chunk validation and the eventual create can be re-declared by a later request. All five are grounded in the pinned code, none depends on the advisory text, and the set forces four distinct judgements (where the check runs, which value it reads, which action/model it decides on, which request's declaration is authoritative) while the must-keep-working values (first-chunk shortcut, field uploads, self-avatar, replace-only roles) sit directly next to them. T5 is folded into the same fix site as T1/T2 and is covered by the T2 conflict; T7, T8 and T9 are recorded but left out of the design because they are outside the published permission fix (T7, T8) or are a public seam whose fail-closed variant collides with the existing test contract (T9). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Authorized chunked uploads must still complete unchanged, including the first-chunk-already-completes-the-file shortcut (tests/Api/UploadTest.php:325-346) and multi-request assembly (tests/Api/UploadTest.php:408-441); a preflight that refuses chunked requests outright denies every real chunked upload. | Field uploads declare their template only as the Api::upload(template:) argument (config/fields/mixins/upload.php:82); a check that reads requestBody('template') denies or mis-decides them, and the existing test testValidateChunkTemplatePriority (tests/Api/UploadTest.php:650-681) pins the constructor argument as the winning value. | A null/omitted template is legitimate and means the default file blueprint (config/api/routes/files.php:56, src/Cms/File.php:158-165); treating 'no template' as a refusal breaks default-template uploads. | Library callers and test doubles call Api::upload() and Upload::process()/processChunk() with no target model (tests/Api/ApiTest.php:629-670, tests/Api/UploadTest.php:340-441, tests/Form/Field/FilesFieldTest.php:17-29); a mandatory or fail-closed preflight turns these into hard failures. | Self-service permissions differ from other-user permissions (UserPermissions::category() returns 'user' for the acting user and 'users' otherwise, src/Cms/UserPermissions.php:62-67); a preflight that always checks the 'users' category refuses a role that may update its own account. | A file blueprint can grant create for a role whose files category denies it (ModelPermissions::can() consults blueprint options first, src/Cms/ModelPermissions.php:93-116), so a role-only check refuses uploads that the commit path would allow. | Non-chunked uploads (no Upload-Length header) never touch processChunk() (src/Api/Upload.php:181-183) and must keep their current behaviour; requiring chunk headers or a template on every request breaks them.. Conflicts the reader found: A single generic authorization check in the shared uploader is the natural fix for T1, but a role that has files.replace without files.create (or a blueprint whose options grant replace but not create for the template) must still be able to finish the replace route; a create-only check placed in Upload::process() denies legitimate replaces. | The same generic file-create check cannot serve the avatar route, whose authorization is user `update` on Find::user($id); applying it breaks every legitimate avatar upload. | Resolving the template only from the request body (the easy way to build the permission subject) makes the check run against the default file blueprint for field uploads, so a template whose blueprint options grant create while the role does not will be refused - the coupled value and the permission subject must be taken together. | Making Api::upload() fail closed (required preflight) closes T9 but breaks the existing library contract: tests/Api/ApiTest.php:629-670 calls Api::upload() with no authorization and tests/Form/Field/FilesFieldTest.php:17-29 overrides Api::upload() with the current four-parameter signature, so an added parameter must stay optional or that override becomes signature-incompatible.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-kirby-32469/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-kirby-32469/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-kirby-32469/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-kirby-32469/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-kirby-32469/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-kirby-32469/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-kirby-32469/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-kirby-32469 --only static
python3 -I common/gate/gate.py stk-kirby-32469 --only nop
python3 -I common/gate/gate.py stk-kirby-32469 --only oracle
python3 -I common/gate/gate.py stk-kirby-32469 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-kirby-32469/`;
  - edit only `tasks/stk-kirby-32469/`, `build/stk-kirby-32469/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-32469.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-kirby-32469`. Control task slug: `stk-kirby-32469-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-32469.json`.
