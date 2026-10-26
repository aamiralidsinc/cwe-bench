# nocobase-ds — build notes

Start (UTC): 2026-10-24T05:15:07Z
End (UTC): TBD

Advisory: GHSA-GHVF-QF6H-G8X5 (nocobase/nocobase, path traversal / external control of file
path, CWE-73/434/829). Pinned 7257be6c97b67335d4451c477b26d265a2c54a93; published fixes
a89e5a999 (file-manager local storage paths) and 7c9ffe142 (plugin-name validation).

Scope kept: the advisory's own protection only — local file-storage destination confinement and
plugin package-name validation. Out of scope, noted once: `pm:add` installs from a caller-supplied
archive URL/registry (an install-trust question, not built on); the error-detail leak fixed in the
same upstream commit (CWE-209) is not part of this task.

## Security property (written once, general)

No client-supplied value may cause the server to create, overwrite, read, delete or load any
filesystem object outside the locations the server manages for that purpose: files written for a
storage stay inside that storage's configured root, and a plugin is selected only by an installed
plugin package name. This holds however the value arrives (request field, stored setting, later
reload) and nothing outside those roots may be created or changed even when a request is refused.

A second, genuinely different property is not needed: plugin-package selection and storage-root
confinement are both "attacker value must not name a location outside the managed roots", so they
are stated as one invariant over the protected outcome.

## Levers (each with a different reason a solver skips/mis-fixes it)

### T1 — storage root is the trust boundary (how-type: shape a plausible check mishandles)
- where: plugin-file-manager server/storages/local.ts getDocumentRoot (24-28) + actions/index.ts
  storages resource definition (15-18) + actions/attachments.ts (209-238).
- What: a client-submitted `options.documentRoot` (HTTP storages:create / storages:update) chooses
  the root the multer destination then joins the (sanitised) relative path onto. A check that only
  contains the per-request path inside `getDocumentRoot(storage)` is vacuously true when the
  attacker chose the root.
- Reason to dismiss: storage configuration is admin-only; the request `path`/`filename` is already
  validated in the non-multipart branch, so the reported "file path" looks covered.
- Coupled must-keep-working: an operator-configured absolute documentRoot outside the application
  directory (seeded/ORM) keeps accepting uploads; a legitimate relative root and an update that
  only changes the sub-path keep working.
- Security tests: create with an outside absolute root -> client error, no record, no outside
  directory; update the default storage to an outside root -> client error, existing root kept,
  next upload inside; relative `..` root refused.
- sf patch: reference fix everywhere except documentRoot is never allowlisted on the client
  config-write routes (sink containment only).

### T2 — nothing outside the root is created, even on refusal (how-type: side-effect ordering)
- where: storages/local.ts `make()` destination (62-64) does `mkdirp(destPath)` before any write.
- What: a stored/cached `storage.path` that escapes (`../outside-X`) makes multer create the
  outside directory and write the file. A validation placed after the destination callback (e.g.
  in the filename getter) still creates the directory.
- Reason to dismiss: the stored `path` was already accepted by config validation, so the upload
  handler "just needs to write the file"; the harm is seen as the file, not the directory.
- Coupled: ordinary sub-path uploads and upload to the default root still work; refusal returns a
  client error.
- Security test: cached local storage with `path = '../<outside>'` -> upload refused and the
  outside directory never exists (also no file/record).
- sf patch: reference fix with the sink containment moved after `mkdirp` (file blocked, directory
  created).

### T3 — the default create-or-update routes (route where the protection never existed)
- where: packages/core/actions/src/index.ts:49-50 registers `updateOrCreate`/`firstOrCreate` for
  every resource; plugin-file-manager only adds the new validation middleware to create/update.
- What: `storages:updateOrCreate` / `storages:firstOrCreate` save an outside `options.documentRoot`
  through the real HTTP route with no allowlist (the model save hook runs with
  validateDocumentRoot=false), after which the next upload writes outside.
- Reason to dismiss: the UI only calls create/update, and "the save hook covers every ORM save".
- Security test: HTTP updateOrCreate/firstOrCreate pointing the default storage's root outside ->
  client error (or unchanged root) and no outside write from the following upload.
