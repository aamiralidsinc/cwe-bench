# portainer-ds — pre-trial fairness and leniency review

Reviewed: `tasks/portainer-ds/instruction.md`, every file under `tasks/portainer-ds/tests/`,
`solution/fix.patch`, `build/portainer-ds/manifest.json`, `notes.md`, all 11 `checks/*.patch`.
No Docker, trials or gates were run.

Covering labels used below, all quoted from `instruction.md`:

- **P** — "While an instance has no operator account, every action that would grant operator
  authority or replace the instance's persistent state is an operator action: it may proceed only
  for a request that proves knowledge of the instance's current setup token."
- **R** — "A request that does not present the token, presents a wrong one, or presents no usable
  value at all must be refused with a client error and must leave the instance unchanged."
- **N** — "No value a client can send or configure may substitute for that proof, regardless of how
  the request is shaped or delivered."
- **T** — "The token is presented in the `X-Setup-Token` request header ... `PORTAINER_SETUP_TOKEN`
  ... With no token pinned on a fresh instance the server must still require a token that it
  generates itself ... Comparison is exact."
- **K** — "With the correct token, legitimate operator actions continue to succeed exactly as they
  do today, with the same validation and the same success responses."
- **I** — "On an instance that already has an operator account, the corresponding actions keep their
  present behaviour and require no token, including the existing 'already initialized' refusals."
- **M** — "This applies to the instance's state at the moment of the request, whatever state it
  started in."
- **U** — "Information that must stay publicly readable before anyone signs in stays readable
  without credentials."

## 1. Test-by-test fairness

