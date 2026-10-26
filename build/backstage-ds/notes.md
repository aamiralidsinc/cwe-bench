# backstage-ds — build notes

- Start (UTC): 2026-10-18T20:01Z
- Advisory: GHSA-29GX-H2M3-XW44 / CVE-2026-106462 (backstage/backstage)
- Pinned: 29330a97934f04b5ea4ce8f8219903f1f22402ff (verified parent of published fix
  6fb2a41ea47da37eafe5ea744050ef90be6820c0, "fix: require user credentials for SCM actions")
- Track: injected. Pattern: A.

## Scope

The full monorepo is in `/app` at the pinned commit. The task's protection covers the GitHub
module, the GitLab module and the four built-in template fetch actions. The Bitbucket
Cloud/Server, Azure, Gitea, Gerrit, cookiecutter and rails modules are present in the tree but
are outside this task's protection and are not tested (noted in the report as out of scope).

The published fix adds an opt-in root-config setting `scaffolder.requireScmUserCredentials`
(default false). When enabled, a scaffolder SCM operation must be performed only with a
user-supplied token; the backend integration credential must not be used, and operations that
inherently need the integration identity must be refused.

## Levers (one line each)

- T1 (A, report-led): every GitHub action's credential choice goes through the shared
  `getOctokitOptions` fallback. Dismiss: none, landing point.
  `plugins/scaffolder-backend-module-github/src/util.ts:188`.
- T2 (A, wrapper): the pull-request action builds its client through an injectable client
  factory, outside the shared helper. Dismiss: "the helper is fixed".
  `plugins/scaffolder-backend-module-github/src/actions/githubPullRequest.ts:309`.
- T3 (A, second implementation): the whole GitLab module (getToken, getClient, createGitlabApi
  and an inline publish client) plus the privileged ownership assignment. Dismiss: "the report
  is about GitHub". `plugins/scaffolder-backend-module-gitlab/src/util.ts:95`.
- T4 (A, separate package, separate credential path): the four built-in fetch actions read SCM
  content through the URL reader. Dismiss: "read-only template fetchers, not publish actions".
  `plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/plain.ts:78`.
- T5 (producer): the setting is read from root config in each module/plugin init; tests enable it
  only through the config. Dismiss: "checked in the actions, forgot the wiring".
  `plugins/scaffolder-backend-module-github/src/module.ts:60`.
- S1 (injected): GitHub release action resolves its own credential from the credentials provider.
  Dismiss: "every GitHub action goes through the shared helper".
  `plugins/scaffolder-backend-module-github/src/actions/githubRelease.ts:119`.
- S2 (injected): GitLab project-member action builds its client inline with the same
  token-or-integration fallback. Dismiss: "all GitLab actions go through the shared helpers".
  `plugins/scaffolder-backend-module-gitlab/src/actions/gitlabProjectMemberCreate.ts:83`.

## Coupled must-keep-working behaviour

- Setting off/absent: the integration fallback works for GitHub, GitLab and the fetch actions.
- Setting on with a user token: the same actions use the user's token.
- Setting on without a user-token concept: plain HTTPS, Bitbucket Server and relative file://
  template paths still fetch.
- The project's own tests for the affected packages keep passing (github/gitlab util tests and
  the fetch plain/template tests).

## What was verified

- The pinned tree is the parent of the published fix (git log between the two commits shows the
  fix and its regression tests only in the fix commit).
- The injected actions are reachable through the real module init and fall back to the
  integration credential at the pinned commit.
- At the pinned commit every security test fails and every functional test passes
  (security 0/34, functional 74/74).
- With `solution/fix.patch` applied: security 34/34, functional 74/74, reward 1.0.
- Every check patch behaves as declared (see manifest.patch_checks).
- Both patches apply cleanly with `patch -p1` to a fresh pinned checkout.
- Grading is offline: dependencies are installed at image build time and the tests use mocked
  SCM clients and a fake URL reader; no network calls are made at test time.
- The project's own tests for the affected area pass in both states.
- No security test asserts an exact HTTP status; refusals are asserted as `InputError`.

## What could not be verified

- No pre-trial model runs were made by design (the builder does not run target models).
- Bitbucket Cloud/Server, Azure and the other scaffolder modules were not exercised; they are
  outside the task's declared scope.
