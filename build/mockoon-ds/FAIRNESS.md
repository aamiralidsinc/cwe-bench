# FAIRNESS — mockoon-ds

## 1. Test-by-test fairness

Covering sentences (quoted from instruction.md):
- **P1**: "State and recorded traffic that the runtime makes available to remote callers, and every update of it, are accessible only to a caller presenting the secret the operator configured. This holds for every exposure, every operation and every way the runtime is run or embedded."
- **P2**: "When no secret is configured, the runtime generates one and reports it to the operator, and remains closed to everyone else."
- **P3**: "An absent, malformed or wrong secret is refused."
- **P4**: "A refused request is answered with a client error and has no side effect; a refused continuing exposure may simply deliver nothing."
- **P5**: "No record of served traffic that the runtime produces, in any form or for any consumer, may contain the value of a sensitive request or response header. Header names and every non-sensitive value remain available."
- **P6**: "No cross-origin grant may be given to a web origin the operator did not list, on an ordinary response or a preflight; refusing the preflight is an acceptable outcome. … An allowed origin is echoed back, or `*` is returned when the operator opted into the wildcard."
- **P7**: "A caller may change process-environment values only under the operator's configured prefix. A key supplied without that prefix must never reach the process environment under its bare name, and no such change may take effect when the configured prefix is empty."
- **P8**: "Callers present the secret as `Authorization: Bearer <secret>`. A client that cannot set request headers presents the same secret as a `token` query parameter; that form is never a substitute for the header on a request that can carry one."
- **P9**: "the `adminApiAuthToken` option or the `MOCKOON_ADMIN_API_TOKEN` environment setting for the secret, and the `adminApiCorsOrigins` option (an array of origins)"
- **P10**: "Ordinary user-defined mock traffic, together with the headers and cross-origin behaviour the environment configures for it, keeps working without the secret."
- **P11**: "Existing reads of process-environment values keep their automatic prefix, and writes under the configured prefix keep working."

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| admin_auth::an unauthenticated request cannot read recorded transactions | 4xx; no TXN_MARKER | P1, P3, P4 | no — any 4xx form passes | low |
| admin_auth::an unauthenticated global variable write has no effect | 4xx; authed read-back lacks value | P1, P4 | no | low |
| admin_auth::an unauthenticated environment variable write has no effect | 4xx; bare key unset | P1, P4, P7 | no — auth-first and prefix-first both leave bare key unset | low |
| admin_auth::an unauthenticated environment update has no effect | 4xx; probe response lacks injected header | P1, P4 | no | low |
| admin_auth::an unauthenticated event stream delivers no recorded transactions | body lacks marker and `transaction-complete` | P1, P4 | no — 4xx response or silent stream both pass | low |
| admin_auth::an unauthenticated management stream delivers no recorded transactions | WS receives no marker | P1, P3 | no — refused upgrade or silent socket both pass | low |
| admin_auth::a wrong bearer token is refused | 4xx; no marker | P3 | no | low |
| admin_auth::the bearer scheme is required in the authorization header | bare token, `Basic`, empty bearer all 4xx | P8, P3 | no | low |
| admin_auth::a token in the query string does not authorize an ordinary request | query token alone → 4xx | P8 | no | low |
| admin_auth::management stays closed when no token is configured | 4xx; no marker | P2 | no — auto-generation, refusal or 404 all pass | low |
| admin_auth::a refusal has no side effect on data buckets | PURGE 4xx; authed listing still has bucket | P1, P4 | no | low |
| admin_redaction::the logs endpoint keeps header names but redacts sensitive values | 2xx; marker and `x-api-key` name present; no secret values | P5 | no | low |
| admin_redaction::the event stream replay keeps header names but redacts sensitive values | replay delivered; no secrets | P5 | no | low |
| admin_redaction::the event stream live events keep header names but redact sensitive values | live event delivered; no secrets | P5 | no | low |
| admin_redaction::the management stream keeps header names but redacts sensitive values | `x-api-key` name present; no secrets | P5 | no | low |
| admin_redaction::runtime transaction logging keeps header names but redacts sensitive values | URL and `x-api-key` name logged; no secrets | P5 | no — "for any consumer" makes cleaning the record before it reaches any logger the primary mechanism; redacting only inside the product's logger factory would fail but leaves an injected logger with the value, so it is not a correct fix | medium |
| admin_redaction::a credential reproduced in a recorded response is redacted wherever it is exposed | echoed secrets absent from live, replay, listing, WS and runtime log | P5 ("in any form") | no — header-slot plus value scan, or whole-record scrub, both pass | medium |
| admin_cors::a disallowed origin gets no grant on an ordinary response | no ACAO for evil origin; status < 500 | P6 | no | low |
| admin_cors::a disallowed origin gets no grant on preflight | no ACAO; status < 500 | P6 | no — omission or 4xx both pass | low |
| admin_cors::no origin is granted when no origin is configured | no ACAO | P6 | no | low |
| admin_cors::a disallowed origin gets no grant on the event stream | no ACAO | P6 | no | low |
| env_prefix::a write outside the configured prefix leaves the bare key unset | bare key unset (status not asserted) | P7 | no — auto-prefix and refusal both pass | low |
| env_prefix::a write is refused when the configured prefix is empty | 4xx; bare key unset | P7, P4 | no | low |
| env_prefix::a bulk import outside the configured prefix leaves the bare key unset | bare key unset | P7 | no | low |
| env_prefix::a bulk import is refused when the configured prefix is empty | 4xx; bare key unset | P7, P4 | no | low |
| serverless_auth::a configured token is required by the serverless listener | no-token and wrong-token both 4xx; no marker | P1, P3, P9 | no | low |
| serverless_auth::the environment token is required when no option is given | same, with env setting supplied | P9, P1, P3 | no | low |
| admin_legit::mock routes keep their environment headers and CORS behaviour | /hello 200 body/headers; OPTIONS 200 with env ACAO | P10 | no | low |
| admin_legit::management endpoints work with the configured token | welcome and logs 2xx; logs parsed array | P1, P9 | no — leaving the welcome open or protecting it both pass | low |
| admin_legit::global variables can be written and read with the token | write and read 2xx; value returned | P1 | no | low |
| admin_legit::environment variable reads keep their automatic prefix | key is `MOCKOON_…`; value read | P11 | no | low |
| admin_legit::prefixed environment variable writes work | 2xx; prefixed env var set | P11, P7 | no — reject-inside and auto-prefix both pass | low |
| admin_legit::prefixed bulk imports work | 2xx; prefixed env var set | P11, P7 | no | low |
| admin_legit::data bucket listing works with the token | 2xx; bucket name present | P1 | no | low |
| admin_legit::environment updates work with the token | 2xx; probe shows updated header | P1 | no | low |
| admin_legit::the event stream delivers live transactions with the token | query token accepted; event and URL delivered | P8 | no | low |
| admin_legit::the management stream delivers transactions with the token | query token accepted; event and URL delivered | P8 | no | low |
| admin_legit::a configured origin is granted access to the management API | 2xx; ACAO = origin or `*` | P6 | no | low |
| admin_legit::a configured origin can preflight the management API | OPTIONS 2xx; ACAO = origin or `*` | P6 (the "refusing the preflight" clause is scoped to unlisted origins; the echo contract covers allowed ones) | no — refusing *all* preflights would fail, but it contradicts "an allowed origin is echoed back" | medium |
| admin_legit::runtime transaction logging still records transactions | logged text has URL and the word `transaction` | P5, P11 | no — the key is the pre-existing log shape | low |
| admin_legit::the serverless listener serves mocks and the management API with the token | /hello 200; logs 2xx array | P10, P1, P9 | no | low |
| admin_legit::the serverless listener honours the environment token | logs 2xx array via env token | P9 | no | low |

