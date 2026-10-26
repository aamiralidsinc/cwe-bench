# Build notes: keras-ds

- Start (UTC): 2026-10-18 22:01
- End (UTC): 2026-10-19 00:46

## Advisory / commits
GHSA-26C4-7VV6-867J / CVE-2026-12480 / PYSEC-2026-3629 — keras-team/keras,
CWE-73: an untrusted HDF5 model/weights artifact can make the loader read a
different local file and return it as model weights. Pinned commit
`f704c887bf459b42769bfc8a9182f838009afddb` (release 3.12.1), verified as the
parent of the published fix `8f987f11bf7512f0df4774a8f1557bba07dc2b49`
(3.12.2). Track INJECTED, pattern A + pattern B + injected siblings.

## Mechanism (one line)
Every lookup of a group or value in an HDF5 model/weights artifact must reject
links, values whose bytes live in an external file, and virtual values; at the
pinned commit the core serialization store only rejects external-storage
values, and several other read paths check nothing.

## Levers (8; all verified nop-fail / oracle-pass offline)
- T1 base store, indirect value (A, report target): `H5IOStore.__getitem__`
  (saving_lib.py). Shapes: virtual dataset in .weights.h5 via load_weights and
  Model.load_weights, and in an unzipped .keras directory via load_model.
  Dismiss: this is the report's site; a one-line virtual check looks complete.
- T2 base store, links (A, report target): `H5IOStore.get` group lookup
  (saving_lib.py). Shapes: ExternalLink at a layer group, SoftLink at a value,
  SoftLink in a zipped .keras, SoftLink in the older checkpoint-dependency
  fallback. Dismiss: links resolve to ordinary-looking objects; the existing
  check only looks at external storage on the value.
- T3 sharded store (A, far site, second implementation):
  `ShardedH5IOStore._get_h5_group` (saving_lib.py). Shape: ExternalLink at a
  layer group in the later shard of a two-shard set whose layer spans shards.
  Dismiss: the subclass/shard-switching path is easy to miss when fixing the
  base store.
- T4 older single-file loader (A, far site, separate module):
  `legacy_h5_format.py` loaders and value reads. Shapes: external storage
  (arbitrary local file), virtual dataset, value ExternalLink; load_model,
  load_weights and by_name=True. Dismiss: keras/src/legacy reads as the Keras 2
  compatibility path and has no validation helper at all.
- T5 weights-file inspection utility (B, real upstream): `file_editor.py`
  recursive extractor. Shapes: virtual dataset, SoftLink, ExternalLink.
  Dismiss: an inspector, not a loader, and it already has its own
  external-storage check.
- T6 older-format top-level lookup (B, real upstream): `saving_api.py` legacy
  branch raw `f["model_weights"]`. Shape: model_weights is an ExternalLink to a
  complete group in another file. Dismiss: a dispatch step; the loader below
  validates groups and values.
- S1 injected: `ShardedH5IOStore.__getitem__` cross-shard branch reads the
  value in place, bypassing the base reader. Shape: external-storage value in
  the later shard. Dismiss: the base value reader was fixed, so every read
  looks protected.
- S2 injected: `ShardedH5IOStore.get` missing-weight-map fallback resolves the
  layer group raw in the open shard. Shape: an index that omits the path plus
  an ExternalLink at the layer group. Dismiss: the weight map is bookkeeping,
  not a data read.

Distinct reasons-to-skip: report-site minimality / link-resolution look /
subclass / legacy module / inspector-not-loader / dispatch-step / base-reader
assumption / bookkeeping-fallback.

## Injection
`environment/injection.patch` adds the two siblings to
`keras/src/saving/saving_lib.py` on top of the pinned tree (19 added lines,
2 removed). An ordinary multi-shard file with a layer spanning the shard size
exercises S1's branch, and a weight map that omits a path exercises S2's
fallback, so neither is dead code. The published fix does not touch either
function.

## Verified
- Flaw reproduces at the pinned+injected commit through the real public APIs:
  `keras.saving.load_weights`, `Model.load_weights`,
  `keras.saving.load_model` (archive, unzipped directory, older .h5),
  sharded `.weights.json`, and `keras.saving.KerasFileEditor`. External storage
  points at an absolute temp file; virtual datasets and links point at a temp
  HDF5 file; marker values are read back from the model variables or the
  inspector data. No network, no GPU, no service. NumPy backend.
- Oracle (`solution/fix.patch`) closes all 8 levers and keeps ordinary use: 18
  security tests fail on pinned and pass on oracle; 12 functional tests pass on
  both; 104 curated project cases pass on both and on every check patch.
- All 11 check patches locally reproduce their declared behaviour (8
  security_fail each isolating exactly one lever's tests, 1 functional_fail on
  8 functional tests, pass-hardening and pass-alt both all-pass).
- `fix.patch` applies with `patch -p1` to the pinned+injected tree;
  `injection.patch` applies with `patch -p1` to the pinned tree.
- Latest upstream (read-only, raw master): `saving_api.py` now calls
  `safe_get_h5_group` for the top-level container and the inspector checks
  `is_virtual`, so both pattern-B routes are fixed later; the inspector still
  indexes `data[key]` raw, so its link handling is only partial upstream.

