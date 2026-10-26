# stk-katex-7340 — build notes

## Window
- start: 2026-10-26T02:24:02Z (build job start)
- end: 2026-10-26T04:45Z (hand-off; the pipeline re-gates after the build)

## What the task is
KaTeX (TypeScript, pinned 5a5bf206, parent of the published fix 0adf7e77 "prevent prototype
pollution in settings"). A value placed on JavaScript's shared object prototype must not decide
what KaTeX renders or which commands it permits. Two properties: render options and defaults come
only from the caller's own entries / KaTeX's own defaults; a macro name expands only when KaTeX or
the current render defines it.

## Levers (one line each)
- T1_settings_options (both, advisory route): the caller's own entry only — src/Settings.ts:336-348; reason to dismiss: none (reported).
- T8_option_value_forms (mimo, coupled value): function-valued trust/strict, own-undefined fallback and a settings instance as options must survive the own-property read — src/Settings.ts:336-348, 261-272; the natural Boolean/hasOwnProperty hardening breaks them.
- T2_schema_metadata (deepseek, advisory route): the schema entry's own default/processor only — src/Settings.ts:328-334, 344-345; reason to dismiss: SETTINGS_SCHEMA is a module constant, so it reads as static bookkeeping.
- T3_trust_context (both, uncovered upstream): the protocol handed to the trust function must come from the command's own URL — src/Settings.ts:464-476; reason to dismiss: it is the check itself and already derives the protocol, and the report's shape is a polluted setting.
- T4_macro_namespace (deepseek, published-fix far site): macro names resolve only from own properties — src/Namespace.ts:81-87; reason to dismiss: the class already calls hasOwnProperty on the per-render map and has() checks both maps.
- T5_namespace_undo (deepseek, published-fix far site, same concept/patch as T4): the undo capture must not record an inherited value — src/Namespace.ts:112-115; reason to dismiss: it reads as undo bookkeeping, and it is masked while the lookup still falls through.
- T7_auto_render (deepseek, uncovered upstream): auto-render resolves its own options only — contrib/auto-render/auto-render.ts:130-161; reason to dismiss: a separate package entry that only picks macros and delimiters, outside the settings path.

## What I verified
- The published fix (0adf7e77) is the four source hunks in src/Settings.ts (schema default,
  options and processor read) and src/Namespace.ts (get, set); it does not touch isTrusted or auto-render.
- Every lever reproduces behaviourally on the pinned tree through the real entry points
  (renderToString / renderMathInElement), and every one is closed by the oracle.
- Local matrix (node 20.19.2 + jest 30 / jsdom 24): pinned security 0/15 + functional 648/648;
  oracle 15/15 + 648/648; each miss_* patch fails only its concept's security tests with functional
  648/648; sf-get-only 14/15; sf-href-only 13/15; sf-wrong-object 14/15 + 647/648;
  ff-refuse-trusted 15/15 + 620/648; ff-overcoerce 12/15 + 545/648; upstream_fix exactly as shipped
  10/15 + 648/648 (it leaves T3 and T7 open, so the stack adds beyond upstream); pass-hardening and
  pass-alt 15/15 + 648/648.
- Container runs through tests/test.sh: pinned reward 0.0 (security 0/15, functional 648/648);
  oracle reward 1.0 (15/15, 648/648).
- The project's own test/katex-spec.ts (623 tests, 22 snapshots) passes at the pinned commit in the
  environment image and runs from the pristine copy in the functional group.
- The pinned tree contains no regression test for the fix (0adf7e77 adds the only one).
- Control: same instruction byte-for-byte; security tests cover only the options own-read (5 tests);
  reference is the published fix; matrix: reference 5/5 + 648/648, pf-miss 0/5 + 648/648,
  pf-trust-key-only 4/5 + 648/648, ff-refuse 5/5 + 620/648, ff-overcoerce 5/5 + 545/648,
  pass-hardening / pass-alt 5/5 + 648/648.

## Gate status at hand-off
- static: PASS (`gate_report.partial.json`, 2026-10-26T03:23Z).
- The same verifier pipeline ran end-to-end in the task's own verifier image on this host:
  pinned workspace -> reward 0.0 (security 0/15, functional 648/648) and the oracle workspace ->
  reward 1.0 (security 15/15, functional 648/648). Results kept in
  build/stk-katex-7340/evidence/container-*.json and gate-nop-trial-results.json. After trimming a
  375 MB duplicate chown layer from the verifier image, both were re-run on the rebuilt image with
  the same results (pinned 0/15 + 648/648; oracle 1.0, 15/15 + 648/648).
- Harbor's nop/oracle/patches stages could not complete during the build window: every trial
  stalled at "Collecting main service artifacts" / the shielded agent-environment stop (and once in
  verifier-container removal), under an unrelated load average of 85-250 from other builders'
  concurrent trials. The first nop trial did reach a complete verifier result (security 0/15,
  functional 648/648) before its teardown hung; later attempts hit the same stop at every load
  level. The pipeline re-gates the task after the build (common/gate/postbuild.sh, with infra
  retries); the full local patch matrix above matches every declared outcome.

## What I could not verify / unknowns
- There is no advisory id (CVE/GHSA) for this issue in the inputs; the record's "7340" is used only
  as the candidate id. The upstream fix PR is 4260.
- The reported threat model assumes another library pollutes the shared prototype (as the record
  states); I did not look for a pollution primitive inside KaTeX itself.
- `Object.prototype.processor` used as a value adjuster is exercised with a function value, the
  shape the upstream regression test uses; a data-only pollution of that key throws instead of
  bypassing, and the test only requires that the inherited value does not adjust the setting.
- The package's own browser-build/screenshot suites are not run (they need a built dist, a browser
  and network); the affected spec plus the hidden suites are.

## Fairness notes
- The coupled values (function-valued trust and strict, own-undefined fallback, settings instances,
  the caller's mutable macro table, HTML-command contexts without a URL) are documented product
  behaviour and are tested functionally; the report covers them only by "everything that works today
  keeps working exactly as today".
- A fix placed at any valid layer passes: own-property reads, descriptor reads, a fresh context, a
  prototype-free option copy (pass-alt), and the oracle's layer.
