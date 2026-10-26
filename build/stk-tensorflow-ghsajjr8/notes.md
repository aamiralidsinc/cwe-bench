# stk-tensorflow-ghsajjr8 — build notes

- Start (UTC): 2026-10-23T01:19:51Z (build restarted from the preserved work tree at 08:18:33Z after a queue reset)
- End (UTC): 2026-10-23T09:25:48Z
- Repo / pin: tensorflow/tensorflow @ 00a5ef689b0080ae2a73fe81da4673985078ec5c (parent of the earlier fix)
- Advisories: GHSA-qh32-6jjc-qprm (fix 0b5662bc2be13a8c8f044d925d87fb6e56247cd8), GHSA-jjr8-m8g8-p6wv (fix f8378920345f4f4604202d4ab15ef64b2aceaa16)
- Pattern: H3a (fix of a fix). The pinned tree contains neither fix (verified by reading core/subgraph.cc and the reshape kernel).

## Levers (one line each)

- T1 (both; published_fix_far_site): a node input with `bytes > 0` and `data.raw == nullptr` must be refused before any operator runs, for every operator (verified with EXPAND_DIMS, ADD and RESHAPE); a fix placed in the reshape kernel leaves the other operators reading the missing buffer. Guard lives at tensorflow/lite/core/subgraph.cc:1023.
- T2 (mimo; advisory_route): the reshape's second input is a rank-1 int32 tensor with a size and no buffer; the first published fix exempted that input wholesale, so the shape read still dereferences it. The coupled value is a second input the operator never reads (rank-2), which must keep working. tensorflow/lite/kernels/reshape.cc:108-119.
- T3 (deepseek; uncovered_upstream): reshape with two declared inputs where the second is the absent marker; setup calls the constant-tensor query on the null pointer returned for an absent input. tensorflow/lite/kernels/reshape.cc:134-135. Still present in upstream master (read on 2026-10-23).

## What was verified (behavioural, on the pinned source)

- Built the TFLite library with its own CMake project (ubuntu 20.04, gcc 9, ninja). Library build ~70 s on 8 CPUs.
- Wrote a model builder over the checked-in flatbuffer schema; every case loads a real serialized model through FlatBufferModel + InterpreterBuilder and runs it through AllocateTensors/Invoke.
- Pinned tree: the five security cases each die with SIGSEGV (the runner forks each case, so a crash is a failed case); the seven functional cases pass, including a rank-2 ignored shape input, an empty (zero-element) tensor, the operator-parameters fallback and the project's own 45 kernel gtest cases.
- Reference fix: security 5/5 pass, functional 7/7 pass.
- Project tests: tensorflow/lite/kernels/reshape_test.cc + expand_dims_test.cc (45 gtest cases) compiled from pristine copies against the tree under test; pass on the pinned tree and with the reference fix.
- Each check patch re-run through the verifier against a rebuilt library:
  - miss_shared_guard (reshape-only fix): 3 security failures (T1), functional clean.
  - miss_shape_exemption (published first fix's wholesale exemption): 1 security failure (T2), functional clean.
  - miss_optional_index (no absent-input guard): 1 security failure (T3), functional clean.
  - upstream_first_fix (A alone): 2 security failures (T2, T3).
  - upstream_fix (A+B): 1 security failure (T3).
  - overbroad_refuse: 2 functional failures (ignored input, empty tensor).
  - crash_as_refusal: 4 security failures, functional clean.
  - alt_kernel_checks (per-kernel checks instead of the shared loop): 1.0.
  - hardening (reference + kernel-level defensive checks): 1.0.

## Gate (deterministic, builder/gate.py)

- static: PASSED (main and control). The only missing named check is `checks/blind.patch`, which the blind-fix stage supplies later.
- nop: PASSED — 5/5 security tests fail on the pinned tree, 7/7 functional pass.
- oracle: PASSED — 3 identical runs at reward 1.0.
- patches: PASSED — miss_shared_guard 0.4, miss_shape_exemption 0.8, miss_optional_index 0.8, upstream_fix 0.8,
  upstream_first_fix 0.6, overbroad_refuse 0.0, crash_as_refusal 0.2, alt_kernel_checks 1.0, hardening 1.0.
  (A `security_fail` check needs one or more security failures with every functional test passing; overbroad_refuse
  is the functional-fail check; the last two are correct-fix passes.)
- stacking/check_stack.py: conforming (3 concepts, pattern H3a).

## What could not be verified

- The acceptance bar (both target models failing three attempts) is not measured here: trials and target models are outside this build's scope.
- The upstream tree's own bazel test runner is not usable offline; the project's kernel tests were compiled directly with gtest instead of through bazel.
- Whether the published fixes were backported to every release branch (not needed for the task).
- The optional-input route was exercised through the public C++ API with a real serialized model whose node input index is -1, not from a hand-written flatbuffer file on disk.
- String tensors are not exercised end to end through a graph that produces one; a generic execution-time check that fires only for `bytes > 0` is safe for them by construction, but that path has no hidden case.
- The score model flags the design `single-trap-carries` (P(fail 3x) without each model's hardest concept is 0.003): T1 is medium-tier for both models, so most of the stacked task's difficulty rests on T2 (MiMo) and T3 (DeepSeek).
