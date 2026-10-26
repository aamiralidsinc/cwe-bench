# stk-vikunja-ghsaxv7q — build notes

- Start (UTC): 2026-10-22T20:58:20Z (first build); rebuilt from the preserved artifacts at
  2026-10-22T23:53Z.
- Pipeline restart (UTC): 2026-10-23T05:03Z re-ran `run_build.sh`, which starts a fresh task tree, so
  `tasks/stk-vikunja-ghsaxv7q{,-control}` were reconstructed byte-for-byte from the preserved work
  tree (`~/.tb-graders/cwe/work/stk-vikunja-ghsaxv7q/`, still holding the hidden suites, the pristine
  project test and the reference checkout), the surviving `build/.../checks`, and the first
  session's writes; all four gate stages were then re-run from scratch (see below).
- End (UTC): 2026-10-23T06:59Z for the reconstruction and the main-task re-gate; the pipeline then
  runs its own full gate and the blind fix.
- Pinned commit: 546db0dc219c736a34336dab9f3411ee7b821fde — exactly the parent of A's first fix commit
  (`git rev-parse b642b2a4536a^` returns it). A and B are both absent from the checkout.
- Published fixes: A b642b2a4536a (frontend TOTP prompt, GHSA-8jvc-mcx6-r4cg), B 7854f2729ab7
  (verified-email OIDC fallback, GHSA-xv7q-fvmc-jx96).
- Entry point: POST /api/v1/auth/openid/:provider/callback (openid.HandleCallback), driven in-process
  with a loopback fake OIDC provider (discovery, JWKS, token exchange, signed ID token, profile
  response). No external network at test time.

## Levers

- T1 (concept C1, advisory route): the fallback match uses the reported address with no verification
  assertion — pkg/modules/auth/openid/openid.go:361-391; reason to dismiss: it is the reported route.
- T2 (concept C2, uncovered_upstream, how-type): the assertion must follow the address when the
  provider's separate profile response supplies it — openid.go:440-442,484-499; reason to dismiss: a
  check reading the assertion from the identity token looks complete, and the merge only fills blanks
  or honours an admin preference.
- T3 (concept C1, coupled value, MiMo-type): the assertion may be absent or a string, and first-time
  registrations and already-bound identities must keep working — openid.go:75-97,393-446; no separate
  security test; `ff-strict-decode.patch` proves the coupled value is enforced.
- T4 (concept C3, absent protection, DeepSeek-type): the fallback attaches to a local account that has
  not confirmed its own address — user.go:324-330,370-373, openid.go:381-446, user_create.go:96-100;
  reason to dismiss: the advisory is about the provider's assertion, the local row is first-party data
  and the account is not disabled or locked.

Concepts: C1=[T1,T3] (one edit site: claims decode + fallback gate), C2=[T2], C3=[T4].
DeepSeek-type: T4. MiMo-type: T2 (how-type) and T3 (coupled).

## Verified locally (pinned worktree, go test)

- nop: 6/6 hidden security tests fail; 6/6 hidden functional and 4/4 project tests pass on pinned.
- oracle: all 6 security, 6 hidden functional and 4 project tests pass with solution/fix.patch.
- Control: 4/4 control security tests fail on pinned; 4/4 security and 5/5 hidden functional pass
  with the control reference.
- The fake provider uses only loopback httptest servers; no external network at test time. Avatar
  sync is avoided by leaving the picture claim empty.
- The restored project test removes the two fallback subtests whose expectation (fallback linking
  with no verification assertion) contradicts the security rule, as the reader's fairness note
  requires.

## Check patches

- sf-no-verified-gate: misses T1, functional passes.
- sf-no-merge-source: misses T2 (assertion from either source certifies), functional passes.
- sf-no-confirmation-check: misses T4 (unconfirmed local account), functional passes.
- ff-refuse-all: security passes, functional fails.
- ff-strict-decode: security passes, one functional test fails (string assertion).
- crash-as-refusal: all security tests fail (HTTP 500 is not a client refusal), functional passes.
- pass-hardening / pass-alt: all pass.
- upstream_first_fix (A alone): all security fail, functional passes.
- upstream_fix (A+B reduced to this tree): all security fail, functional passes.

## Could not verify

- Real-IdP claim shapes: which providers send the assertion only in the profile response or as a
  string was not checked outside this repo. The task states both forms as a contract and tests only
  that the string form does not break a sign-in.
- T4's real-world harm: with a mailer configured an attacker-created unconfirmed local account cannot
  be logged into by the attacker, so the tested direction is an external identity taking over a local
  account that is still awaiting confirmation. The security test asserts the ownership gate.
- Published fix B was authored on a later tree (July); it was reduced to the April tree by semantic
  equivalence, not by applying the commit. The reference differs from upstream in one deliberate way:
  a conflicting unverified address is refused with a client error rather than silently registered as
  a separate account. The report states this refusal contract explicitly.
- T5 (unverified claim email persisted on an already-linked account) was left out: no path to
  takeover was found.

