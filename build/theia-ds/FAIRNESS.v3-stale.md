# Fairness review — theia-ds

Scope read: `tasks/theia-ds/instruction.md`, all of `tasks/theia-ds/tests/`, `solution/fix.patch`,
`build/theia-ds/manifest.json`, `build/theia-ds/notes.md`, `build/theia-ds/checks/*.patch`.

## 1. Per-test fairness

Covering-sentence labels (quoted from instruction.md):

- **G** — “no AI feature may start, run or act on the user's behalf, and nothing the workspace supplies may influence what an AI feature does or draws on.”
- **RUNS** — “Every attempt to use an AI feature is refused with an error, however it is reached, and no AI feature starts or initialises on the workspace's behalf.”
- **CONF** — “No value a workspace, or a folder within it, supplies for an AI feature may have any effect.”
- **KEEP** — “The user's own values and the product's built-in defaults keep applying exactly as before, and are never dropped or replaced by empty values: where the workspace would otherwise override one of them, the user value or the default is what is used.”
- **CONTENT** — “Content that a workspace supplies, or points an AI feature at, is not loaded and does not shape any AI behaviour.”
- **UNKNOWN** — “Until trust has been established the workspace is treated as untrusted; the IDE must never start out permissive.”
- **RUNTIME** — “Trust gained or lost while running takes effect immediately, in both directions.”
- **VIS** — “withholding trust must not take them out of view.”
- **TRUSTED** — “A trusted workspace behaves exactly as it does today.”
- **PREF** — “Whether AI is enabled is a preference; whether it may run is governed by trust.”
- **WRITE** — “A value the user saves is still saved, and must not be silently discarded while a workspace is untrusted.”
- **CR** — “The AI activation service must keep `isActive` and `onDidChangeActiveStatus` … and expose `canRun` and `onDidChangeCanRun` …; `canRun` is true only while AI is enabled and the workspace is trusted.”
- **PS** — “preferences as `PreferenceService` (`get` for the effective value, `inspect` for the default, user, workspace and folder scopes).”

