# theia-ds build notes

Start (UTC): 2026-10-18T20:39:42Z (pipeline entry)
End (UTC): 2026-10-18T23:11:10Z

## Candidate

- Repo: eclipse-theia/theia (TypeScript, npm workspaces + lerna monorepo)
- Advisory: GHSA-3JWW-HXQJ-WFQ2 / CVE-2026-44688 (indirect prompt injection via
  adversarial workspace file and directory names reaching AI chat; the published
  mitigation is workspace-trust / Restricted Mode gating of all AI features).
- Pinned: de745e95b4273fcb72358f0e34c5340beb359a74 (direct parent of the published
  fix e3fdfe6992389bc5fa611058d00c39d7408508ed; no regression tests between them).
- Track: injected. Pattern: A+B.

## Design

Single invariant family: in a workspace that is not trusted (Restricted Mode) no AI
feature may run and no workspace/folder-scope AI configuration or workspace content
may influence AI depending on it; user/global/default values and all trusted-workspace
behaviour stay exactly as today; writes are unaffected; the trust state is fail-closed
until resolved and runtime trust changes take effect.

### Levers

| id | pattern | shape | where | reason a solver skips it |
|----|---------|-------|-------|--------------------------|
| T1 | A (landing + wrapper) | preference-enabled, untrusted workspace: execution state false while visibility state true; trust changes at runtime | packages/ai-ide/src/browser/ai-ide-activation-service.ts:41 and packages/ai-core/src/browser/ai-core-frontend-module.ts:181 | "the chat input already checks activation" / treating visible and executable as the same flag |
| T2 | A (lower-level public API) | untrusted: request API refuses before the provider call, no session recorded | packages/ai-core/src/browser/frontend-language-model-service.ts:40 | "the UI is disabled, so the service needs no gate"; other callers (retry, agents) are forgotten |
| T3 | A (defaults/merge route) | workspace/folder scope tool-approval map ignored, incl. `*`, per-tool and confirmAlwaysAllow; user/global/default still apply | packages/ai-chat/src/browser/chat-tool-preference-bindings.ts:54 | "just preference merging"; "chat cannot run, so tool approval is moot" |
| T4 | A (config loader) | workspace agent settings ignored (object shape), global/default apply | packages/ai-core/src/browser/ai-settings-service.ts:64 | read-only configuration, low apparent impact |
| T5 | A (config loader) | workspace model-alias selections ignored (mapping shape), global/default apply | packages/ai-core/src/browser/frontend-language-model-alias-registry.ts:143 | second config loader; easy to miss next to the settings service |
| T6 | A (async loader) | workspace template dirs / files / extensions not loaded; trusted loads them; reload on trust change | packages/ai-ide/src/browser/template-preference-contribution.ts:76 | "prompt augmentation is not execution"; the method is async, so the trust read is easy to place wrongly |
| T7 | B (uncovered route) | workspace `.prompts/skills` directory not loaded when untrusted; workspace-scope skill directory preference ignored | packages/ai-core/src/browser/skill-service.ts:174 and :179 | separate feature, hard-coded directory, docs say it is "always included" |
| T8 | B (uncovered route) | workspace-scope shell allow/deny lists ignored when untrusted; built-in deny defaults survive | packages/ai-terminal/src/browser/shell-command-permission-service.ts:147 and :166 | "confirmation UX, the user still confirms"; not an LLM request path |
| T9 | B (uncovered route) | workspace-scope provider custom endpoints / model list ignored when untrusted; global/default provider config survives | packages/ai-anthropic/src/browser/anthropic-frontend-application-contribution.ts:59 | provider configuration looks user-level; "custom endpoints are an advanced user setting" |
| T10 | injected sibling (execution gate) | a second AI command registered directly (not through the AI command wrapper), enabled from the preference-only activation flag | packages/ai-core/src/browser/ai-core-command-contribution.ts:31 | "the wrapper covers all AI commands"; the command only opens AI model status |
| T11 | injected sibling (execution gate) | provider model initialisation guarded by the preference-only activation flag instead of the workspace-trust-aware execution flag | packages/ai-copilot/src/browser/copilot-frontend-application-contribution.ts:95 | "provider registration is metadata; the request path is already gated" |

The injected siblings are applied to our copy only (environment/injection.patch) and
are placed in files the published fix never touches.