- sf patch: reference fix with the validation middleware registered for create/update only.

### T4 — plugin identifier chokepoint, not one route (Pattern A far site: other package, second sink)
- where: packages/core/server/src/plugin-manager/plugin-manager.ts parseName (222-253, called by
  resolvePlugin/importModule, enable/disable/remove/update/add); utils.ts already ships
  assertSafePluginPackageName (53-74) but parseName never calls it; remove() open-codes
  `resolve(NODE_MODULES_PATH, packageName)` and `fs.rm(..., {recursive:true})` (744).
- What: a plugin identifier that is a filesystem path is loaded as code by `pm:enable` (HTTP ->
  CLI -> parseName -> importModule) and, separately, a path identifier deletes an arbitrary
  directory through `remove()`. Validating only the HTTP enable action leaves the lower-level
  API/CLI and the delete sink open.
- Reason to dismiss: plugin administration is an admin-only, different package from the reported
  file-storage issue; "remove can only delete the plugin's own installed package".
- Coupled: installed plugins still enable/disable by name; `pm add` from a URL/uploaded archive
  (which never goes through parseName) still works.
- Security tests: HTTP enable with an absolute marker-module path must not execute the module API
  enable too; remove() with an absolute temp dir must not delete it.
- sf patch: reference fix with the name assertion applied at the enable action/resolvePlugin only,
  leaving parseName and remove() raw.

### T6 — injected sibling: plugin metadata read (new file, published fix never touches it)
- where: new packages/core/server/src/plugin-manager/options/plugin-info.ts, registered as the
  `pm:info` action; reads `<NODE_MODULES_PATH>/<filterByTk>/package.json` with no name check.
- Reason to dismiss: it only reads a package.json for a detail dialog; no code is executed.
- Security test: request with an absolute temp directory containing a marked package.json -> the
  marked content is not returned (client error or empty).
- sf patch: reference fix with the info action left as injected.

### T7 — injected sibling: second local-disk write path in a different module
- where: injected `storages:probe` action (actions/storages.ts) that writes a probe file to a
  candidate root/path supplied in the request body (an admin "test this storage config" button),
  using `path.resolve` without the safe-path helper.
- Reason to dismiss: it is a diagnostics endpoint that writes a dotfile, admin-only; the config is
  validated before saving anyway.
- Security test: probe with a candidate root outside the app -> client error and no outside
  file/directory.
- sf patch: reference fix with the probe action left as injected.

## Full candidate list (why each was kept or dropped)

Storage side
1. local storage make() destination (reported sink) — KEPT as T2.
2. getDocumentRoot / config root (reported helper) — KEPT as T1.
3. attachments non-multipart path check (reported middleware) — covered by T1/T2 oracle; not a
   separate lever (published fix).
4. storages create/update middleware (published fix) — the T1 fix site.
5. Storage.beforeSave (published fix) — path validation on every save; part of oracle.
6. storages:updateOrCreate / firstOrCreate default actions — KEPT as T3 (real, unmodified route;
   strongest known lever).
7. PluginFileManagerServer.uploadFile({documentRoot}) cache override — real, published fix does
   not allowlist it, but the caller is server code, not a client; the property is written over
   client-supplied values, so not tested (avoids an unfair "trusted API" requirement).
8. `{{$env.X}}`-rendered documentRoot (config loader producer) — DROPPED: an escape needs a
   malicious environment value, i.e. a trusted operator input; not a client-supplied value, and a
   fair property cannot claim it.
9. Injected storages:probe write — KEPT as T7 (plausible diagnostics action, different dismissal).
10. Cloud key prefix in utils.ts (ali-oss/s3/tx-cos) — remote object keys, not the local managed
    filesystem the property names; dropped.
11. commands/repair-filenames.ts — remote keys only; dropped.
12. A second local storage type/driver (injected "local-cache") — considered (type-string guard is
    a strong how-type shape) but requires a whole driver plus registration in a file the published
    fix touches; dropped for build cost/risk while T2 already carries the local-write layer.