| Test (file::name) | What it asserts | Covering sentence | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| security/01::AI execution is gated on workspace trust::does not allow execution in an untrusted workspace although AI is enabled | `isActive` true, `canRun` false (AI enabled, untrusted) | PREF + CR + G | no | low |
| security/01::…::keeps command visibility but disables command execution in an untrusted workspace | wrapper `isVisible()` true, `isEnabled()` false | VIS + PREF + CR | no | low |
| security/01::…::fails closed while the trust state has not been resolved | `canRun` false while trust pending; wrapper disabled | UNKNOWN | no | low |
| security/01::…::re-evaluates execution when workspace trust changes at runtime | `canRun` true after trust; `onDidChangeCanRun` fires `[true]`; wrapper enabled | RUNTIME + CR | no | low |
| security/01::commands registered directly by the AI core contribution::are all disabled while execution is not allowed | every registered handler `isEnabled()===false` with stub `canRun:false` | RUNS (“however it is reached”) + PREF + CR | no (a direct `WorkspaceTrustService` injection is unbound, but CR names `canRun` as the execution state) | low |
| security/02::language model requests in an untrusted workspace::are refused before reaching the provider and leave no session behind | `sendRequest` rejects, 0 provider calls, `sessions.length===0` | RUNS | no | low |
| security/02::…::do not reach the provider while the trust state is unresolved | no provider call, no session; outcome pending or rejected, never resolved | UNKNOWN + RUNS | no | low |
| security/02::…::cannot be bypassed by gaining trust and losing it between requests | reject / succeed / reject; exactly 1 provider call | RUNTIME + RUNS | no | low |
| security/02::…::ignores workspace request settings while untrusted | request rejected, 0 provider calls | CONF + RUNS | no (vacuously true once the request is refused) | low |
| security/03::tool approval in an untrusted workspace::ignores a workspace wildcard that would auto-approve every tool | `CONFIRM` (workspace `*`=ALWAYS_ALLOW ignored, default CONFIRM) | CONF + KEEP | no | low |
| security/03::…::ignores a workspace per-tool auto-approval for a tool that always needs confirmation | `CONFIRM`, no throw, `confirmAlwaysAllow` honoured | CONF | no | low |
| security/03::…::ignores a folder-scoped approval override | folder-scope `*`=ALWAYS_ALLOW ignored → `CONFIRM` | CONF (“or a folder within it”) | no | low |
| security/04::workspace-scoped AI settings in an untrusted workspace::are ignored by the agent settings reader | `getSettings()` returns the global object | CONF + KEEP | no | low |
| security/04::…::fall back to the built-in default when only a workspace value exists | `getSettings()` returns `{}` | KEEP | no | low |
| security/04::…::are ignored by the language model alias registry | `resolveAlias` returns the global selected model | CONF + KEEP | no | low |
| security/05::workspace prompt templates in an untrusted workspace::do not contribute any workspace path or extension | no call contains a `/workspace` path; no `.evil-extension` | CONTENT + G | **maybe** — fixture default is `['.prompts']`; a correct fix that follows KEEP through `inspect()` (`globalValue ?? defaultValue`) resolves it to `/workspace/.prompts` and fails. A fix that keeps the contribution’s arguments but stops the loader (customization service) also fails, because the harness stubs the loader and inspects only the contribution’s arguments. | medium |
| security/06::skills in an untrusted workspace::are not loaded from the workspace prompts directory | `workspace-skill` absent | CONTENT | no | low |
| security/06::…::are not loaded from workspace-scoped extra directories | `evil-cli-skill` absent | CONF | no | low |
| security/07::shell command approval in an untrusted workspace::ignores a workspace allowlist | `isCommandAllowed('git status')===false` | CONF | no (assumes the sync signature is kept; natural fix keeps it) | low |
| security/07::…::cannot remove the built-in deny list from workspace settings | `checkCommand('sudo ls').allowed===false` | CONF + KEEP | no | low |
| security/08::model provider configuration in an untrusted workspace::does not register a workspace-provided custom endpoint | workspace endpoint/model/credential/proxy ignored; global endpoint and user key/proxy still applied | CONF + KEEP | no | low |
| security/09::provider initialisation in an untrusted workspace::does not register provider models while execution is not allowed | `manager.created` empty with stub `canRun:false` | RUNS (“no AI feature starts or initialises”) + CR | no (CR names `canRun`; a trust-aware read also passes this test, but a direct `WorkspaceTrustService` injection is unbound) | low |
| functional/01::AI command availability::is enabled and visible in a trusted workspace with AI enabled | visible and enabled true | TRUSTED + PREF | no | low |
| functional/01::…::keeps AI commands visible in an untrusted workspace when AI is enabled | visible true | VIS | no | low |
| functional/01::…::hides AI commands when AI is disabled in the preferences | visible and enabled false | PREF | no | low |
| functional/01::…::executes again after trust is granted at runtime | enabled true after trust | RUNTIME | no | low |
| functional/01::…::runs every command of the AI core contribution while execution is allowed | every registered handler enabled with stub `canRun:true` | TRUSTED + CR | no | low |
| functional/02::language model requests::are sent in a trusted workspace and merge workspace request settings | response ok; workspace temperature 1.5 and thinking mode applied; 1 session | TRUSTED | no | low |
| functional/02::…::merge user-level request settings in a trusted workspace | temperature 0.2 | TRUSTED + KEEP | no | low |
| functional/02::…::work after trust is granted at runtime | 1 provider call | RUNTIME | no | low |
| functional/03::tool approval settings::apply workspace wildcard overrides in a trusted workspace | `ALWAYS_ALLOW` | TRUSTED | no | low |
| functional/03::…::apply user-level wildcard overrides in an untrusted workspace | `ALWAYS_ALLOW` | KEEP | no | low |
| functional/03::…::apply the built-in default in an untrusted workspace | `CONFIRM` | KEEP | no | low |
| functional/03::…::let a session-only override win in an untrusted workspace | in-memory session override `DISABLED` wins | G (“nothing the workspace supplies …”) + standard expert knowledge: session state is user/client state, not workspace-scope configuration | no (a fix that forces CONFIRM in untrusted also fails the user-wildcard test) | low |
| functional/03::…::still persist a user choice made in an untrusted workspace | `updateValue` called with the choice | WRITE | no | low |
| functional/03::…::apply workspace per-tool overrides in a trusted workspace | `DISABLED` | TRUSTED | no | low |
| functional/04::AI settings readers::apply workspace agent settings in a trusted workspace | temperature 0.9 | TRUSTED | no | low |
| functional/04::…::apply user-level agent settings in an untrusted workspace | global object | KEEP | no | low |
| functional/04::…::fall back to the built-in default settings | `{}` | KEEP | no | low |
| functional/04::…::apply workspace alias selections in a trusted workspace | `workspace/model` | TRUSTED | no | low |
| functional/04::…::apply user-level alias selections in an untrusted workspace | `global/model` | KEEP | no | low |
| functional/04::…::fall back to the alias default models | non-empty default, not the global model | KEEP | no | low |
| functional/05::workspace prompt templates::are loaded in a trusted workspace | workspace dirs/files/extensions resolved | TRUSTED | no | low |
| functional/06::skills::load workspace, user and configured skills in a trusted workspace | all three names present | TRUSTED | no | low |
| functional/06::…::keep loading user-level skills in an untrusted workspace | `user-skill` present | KEEP | no | low |
| functional/07::shell command approval settings::apply workspace allowlist entries in a trusted workspace | allowed | TRUSTED | no | low |
| functional/07::…::apply user-level allowlist entries in an untrusted workspace | allowed | KEEP | no | low |
| functional/07::…::keep the built-in deny list in an untrusted workspace | denied | KEEP | no | low |
| functional/07::…::do not approve commands without an allowlist entry | denied | standard expert knowledge: default deny when no allowlist entry matches | no | low |
| functional/08::model provider configuration::applies workspace endpoints in a trusted workspace | workspace endpoint registered | TRUSTED | no | low |
| functional/08::…::applies user-level endpoints in an untrusted workspace | user endpoint registered | KEEP | no | low |
| functional/08::…::keeps the built-in model list when no user or workspace value is set | default model registered | KEEP | no | low |
| functional/09::provider initialisation::registers configured models while execution is allowed | `copilot/gpt-test` registered with stub `canRun:true` | TRUSTED + CR | no | low |

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught by |
|---|---|---|
| G / RUNS | Disable the chat input only; leave `LanguageModelService.sendRequest` callable | security/02 (checks/sf-no-request-gate.patch) |
| G / RUNS | Gate with the preference-only `isActive` flag | security/01 1–4 (checks/sf-no-activation.patch) |
| RUNS / T10 | Gate the factory wrapper but leave a directly registered command on `isActive` | security/01 last (checks/sf-no-injected-command.patch) |
| RUNS / T11 | Leave provider initialisation on `isActive` | security/09 (checks/sf-no-injected-copilot.patch) |
| CONF | Blanket-drop all AI preferences in untrusted workspaces | functional 03/04/06/07/08 (checks/ff-wipe-preferences.patch) |
| CONF / T3 | Trust-aware map but crash on `confirmAlwaysAllow` instead of a clean `CONFIRM` | security/03 test 2 (checks/sf-crash-tool-approval.patch) |
| CONF / T3 | Strip `workspaceValue` only; keep `workspaceFolderValue` | security/03 test 3 |
| CONF / T4, T5 | Fix one loader (settings or aliases) and leave its sibling | security/04 1–2 (sf-no-settings), security/04 3 (sf-no-aliases) |
| CONF / T8 | Fix the allowlist but leave the denylist (or vice versa) | security/07 both (sf-no-shell.patch) |
| CONF / T9 | Fix the endpoint list but leave key/proxy/models | security/08 (sf-no-provider.patch) |
| CONTENT / T6 | Fix directories but leave files/extensions | security/05 (loop over all three; sf-no-templates.patch) |
| CONTENT / T7 | Fix the hard-coded workspace skills dir but leave configured dirs (or vice versa) | security/06 both (sf-no-skills.patch) |
| UNKNOWN | Fail-open default `true` before trust resolves | security/01 test 3 (sf-fail-open.patch) |
| VIS / P5 | Hide commands with `canRun` instead of disabling them | security/01 test 2 and functional/01 test 2 (ff-hide-ai.patch) |
| KEEP / P5 | Drop user/global values while untrusted | functional 04, 07, 08 (ff-wipe-preferences.patch) |
| T1 | `canRun` computed from trust only, ignoring the AI preference | functional/01 test 3 |
| T2 | No request gate; rely on the disabled UI | security/02 (sf-no-request-gate.patch) |
| all “published” sites only | Fix only the files in the advisory’s published patch | security/05–09 and security/01 last (sf-published-only.patch) |

