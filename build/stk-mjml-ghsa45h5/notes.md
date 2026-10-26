# stk-mjml-ghsa45h5 build notes

- Start: 2026-10-23T04:59Z (rebuild; the previous build's task tree was missing from `tasks/`, its
  hidden suites were recovered unchanged from the verifier image left by its last gate job,
  `stk-mjml-ghsa45h5__7xp87qb__verifier__trial-main:latest`, and re-verified against the pinned
  tree; one test was corrected to accept a correct refusal instead of requiring a zero exit).
- End: 2026-10-23T07:22Z.
- Track: stacked (H3a), pattern A+B. Slug `stk-mjml-ghsa45h5`; control `stk-mjml-ghsa45h5-control`.
- Pinned: mjmlio/mjml `21034a7187f2bda4b0d66e7a1c63314c88dce71a`, the direct parent of the
  earlier fix A (`30e29ed2cdaec8684d60a6d12ea07b611c765a12`, gh rev-parse `30e29ed2^`). The pinned
  tree is mjml 4.6.2. The later fix B is `517b376b068e71c713ec4bb4ef9e5b0b7235b8ce`.
- Reader record: `stacking/out/reader/h3-ghsa-45h5-66jx-r2wf.json`, re-checked on the pinned tree.

## Levers (one line each)

- **C1 = T1 + T6 (parser confinement; reported route; MiMo-type).**
  `packages/mjml-parser-xml/src/index.js:37-48,69-84,105-115`: an include target is resolved against
  the current parse context and read with no containment. Shapes: relative climb, absolute path,
  prefix-sharing sibling, a link to a file outside the base, and nested partials that climb one
  level deeper. The base must be the configured partials directory carried through the recursive
  parse. One concept: one containment helper plus the carried base.
- **C2 = T4 (CLI watch dependency resolver; DeepSeek-type, pattern B, uncovered upstream).**
  `packages/mjml-cli/src/helpers/fileContext.js:29-41,53-60`: a second, regex-based include
  resolver reads every referenced file and adds it to the watch list. It never puts content in the
  output, which is the reason to dismiss it. Unmodified upstream code; neither published fix
  touches it.
- **C3 = T7 (failure disclosure; DeepSeek-type, uncovered upstream).**
  `packages/mjml-parser-xml/src/index.js:80-95`, `packages/mjml-validator/src/rules/errorAttr.js:8-18`
  and `packages/mjml-validator/src/rules/ruleError.js:18-25`: a failed include writes the resolved
  location into the generated comment and the formatted validator message. A diagnostic, and the
  read already failed, is the reason to dismiss it. Second property (filesystem-location
  disclosure), tested through in-base missing targets.

T6 is the coupled must-keep-working value (configured partials directory, nested sibling above the
partial's own directory); the functional suite keeps it honest.

## What I verified

- Every route reproduces through a real entry point at the pinned commit: `mjml2html`, the public
  parser package, the CLI render (`-s`), validate (`-v`) and watch (`-w`) commands, including
  nested partials, a prefix-sharing sibling and links.
- Local runs (rebuilt tree, `HARNESS_WORKSPACE` pointing at it):
  - pinned: security 0/15, functional 12/12; reference: 15/15 and 12/12;
  - miss_parser 5/15 + 12/12; miss_watcher 14/15 + 12/12; miss_diagnostics 13/15 + 12/12;
  - sf_core_only 2/15 + 12/12; sf_lexical 14/15 + 12/12;
  - ff_refuse_all 12/15 + 2/12; ff_default_off 11/15 + 2/12;
  - upstream_first_fix 0/15 + 12/12; upstream_fix 12/15 + 12/12;
  - pass_alt 15/15 + 12/12; pass_hardening 15/15 + 12/12.
- Project suites pass at pinned and under the reference: `packages/mjml-parser-xml/test/test.js`
  and `packages/mjml-core/tests/index.js` (both part of the hidden functional group).
- `stacking/check_stack.py stk-mjml-ghsa45h5`: conforming (3 concepts, pattern H3a).
- Container gate, run one stage at a time with `builder/gate.py --only`:
  - static: only the expected missing `blind` pass patch (all other static checks pass, including
    leaks, conformance and the wrong-fix catalogue).
  - nop: PASSED. Security 0/15, functional 12/12, reward 0.0.
  - oracle: PASSED. Three runs, reward 1.0 each, identical results. (One attempt was cut by
    Harbor's `network_mode='no-network'` capability-probe flake under the shared VM's load; the
    retry passed.)
  - patches: PASSED. 10/10 as declared: miss_parser 0.3333 (10 security failing, 0 functional),
    miss_watcher 0.9333 (1, 0), miss_diagnostics 0.8667 (2, 0), sf_core_only 0.1333 (13, 0),
    sf_lexical 0.9333 (1, 0), ff_refuse_all functional_fail (3, 10), upstream_first_fix 0.0 (15, 0),
    upstream_fix 0.8 (3, 0), pass_alt 1.0, pass_hardening 1.0. (One attempt hit the same
    capability-probe flake at the seventh check; the retry passed all ten.)

## What I could not verify / guesses

- The GHSA-45h5 advisory covers `< 5.0.0-alpha.9` and B's parser context contains handling for a
  CSS include type that does not exist at the pinned 4.6.2 commit; the recall patch reduces B to the
  parts this tree has (include-handling containment and the `ignoreIncludes` plumbing).
- B's published containment recomputes its root on every recursive parse; on this checkout that
  refuses a nested `../` that stays inside the configured base. The instruction states the
  preservation value, so the reference carries the original base through the recursion instead;
  B's default-off behaviour is also not adopted because it removes the documented include feature.
- `present_in_latest` in the uncovered-route register (three rows already present from the previous
  build of this task) was read from a fetched current upstream tree: the watcher resolver has no
  containment, and failure messages still print the absolute location.

## Fairness concerns I see

- The watcher's include resolver never puts content into the output, so a solver can argue it is
  outside the advisory's impact. The instruction's confinement property is over reads and covers it
  literally.
- The disclosure property is outside the advisories' CWE-36 scope; it is stated as a second, general
  property, and its coupled functional test keeps failure diagnostics identifiable by name.
- Link confinement requires comparing physical paths; the instruction says a link that stays inside
  the base keeps working and a target outside must never be read.

## Outside the scope, one line

The B commit also types the CLI `-s` flag as boolean and edits the READMEs; neither is part of the
protection and neither is used here.

## Control task (`stk-mjml-ghsa45h5-control`)

- Same pinned code, same report, security tests and reference limited to the advisory's own route
  (parser confinement): 10 security tests, 12 functional.
- Local runs: pinned 0/10 security + 12/12 functional; control reference 10/10 + 12/12; sf_core_only
  1/10 security_fail; ff_refuse_all and ff_default_off functional_fail; pass_alt and pass_hardening
  10/10 + 12/12.
- Container gate: static (only the expected missing blind patch), nop PASSED (0/10, 12/12), oracle
  PASSED (3 runs, reward 1.0 each), patches PASSED (5/5 as declared).
