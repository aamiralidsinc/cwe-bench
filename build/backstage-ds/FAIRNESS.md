# Fairness and leniency review — backstage-ds

Inputs read: `instruction.md`, every file under `tests/`, `solution/fix.patch`,
`build/backstage-ds/manifest.json`, `notes.md`, all `checks/*.patch`, and (context)
`environment/injection.patch`, `focus.txt`. Nothing was run; no upstream fix was consulted. The
solver sees only `instruction.md` and the repository.

Basis labels:

- **G1** — "While it is enabled, no supported scaffolder step may perform any source-control
  operation, however its target is expressed or referenced, using the instance's configured
  integration credential. A step may proceed only with a non-empty credential supplied through its
  own step input."
- **G2** — "Without one it must fail with a client error before making any source-control request
  and without constructing a client for the target host."
- **G3** — "The same applies to an operation that inherently requires the instance's own identity:
  it must be refused with a client error even when the user supplied a credential."
- **G4** — "An empty-string credential is treated as no credential."
- **G5** — "Integrations that have no concept of a per-user credential keep their existing
  behaviour, including their use of a configured integration credential."
- **G6** — "Everything that is not a source-control operation keeps working without a user
  credential."
- **G7** — "Enabling the setting in the instance configuration must be sufficient at startup; no
  per-step option may be required from the template author."
- **G8** — "While the setting is absent or false, behaviour must be exactly as today: the
  integration-credential fallback remains available to every step, and every step keeps working as
  it does now."
- **C1** key `scaffolder.requireScmUserCredentials`; **C2** credential input `token`; **C3**
  factory option `requireScmUserCredentials`; **C4** refusal is `InputError`, not a crash.
- **E** standard expert knowledge: do not regress the repository's existing unchanged tests;
  Backstage URL readers take a per-request user token only for the integrations that define one
  (GitHub/GitLab), so other integrations are the G5 class.

## 1. Per-test fairness table

Security rows load the action through the real module init (or the public fetch factory), invoke
the real handler with a mock context, and require the mocked SCM client constructor not to be
called. A guard in the handler, the shared helper, or the client factory all pass; only a guard
that fires after client construction fails.

### 1.1 `tests/security/github_security.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `github_security.test.ts::publish:github refuses without a user token and never creates an authenticated client` | no `Octokit`; `InputError` | G1, G2, C4 | no | low |
| `::github:repo:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:repo:push refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:actions:dispatch refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:autolinks:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:branch-protection:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:deployKey:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:environment:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no — guard before catalog/client use passes | low |
| `::github:issues:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:issues:label refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:pages:enable refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::github:webhook refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::publish:github:pull-request refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; injectable factory route | G1, G2 | no — action-level or default-factory guard passes | low |
| `::github:release:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; action resolves credentials itself | G1, G2 | no | low |
| `::publish:github treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::github:issues:create treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::publish:github:pull-request treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::github:release:create treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::github:issues:create refuses when the integration entry has no token` | factory called directly with the option; a provider could return a fallback token; no ctor; `InputError` | G1, G2, C3 | no — setting alone forbids; do not condition on a configured integration token | low |

### 1.2 `tests/security/gitlab_security.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `gitlab_security.test.ts::publish:gitlab refuses without a user token and never creates an authenticated client` | no `Gitlab`; `InputError` | G1, G2, C4 | no | low |
| `::gitlab:group:ensureExists refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:group:access refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:issues:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; shared `getClient` | G1, G2 | no | low |
| `::gitlab:issue:edit refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:pipeline:trigger refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:projectAccessToken:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; shared `getToken` | G1, G2 | no | low |
| `::gitlab:projectDeployToken:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:projectVariable:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::publish:gitlab:merge-request refuses without a user token and never creates an authenticated client` | no ctor; `InputError` | G1, G2 | no | low |
| `::gitlab:repo:push refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; `createGitlabApi` | G1, G2 | no | low |
| `::gitlab:projectMember:create refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; inline client | G1, G2 | no | low |
| `::gitlab:user:info refuses without a user token and never creates an authenticated client` | no ctor; `InputError`; shared helper | G1, G2 | no — the route is a literal SCM operation covered by the general property | low |
| `::gitlab:group:migrate refuses without a user token and never creates an authenticated client` | `destinationAccessToken:''`; no ctor; `InputError` | G1, G2, G4 | no — the destination operation would use the integration credential; a guard on the destination credential passes, a handler check of "any non-empty input" is not correct | low |
| `::publish:gitlab treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::gitlab:issues:create treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::gitlab:projectAccessToken:create treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::gitlab:repo:push treats an empty user token as no user token` | `token:''`; no ctor; `InputError` | G4 | no | low |
| `::publish:gitlab refuses the privileged ownership assignment with a user token` | `setUserAsOwner:true` and `ownerUsername` both refuse with a real token; no ctor; `InputError` | G3, C4 | no — both inputs resolve the user via the integration identity in the visible code | low |

