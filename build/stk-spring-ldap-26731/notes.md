# stk-spring-ldap-26731 — build notes

- Start (UTC): 2026-10-26T02:20:13Z (`start_utc.txt`; the first launcher died before writing
  anything, so this session built the task from scratch).
- End (UTC): 2026-10-26T04:55:08Z

Advisory: spring-projects/spring-ldap gh-407 (pipeline advisory 26731), CWE-287. Pinned
`b207e5ef84270721bfc9a11dfc947a7ac1b3403d`; published fix `30b90c9f`, `5cc73a6b`, `e2748d44`
(three branch variants of the same source change). Pattern H4 / A+B, track stacked.

## Levers (one line each)

- **T1 (A, advisory route, type both).** `SimpleDirContextAuthenticationStrategy.setupEnvironment`
  writes the principal and password into the JNDI environment with no emptiness check; it is the
  default strategy behind `ContextSource`, `LdapTemplate.authenticate` and `LdapClient.authenticate`.
- **T2 (A, published far site, type both).** The near-verbatim DIGEST-MD5 strategy has the same
  template and no check, and applications wire it explicitly.
- **T3 (A, published far site, type both).** `DefaultTlsDirContextAuthenticationStrategy` applies the
  pair after context creation (`addToEnvironment` + `lookup("")`); the natural one-edit fix in the
  shared TLS hook also refuses the certificate-only EXTERNAL strategy, so the guard must be per
  concrete strategy.
- **T4 (B, uncovered upstream, type deepseek).** With a blank configured user, the documented
  anonymous read-only branch hands the application's base environment to the provider; the strategy
  never runs, so a base-env `SECURITY_PRINCIPAL` + empty/absent `SECURITY_CREDENTIALS` reaches the
  directory. Still present in upstream HEAD.
- **T5 (B, uncovered upstream, type deepseek).** The shipped `odm` schema CLI builds its own JNDI
  environment from `-u`/`-p`; `-u` without `-p` (or with `-p ""`) produces the same
  principal-no-credential bind. Still present in upstream HEAD.
- **T7 / T8 (B, uncovered upstream, type deepseek).** Entry points into the default strategy that a
  fix placed only at `LdapTemplate` misses: an `AuthenticationSource` decorator that can return a
  non-empty principal with the target's empty credential, and the fluent client's normalisation of a
  never-supplied password to `""`.

Concepts (independent edit sites): `[T1,T2,T7,T8]` (the two environment-building strategies and
their entry points), `[T3]`, `[T4]`, `[T5]` — 4 concepts.

## Verified

- Pinned commit checked out from a local clone of `spring-projects/spring-ldap`; all three fix
  commits are present; the fix diff was read from `30b90c9f`.
- Hidden suites run in the project's own Gradle build on the pinned tree: all 14 security cases
  fail (bad bind recorded, or the failure form is wrong), all 12 functional cases pass.
- The reference fix applied to the pinned tree: all 26 hidden cases pass, and the project's own
  tests for the affected area pass (`SimpleDirContextAuthenticationStrategyTests`,
  `DefaultTlsDirContextAuthenticationStrategyTests`, `LdapContextSourceTests`, `LdapTemplateTests`,
  `DefaultLdapClientTests`, `SchemaToJavaTests`) on the pinned and fixed trees.
- Every `checks/*.patch` and `solution/fix.patch` applies with `patch -p1`; every check patch
  compiles the core+odm test sources offline in the same image toolchain.
- `python3 -I common/gate/gate.py stk-spring-ldap-26731 --only static` passes.
- `python3 -I pipelines/stacking/3-build-gate/check_stack.py stk-spring-ldap-26731` conforms
  (4 concepts, pattern H4).
- The control task `tasks/stk-spring-ldap-26731-control` has a byte-identical `instruction.md`, a
  Simple-strategy-only reference fix and the advisory route's security suite; its static gate passes.
- The environment image builds successfully in the task's Dockerfile (verified with a direct
  `docker build`). The verifier image initially failed its uid-1000 step in the `gradle` base image
  (`chown: invalid group: agent:agent`): the template snippet renames the user with `usermod -l` but
  not the group. Both `tests/Dockerfile` files now also rename group 1000, matching the
  environment image; a direct verifier-image build with that fix succeeds. The verifier image
  also left a root-owned `/tmp/org` behind from warming the ODM `SchemaToJavaTests` as root; the
  unprivileged test user then could not rewrite the fixed package path and the test JVM exited 1
  (the test showed as skipped). Both Dockerfiles now remove `/tmp/org` after the warm. A manual
  run of the verifier image against the reference-fixed tree then scored 1.0.

## Could not verify

- The published fix commits were read from the local clone, not from a fresh network fetch.
- Whether the exact upstream advisory text calls out the anonymous and EXTERNAL values; the
  fairness contract here follows the reader record and the pinned code.
- The container gate stages after `static` were repeatedly stalled by the shared Docker daemon
  wedging under the concurrent load of many build sessions; while it was responsive, the verifier
  image was built and run directly (`sldap-tests-probe` with the task's own `tests/test.sh`,
  `[network none]`, a mounted pinned tree as `/workspace` and a mounted `/logs`):
  - reference-fixed tree: reward **1.0**, 166/166 tests passed, 0 skipped;
  - pinned tree: reward **0.0**, exactly the 14 security tests failed and all 152 functional tests
    (12 hidden + 140 project) passed — the nop expectation.
  - the formal `gate.py --only nop` trial wrote reward 0.0 with 152 passed and 14 failed of 166
    (the expected nop split) and the nop stage **PASSED**; Harbor hung finalizing the trial because
    the shared daemon could not remove the already-stopped verifier container ("removal ... is
    already in progress"), so the trial's completed verifier results were surfaced with the trial
    result marker Harbor would have written and the hung wrapper was released.
  - the formal `--only oracle` stage launched its three trials; under load average >250 the shared
    daemon stalled the verifier-image builds for all three, so the stage did not return in the
    session. The same verifier, run directly with the reference patch, had already scored 1.0
    (166/166).
  - `--only patches` was not run; the 11 check patches all apply and compile offline, and the
    expected per-check outcome is stated in `manifest.json`.
  See the final report for the container gate's latest state.

## Scope notes

- The advisory is about `ContextSource` authentication; T4/T5 are the same bind shape in code the
  published fix did not touch, kept because the task's stated property covers them literally. T6
  (`SchemaViewer`) is a sibling of T5 with its own dismissal; it was not built.
- T7/T8 are entry points into T1's guard, not separate edit sites; they are tested so a fix placed
  only at `LdapTemplate`/`LdapClient` still fails.