Plugin side
13. parseName chokepoint + resolvePlugin/importModule — KEPT as T4.
14. remove() fs.rm sink — KEPT inside T4 (second sink, different dismissal).
15. resource enable/disable/remove actions — entry points for T4.
16. PackageUrls.fetch raw path from DB records — not client-controlled; dropped.
17. Injected pm:info package read — KEPT as T6 (read outcome, different dismissal).
18. pm:add install from archive URL/registry — out of scope (install trust); functional control
    only.
19. getStoragePluginDir/getNodeModulesPluginDir — already assert at pinned; not a gap.

## Routes and input shapes the security tests cover

- HTTP storages:create with absolute outside root; with relative `..` root.
- HTTP storages:update with outside root (existing values merge).
- HTTP storages:updateOrCreate and storages:firstOrCreate with outside root.
- HTTP attachments:create (multipart) after each of the above (write observed).
- Cached/stored storage path `../outside` reaching the multer destination (directory side effect).
- HTTP pm:enable with an absolute marker-module path; PluginManager.enable API with the same.
- PluginManager.remove with an absolute temp directory.
- HTTP pm:info with an absolute directory holding a marked package.json.
- HTTP storages:probe with an outside candidate root.

All harmless: marker JS module, marker text files, temp directories under the system temp dir;
nothing destructive outside test-created temp dirs.

## Coupled legitimate behaviour (functional tests)

- Default local upload works; relative sub-path upload works; leading/trailing slash path still
  resolves (normalisation preserved).
- Update that only changes the sub-path keeps the existing root and uploads under it.
- Operator-seeded absolute documentRoot outside the application directory (created through the
  ORM, as an operator/seed would) keeps accepting uploads.
- Installed plugins enable/disable by name; parseName still resolves scoped preset/plugin names.
- `pm add` from an existing archive path never needs a package-name check (control: the action is
  accepted; no network).

## Wrong-fix catalogue plan

- refuse_all -> functional_fail patch (refuses every storage config/upload).
- crash_as_refusal -> n/a: refusal contract accepts any client error; an uncaught crash on a
  legitimate upload is caught by the functional suite, but no separate patch is built.
- wrong_resource -> n/a: each route confines the exact location it touches; there is no proxy
  object to authorise instead.
- one_role_or_direction -> n/a: no role/peer/direction dimension.
- reads_only -> T7 (read vs write) and T6 are separate tests; a write-only fix fails T6.
- check_after_adjustment -> T2 sf patch (check after mkdirp).
- unlisted_route -> T3 sf patch (updateOrCreate/firstOrCreate).
- malformed_identity -> n/a: values are paths/names, and non-string shapes are not security
  relevant here.
- missing_authority -> n/a: no external authority lookup.
- adjacent_api -> T4 sf patch (fix the HTTP action, miss the lower-level API/remove).

## Verification plan / open questions

- Confirm the pinned tree boots under vitest+sqlite in the image and the project's
  plugin-file-manager action.test.ts and core pm.test.ts pass.
- Confirm behaviourally on the pinned tree: docroot create/update, updateOrCreate/firstOrCreate,
  multipart write outside, cached path mkdirp side effect, pm enable import, remove delete.
- Confirm updateOrCreate/firstOrCreate are routed by the global default actions and not blocked by
  the resource definition.
- Confirm remove() removes the directory when no `applications` collection exists in the mock app.
- Confirm a client error is produced by the oracle for each route (and that a parseName-only fix
  is enough for enable but not for the injected info action).

## Built as (after implementation)

Levers shipped (all verified locally on the pinned/injected tree and on the reference fix):

- T1 storage root trust boundary: HTTP create / update with an absolute or relative root outside the
  managed areas; a root submitted while the type is remote and used after switching to local.
  Reference fix validates the submitted root at those client routes and validates every save.
- T2 sink side-effect ordering: a cached storage path that escapes must not create the outside
  directory; reference fix checks before mkdirp.
- T3 pattern-B generic routes: storages:updateOrCreate / storages:firstOrCreate (real, unmodified
  upstream default actions) reach the save with no document-root allowlist.