### 1.3 `tests/security/fetch_security.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `fetch_security.test.ts::fetch:plain refuses an absolute GitHub URL without a user token` | factory called with the option; no `readTree`; `InputError` | G1, C3 | no | low |
| `::fetch:plain refuses a relative URL resolved against a GitHub template location` | `./skeleton` + GitHub base; no `readTree`; `InputError` | G1 ("however its target is expressed or referenced") | no | low |
| `::fetch:plain refuses an absolute GitLab URL without a user token` | no `readTree`; `InputError` | G1 | no | low |
| `::fetch:plain refuses a GitHub URL when the integration entry has no token` | GitHub integration with no token; no `readTree`; `InputError` | G1, G2 | no — do not condition on a configured token | low |
| `::fetch:plain:file refuses without a user token` | no `readUrl`; `InputError` | G1, G2 | no | low |
| `::fetch:template refuses without a user token` | no `readTree`; `InputError` | G1, G2 | no | low |
| `::fetch:template:file refuses without a user token` | no `readUrl`; `InputError` | G1, G2 | no | low |
| `::fetch:plain registered through the plugin startup refuses GitHub content without a user token` | real plugin init reads config; no `readTree`; `InputError` | G7 | no | low |
| `::fetch:plain:file registered through the plugin startup refuses GitHub content without a user token` | same | G7 | no | low |
| `::fetch:template registered through the plugin startup refuses GitHub content without a user token` | same | G7 | no | low |
| `::fetch:template:file registered through the plugin startup refuses GitHub content without a user token` | same | G7 | no | low |

### 1.4 `tests/functional/github_functional.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `github_functional.test.ts::uses the integration credential by default when no user token is given` | setting absent; `auth` = integration token (`github:issues:create`) | G8 | no | low |
| `::uses the user token when one is given and the setting is enabled` | setting on; `auth` = `user-token` | G1, C2 | no | low |
| `::keeps the integration fallback for the release action by default` | setting absent; release falls back | G8 | no | low |
| `::uses the user token for the release action when the setting is enabled` | setting on; `auth` = `user-token` | G1 | no | low |
| `::keeps the integration fallback for the webhook action by default` | setting absent; integration token | G8 | no | low |
| `::uses the user token for the webhook action when the setting is enabled` | setting on; user token | G1 | no | low |

### 1.5 `tests/functional/gitlab_functional.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `gitlab_functional.test.ts::uses the integration credential by default when no user token is given` | setting absent; `token` field = integration token | G8 | no | low |
| `::uses the user token when one is given and the setting is enabled` | setting on; `oauthToken ?? token` is the user token and neither field is the integration token | G1, C2 | no — either credential field is accepted | low |
| `::keeps the integration fallback for the project member action by default` | setting absent; inline client uses integration token | G8 | no | low |
| `::uses the user token for the project member action when the setting is enabled` | setting on; user-token-only assertion | G1 | no | low |
| `::keeps the integration fallback for the repo push action by default` | setting absent; integration token | G8 | no | low |
| `::uses the user token for the repo push action when the setting is enabled` | setting on; user-token-only assertion | G1 | no | low |