## Fairness concerns

- The score at build is 0.275 for the built concepts [[T1,T3],[T2],[T4]] (p_fail3 deepseek 0.608,
  mimo 0.452) with the `single-trap-carries` flag: T4 is the hardest concept and the stack has no
  second xhard concept. The reader's chosen T1–T4 design was built as instructed; T5 was not added
  because its impact is unproven.
- The refusal contract is stricter than the published fix's "register a separate account" behaviour.
  It is stated explicitly in the report, and the alternative and hardening patches show that
  different correct designs (400 or 412, a helper or inline) pass.
- Providers that never assert verification lose email fallback. That is the intended security
  outcome; the report does not require fallback without the assertion, and a deployment that prefers
  the profile response keeps working when the profile response supplies the assertion.
- The project test restored at grade time removes two subtests; this is the update the reader's
  fairness note requires, and the security rule would otherwise contradict them.

## Outside this advisory's scope

Nothing outside the advisory's own protection was built on. The frontend TOTP fix (A) is part of the
H3b history and the recall patch, but no TOTP behaviour is tested. T5 and username-fallback hardening
are noted and not built.

## Gate results (main task)

- static: only the permitted missing `blind` pass patch (and FAIRNESS.md, which is written later).
- nop: PASSED — 6/6 hidden security tests fail, all 30 functional entries pass on the pinned code.
- oracle: PASSED — 3 runs, each reward 1.0; result maps identical.
- patches: PASSED after one retry. The first run hit a known Harbor infra flake
  (`network_mode='no-network' is not supported by EnvironmentType.DOCKER environment`, seen in 99
  other build evidence files on this VM) on the 9th check; all checks passed on the retry:
  - sf-no-verified-gate: 5 security fail, 0 functional fail.
  - sf-no-merge-source: 1 security fail, 0 functional fail.
  - sf-no-confirmation-check: 1 security fail, 0 functional fail.
  - crash-as-refusal: 6 security fail, 0 functional fail.
  - ff-refuse-all: 0 security fail, 7 functional fail.
  - ff-strict-decode: 0 security fail, 1 functional fail.
  - pass-hardening: reward 1.0.
  - pass-alt: reward 1.0.
  - upstream_first_fix: 6 security fail, 0 functional fail (upstream's first fix is a wrong fix).
  - upstream_fix: 6 security fail, 0 functional fail (the published fixes together are a wrong fix).
- stacking conformance: `check_stack.py` conforming, 3 concepts, pattern H3b.

## Gate results (control task)

- static: only the permitted missing `blind` pass patch (the control is not given a blind patch).
- nop: PASSED — 4/4 control security tests fail, all 29 functional entries pass on the pinned code.
- oracle: PASSED on retry — 3 runs, each reward 1.0, identical maps. The first attempt's runs 1
  and 2 were already 1.0; run 3 hit the same known Harbor no-network infrastructure flake as the
  main patches stage, not a task failure.
- patches: not run in this session (the 3-hour build budget ended first); the control manifest
  lists the checks it would run (sf-no-verified-gate security_fail, ff-refuse-all functional_fail,
  pass-hardening and pass-alt pass), and each was exercised against the main suite.

## Re-gate after the 2026-10-23T05:03Z pipeline restart (main task)

- static: FAILS only on `manifest.patch_checks has no expect=pass patch with kind='blind'` — the
  permitted exception (the pipeline's `normalize_expect.py` adds that declaration and the blind fix
  is produced later by `run_blindfix.sh`). Every other static requirement passed, including the
  canary/GUID, offline settings, uid-1000 boilerplate, no-leak scan and the wrong-fix catalogue.
- nop: PASSED (second attempt; the first hit the known Harbor `network_mode='no-network' is not
  supported` infrastructure flake seen across this VM). 6/6 security tests fail on the pinned code,
  all functional and project tests pass.
- oracle: PASSED — 3 runs, each reward 1.0.
- patches: PASSED on the first attempt — every check behaved as declared:
  sf-no-verified-gate (5 security fail), sf-no-merge-source (1), sf-no-confirmation-check (1),
  crash-as-refusal (6), ff-refuse-all (7 functional fail), ff-strict-decode (1 functional fail),
  pass-hardening (1.0), pass-alt (1.0), upstream_first_fix (6 security fail, A alone is a wrong
  fix), upstream_fix (6 security fail, A+B are a wrong fix).
- stacking conformance: `check_stack.py` conforming (3 concepts, pattern H3b).

## Re-gate after the restart (control task)

- static: fails only on the permitted missing `blind` declaration (a control is not given a blind
  fix), as before.
- nop: PASSED — 4/4 control security tests fail on the pinned code; functional and project tests
  pass.
- oracle: PASSED — 3 runs, each reward 1.0.
- patches: PASSED — sf-no-verified-gate (4 security fail), ff-refuse-all (6 functional fail),
  pass-hardening (1.0), pass-alt (1.0).