## 2. Leniency (quality, non-blocking)

**Per trap — most plausible wrong fix and the catching test/patch:**
- **T1** auth only on `/logs` → caught by `admin_auth::an unauthenticated global variable write…` (and env/update/bucket rows); `checks/sf-logs-only.patch`. GET-only auth → `admin_auth::an unauthenticated global variable write…`; `sf-reads-only`. Presence-only → `admin_auth::a wrong bearer token is refused`; `sf-presence-only`. Fail-open → `admin_auth::management stays closed when no token is configured`; `sf-fail-open`. Throw/500 → every `assertClientError` row; `sf-crash-refusal`.
- **T2** keep the pinned authorization-only masking → `admin_redaction::runtime transaction logging keeps header names…`; `sf-miss-runtime-log`.
- **T3** redact the listing only → `admin_redaction::the event stream replay…` and `…live events…`; `sf-miss-stream-redaction`.
- **T4** write the raw key → `env_prefix::a write outside…` and `…refused when the configured prefix is empty`; `sf-miss-env-prefix`.
- **T5** wrapper drops the token → `serverless_auth::a configured token is required…` and functional `…serverless listener serves mocks…`; `ff-miss-serverless`.
- **T6** no WS check/redaction → `admin_auth::an unauthenticated management stream…` and `admin_redaction::the management stream…`; `sf-miss-ws-auth`.
- **T7** import writes raw keys → `env_prefix::a bulk import outside…` and `…bulk import is refused…`; `sf-miss-bulk-prefix`.
- **T8** header-slot-only redaction → `admin_redaction::a credential reproduced in a recorded response…`; `sf-miss-echo`.
- CORS property: keep the pinned `*` → all four `admin_cors` tests (no dedicated check patch).