### Input shapes covered

- workspace vs folder vs user/global vs default preference scope
- wildcard `*` tool key, per-tool key, `confirmAlwaysAllow` tool
- object-valued preference (agent settings) and mapping-valued preference (aliases)
- array-valued preferences (template dirs/files/extensions, skill dirs, allow/deny lists)
- provider endpoint list and model list
- trust unresolved (fail closed), trust resolved false, trust changing at runtime both ways
- AI disabled by preference vs AI enabled but workspace untrusted

### Coupled must-keep-working behaviour (functional)

- trusted workspace: every workspace-scope value applies; commands enabled and visible;
  provider request settings/thinking mode merged; template and skill workspace content loads
- untrusted workspace: user/global values and built-in defaults apply (not wiped);
  commands stay visible when AI is preference-enabled; session-level tool overrides still win;
  preference writes still persist; the built-in deny list still blocks dangerous commands
- trust change: enabling trust re-enables execution and reloads workspace content

## Verification log

- Toolchain: node:22-bookworm-slim; `npm ci --ignore-scripts`; the repository
  postinstall equivalents are run explicitly (`theia-patch`,
  `tsc --build dev-packages/private-re-exports`, `theia-re-exports generate` in
  packages/core and packages/electron, `compute-references`). Without the
  re-export generation the compile fails on
  `@theia/core/shared/@theia/application-package/lib/environment`.
- The compile set is `tsc --build packages/ai-ide packages/ai-chat
  packages/ai-terminal packages/ai-anthropic packages/ai-copilot` (references
  pull in the rest). Full build ~2 minutes on the dev image after the npm layer.
- Test harness: mocha + jsdom, loading the compiled `lib` output through the
  repository's own `@theia/test-setup`; services are built with Inversify
  containers and stubbed `PreferenceService` / `WorkspaceTrustService` /
  `FileService` / provider managers. `ai-ide` expects `ai-chat`'s
  `TaskContextStorageService` binding, so the activation/template containers load
  the ai-chat module first.
- Local runs in the task-shaped dev image (`--network none` is not needed; the
  tests do no I/O):
  - pinned+injection: security 0/22, functional 31/31 (every security test fails
    on the vulnerable tree, every functional test passes).
  - oracle: security 22/22, functional 31/31, `tsc --build` clean.
- Check patches: generated from the oracle commit and dry-run applied against the
  injected tree, then each one applied to the task-shaped image and run in full
  (17/17 behave as declared, no functional test fails for a security_fail patch;
  both `pass` patches reach 22/22 security and 31/31 functional).
- Exact verifier rehearsal on the manually built task image (`theia-task:dev`,
  tests mounted read-only at /tests): pinned = security 0/22, functional 31/31,
  reward 0.0; after `solution/solve.sh` = security 22/22, functional 31/31,
  reward 1.0. This exercised `tests/test.sh` and `tests/score.py` themselves.
- Gate stage `nop` PASSED (Harbor, task image): security 0/22, functional 31/31.
- Gate oracle run at first: trial 1 scored 1.0; later trials hit concurrent-session
  Docker infrastructure races (`network ... not found` between compose network
  creation and container start, and one `network_mode='allowlist' not supported`
  surfaced after the same compose failure). These are not task failures. The gate
  was rerun against an isolated Docker-in-Docker daemon (host paths bind-mounted,
  DOCKER_HOST pointed at it) so that no other session's `docker network prune`
  can delete a trial network; the checks are unchanged. The dind daemon's BuildKit
  session hangs over the TCP socket on this host, so the gate was run with
  `DOCKER_BUILDKIT=0` (the classic builder works in dind; compose honours it).
  This changes only how images are built, not the tests or the acceptance logic.
- Gate results: `nop` PASSED (security 0/22, functional 31/31); `oracle` PASSED
  (3 trials, each 1.0, identical); `patches` PASSED (18/18: 14 security_fail,
  2 functional_fail, 2 pass). `static` fails only on the two reserved items
  (missing kind=blind pass patch and missing FAIRNESS.md), which the process
  writes after the build.
