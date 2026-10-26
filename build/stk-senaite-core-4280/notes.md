# stk-senaite-core-4280 build notes

Start (UTC): 2026-10-22T22:12:00Z
End (UTC): 2026-10-22T23:41:23Z

Pinned: `3195f890fe591c0e962294edc013f77826209c5c`, the direct parent of the first
published fix (`git rev-parse a24d65e^` = pinned). Published fixes:
`a24d65e99a17ac43c5374ed9f0a60d0fe60d2f74` (record text parsed as a data literal) and
`ef4b6d73575b0fbc0edc6114e5e025089aaf9eb7` (AccessJSONAPI on the state-changing
integration routes). Neither regression test file exists at the pin.

## Levers (one line each)

- C1 / T1 (A, landing): the update route writes every field the caller names without
  checking that field's write permission on the object being written
  (src/bika/lims/jsonapi/update.py:126-150).
- C1 / T2 (A, far site, second implementation): the batch update resolves the object
  itself and calls the shared writer directly, so a fix placed in the single update
  leaves it open (src/bika/lims/jsonapi/update.py:216-234). Reason to dismiss: its
  docstring calls it a wrapper around the single update.
- C1 / T5 (coupled must-keep-working value, MiMo-type): a non-manager may edit the
  remarks field through the same route because that field grants a field-level
  permission; a blanket API-permission gate removes a legitimate edit.
- C2 / T7 (A, advisory route): record text for a field whose type is exactly the
  record/records class is evaluated at the API boundary
  (src/bika/lims/jsonapi/__init__.py:237-240).
- C2 / T8 (A, far site, type-name bypass): field subclasses (address and the other
  record-derived fields) skip that exact-type branch and reach the field layer's own
  evaluation (src/senaite/core/browser/fields/record.py:253-256,
  records.py:134-142). Reason to dismiss: the API sink looks like the only one.
- C3 / T9 (B, uncovered route, protection never existed): a data-returning request
  names a zero-argument attribute and the route calls it
  (src/bika/lims/jsonapi/__init__.py:151-157, reached from read.py:132-134). Reason
  to dismiss: the route is read-only and every caller's UI depends on it.

## Verified

- Tree reconstructed from the recorded build operations; the 133 files match
  `evidence/tree-sha256.txt` byte for byte (the tree that produced the saved
  gate evidence).
- Local matrix (python 2.7.18, six 1.16.0, zope.interface 4.7.2): pinned
  security 0/11 + functional 10/10; oracle 11/11 + 10/10; control pinned 0/4 +
  10/10; control reference 4/4 + 10/10.
- Every checks/ patch applies cleanly to the pinned tree (dry-run, each on a fresh
  copy), and a local 15-variant matrix reproduced every declared count exactly
  (including `upstream_fix_raw` 8/11 security + 8/10 functional). The control's
  9-variant matrix likewise reproduced its declared counts (reference 4/4 + 10/10).
- Recall: the two published fixes applied together (single combined diff) leave
  `refreshTotals` executable through the read route and the object-level write open,
  and break the remarks edits => security 8/11 + functional 8/10. The corrected
  recall variant (plus the remarks-compatibility correction) is 9/11 security
  (only the two read-route tests fail) + 10/10 functional.
- Gate: nop PASS. Oracle and patches results are recorded below when finished.

## Not verified / limitations

- The project's own Plone 5.2 / Zope 2 suite cannot run in the offline image; the
  functional suite drives the same product behaviour through the real route classes.
- The harness substitutes the Plone runtime with offline stubs. Common fix APIs are
  modelled (getSecurityManager/checkPermission, field.checkPermission/writeable,
  senaite.core.permissions constants, bika.lims.api.security.check_permission,
  plone.api.user), so a fix written against those APIs runs; a fix that needs a
  Plone facility not modelled here would fail.
- Conformance: `stacking/check_stack.py` (current version) reads
  `expect: "security_fail"`, not `"fail"`, so the manifest satisfies it and
  `builder/gate.py` at the same time. The three concept-miss checks carry
  `kind: security_fail` plus `misses` (T2_update_many, T8_field_layer_eval,
  T9_named_method_invocation).
