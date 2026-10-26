# pv-nx build notes

Start: 2026-10-23T03:22:29Z
End: 2026-10-23T04:37:00Z

## Candidate and pinned tree
- nrwl/nx, advisory GHSA-VP3H-GHGH-JR7G / CVE-2026-71476 (CWE-22/CWE-59), injected track, pattern A+B.
- Pinned commit: `b2d4f673f2576c85ee61b9b44aa262a98665f736`, verified as `2b20c2da39d263c32ae05767577589481a309fee^`.
- `2b20c2d` is the published fix and the full three-file change; its message says it is a cherry-pick of `ad296578`. The other recorded fix commit `a8280762` is not reachable from the public repo refs (fetch by SHA failed). The oracle was reduced from `2b20c2d` with the upstream in-file `#[cfg(test)]` modules dropped.
- The pinned tree contains none of the advisory's regression tests (the fix commit introduces them).

## Security property (stated once, in the report)
A cache entry may only ever affect (1) its own directory inside the cache and (2) the task's declared
outputs, each of which must resolve inside the project. Whatever the entry contains and however its
paths are written, nothing else may be created, changed or deleted -- on the way into the cache or on
the way back. An artifact cannot add content it does not carry.

## Levers
- **L1 restore-beyond-outputs** (A, how-type, route where the protection never existed): the restore copies
  the whole artifact directory into the workspace, deletes expanded outputs before validating anything,
  and writes through links that already exist in the workspace. `cache.rs:424`, `file_ops.rs:105`.
  Reason to dismiss: once extraction is confined to the cache directory, the local cache looks trusted,
  and this whole-directory copy is pre-existing plumbing shared by every backend.
- **L2 declared-output-paths** (A, how-type, shape a check mishandles + ordering): declared outputs are
  joined literally (an absolute path replaces the base; `..` climbs out) and the expanded outputs are
  deleted before validation; an absolute path that resolves inside the project must keep working while
  one outside must not be touched. `cache.rs:216`, `cache.rs:424`.
  Reason to dismiss: outputs are "just configuration", and the safe-looking move is to reject every
  absolute path (which breaks the in-project form).
- **L3 store-link-follow** (A, how-type, ordering): on the way into the cache `is_dir()` is tested before
  `is_symlink()`, so a symlinked output directory is read through and the target's contents become part
  of the entry. `file_ops.rs:36`, reached from `cache.rs:216`.
  Reason to dismiss: the store side runs against the user's own workspace, and following links is expected
  output behaviour.
- **I1 legacy-extract-route** (B, injected): the pre-v19 compatibility retrieval re-implements extraction
  with the old join-and-unpack body, so a fix to the current extractor leaves it open.
  `http_remote_cache.rs:88`, `:262-337`. Reason to dismiss: it reads as untouched code for old servers.
- **I2 batch-restore-route** (B, injected): a batch twin of the restore inlines the old whole-directory copy
  instead of the per-output restore, so a fix to the single-entry path leaves the batched path open.
  `cache.rs:305`. Reason to dismiss: it reads as a thin performance wrapper.

## Injected sibling candidates considered
1. **Legacy endpoint extraction fallback** -- picked. A second implementation of exactly the guarded
   operation, reached from the real `retrieve` entry point, untouched by every hunk of the published fix.
2. **Batch restore twin** -- picked. A second implementation of the restore, exported as a real napi
   operation and wired into `DbCache.getBatch`; untouched by the published fix.
3. TypeScript remote-cache backend unpacking with tar-stream (O8b) -- rejected: the TypeScript layer would
   need node_modules and a compile step offline; the hidden tests could not reach it.
