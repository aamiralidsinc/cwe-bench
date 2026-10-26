# Build notes: tinacms-ds

- Start (UTC): 2026-10-18 21:43
- End (UTC): 2026-10-18 23:01

## Advisory / commits
GHSA-8MQ9-5FW2-5RM4 / CVE-2026-59992 — tinacms/tinacms, broken access control /
object-key path traversal (CWE-639). Pinned (vulnerable) `d08ffb4` (verified parent
of the published fix `d44558e`, "Fix media mediaroot key scoping (#7088)").
Track INJECTED, pattern A + injected siblings.

## Mechanism (one line)
Each first-party media adapter hands a caller-supplied object key or directory to
the storage SDK for presign/write/delete/list without confining it to the
operator's media root; the published fix resolves every key/directory against the
root and returns 400 on absolute, traversal, NUL/backslash, empty or escaping values.

## Levers (7; plan)
- T1 (A, report landing point): S3 adapter pages-router handler — presigned upload
  GET `?key=` plus the same handler's delete and list branches
  (`packages/next-tinacms-s3/src/handlers.ts:68-89,133-139,205-211`).
  Shapes: `../`, absolute, inner climb, backslash, key as array, key split across
  route segments, listing directory with leading-slash traversal.
  Dismiss: the observed symptom is an upload URL; the other branches look unrelated.
- T2 (A, far second implementation): DOS adapter — multipart upload directory,
  delete (split segments joined), list (`packages/next-tinacms-dos/src/handlers.ts`).
  Dismiss: a sibling package that looks like an S3-compatible copy, not the
  reported handler.
- T3 (A, far adapters with no configured root): Azure Blob and Cloudinary
  upload/delete/list (`packages/next-tinacms-azure/src/handlers.ts`,
  `packages/next-tinacms-cloudinary/src/handlers.ts`).
  Dismiss: those adapters have no media-root option, so a solver argues there is
  no boundary to escape; the advisory's own fix still refuses absolute/traversal
  keys there.
- I1 (injected): S3 batch-delete route in a new module
  (`packages/next-tinacms-s3/src/batch-delete.ts`, exported from `index.ts`).
  Dismiss: solver fixes the single-key delete branch and never sees the
  multi-select route's key array.
- I2 (injected): S3 app-router handler module
  (`packages/next-tinacms-s3/src/app-handlers.ts`, exported from `index.ts`).
  Dismiss: the reported handler is the pages-router one; a parallel app-router
  export in another module looks like a separate surface.
- I3 (injected): DOS copy/move route
  (`packages/next-tinacms-dos/src/copy-handler.ts`, exported from `index.ts`).
  Dismiss: copy is neither upload nor delete, so it is skipped.
- T4 (coupled must-keep-working): delete of a listing identifier that already
  carries the root must not be double-prefixed; literal `%` names must not be
  re-decoded; inner `..` that stays inside is collapsed, not rejected; split
  route segments still resolve; root/trailing-slash listing still works.
  Tested functionally so over-broad fixes fail.

Distinct reasons-to-skip: unrelated-branch / sibling-package / no-configured-root /
separate-batch-route / separate-router-module / different-operation.

## Sites and input shapes the security tests cover
S3 pages handler upload/delete/list; DOS upload/delete/list; Azure upload/delete/
list; Cloudinary upload/delete/list; injected S3 batch delete, S3 app-router
upload/delete/list, DOS copy. Shapes: plain query string, repeated query array,
catch-all route segments, multipart directory+filename, form-data directory+
filename, batch key array, copy source+destination, leading-slash traversal,
absolute POSIX path, Windows drive prefix, backslash, NUL, empty.

## Fairness plan
`instruction.md` states the invariant over every backend the project ships, every
operation class (presign/write/delete/list/copy), every input shape, and both
cases (root configured / no root configured), plus the refusal form (client error,
no storage operation) and the preservation clauses. No file/package/function
names. A blind engineer reading the four adapter packages finds every lever.

## Verified
- Pinned SHA is the parent of the published fix (git log on the shallow fetch).
- Fix diff read in full: 4 handler files + 4 byte-identical new helper files;
  `.changeset` and root `package.json` changes are excluded from the oracle.
- Injected siblings are new modules exported from each package's `index.ts`
  (a file the published fix never touches).
- Flaw reproduces on the pinned tree through every real entry point: a local
  container run gave security 0/73 pass and functional 30/30 pass (nop).
- Oracle (`solution/fix.patch`) closes all 73 security tests and keeps all 30
  functional tests passing (reward 1.0). The gate re-ran it three times
  identically (see gate_report).
- All 12 check patches behave as declared in `build/tinacms-ds/checks/`:
  9 security_fail (one per lever plus the two extra wrong-fix classes),
  1 functional_fail, 2 pass (hardening + alternative), all verified by
  applying each to the pinned+injected tree and running the hidden suite.
- `fix.patch` and every `checks/*.patch` apply with `patch -p1` on the
  pinned+injected tree.
- Gate stages: static fails only on the downstream `blind.patch` +
  `FAIRNESS.md`; nop PASSED; oracle PASSED (3/3); patches PASSED.


## Could not verify
- `present_in_latest`: injected siblings are our-copy-only (n/a).
- Whether any write-side route outside the reviewed adapters exists; the adapters'
  `delivery-handlers.ts` is read-only and out of scope (see below).

## Out of scope (one line)
`packages/next-tinacms-azure/src/delivery-handlers.ts` mints a read SAS for an
unvalidated path with no auth check; it is a read path, unchanged by the published
fix, and not built on. Cloudinary listing still interpolates the raw directory
into its search expression (the upstream fix calls this a separate follow-up).

## Scratch
`~/.tb-graders/cwe/work/tinacms-ds/` (repo branches pinned/inj/oracle).