**Wrong fixes no test catches**

- A fix that flips only `isEnabled`/`isVisible`: no test calls `wrapped.execute()` or a command’s `execute` in an untrusted workspace, so programmatic execution stays open.
- A fix that snapshots trust once at start-up for templates, skills, shell lists, provider config, agent settings or aliases: only activation, `sendRequest` and command availability have runtime-trust tests; T4–T9 do not.
- Deleting the injected AI-core command instead of gating it: functional/01 only requires that the commands that *are* registered are enabled; it never asserts the status command still exists.
- A trust-aware read cached once: no test changes a preference while untrusted, so a stale snapshot passes every settings/content test.
- `getAllConfirmationSettings` / `resetAllConfirmationModeSettings` left on the workspace-effective read: no test calls them; they are not security-relevant by themselves but are dead untrusted reads.

## 3a. Surface descriptions — Required: generalize

none. The upgrade removed route names; the only named identifiers are in the contracts paragraph and are needed for fairness (see Hints).

## 3. Hints (quality, non-blocking)

1. “That was one symptom, not the whole problem: the same workspace was able to shape other AI behaviour too.” — reveals the flaw count is greater than one. Neutral: “The example is illustrative; the property below is what must hold.”
2. “The AI activation service must keep `isActive` and `onDidChangeActiveStatus` for the preference-only state, and expose `canRun` and `onDidChangeCanRun` for the execution state; `canRun` is true only while AI is enabled and the workspace is trusted.” — names the landing service, the two-state design and its formula (T1). The identifiers cannot be removed, but the descriptive clauses can: “Hidden checks resolve `AIActivationService` and read `isActive`, `canRun` and their change events; `canRun` is false whenever the workspace is not trusted.”
3. “preferences as `PreferenceService` (`get` for the effective value, `inspect` for the default, user, workspace and folder scopes).” — prescribes the fix technique (scope inspection) and the exact fallback chain that leads a solver into the template/default conflict. Neutral: “Hidden checks bind preferences through `PreferenceService`; its public API is available.”
4. “If you introduce a new service, bind it in the package's frontend module.” — suggests the fix will add a shared service. Neutral: “Anything a hidden check resolves must be bound in its package's dependency-injection module.”
5. “Nothing is sent to an external model service, nothing is carried out for the user, and nothing is recorded as though it had been.” — enumerates the request route’s provider-call, execution and session-record outcomes. Neutral: “No external effect is produced and nothing is left behind as though it had been.”

