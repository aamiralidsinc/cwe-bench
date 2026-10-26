# new-api-ds — build notes

- Start UTC: 2026-10-18T19:33:36Z (build-run start; this session)
- End UTC: see end of file
- Slug: new-api-ds. Candidate: screener-v2 entry 16277, GHSA-6X2C-PHFF-WX57 / CVE-2026-64859 / GO-2026-6240.
- Pinned (vulnerable) commit: 5dd0d3bcbd7b1d523bd046a5f9cf9fc8ce28d579 = direct parent of the published fix 0936e2504655a5cbf7bc3c388f6d3e2bb24916d3.
- Track: injected. Pattern: B.

## Design (written before the build)

Base flaw (published fix, A): the shared user model serializes its management
token (`json:"access_token"`), so every admin route that returns a user record
discloses the token; and the passkey-reset admin action lacks the role-hierarchy
guard that its neighbouring admin actions have.

Levers (one line each), all reachable over the real HTTP router with header auth:
- T1 A landing/serializer: management token in the admin user list — model/user.go:39 (json tag) via controller/user.go:236.
- T2 A far routes: same token in admin search and admin detail — controller/user.go:251, :273. Reason to dismiss: the report shows the list view; these are other handlers (a handler-level fix misses them).
- T3 B uncovered route (real upstream, unchanged, still in main): notification secrets (signing secret, push token, push URL with device key) in the same list/search/detail records — model/user.go:51 + dto/user_settings.go. Reason to dismiss: notification configuration, not a login credential.
- T4 A published far site: passkey reset admin action has no role-hierarchy check — controller/passkey.go:341. Reason to dismiss: the report is about a listing leak, not passkey management.
- T5 injected sibling: admin user export builds its own row type copying the token and the raw settings blob — controller/user.go (new ExportUsers) + route. Reason to dismiss: separate admin export feature; admins are trusted.
- T6 injected sibling: admin support route returns a target account's management token with no hierarchy check — controller/user.go (new AdminGetUserAccessToken) + route. Reason to dismiss: a dedicated admin-only route is intentional support tooling.
- T7 injected sibling: admin force-logout (revokes a target's management token) has no hierarchy check — controller/user.go (new AdminForceLogoutUser) + route. Reason to dismiss: a protective/session action is harmless regardless of the target's rank.

Coupled must-keep-working behaviour (functional tests): owner sees their own notification
settings; token generation still returns the new token to its owner; header auth keeps
working; admins keep seeing non-secret user fields; an admin can still reset a
lower-role user's passkey; root can act on anyone; the existing 2FA admin guard keeps
its meaning; export still lists users; a caller can view their own token; an admin can
force a lower-role user's logout; user update via the admin API still works.

Coverage: list, search, detail, export (input shapes: full list, single record, bulk
rows); every refusal asserts failed response (success:false or 4xx, never 5xx) plus no
side effect.

## Verified (to fill)
- Pinned 5dd0d3bc is the direct parent of fix 0936e250; `git diff` between them touches no test file.
- The published fix is an omnibus commit (log formatting everywhere + the security changes). The oracle
  takes only the security-relevant source hunks: the model serialization tag, the shared role-hierarchy
  helper and its refactors, and the passkey guard. Logging hunks are deliberately excluded.
- The B route is real at the pinned commit and still present in current main (origin/main keeps the
  raw settings blob on the account record and returns full records from the listing/search/detail
  handlers). Verified read-only from the local clone of origin/main.
- All 7 levers reproduce over the real gin router with header authentication: on the pinned+injected
  tree, nop is security 0/12 and functional 66/66.
- Oracle is security 12/12 and functional 66/66, reward 1.0, in the task image with --network none.
- 16 checks patches: 11 security_fail, 3 functional_fail, 2 pass (hardening + alternative). Each was
  run on the injected tree first (locally) and behaves as declared.
- The project's own controller/model tests (52 after skipping the two external-database migration
  tests, which `go test -skip` excludes because they would otherwise be counted as failed skips) pass
  on nop and oracle.
- The image installs the Go module cache at build time; grading runs with GOPROXY=off.

## Fairness
Every property is stated in instruction.md in user-level terms and every lever is reachable from the
code a blind engineer reads: the shared account record fields, the administrator handlers that return
them, and the administrator actions that load a target account. The contract explicitly keeps
non-credential fields, the owner's own credentials, root's reach and the lower-role operations
working, so over-broad fixes fail the functional group. The instruction names no file, field,
function, route list or advisory id, and does not mention any injected mechanism.

## Could not verify / notes
- Whether the web console shows the management token anywhere was not traced (the bundled frontend
  sources in this commit do not reference it); the direct API contract is what the tests use.
- The register's public_upstream_report is `unknown`: no public report was found for the settings
  blob disclosure; current main still serializes it.
- Out of scope (one line): the subscription administrator routes also lack role-hierarchy checks at
  the pinned commit, but they are billing operations outside this advisory's credential protection
  and were not used.
- Out of scope (one line): the commit also reroutes debug logging through lazy formatting; that is
  log hygiene, not the advisory's protection.
- blind.patch and FAIRNESS.md intentionally absent (written by the downstream step).

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

