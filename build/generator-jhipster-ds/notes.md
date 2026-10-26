# generator-jhipster-ds — build notes

- Start (UTC): 2026-10-24T04:59:00Z (pipeline launch); design work from 05:00Z.
- End (UTC): TBD
- Advisory: GHSA-9FFP-22J7-56R2 / CVE-2026-107303 (CWE-79). Repo jhipster/generator-jhipster.
  Pinned bc2f089c9d44e96072346a716b8960a907236ebd, fix efe95edd4dedc3379735094936439410a51ce3d9.
- Track: injected (pattern A).

## What the product does
JHipster generates Spring Boot apps with Angular, React or Vue clients. A binary entity field
holds base64 data plus a content type chosen by whoever saves the record. The generated client
renders the field and can open it in a new window.

## Security property (written once, before routes)
A content type that arrives from stored data must never cause a generated application to open a
document that can execute script — whatever action starts the open, whichever generated client,
whatever spelling/parameters the stored value has, and whichever page the control sits on. A file
that cannot be shown safely must still be delivered: the open completes without error and yields
an inert download rather than a rendered document. Ordinary raster-image previews keep working
inline.

## Leads examined (full candidate list)
Published-fix sites (screener + own search):
- shared generated helper `openFile` (client/common template) — core sink.
- Angular `DataUtils.openFile` wrapper; Angular detail/list/update component wrappers; Angular
  detail/list/update view links.
- React detail/list views: pinned code imports `openFile` from the `react-jhipster` npm package
  (a different implementation: a `data:` URL written into an iframe in a new window).
- React update form: `ValidatedBlobField` from `react-jhipster` (same library opener) — external
  package, cannot be changed through a template hook; noted out of scope (one line below).
- Vue `useDataUtils().openFile` composable (argument order reversed vs shared helper); Vue
  details/list/update view links.
- Vue `downloadFile` (own Blob builder, `<a download>`): real upstream code, but the download
  attribute prevents inline document rendering. Not exploitable as pinned; not used.
- `setFileData` (Vue composable / Angular form service) stores `file.type` — producer of the
  attacker value, but server data is equally untrusted and the open-time check is the right
  layer; not a lever.
- `<img [src]="'data:' + ContentType ...">` in views: script does not run in an image element; not
  exploitable.
- Uncovered routes where protection never existed: none that stay inside the advisory (the
  Angular/Vue update "Open" links are protected by the shared helper's default; the React update
  library opener is external). Pattern B register: no rows.

## Levers chosen
T1 (main, HOW-type, mechanism): XML-based image types are script-capable. A check that admits
`image/*` leaves `image/svg+xml` (and parameterised/mixed-case forms) open. Fix needs an explicit
raster/no-`+xml` rule. Reason to dismiss: the report speaks about HTML documents and "images are
safe"; the natural allowlist is `startsWith('image/')`.
Where: shared resolver + every call site (generators/client/generators/common/templates/.../
data-utils.ts.ejs; angular/vue/react view templates).

T2 (HOW-type, coupled must-keep-working): raster image previews must stay inline. The obvious
over-broad fix (always octet-stream / always download) breaks the image-preview action on list,
detail and form pages. The fix must carry the field kind (image/text/any) to the resolver, or infer
it from a safe allowlist. Reason to dismiss: "forcing downloads everywhere is the safest fix."
Coupled functional tests: image/png and image/jpeg open inline in each client; other files still
open.

T3 (pattern A far site, second implementation): React detail/list use `react-jhipster`'s
`openFile`, a different mechanism (data: URL iframe in a new window) and a different package
(generators/react). Hardening only the shared blob helper leaves React on the library. Reason to
dismiss: third-party code / different mechanism ("the advisory is about blob: URLs").

T4 (pattern A wrapper chain): Angular service/component wrappers and the Vue composable sit between
the view and the helper; a fix that only changes the helper signature leaves images downloading
(functional coupling), and the Vue wrapper's reversed (contentType, data) order invites a wrong
fix. Covered by the functional image tests and an adjacent_api wrong-fix patch.