### 1.6 `tests/functional/fetch_functional.test.ts`

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `fetch_functional.test.ts::reads a plain HTTPS location with the setting enabled` | plain host; `readTree` called | G6 | no | low |
| `::reads a Bitbucket Server location with the setting enabled` | Bitbucket Server integration with a configured token; `readTree` called without a user token | G5 | no — that integration has no per-user credential; the class must be derived from the repo (medium) | medium |
| `::reads GitHub content with a user token when the setting is enabled` | `readTree` called with exactly `{token:'user-token'}` | G1, C2 | no — existing plumbing unchanged | low |
| `::keeps the integration fallback in the default configuration` | setting absent; `readTree` called | G8 | no | low |
| `::copies a relative local template path with the setting enabled` | `file://` base; no `readTree`; local copy | G6 | no | low |
| `::fetch:template reads a plain HTTPS location with the setting enabled` | `readTree` called | G6 | no | low |
| `::fetch:template reads a Bitbucket Server location with the setting enabled` | Bitbucket Server; `readTree` called | G5 | no — same judgment as above | medium |
| `::fetch:template copies a relative local template path with the setting enabled` | `file://`; no `readTree` | G6 | no | low |
| `::fetch:plain:file reads a plain HTTPS location with the setting enabled` | `readUrl` called | G6 | no | low |
| `::fetch:plain:file copies a relative local file with the setting enabled` | `file://`; no `readUrl` | G6 | no | low |
| `::fetch:template:file reads a plain HTTPS location with the setting enabled` | `readUrl` called | G6 | no | low |
| `::fetch:template:file copies a relative local file with the setting enabled` | `file://`; no `readUrl` | G6 | no | low |

### 1.7 Project tests (pristine upstream copies)

Basis for every row: G8 + E (factories constructed with no option, so the guard must no-op; the
helpers tested are untouched).