## 4. Realism (quality, non-blocking)

T1–T6 are the published upstream sites; T7–T9 are real unmodified routes the published fix left open and are realistic by definition (not flagged as out of scope). T10 (a small, directly registered AI command enabled from the activation flag) and T11 (provider model start-up gated on `isActive`) are plausible maintainer code and reachable via the real frontend contributions. Nothing looked planted or contrived. One realism-adjacent note: the oracle’s template fix drops the built-in `.prompts` default, which is what creates the security/05 tension, not a realism defect.

## 5. Verdict

**Gate a (fairness): NOT READY.** `security/05` drives a fixture with `defaultValue: ['.prompts']` overridden by `workspaceValue: ['.evil/prompts']` and forbids any `/workspace` path. The KEEP sentence says the default “is what is used” and is “never dropped or replaced by empty values”, and the Contracts paragraph points at `inspect` scopes. A correct DRY fix — trust-aware read returning `globalValue ?? defaultValue` — resolves `.prompts` to `/workspace/.prompts` and fails; the only passing template fix replaces the default with `[]`, contradicting that sentence. A loader-layer guard (customization service) is also valid and unobservable through the stub. Required: narrow KEEP to “except that a value naming a location inside the workspace is not applied while untrusted; other user/default values keep applying”, and extend CONTENT to cover default-named workspace paths; or set the three template defaults in tests/security/05 to `[]` and add a functional test for a user-level template directory outside the workspace. Do not add a route sentence.

**Quality to tighten**

- Test `wrapped.execute()`/command `execute` refusal, not only `isEnabled`.
- Add runtime-trust tests for templates, skills, shell, provider config, settings, aliases.
- Assert the injected status command still exists and is enabled while execution is allowed.
- Add a preference-change-while-untrusted test to catch snapshot readers.
- Neutralize hints H1–H5 as proposed. No realism changes.

Human review: confirm whether the built-in `.prompts` template directory must be suppressed when untrusted (security/05) despite the “defaults keep applying” sentence, and approve the instruction or fixture change.

GATE_A: NOT_READY
NEEDS_HUMAN_REVIEW: YES