- T4 plugin identifier chokepoint: parseName / resolvePlugin / enable / remove in the core server
  package; the remove() directory-deletion sink is a second sink on the same value.
- S1 injected pm:info package-metadata read (new file; published fix never touches it).
- S2 injected storages:probe diagnostics write (actions/storages.ts; published fix never touches it).

Dropped candidates and why: PluginFileManagerServer.uploadFile({documentRoot}) (server-side caller,
not a client-supplied value); the `{{$env.X}}` rendered-root producer (an escape needs a malicious
operator environment value, so the property cannot fairly claim it); a second local storage driver
(build cost, and T2 already covers the local write layer); cloud key concatenation and the
repair-filenames command (remote object keys, not the managed local filesystem).

Local verification (host, same vitest version and env as the verifier):
- pinned/injected tree: 12/12 security tests fail on their intended assertions; 8/8 functional pass.
- reference fix: 12/12 security and 8/8 functional pass.
- every check patch applied to a pristine pinned+injection worktree with `git apply --check`.
- project tests at the pinned tree: pm.test.ts 18/18; plugin-file-manager action.test.ts 23 pass,
  1 skipped.

Verifier design notes: the image ships a pristine dependency tree at /opt/nocobase (yarn install
--ignore-scripts, because yarn's build-script scheduler does not terminate on this workspace graph;
only tsconfig.paths.json generation and a self-contained sqlite3 are run). test.sh overlays the
restored /workspace source, restores the test harness config (vitest config, tsconfig paths,
@nocobase/test and @nocobase/cli) from pristine copies, drops the hidden suites in, and runs vitest
as uid 1000.

## Local check-patch matrix (host, same vitest/env as the verifier)

fix.patch: 8/8 fm-security, 4/4 pm-security, 6/6 fm-functional, 2/2 pm-functional.
sf-miss-storage-root: 4 fm-security fail (the root-trust tests), everything else pass.
sf-miss-stored-path-order: 1 fm-security fail (directory side effect), everything else pass.
sf-miss-generic-route: 2 fm-security fail (updateOrCreate/firstOrCreate), everything else pass.
sf-miss-plugin-chokepoint: 1 pm-security fail (remove), everything else pass.
sf-miss-probe: 1 fm-security fail (probe), everything else pass.
sf-miss-plugin-info: 1 pm-security fail (info read), everything else pass.
ff-overbroad: 1 fm-functional fail (external operator root), security all pass.
pass-hardening: all 20 pass. pass-alt: all 20 pass.
Verifier-runner simulation (run-group.sh + score.py): security 12/12, functional 8/8, reward 1.0.

## Verifier image design (final)

Harbor empties `/workspace` before restoring the submission's artifacts, so the dependency tree
cannot live there. The verifier image installs the pinned tree at `/workspace` in the exact same
instructions as the environment image (shared classic-builder cache), then ships
`/opt/tree.tgz` — the whole prepared tree (source + all top-level and nested `node_modules`) as
one gzip archive — plus small pristine copies of the harness (`vitest.config.mts`,
`tsconfig.paths.json`, `packages/core/test`, `packages/core/cli`). test.sh extracts the archive to
`/opt/nocobase`, overlays the restored submission, puts the harness back, drops the hidden suites
in and runs vitest as uid 1000. An earlier attempt that kept the tree at `/workspace` failed
because Harbor's `empty_dirs` wiped it; an archive limited to the top-level `node_modules`
failed because yarn's nested `packages/*/node_modules` (the correct `commander` for
`@nocobase/server`) were missing.

## Gate results (final)

static: PASS. nop: PASS (security 12/12 fail, functional 8/8 pass, reward 0.0).
oracle: PASS (3 identical runs, reward 1.0). patches: PASS, every check behaved as declared:
sf-storage-root 4 security fail; sf-stored-path-order 1; sf-generic-route 2;
sf-plugin-chokepoint 1; sf-probe 1; sf-plugin-info 1; ff-overbroad 1 functional fail, security
all pass; pass-hardening 1.0; pass-alt 1.0.
End (UTC): 2026-10-24T10:29:18Z (gate); total session resumed 2026-10-24T07:45:37Z.