| test (file::name) | what it asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `project/github/util.test.ts::isRetryEnabled returns false when retries is == 0` | retry parsing | G8, E | no | low |
| `::isRetryEnabled returns false when retries is <= 0` | retry parsing | G8, E | no | low |
| `::isRetryEnabled returns false when retryAfter is == 0` | retry parsing | G8, E | no | low |
| `::isRetryEnabled returns false when retryAfter is <= 0` | retry parsing | G8, E | no | low |
| `::isRetryEnabled returns true when retryOptions is undefined` | retry parsing | G8, E | no | low |
| `::isRetryEnabled returns true when retries is > 0 and retryAfter is > 0` | retry parsing | G8, E | no | low |
| `::getOctokitClient returns a plain Octokit client when retries is 0` | no retry plugin | G8, E | no | low |
| `::getOctokitClient returns a plain Octokit client when retryAfter is 0` | no retry plugin | G8, E | no | low |
| `::getOctokitClient returns a retry-enabled Octokit client with default retries and delay when retryOptions is undefined` | retry defaults | G8, E | no | low |
| `::getOctokitClient returns a retry-enabled Octokit client with custom retries and delay` | custom retry | G8, E | no | low |
| `::getOctokitClient merges existing request options when building retry client` | merge semantics | G8, E | no | low |
| `project/gitlab/util.test.ts::getTopLevelParentGroup should return the top-level parent group if the input group has a parent in the hierarchy` | hierarchy walk | G8, E | no | low |
| `::getTopLevelParentGroup should return the input group if it has no parents in the hierarchy` | top of hierarchy | G8, E | no | low |
| `::checkEpicScope should return true if the project is inside the epic scope` | epic scope | G8, E | no | low |
| `::checkEpicScope should return false if the project is not inside the epic scope` | epic scope | G8, E | no | low |
| `::checkEpicScope should throw an InputError if the project is not found` | `InputError` | G8, E | no | low |
| `::checkEpicScope should throw an InputError if the top-level parent group is not found` | `InputError` | G8, E | no | low |
| `::checkEpicScope should throw an InputError if the epic is not found` | `InputError` | G8, E | no | low |
| `::convertDate should convert a valid input date with milliseconds to an ISO string` | date format | G8, E | no | low |
| `::convertDate should convert a valid input date to an ISO string` | date format | G8, E | no | low |
| `::convertDate should use default date if input date is undefined` | default | G8, E | no | low |
| `::convertDate should throw an InputError if input date is invalid` | `InputError` | G8, E | no | low |
| `project/fetch/plain.test.ts::should disallow a target path outside working directory` | path containment | G8, E | no | low |
| `::should fetch plain` | `fetchContents` args | G8, E | no — option absent; guard no-ops | low |
| `::should fetch plain with token` | `fetchContents` args with token | G8, E | no | low |
| `project/fetch/template.test.ts::returns a TemplateAction with the id 'fetch:template'` | action id | G8, E | no | low |
| `::handler throws if output directory is outside the workspace` | containment | G8, E | no | low |
| `::handler throws if cookiecutterCompat is used with extension` | incompatible options | G8, E | no | low |
| `::handler with optional directories / files skips empty filename` | optional dirs | G8, E | no | low |
| `::handler with optional directories / files skips empty filename syntax #2` | optional dirs | G8, E | no | low |
| `::handler with optional directories / files skips empty directory` | optional dirs | G8, E | no | low |
| `::handler with optional directories / files skips empty filename inside directory` | optional dirs | G8, E | no | low |
| `::handler with optional directories / files skips content of empty subdirectory` | optional dirs | G8, E | no | low |
| `::handler with valid input uses fetchContents to retrieve the template content` | fetch args | G8, E | no | low |
| `::handler with valid input copies files with no templating in names or content successfully` | copy | G8, E | no | low |
| `::handler with valid input copies files with templated names successfully` | templated names | G8, E | no | low |
| `::handler with valid input copies files with templated content successfully` | templated content | G8, E | no | low |
| `::handler with valid input processes dotfiles` | dotfiles | G8, E | no | low |
| `::handler with valid input copies empty directories` | empty dirs | G8, E | no | low |
| `::handler with valid input copies binary files as-is without processing them` | binary | G8, E | no | low |
| `::handler with valid input copies files and maintains the original file permissions` | mode | G8, E | no | low |
| `::handler with valid input copies file symlinks as-is without processing them` | symlink | G8, E | no | low |
| `::handler with valid input copies broken symlinks as-is without processing them` | broken symlink | G8, E | no | low |
| `::handler with valid input passed through the token to the fetchContents call` | token passthrough | G8, E | no | low |
| `::copyWithoutTemplating renders path template and ignores content template in files matched in copyWithoutTemplating` | selective render | G8, E | no | low |
| `::copyWithoutTemplating processes files not matched in copyWithoutTemplating` | selective render | G8, E | no | low |
| `::copyWithoutTemplating with exclusion filter renders path template including excluded matches in copyWithoutTemplating` | exclusion | G8, E | no | low |
| `::cookiecutter compatibility mode copies files with cookiecutter-style templated names successfully` | names | G8, E | no | low |
| `::cookiecutter compatibility mode copies files with cookiecutter-style templated content successfully` | content | G8, E | no | low |
| `::cookiecutter compatibility mode includes the jsonify filter` | filter | G8, E | no | low |
| `::with extension=true copies files with no templating in names or content successfully` | extension copy | G8, E | no | low |
| `::with extension=true copies files with templated names successfully` | extension names | G8, E | no | low |
| `::with extension=true copies jinja2 files with templated names successfully` | extension names | G8, E | no | low |
| `::with extension=true copies files with templated content successfully` | extension content | G8, E | no | low |
| `::with extension=true processes dotfiles` | extension dotfiles | G8, E | no | low |
| `::with extension=true copies empty directories` | extension dirs | G8, E | no | low |
| `::with extension=true copies binary files as-is without processing them` | extension binary | G8, E | no | low |
| `::with specified .jinja2 extension does not process .njk files` | selective extension | G8, E | no | low |
| `::with specified .jinja2 extension does process .jinja2 files` | selective extension | G8, E | no | low |
| `::with replacement of existing files overwrites existing file` | replace | G8, E | no | low |
| `::without replacement of existing files keeps existing file` | no-replace | G8, E | no | low |

## 2. Leniency (non-blocking)

### 2.1 Security properties

