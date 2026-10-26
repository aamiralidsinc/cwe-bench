# payload-plugins-ds — build notes

- Task: `payload-plugins-ds` (pattern A, track injected)
- Advisory: GHSA-4QPV-39HG-F7FX / CVE-2026-59965 — CWE-863, Payload Local API default
  `overrideAccess:true` bypasses collection access in the alt-text plugin's endpoints and in an
  elevated-access cached aggregate.
- Pinned: `1ac5d7ee8bf228a214723439b959d8f2740dd4ec`; published fix: `e39634868ce13a414e2981e219befc58101654d3`
- Start: 2026-10-24T05:18:07Z (pipeline start); build end: see the end of this file.

## One-line mechanism summary

The plugin's HTTP handlers and reporting utility call the Payload Local API without
`overrideAccess:false,user:req.user`, so the collection's own read/update access is never applied;
the health aggregate is computed once with elevated access and cached under a user-independent key,
so a complete scan is returned to every caller.

## Security property (written once, over the protected data)

Every request handled by the plugin is limited to what the requesting user's collection access
rules allow on the affected documents: no alt text, keywords, identifiers, counts or other
information about documents the user may not read, and no change to alt text or keywords on
documents the user may not change — whatever operation the request uses, and including results the
plugin computed earlier and shares between requests. Collection-wide information is governed at
collection level: a read rule that limits a user to some documents still grants the collection-wide
information. A request that cannot be satisfied without disclosing or changing protected data gets
an error response and leaves no change; a response that can be limited to accessible data contains
only that data.

## Levers (each with a different reason a solver skips it)

| # | type | site | shape | reason to dismiss |
|---|------|------|-------|-------------------|
| T1 | how: producer off the check's path + coupled shared cache | `alt-text/src/utilities/altTextHealth.ts:88-130,224-238` (elevated compute + user-independent cache key) and `:241-243` (`getAltTextHealth`) | The per-request check never calls the compute; the compute must stay elevated for the shared cache, and the cached result must be filtered per request. Flipping the compute to `overrideAccess:false` is the tempting wrong fix: the cache key has no user, so one user's view is served to another (or, if the low-priv request warms it, the admin loses data). | The `overrideAccess: true` is explicit and the scan is a read-only shared report, so it reads as deliberate design while the report names the generate route. |
| T2 | where: separate implementation, far file | `alt-text/src/endpoints/bulkGenerateAltTexts.ts:120-124,170-178` | Its own `generateAndUpdateAltText` helper does a read and a per-locale update loop; a fix to the single-image handler changes nothing here. | "Bulk is a separate/admin batch feature"; the report's example is the single-image route. |
| T3 | where: second consumer of the same producer | `alt-text/src/utilities/altTextHealth.ts:245-257` (`getAltTextHealthWidgetData` calls `getAltTextHealthScan` directly) | Fixing `getAltTextHealth` (or the endpoint) does not fix the widget data path; the two consumer functions reach the scan independently. | The dashboard is admin UI for trusted users, and "the health API is fixed". |
| T4 | shape: read vs write split | `alt-text/src/endpoints/generateAltText.ts:31-35` vs `:121-129`; bulk `:120` vs `:170` | A guard added to the lookup leaves the persist writes elevated (and vice versa). Preview and persist are two modes of the same request. | The read is the visible channel; the writes look like the framework's own save. |
| T5 | injected sibling: maintenance route | new `alt-text/src/endpoints/backfillMissingAltTexts.ts`, registered in `plugin.ts` | `payload.find` (default elevated) selects missing-alt docs and `payload.update` writes them; the response reports how many were found. Guarding only the update leaves the count/target-set leak; guarding only the find leaves the write path. | It is a gap-filling maintenance action next to the health widget; the selection looks internal and only counts are returned. |
| T6 | injected sibling: read-only export | new `alt-text/src/endpoints/exportAltTexts.ts`, registered in `plugin.ts` | `payload.find` (default elevated) returns alt/keywords/filename for a whole collection. | Read-only, no writes, and not a "generation" route. |
| T7 | injected sibling: caller-content import | new `alt-text/src/endpoints/importAltTexts.ts`, registered in `plugin.ts` | `payload.update` (default elevated) writes caller-supplied alt/keywords to the given ids; no read at all. | An admin metadata-migration utility; it looks like a write-only path so no leak is suspected. |

## All sibling candidates found (before picking)

Real code: `bulkGenerateAltTexts.ts` helper (T2); `altTextHealth.ts` widget consumer (T3); the
update sites (T4). Lead list from the screener plus own search:
1. `plugin.ts` third endpoint "generate all missing in a collection" — **picked T5** (find + update, count leak).
2. `hooks/revalidateAltTextHealth.ts` afterChange auto-generate hook — rejected: not an HTTP entry
   point, and the natural version writes the document the user just changed (access already
   required); a broader sweep would be contrived.
3. `plugin.ts` read-only audit/export endpoint — **picked T6** (find only, returns alt/keywords).
4. `plugin.ts` import/migration endpoint — **picked T7** (update only, caller content).
5. A per-collection uncached stats endpoint using `find` + `summarizeCollection` — rejected: same
   concept as the health aggregate (more routes of one concept).
6. A copy-alt-between-locales endpoint — rejected: it touches the same document, so the same
   document access; no distinct object.
7. A duplicate/clone endpoint — rejected: needs a create path and is less plausible as plugin
   code.