## Could not verify
- `project_tests_run`: the legacy_h5_format_test.py suite is entirely gated on
  `tf_keras` (absent in the image); the task's own functional legacy tests cover
  that format. Trainer-dependent and other runtime-skipped project cases are
  excluded by node id (skips count as failures in the scorer).
- No upstream regression test exists for the pinned attack shapes; the hidden
  tests are ours.
- The `.keras` in-memory reader does not resolve virtual datasets or external
  links (h5py cannot resolve them from a BytesIO), so those shapes are tested
  through the on-disk forms and the unzipped directory; in-memory soft links do
  resolve and are tested in the archive form.

## Gate
- static: FAILS only on the two downstream items — `checks/blind.patch` and
  `FAIRNESS.md` are written after this build; every other static check passes.
- nop: PASSED (18/18 security tests fail on the pinned+injected image; 12/12
  hidden functional and 104/104 curated project cases pass).
- oracle: PASSED (3 runs, each reward 1.0 and identical).
- patches: PASSED with 11 checks (the 12th, blind, is downstream). Rewards:
  8 security_fail checks leave 1–4 security tests failing with all functional
  passing; ff-overbroad 0.0; pass-hardening and pass-alt 1.0.
- Shared-VM infrastructure: repeated `RuntimeError: ... network ... not found`
  from docker compose (concurrent `docker network prune -f` from other gate
  jobs) and one `network_mode='allowlist'` egress-probe rejection. These are
  environmental, not task behaviour; the stages were retried until clean, and
  the patches run used a short-lived labelled guard endpoint on this task's
  own compose networks during the create/attach window. No task setting was
  weakened.

## Hardening (2026-10-22)

Both earlier delivery rounds left the task fair but too easy for MiMo (which
solved the original 18-test suite). This round adds three position-level levers
in real, unmodified upstream code; the published-fix oracle already closes all
three, so `fix.patch` is unchanged (the rules were violated by missing tests,
not by missing code).

- T7 core store, top-level container: an ExternalLink at the root `vars` group
  of a `.weights.h5` produced by a model that owns its own variable, loaded
  through `Model.load_weights`. `H5IOStore.get("")` (`saving_lib.py:1117-1118`)
  read the root group with no link check at the pinned commit. Dismiss:
  ordinary Sequential artifacts leave the top-level container empty, so
  per-layer fixes never visit the empty-path branch. Coupled: top-level
  variable round-trip.
- T8 older loader, optimizer state: an ExternalLink at an optimizer-state
  value in the older `.h5`, loaded by `keras.saving.load_model` with
  compilation. `load_optimizer_weights_from_hdf5_group`
  (`legacy_h5_format.py:594-599`) read the root optimizer group and its values
  raw; only the later `set_weights` call warnings on ValueError. Dismiss:
  optimizer state sits at the file root outside the weight container. Coupled:
  non-default iteration/learning-rate restore.
- T9 inspector container shortcut: an ExternalLink at a layer's `vars`
  container in a `.weights.h5` opened by `KerasFileEditor`
  (`file_editor.py:487-493`). The extractor checks child entries and datasets
  but resolves the container directly. Dismiss: the shortcut reads as plumbing,
  not a value read (the screener's O8b sibling). Coupled: two-layer editor
  round-trip.

Each lever has one security test through the real entry point, one
security_fail check patch that isolates exactly that test
(`sf-miss-root-vars`, `sf-miss-optimizer`, `sf-miss-editor-vars`), and one
coupled functional test. `sf-miss-base-links.patch` was adjusted to keep
rejecting group links while fixing the root container, so it still isolates the
original T2 trap on its own.

Delivery format: the task now follows `FRONTIER-CONFORMANCE-SPEC.md` and
`builder/conformance_check.py` (schema 1.4, `/workspace`, separate offline
verifier, uid-1000 non-root grading, artifacts restore, fresh canary GUID,
B7 metadata). `tests/Dockerfile` and `tests/runner/run_project.sh` are new;
`tests/test.sh` is the non-root separate-mode scaffold.

Local pre-check (venv, NumPy backend): 21/21 security tests fail on the
pinned+injected tree; 21/21 security and 15/15 hidden functional pass on the
oracle; the three new security_fail patches each fail exactly one security
test with all functional passing; ff-overbroad fails 10 functional; both pass
checks are 21/21 + 15/15; 104/104 curated project cases pass on pinned and
oracle. Docker gate re-run 2026-10-22 (this final state):
- `conformance_check.py tasks/keras-ds` -> conforming.
- static -> PASSED.
- nop -> PASSED: security 0/21, functional 119/119 (15 hidden + 104
  project), reward 0.0.
- oracle -> PASSED: 3 runs, each reward 1.0, 140/140 tests.
- patches -> PASSED with 15 checks: the 11 security_fail patches each leave
  1-4 security tests failing with every functional test passing; ff-overbroad
  0.0 (75 failures/1 error); pass-hardening, pass-alt and blind all 1.0
  (140/140). The blind check is a whole-file structural validator and still
  covers the three new positions; that is the main limit on the hardening's
  bite and why the post-verdict confidence is medium, not high.

## Out of scope (one line)
The same published release also hardens archive extraction and Functional
config traversal (other advisories); neither is touched here. `KerasFileEditor`
and the legacy top-level lookup were still open upstream after the published
fix and are used as pattern-B routes, not as published-fix sites.