## Injected siblings (2, both in code the published fix never edits)
S1 Angular: `DataUtils.previewFile(data, contentType)` — a second Blob builder opening the blob
inline — plus a "Preview" action in the update form (the update view is untouched by the published
fix). Reason to dismiss: a neighbouring form action with a different name; the reported path is
the list/detail open link.
S2 Vue: `useDataUtils().previewFile(contentType, data)` — same shape in the composable — plus a
"Preview" action in the Vue update form (untouched by the published fix). Reason to dismiss as S1,
in another client.
Both are reached through the real generated update page (click), fall under the general property,
and are closed by routing them through the safe resolver in the oracle.

Rejected sibling candidates: Vue `downloadFile` (already safe via `download`); a new separate
service module (needs generator registration changes for little extra realism);
React update (library component has no hook to override its opener).

## Test/oracle architecture
- Verifier rebuilds the agent's source (`npm run build`) with a restored pristine node_modules,
  then runs the real generator CLI (`dist/cli/jhipster.cjs jdl ... --skip-install --skip-git`)
  three times to emit Angular, React and Vue clients for one entity with ImageBlob/AnyBlob/TextBlob
  fields.
- Hidden security tests load the generated modules, stub the external packages, execute the real
  generated open paths (component/service/composable/view expressions) with a recorded
  `URL.createObjectURL`/`window.open`, and assert no script-capable document type is ever opened,
  with a clean download for unsafe types.
- Functional tests assert raster image previews still open inline and other files still open.
- The react-jhipster stub mirrors 1.0.3's `openFile` (data: URL written into an iframe), verified
  from the published package source; React is safe only when it uses the local helper.
- Runner: the project's own esmocha, JUnit XML via a small staged reporter.

## Gate log
- 2026-10-24T05:49 static: PASSED.
- 2026-10-24T05:50 nop: first trial aborted with Harbor
  `EnvironmentStartTimeoutError` after 600 s while the shared VM was at load ~90 (91 concurrent
  docker builds); the agent image build had not finished. Fixed by setting
  `[environment].build_timeout_sec = 1800.0` (Harbor reads the agent-environment build timeout from
  `[environment]`, not `[verifier.environment]`) and by dropping a duplicate explicit `npm run
  build` from the image (npm ci already runs the prepare build).
- Test fixes found while reading the script: the group commands passed a directory to esmocha
  instead of a `*.spec.ts` glob (esmocha reports "No test files found"); corrected before any trial
  reached the suites.
- 06:26 nop on the task-private dockerd: PASSED. security 28/28 fail on the vulnerable code,
  functional 19/19 pass, reward 0. The verifier's first attempt had failed in its own
  user-creation step (`chown: invalid group: agent:agent`) because the separate-mode verifier
  boilerplate lacks the group rename the agent boilerplate has; added the `groupmod -n agent`
  line to tests/Dockerfile (same fix as environment/Dockerfile).
- 06:31 oracle started on the private dockerd; the system Docker daemon was fixed by the operator
  and the private dockerd shut down mid-stage.
- 07:43 oracle re-run on the fixed system daemon: PASSED, 3 runs, each reward 1.0, identical
  security (28/28) and functional (19/19) results.
- 08:15 patches stage started (11 checks) on the system daemon: PASSED at 09:47. Every check
  matched its declaration:
  sf-miss-t1-svg security 11 failed / functional 0; sf-miss-t3-react 4/0; sf-miss-s1-angular-preview
  2/0; sf-miss-s2-vue-preview 2/0; wf-crash 12/0; wf-check-after-adjustment 1/0;
  wf-overbroad 0 security / 9 functional failed; wf-refuse-all 24/12; wf-adjacent-api 1/2;
  pass-hardening reward 1.0; pass-alternative reward 1.0. The missing blind-fix.patch was skipped
  as designed (a separate blind-fix run produces it).
- End (UTC): 2026-10-24T09:47:10Z



