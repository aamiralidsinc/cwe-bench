# stk-openremote-29156 — build notes

Start: 2026-10-22T20:17:27Z. Restored and re-verified: 2026-10-23T04:03–06:12Z.
End: 2026-10-23T06:12:56Z.

Repository: openremote/openremote, pinned `3dd5fd93f2b9971c52660dbae48af94c108991a5`;
published fix `de89b8d3af272d717bf297934c2cbc97243f08b7`. Pattern A+B, track stacked, reader record
`stacking/out/reader/h4-29156.json`.

The pinned commit is the direct parent of the published fix (`git cat-file -p de89b8d3` -> parent
`3dd5fd93f...`). The published fix touches only `UserResourceImpl.java` plus its own Groovy tests;
it does not touch session disconnection, so the recall check leaves the three session-control
security tests failing. Those regression tests exist only in the fix commit, not at the pin.

**Restore note.** The task tree had been removed from `tasks/` after the first session. It was
restored from the gate's last temp copy (`/tmp/gate-ne43377h`), whose tests/instruction/task.toml
are the final files (mtimes 23:30–23:33, matching the recorded 14/18 suites). That copy's
`solution/fix.patch` had been overwritten by a patch check (it held the refuse-all variant), so the
reference was taken from the surviving scratch tree
(`~/.tb-graders/cwe/work/stk-openremote-29156/fix.patch`, the full fix: published fix + the
session-disconnect guard + the broker owner lookup). The control tree was rebuilt from the same
report/tests: its `SecUserReadTest` and 4/7 suites reproduce the recorded nop result exactly
(failure line numbers 24/33/42/51 and the same messages).

## Levers (one line each)

- **T1** — advisory route: the per-user profile read checks only READ_ADMIN/own-id, never the path
  realm or the looked-up user's realm, and the lookup is realm-blind, so an own-realm path with a
  foreign user identifier returns that user. Fix: realm accessibility plus user-belongs-to-realm.
- **T2** — same decision missing on the per-user client-role and realm-role lists; the Keycloak
  lookup is scoped to the path realm, so naming the target's realm reaches it.
- **T3** — the per-user session list is fetched from the broker by subject identifier only; the sink
  takes no realm.
- **T4** — far site (deepseek): the realm-level client-role catalogue has only the READ_ADMIN
  annotation and never checks realm accessibility; it returns role definitions, so it looks out of
  scope.
- **T5** — uncovered route (deepseek): session disconnect has no annotation and no realm, ownership
  or role decision; the sink is in another package and takes an opaque connection id.
- **T6** — far site (mimo), coupled value: the current-user reads pass the client Realm header into
  the per-user handlers, so the new realm+user decision rejects the caller's own record for a
  superuser whose header names another accessible realm. Fix: address the authenticated realm.

Concepts: C1 = T1/T2/T3/T6 (per-user read scoping plus the current-user coupling), C2 = T4
(realm-level role definitions), C3 = T5 (session control).

## Verified in this rebuild (2026-10-23)

- `static`: PASSED for both tasks (blind patch declaration supplied by `normalize_expect.py`).
  `check_stack.py`: conforming, 3 concepts, pattern H4.
- `nop`: main PASSED — 14/14 security tests fail on the pinned code, 18/18 functional pass.
  Control PASSED — 4/4 security fail, 7/7 functional pass, 11 tests.
- `oracle`: main PASSED — 3 runs, each reward 1.0, 32/32, identical. Control PASSED — 3 runs,
  each reward 1.0, 11/11, identical.
- `patches`: main PASSED — all 13 declared checks behave as declared:
  miss-per-user 8 security failures (functional all pass), miss-role-definitions 3,
  miss-session-control 3; refuse-all leaves 16 functional errors; realm-equality 5 and
  current-user-header 1 functional failures; crash-as-refusal 6, wrong-object 8, get-only 8 and
  superuser-exempt 1 security failures; alternative and hardening 1.0; upstream_fix leaves the 3
  session-control security tests failing (recall).
  Control PASSED — sf-no-get-guard leaves the 4 profile reads open; ff-realm-equality breaks the
  superuser cross-realm functional read; pass-hardening scores 1.0.
- The reference patch and all 16 check patches apply cleanly to the pinned tree.
- Register row for T5 (`build/audit/uncovered-routes.tsv`); the stale duplicate row (which said
  `present_in_latest=no`) was removed, leaving the verified `yes` row.

## Could not verify

- The project's own affected-area test (`UserResourceTest.groovy`) starts the full manager against
  live Keycloak and PostgreSQL and cannot run in the offline verifier; it is not run. The hidden
  functional group drives the same `UserResource` operations with the same realm/user shape.
- Whether a non-superuser can reach a route with a Realm header different from its token realm:
  `TokenVerifierImpl` rejects that combination for non-superusers, so no test relies on it.
- The exact split of Keycloak client roles held by the project's test master admin was not traced;
  the harness constructs the token claims directly (realm role `admin` plus READ_ADMIN/WRITE_ADMIN
  client roles), matching the roles the guards consult.
- `stacking.score_at_build` is carried from the first build's `stacking/score_stack.py` run; it was
  not recomputed here.

## Tooling notes (outside the task)

- The manifest uses `expect: "security_fail"` on the concept miss checks and the recall check, the
  vocabulary `builder/gate.py` and `stacking/check_stack.py` accept; `normalize_expect.py` adds the
  blind declaration the strict static stage requires.
- `run_blindfix.sh` extracts `/app` from the agent image, while frontier-conformant tasks (this one
  and other stacked tasks) keep the checkout in `/workspace`. The blind step therefore cannot see
  this task's tree as written; this is a shared-runner issue affecting the other stacked tasks too,
  not a defect of this task (the gate does not run blind).

## Outside scope (one line)

- Post-pinned upstream refactors (including the later session-disconnect guard) are outside this
  build; the task uses only the pinned tree.

## Control task

`stk-openremote-29156-control` uses the same pinned code and the same instruction, with only the
advisory's own profile-read route in its security suite (4 cases) and a reference that adds the
realm+user decision to that read and moves the current-user read to the authenticated realm.
All four gate stages pass (above).