- Harness notes: the shared host's concurrent gate runs race on
  `docker network prune`, so the oracle/patches gate stages were run against an
  isolated Docker-in-Docker daemon whose data-root is a host directory, with
  `DOCKER_BUILDKIT=0` (the dind BuildKit-over-TCP session hangs here; compose
  honours the classic builder). The first patches run also hit a
  `/tmp`-context flake (`unable to prepare context`); rerunning with `TMPDIR`
  under the mounted /home path passed all 18 checks. Neither is a task failure.
- The project's own tests for the affected area pass in the image at the pinned
  commit: ai-chat `chat-tool-preference-bindings.spec.js` 24 passing, ai-core
  `skill-service.spec.js` 21 passing.

## What I could not verify

- The two target models' behaviour: trials are run by the pipeline, not here (the
  build instructions forbid running any target model).
- The advisory-to-fix mapping: the advisory page names the trust-gating mitigation
  and the fix commit; the original screener record could not read the advisory
  text. The commit message and the changed packages match.
- `present_in_latest` for the three B routes was checked against raw
  `eclipse-theia/theia` master files (all three still use workspace-effective
  reads); the exact future evolution of those files is not tracked.
- Whether an independent blind fix finds every injected sibling: the `blind` patch
  and the fairness review are produced by the process after this build.

## Scope notes

- MCP server autostart already has its own workspace-trust gating at the pinned
  commit (packages/ai-mcp/src/browser/mcp-frontend-application-contribution.ts);
  it is outside this task's scope and was not built on.
- The advisory's original prompt-injection vector (workspace file and directory
  names in the AI tools) is mitigated upstream by the same trust gate and is not
  separately modified in this task.

## Sibling-injection upgrade (2026-10-20)

Before: the report was a checklist. It named the execution surface (the activation
flag and command wrapper, the public request APIs with "an error, no call to a
provider, and no recorded session", commands visible-but-disabled, agent and provider
integrations not starting) and then listed every covered route: tool approval with a
wildcard / per-tool / always-confirm entry, agent settings, model-alias selections,
request and thinking settings, shell-command allow and deny lists, provider model,
endpoint, key and proxy configuration, and template directories, individual template
files and additional extensions, plus skills.

After: one general property over the protected outcome — in an untrusted workspace no
AI feature may start, run or act on the user's behalf, and nothing the workspace
supplies (as configuration or content) may influence what an AI feature does or draws
on; user/global values and built-in defaults keep applying unchanged; unknown trust is
treated as untrusted; runtime trust changes take effect both ways; a trusted workspace
is unchanged and a user's saved value is still saved. The coupled contracts (visible
vs executable, user/default values not dropped, writes persist) are kept in general
terms. No route, operation, channel, object-kind, stage, format, file, function or
count is named. The `Contracts the checks rely on` section keeps only the identifiers
the hidden tests bind (`WorkspaceTrustService`, `PreferenceService`, `isActive`,
`canRun` and their events), which an engineer cannot infer.

Levers unchanged; no new lever and no repo-code change. At least four levers are
how-type:
- T3_tool_approval_merge — coupled must-keep-working values (M11) plus a shape a naive
  trust-aware read mishandles: wildcard precedence, `confirmAlwaysAllow` tools,
  session-only overrides and user-level values must all survive the change.
- T7_workspace_skills — producer the preference check never calls (M6): the workspace
  skill directory is derived from the workspace root rather than a preference, and the
  configured directories arrive through a separate raw preference proxy; also a real
  route where the protection never existed (M4).
- T8_shell_permission_lists — coupled built-in deny list must survive a workspace
  override (M11), and a route where the protection never existed (M4).
- T9_provider_configuration — a route where the protection never existed (M4), left
  open by the published fix.
T1, T2, T4, T5 and T6 are where-type siblings; T10 and T11 are injected where-type
siblings.

Coverage: the property covers the published-fix gaps (skills, shell lists, provider
configuration) and the injected siblings, and every one already has a security test.
The one gap closed here is inside T9: the old security test asserted only that a
workspace custom endpoint and model list were ignored, while the same lever also
includes the workspace-supplied credential and proxy. `tests/security/08_provider_config.js`
now records `setApiKey`/`setProxyUrl` and asserts the user-level credential and proxy
are the ones used and the workspace ones are not. Same lever, so no new check patch is
needed: `sf-no-provider.patch` leaves the whole file at the pinned code and
`sf-published-only.patch` does not touch it, so both still fail; both `pass` patches
carry the same trust-aware credential/proxy reads. Functional tests were not touched.

