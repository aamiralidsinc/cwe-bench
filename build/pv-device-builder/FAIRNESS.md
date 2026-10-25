# pv-device-builder — pre-trial fairness review

## 1. Test by test

Covering sentence abbreviated as **P** (the general property): "Whenever a complete user-name/password pair is configured through any supported source, every client-facing surface that reads or changes dashboard-managed data must require authentication, and no request may reach such a surface without valid credentials." **T** = "Everything that works today keeps working exactly as today: a dashboard with no credentials stays open and usable, and a correctly supplied pair still logs clients in."

| Test (file::name) | What it asserts | Fair because | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/test_credential_gate.py::test_legacy_credential_pair_requires_authentication | Old pair configured → anonymous GET /devices is not served | "The old variable names remain supported as a fallback"; **P** | no — any layer (resolver, middleware, handler) satisfies it | low |
| security/...::test_legacy_credential_pair_rejects_wrong_password | Wrong old secret refused, right one accepted | "no request may reach such a surface without valid credentials"; "a complete pair supplied in any supported way must be honoured everywhere" | no | low |
| security/...::test_lone_legacy_password_never_serves_open | Lone old $PASSWORD: non-zero exit, or never serves inventory | "a configuration that supplies only part of a pair must stop startup with a clear error and a non-zero exit instead of serving"; **T** | no — refusal accepted; the alternative also passes. Only an "adopt the old pair only when both halves are set" reading leaves it open, which the partial-pair sentence rules out | medium |
| security/...::test_preauth_command_does_not_expose_inventory | Pre-auth WS summary: `requires_auth` true, no device name, no `result` | **P** (the summary reads managed device data); "session token ... after a successful login" | no — allowlist removal or a dispatcher/handler guard both pass; any no-data refusal shape passes | low |
| security/...::test_public_export_requires_authentication | Anonymous configuration download not served | **P** (it reads managed configuration) | no — prefix removal or handler guard; any non-2xx/no-body refusal | low |
| functional/test_dashboard_auth.py::test_starts_open_without_credentials | No credentials → /devices open | "a dashboard with no credentials stays open and usable" | no | low |
| functional/...::test_lone_os_username_is_not_a_credential | Lone OS user name → starts open | "A user name that the operating system supplies by itself is not a configured credential; it must neither turn protection on nor block a startup that has no credentials at all" | no | low |
| functional/...::test_current_pair_authenticates | Renamed pair gates; Basic accepted | **P**; **T** | no | low |
| functional/...::test_current_pair_beats_legacy_pair | Renamed pair wins; stale pair refused | "the renamed variables and the command-line flags keep precedence over them" | no | low |
| functional/...::test_cli_flags_beat_legacy_pair | Flags win over the old pair | same precedence sentence | no | low |
| functional/...::test_half_current_pair_stops_startup | Half renamed pair → non-zero exit, no port | "a configuration that supplies only part of a pair must stop startup ... non-zero exit" | no | low |
| functional/...::test_os_username_is_not_promoted | OS name + half renamed pair → exit non-zero or refuse `osuser`/hunter2 | "A user name that the operating system supplies by itself is not a configured credential"; partial-pair sentence | no — either accepted branch is reachable at any layer | low |
| functional/...::test_authenticated_client_can_read_summary | After WS login, summary returns devices | **T** ("a correctly supplied pair still logs clients in") | no | low |
| functional/...::test_authenticated_client_can_download_configuration | Basic-auth download succeeds | **T** | no | low |
| functional/test_project_auth_middleware.py::test_auth_middleware_no_password_lets_request_through | Auth off → 200 | **T** | no | low |
| functional/...::test_auth_middleware_options_request_passes_through | OPTIONS → 200 | **T** (existing preflight contract) | no | low |
| functional/...::test_auth_middleware_public_paths_pass_through[spa_shell,favicon] | `/` and `/favicon.ico` public | **T** | no | low |
| functional/...::test_auth_middleware_public_prefixes_pass_through[assets,boards_images] | `/assets/`, `/boards/images/` public | **T** | no | low |
| functional/...::test_auth_middleware_top_level_hashed_bundle_passes_through[5 ids] | Top-level content-hashed bundles public (GET) | **T** | no | low |
| functional/...::test_auth_middleware_hashed_bundle_head_passes_through | HEAD on a hashed bundle public | **T** | no | low |
| functional/...::test_auth_middleware_unhashed_top_level_path_still_gated | `/api/anything` → 401 | **P**; **T** | no | low |
| functional/...::test_auth_middleware_ping_is_gated | `/ping` 401 anonymous, 200 with Basic | **P** (inventory map); **T** | no | low |
| functional/...::test_auth_middleware_nested_hashed_path_still_gated | Deep-link hashed path → 401 | **P**; **T** | no | low |
| functional/...::test_auth_middleware_non_get_hashed_path_still_gated | POST hashed path → 401 | **P** ("or changes"); **T** | no | low |
| functional/...::test_auth_middleware_accepts_valid_bearer_token | Valid Bearer passes | "a session token issued by the dashboard, as today" | no | low |
| functional/...::test_auth_middleware_rejects_invalid_bearer_token | Unknown Bearer → 401 | **P** | no | low |
| functional/...::test_auth_middleware_accepts_valid_basic_auth | Basic passes; limiter cleared | "HTTP Basic ... as today"; **T** | no | low |
| functional/...::test_auth_middleware_records_failure_on_wrong_basic_password | Wrong Basic → 401 + `record_failure` | "a refused request gets a 4xx response and no data"; today's limiter contract | no | low |
| functional/...::test_auth_middleware_returns_lockout_message_when_rate_limited | Lockout → 401 with the existing message | **T** | no — pre-existing, unchanged by the primary fix | low |
| functional/...::test_auth_middleware_no_auth_header_returns_401_with_challenge | 401 + `Basic realm=...` + `Bearer` + body text | **T**; "a refused request gets a 4xx response and no data" | no | low |
| functional/...::test_auth_middleware_malformed_authorization_header_returns_401 | `Token abc` → 401 | **P**; **T** | no | low |
| functional/...::test_create_app_gates_every_non_public_route | Every plain route in the real table → 401 unless in the hard-coded public set; set ⊇ {/devices, /json-config, /compile, /upload} | **P**; **T** | no — the primary fix leaves middleware and route table untouched; a middleware rewrite returning 403 would fail, but that abandons today's contract | low |