| test (file::name) | what it asserts | covering sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/test_restore.py::test_restore_without_token_is_refused | multipart restore with no header → 4xx; admin/check 404; attacker cannot sign in | P + R (persistent-state branch) | no — any layer (handler, dispatcher, middleware) returning 4xx before state replacement passes | low |
| security/test_restore.py::test_restore_with_wrong_token_is_refused | same with `wrong-token` | P + R ("presents a wrong one") + T ("Comparison is exact") | no | low |
| security/test_restore.py::test_local_restore_without_token_is_refused | JSON server-side restore, no header → 4xx, no takeover | P (persistent-state branch; route need not be named) | no | low |
| security/test_restore.py::test_local_restore_with_wrong_token_is_refused | same with wrong header | P + R + T | no | low |
| security/test_admin_init.py::test_admin_init_without_token_is_refused | first-admin init, no header → 4xx, no admin | P (operator-authority branch) | no | low |
| security/test_admin_init.py::test_admin_init_with_wrong_token_is_refused | same with wrong header | P + R + T | no | low |
| security/test_admin_init.py::test_admin_init_with_multi_value_token_is_refused | comma-joined wrong header value → 4xx | N ("however the request is shaped") + T ("exact") | no | low |
| security/test_admin_init.py::test_admin_init_without_configured_token_is_refused | no pinned token, no header → 4xx (no fail-open) | T ("must still require a token that it generates itself ... must not be disabled just because no value was configured") | no — a correct fix either generates or fails closed | low |
| security/test_legacy_admin_init.py::test_legacy_admin_init_without_token_is_refused | legacy init, no header → 4xx | P (operator-authority branch) | no | low |
| security/test_legacy_admin_init.py::test_legacy_admin_init_with_wrong_token_is_refused | same with wrong header | P + R + T | no | low |
| security/test_automation_import.py::test_automation_import_without_token_is_refused | provisioning list whose first entry omits `Role` (becomes admin), no header → 4xx | P + N (authority from an omitted field is still authority) | no | low |
| security/test_automation_import.py::test_automation_import_with_wrong_token_is_refused | same with wrong header | P + R + T | no | low |
| security/test_setup_state.py::test_admin_init_after_operator_account_removed_is_refused | `--admin-password` instance, operator demoted at run time, init with no token → 4xx | M ("state at the moment of the request") + P | no — binding to startup state is incorrect under M | low |
| security/test_setup_state.py::test_restore_after_operator_account_removed_is_refused | same, then restore with no token → 4xx | M + P | no | low |
| functional/test_first_run.py::test_first_run_admin_init_with_token_succeeds | correct pinned token → 200, admin exists and can sign in | K + T | no | low |
| functional/test_first_run.py::test_first_run_validation_is_unchanged | weak password 400, malformed JSON 400, second init 409 | K ("same validation and same success responses") + I ("existing ... refusals") | no — a token check before payload decoding still returns 400 for a correct-token request | low |
| functional/test_first_run.py::test_public_settings_stays_public | `GET /api/settings/public` → 200 JSON | U | no | low |
| functional/test_restore.py::test_restore_with_token_succeeds | correct token → 2xx/connection drop, then restored admin signs in | K | no | low |
| functional/test_restore.py::test_local_restore_with_token_succeeds | correct token → 2xx, restored admin signs in | K | no | low |
| functional/test_initialized.py::test_restart_with_existing_admin_needs_no_token | restart with existing admin: init/legacy 409, restore/local 400, no token | I (explicit: no token, existing refusals) | no — only a fix that checks the token before the initialized check fails, and that contradicts I | low |
| functional/test_initialized.py::test_admin_password_startup_needs_no_token | `--admin-password` instance: login 200, init 409, restore 400, no token | I ("however the operator account came to exist") | no | low |
| functional/test_initialized.py::test_operator_account_change_keeps_instance_usable | demotion 200, account can still sign in, server still serves | I + K ("keep legitimate use working") | no | low |
| functional/test_legacy_admin_init.py::test_legacy_admin_init_with_token_succeeds | legacy route with correct token → 200 and login | K | no | low |
| functional/test_automation_import.py::test_automation_import_with_token_succeeds | import with token → 200; omitted Role's first account is an admin | K ("succeed exactly as they do today") | no | low |
| functional/test_automation_import.py::test_automation_import_keeps_explicit_roles | explicit roles preserved; viewer denied user list, ops allowed | K | no | low |
| project/backup/restore_test.go::Test_restoreArchive_usingCombinationOfPasswords (3 subtests) | direct `h.restore` on an in-process handler built by `NewHandler(...)` with an uninitialised store: empty/empty-password restore succeeds, mismatched password fails | standard expert knowledge: the project's own tests for the touched packages must keep passing (`tests/test.sh:60-63` restores pristine copies before build) + K | **no for the primary fix** (token resolved at startup, plain exact compare: in this in-process test the handler's expected value is empty and the absent header is empty, so it proceeds, as the oracle does). A guard that explicitly refuses an empty expected token, or a change to `NewHandler`'s 6-argument signature, fails this pristine copy. | medium |
| project/backup/restore_test.go::Test_restoreArchive_shouldFailIfSystemWasAlreadyInitialized | initialized store → exact error "Cannot restore already initialized instance" | I ("existing 'already initialized' refusals") | no | low |
| project/backup/backup_test.go::Test_backupHandlerWithoutPassword_shouldCreateATarballArchive | backup handler with no token creates expected tarball | standard expert knowledge: backup reads state, is not a protected action | no — gating backup would be over-broad | low |
| project/backup/backup_test.go::Test_backupHandlerWithPassword_shouldCreateEncryptedATarballArchive | encrypted backup handler with no token | same | no | low |
| project/users/user_create_test.go::TestConcurrentUserCreation | direct `userCreate` on an uninitialised test store: exactly one success | standard expert knowledge: the route is authenticated-only; P is about unauthenticated actions | no — gating user creation would be over-broad | low |
| project/users/user_list_test.go::Test_userList (4 subtests) | admin/standard user listing and access policy | standard expert knowledge: unrelated existing behaviour | no | low |
| project/users/user_create_access_token_test.go::Test_userCreateAccessToken | API-key creation by standard/admin users | standard expert knowledge: unrelated existing behaviour | no | low |
| project/users/user_create_access_token_test.go::Test_userAccessTokenCreatePayload | payload validation | standard expert knowledge: unrelated | no | low |
| project/users/user_get_access_tokens_test.go::Test_userGetAccessTokens | listing tokens | standard expert knowledge: unrelated | no | low |
| project/users/user_get_access_tokens_test.go::Test_hideAPIKeyFields | serialisation hides secrets | standard expert knowledge: unrelated | no | low |
| project/users/user_remove_access_token_test.go::Test_userRemoveAccessToken | token removal | standard expert knowledge: unrelated | no | low |
| project/users/user_effective_access_test.go::Test_userEffectiveAccess | effective access calculation | standard expert knowledge: unrelated | no | low |
| project/users/user_update_test.go::Test_updateUserRemovesAccessTokens | update removes tokens | standard expert knowledge: unrelated | no | low |
| project/users/user_delete_test.go::Test_deleteUserRemovesAccessTokens | delete removes tokens | standard expert knowledge: unrelated | no | low |