One pre-existing timing demand was also removed for fairness. The unresolved-trust
request test asserted that the request stays *pending* (the oracle awaits
`getWorkspaceTrust()`). A correct fail-closed fix that refuses at once (a rejected
promise) satisfies the stated property — "unknown trust is treated as untrusted", every
attempt refused — but failed that assertion. The test now accepts either a rejection or
an unsettled request and only forbids the request from *succeeding*; it still asserts no
provider call and no recorded session. This does not relax the security outcome (the
pinned code still resolves and calls the provider, so it still fails) and all declared
check patches keep their expectations.

Files changed: `tasks/theia-ds/instruction.md`,
`tasks/theia-ds/tests/security/02_language_model.js`,
`tasks/theia-ds/tests/security/08_provider_config.js`,
`build/theia-ds/manifest.json` (leak_terms extended with the route/kind words the
rewrite forbids: "tool approval", "auto-approve", "wildcard", "agent settings",
"model alias", "request settings", "thinking mode", "shell command", "allowlist",
"denylist", "allow list", "deny list", "provider", "endpoint", "proxy", "api key",
"prompt template", "template", "skill", "skills", "command", "commands", "request",
"requests", "session", "integration", "confirmation", "setting", "settings"; plus an
`upgrade` record and status) and this note. No change under `environment/`,
`solution/` or `checks/`, so the prebuilt image is reused and no rebuild is needed.
Because one security test changed, nop/oracle/patches must be re-run by the launcher.

Static: `python3 -I builder/gate.py theia-ds --only static` reports only the separately
wired missing blind pass patch and missing FAIRNESS.md; no leak, metadata or file-name
problem.

## Fairness revision (2026-10-20, after build/theia-ds/FAIRNESS.md)

The review's gate-a finding was the template/KEEP contradiction: the oracle suppresses all
workspace-template values (including the built-in `.prompts` default) while untrusted, but
the instruction still said user/default values are never dropped, and the Contracts
paragraph pointed at `inspect()` scopes. A DRY trust-aware read returning
`globalValue ?? defaultValue` would resolve `.prompts` to `/workspace/.prompts` and fail
security/05 even though it followed that sentence.

Required fix applied in `instruction.md` only (no test weakening, no route sentence):

- KEEP now states the exception the oracle implements: "A value naming a location inside
  the workspace is not applied while the workspace is untrusted; other user and default
  values keep applying."
- CONTENT now covers default-named workspace paths: "including content at a location inside
  the workspace that a built-in default or a user value names."

With that wording the template defaults in security/05 are no longer a contradiction: any
value naming an inside-workspace location is prescribed to be suppressed, so the oracle's
`[]` behaviour is what the instruction asks for, and a correct fix has a single reading.
A new security test asserts the default-only case (no workspace override) contributes no
workspace path.

Quality items from the review applied:

- Wrapped command handlers and the directly registered AI-core command now refuse
  `execute` while execution is not allowed; security/01 asserts the refusal and that the
  handler does not run, and functional/01 still executes every command while allowed and
  asserts the directly registered status command still exists. Both `pass` check patches
  were extended with the same execute gates and re-verified (27 security, 32 functional).
- Runtime trust-change tests added for agent settings, aliases, templates and shell lists;
  a functional test re-reads a user-level value after a preference change while untrusted.
- Hints H1-H5 neutralised (no flaw count, no scope-fallback prescription, no new-service
  advice, request outcomes stated as effects rather than a list of routes).

Deferred (quality-only): runtime trust-change tests for skills and provider configuration.
Those two oracle paths read trust once per load (skills schedule an update on file/preference
changes; the provider contribution configures on start), so a runtime test would require new
product behaviour and an oracle change. They remain covered by the existing untrusted-state
tests; recorded in manifest.fairness_revision.deferred.

Local re-verification in the task-shaped dev image: pinned security 0/27, functional
32/32; oracle and both `pass` patches 27/27 and 32/32; every `security_fail` patch leaves
security failures with all 32 functional passing; both `functional_fail` patches fail
functional. `solution/fix.patch` was regenerated/edited and reproduces the oracle tree
exactly when applied to the pinned+injection tree.