8. A server-side migration utility called from config — rejected: no request/entry point.
9. Other workspace packages (`content-translator`, `pages`) that also call the Local API —
   outside this advisory's protection (noted as out of scope; not built on).

Picked T5/T6/T7 because they are three different mechanisms (read+write, read-only, write-only),
all reachable through the plugin's registered endpoints, none in a file the published fix touches,
and each has a distinct plausible dismissal. T5 is the most complex (two Local API calls and a
count response).

## Sites/routes and input shapes the security tests cover

- single-image generate: preview (`update:false`) and persist (`update:true`); string and numeric id.
- bulk generate: read denied; read allowed/update denied; per-locale update loop; several ids.
- public server API `getAltTextHealth` (lower-level API) and `GET /alt-text-plugin/health`.
- widget data path `getAltTextHealthWidgetData`.
- shared-cache ordering: admin warms then low-priv request; low-priv warms then admin request.
- health error entries tagged with a collection.
- collection read access: `true`, `false`, a scoped `Where`, throwing.
- injected: backfill (find+update), export (find), import (update).
- refusal: any error response (no exact status) plus no write / no protected data.

## Coupled must-keep-working (functional)

- preview for a user who may read but not change the document.
- persist for a user who may read and change it.
- bulk over several accessible docs updates all locales.
- a user whose read rule is a scoped `Where` still gets the collection-wide entry.
- admin sees the complete aggregate even after a low-priv request warmed the cache.
- authorized backfill/export/import still work.
- the project's own unit tests for the area (summarize, mime types, schemas, field validation).

## What I verified

- The pinned project tests pass under Node 22 with `node --experimental-strip-types --test`
  (40/40).
- The plugin can be constructed with a fake Payload config and its registered handlers called; the
  health scan's `next/cache.js` import is replaced in grading by a test-side in-memory cache with
  the same contract (alias in the hidden vitest config), giving real cross-request sharing.
- The published fix's diff and its two new tests were read; the oracle patch is the source part of
  that diff (plus fixes for the injected siblings).
- The cache trap: with the compute flipped to access-scoped but a user-independent cache key,
  admin-first serves secret data to a low-priv caller, and low-priv-first hides it from the admin.
- Local pre-flight of every `checks/*.patch` on the injected vulnerable tree:
  - on the pinned code: 28/28 security tests fail, 17/17 hidden functional tests pass, and the
    project's 5 test files pass;
  - on the oracle: 45/45 hidden tests and the project tests pass;
  - each `security_fail_*` patch leaves at least one security test failing with all functional
    tests passing; each `functional_fail_*` patch fails at least one functional test;
  - `pass_hardening.patch` and the user-scoped-cache alternative score 1.0;
  - the auxiliary route patches (backfill/export/import) also leave the project tests passing.
- The injection patch applies cleanly to a pristine checkout of the pinned commit
  (`patch -p1 --dry-run`).

## Gate run notes

- static: passed (no warnings; blind patch and FAIRNESS.md are produced after this build).
- nop: passed on a task-private dockerd — 28 security tests all fail on the pinned code and 57
  functional tests pass (17 hidden + the project's 40).
- oracle: passed — 3 independent runs, each 28/28 security + 57/57 functional, reward 1.0, with
  identical per-test results.
- First nop attempts on the shared daemon failed as infrastructure errors: the shared VM's `/tmp`
  tmpfs hit 100% inodes during one Docker build ("mkdir /tmp/containerd-mount…: no space left on
  device"), and later the shared daemon's `/info`/`/version` stopped answering under ~40 concurrent
  gate runs ("Docker daemon is not running"). Neither is a task failure. Workaround: a
  task-private dockerd with its `data-root`/`exec-root` on the disk-backed home filesystem, a
  unique bridge/pool (10.242/10.243) and `TMPDIR` on disk; all subsequent stages ran there.
- The shared VM was at load average 100–160 with many concurrent gate runs, so the shared daemon
  was not usable.
- On the private daemon, the first oracle attempt lost its address pool mid-stage: another task's
  private bridge (`acpriv0`) claimed 10.243/16 right after our daemon started, so compose could
  not allocate a subnet ("all predefined address pools have been fully subnetted"). Oracle run 1
  itself had already scored 1.0 (28/28 security, 57/57 functional). The daemon was restarted with
  a 192.168.0.0/16 pool and matching NAT/FORWARD rules; the stage was re-run.
- Final full gate (`python3 -I builder/gate.py payload-plugins-ds`, all stages in order) on the
  system Docker daemon after the host daemon was repaired: **PASSED** — static ok; nop 28 security
  failures / 57 functional passes; oracle 3/3 runs reward 1.0 with identical results; patches
  13/13 as declared. `build/payload-plugins-ds/gate_report.json` records `verdict: pass`,
  `passed: true` (started 2026-10-24T07:48:12Z, finished 2026-10-24T09:16:54Z).

## Could not verify / guesses

- `present_in_latest` for the injected siblings: they do not exist upstream (injected); the
  published health read-access behaviour is in the fix commit and current upstream beyond that
  commit was not inspected.
- The real Next `unstable_cache` cannot run outside a Next server; grading uses a contract-matched
  stub. The stub is test-side only and never visible to the solver.
- Whether the two target models fail all three attempts: the build brief forbids running trials;
  the gate is the build proof and the bar is evaluated later.
- The injected sibling routes are maintainer-plausible but not upstream code; their style was
  matched to the package by hand.

## End

- End (UTC): 2026-10-24T09:17:00Z
