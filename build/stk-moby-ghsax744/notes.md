# stk-moby-ghsax744 — build notes

Started: 2026-10-26T02:24:43Z
Ended: 2026-10-26T05:24Z (main task complete and gate-green; the control's nop is green and its
oracle/patches were still queued behind the shared Docker daemon when this session ended; that
background chain continues under nohup and writes build/stk-moby-ghsax744-control/{oracle,patches}-gate.log)

## Task
Stacked H3b2 on moby/moby. Pinned commit `fc274cd2ff4cf3b48c91697fb327dd1fb95588fb` (the earlier
fix A, "Authz plugin security fixes for 0-length content and path validation", is already applied
in the tree). The later published fix B is `e89edb19ad7de0407a5d31e3111cb01aa10b5a38`.
Pattern A+B (published-fix far sites plus uncovered routes). The report is product-level and states
three general invariants; no route, file, function or mechanism is named.

## Levers (one line each)
- T1 (deepseek, advisory route) — a declared `Content-Length` at or above the inspection limit skips
  body capture (`pkg/authorization/authz.go:71-79`, cap at `:18`); reason to dismiss: the cap is
  documented and the in-tree `TestDrainBody` asserts an oversized body yields a zero-length capture.
- T2 (deepseek, advisory route) — the streamed/undeclared-length framing reaches `drainBody`, whose
  full-buffer branch returns a nil body with only a warning (`authz.go:144-161`); reason to dismiss:
  the earlier 0-length fix already routes chunked requests into that helper.
- T3 (deepseek, uncovered upstream) — the client-declared media type decides whether the body is
  shown (`authz.go:172-193`), while JSON is decoded from the body without a media-type check in the
  swarm, plugin and checkpoint handlers; reason to dismiss: `sendBody` documents a JSON-only body
  and most JSON handlers enforce the type themselves. Coupled keep-working: legit JSON routes and a
  2 MiB non-JSON upload.
- T4 (mimo, uncovered upstream) — the response adapter flushes buffered output to the client when
  the next write would exceed 64 KiB, before `AuthZResponse` runs (`response.go:50,120-130,169-204`);
  reason to dismiss: the buffer is an explicit memory bound with a TODO and streaming endpoints must
  flush as they go. Coupled keep-working: explicit incremental flushing still delivers.
- T6 (both, published-fix far site) — `isAuthEndpoint` is given `url.Parse(...).Path`, which starts
  with `/`, while its pattern expects a host-prefixed path, so the credential body is always shown
  (`authz.go:163-170,181-184`); reason to dismiss: the plugin is trusted and the login body never
  feeds an authorization decision. Coupled keep-working: the login request still reaches the daemon
  and credential headers stay hidden.

Concepts (independent reference edit sites): [T1,T2] body capture, [T3] media-type routes,
[T4] response ordering, [T6] auth-path exclusion.

## Verified on the pinned tree (local, GOPATH mode, Go 1.27 host)
- All 8 security tests fail on the pinned tree and pass on the reference fix.
- All 7 functional tests pass on the pinned tree and on the reference fix.
- `go test ./pkg/authorization` passes on the pinned tree, the reference fix, and every check patch
  except the deliberately over-broad ones.
- Every check patch was run locally: miss_framing/miss_media/miss_response/miss_auth/flush_after_append/
  upstream_fix/upstream_first_fix leave at least one security test failing with functional green;
  refuse_all, crash_as_refusal and adjacent_api break functional; alt_correct_fix and hardening score
  green; the control's four advisory-route security tests fail on pinned and pass on its reference.
- Every patch applies cleanly to a pristine checkout with `patch -p1`.
- The control task's instruction.md is byte-identical to the stacked task's.

## Could not verify here
- Whether Docker's artifact restore replaces /workspace by mount or copy; both keep the
  `/go/src/github.com/docker/docker -> /workspace` symlink working.
- The exact mapping of each GHSA id to its commit (A vs B) is taken from the reader record and the
  supplied fix-commit list; the 2019 commit is A and e89edb19ad7d is B, but no advisory page was read
  to confirm the id-to-commit pairing.
- The upstream intent for an oversized body (refuse versus buffer) is not documented in-tree; the
  reference refuses, and the tests also accept a correct fix that shows the body instead.
- No container-level gate result yet at the time these notes were started; see the gate reports.

## Fairness notes
- The pinned `TestDrainBody` asserts the vulnerable behaviour. The reference leaves the now-unused
  helper in place so the project test stays green; a solver may also remove it and update that test,
  and nothing in the report forbids it.
- The report names only the advisory's own impact example; the response-side, media-type-route and
  credential-body protections are stated as invariants over the protected data, not as routes.
- Coupled keep-working values are covered only by the general keep-working sentence plus the
  one-megabyte legitimate magnitude.

## Out of scope
- Image-push bodies that carry registry credentials are not used as a lever: withholding credential
  material from plugins and showing request bodies pull in opposite directions there, and the
  advisory does not cover it. Not built on.

## History / recall checks
- The reader record on disk (`pipelines/stacking/out/reader/h3-ghsa-x744-4wpc-v9h2.json`) is a
  7-trap, `usable: false` analysis; this build follows the screener/lead record supplied with the
  build prompt (traps T1, T2, T3, T4, T6), all of which were re-verified behaviourally on the pinned
  tree rather than trusted.
- `checks/upstream_fix.patch` is the published later fix B ported to the pinned tree (body-capture
  rewrite plus the auth-path repair). It leaves the media-type-route and response-ordering security
  tests failing, so the stack adds coverage beyond what upstream shipped.
- `checks/upstream_first_fix.patch` is behaviourally a no-op: the pinned commit is A's own commit,
  so A is already applied. The nop stage is the direct proof that A alone is insufficient (every
  security test fails on that tree). The file carries a comment-only change so `patch -p1` succeeds.
- `checks/flush_after_append.patch` (catalogue: check_after_adjustment), `miss_response.patch`
  (one_role_or_direction), `miss_media.patch` (unlisted_route) and `miss_auth.patch`
  (malformed_identity) are the wrong-fix-catalogue evidence; refuse_all, crash_as_refusal and
  adjacent_api are functional-fail checks.

## Gate log
- static: PASSED (2026-10-26).
- nop: PASSED. Verifier: 8/8 security tests fail on the pinned tree, 22/22 functional pass
  (7 hidden + 15 project tests). First nop attempt raised an infra error because Harbor's /tmp
  compose file was reaped during an 18-minute queue wait; retried with a private TMPDIR.
- oracle: PASSED (3 runs, strict). Verifier: reward 1.0 each; 8/8 security pass, 22/22 functional
  pass; the oracle agent applied the reference patch to each workspace.
- patches: PASSED; all 12 verified (miss_framing: T1/T2 fail; miss_media: T3 four routes fail; miss_response:
  T4 fail; miss_auth: T6 fail; flush_after_append: T4 fail; upstream_fix: T3/T4 fail). Every one
  leaves functional at 22/22. Batch 2: upstream_first_fix leaves all 8 security failing with
  functional 22/22; refuse_all (13/22 functional), crash_as_refusal (F6 fails), adjacent_api (F7
  fails) are functional_fail; alt_correct_fix and hardening both score reward 1.0 with 8/8 and
  22/22. All 12 checks reproduce their declared outcome (gate report: each ok=true).
- control: static PASSED; nop PASSED (4/4 advisory-route security tests fail, 22/22 functional
  pass). Oracle and patches were still in the shared daemon's queue at session end (see logs).
- control: static PASSED; nop/oracle/patches pending.
