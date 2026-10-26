# FAIRNESS — stk-avideo-ghsawc3f

Legend — **INV**: "No client-supplied value may make the separate media host run any program other
than the media command the request describes, and no such value may start, extend or replace that
command with other shell work." **REF**: "A request whose values cannot be run safely must not run
the unsafe part. It may be refused with a client error." **KEEP**: "Everything that works today
keeps working exactly as it does today, and every legitimate input the system accepts today is
still accepted."

## 1. Per-test fairness

| test (file::name) | what it asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/CommandShellTest.php::testSeparatorCannotStartAnotherCommand | endpoint answers (JSON or ≥400); no marker after command text with `& touch` | INV — "no such value may start, extend or replace that command with other shell work"; a client supplies the command text | no — quote-aware stripping, escaping or a JSON/4xx refusal all pass; guard at dispatcher, sanitizer or exec wrapper all reach it | low |
| security/CommandShellTest.php::testCommandSubstitutionCannotStartAnotherCommand | no marker from `$(touch …)` in command text | INV — expansion is "other shell work" | no — reference removes `$`, `(`, `)` everywhere; refusal also passes | low |
| security/CommandShellTest.php::testNewlineCannotStartAnotherCommand | no marker from a newline in command text | INV | no | low |
| security/NotifyValueTest.php::testNotifyCodeCannotStartAnotherCommand | no marker from a notification value beside the job command | INV — "no client-supplied value"; REF's JSON refusal accepted | no — escaping (reference) and allowlisting (alt_fix) both pass | low |
| security/NotifyValueTest.php::testCallbackCannotStartAnotherCommand | same for the second notification value | INV | no | low |
| security/ProcessLookupTest.php::testListLookupValueCannotStartAnotherCommand | no marker from a lookup value in list mode | INV — the lookup value is client-supplied and reaches a shell | no — escaping (reference) or an allowlist returning an empty list (alt_fix) passes | low |
| security/ProcessLookupTest.php::testRunningLookupValueCannotStartAnotherCommand | same in running-state mode | INV | no | low |
| security/RestreamLogTest.php::testUserIdentifierCannotStartAnotherCommand | no marker from a client identifier placed in a log path | INV — restreamer.json.php is under `standAloneFiles` and runs media work on the media host; the identifier is client-supplied | no — stripping, escaping the path, or refusing (alt_fix) all pass | low |
| functional/MediaLegitimateUseTest.php::testOutputRedirectIsRemovedAndTheJobStillRuns | the job runs (`/tmp/in.mp4` in argv); the redirect target is not an argv element | KEEP — today this request is accepted, the redirect tail is dropped and the job runs | no — dropping (today's behaviour, the reference) passes, and honouring the redirect also passes because a shell redirect never enters argv; refusing the request would fail, but that breaks KEEP, so it is not a correct fix | medium |
| functional/MediaLegitimateUseTest.php::testQuotedPathsWithSpacesArePreserved | quoted paths arrive as single argv elements | KEEP — quoted paths are accepted today; quoting is not "other shell work" | no — only over-broad quote stripping fails, and that refuses a value accepted today | low |
| functional/MediaLegitimateUseTest.php::testPrintableStatusValuesArriveIntact | base64 notification values arrive unchanged | KEEP — accepted today; `+` and `=` are data, not shell work | no | low |
| functional/ProcessLookupFunctionalTest.php::testListOfRunningJobsAnswers | list request returns a JSON `list` array | KEEP | no | low |
| functional/ProcessLookupFunctionalTest.php::testRunningStateAnswers | running-state request returns JSON `isRunning` false | KEEP | no | low |
| functional/RestreamFunctionalTest.php::testRestreamForAWebUserStillWorks | restream runs, URL query kept, log file named for `web` | KEEP — `web` is accepted today; the identifier is data, not shell work | no — sanitized id is unchanged and escaping the path keeps the filename; hashing or refusing `web` breaks KEEP | low |
| functional/RestreamFunctionalTest.php::testRestreamForANumericUserStillWorks | same for `4242` | KEEP | no | low |
| project/FunctionsFFMPEGTest.php (22 methods, 50 cases with providers) | upstream suite for the callback helpers | standard expert knowledge: the project's own suite must keep passing / KEEP | no — the reference and alt_fix touch none of these callbacks and score 1.0 | low |
| project/NotifyFFmpegTest.php (21 methods) | upstream suite for the callback endpoint | standard expert knowledge / KEEP | no | low |

## 2. Leniency (quality)

| trap / property | most plausible WRONG fix | caught? |
|---|---|---|
| T1 separator | add `&` to the character blacklist | testSeparator catches the injection but nothing catches the over-broad deletion of `&` inside legitimate quoted values (the media quoted-URL test was removed — notes.md "Rebuild decision"); **not caught** |
| T1 separator | escape only the exec wrapper (`functionsExec.php`) and leave the command text | caught: testSeparator (marker still runs); `checks/miss_command_shell.patch` 0.625 |
| T2 substitution/newline | add `$`, `(`, `)`, newline to the blacklist but leave `&` | caught: testSeparator; `checks/upstream_first_fix.patch` (0.25) |
| T2 | escape the wrapper only | caught: testCommandSubstitution / testNewline |
| T3 notifications | escape `notifyCode` only, leave `callback` | caught: testCallbackCannotStartAnotherCommand; `checks/miss_callback_only.patch` 0.875 |
| T3 | strip `;` from both notification values | **not caught** — no `$(…)`/newline shape is sent through either field |
| T4 lookup | fix the job path, leave `listFFmpegProcesses` raw | caught: both ProcessLookup tests; `checks/miss_keyword.patch` 0.75 |
| T4 | strip `;` only from the keyword | **not caught** — the single-quoted grep shape is neutralised, but a `$(…)` or newline keyword is not exercised |
| T5 restream | escape the log path but leave the identifier raw | caught: testUserIdentifierCannotStartAnotherCommand; `checks/miss_restream.patch` 0.875 |
| T5 | strip `;` only from the identifier | **not caught** — `$(…)`/quote shapes in `users_id` are not exercised |
| T6 coupled values | strip every quoting character | caught: testQuotedPathsWithSpacesArePreserved; `checks/func_overbroad.patch` 0.0 |
| T6 | deny every media command | caught: all three MediaLegitimateUseTest cases; `checks/refuse_all.patch` 0.0 |
| T6 | strip `&` inside quoted values | **not caught** (same removed media quoted-URL contract as T1) |
| refusal side-effect property | refuse after creating a log file or process | **not caught** — no test checks that a refused request leaves no file/dir/process |

Wrong fixes no test catches: `&`-inside-quotes stripping; `;`-only neutralisation for T3/T4/T5;
refusal side effects.

## 3. Hints (quality)

- "The payload began with a normal FFmpeg invocation, so it looked like an ordinary media job; the
  extra command still ran on the host." — paraphrases the flaw shape (normal prefix plus appended
  program). Drop it; keep only "…can make the host run an unrelated operating system command."
