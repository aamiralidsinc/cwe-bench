# Fairness review — stk-avideo-ghsaghcv

Read: `instruction.md`, every `tests/` file, `solution/fix.patch`, `manifest.json`, `notes.md`, `checks/*.patch`. Nothing was run.

**Revision 2026-10-24 (AUDIT-FIX-20261024.md).** The post-run audit found one test-fault: `tests/support/caller_harness.js` stubbed jQuery's `text()`/`html()` so both returned the stub object, so a correct fix that escapes the caller name on the client with the standard idiom `$('<span>').text(name).html()` produced an object and the six identity/functional heading tests failed. The harness now models jQuery: `text(value)` stores text and chains, `text()` returns it, `html()` returns the stored text HTML-escaped as a string (`&`, `<`, `>`, `"`, `'`), `html(value)` stores markup and chains, and the element's `textContent`/`innerHTML` expose the same content. No test assertion, reference fix or instruction sentence changed. The pinned code still fails every security test and the reference still passes everything (gate below).

**Covering text.** **P1**/**P2** are the two numbered property paragraphs (quoted in fragments below); **K1**–**K5** are the five "What must keep working" bullets in order; **G** is "The examples above are examples, not the full set... keep legitimate use working exactly as today."

## 1. Per-test fairness

| Test | Asserts | Fair because | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/SecAutoEvalMessageTest.php::testBrowserPayloadInMessageIsNotRelayed | victim receives a frame; relayed payload has no `autoEvalCodeOnHTML` in the message object | P1 "wherever in a frame the value is carried"; K2 keeps the frame flowing | no | low |
| security/SecAutoEvalMessageTest.php::testBrowserPayloadInJsonCarrierIsNotRelayed | same when the value sits in the object carried beside the text | P1 same phrase | no | low |
| security/SecAutoEvalMessageTest.php::testBrowserPayloadAtTopLevelIsNotRelayed | same at the top of the frame | P1 "wherever"; "however the frame is addressed" | no | low |
| security/SecAutoEvalMessageTest.php::testRelayedBrowserPayloadDoesNotExecuteOnRecipient | the platform's client, run on the delivered frame, does not execute it | P1 "may cause any other page to execute code" | no (a client-layer fix also passes) | low |
| security/SecAutoEvalMessageTest.php::testSenderClaimsDoNotBypassTheCheck | `isCommandLine`, `sentFrom`, `msg.isCommandLineInterface` in the frame body do not exempt it | K3 "decided by what the service issued, not by anything written inside the frame"; K2 bars whole-frame refusal | no | low |
| security/SecAutoEvalMessageTest.php::testEveryTargetedRecipientIsProtected | account-targeted delivery is filtered and still delivered | P1 "however the frame is addressed"; K1 | no | low |
| security/SecAutoEvalV2Test.php::testBrowserPayloadInMessageIsNotRelayed | same, default SQLite implementation | P1 speaks of "the socket service", not one class; G; standard expert knowledge: the host loads this class by default | no (only a one-class fix fails — a wrong fix) | low |
| security/SecAutoEvalV2Test.php::testBrowserPayloadInJsonCarrierIsNotRelayed | same | as above | no | low |
| security/SecAutoEvalV2Test.php::testBrowserPayloadAtTopLevelIsNotRelayed | same | as above | no | low |
| security/SecAutoEvalV2Test.php::testRelayedBrowserPayloadDoesNotExecuteOnRecipient | same | as above | no | low |
| security/SecAutoEvalV2Test.php::testSenderClaimsDoNotBypassTheCheck | same | K3; K2 | no | low |
| security/SecAutoEvalV2Test.php::testEveryTargetedRecipientIsProtected | same | P1; K1 | no | low |
| security/SecCallbackMessageTest.php::testCallerChosenCodeIsNotExecuted | an expression as the applied function name does not execute on the recipient | P1 "the name of a function the receiving page would apply, except for the ordinary application functions the site's own pages define" | no | low |
| security/SecCallbackMessageTest.php::testBuiltInFunctionNameIsNotUsedAsCallback | `setTimeout` plus a string message does not execute | P1 same exception clause: a built-in is not an application function | no (a server-only shape check fails — wrong fix) | low |
| security/SecCallbackMessageTest.php::testArrayShapedFunctionNameIsNotUsedAsCallback | an array that stringifies to a built-in name does not execute | P1 covers the effect (the page would apply `setTimeout`), whatever the shape | no | low |
| security/SecCallbackV2Test.php::testCallerChosenCodeIsNotExecuted | same on the default implementation | P1; G | no | low |
| security/SecCallbackV2Test.php::testBuiltInFunctionNameIsNotUsedAsCallback | same | P1 | no | low |
| security/SecCallbackV2Test.php::testArrayShapedFunctionNameIsNotUsedAsCallback | same | P1 | no | low |
| security/SecIdentityMessageTest.php::testSpoofedSenderAccountDoesNotChooseTheOtherName | heading is a string, holds no `<` and no `onerror` when the frame claims the recipient's account | P2 "which of the two parties' details it presents... never a value written into the frame"; K5 bars dropping the notice | no — a client-side `$('<span>').text(x).html()` escape now yields a string (harness revised 2026-10-24) | low |
| security/SecIdentityMessageTest.php::testSenderSuppliedNameIsNotShown | heading carries no markup | P2 "never a value written into the frame; and no name may be presented in a way the receiving page interprets as markup" | no — same harness revision; escaping the authenticated name yields that name | low |
| security/SecIdentityMessageTest.php::testAnonymousSenderCannotImpersonate | an unauthenticated sender's notice is not shown as the claimed account | P2 "must reflect the authenticated sessions" | no | low |
| security/SecIdentityV2Test.php::testSpoofedSenderAccountDoesNotChooseTheOtherName | same, default implementation | P2; G | no — client-escape idiom now yields a string (harness revised 2026-10-24) | low |
| security/SecIdentityV2Test.php::testSenderSuppliedNameIsNotShown | same | P2 | no — same harness revision | low |
| security/SecIdentityV2Test.php::testAnonymousSenderCannotImpersonate | same | P2 | no | low |
| functional/FuncMessageTest.php::testOrdinaryMessageIsDeliveredIntact | text and nested metadata arrive unchanged | K1 | no | low |
| functional/FuncMessageTest.php::testDirectTargetingByConnection | connection-targeted frame arrives | K1 "whoever they are addressed to" | no | low |
| functional/FuncMessageTest.php::testDirectTargetingByAccount | account-targeted frame arrives | K1 | no | low |
| functional/FuncMessageTest.php::testLegitimateFunctionNameIsRelayedAndRuns | `incomeCall` stays in the frame and the client calls it once | K4 | no | low |
| functional/FuncMessageTest.php::testServerGeneratedUiUpdateIsDelivered | a server-token frame keeps its field and the client applies it | K3 "still take the effect they take today, including the small screen updates" | no under the primary token-provenance fix; maybe for a guard scoped to the opened connection | medium |
| functional/FuncMessageTest.php::testServerGeneratedPayloadIsNotAltered | server payload data and field unchanged | K3 "whatever account they are sent under" | no under the primary fix; same caveat | medium |
| functional/FuncMessageTest.php::testLegitimateCallShowsAuthenticatedSenderName | heading is exactly `Alice` | P2 "authenticated sessions"; K5 "the caller's real name" | no under the primary fix (token `user_name`, the pattern already in the file); the client-escape idiom now yields `Alice` (harness revised 2026-10-24); maybe if re-derived from the user table (the bootstrap stub returns `user7`) | medium |
| functional/FuncV2Test.php::testOrdinaryMessageIsDeliveredIntact | same as the Message twin | K1; G | no | low |
| functional/FuncV2Test.php::testDirectTargetingByConnection | same | K1 | no | low |
| functional/FuncV2Test.php::testDirectTargetingByAccount | same | K1 | no | low |
| functional/FuncV2Test.php::testLegitimateFunctionNameIsRelayedAndRuns | same | K4 | no | low |
| functional/FuncV2Test.php::testServerGeneratedUiUpdateIsDelivered | same | K3 | no under the primary fix; same caveat | medium |
| functional/FuncV2Test.php::testServerGeneratedPayloadIsNotAltered | same | K3 | no under the primary fix; same caveat | medium |
| functional/FuncV2Test.php::testLegitimateCallShowsAuthenticatedSenderName | same | P2; K5 | no under the primary fix; client-escape idiom now yields a string (harness revised 2026-10-24); same caveat | medium |
| functional/FuncClientTest.php::testServerGeneratedUiScriptRuns | the client still applies a server UI frame | K3 "the small screen updates recipient pages apply" | no (removing it is the over-broad wrong fix) | low |
| functional/FuncClientTest.php::testOrdinaryFunctionNameRuns | `incomeCall` runs once, no error | K4 | no | low |
| functional/FuncClientTest.php::testUnknownFunctionNameFallsBackToDefault | unknown name runs nothing and raises nothing | G "exactly as today" (the visible existing fallback) | no | low |
| functional/FuncClientTest.php::testMessageWithoutFunctionNameDoesNotError | no callback runs nothing, no error | G | no | low |

## 2. Leniency (quality, non-blocking)

| Trap / property | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 / P1 | strip only the obvious sub-key | yes — `SecAutoEvalMessageTest::testBrowserPayloadInJsonCarrierIsNotRelayed` + `::testBrowserPayloadAtTopLevelIsNotRelayed` (and V2 twins); `checks/sf-msg-carrier-only.patch` (4 security fails), `checks/miss_executable.patch` |
| T2 / P1 | fix only the in-memory class | yes — the six `SecAutoEvalV2Test` tests; `checks/miss_executable_relay.patch` (12 security fails) |
| T3 / P1 | same as T1 | yes — same tests and patch |
| T4 / P1 | delete the client eval, or strip every sender | yes — `FuncClientTest::testServerGeneratedUiScriptRuns`, `FuncMessageTest`/`FuncV2Test::testServerGeneratedUiUpdateIsDelivered`; `checks/ff-remove-client-eval.patch`, `checks/ff-strip-all-senders.patch` |
| T4 / K3 | trust the frame's own `isCommandLine`/`sentFrom` | yes — `SecAutoEvalMessageTest`/`SecAutoEvalV2Test::testSenderClaimsDoNotBypassTheCheck` (no check patch exists; tighten) |
| T5 / P1 | server-side identifier check only | yes — `SecCallbackMessageTest`/`SecCallbackV2Test::testBuiltInFunctionNameIsNotUsedAsCallback`; `checks/miss_callback.patch` |
| T5 / P1 | unanchored identifier regex | yes — the expression and array tests; `checks/sf-loose-callback-match.patch` (4) |
| T7 / P2 | rewrite the recipient's field instead of the sender's | yes — `::testSenderSuppliedNameIsNotShown`; `checks/sf-check-recipient-identity.patch` (4) |
| T7 / P2 | skip enforcement for an anonymous sender | yes — `::testAnonymousSenderCannotImpersonate`; `checks/sf-fail-open-anonymous.patch` (2) |
| T7 / P2 | escape the heading only | yes — `::testSenderSuppliedNameIsNotShown`: escaping keeps the literal `onerror` |
| T7 / P2 | enforce only one of the two identity fields | yes — the spoofed-account and sender-name tests fail respectively |

Wrong fixes no test catches: sanitize/rewrite only `from_identification` and strip markup everywhere, leaving caller-controlled `from_users_id` (all six identity tests pass; the spoofed heading becomes `''`); null out the forbidden payload instead of removing the key (the security tests only require that something was sent); enforce identity only for the fixture's callback; allowlist only the two known names (`testUnknownFunctionNameFallsBackToDefault` still passes); drop anonymous calls entirely (a null heading passes `assertNotSame`).

## 3. Hints (quality, non-blocking)

| Quote | Why | Neutral wording |
|---|---|---|
| "Its live pages — chat, viewer counts, watch-together, incoming-call notices — stay in sync through a socket service." | Surface list naming the call-notice route (T7). **Required: generalize** | "Its live pages stay in sync through a socket service." |
| "the service relays small JSON frames between connected pages: to one connection, to one account, or to everyone connected." | Variant list of addressing modes (T1/T3). **Required: generalize** | "the service relays small JSON frames between connected pages." |
| "including making a call appear to come from an account that is not the sender's" | Enumerates the role-selection sub-case (the wrong-object half of T7). **Required: generalize** | state only that a page may present identities the sender chose rather than the authenticated ones |
| "Whether a frame is the platform's own is decided by what the service issued, not by anything written inside the frame." | Paraphrases the fix approach; also the contract T4 needs. Keep, but state as a property: "A frame is the platform's own only if the service established that for its sender; nothing written in the frame can make it so." | |
| "including the small screen updates recipient pages apply" | Names the coupled value's effect (T4); K3 needs it. Keep; "including the effects recipient pages apply in response" is slightly more general | |
| "the name of a function the receiving page would apply, except for the ordinary application functions the site's own pages define" | Names the callback mechanism and the exception rule (T5); needed for fairness and K4 — keep | |

No flaw count appears.

## 4. Realism (quality, non-blocking)

- T1, T3, T4, T5, T7 are the product's own code on the real `onOpen`/`onMessage` path; T2 is real, unmodified upstream code the host loads by default. None is planted.
- T4's legitimate value is real: PHP senders sign `sentFrom='php'` and the live page applies the field.
- One synthetic element: both server-generated fixtures send a server token over a browser-token connection. A real PHP sender opens its own connection, so a connection-scoped guard cannot pass these fixtures although it would work in production.
- The client harness's native-code stand-in matches real browser behaviour; the note records the inherited harness fixes.

## 5. Stacking checks

Concepts (manifest.stacking): **C1** = T1+T2+T3+T4 (executable payload relay and provenance); **C2** = T5 (function-name execution); **C3** = T7 (authenticated call identity). One row per check per concept.

| Check | Concept | Finding | Gate a |
|---|---|---|---|
| S1 coupled traps | C1 | The must-keep values are quoted by K1 ("Ordinary frames ... still arrive intact"), K2 ("the rest of its content delivered, and the connection stays open"), K3 ("Notices the platform's own server code sends ... still take the effect they take today ... whatever account they are sent under") and K4 ("ordinary application functions"). P1 read literally is limited to "Nothing a visitor's browser supplies", so no security rule forbids a server-issued value. No contradiction: a correct fix can satisfy both sides. | pass |
| S1 coupled traps | C2 | K4 ("A message that names one of the page's ordinary application functions still runs that function") is quoted; P1 excludes exactly "the ordinary application functions the site's own pages define". The two clauses agree by their own words; no security rule forbids `incomeCall`. | pass |
| S1 coupled traps | C3 | K5 ("Incoming calls still ring: the notice reaches the recipient with the caller's real name shown as plain text, and a call may be started from either party's account") plus K2 cover the coupled values; P2 requires only that the presented identity reflect "the authenticated sessions", which the same clause permits. No contradiction. | pass |
| S2 shape traps | C1 | Refused shapes are the three carriers of the executable value and a caller-written provenance claim; none is inside the legitimate set described by K1–K3 or by any example/fixture (ordinary `msg` text, a plain `json` payload, a server-issued frame). Legitimate ordinary frames are never refused. | pass |
| S2 shape traps | C2 | Refused shapes are an expression, a built-in function name and an array that stringifies to a name; the stated legitimate set is "the ordinary application functions the site's own pages define", so every refused shape lies outside it. | pass |
| S2 shape traps | C3 | Refused shapes are a frame-chosen recipient/sender name, markup in the name, and an anonymous claim to another account; the stated legitimate set (a signed-in caller's own real name, either party starting the call) never includes them. | pass |
| S3 fixtures and harness | C1 | Both server implementations are states the product itself loads (one is the default when pdo_sqlite exists), and the server token is minted exactly as the platform's token endpoint mints it; the suites call the real `onOpen`/`onMessage`. Caveat recorded: the server-generated fixtures ride a browser-token connection (see Verdict), which only a connection-scoped guard would mind. | pass (caveat) |
| S3 fixtures and harness | C2 | The suites run the platform's own `script.js` under Node; the stand-in timer reports itself as a browser built-in while still executing a string, matching the real page. Real entry point, real script. | pass |
| S3 fixtures and harness | C3 | The suites run the platform's own `caller.js` through `incomeCall`; `test.sh` restores the agent's `/workspace`, so the browser script is the submitted one. The harness now models jQuery's `text()`/`html()` getters/setters (2026-10-24), so both the reference (plain string) and a correct client-side escape produce the recipient-visible string. Fixtures use legitimate states (a public page token, signed-in users 7 and 42). | pass |
| S4 concept independence | C1 | `checks/miss_executable_relay.patch` leaves C2 and C3 unfixed: 12 C1 security tests fail, 0 functional. A correct C1 fix passes all C1 tests whatever C2/C3 do. Masking (H3c) does not apply (pattern H3a). | pass |
| S4 concept independence | C2 | `checks/miss_callback.patch` leaves C1 and C3 unfixed: 6 C2 security tests fail, 0 functional; a correct C2 fix passes them independently. | pass |
| S4 concept independence | C3 | `checks/miss_identity.patch` leaves C1 and C2 unfixed: 6 C3 security tests fail, 0 functional; a correct C3 fix passes them independently. The C3 security tests fail through their own route (`incomeCall` heading) on the pinned tree, through the test-fault the audit found. | pass |
| S5 history | C1 | `checks/upstream_first_fix.patch` (advisory A alone) strips only the message sub-key and only a top-level callback, so a value in the beside-the-text object or at the frame top level still reaches the recipient: it violates P1 "wherever in a frame the value is carried" read literally, not merely differs from the reference. | pass |
| S5 history | C2 | The same first fix refuses only a non-identifier callback; a plain built-in name (`setTimeout`) remains, which P1's exception ("except for the ordinary application functions the site's own pages define") read literally forbids. | pass |
| S5 history | C3 | Both advisories' fixes (A and A+B) leave the identity tests failing: the caller-written `from_users_id`/`from_identification` still reach the notice, violating P2 ("never a value written into the frame"). No dependency bump; the reference proves an in-repo fix. | pass |
| S6 contracts | C1 | Every field the tests use is the product's own (`msg`, `json`, `callback`, `resourceId`, `to_users_id`, the encrypted token); nothing has to be guessed. The authority for the fail-open case is stated: whether a frame is the platform's own is "decided by what the service issued". | pass |
| S6 contracts | C2 | The callback name is the product's own field, and the permitted class is named in product terms ("the ordinary application functions the site's own pages define"). | pass |
| S6 contracts | C3 | The protected object is named in product terms ("a call notice", "the caller", "the name and account a recipient sees"). The authority is stated (the authenticated sessions / what the service issued). | pass |
| S7 decisive tests | C1 | `build/stk-avideo-ghsaghcv/trial_summary.md` does not exist; the post-run audit instead names the six deciding tests, all in C3 (see next row). C1 was not decisive. | n/a |
| S7 decisive tests | C2 | No trial summary; the audit does not name a C2 test as deciding a run. | n/a |
| S7 decisive tests | C3 | The 2026-10-24 post-run audit (`AUDIT-FIX-20261024.md`) attributes the failed deepseek-r1 run to six tests — `SecIdentityMessageTest`/`SecIdentityV2Test::testSpoofedSenderAccountDoesNotChooseTheOtherName` and `::testSenderSuppliedNameIsNotShown`, plus `FuncMessageTest`/`FuncV2Test::testLegitimateCallShowsAuthenticatedSenderName` — which failed a correct client-side escape through the harness, not the fix. Re-checked against S1–S6: S1/S2 pass (the values are legitimate), S6 passes (the heading option is the product's own toast API); the defect was S3's harness. Fixed by the harness revision; these tests now pass both the reference and a client-escape correct fix. `NEEDS_HUMAN_REVIEW: YES` stands for the separate connection-scoped-guard judgment below. | pass (fixed) |

## Verdict

**READY.** No test contradicts the instruction or a keep-working bullet, and every assertion follows from P1/P2/K1–K5 or the repo's own code. The reference and the delivery-layer alternative pass 42/42; the pinned copy fails 24/24 security with 18/18 functional. The two "maybe" rows share one judgment: a correct alternative that decides provenance from the opened connection, or re-derives the display name from the user table, would fail the T4/identity fixtures. The instruction's primary mechanism — provenance and identity from the decrypted token, matching the existing rewrite — passes everything, so under the primary-mechanism rule these are quality/human-review items, not unfairness.

**Required: generalize** → the three rows marked in §3.

**Quality to tighten** →
1. `testSpoofedSenderAccountDoesNotChooseTheOtherName` (both): assert the heading is the authenticated sender's name (`Attacker`) — closes the sanitize-only wrong fix.
2. `SecAutoEval*` non-execution tests: assert the ordinary `text`/`stats` survives, enforcing K2.
3. Add a `security_fail` check patch for trusting frame-supplied provenance.
4. Identity: exercise a frame carrying identity fields under a different callback.
5. `FuncClientTest`: exercise a second page-defined function name.
6. Decide whether an anonymous caller's notice must ring; if yes, add a functional test.
7. T4 fixtures: open the server token's own connection, or record the shortcut.
8. Apply the three generalizing rewrites.

**Human review:** confirm a connection-scoped provenance guard need not pass; if it must, the T4 fixtures need a server-opened connection.

**2026-10-24 audit-fix re-run.** The one test-fault in `AUDIT-FIX-20261024.md` is fixed in the caller harness (jQuery `text()`/`html()` and DOM-property semantics); no assertion, reference or instruction sentence changed. Direct probe of the shipped harness: `$('<span>').text('Alice').html()` → `"Alice"`, `$('<span>').text('<img src=x onerror=…>').html()` → the escaped string. Gate on the final tree: static PASSED; nop PASSED (24/24 security fail, 18/18 functional pass); oracle PASSED (3 runs, reward 1.0, 42/42 each); patches PASSED (15/15 as declared, including `pass-hardening` with its own client-side escape at 1.0). The verdict is unchanged.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
