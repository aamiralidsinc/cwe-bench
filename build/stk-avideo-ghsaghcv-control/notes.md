# stk-avideo-ghsaghcv-control build notes

Control of `stk-avideo-ghsaghcv` (`manifest.control_of`). It isolates one concept — a browser
frame carrying an executable value is relayed unchanged and the recipient page runs it (three
carriers, claimed-sender variants, both addressing modes) — using the same verifier harness as
the stacked task.

## 2026-10-24 audit fix (`build/AUDIT-FIX-20261024.md`)

Applied the audit's Required changes 1–3.

- `tests/support/caller_harness.js`: the `jq()` stub now models jQuery for `text()`/`html()`.
  `.text(v)` stores text and chains; `.text()` reads it back; `.html()` with no argument returns a
  string, HTML-escaping text that was set as text (`& < > " '` -> `&amp; &lt; &gt; &quot; &#39;`);
  `.html(v)` stores markup and chains. `text()` after `.html(v)` returns the text a browser would
  extract (tags dropped, basic entities decoded). Every other stub method is unchanged.
- Verified with node against the pinned `plugin/WebRTC/call/caller.js`: a client-side fix written
  as `$('<span>').text(userIdentification).html()` now yields the escaped string
  (`&lt;img src=x onerror=globalThis.__pwned=1&gt;`, a string) instead of a stub object; with the
  reference payload (authenticated name `Attacker`) it yields `Attacker`, i.e. the heading is a
  plain string.
- No test assertion, reference fix or instruction.md sentence changed (the audit requires this).
  The control's two suites never call `ServerHarness::caller()`, so nop and oracle rewards are
  unchanged; the fix is carried because the control ships the same harness file as the stacked
  task, whose identity and call-notice tests do drive it.

## Verdict

Same as the audit: the defect was a harness test-fault, not a model failure. Nothing in the
control's instruction or tests changed, so no manifest trap, leak term or patch_check changes are
needed.

## Gate (2026-10-24, after the change; one stage at a time)

- static: PASS
- nop: PASS (6 security fail / 5 functional pass)
- oracle: PASS (3/3 runs reward 1.0, 11/11)
- patches: PASS (control_malformed_identity.patch security_fail 0.6667; control_overbroad.patch
  functional_fail 0.0; control_pass_hardening.patch pass 1.0)
- `blind.patch` is still absent and wired separately.

## Stacking checks

`manifest.json` has no `stacking` block: this is the single-concept control of a stacked task, so
the stacked addendum (S1–S7) does not activate. Assessed for the one concept anyway:

- S1 coupled traps: `FuncMessageTest::testServerGeneratedUiUpdateIsDelivered` and
  `testServerGeneratedPayloadIsNotAltered` are covered by "Notices the platform's own server code
  sends still reach the recipient and still take the effect they take today ... whatever account
  they are sent under"; security property 1 speaks only of what "a visitor's browser supplies",
  so no security rule read literally forbids those values.
- S2 shape traps: the refused carriers (inside the message object, in the payload beside the
  text, at the top level, or with a claimed sender) are all client-supplied executable values;
  none is described as legitimate by a keep-working clause, example or fixture.
- S3 fixtures and harness: every suite drives the real `onOpen`/`onMessage` entry points; the
  server-generated fixtures send through a token the service itself issued, which is the
  provenance rule the instruction states.
- S4 concept independence: one concept only; a correct fix passes all its tests.
- S5 history: no `checks/upstream_first_fix.patch` exists for the control (the advisory route is
  the bug); not applicable.
- S6 contracts: the tests read product fields the solver can see in the repository; the
  instruction introduces no field or function name the solver must guess.
- S7 decisive tests: no model trial of this control exists (`trial_summary.md` absent); not
  applicable.
