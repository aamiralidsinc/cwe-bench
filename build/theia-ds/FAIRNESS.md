# theia-ds — pre-trial fairness and leniency review

Covering sentences quoted in the table (the task's one general property, read literally):

- **(R)** "Every attempt to use an AI feature is refused with an error, however it is reached, and no AI feature starts or initialises on the workspace's behalf. No external effect is produced and nothing is left behind as though it had been."
- **(C)** "No value a workspace, or a folder within it, supplies for an AI feature may have any effect. The user's own values and the product's built-in defaults keep applying exactly as before ... A value naming a location inside the workspace is not applied while the workspace is untrusted."
- **(K)** "Content that a workspace supplies, or points an AI feature at, is not loaded ... including content at a location inside the workspace that a built-in default or a user value names."
- **(U)** "Until trust has been established the workspace is treated as untrusted ... Trust gained or lost while running takes effect immediately, in both directions."
- **(T)** "A trusted workspace behaves exactly as it does today ... withholding trust must not take them out of view. A value the user saves is still saved."
- **(X)** Contracts: "`canRun` is false whenever the workspace is not trusted"; `isActive` is the enabled preference.

## 1. Test-by-test fairness

| Test (file::name) | What it asserts | Covering instruction sentence | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| security/01_activation.js::does not allow execution in an untrusted workspace although AI is enabled | `isActive` true, `canRun` false | (X); (R) | no | low |
| security/01_activation.js::keeps command visibility but disables command execution | wrapper `isVisible` true, `isEnabled` false | (T) "withholding trust must not take them out of view"; (R) | no | low |
| security/01_activation.js::refuses programmatic command execution | wrapper `execute` rejects; handler not run | (R) "however it is reached"; no external effect | no — a guard only in the registry dispatcher leaves direct handler calls open, which the sentence forbids | medium |
| security/01_activation.js::fails closed while the trust state has not been resolved | `canRun` false while trust pending | (U); (X) | no | low |
| security/01_activation.js::re-evaluates execution when workspace trust changes at runtime | `canRun`/event true after grant | (U) both directions | no | low |
| security/01_activation.js::commands registered directly by the AI core contribution are disabled and refuse execution | every direct command disabled and rejects | (R) "however it is reached"; "no AI feature ... runs" | no — a direct AI command is still an AI feature | low |
| security/02_language_model.js::are refused before reaching the provider and leave no session behind | rejects, 0 provider calls, 0 sessions | (R) refusal + nothing left behind | no | low |
| security/02_language_model.js::do not reach the provider while the trust state is unresolved | no call/session; may reject or pend, not succeed | (U); (R) | no — test accepts immediate refusal or awaiting trust | low |
| security/02_language_model.js::cannot be bypassed by gaining trust and losing it between requests | only the trusted request reaches the provider | (U) both directions | no | low |
| security/02_language_model.js::ignores workspace request settings while untrusted | rejects, 0 calls | (C); (R) | no | low |
| security/03_tool_confirmation.js::ignores a workspace wildcard that would auto-approve every tool | default wildcard CONFIRM wins | (C) workspace value no effect, default applies | no | low |
| security/03_tool_confirmation.js::ignores a workspace per-tool auto-approval for a tool that always needs confirmation | CONFIRM for confirmAlwaysAllow tool | (C); standard expert knowledge: existing always-confirm policy is unchanged | no | low |
| security/03_tool_confirmation.js::ignores a folder-scoped approval override | folder override ignored, default CONFIRM | (C) "a workspace, or a folder within it" | no | low |
| security/04_config_loaders.js::are ignored by the agent settings reader | untrusted returns global settings | (C) user values keep applying | no | low |
| security/04_config_loaders.js::fall back to the built-in default when only a workspace value exists | returns `{}` | (C) defaults apply, workspace value no effect | no | low |
| security/04_config_loaders.js::are ignored by the language model alias registry | resolves to global model | (C) | no | low |
| security/04_config_loaders.js::re-evaluate the trust state at runtime | both readers switch with trust | (U) both directions | no — oracle-style trust-event reader passes; a per-call trust read also passes | low |
| security/05_templates.js::do not contribute any workspace path or extension | no `/workspace` path, no workspace extension | (C); (K) | no | low |
| security/05_templates.js::do not use a built-in default that names a location inside the workspace | default `.prompts` alone contributes no `/workspace` path | (C) inside-workspace value not applied; (K) default-named location not loaded | no | low |
| security/05_templates.js::reload when workspace trust changes at runtime | trusted loads workspace path; untrusted none | (U); (T) | no | low |
| security/06_skills.js::are not loaded from the workspace prompts directory | workspace skill absent | (K) "Content that a workspace supplies" | no | low |
| security/06_skills.js::are not loaded from workspace-scoped extra directories | workspace extra dir absent | (C) workspace value no effect | no — natural fix reads `PreferenceService` scopes (named in Contracts); only a wrapper around the injected `AICorePreferences` stub would see merged workspace values | medium |
| security/07_shell_permissions.js::ignores a workspace allowlist | workspace allow entry does not approve | (C) | no | low |
| security/07_shell_permissions.js::cannot remove the built-in deny list from workspace settings | built-in deny still blocks | (C) defaults keep applying | no | low |
| security/07_shell_permissions.js::re-evaluates the trust state at runtime | allow only while trusted | (U) | no | low |
| security/08_provider_config.js::does not register a workspace-provided custom endpoint | evil endpoint/model absent; global endpoint, user key and proxy apply | (C); (K) | no | low |
| security/09_provider_init.js::does not register provider models while execution is not allowed | manager registers nothing | (R) "no AI feature starts or initialises"; (X) | no — `canRun` is the stated execution API; a direct trust-service gate would miss the stub binding | medium |
| functional/01_activation.js::is enabled and visible in a trusted workspace with AI enabled | visible and enabled true | (T) | no | low |
| functional/01_activation.js::keeps AI commands visible in an untrusted workspace when AI is enabled | visible true | (T) | no | low |
| functional/01_activation.js::hides AI commands when AI is disabled in the preferences | visible and enabled false | (T) "Whether AI is enabled still governs what is offered" | no | low |
| functional/01_activation.js::executes again after trust is granted at runtime | visible and enabled true | (U); (T) | no | low |
| functional/01_activation.js::runs every command of the AI core contribution while execution is allowed | status command exists; all enabled and execute resolves | (T) "behaves exactly as it does today" | no | low |
| functional/02_language_model.js::are sent in a trusted workspace and merge workspace request settings | provider called with workspace temp/thinking; session recorded | (T) | no — an oracle-style reader resolves initial trust before the awaited call; awaiting `ready` also works | low |
| functional/02_language_model.js::merge user-level request settings in a trusted workspace | global temp applied | (T) | no | low |
| functional/02_language_model.js::work after trust is granted at runtime | request succeeds | (U) | no | low |
| functional/03_tool_confirmation.js::apply workspace wildcard overrides in a trusted workspace | ALWAYS_ALLOW | (T) | no | low |
| functional/03_tool_confirmation.js::apply user-level wildcard overrides in an untrusted workspace | ALWAYS_ALLOW | (C) user values keep applying | no | low |
| functional/03_tool_confirmation.js::apply the built-in default in an untrusted workspace | CONFIRM | (C) defaults keep applying | no | low |
| functional/03_tool_confirmation.js::let a session-only override win in an untrusted workspace | session DISABLED wins | (C) user values; (T) | no | low |
| functional/03_tool_confirmation.js::still persist a user choice made in an untrusted workspace | `updateValue` recorded | (T) "A value the user saves is still saved" | no | low |
| functional/03_tool_confirmation.js::apply workspace per-tool overrides in a trusted workspace | workspace DISABLED applied | (T) | no | low |
| functional/04_config_loaders.js::apply workspace agent settings in a trusted workspace | workspace temperature applied | (T) | no | low |
| functional/04_config_loaders.js::apply user-level agent settings in an untrusted workspace | global temperature applied | (C) | no | low |
| functional/04_config_loaders.js::fall back to the built-in default settings | `{}` | (C) | no | low |
| functional/04_config_loaders.js::re-read user-level agent settings when the preference changes while untrusted | new global value visible on the next call | (C) "keep applying exactly as before" | no — the pinned reader is per-call; only an event-only cache fails on the harness's eventless scope mutation | medium |
| functional/04_config_loaders.js::apply workspace alias selections in a trusted workspace | workspace model applied | (T) | no | low |
| functional/04_config_loaders.js::apply user-level alias selections in an untrusted workspace | global model applied | (C) | no | low |
| functional/04_config_loaders.js::fall back to the alias default models | non-global built-in default | (C); standard expert knowledge: alias registry default models | no | low |
| functional/05_templates.js::are loaded in a trusted workspace | workspace dir/file/extension applied | (T) | no | low |
| functional/06_skills.js::load workspace, user and configured skills in a trusted workspace | workspace, configured and user skills load | (T) | no | low |
| functional/06_skills.js::keep loading user-level skills in an untrusted workspace | user skill loads | (C); (K) user-independent content still loads | no | low |
| functional/07_shell_permissions.js::apply workspace allowlist entries in a trusted workspace | allowed | (T) | no | low |
| functional/07_shell_permissions.js::apply user-level allowlist entries in an untrusted workspace | allowed | (C) | no | low |
| functional/07_shell_permissions.js::keep the built-in deny list in an untrusted workspace | sudo denied | (C) | no | low |
| functional/07_shell_permissions.js::do not approve commands without an allowlist entry | not allowed | (C) | no | low |
| functional/08_provider_config.js::applies workspace endpoints in a trusted workspace | workspace endpoint registered | (T) | no | low |
| functional/08_provider_config.js::applies user-level endpoints in an untrusted workspace | global endpoint registered | (C) | no | low |
| functional/08_provider_config.js::keeps the built-in model list when no user or workspace value is set | built-in model registered | (C) defaults keep applying | no | low |
| functional/09_provider_init.js::registers configured models while execution is allowed | configured model registered | (T); (X) | no | low |

Refusal form: every refusal assertion is `assert.rejects` (or `assert.rejects(async () => handler.execute())`); any rejection, including a synchronous throw inside the async arrow, and any error class/message satisfies it. No test demands a specific error type or status.

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught by |
|---|---|---|
| Execution gating | only flip `isVisible` (hide instead of disable) | security/01 visibility, functional/01 "keeps AI commands visible"; `checks/ff-hide-ai.patch` |
| Execution gating | `canRun = isActive`, no trust | security/01 all; `sf-no-activation.patch` |
| Execution gating | gate `isEnabled` but not `execute` | security/01 programmatic and direct-command; `sf-published-only.patch` |
| Execution gating | default trusted until resolution | security/01 fail-closed; `sf-fail-open.patch` |
| Config | drop user/default too | functional/03,04,07,08; `ff-wipe-preferences.patch` |
| Config | raw effective read (workspace wins) | security/03,04,07,08; `sf-no-tool-approval`/`no-settings`/`no-aliases`/`no-shell`/`no-provider.patch` |
| Content | suppress workspace prefs but apply built-in `.prompts` default | security/05 default-only test (no dedicated patch; `sf-no-templates` fails both) |
| Trusted unchanged | block preference writes while untrusted | functional/03 persist test (no check patch) |
| T1 activation/wrapper | wrapper-only assumption | security/01; `sf-no-activation.patch` |
| T2 request gate | UI-disabled assumption, no service gate | security/02; `sf-no-request-gate.patch` |
| T3 tool approval | keep raw `ChatToolPreferences` | security/03; `sf-no-tool-approval.patch` |
| T4 agent settings | keep raw settings | security/04; `sf-no-settings.patch` |
| T5 aliases | keep raw alias registry | security/04; `sf-no-aliases.patch` |
| T6 templates | trust read after path resolution, or default `.prompts` applied | security/05; `sf-no-templates.patch` |
| T7 skills | guard only preference dirs, leave hard-coded workspace dir | security/06 first; `sf-no-skills.patch` |
| T8 shell lists | raw allow/deny reads | security/07; `sf-no-shell.patch` |
| T9 provider config | raw endpoint/key/proxy reads | security/08; `sf-no-provider.patch` |
| T10 injected command | assume the wrapper covers every command | security/01 direct-command; `sf-no-injected-command.patch` |
| T11 provider init | gate on `isActive` only | security/09; `sf-no-injected-copilot.patch` |

Wrong fixes no test catches: (a) runtime trust-change for skills and Anthropic provider config (manifest `fairness_revision.deferred`); (b) runtime trust-change for Copilot provider init — a fix that initialises once but never re-registers on trust gain passes functional/09 and security/09; (c) write paths other than tool confirmation (`AISettingsService.updateAgentSettings`, shell/provider writes) — "a value the user saves is still saved" is only asserted for tool confirmation; (d) `getAllConfirmationSettings` / `resetAllConfirmationModeSettings` trust-aware reads — changed by the oracle but unasserted, so a raw-read fix passes; (e) a request that never settles under unresolved trust — security/02 explicitly accepts pending, though (R) says "refused with an error".

## 3. Hints (quality, non-blocking)

- "Fix the flaw everywhere it can be reached, not only the example." / "The example is illustrative; the property below is what must hold." → delete both meta-sentences or write "The property below applies to every AI feature."
- "Do not special-case anything taken from this report." → "Address the property generally."
- "Whether AI is enabled is a preference; whether it may run is governed by trust." → "The preference that enables AI does not grant permission to run; trust does." (keeps the property, drops the mechanism split).
- Contracts paragraph ("Workspace trust is supplied as `WorkspaceTrustService` (`getWorkspaceTrust()` and `onDidChangeWorkspaceTrust`); hidden checks bind preferences through `PreferenceService` ... Anything a hidden check resolves must be bound in its package's dependency-injection module.") and "Hidden checks resolve `AIActivationService` and read `isActive`, `canRun`..." — these name functions/mechanisms, but the identifiers are required so the hidden checks can bind and read them; removing them would make the tests unfair. Keep; no change recommended.
- "A value naming a location inside the workspace..." and "...including content at a location inside the workspace that a built-in default or a user value names" are general data properties added for the template default; they are not route hints and should stay (they resolve the prior contradiction).

## 3a. Required: generalize

none — no sentence names a route, operation, command, channel, object kind, stage, format, file, function or sibling site. "Workspace / folder", "value naming a location", "starts or initialises" are general data/outcome properties; the Contracts identifiers are test-binding contracts, not route descriptions.

## 4. Realism

T1–T6 are the real published upstream fix sites. T7–T9 are real, unmodified upstream code reachable through the DI services (`SkillService`, `ShellCommandPermissionService`, anthropic contribution); they are realistic even though the published fix left them open. T10/T11 are injected but plausible maintainer patterns (a small AI command registered without the wrapper; provider init gated on the preference flag), reachable through the real entry point. Nothing looks planted or contrived; no flags.

## 5. Verdict

**Gate a (UNFAIRNESS): READY.** Every test is covered by a literal reading of (R)/(C)/(K)/(U)/(T)/(X). The natural correct fix — `canRun` = preference-enabled ∧ trusted (fail-closed, live trust events), refusal with an error at the handler, request service and direct command, trust-aware reads of global/default for config and content, suppression of inside-workspace defaults, writes untouched — passes all 27 security and 32 functional tests. The historical template/KEEP contradiction is resolved by the inside-workspace exception. The four medium rows are alternative-design or harness-sensitivity risks, not the primary stated mechanism: registry-only command gating leaves direct calls open (forbidden by "however it is reached"); event-only settings caching changes the pinned per-call read that "exactly as before" preserves; a `WorkspaceTrustService`-direct provider-init gate and an `AICorePreferences`-proxy wrapper are not the contract's stated `canRun`/`PreferenceService` mechanism. No "yes" remains.

**Required: generalize:** none (see 3a).

**Quality to tighten:** (1) make functional/04 "re-read ... while untrusted" simulate the change through `updateValue`/a fired preference event, or document per-call reads; (2) bind a trust stub in the skill and Copilot containers (or state that `canRun`/`PreferenceService` is the required path) so correct alternative layers are not failed; (3) add runtime trust-change tests for skills, Anthropic provider config and Copilot provider init; (4) add write-path tests for agent settings and shell/provider preferences; (5) assert the trust-aware `getAllConfirmationSettings`/reset paths; (6) decide whether unresolved trust must reject immediately rather than pend (R says "refused with an error").

Human review: confirm that the eventless preference mutation in functional/04 and the DI stubs that omit a trust binding in security/06/09 are acceptable harness choices (they pass the primary-mechanism fix but would fail alternative, still-correct implementations).

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
