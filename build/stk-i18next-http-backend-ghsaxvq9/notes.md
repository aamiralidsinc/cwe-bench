# stk-i18next-http-backend-ghsaxvq9 — build notes

Started: 2026-10-26 02:08 UTC (work dir created)
Builder: build-v1, stacked H3b, pattern A+B.

## Scope

- Repo: i18next/i18next-http-backend, pinned `4cbc48741128d9b1f6cceb43edabfbec84c92615`
  (direct parent of the first published fix `4cee84f229c6`, 3.0.5).
- Advisories: GHSA-q89c-q3h5-w34g (value interpolation into the request URL, 3.0.5) and
  GHSA-xvq9-wjp8-hwqf (scheme injection when the template starts with the placeholder, 4.0.2).
- Second fix: `07e028862b25` (4.0.2). Only its source semantics are used: the second fix's
  helper edits are written against the post-v4-refactor tree and do not apply to the pinned
  pre-refactor tree, so `checks/upstream_fix.patch` is the two published fixes reduced to the
  pinned source (A's three files plus the `:` denylist entry from B). The `//`-in-`ns` half of B
  is already covered by A's global denylist (which rejects `/` in both values).
- Bug classes: CWE-918 (primary), CWE-74 (sub-case).

## Levers (one line each)

- T1 (both; advisory route): read-side value interpolation lets a supplied language/namespace
  choose the request destination (scheme, traversal, query, joined multi-value), through string,
  function and promise locations and both transports. `lib/index.js:55-66,74`,
  `lib/utils.js:47-52`, `lib/request.js:162-170`. No reason to dismiss (reported route).
- T2 (deepseek; published-fix far site): the same value construction on the opt-in write path
  `create`/`addPath`. `lib/index.js:110-135,7`. Reason to dismiss: dormant unless saveMissing +
  addPath are configured; it reads as an app-owned opt-in write endpoint.
- T7 (deepseek; uncovered upstream route): the transport follows a redirect served by the
  configured destination. `lib/request.js:51-72,89-97,146-152`. Reason to dismiss: redirects are
  normal HTTP and the configured origin is trusted; no published fix touches the transport
  (current master 44312912 still calls fetch with default redirect handling).
- T8 (mimo; coupled must-keep-working value / rule shape): the value rule must stay scoped to
  the supplied values. `lib/index.js:6-7,63,74`, `lib/request.js:38-49,89-97`. Reason to
  dismiss: the visible values are the legitimate ones, so absolute-http(s)-only looks safe.

Concepts: [T1, T8], [T2], [T7]. DeepSeek-type: T2, T7. MiMo-type: T1 (both), T8.

## What was verified

- Gate static: PASSED.
- Gate nop (Harbor, offline verifier): PASSED — 17/17 security tests fail on the pinned code,
  52/52 functional tests pass (15 hidden fetch + 3 hidden XHR + 34 project tests across both
  transports); reward 0.0.
- Gate oracle: PASSED — three reference runs, reward 1.0 each, identical results.
- Gate patches: first wave (the three `miss_concept_*` checks) exactly as designed:
  miss_concept_read 10 security failures / 0 functional, miss_concept_write 5 / 0,
  miss_concept_redirect 2 / 0.
- Pinned code, local harness: all 17 security tests fail (a local HTTP server receives the
  attacker-chosen request); all 18 hidden functional tests pass; the project's own tests pass on
  both transports (mocha: 18 fetch / 16 XHR).
- Reference (`solution/fix.patch`, pinned → oracle tree): all 17 security and all 18 functional
  tests pass; project tests pass on both transports.
- `checks/upstream_first_fix.patch` (A alone): 6 security tests fail, functional all pass.
- `checks/upstream_fix.patch` (A + `:`): 2 security tests fail (both redirect cases), functional
  all pass — the stack adds beyond upstream.
- Every `miss_concept_*.patch`: exactly its concept's security tests fail, functional all pass.
- `sf_template_only.patch`, `sf_lng_only.patch`: security fails, functional passes.
- `ff_absolute_only.patch`, `ff_refuse_all.patch`: functional fails.
- `alt_correct_fix.patch` (per-key allowlists + `redirect: 'manual'`) and `hardening.patch`
  (reference + per-segment allowlist + URL length cap): reward 1.0 locally.
- `check_stack.py`: conforming (3 concepts, pattern H3b); control instruction byte-identical.
- Control task: static PASSED; its own nop/oracle/patches gate to be recorded below.

### Infrastructure notes

- The shared VM ran at load average ~128 during the build. Two gate attempts failed on host infra
  (not the task): one Harbor compose bring-up stalled on a dead egress sidecar, one oracle run hit
  a transient `/tmp` "no space left" during a compose image export. Both were retried; the oracle
  retry used `GATE_PARALLEL=2`, and the patches stage uses a task-local `TMPDIR`.

## What could not be verified

- The ghsa texts used are the public advisory pages; the A commit message says its GHSA was
  filed after release, and the mapping GHSA-q89c-q3h5-w34g -> 3.0.5 is taken from the task input
  and the public page, not from a commit trailer.
- The XHR transport cannot be constrained on redirects (browser/platform behaviour), so T7 is
  tested on the fetch transport only; the reference leaves XHR redirects alone. A fix that only
  patches fetch still passes, which is deliberate.
- The second fix's literal diff does not apply to the pinned tree (intervening v4 refactor);
  `upstream_fix.patch` is an equivalent reduction (see Scope).
- The reader record used is `pipelines/stacking/out/reader-ds/h3-ghsa-xvq9-wjp8-hwqf.json`
  (the prompt's `out/reader/` path has no such file).

## Fairness

- The report gives one impact example (the advisory's own route) and one general property.
  No hidden route or coupled value is named or described: "everything that works today keeps
  working exactly as today" is the only keep-working line.
- The coupled values are only enforced through the functional suite (relative default, leading
  placeholder, falsy abort, `+` join, regional tags, query parameters, custom request verbatim,
  alternateFetch) so an over-broad fix fails without any hint in the report.
- Out of scope: none noticed.
