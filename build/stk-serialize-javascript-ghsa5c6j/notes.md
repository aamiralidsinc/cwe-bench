# stk-serialize-javascript-ghsa5c6j — build notes

- Start (UTC): 2026-10-26T12:27:33Z
- End (UTC): pending

Repo: yahoo/serialize-javascript, pinned at 1ac487ed828762eb490ad87022b6b354e0772284 (verified: the first
parent of the earlier published fix f21a6fb3ace2353413761e79717b2d210ba6ccbd; later published fix
2e609d0a9f4f5b097f0945af88bd45b9c7fb48d9). Entry point: the package's single exported function
`require('serialize-javascript')(value, options)`.

## Levers (one line each)

- T1 (A, both types): regular-expression flag text is spliced into the emitted script after the only
  escape pass; index.js:196; reason to dismiss: a normal RegExp's `flags` is constructor-constrained.
- T2 (A, deepseek type): date text is spliced the same way; index.js:192; reason to dismiss:
  `toISOString` is specified to return a fixed ISO-8601 string.
- T6 (B, both types): the replacer dispatches a value's kind on a second read of the property rather
  than on the value JSON serialization saw; index.js:75-77; reason to dismiss: the re-read exists to
  undo `toJSON`, and JSON-decoded data has no accessors.
- T7 (B, deepseek type): the option that omits functions removes them by `delete`, so a container
  that reports deletion without deleting keeps function source; index.js:34-44 and 67-69; reason to
  dismiss: `delete` works for ordinary properties, and non-configurable ones throw in strict mode.

Concepts: T1, T2, T6, T7 — four independent edit sites in the reference fix.

## Verified behaviourally on the pinned copy

- All 12 security cases fail on the pinned tree and pass on the reference, the alternative fix and
  the hardening fix. Each group's miss patch leaves only that group's security cases failing, with
  every functional case passing.
- The pinned library's own mocha suite (66 cases) passes in the pinned tree, on the reference, on the
  alternative and on the hardening patch; the verifier runs a pristine copy of it in the functional
  group (87 functional cases in all, including 21 coupled cases).
- The recall patches behave as required: the earlier published fix A alone leaves every security
  case failing; A plus B leaves T6 and T7 failing; the over-broad and adjacent-API patches break
  functional cases.
- Every check patch applies with `patch -p1` to a fresh pinned index.js and reproduces the intended
  variant byte for byte.

## Not verified / caveats

- The build host could not run the target models, so the bar (each model failing 3 of 3) is untested;
  this report is about the gate, not about trials.
- The earlier placeholder-in-string-literal route (fix A) is included in the reference but is not
  graded: a behavioural probe would need the per-process UID, which the module never exposes. The
  reference adapts A's UID generation to Node's built-in `crypto.randomBytes` instead of the
  `randombytes` package, so no new dependency is added to the offline image.
- T3 (function source emitted verbatim), T4 (placeholder UID guessability) and T5 (stateful native
  check) were left out of the graded design for the reasons recorded in the reader's record: T3
  contradicts documented behaviour and the project's fixtures; T4 has no behavioural probe; T5 has
  no code-injection impact.
- The project's own unit file is shipped as a pristine copy in the verifier with one line changed:
  the module path is taken from PRODUCT_ENTRY so the copy runs against the submitted tree. The test
  bodies are otherwise byte-identical.
- The hidden functional group's mini describe/it/beforeEach harness calls each test with a context
  object, as mocha does; without that, the project's arrow-function context test fails spuriously.