## 2. Leniency (QUALITY — non-blocking)

| property / trap | most plausible wrong fix | caught? (test + checks patch) | gap |
|---|---|---|---|
| P, operator authority (T0 restore) | fix only the admin-init route; leave restore | yes — security/test_restore.py (2) + sf-no-restore | — |
| P, operator authority (T1 far site) | fix only the reported restore route | yes — security/test_admin_init.py (3) + sf-no-admin-init | — |
| P, persistent state (T2 local) | fix only the multipart upload restore | yes — test_local_restore_* (2) + sf-no-local | — |
| P, operator authority (T3 legacy) | fix only the documented init handler, never the deprecated alias | yes — test_legacy_admin_init.py (2) + sf-no-legacy | — |
| P, authority by omission (T5 automation) | fix only handlers whose route says "public"; leave the setup-or-authenticated subrouter | yes — test_automation_import.py (2) + sf-no-import | — |
| R, refusal hygiene | refuse with 500 (crash) | yes — `client_error` in all 14 security tests + sf-crash | — |
| R, refusal hygiene | refuse everyone / remove the routes | yes — 11 functional tests (incl. token-success and project restore) + ff-refuse-all | — |
| T, no pinned token (T4) | env-only producer: empty expected value means "gate disabled" | yes at server level — test_admin_init_without_configured_token_is_refused + sf-env-only | a handler-level fail-open on empty is not reachable in production once startup always generates; the project unit test actually requires it (see row 26) |
| M, request-time state (T6) | resolve the token / initialized decision once at startup (the published shape) | yes — test_setup_state.py (2) + sf-static-gate | — |
| I, initialized instance | require the token on initialized instances too | yes — functional/test_initialized.py (3) + ff-refuse-all | — |
| U, public readability | gate `/api/settings/public` | yes — functional/test_first_run.py::test_public_settings_stays_public | — |
| P, "must leave unchanged" | create/restore and only then refuse | yes — `assert_no_takeover` (admin/check + login) in every security test; notes record sf-after-create failing 4 | — |
| T, exact comparison | case-insensitive, trimmed, or prefix comparison | **no** — only `wrong-token` and `wrong-token,wrong-token-2` are sent | add a near-miss test: `SETUP_TOKEN.upper()`, `" "+SETUP_TOKEN`, and `SETUP_TOKEN+"x"` must all be refused |
| T5, explicit role | gate only the omitted-`Role` branch; `{"Role":1}` with no token still creates an operator | **no** — security tests only use an omitted Role | add a security case with explicit `Role: 1` and no/wrong token |
| channel | exempt loopback / localhost requests | **no** — the whole harness is loopback | add a test through a non-loopback bind or drop the exemption clause from any future prose |
| configuration | add a `--no-setup-token` / `PORTAINER_NO_SETUP_TOKEN` disable switch | **no** — never set by any test | either test that the switch is off by default (it is) or state that no disable switch is authorised; a default-off switch passes today |
| "leave unchanged" | return 4xx but write part of the archive that does not create an admin | **no** — `assert_no_takeover` only detects an admin/login | add a check that a marker in the data directory is unchanged after refusal |

Wrong fixes no test catches: **explicit-Role automation import**, **near-miss token comparison**,
**loopback exemption**, **an explicit disable switch**, **partial state replacement without an
admin**.

## 3. Hints (QUALITY — non-blocking)

Quoted sentences and neutral rewording:

1. "With no token pinned on a fresh instance the server must still require a token that it generates
   itself; the requirement must not be disabled just because no value was configured." — names the
   generation mechanism (the T4 fix approach). Neutral: "The requirement must apply even when no
   token has been configured."
2. "This applies to the instance's state at the moment of the request, whatever state it started
   in." — the trailing clause paraphrases T6. Neutral: "This applies to the instance's state at the
   moment of the request."