(The middleware file is the repository's own 24-case suite, visible to the solver; the reference fix scores 1.0.)

## 2. Verdict

READY. The instruction's primary mechanism — renamed variables/flags authoritative, the pre-rename pair restored as a fallback, a half pair refused at startup — is the reference fix, which passes every test. The general property, read literally, covers all three surfaces (inventory, configuration download, WS summary). The injected surfaces pass with a guard at any layer and any no-data 4xx refusal.

## 3. Required: generalize

none

## 4. Quality to tighten

- Leniency — caught: naive per-variable `or os.getenv("USERNAME")` fallback → `test_os_username_is_not_promoted` + lone-password test (`functional_fail_naive.patch`); settings-only fix → `test_lone_legacy_password_never_serves_open` (`miss_validator.patch`); leaving the WS command pre-auth → pre-auth test (`miss_ws_allowlist.patch`); leaving the export prefix → export test (`miss_public_path.patch`); deleting either feature → the two authenticated positive tests.
- Uncaught: keeping `dashboard/summary` pre-auth but redacting device names (the test only checks DEVICE_NAME and `result`) — assert the payload carries no instance data. Adopting the old pair when the current scheme supplied one half (`{ESPHOME_USERNAME, PASSWORD}`) authenticates instead of erroring; no test drives that shape — add a startup-error case. Over-gating `/api/firmware/download` is unpunished; add a positive token-download test.
- Hints: "A user name that the operating system supplies by itself is not a configured credential; it must neither turn protection on nor block a startup that has no credentials at all." → "A user name that arrives without its own password is not a configured credential; it must neither enable protection nor block a credential-free startup." (optional; current wording is a property, not a route pointer).
- Realism: t1/t2 are real upstream sites; t3/t4 are plausible features on existing allowlists and reachable through the real CLI. Only nit: the injected `config_export` docstring names "the public prefix list in helpers.auth"; a product-level rationale would read less pointed.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