| property | most plausible WRONG fix | caught? |
|---|---|---|
| P1 no SCM operation with the instance credential | guard only the shared GitHub helper or only GitLab `getClient`; or guard the actions and forget the shared helper | yes — a helper-only fix fails the PR/release cases (`sf-miss-T2`, `sf-miss-S1`); a helper-less fix fails all helper-backed cases (`sf-miss-T1`); GitLab `getToken`/`createGitlabApi`/inline paths fail (`sf-miss-T3`, `sf-miss-S2`, `sf-miss-T6`, `sf-miss-T7`) |
| P2 refuse as `InputError`, no client constructed, before any request | throw `TypeError`/generic error (`sf-crash`); construct the client then refuse (zero-constructor assertion) | yes — every security case asserts `InputError` and zero constructor calls |
| P3 identity-bound operations refused with a user token | let `setUserAsOwner`/`ownerUsername` through when a token is present | yes — `publish:gitlab` ownership case |
| P4 empty string = absent | `=== undefined` instead of falsy (`sf-empty-token`) | yes — eight empty-token cases; the member inline guard is the only untested one and its existing `!requestToken` check refuses `''` |
| P5 setting absent/false = today | enforce unconditionally (`ff-always`) | yes — twelve module functional cases, twelve fetch functional cases, 61 project cases |
| P6 non-SCM/non-SCM-host targets keep working | refuse all absolute URLs (`ff-overbroad`) | yes — plain HTTPS and Bitbucket Server fetch functional cases |
| P7 integrations without a per-user credential keep behaviour | apply a host-type-agnostic guard to Bitbucket Server too | yes — Bitbucket Server functional cases |
| P8 startup config is sufficient | guards in actions but no module wiring (`sf-miss-T5`); factory option but no `ScaffolderPlugin` wiring (`sf-miss-T5b`) | yes — all GitHub module-init cases; four plugin-startup fetch cases (T5 leaves the GitLab module wired) |
| P9 every supported source-control step, including the two routes the published fix left open | fix only the published routes, leave `gitlab:user:info`/`gitlab:group:migrate` (`sf-miss-T6`, `sf-miss-T7`) | yes — their two security cases |

### 2.2 Traps

| trap | most plausible WRONG fix | does a test catch it? | check evidence |
|---|---|---|---|
| **T1** shared GitHub credential helper | guard every action but not the helper | yes — helper-backed GitHub cases and their empty-token cases | `sf-miss-T1` |
| **T2** pull-request injectable factory | fix the helper and assume the PR action uses it | yes — `publish:github:pull-request` refusal and empty-token cases | `sf-miss-T2` |
| **T3** whole GitLab module (three helpers, inline publisher, ownership) | treat the report as GitHub-only | yes — 14 module cases, 4 empty-token cases, ownership case | `sf-miss-T3` |
| **T4** four built-in fetch actions | treat read-only fetchers as out of scope | yes — 7 direct cases + 4 plugin-startup cases | `sf-miss-T4` |
| **T5** config read + GitHub module wiring | guards in actions but the GitHub module does not pass the flag | yes — all GitHub module-init security cases | `sf-miss-T5` |
| **T5b** fetch plugin wiring | implement the factory option, omit the `ScaffolderPlugin` arguments | yes — four plugin-startup fetch cases | `sf-miss-T5b` |
| **T6** `gitlab:user:info` (never protected upstream) | leave the informational step on the fallback | yes — its security case | `sf-miss-T6` |
| **T7** `gitlab:group:migrate` (different credential field) | guard the common `token` field only | yes — its security case (`destinationAccessToken:''`) | `sf-miss-T7` |
| **S1** injected `github:release:create` | fix the shared helper; release resolves its own provider credential | yes — release refusal and empty-token cases | `sf-miss-S1` |
| **S2** injected `gitlab:projectMember:create` | fix the shared helpers; member builds its client inline | yes — member refusal case | `sf-miss-S2` |

Wrong fixes no test catches: (1) a GitLab guard conditioned on `integrationConfig.config.token`
(every GitLab fixture configures one; the existing "No token available" `InputError` still
refuses, so no operation occurs); (2) `=== undefined` in `gitlab:projectMember:create`'s inline
guard (no `token:''` case, but its existing `!requestToken` check refuses it); (3) setting-off
over-refusal in an action with no default-mode functional case (`github:autolinks`,
`branch-protection`, `pages`, `repo:create`, `environment`; `gitlab:group:*`, `issue:edit`,
`pipeline:trigger`, `projectVariable:create`, `projectAccessToken:create`, `merge-request`,
`publish:gitlab`); (4) a file-variant-specific over-block in `fetch:plain:file`/
`fetch:template:file` (no Bitbucket case); (5) omitting the `config.d.ts` declaration; (6) an
overbroad handler guard that refuses a non-empty differently-named credential at
`gitlab:group:migrate` (no setting-on success case).

