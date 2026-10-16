# Fairness audit: async-http-client-inv instruction

The tests are unchanged copies of `tasks/async-http-client/tests/`, including the 2026-10-16 repair
(`SecurityTests::storedSessionNotSubstitutedForANamedCallerCookieWithAnUnusualValue`). The quotes
below are from the new `tasks/async-http-client-inv/instruction.md`.

## Test by test

| test | what it asserts | sentence that makes it fair | risk |
|---|---|---|---|
| SecurityTests::callerCookieHeaderNotReplacedByStoreOnFirstRequest | Store seeded with `SID=storeval`; the caller sets `Cookie: SID=userB`; the first request carries `SID=userB` and no `storeval` | The report example, and "Every cookie the caller puts in a request's `Cookie` header(s) is delivered to the server. A cookie the store already held before the call never replaces, removes or overrides a cookie the caller set" | low |
| SecurityTests::callerCookieHeaderNotDroppedWhenStoreHoldsADifferentCookie | Store holds `SID` and `tracking`; the caller sets `Cookie: session=mine` (a different name); the request carries `session=mine` | "Every cookie the caller puts in ... is delivered"; "never replaces, removes or overrides" (removal covers the dropped-cookie case) | low |
| SecurityTests::callerCookieHeaderHonoredAcrossARedirect | With redirect following on, a 302 to the same origin; the follow-up request carries `SID=userB` and no `storeval` | "on any request the client sends for that call, including those it issues automatically to continue it". Standard expert knowledge: an HTTP client continues a call automatically by following redirects and by answering authentication challenges; both are visible options of this client | medium (redirect is no longer named; the agent must find the follow-up paths itself) |
| SecurityTests::callerCookieHeaderHonoredOnAnAuthenticationRetry | Non-preemptive Basic auth; exactly 2 requests (401, then one retry); the retry carries `SID=userB` and no `storeval` | Same sentence as above. Exactly two requests: "Everything else about how requests are sent and continued behaves exactly as today" (the existing one-retry behaviour) | medium (as above, auth retry is no longer named) |
| SecurityTests::storedSessionNotSubstitutedForANamedCallerCookieWithAnUnusualValue (2026-10-16 repair) | Store holds `SID=storeval`; the caller sends `SID=user"B; x=1` and then `SID=user B; x=1`, each on a fresh client. An exception is accepted. Every request that reaches `/first` must contain no `storeval` and must contain `x=1` | "This holds whatever value, in whatever syntax, the caller gives a cookie. A client that cannot send a caller's header may fail the request instead, but it must never send a stored cookie in place of one the caller named." `x=1` present: "Every cookie the caller puts in a request's `Cookie` header(s) is delivered" | low (the repair's contract is kept: the "named cookie wins" property for any value, and the refusal form "may fail the request") |
| SecurityTests::multipleCallerCookieHeadersAreNotReplacedByTheStore | The caller adds two `Cookie` headers (`a=1`, `b=2`); store holds `SID`; the request carries both `a=1` and `b=2` | "Every cookie the caller puts in a request's `Cookie` header(s) is delivered" (the plural covers several headers) | low |
| FunctionalTests::storeCookieIsDeliveredWhenTheCallerSetsNoHeader | No caller header; the stored `SID=storeval` is sent | "The cookie store works as today: with no caller header it sends its cookies" | low |
| FunctionalTests::aRequestListCookieIsDelivered | A cookie added through the request-cookie API (`addCookie`) is sent | "Cookies added through the client's request-cookie API are still sent." | low |
| FunctionalTests::aCallerHeaderIsDeliveredVerbatimWhenNoStoreCookieCompetes | Empty store; caller sets `Cookie: only=1`; the server receives exactly `only=1` | "A caller's `Cookie` header is sent exactly as written when the store holds nothing for that origin." | low |
| FunctionalTests::aSessionTheServerRotatesOnARedirectWins | Caller sets `SID=old`; the 302 response sets `SID=rotated`; the redirect target receives `SID=rotated` and no `SID=old` | "When the server sets a new value for a cookie in a response during the call (a session rotation), the requests the client then issues automatically to continue the call carry that new value, not the value the caller started with." The security bullet limits itself to cookies "the store already held before the call", so the two rules do not conflict | low |
| FunctionalTests::aSessionTheServerRotatesOnAnAuthChallengeWins | Caller sets `SID=old`; the 401 response sets `SID=rotated`; exactly 2 requests; the retry carries `SID=rotated` | Same rotation sentence; two requests: "Everything else about how requests are sent and continued behaves exactly as today" | low |
| FunctionalTests::theStoreCookieIsStillDeliveredAlongsideACallerHeader | Store holds `SID` and `tracking`; caller sets `session=mine`; the request also carries `tracking=xyz` | "next to a caller header it still adds the stored cookies whose names the caller did not set" | low |

The rotation tests go through the same automatic continuation paths as the two medium-risk security
tests, so the preservation side tells the agent the same thing: rotations during the call must win.
The 2-request count in both auth tests is the client's current behaviour, kept by the preservation
clause.

## Details removed from the old instruction

- The heading "Cookie header replaced by the client's stored session" (it named the mechanism: replacement of the header by the store's cookies).
- "the request actually sent on the wire does not carry the session we set. Instead it carries a session value the client had stored earlier": the old text described the replacement mechanism. The new text states only the observed impact (the wrong session reached the server).
- The "How to reproduce" section and its three steps (seed the store with a prior Set-Cookie request, set the header, use a server that echoes the `Cookie` header).
- The named follow-up variants: "when it follows a redirect to the same origin, and when it retries after an authentication challenge". They are replaced by "requests it issues automatically to continue it".
- "on the first request and on any automatic follow-up request" (it listed the request phases).
- "it may still add its own cookies to a request, including alongside a caller-set header": this is kept as a contract, but reworded to "adds the stored cookies whose names the caller did not set".
- "a session that the server rotates during a redirect or an authentication exchange": this is kept as a contract, but redirect and authentication are no longer named ("in a response during the call").
- The term "cross-account authentication failure" (it named the weakness class). The impact is now given only as "authenticated as the wrong user".

## Added

- The standard constraints block (fix the behaviour and its close variants, keep legitimate use, do
  not modify or add tests, do not look up the upstream fix, do not special-case the example). The old
  instruction had none.
- Contracts that the old instruction left implicit and the tests check: the verbatim delivery of a
  caller header when the store is empty (functional test), the request-cookie API (functional test),
  and the repair's "any value, any syntax; may fail the request instead" wording. Under the old
  instruction the repair test relied on the general "the caller's value is the one that must be sent"
  sentence. The new instruction states it outright. It does not say which syntax is unusual or why.

## Kept on purpose

- The environment block, including the Maven build command and its `-pl client` module name. This is
  a how-to-run fact and is not a hint about the location of the flaw.
- The `Cookie` header and the `SID=` example in the report, as the single allowed trigger.
- The fact that the client's default configuration keeps a cookie store. This is needed because the
  flaw requires the store, and it is user-visible.

No test needed a restated hint beyond the minimum above. The "whatever syntax" clause is the least
wording that keeps the 2026-10-16 repair test fair.