- "no such value may start, extend or replace that command with other shell work" — a variant list.
  Reword: "No client-supplied value may cause any program or shell work to run on the media host
  other than the media command the request describes."
- "Fix the problem and its close variants." → "Fix the underlying problem."
- "Do not special-case the example." → "Do not special-case any particular input."

## 3a. Required: generalize

- "The payload began with a normal FFmpeg invocation, so it looked like an ordinary media job; the
  extra command still ran on the host." — names the command object kind and the flaw's stage shape
  (T1). Reword to the outcome: "We found that a client able to send such a payload can make the host
  run an unrelated operating system command."
- "and runs it as the web user" — "the web user" is also the identity form of a restream fixture
  (`web`). Reword: "and runs it with the web server's privileges."
- "Some installations run a separate media host that the main site drives over HTTP…" is necessary
  context for the protected host, not a route pointer; keep.

## 4. Realism (quality)

| trap | real maintainer code? | real entry point? |
|---|---|---|
| T1 | yes — unmodified upstream sanitizer and wrapper | yes — media HTTP endpoint |
| T2 | yes — the double-quoted `sh -c` wrapper is the product's normal path | yes |
| T3 | yes — server-made base64 values read as trusted beside escaped neighbours | yes |
| T4 | yes — the keyword is sanitised in the job path but not in the lookup | yes |
| T5 | yes — unmodified upstream in another plugin; the log path is appended unquoted | yes |
| T6 | yes — genuine restream/conversion commands carry their own redirect and quoted paths | yes |

Nothing planted; the accepting stand-in is the product's main-site contract.

## 5. Stacking checks

| check | concept | finding | gate a? |
|---|---|---|---|
| S1 | C1 (T1/T2) | keep-working clause = KEEP; the redirect value is not required to take effect, so INV (no shell work) and the test are jointly satisfiable; quoted paths are media arguments | no |
| S1 | C2 (T3) | KEEP covers the base64 values; INV forbids only extra programs/shell work, never `+` or `=` | no |
| S1 | C3 (T4) | KEEP covers `legitkw-1`; no rule forbids the hyphen | no |
| S1 | C4 (T5) | KEEP covers `web`/`4242` and the quoted URL's `&`; no rule forbids them | no |
| S2 | C1–C4 | every refused shape (`&`, `$(…)`, newline, `;`, quote breakout) is outside the legitimate sets shown by the fixtures and by the repo's own keyword sanitisation | no |
| S3 | all | fixtures are legitimate (secret, token, enabled routes); tests drive the real HTTP entry points, and guards at dispatcher, handler or exec helper all pass; only a refusal returning a non-JSON 200 with no body would fail — not a plausible correct form | no |
| S4 | C1 | CommandShellTest passes with only the sanitizer/wrapper change; no cross-concept state | no |
| S4 | C2 | NotifyValueTest passes with only the notification escaping | no |
| S4 | C3 | ProcessLookupTest passes with only the lookup escaping | no |
| S4 | C4 | RestreamLogTest passes with only the restream change | no |
| S4 | H3c | each security test fails on pinned through its own route (nop 8/8; `checks/miss_restream.patch` fails only RestreamLogTest, etc.) | no |
| S5 | H3a | `checks/upstream_first_fix.patch` leaves `&`, so the separator still runs: it violates INV read literally; the property is not too narrow | no |
| S5 | F5 | no dependency bump; an in-repo fix exists (reference scores 1.0) | no |
| S6 | all | the tests use product field names visible in the repo; the protected object is the command line, named in product terms; no fail-open authority interface | no |
| S7 | all | no `trial_summary.md`; three graded mimo runs scored 0.875, so one security test decided each — identity not recorded in build/ | human review |

## Verdict

READY. Every test derives from INV, REF and KEEP, which apply literally to each route without
naming one. Reference, `alt_fix` and `hardening` all score 1.0 and a model solved it. The only
correct-fix-fails candidates — refusing a redirect-bearing request, hashing the restream log name,
a plain-text 200 refusal — violate KEEP or REF, so they are not correct fixes.

Quality to tighten: add `$(…)`/newline shapes to NotifyValueTest, ProcessLookupTest and
RestreamLogTest; assert the full argv in the redirect test (a shell redirect never enters argv);
add a refusal side-effect assertion; restore a media quoted `&` value if the recall expectation can
be relaxed.

Human review: S7 — identify which of the eight security tests decided the three 0.875 mimo runs
(not recorded in build/) and confirm the restream endpoint is recognisably on the media host from
the repository alone.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