**Wrong fixes no test catches:**
1. WebSocket auth by presence only (any non-empty token) — no wrong-token WS case.
2. Reflect any `Origin` whenever `adminApiCorsOrigins` is non-empty — no test configures a list and sends an unlisted origin.
3. Auto-generated secret never exercised: a fix that disables the admin API (or generates an unusable token) passes; "reports it to the operator" is untested.
4. Bulk-import guard checks only the first key — bulk tests send a one-key map.
5. Sensitive response headers (`set-cookie`) never sent; only request-side values are exercised.
6. Callback headers and WebSocket in-flight request logs are never driven — redacting only `transaction-complete` records passes.
7. Serverless CORS: the wrapper may drop `adminApiCorsOrigins` undetected.
8. `proxy-authorization`, `api-key`, `set-cookie` are never sent — a fix covering only the four harness headers passes.
9. Query token accepted on management GETs other than `/logs` — only `/logs` is tested.
10. Bare `/mockoon-admin` welcome left unauthenticated — only an authenticated welcome is tested.

## 3. Hints (quality, non-blocking)

- "Existing reads of process-environment values keep their automatic prefix, and writes under the configured prefix keep working." → "Legitimate environment-value operations keep working, including the runtime's existing prefix behaviour."
- "Ordinary user-defined mock traffic, together with the headers and cross-origin behaviour the environment configures for it, keeps working without the secret." → "Traffic and behaviour the operator defines for their own mocks is unaffected."
- "Sensitive headers are `authorization`, `proxy-authorization`, `cookie`, `set-cookie`, `api-key`, `x-api-key` and `x-auth-token`." (variant list) → "Header names that carry credentials or session material — authentication schemes, cookies, API keys and equivalent custom headers."
- "A configured secret is an ordinary value of a few dozen characters." → "The secret is an arbitrary string" (or drop).
- "A client that cannot set request headers presents the same secret as a `token` query parameter; that form is never a substitute for the header on a request that can carry one." — names a mechanism/form and the tested negative; keep the rule (tests depend on it) but prefer: "The secret may also be read from a `token` query parameter, but never in place of the `Authorization` header on a request that carries one."

## 3a. Required: generalize

- "Existing reads of process-environment values keep their automatic prefix, and writes under the configured prefix keep working." (names the read/write sibling operations and the auto-prefix mechanism).
  Reword: "Legitimate environment-value operations keep working, including the runtime's existing prefix behaviour."
- "Ordinary user-defined mock traffic, together with the headers and cross-origin behaviour the environment configures for it, keeps working without the secret." (names the user-mock/cors sibling surface).
  Reword: "Traffic and behaviour the operator defines for their own mocks is unaffected."
- "a refused continuing exposure may simply deliver nothing" (names the streaming channel kind; the stream tests need only absence, not this allowance).
  Delete; keep "A refused request is answered with a client error and has no side effect."

## 4. Realism (quality, non-blocking)

T1–T5 are unmodified upstream sites and realistic by definition. T6 (management WS log stream attached to the real upgrade handler, outside Express) and T7 (a bulk import next to the existing env-var CRUD routes, with its own write loop) are believable maintainer additions and reachable through the real public entry points; neither looks planted. T8's producer is the existing response-templating engine, reachable via an ordinary mock route. No flags.

## 5. Verdict

**READY.** Every test is derivable from P1–P11 read literally over the protected data/outcome: auth tests accept any 4xx or silence; redaction keeps header names as P5 requires; env-write tests accept both auto-prefix and reject-inside; CORS tests accept omission; the echo test is covered by "in any form". No correct fix following the primary mechanism (authenticate at the management request boundary, redact the record before exposing it, scope env writes, echo only listed origins, convey the token in the wrapper) fails a test. The only judgement calls are the runtime-log record boundary and the scope of "refusing the preflight"; both resolve for the solver under the literal property.

**Quality to tighten:** add a wrong-token WS case; a configured-list + unlisted-origin CORS case; assert the auto-generated token authenticates (or that reporting occurs); send two keys to the bulk import; send a sensitive response header; exercise callback/WS in-flight logs; add a serverless CORS case; send all seven header names; test a query token on a non-`/logs` GET; test the bare welcome path.

Human review: confirm that redacting only in the product's logger factory (leaving an injected logger with the raw record) is not accepted as a correct fix, and that "refusing the preflight is an acceptable outcome" is scoped to unlisted origins only.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