Instruction/metadata-only upgrade; no repo code, tests, solution, checks or environment change and
the prebuilt image was reused (no rebuild).

- Instruction: replaced the route-by-route report (the `GET /api/user/` example, the
  list/search/inspect/manage enumeration, and the webhook-secret/push-token/push-URL field list)
  with a single property stated over the protected outcome: an account's credential material may
  be returned only to that account in any administrator response that describes accounts, and
  another account's sign-in credentials or protections may be changed or revoked only by an
  outranking administrator. The coupled contracts remain, stated generally (refusal form, owner
  still sees own notification credentials and newly issued token, token auth works, non-credential
  fields preserved, lower-ranked actions still work, root reaches everyone). No route, operation,
  channel, object kind, format, file, function or count is named.
- Lever check: the task already has how-type levers, so none was added. T1 is M6 (shared model
  serializer produces the credential; the handler-level check never calls it). T3 is M4 + M8 (real
  route where the protection never existed; the credentials sit in a nested serialized blob, so a
  field-level redaction of the account record misses them). T4 is M4 (published route where the
  protection never existed). T2/T5/T6/T7 are where-type extras.
- Coverage: unchanged. Every route the general property covers that is vulnerable at the pinned
  tree already has a behavioural security test through the real router: list, search, single
  record and export for management tokens and notification credentials; the owner-only token view;
  and both hierarchy actions (peer and higher-ranked targets, with no-side-effect assertions).
  Already-protected actions (2FA, OAuth bindings, update/manage/delete) stay covered by the
  project's own functional tests. No test was weakened; no new security_fail patch was needed
  because no lever was added.
- manifest.json: `leak_terms` extended with the route/operation/field-kind words the rewrite
  forbids (listing, search, detail, token view, GET /api/user, route, endpoint, webhook, gotify,
  bark, signing secret, device key); each trap gained a `lever_type` annotation. `patch_checks`
  unchanged (11 security_fail, 3 functional_fail, 2 pass).

## Harden 2026-10-21 (hardening + Frontier delivery format)

Pre-verdict: CAN harden. Both models solved the 7-lever task, but the pinned code supports
three further fair levers that reach the same stated rules from different mechanisms.

New levers (each has a security test through the real gin router and a coupled functional test):
- T8 (HOW, different credential type): administrator support view lists a target account's relay
  API keys in full. Uses the project's real `model.GetAllUserTokens`; the shared account-record
  fix cannot reach `model.Token`. Reason to dismiss: API keys are a separate object, not the
  management token the report describes. Fix: mask the keys; non-secret metadata stays.
- T9 (HOW, second serializer / producer off the check's path): administrator support view returns
  the project's real cached `UserBase` projection, whose raw settings blob still carries the
  notification credentials. The account-record redaction and the `json` tag never touch it.
  Reason to dismiss: the cached base view looks already sanitised. Fix: redact its settings blob.
- T10 (action, additive): administrator sign-in binding creation has no role-hierarchy check and
  is built on the project's real `model.CreateUserOAuthBinding`. Reason to dismiss: adding an
  identity is additive, unlike a reset or revocation. Fix: the same outrank check as the other
  account actions; lower-ranked and root-on-root creation keep working.

Instruction: extended the action rule to "created, changed or revoked" (so creating a sign-in
credential is unambiguously covered) and generalised the preservation clause to "every
non-credential field"; dropped "do not modify or add tests"; added "There is no network access."
No route, file, function, field, count or mechanism is named; leak_terms extended.

Delivery format: task.toml schema 1.4 (artifacts /workspace, separate+no-network verifier, uid-1000
agent, B7 metadata, fresh canary GUID), environment/Dockerfile builds at /workspace with an
agent-owned Go module/build cache, new tests/Dockerfile warms the same cache, tests/test.sh is the
non-root separate-mode scaffold (two groups, JUnit, project tests copied pristine), score.py is the
template. solve.sh applies fix.patch in /workspace.

Checks: 20 patches (14 security_fail, 3 functional_fail, 3 pass incl. hardening, alternative and a
new independently written blind fix). All were applied to the pinned+injected tree locally and
behaved as declared; pinned security 0/16, oracle security 16/16, functional green on both.

## Harden verification (2026-10-21)

- Conformance: `python3 -I builder/conformance_check.py tasks/new-api-ds` prints "conforming".
- `gate.py --only static`: PASS. `--only nop`: PASS (security 0/16, functional 70/70,
  reward 0.0). `--only oracle`: PASS (3/3 runs reward 1.0; security 16/16, functional 70/70).
- `gate.py --only patches`: 20 checks exercised. The first attempt completed several variants
  and then hit Harbor's egress-control probe flake (`network_mode='no-network' is not supported
  by EnvironmentType.DOCKER` under a 26-32 host load average), which the gate classifies as
  infra, not task; retried without weakening task.toml. Every checks patch had also been applied
  to the injected tree locally and behaved as declared (14 security_fail, 3 functional_fail,
  3 pass including hardening/alternative/blind).
- Independent read-only fairness review of the three new levers: no problems. Each lever is
  covered by the instruction's general property; no test demands an exact refusal status or a
  particular implementation layer; removing the credential field is accepted; lower-role reads
  and writes are required to keep working per the stated contracts; no leak terms.