3. "A request that does not present the token, presents a wrong one, or presents no usable value at
   all must be refused..." — a test-shaped variant list. Neutral: "A request that does not prove
   knowledge of the token must be refused with a client error and must leave the instance
   unchanged."
4. "Comparison is exact: only the configured or generated token is accepted." — names the
   comparison mechanism. Neutral: "Only the token the instance currently expects is accepted."
5. "This holds however the operator account came to exist." — points at the `--admin-password`
   variant. Delete; the general initialized-instance sentence already covers every origin.

Not a hint (keep): the `X-Setup-Token` / `PORTAINER_SETUP_TOKEN` names are the black-box interface
contract; without them the tests are not derivable.

## 3a. Required: generalize

- "until its first operator completes setup" → "until the first operator account exists" (`setup`
  is the name of one stage).
- "whatever state it started in" → "at the moment of the request" (the startup stage).
- "The client caused the instance to start with persistent state of the client's choosing and then
  signed in as its operator." → "The client obtained operator authority and replaced the
  instance's persistent state." (removes the restore/start/sign-in operation sequence).
- "including the existing 'already initialized' refusals. This holds however the operator account
  came to exist." → "including the existing refusals." (drops the origin variant).
- "A freshly deployed instance has no operator account until its first operator completes setup,
  and until then it is reachable without credentials." → "A freshly deployed instance has no
  operator account until one is created, and until then requests are unauthenticated." (same
  premise, no stage name, no channel description).

## 4. Realism (QUALITY — non-blocking)

- T0 (`restore.go`), T1 (`admin_init.go`), T4 (startup token producer) and T6 (run-time demotion)
  are real upstream code paths; T6 is confirmed reachable through the real entry point.
- T2 (`restore_local.go`) is a plausible air-gapped recovery handler that copies the existing
  restore policy; reachable through the registered route. Not flagged.
- T3 (`admin_init_legacy.go` plus the `/api/admin` prefix alias) is a plausible deprecated
  bootstrap alias, but duplicating the whole creation path rather than delegating is slightly
  convenient. Borderline, not planted.
- T5 (`users_automation_import.go`) is the weakest: an unattended provisioning profile whose first
  entry *without* a `Role` silently becomes the operator is an unusual default, and the
  setup-or-authenticated subrouter exists to carry the lever. It is still reachable through the
  real entry point and uses the real user model; flag as borderline, not contrived enough to
  remove.
- No real upstream route is flagged as "beyond the advisory" or out of scope; leaving one open is
  the solver's failure, not a task defect.

## 5. Verdict

**Gate a — UNFAIRNESS: READY.** Every security test is covered by the general property (P/R/T/M),
read literally at the route it drives; the sibling tests need no route-naming sentence. The refusal
form is any 4xx and the guard layer is free (handler, dispatcher, middleware). The functional tests
assert exactly the behaviour the instruction says must keep working. A correct fix following the
primary mechanism — resolve the pinned or generated token at startup, compare the header exactly,
decide "no operator account" at request time — passes all 14 security, 11 feature and 40 project
test cases, as the oracle, pass-blind and pass-hardening patches do.

Residual (not gate a under the primary-mechanism rule): the pristine project unit test constructs a
handler with no token. A handler guard that explicitly refuses an *empty expected token*, or a
change to `NewHandler`'s arity, would fail it even though the running server is correct. The
natural generate-at-startup + direct-compare fix is unaffected.

### Quality to tighten

- Add the near-miss token tests (case, whitespace, prefix) and an explicit-`Role: 1` import case
  with no token.
- Add a non-loopback or no-loopback-exemption assertion; do not let a localhost exemption pass.
- Exercise (or explicitly reject) an operator disable switch; state in the instruction that no
  disable switch is authorised.
- Add a marker check that a refused restore leaves the data directory byte-identical, not merely
  admin-free.
- Neutralize the hint sentences 1–5 above; apply the 3a rewording.

Human review: confirm that a handler guard which refuses an empty expected setup token (the literal
reading of "must not be disabled just because no value was configured") is acceptable given the
pristine project unit test that builds a handler with no token; also confirm that changing
`NewHandler`'s signature is not a required-fix path.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