4. Restore driven by outputs recorded in SQLite at put time (producer off the check's path) -- rejected: the
   recorded values are normalized before they are stored, so an attacker cannot inject a bad path; there is
   no real gap to demonstrate.
5. Shared-filesystem cache import helper -- rejected: its path comes from local administrator configuration,
   not from attacker-controlled data.
6. Second extraction in the Nx Cloud client-bundle updater (`packages/nx/src/nx-cloud/update-manager.ts`) --
   real upstream code, but a different sink and trust source (vendor bundle); noted as out of scope below.
7. Public napi `copy`/`remove` helpers -- rejected: generic file utilities; the published fix deliberately
   leaves them unchanged and the property does not cover arbitrary JS file utilities.
8. Legacy TypeScript `Cache.copyFilesFromCache` -- rejected: selected only when the db cache is disabled
   (WASM), where the self-hosted HTTP cache is unsupported; unreachable in this harness.
Why 1 and 2: they are the only candidates that are genuinely reachable through the tested entry points,
look like code a maintainer plausibly left behind, and are outside every hunk of the published patch.

## Tests and local matrix
15 security tests and 8 functional tests, run with Node's built-in runner against the rebuilt addon loaded
with `process.dlopen`; the remote tests serve artifact bytes from an in-process loopback HTTP server.
Local matrix (fresh builds of each variant):
- pinned + injection: 15/15 security fail, 8/8 functional pass (nop condition).
- oracle: 23/23 pass.
- `pass_hardening`: 23/23. `pass_alternative` (parent-walk restore design): 23/23.
- `secfail_restore`: 3 security fails (L1), functional green.
- `secfail_normalize`: 3 security fails (L2), functional green.
- `secfail_store_symlink`: 1 security fail (L3), functional green.
- `secfail_legacy`: 1 security fail (I1), functional green.
- `secfail_batch`: 2 security fails (I2), functional green.
- `secfail_extraction_only`: 9 security fails, functional green (the tempting wrong fix).
- `wrong_check_after_delete`: 1 security fail. `wrong_malformed_identity`: 4 security fails.
- `functional_fail_refuse_all`: 6 functional fails. `functional_fail_overbroad`: 2 functional fails.

## Verified
- Every tested route reproduces at the pinned commit through the napi cache API used by the task runner.
- Project tests at the pinned commit: `cargo test -p nx --lib native::cache:: -- --test-threads=2` =
  12 passed, 0 failed, 1 ignored (file_ops, expand_outputs, validate_outputs).
- Offline dependency reuse: the verifier image pre-builds every dependency from a dummy crate named
  `nx-prebuild`, so its target directory holds no `nx` artifact and the restored workspace must compile the
  addon for real. With that prebuild the real addon rebuilds in ~1m40s on 4 CPUs (~3-4 min on the
  verifier's 2 CPUs) with no network. (An earlier prebuild that reused the name `nx` let cargo treat the
  stale stub artifact as fresh and Node refused it with "Module did not self-register"; the dummy name
  removes that failure mode.)
- `nop` gate stage passed in the real container: 15/15 security tests fail on the vulnerable tree and 8/8
  functional tests pass.

## Could not verify / guesses
- `a8280762` could not be fetched; the oracle relies on `2b20c2d`, which carries the identical change.
- The hidden tests call the napi exports directly rather than through the compiled TypeScript cache layer
  (node_modules are not shipped offline); the exports are the same operations the TypeScript layer calls.
- No target-model trials were run (not permitted in this build role).
- Known residual left as upstream: when a declared output names a path *beneath* a symlink directory inside
  an artifact, the fixed per-output restore can read the link target's content into the workspace. The pinned
  code does not exhibit it (it copies the link as a link), so it cannot be a nop-failing security test; the
  "content the artifact actually carries" clause is enforced by the hardlink and store-link tests instead.
- The screener's unverified point about `nx_walker_sync` following symlinks was checked: it does not follow
  a top-level symlink entry in the artifact, and glob expansion produced no matches through it.

## Pattern B register
Two rows were appended to `build/audit/uncovered-routes.tsv` for the screener's O8 leads, both dismissed and
not built, with the reason in the note column. The B side of this task is carried by the two injected
siblings, recorded as manifest traps.

## Out of scope (one line)
`packages/nx/src/nx-cloud/update-manager.ts:341-362` extracts the Nx Cloud client bundle by joining tar
header names onto the install dir with no containment; different sink and trust source, not pursued.

## Gate results (run in order, one stage at a time)
- `static`: PASSES everything except the one expected item -- `manifest.patch_checks` has no
  `expect=pass` patch with `kind='blind'`. The blind patch and FAIRNESS.md are written by the later
  blind-fix / fairness agents, not here; no other static problem was reported.
- `nop`: PASSED. All 15 security tests fail on the vulnerable tree and all 8 functional tests pass in
  the verifier container.
- `oracle`: PASSED. Three trials, each reward 1.0 with identical per-test results.
- `patches`: PASSED. 12 checks behaved exactly as declared:
  - `pass_hardening` 1.0, `pass_alternative` 1.0;
  - `secfail_restore` 3 security fails / 0 functional, `secfail_normalize` 3/0,
    `secfail_store_symlink` 1/0, `secfail_legacy` 1/0, `secfail_batch` 2/0,
    `secfail_extraction_only` 9/0, `wrong_check_after_delete` 1/0,
    `wrong_malformed_identity` 4/0;
  - `functional_fail_refuse_all` 6 functional fails, `functional_fail_overbroad` 2 functional fails
    (the over-broad patch breaks only functional tests, with 0 security failures).
Incidents during gating, all resolved: the first `nop` run was stopped by the tool's background time
limit mid-image-build (re-run with a 2 h budget); the first verifier prebuild reused the crate name
`nx`, so cargo treated the stale stub artifact as fresh ("Module did not self-register") -- fixed by
prebuilding under the name `nx-prebuild`; the first `patches` run stopped on an infra-only Docker
`docker inspect` failure (re-run); the `wrong_malformed_identity` variant was regenerated by an old
script that dropped a function, so its patch failed to compile -- script fixed, variant rebuilt,
patch regenerated and verified.
