# Fairness audit: mcp-ts-sdk-oauth

Reviewed 2026-10-16 from instruction.md, tests/ (security 18, functional 21, harness, score.py),
solution/fix.patch, manifest.json, notes.md and checks/*.patch, plus the vulnerable source at ef39308e
(read only). Nothing was run. Hadi's original instruction
(~/.tb-graders/cwe/work/mcp-ts-sdk/hadi/.../task/instruction.md) and his DEEPSEEK_WEAKNESS note were
compared against the new text.

Every security test asserts only on what the other authorization server (AS) received, so any
refusal form (throw, discard, re-registration) passes: "Refusing with an error is fine. What matters
is that nothing reaches the other server."

Key instruction sentences:
- R1 "Credentials that belong to one authorization server must never be presented to a different
  authorization server, whichever authorization server an MCP server names and whichever of the SDK's
  OAuth client functions the application uses."
- R2 "This covers credentials configured on a provider for that server, and credentials the
  application saved from an earlier sign-in there, however that sign-in was done."
- P "Legitimate use keeps working as it does today: sign-in, token refresh and reuse of saved
  credentials at the authorization server they belong to; providers configured without naming their
  authorization server; credentials stored by earlier versions of the SDK; and an application whose
  MCP server moves to another authorization server still signs in there."

## 1. Tests

### Security (security/security.test.ts)

| Test | Asserts | Fair because | Correct fix could fail? | Risk |
|---|---|---|---|---|
| standalone token helper > client_credentials pinned provider | fetchToken at attacker AS: client secret not sent | The reported scenario itself; R1, R2 | no | low |
| > private_key_jwt pinned provider | no client assertion presented to attacker | R2 "configured on a provider"; a signed assertion is a credential (expert knowledge) | no | low |
| > static private_key_jwt | pre-built assertion not presented | same | no | low |
| > cross-app access | XAA client secret not sent | R2 | no | low |
| > DCR client from an earlier sign-in | stored registration secret not sent by fetchToken | R2 "saved from an earlier sign-in" | no | low |
| > URL only, no metadata | secret not sent | R1 "whichever AS an MCP server names" | no | low |
| > credentials loaded during prepareTokenRequest | lazily loaded secret not sent | R1 (outcome-based); expert knowledge: check at send time, not before the provider runs | maybe (a check placed before prepareTokenRequest), but that fix is genuinely wrong | low |
| > lookalike tenant on same host | secret for /realms/acme not sent to /realms/acme-support | Expert knowledge: an issuer is the full URL incl. path (RFC 8414) | no | low |
| > authorization_code redemption | stored client secret not sent | R2 | no | low |
| persisted + schema > transport | refresh token and secret not sent after schema reload | R2 (Hadi's original sentence) | no | low (difficulty, not fairness: data producer) |
| > auth(), token schema | refresh token not sent | R2 | no | low |
| > auth(), client-info schema | secret not sent | R2 | no | low |
| > transport, pre-registered, read-only | secret not sent | R2 | no | low |
| > withOAuth, full schema | secret not sent | R2 | no | low |
| other helpers > refresh helper (trap 1) | refreshAuthorization with stamped saved registration + refresh token, pointed at attacker: neither sent | R1 "whichever of the SDK's OAuth client functions"; R2 | no | low-medium (see 6) |
| other helpers > code-exchange helper (trap 1) | exchangeAuthorization at attacker: saved secret not sent | same | no | low-medium |
| saved as returned > auth() after fetchToken redemption (trap 2) | unstamped fetchToken tokens + stamped registration; auth() at attacker does not refresh there | R2 "however that sign-in was done"; R1 | no (reference and alt both pass) | medium (second-order; see 6) |
| saved as returned > transport after refresh helper (trap 2) | same with refreshAuthorization output | same | no | medium |

### Functional (functional/functional.test.ts)

| Test | Asserts | Fair because | Correct fix could fail? | Risk |
|---|---|---|---|---|
| client credentials via transport | connects, legit token | P | no | low |
| expectedIssuer with trailing slash | still matches | P "as it does today"; existing issuersMatch tolerance | maybe, if a new exact `===` compare is written instead of the existing helper | low |
| no pinned issuer | works | P "providers configured without naming their AS" | no | low |
| fetchToken cc / private_key_jwt / multi-tenant | usable tokens | P | no | low |
| DCR client reused by fetchToken | 1 registration | P "reuse of saved credentials" | no | low |
| static pkjwt / XAA through auth() | AUTHORIZED | P | no | low |
| interactive sign-in then refresh | grants [code, refresh], 1 reg | P | no | low |
| schema-validated storage (3 tests) + withOAuth full schema | refresh/reuse, 1 reg | P | no (fix that drops unparseable stamps still passes) | low |
| refresh helper same server | refreshes at legit | P "token refresh" | no | low |
| refresh helper, URL only | `String(URL)` adds "/" vs unslashed stamp | P; issuersMatch documents exactly this case | maybe (exact compare) | low-medium |
| code-exchange helper, app-driven | tokens at legit | P "sign-in" | no | low |
| fetchToken-redeemed tokens refreshed by later auth() | AUTHORIZED via refresh, 1 reg | P "reuse of saved credentials" + R2 "however that sign-in was done" | maybe: a fix that drops every unstamped token next to a stamped registration fails it; that fix breaks legit reuse the instruction protects | medium |
| refresh-helper tokens via transport | works, 3 grants | same | same | medium |
| legacy unbound storage | client+tokens without stamp refresh at honest AS | P "credentials stored by earlier versions of the SDK" | no (refuse_unbound fails it, correctly) | low |
| MCP server moves AS | DCR client re-registers at new AS, old secret not sent | P last clause | no (throw_on_mismatch_in_auth fails it, correctly) | low |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught by |
|---|---|---|
| check in fetchToken | check before prepareTokenRequest | lazily-loaded test (check_before_prepare_only) |
| identity compare | origin-only / prefix compare | lookalike tenant (origin_only_compare, prefix_compare) |
| all credential types | secret only, assertions still sent | private_key_jwt + static tests (secret_only) |
| data producer (schemas strip stamp) | check only | 4 schema tests (check_only) |
| trap 1 helpers | upstream fix (fetchToken only) | 2 helper tests (miss_trap_helpers, upstream_fix) |
| trap 2 unbound tokens | keep legacy back-stamp as is | 2 trap-2 tests (miss_trap_unbound_tokens) |
| trap 2 over-correction | refuse all unstamped | legacy functional (refuse_unbound) |
| moving AS | throw on any mismatch in auth() | moves functional (throw_on_mismatch_in_auth) |
| refuse everything | disable feature | functional (disable_feature) |

Wrong fixes no test catches (all low impact or out of the SDK's reach):
- Keeping `issuer` in the schemas without stripping a server-supplied `issuer` from token/registration
  responses (the reference's `withoutIssuer`): the fake AS never returns one. auth() overwrites the
  stamp, so the impact is limited to helper outputs.
- Providers keyed by issuer holding fetchToken tokens in one slot (builder notes; alt fix closes it).
- Legacy unbound credentials + malicious server: unfixable while P holds; untested by design.
- `exchangeJwtAuthGrant` takes a raw client secret with no binding, and `startAuthorization` sends only
  the client_id. The SDK cannot enforce anything here. Out of scope.

## 3. Hints

No leak_terms appear in instruction.md (checked). The only names are `fetchToken()` and `expectedIssuer`,
both part of Hadi's reported scenario.
- "whichever of the SDK's OAuth client functions the application uses" names the class of trap 1
  (other entry points) without naming a function. Keep it: trap 1's fairness rests on it.
- "however that sign-in was done" names the class of trap 2 abstractly. Keep it: trap 2 rests on it.
- "credentials stored by earlier versions of the SDK" gestures at the legacy (unstamped) fallback.
  It is needed so that refuse_unbound fails fairly. Keep it.
- "obtains tokens there, and keeps them fresh" is a mild cue towards refresh. Optional neutral form:
  "and obtains tokens there".

Hadi's finding: his B2 control sentence ("persists its tokens and client registration and loads them
back through the SDK's own token and client-information schemas") flipped DeepSeek to 3/3. The new
text keeps his original "credentials the application saved from an earlier sign-in there" and adds
nothing about loading, validating, parsing or schemas. The added storage words ("reuse of saved
credentials", "stored by earlier versions") point at the unstamped-means-legacy branch. That is the
branch DeepSeek already saw and kept in all analysed runs, not at the schema producer. So the
saved-credentials path is NOT pointed at more concretely than in Hadi's original. The text is new,
though, so DeepSeek's 0/3 must be re-measured, not assumed.

## 4. Realism

Both traps are unmodified upstream code at ef39308e and are left open by the upstream fix. Nothing is
planted.
- Trap 1: `discoverOAuthServerInfo()`'s doc recommends using it for "token refresh" outside `auth()`.
  `executeTokenRequest()`'s doc names its three callers. The test app does for refresh exactly what the
  report does for fetchToken.
- Trap 2: the legacy back-stamp (auth.ts:1369-1375) is deliberate. However, the docs promise "round-trips
  the stored object verbatim is protected", while the report's own API returns unstamped tokens. The
  first trap-2 test mixes auth() (to get the redirect) with fetchToken (to redeem the code). That is
  slightly unusual, but fetchToken documents the `authorizationCode` option, so it is plausible.

## 5. Verdict

READY. No test needs to change. Optional: drop "keeps them fresh".

## 6. Flagged items

- Trap 1 is fair as worded. The "caller's responsibility" objection fails on two counts. R1 explicitly
  extends the rule to every SDK OAuth client function. And the `clientInformation` handed over carries
  the SDK's own binding (written by `auth()`), so the SDK has what it needs to refuse. Risk low-medium.
  The URL-only refresh functional test needs a trailing-slash-tolerant compare, which the existing
  `issuersMatch` provides.
- Trap 2 is fair as worded. R2 "however that sign-in was done" covers tokens obtained with fetchToken
  or the refresh helper. P requires legacy storage to keep working, so the task is to tell the two
  apart. Two valid routes exist and both pass: (a) ignore unstamped tokens once the stored
  registration is bound elsewhere; (b) stamp the helpers' outputs. The code comment calls the fallback
  intentional for legacy storage, and the instruction makes legacy storage a stated constraint, so a
  careful engineer is not misled.
  Medium risk:
  - route (b) makes about 14 repo `toEqual` tests fail, which may push a solver towards route (a);
  - an over-strict variant of (a) (drop every unstamped token next to a stamped registration) fails
    2 functional tests. That variant breaks reuse the instruction protects, so failing it is fair.
