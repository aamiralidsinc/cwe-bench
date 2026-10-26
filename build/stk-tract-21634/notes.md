# stk-tract-21634 — build notes

- **Started (UTC):** 2026-10-26T02:01Z (queue job), build work from 02:03Z
- **Ended (UTC):** _pending_

## Levers (one line each)

- **T1 (reported route, `both`)** — NNEF tensor-file reader multiplies model-declared dims with
  unchecked `usize` arithmetic (`nnef/src/tensors.rs:64-84`); the byte count wraps and an empty
  allocation backs a tensor that claims 2^62 elements. No reason to dismiss: this is the advisory's
  own site.
- **T2 (coupled must-keep, `mimo`)** — the obvious hardening (require `len * bytes_per_item ==
  data_size` for every tensor file, drop the `u32::MAX` skip) rejects the library's own
  block-quantized payloads (18/36 bytes per 32 values) and packed one-bit booleans that allow a
  trailing partial byte (`nnef/src/tensors.rs:66-84`, `:287-295`). Tested functionally only.
- **T3 (uncovered upstream, `deepseek`)** — `read_block_quant_value` computes the payload size with
  its own unchecked `(q_m*q_k)/block_len*block_bytes` (`nnef/src/tensors.rs:283-295`). Dimensions
  whose element count fits a `usize` but whose Q8_1 byte count overflows slip past a fix at the
  plain reader. Reason to dismiss: an internal GGML-style extension with its own formula and a
  reader/writer item-type mismatch; the published fix never touches it.
- **T4 (uncovered upstream, `mimo`)** — for a block-quantized constant the graph-declared shape
  silently replaces the shape stored in the tensor file, with no byte check
  (`nnef/src/ops/nnef/deser.rs:105-122`), while the plain branch does check shape equality. Reason
  to dismiss: the graph shape is authoritative on purpose because the file stores the flattened
  matrix, so it reads as intended reshaping.
- **T5 (uncovered upstream, `deepseek`)** — the ONNX tensor deserializer builds a tensor from
  model-declared initializer dims and the raw payload through the same unchecked shared allocator
  (`onnx/src/tensor.rs:113-134` → `data/src/tensor.rs:282`). Reason to dismiss: another format
  crate and a shared core layer; the report never points there.

All five are real upstream code. Nothing was injected.

## Concepts (as built)

1. `T1 + T2 + T5` — one size-arithmetic protection on plain tensors: a single checked product in
   the shared allocator would close both T1 and T5, so they are counted as one concept.
2. `T3` — the block-quantized reader's own byte formula.
3. `T4` — the graph-declared shape of a block-quantized constant against its payload.

Three concepts, with independent reference-fix edit sites. DeepSeek-type: T3, T5. MiMo-type: T2, T4.

## What I verified (all on the pinned commit bee4349, in a rust:1.95 container)

- Reproduced every security route against the pinned tree and the reference fix; the pinned copy
  accepts (or crashes on) each attack and the reference fix refuses each one.
- The published fix alone (`checks/upstream_fix.patch`) closes the plain reader only: 3 of the 7
  security tests still fail, so the recall check holds.
- Every `checks/*.patch` applied to a clean pinned tree and ran both hidden suites: each security
  miss leaves its concept's tests failing with the functional suite green; both over-broad fixes
  break legitimate tensor files; both pass patches score 1.0.
- The full `tests/Dockerfile` verifier ran end to end on the pinned tree (reward 0.0: 7 security
  failures, 9 functional passes) and on the reference-fixed tree (reward 1.0), offline.
- The agent image builds the tree, fetches the dependency closure including dev-dependencies, and
  `cargo test -p tract-nnef -p tract-data -p tract-linalg` compiles and runs with no network.
- Upstream `origin/main` (952a8e23d, checked 2026-10-26) still carries T3, T4 and T5: the block
  formula, the block-quantized graph shape and the ONNX deserializer are all unchanged.

## What I could not verify

- I did not run any target model; the difficulty claim is the reader's tiers plus the design, not a
  measured failure rate.
- The task records `stacking.reader_record` as `stacking/out/reader-ds/h4-21634.json`: that is where
  the reader's record for this candidate actually lives (`out/reader/` has no h4-21634 record).
- The `score_at_build` row is copied from `out/stack_scores_ds.tsv`; the scorer saw four concepts,
  this build declares three (see above), and `score_stack.py` was not run.
- The verifier's build profile sets `overflow-checks = false` (the harness is its own workspace
  root) so the graded build behaves like a release build, where the overflow wraps. The agent's own
  `cargo build` keeps the project's default profile.