- The published fix also threads the setting into the GitHub/GitLab autocomplete handlers and
  leaves `gitlab:user:info` on the fallback in current upstream; those routes are not part of
  this task's protection (pattern A scope), and the oracle leaves them as upstream does.

## Status

See the final line of the report and build/backstage-ds/gate_report.json.

## Fairness revision (2026-10-19)

Applied the pre-trial FAIRNESS.md requirements:

- Added a fetch security case that starts the real `scaffolderPlugin` (real
  `init.func`, with the router/actions registration mocked) so the four fetch
  wiring arguments are covered; added `checks/sf-miss-T5b.patch` for that gap.
- Added a GitLab-hosted fetch security case, empty-token cases for
  `github:issues:create` and `gitlab:issues:create`, functional non-SCM cases for
  `fetch:template`, `fetch:plain:file` and `fetch:template:file`, and
  default/user-token cases for `github:webhook` and `gitlab:repo:push`.
- GitLab user-token functional tests now assert the integration token field is
  absent; the project fetch template test uses a real integrations registry and
  base URL.
- Instruction: removed the ownership-input enumeration, the file/mechanism-level
  startup-wiring wording and the exact non-SCM location list; added the
  no-client-construction and relative-base clarification, the scope statement for
  the GitHub/GitLab modules and fetch actions, and explicitly excluded the two
  GitLab steps the reference leaves unchanged (`gitlab:user:info`,
  `gitlab:group:migrate`).

## Fairness revision, round 2 (2026-10-19, FAIRNESS.md F1-F7)

- F1: instruction now requires that no SCM client be constructed at all when the
  step refuses (keeps the strong zero-construction assertion fair).
- F2: instruction scopes the guard to GitHub and GitLab locations; other SCM
  hosts (e.g. Bitbucket Server) keep existing behaviour including a configured
  integration credential.
- F3: GitLab user-token functional cases assert behaviourally that the user
  token reaches the client and the integration token reaches neither credential
  field, instead of hard-coding `oauthToken`/`token`.
- F4: added `token: ''` security cases for `publish:github:pull-request` and
  `github:release:create`; `sf-empty-token.patch` now fails 6 security tests.
- F5: added setting-on security cases with a tokenless integration entry for
  `github:issues:create` and `fetch:plain`, so a guard conditioned on a
  configured integration token cannot pass.
- F6: dropped the "credential helper" hint, the publishes/reads hint, and the
  named out-of-scope step list; the startup requirement is now generic.
- F7: softened the unobserved side-effect sentence to the asserted
  no-SCM-request/no-client-construction contract.
- Follow-up alignment: the non-SCM exemption now names plain HTTP(S) locations
  with no GitHub/GitLab integration and local files (a tokenless GitHub
  integration is still in scope, matching F5 and the oracle), and the factory
  contract notes that the checks call the affected action factories directly.
- Manifest trap descriptions record the added F4/F5 cases.


## Sibling-injection upgrade (2026-10-20)

Rules applied: BETTER-PATTERNS §2–§8.

- Instruction: replaced the route/mechanism checklist (SCM host names, relative-base rule,
  read/write enumeration, privileged-input names) with one general invariant over the protected
  outcome — when the setting is enabled no supported step may use the instance integration
  credential, only a non-empty credential supplied through the step's own input, however the
  target is expressed; operations inherently needing the instance identity are refused. The
  must-keep-working clauses (setting off, user token accepted, integrations without a per-user
  credential, non-SCM targets) are stated generally. Test contracts (config key, `token` field,
  factory option, `InputError`) are retained once.
- Levers: T5 (config producer wired through startup) and the relative-target classification were
  already how-type. Added two M4 how-type routes the published fix left open:
  T6 `gitlab:user:info` and T7 `gitlab:group:migrate`.
- Coverage: one behavioural security case each (through the real module init, mocked
  `@gitbeaker/rest`, expected zero client constructions + `InputError`), wired as `sf-miss-T6` /
  `sf-miss-T7` security_fail checks. The oracle now threads the option into both actions.
  `pass-alt` and `pass-hardening` were extended to close the new routes so they still score 1.0.
- No repo (environment) change: the pinned tree is untouched, so the prebuilt image is reused.
- Static: clean except the separately wired `blind.patch` (allowed).
