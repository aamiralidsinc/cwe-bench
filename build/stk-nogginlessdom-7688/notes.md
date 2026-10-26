# stk-nogginlessdom-7688 — build notes

Start (UTC): 2026-10-26T12:29:55Z
End (UTC): PENDING

Repo: asymmetric-effort/nogginlessdom. Pinned: 7cd241350fb7669b006fed46b81436925d1bb55c
(parent of the published fix 785e6ac6e124d1a89b3ccf40bbd75fc8e4cb215d, which is not in the
pinned tree). Advisory: GHSA-322X-V876-G883, CWE-22 arbitrary file write in a file-snapshot writer.

## Levers (one line each)

- **T1** (pattern A, both): `matchFileSnapshot` hands the caller's `filePath` straight to
  `existsSync`/`mkdirSync`/`writeFileSync`; the create and overwrite branches write anywhere.
  `src/assertions/snapshots.ts:732-744,760`. Reported route; no reason to dismiss.
- **T2** (pattern B, deepseek): the compare branch reads the caller's path and folds its content
  into the mismatch error, so a guard on the write branches only still leaks outside content.
  `src/assertions/snapshots.ts:753,764-768`. Dismissal: the advisory is write, not read.
- **T3** (pattern B, both): a path that is lexically inside the project but whose existing
  ancestor is a link outside it; a resolve-and-prefix check passes and the I/O follows the link.
  `src/assertions/snapshots.ts:732-736`. Dismissal: the in-repo idiom (`src/coverage/filter.ts:84-90`)
  and the published check are lexical/absolute-only.
- **T5** (pattern A, both): the snapshot store writes the caller-supplied filepath through
  `NodeSnapshotEnvironment.saveSnapshotFile` with no confinement to the directory it was given;
  reached through `SnapshotClient.saveSnapshots` and `SnapshotManager.finishFile`.
  `src/assertions/snapshot-environment.ts:65-69`, `src/assertions/snapshot-client.ts:54-56,130-141`.
  Dismissal: an absolute snapshot directory is supported and tested, the path comes from the
  runner's test-file list, and the classes are not package exports.
- **T6** (pattern B, deepseek): `removeSnapshotFile` unlinks the caller-supplied filepath with no
  confinement to the configured directory (also reached from `SnapshotManager.cleanup`).
  `src/assertions/snapshot-environment.ts:80-86`, `src/assertions/snapshot-manager.ts:82-91`.
  Dismissal: the advisory is write, not deletion.

Independent concepts: {T1,T2,T3} (one matcher guard, three misjudgements), {T5} (store write),
{T6} (store delete). Three edit sites in the reference fix: matcher confinement, store write
confinement, store delete confinement.

## What was verified

- Behavioural probes on the pinned tree: absolute outside write, overwrite, relative traversal,
  compare-branch content leak, link inside the project, outside parent creation, store write
  through client/manager/environment, store write parent creation, store removal direct and
  through a link all succeed on the pinned code.
- Hidden suites on the pinned tree: 12/12 security fail, 9/9 functional pass.
- Reference fix (`solution/fix.patch`): applies with `patch -p1`; 12/12 security, 9/9 functional.
- Every `checks/*.patch` applies cleanly to the pinned tree and behaves as declared:
  miss_matcher_guard 6 security fail / functional pass; miss_environment_write 4 / pass;
  miss_environment_delete 2 / pass; reads_only 10 / pass; check_after_mkdir 1 / pass;
  upstream_fix (recall) 7 / pass; overbroad, wrong_resource, adjacent_api functional_fail;
  hardening and alt_correct_fix 12/12 + 9/9.
- The project's own snapshot tests (matchers, client, improvements) pass at the pinned commit:
  65 pass, also run inside the image build.
- Current upstream (read-only, main 7f2a952): the store write and removal remain unconfined; a
  later unrelated fix rejects `..` and final-component links and forbids absolute snapshot
  directories. The read branch is closed there for plain paths by the same lexical guard.

## What could not be verified / fairness notes

- The listing check and trials were not run here (the pipeline runs them after this build).
- The pinned `tests/unit/snapshot-matchers.test.ts` writes absolute `os.tmpdir()` paths through
  `matchFileSnapshot`; the published fix changes those tests to pass a root. Those exact cases
  contradict the reported property, so the hidden functional suite uses inside-project paths and
  the store's own directory instead. A solver who runs the pinned matcher tests after the fix will
  see them fail; the published fix updated them for the same reason.
- The coupled must-keep-working value is the store pointed at its own directory outside the
  project (plus the default relative store layout). A fix that confines every store write to the
  project root fails the functional suite.
- The hidden suites exercise `SnapshotClient`/`SnapshotManager`/`NodeSnapshotEnvironment`
  directly; those classes are exported from their modules and used by the project's own tests but
  not re-exported from the package entry point. The instruction states the second property over
  the store's configured directory so the layer is discoverable from the code.
- Nothing outside this advisory's protection was used: the two later upstream advisories
  (GHSA-wj89-8mc6-xpwx, GHSA-vxqq-6phm-8778) are noted read-only and not built on.