## Notes for the report
- Instruction: 347 words; no file/function names, no advisory id, no root cause, no route list.
- Levers in one line:
  - T1 (A, how): XML image types (image/svg+xml, parameters/case) are script-capable, so `image/*`
    is not a safe allow-list — shared helper + every view action.
  - T2 (A, how, coupled): forcing every stored file to download breaks raster image previews; the
    field kind must reach the resolver through the Angular service/component and Vue composable.
  - T3 (A, far site): the React pages open through react-jhipster's own opener (data: URL in an
    iframe), a different implementation in another package.
  - S1 (injected): Angular edit form's Preview action builds its own Blob (DataUtils.previewFile).
  - S2 (injected): Vue edit form's Preview action builds its own Blob (useDataUtils().previewFile).
- Fairness concerns I see: (1) T3 asks the solver to stop using a third-party opener, which a
  reasonable reader might call out of scope; the property says "a document that can execute script"
  (no origin wording) so it covers the data: URL, and the published fix did move React to the local
  helper. (2) The instruction's preservation clause says "ordinary raster image type", which hints
  that non-raster images are not automatically safe; this is a fairness aid, not a route pointer.
- Outside the scope, one line: the React edit form opens through react-jhipster's
  `ValidatedBlobField` (no template hook to override its opener); server-side validation of the
  stored content type is a separate hardening question — neither is pursued.

## Verified / not verified
- Local verification (dev containers, project toolchain): with fixtures generated from the injected
  tree, all 28 security cases fail and all 19 functional cases pass; with fixtures generated from
  the oracle tree (published fix + sibling fixes), all 28 + 19 pass. Same results under Node 22.
- Offline: generator CLI runs with `--network none`.
- Project tests for the affected area run green in the agent image (client:common 9, entity 7,
  single-entity 5, angular 1452, vue 917, react 760) on Node 22.23.3. Note: they fail on Node 24 in
  this repository (a project-test-harness/Node-24 interaction unrelated to the task), which is why
  both images pin Node 22.
- The React package opener stub mirrors react-jhipster 1.0.3 `util/data-utils.openFile` (data: URL
  written into an iframe in a new window), read from the published package source.
- End-to-end verifier simulation on the host with Node 22.20.0 (no Docker needed):
  - vulnerable tree: apply injection -> `npm run build` -> prepare.mjs (real CLI, three apps) ->
    suites: security 0 passing / 28 failing, functional 19 passing (the nop expectation).
  - oracle tree: apply solution/fix.patch -> `npm run build` -> prepare.mjs -> suites:
    security 28 passing, functional 19 passing; jUnit XML through tests/score.py -> reward 1.0.
- Wrong-fix simulation: the checks/ patches were applied to the generated fixed fixtures (the same
  semantic edit the template patch makes) and both suites run:
  pass-alternative 28/19 pass; pass-hardening 28/19 pass; sf-miss-s1 26p/2f security + 19p
  functional; sf-miss-s2 26p/2f + 19p; sf-miss-t1 17p/11f + 19p; sf-miss-t3 24p/4f + 19p;
  wf-crash 16p/12f + 19p; wf-check-after-adjustment 27p/1f + 19p; wf-overbroad 28p/0f security +
  10p/9f functional; wf-refuse-all 4p/24f + 7p/12f; wf-adjacent-api 27p/1f + 17p/2f. Every one
  matches its declared expectation.
- Artifact excludes: `dist` had to be removed from the task.toml `artifacts.exclude` list. The repo
  keeps a template directory `generators/client/templates/src/main/webapp/swagger-ui/dist`, and
  Harbor restores /workspace with `tar --exclude=<pattern>`, which drops any nested path component
  named `dist`. `node_modules` stays excluded. The restored `dist/` is deleted and rebuilt by
  `npm run build`'s prebuild step, so including it costs only the transfer.
- Not verified: the Harbor gate stages. The shared Docker daemon stopped answering API requests
  (docker version/ps and a raw socket GET /version time out; ~90 concurrent docker builds from other
  sessions; Harbor then reported "Docker daemon is not running"). The gate is re-run if the daemon
  recovers.


