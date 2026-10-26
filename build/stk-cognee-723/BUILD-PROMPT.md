# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-cognee-723`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 723; missing authorization for a critical function (CWE-306 / CWE-862): wri
- Pinned (vulnerable) commit: 4067f0b8a255f3a511a71cc0806b9f20dd73c31b. Published fix: 10971db1b0bd97e88f96bd2a9ffb3edb7b22bcd0, d10b1b77e2157c6238fd4d1acb1923a048991699, ebcf82412d0954f5c5018444f7eee8d96fee5113.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-723",
 "pattern": "H4",
 "repo": "topoteretes/cognee",
 "pinned_commit": "4067f0b8a255f3a511a71cc0806b9f20dd73c31b",
 "protections": [
  "P1: only a privileged caller may overwrite the deployment-global LLM / vector-DB singleton configuration (provider, model, URL, API key) \u2014 cognee/api/v1/settings/routers/get_settings_router.py:73-101, cognee/modules/settings/save_llm_config.py:11-18, cognee/modules/settings/save_vector_db_config.py:12-19, cognee/infrastructure/llm/config.py:263-278",
  "P2: the deployment decides whether anonymous callers may create accounts \u2014 cognee/api/v1/users/routers/get_register_router.py:5-6, cognee/api/client.py:219-223",
  "P3: the settings read response must not disclose stored API keys, and must cope with keys that are unset \u2014 cognee/modules/settings/get_settings.py:22-34, :44-71, :94-96, :184-187"
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "cognee/api/v1/settings/routers/get_settings_router.py:73-76",
    "cognee/api/v1/settings/routers/get_settings_router.py:97-101",
    "cognee/api/client.py:257"
   ],
   "reason_to_dismiss": "The handler depends only on get_authenticated_user and every caller that reaches it is already a legitimate user of this deployment; settings are a UI convenience with no superuser concept anywhere in the module, so treating the write as privileged is a product decision rather than a bug.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "cognee/api/v1/settings/routers/get_settings_router.py:73-76",
    "cognee/api/v1/settings/routers/get_settings_router.py:97-101",
    "cognee/api/v1/settings/routers/get_settings_router.py:52-53",
    "cognee/modules/settings/save_llm_config.py:12-18"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "cognee/api/v1/config/config.py:311-320",
    "cognee/api/v1/config/config.py:358-366",
    "cognee/api/v1/config/config.py:587-595",
    "cognee/api/v1/config/config.py:598-607",
    "cognee/api/v1/config/config.py:659-716",
    "cognee/cli/commands/config_command.py:129-146",
    "cognee/__init__.py:27"
   ],
   "reason_to_dismiss": "These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.",
   "distance": {
    "files": 3,
    "packages": 3
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cognee/api/v1/config/config.py:311-320",
    "cognee/api/v1/config/config.py:323-355",
    "cognee/api/v1/config/config.py:358-366",
    "cognee/api/v1/config/config.py:598-607",
    "cognee/api/v1/config/config.py:659-716",
    "cognee/cli/commands/config_command.py:139-140",
    "cognee/__init__.py:27",
    "cognee/infrastructure/llm/config.py:263-278",
    "cognee/infrastructure/databases/vector/config.py:111-126"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "cognee/api/v1/users/routers/get_register_router.py:5-6",
    "cognee/api/client.py:219-223"
   ],
   "reason_to_dismiss": "Open self-registration is the fastapi-users default and an ordinary product choice; the route mints an ordinary account (the in-repo UserCreate only adds is_verified/parent_user_id and leaves the base defaults alone), so no privilege is gained by using it.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cognee/api/v1/users/routers/get_register_router.py:5-6",
    "cognee/api/client.py:219-223",
    "cognee/modules/users/models/User.py:50-57"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "cognee/modules/settings/get_settings.py:44-71",
    "cognee/modules/settings/get_settings.py:87-96",
    "cognee/modules/settings/get_settings.py:181-191",
    "cognee/api/v1/settings/routers/get_settings_router.py:69-71"
   ],
   "reason_to_dismiss": "get_settings() takes no user argument and only assembles a read response; masking is a display concern for the settings UI, so a solver can hand it to a separate ticket while fixing the unguarded write \u2014 the handler-level guard never calls this module and cannot be expected to cover it.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "cognee/modules/settings/get_settings.py:44-45",
    "cognee/modules/settings/get_settings.py:87-96",
    "cognee/modules/settings/get_settings.py:181-191",
    "cognee/api/v1/settings/routers/get_settings_router.py:69-71"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M8",
   "origin": "published_fix_far_site",
   "locations": [
    "cognee/modules/settings/get_settings.py:22-23",
    "cognee/modules/settings/get_settings.py:94-96",
    "cognee/modules/settings/get_settings.py:32-34",
    "cognee/modules/settings/get_settings.py:184-187"
   ],
   "reason_to_dismiss": "An unset API key is a configuration edge case that the UI never produces and the existing tests never exercise (they always mock a non-empty key); a masking change does not need to consider it.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "cognee/modules/settings/get_settings.py:22-23",
    "cognee/modules/settings/get_settings.py:94-96",
    "cognee/modules/settings/get_settings.py:32-34",
    "cognee/modules/settings/get_settings.py:184-187",
    "cognee/infrastructure/llm/config.py:47",
    "cognee/infrastructure/databases/vector/config.py:31",
    "cognee/tests/api/test_conditional_authentication_endpoints.py:193-206"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "cognee/modules/settings/get_settings.py:94-96",
    "cognee/modules/settings/get_settings.py:184-187",
    "cognee/modules/settings/save_llm_config.py:17-18",
    "cognee/modules/settings/save_vector_db_config.py:18-19",
    "cognee/api/v1/settings/routers/get_settings_router.py:32",
    "cognee/api/v1/settings/routers/get_settings_router.py:41"
   ],
   "reason_to_dismiss": "The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change \u2014 the coupled value looks handled.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "cognee/modules/settings/get_settings.py:94-96",
    "cognee/modules/settings/get_settings.py:184-187",
    "cognee/modules/settings/save_llm_config.py:17-18",
    "cognee/modules/settings/save_vector_db_config.py:18-19",
    "cognee/api/v1/settings/routers/get_settings_router.py:32",
    "cognee/api/v1/settings/routers/get_settings_router.py:41"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "cognee/modules/users/models/User.py:50-57",
    "cognee/api/v1/users/routers/get_register_router.py:6",
    "cognee/modules/users/methods/create_user.py:27-35",
    "cognee/modules/users/methods/create_default_user.py:10-17"
   ],
   "reason_to_dismiss": "The repository never declares is_superuser itself \u2014 the field comes from the library's base create schema and create_user's default is False \u2014 so the argument that 'our code does not accept it' is available; and the identity the fix trusts is in any case produced by library code the check never inspects.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "cognee/modules/users/models/User.py:50-57",
    "cognee/api/v1/users/routers/get_register_router.py:6",
    "cognee/modules/users/methods/create_user.py:27-35",
    "cognee/modules/users/methods/create_default_user.py:10-17",
    "cognee/modules/users/methods/get_authenticated_user.py:83-110",
    "cognee/api/v1/users/routers/get_visualize_router.py:139-143"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T3",
   "T7"
  ],
  [
   "T4",
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T2"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T7 only pays off once T1 is closed: while POST /api/v1/settings is open to any authenticated user, becoming a superuser adds nothing; after the handler guard lands, a caller-supplied superuser identity (T7) or an ungated registration route (T3) becomes the way around it.",
   "T6 becomes load-bearing exactly when T4 is fixed: once the read response hides the key completely, the masked round-trip (the '*****' sentinel that save_llm_config/save_vector_db_config skip) is the only thing keeping the stored key from being replaced by stars, so a masking change silently converts a confidentiality fix into a write-corruption bug."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T6",
   "what": "The natural hardening of the write path (reject api_key values that do not look like a real key, or drop the masked field) breaks the documented save flow: the GET response emits a masked key (get_settings.py:94-96, :184-187), both input DTOs require api_key (get_settings_router.py:32, :41), and both save functions deliberately skip any value containing '*****' (save_llm_config.py:17-18, save_vector_db_config.py:18-19). Any change of sentinel or validation of 'plausible key' makes the UI overwrite the stored secret or fail to save provider/model at all."
  },
  {
   "a": "T3",
   "b": "T7",
   "what": "Gating or closing the public register route removes the only HTTP way to bootstrap an account: the in-repo bootstrap is the in-process create_default_user (create_default_user.py:5-19) which has no route, so a deployment that provisions its first admin through POST /api/v1/auth/register stops being able to onboard users, while hardening the schema alone still leaves anonymous signup open."
  }
 ],
 "fairness_risks": [
  "POST /api/v1/settings must keep working for the anonymous caller of a single-user deployment: with ENABLE_BACKEND_ACCESS_CONTROL=false the auth dependency is optional (get_authenticated_user.py:80) and an unauthenticated request resolves to the default user (get_authenticated_user.py:93-96), which is created with is_superuser=True (create_default_user.py:10-17), and this posture is documented (.env.template:275-301). A guard keyed on the presence of a bearer token instead of the resolved user contradicts that documented mode.",
  "The existing suite expects the settings route to answer an unauthenticated caller (test_conditional_authentication_endpoints.py:161-213) and its mocked default user has no is_superuser attribute (:20-22), so a superuser check placed on the GET route (or on get_settings itself) breaks tests that are legitimate must-keep-working behaviour.",
  "The masked-key round-trip must not be rejected: the request DTOs make api_key mandatory (get_settings_router.py:32, :41), so a client that fetches settings and posts them back always sends a masked value, and save_llm_config/save_vector_db_config are built to ignore it (save_llm_config.py:17-18, save_vector_db_config.py:18-19).",
  "GET /api/v1/settings must stay available to ordinary (non-superuser) users \u2014 it carries the provider and model chooser lists the UI needs (:60-85, :97-179) and the GET handler has no privilege check at the pinned commit (:52-53); only the key material is sensitive.",
  "Disabling registration by default would break single-user deployments whose only account is the default user and whose first real user was expected to self-register."
 ],
 "effort_minutes": 40,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T4",
   "T6"
  ],
  "why": "Four independent judgements in four different files with four different reasons to leave them alone: (T1) the advisory route itself, described by the report, where the only dismissal is 'authenticated users are trusted' \u2014 this is the shallow entry point; (T3) an unguarded public account-creation route one package away, dismissed as 'open signup is normal / the base schema cannot mint a superuser', which only matters once T1 is closed; (T4) the read-side serializer the report never points at, dismissed as 'a display concern', which a route-level guard cannot reach and which is where the key prefix is actually exposed; (T6) the coupled masked-key round-trip that over-hardening breaks, the value a solver must keep working while changing the mask. T5 rides in the same group as T4 (same serializer lines) and sharpens it with the unset-key shape, but does not count as a fifth independent judgement. T7 is grouped with T3 because one registration gate closes both, and T2 is deliberately excluded from the design even though it is a real uncovered route: the published fix never touches cognee.api.v1.config, so a hidden test on it would not pass on the fixed tree. This beat a single-site design because each trap has a different failure mode (missing check, far unguarded route, wrong layer, coupled regression) and a different model profile: T3/T4/T7 are the absent-protection-with-a-dismissal cases DeepSeek misses, T6 is the over-hardening case MiMo misses, and T5 catches both."
 },
 "unverified": [
  "The content of the three fix commits (10971db, d10b1b, ebcf82) and of fix.diff was not read: there is no shell and the worktree is pinned at the parent commit, so the exact masking edit at get_settings.py:94-96/:184-187 and the exact register-router gate are inferred from the screener record, not from the pinned tree.",
  "Whether fastapi-users 15.0.5 (uv.lock:2601-2602) includes is_superuser in schemas.BaseUserCreate and schemas.BaseUserUpdate: the package is not in the tree. The in-repo fact is only that UserCreate/UserUpdate (cognee/modules/users/models/User.py:50-61) add no fields that would remove it and declare no override; no claim is made here that POST /api/v1/auth/register or PATCH /api/v1/users/me can actually set is_superuser.",
  "Whether GET /api/v1/settings really raises on an unset LLM key: this follows from api_key being declared str (get_settings.py:23) while the llm branch yields None (:94-96) and the singleton defaults llm_api_key to None (infrastructure/llm/config.py:47), but pydantic was not executed here; the vector branch has no falsy guard at all (:184-187).",
  "Whether the vector_db_key can ever be None at runtime: the singleton default is the empty string (infrastructure/databases/vector/config.py:31), so the unconditional slice at :185-187 is only reachable as None if a caller assigned None through config.set_vector_db_config.",
  "Whether the fixed tree re-applied the reverted masking commit d10b1 (the screener saw a revert and a re-apply of the same get_settings.py change), and therefore what the net serializer change is.",
  "Whether any hidden test covers the registration route, and whether solvers receive git history that would expose the earlier reverted guard (a recall shortcut).",
  "Repository size in MB (no shell), so neither tiny_repo nor giant_repo could be confirmed.",
  "Whether the fix changes the masking sentinel or the shape of the unset-key value; the round-trip requirement in T6 is inferred from the pinned save functions only."
 ]
}
  ```
- Published fix sites:   - cognee/api/v1/settings/routers/get_settings_router.py:73-76 — T1 M4 (reason to dismiss: The handler depends only on get_authenticated_user and every caller that reaches it is already a legitimate user of this deployment; settings are a UI convenience with no superuser concept anywhere in the module, so treating the write as privileged is a product decision rather than a bug.)
  - cognee/api/v1/settings/routers/get_settings_router.py:97-101 — T1 M4 (reason to dismiss: The handler depends only on get_authenticated_user and every caller that reaches it is already a legitimate user of this deployment; settings are a UI convenience with no superuser concept anywhere in the module, so treating the write as privileged is a product decision rather than a bug.)
  - cognee/api/client.py:257 — T1 M4 (reason to dismiss: The handler depends only on get_authenticated_user and every caller that reaches it is already a legitimate user of this deployment; settings are a UI convenience with no superuser concept anywhere in the module, so treating the write as privileged is a product decision rather than a bug.)
  - cognee/api/v1/users/routers/get_register_router.py:5-6 — T3 M4 (reason to dismiss: Open self-registration is the fastapi-users default and an ordinary product choice; the route mints an ordinary account (the in-repo UserCreate only adds is_verified/parent_user_id and leaves the base defaults alone), so no privilege is gained by using it.)
  - cognee/api/client.py:219-223 — T3 M4 (reason to dismiss: Open self-registration is the fastapi-users default and an ordinary product choice; the route mints an ordinary account (the in-repo UserCreate only adds is_verified/parent_user_id and leaves the base defaults alone), so no privilege is gained by using it.)
  - cognee/modules/settings/get_settings.py:44-71 — T4 M6 (reason to dismiss: get_settings() takes no user argument and only assembles a read response; masking is a display concern for the settings UI, so a solver can hand it to a separate ticket while fixing the unguarded write — the handler-level guard never calls this module and cannot be expected to cover it.)
  - cognee/modules/settings/get_settings.py:87-96 — T4 M6 (reason to dismiss: get_settings() takes no user argument and only assembles a read response; masking is a display concern for the settings UI, so a solver can hand it to a separate ticket while fixing the unguarded write — the handler-level guard never calls this module and cannot be expected to cover it.)
  - cognee/modules/settings/get_settings.py:181-191 — T4 M6 (reason to dismiss: get_settings() takes no user argument and only assembles a read response; masking is a display concern for the settings UI, so a solver can hand it to a separate ticket while fixing the unguarded write — the handler-level guard never calls this module and cannot be expected to cover it.)
  - cognee/api/v1/settings/routers/get_settings_router.py:69-71 — T4 M6 (reason to dismiss: get_settings() takes no user argument and only assembles a read response; masking is a display concern for the settings UI, so a solver can hand it to a separate ticket while fixing the unguarded write — the handler-level guard never calls this module and cannot be expected to cover it.)
  - cognee/modules/settings/get_settings.py:22-23 — T5 M8 (reason to dismiss: An unset API key is a configuration edge case that the UI never produces and the existing tests never exercise (they always mock a non-empty key); a masking change does not need to consider it.)
  - cognee/modules/settings/get_settings.py:94-96 — T5 M8 (reason to dismiss: An unset API key is a configuration edge case that the UI never produces and the existing tests never exercise (they always mock a non-empty key); a masking change does not need to consider it.)
  - cognee/modules/settings/get_settings.py:32-34 — T5 M8 (reason to dismiss: An unset API key is a configuration edge case that the UI never produces and the existing tests never exercise (they always mock a non-empty key); a masking change does not need to consider it.)
  - cognee/modules/settings/get_settings.py:184-187 — T5 M8 (reason to dismiss: An unset API key is a configuration edge case that the UI never produces and the existing tests never exercise (they always mock a non-empty key); a masking change does not need to consider it.)
  - cognee/modules/settings/get_settings.py:94-96 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
  - cognee/modules/settings/get_settings.py:184-187 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
  - cognee/modules/settings/save_llm_config.py:17-18 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
  - cognee/modules/settings/save_vector_db_config.py:18-19 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
  - cognee/api/v1/settings/routers/get_settings_router.py:32 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
  - cognee/api/v1/settings/routers/get_settings_router.py:41 — T6 M11 (reason to dismiss: The '*****' skip in both save functions already stops the masked value from overwriting the stored key, so while adding authorization nothing on this path needs to change — the coupled value looks handled.)
- Uncovered routes to confirm (pattern B):   - cognee/api/v1/config/config.py:311-320 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/api/v1/config/config.py:358-366 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/api/v1/config/config.py:587-595 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/api/v1/config/config.py:598-607 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/api/v1/config/config.py:659-716 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/cli/commands/config_command.py:129-146 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/__init__.py:27 — T2 M2 (reason to dismiss: These are in-process library setters and a local CLI run by the deploying application's own trusted code: there is no HTTP caller and no user identity at that layer, so there is no unprivileged actor to authorise; tests and notebooks call the dict forms directly.)
  - cognee/modules/users/models/User.py:50-57 — T7 M10 (reason to dismiss: The repository never declares is_superuser itself — the field comes from the library's base create schema and create_user's default is False — so the argument that 'our code does not accept it' is available; and the identity the fix trusts is in any case produced by library code the check never inspects.)
  - cognee/api/v1/users/routers/get_register_router.py:6 — T7 M10 (reason to dismiss: The repository never declares is_superuser itself — the field comes from the library's base create schema and create_user's default is False — so the argument that 'our code does not accept it' is available; and the identity the fix trusts is in any case produced by library code the check never inspects.)
  - cognee/modules/users/methods/create_user.py:27-35 — T7 M10 (reason to dismiss: The repository never declares is_superuser itself — the field comes from the library's base create schema and create_user's default is False — so the argument that 'our code does not accept it' is available; and the identity the fix trusts is in any case produced by library code the check never inspects.)
  - cognee/modules/users/methods/create_default_user.py:10-17 — T7 M10 (reason to dismiss: The repository never declares is_superuser itself — the field comes from the library's base create schema and create_user's default is False — so the argument that 'our code does not accept it' is available; and the identity the fix trusts is in any case produced by library code the check never inspects.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T3, T4, T6. Why: Four independent judgements in four different files with four different reasons to leave them alone: (T1) the advisory route itself, described by the report, where the only dismissal is 'authenticated users are trusted' — this is the shallow entry point; (T3) an unguarded public account-creation route one package away, dismissed as 'open signup is normal / the base schema cannot mint a superuser', which only matters once T1 is closed; (T4) the read-side serializer the report never points at, dismissed as 'a display concern', which a route-level guard cannot reach and which is where the key prefix is actually exposed; (T6) the coupled masked-key round-trip that over-hardening breaks, the value a solver must keep working while changing the mask. T5 rides in the same group as T4 (same serializer lines) and sharpens it with the unset-key shape, but does not count as a fifth independent judgement. T7 is grouped with T3 because one registration gate closes both, and T2 is deliberately excluded from the design even though it is a real uncovered route: the published fix never touches cognee.api.v1.config, so a hidden test on it would not pass on the fixed tree. This beat a single-site design because each trap has a different failure mode (missing check, far unguarded route, wrong layer, coupled regression) and a different model profile: T3/T4/T7 are the absent-protection-with-a-dismissal cases DeepSeek misses, T6 is the over-hardening case MiMo misses, and T5 catches both. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): POST /api/v1/settings must keep working for the anonymous caller of a single-user deployment: with ENABLE_BACKEND_ACCESS_CONTROL=false the auth dependency is optional (get_authenticated_user.py:80) and an unauthenticated request resolves to the default user (get_authenticated_user.py:93-96), which is created with is_superuser=True (create_default_user.py:10-17), and this posture is documented (.env.template:275-301). A guard keyed on the presence of a bearer token instead of the resolved user contradicts that documented mode. | The existing suite expects the settings route to answer an unauthenticated caller (test_conditional_authentication_endpoints.py:161-213) and its mocked default user has no is_superuser attribute (:20-22), so a superuser check placed on the GET route (or on get_settings itself) breaks tests that are legitimate must-keep-working behaviour. | The masked-key round-trip must not be rejected: the request DTOs make api_key mandatory (get_settings_router.py:32, :41), so a client that fetches settings and posts them back always sends a masked value, and save_llm_config/save_vector_db_config are built to ignore it (save_llm_config.py:17-18, save_vector_db_config.py:18-19). | GET /api/v1/settings must stay available to ordinary (non-superuser) users — it carries the provider and model chooser lists the UI needs (:60-85, :97-179) and the GET handler has no privilege check at the pinned commit (:52-53); only the key material is sensitive. | Disabling registration by default would break single-user deployments whose only account is the default user and whose first real user was expected to self-register.. Conflicts the reader found: The natural hardening of the write path (reject api_key values that do not look like a real key, or drop the masked field) breaks the documented save flow: the GET response emits a masked key (get_settings.py:94-96, :184-187), both input DTOs require api_key (get_settings_router.py:32, :41), and both save functions deliberately skip any value containing '*****' (save_llm_config.py:17-18, save_vector_db_config.py:18-19). Any change of sentinel or validation of 'plausible key' makes the UI overwrite the stored secret or fail to save provider/model at all. | Gating or closing the public register route removes the only HTTP way to bootstrap an account: the in-repo bootstrap is the in-process create_default_user (create_default_user.py:5-19) which has no route, so a deployment that provisions its first admin through POST /api/v1/auth/register stops being able to onboard users, while hardening the schema alone still leaves anonymous signup open.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-cognee-723/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-cognee-723/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-cognee-723/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-cognee-723/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-cognee-723/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-cognee-723/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-cognee-723/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-cognee-723 --only static
python3 -I common/gate/gate.py stk-cognee-723 --only nop
python3 -I common/gate/gate.py stk-cognee-723 --only oracle
python3 -I common/gate/gate.py stk-cognee-723 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-cognee-723/`;
  - edit only `tasks/stk-cognee-723/`, `build/stk-cognee-723/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-723.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-cognee-723`. Control task slug: `stk-cognee-723-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-723.json`.