- Recall design: the published fixes applied together (`upstream_fix_raw.patch`)
  still fail the object-level denial test and break the product's own remarks
  edits, so it is declared `functional_fail`. The recall check
  (`upstream_fix.patch`) is the same two fixes with one compatibility correction
  their own legitimate remarks path requires (the per-field check replaces the
  blanket API gate at the two update entry points); it keeps every functional
  test green, closes the authorization and parsing concepts, and still leaves the
  caller-named-method route open (security 9/11). The stack therefore adds a
  concept beyond upstream.
- Reader leads T3/T4/T11/T12 were dropped: the guard already exists (workflow
  transitions, container delete check) or the impact is disclosure only.
- No target-model trial was run (per the build rules); the gate is the proof.

## Pattern B register

- `build/audit/uncovered-routes.tsv` row for `stk-senaite-core-4280` / `T9`:
  real, unmodified upstream code; still present on origin/2.x.

## Gate (main task)

- static: PASS (after the manifest gained the blind declaration, `type`/`origin` on
  every trap, full-id concepts, per-concept `misses`, and the `senaite` leak term
  was dropped because the product name is in the report title).
- nop: PASS (security 0/11, functional 10/10) after one retry of the known Harbor
  `no-network` capability-probe ValueError.
- oracle: PASS, 3 runs, reward 1.0 each, identical results.
- patches: PASS, 16/16 executed checks exactly as declared (the blind check is
  declared but its file is written after the build by the pipeline). The first
  attempt aborted on the same Harbor `no-network` capability-probe ValueError
  (infra, at a mid-list check); the retry passed.
  - `upstream_fix.patch` (compatibility-corrected recall): security 9/11 +
    functional 10/10, so the two read-route tests still fail.
  - `upstream_fix_raw.patch` (published fixes exactly as shipped): security 8/11
    + functional 8/10, so its declared `functional_fail` holds.
  - the three concept-miss checks fail only their own concept's tests and keep
    every functional test green.

## Control task

- Earlier session (same 133-file tree): static FAIL only the missing blind patch;
  nop PASS (security 0/4, functional 10/10); oracle PASS (3 runs, 1.0 each);
  patches PASS 9/9 exactly as declared (security_fail 5, functional_fail 2,
  pass 2 incl. the alternative design). Re-run under the rebuilt manifests: see
  "Control gate (2026-10-23)" below.

## Rebuild after the 2026-10-23 reset

Start (UTC): 2026-10-23T02:59:45Z (the stacking pipeline relaunched the build;
`stacking/stacking_restart.sh` had removed `tasks/<slug>`, `tasks/<slug>-control`
and `build/<slug>/manifest.json`).

- Restored the task and control trees from the recorded build operations
  (`~/.tb-graders/cwe/work/stk-senaite-core-4280/recover/cmds`); all 133 files are
  byte-identical to `evidence/tree-sha256.txt`.
- Rebuilt both manifests and brought the main manifest into conformance with the
  current `stacking/check_stack.py`: `type` and `origin` on every trap,
  full trap ids in `stacking.concepts`, `kind`/`misses` on the three concept-miss
  checks, and the `senaite` leak term dropped (it is the product name in the
  report title).
- Split the recall evidence into `upstream_fix_raw.patch` (published fixes exactly
  as shipped; `functional_fail`, security 8/11 + functional 8/10) and
  `upstream_fix.patch` (same fixes with the remarks-compatibility correction;
  `security_fail`, security 9/11 + functional 10/10).
- Re-ran the gate on the main task: static PASS; nop PASS (one infra retry);
  oracle PASS (3 runs, 1.0 each); patches PASS (16/16 executed as declared, one
  infra retry). The control: static PASS; nop PASS; oracle PASS.

End (UTC): 2026-10-23T05:45:00Z

### Control gate (2026-10-23)

- static PASS; nop PASS (security 0/4, functional 10/10); oracle PASS (3 runs, 1.0).
- patches: the Harbor run aborted three times on the same no-network capability
  probe, each at a different check (infra, not a task failure). The same suites
  run directly against every control variant reproduced every declared outcome:
  sf-no-route-check 4 security fail, sf-wrong-object 1, sf-anonymous-only 3,
  sf-check-after-write 4, sf-fail-open 1, ff-blanket-access 1 security + 1
  functional, ff-refuse-all 6 functional, pass-hardening and pass-alt 0.