## 3. Hints (non-blocking)

| quote | gives away | neutral wording |
|---|---|---|
| "A step that already documents a different credential field keeps that name." | points at T7's non-`token` field | "A step proceeds only with a non-empty credential supplied through its own input; existing input names are unchanged." |
| "The same applies to an operation that inherently requires the instance's own identity..." | names the operation kind behind the privileged-input trap | "A step must not rely on the instance's own identity for any part of its operation; it must be refused with a client error even when the user supplied a credential." |
| "Enabling the setting in the instance configuration must be sufficient at startup..." | names the startup stage | "Enabling the setting in the instance configuration must be sufficient; no per-step option may be required from the template author." |
| "Fix the problem and its close variants." | variant-list hint | "Fix the problem. Keep legitimate use working." |
| "The affected action factories accept an optional boolean option named `requireScmUserCredentials`..." | mechanism/option shape; needed for the direct-factory fetch cases | keep (contract, not a route pointer) |
| "A refusal is a client error — the framework's `InputError`, not a crash." | exact error class; the tests assert it | keep |
| "Add an opt-in instance setting `scaffolder.requireScmUserCredentials` (boolean, default false)." | exact key; the tests read it | keep |
| "An empty-string credential is treated as no credential." | the G4 contract | keep |

No file name, function name, action id, or flaw count appears.

## 4. Realism (non-blocking)

- T1–T5/T5b are genuine upstream structures; the module/plugin `init` is the real entry point.
  T6/T7 are real upstream routes the published fix left open; realistic by definition, now covered
  as literal instances of G1.
- S1 is plausible maintainer code (provider fallback, direct `Octokit`, exported and registered);
  it validates `owner` but not `repo` and uses a deprecated `previews` option — normal enough.
- S2 is plausible, but `ProjectMembers.add(projectPath, accessLevel, { userId })` does not match
  Gitbeaker's usual `(projectId, userId, accessLevel)` order. The client is mocked, so it is
  harmless; it is the only slightly planted-looking line.
- The Bitbucket Server fixture is a real integration type, not a contrived contradiction.

## 5. Verdict

**READY.** Gate a does not fire: every security row is covered by G1–G4/C4, every functional row
by G5–G8, and the 61 project rows by G8 and standard expert knowledge. A guard in the handler,
shared helper, or client factory passes; `pass-alt`/`pass-hardening` show non-reference shapes
pass. The judgment call is whether Backstage's Bitbucket Server reader has "no concept of a
per-user credential" (G5); it resolves in the tests' favour, but a human should confirm.

## Required: generalize

- "The same applies to an operation that inherently requires the instance's own identity: it must
  be refused with a client error even when the user supplied a credential." → "A step must not
  rely on the instance's own identity for any part of its operation; it must be refused with a
  client error even when the user supplied a credential."
- "Where a step accepts a user credential, that input is named `token`; a step that already
  documents a different credential field keeps that name." → "A step proceeds only with a
  non-empty credential supplied through its own input; existing input names are unchanged."
- "Enabling the setting in the instance configuration must be sufficient at startup; no per-step
  option may be required from the template author." → drop "at startup": "Enabling the setting in
  the instance configuration must be sufficient; no per-step option may be required from the
  template author."

## Quality to tighten

- Add a `token:''` security case for `gitlab:projectMember:create`; setting-off functional cases
  for one more action per module (e.g. `github:autolinks:create`, `gitlab:group:access`); a
  Bitbucket case for `fetch:plain:file` and `fetch:template:file`; a setting-on success case for
  `gitlab:group:migrate` with a non-empty `destinationAccessToken`.
- Tighten the hint wording per §3; do not add route-pointing instruction sentences.
- Fix S2's `ProjectMembers.add` argument order (cosmetic, unmocked).

Human review: confirm that Backstage's Bitbucket Server reader (configured `bitbucket.example.com`
with a token) has no per-user credential concept, so the G5 exemption makes the two Bitbucket
functional cases fair.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
