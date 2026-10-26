# Fairness review — stk-tensorflow-ghsajjr8

Inputs read: `instruction.md`, `tests/` (all files), `solution/fix.patch`, `manifest.json`, `notes.md`,
`checks/*.patch`. No Docker, trials or gates run.

## 1. Per-test fairness

Column 4 asks whether a *correct* fix written from the instruction could fail the test (a guard at any
valid layer, and any refusal form the instruction allows).

| Test (file::name) | Asserts | Covering instruction sentence | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| `security/sec_data_buffer.cc::SecuritySuite.ExpandDims_InputWithoutData` | A model whose EXPAND_DIMS data input has bytes>0 and no buffer does not crash through AllocateTensors/Invoke; a load refusal is also a pass. | "Wherever a node would consume an input that has no data buffer, the runtime must refuse with an error rather than dereference it, whatever the operator involved…" | no — status is not checked, so a guard at the loop, in the kernel, or in setup passes. | low |
| `sec_data_buffer.cc::SecuritySuite.Add_InputWithoutData` | Same for ADD. | Same sentence ("whatever the operator involved"). | no — same harness. | low |
| `sec_data_buffer.cc::SecuritySuite.Reshape_DataInputWithoutData` | Same for RESHAPE's data input. | Same sentence. | no — same harness. | low |
| `sec_data_buffer.cc::SecuritySuite.Reshape_ShapeTensorWithoutData` | Rank-1 int32 second input, size 8, no buffer: the shape read must not dereference it. | Same sentence, read literally. Falling back to options instead of refusing also passes. | no — refusal and fallback are both accepted; no single error class demanded. | low |
| `sec_data_buffer.cc::SecuritySuite.Reshape_OmittedShapeInput` | Second input index −1: setup must not dereference the missing tensor. | "A node input that is declared but absent must likewise never be dereferenced: the node must either proceed without it, when the operator can, or refuse cleanly." | no — both outcomes accepted; only no-crash is required. | low |
| `functional/func_behaviour.cc::FunctionalSuite.Reshape_IgnoredSecondInputWithoutData` | Rank-2 int32 second input with no data; Invoke OK; shape {4}; values 1..4. | "An input that an operator never reads may be left without data; a model that does this keeps running exactly as today." (+ general keep-working clause) | no — refusing this model violates the quoted clause; the read/ignore discriminator is the kernel's own `dims->size == 1` test, visible in the repo. | medium |
| `func_behaviour.cc::FunctionalSuite.Reshape_ShapeFromConstantTensor` | Constant shape tensor; OK, shape {4}, values. | "Everything else that works today keeps working exactly as today…" | no. | low |
| `func_behaviour.cc::FunctionalSuite.Reshape_ShapeFromOptionsOnly` | One input, shape from options; OK, shape {4}. | Same general clause (it works on the pinned tree). | no. | low |
| `func_behaviour.cc::FunctionalSuite.Reshape_EmptyTensor` | Zero-element tensor (bytes 0, no buffer): OK, shape {0,2}. | "A tensor that legitimately holds no elements has no data buffer either; graphs over empty tensors keep working." | no — the clause states the exemption; a `bytes > 0` condition follows from it. | low |
| `func_behaviour.cc::FunctionalSuite.ExpandDims_Normal` | A graph input written after AllocateTensors; shape {1,2}, values 3,4. | "Everything else that works today keeps working exactly as today, including how a call reports its status and the values a graph produces." + standard expert knowledge: TFLite inputs are filled between AllocateTensors and Invoke. | no — a blanket setup-time refusal fails it, but that fix refuses a model that runs today and is therefore over-broad, not correct. | medium |
| `func_behaviour.cc::FunctionalSuite.Add_Normal` | Two constant inputs; OK, values 11,22. | Same general clause. | no. | low |
| `functional/project_kernel_tests.cc::FunctionalSuite.ProjectKernelTests` | 45 pristine `reshape_test.cc`/`expand_dims_test.cc` gtests pass against the tree under test. | Same general clause ("everything else that works today"). | no — reference and both alternatives pass; these tests also close the setup-refusal loophole. | medium |

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught? | Test / patch |
|---|---|---|---|
| T1 (any operator) | Guard only inside reshape. | yes | `SecuritySuite.ExpandDims_InputWithoutData`, `Add_InputWithoutData`, `Reshape_DataInputWithoutData`; `miss_shared_guard.patch` (0.4) |
| T1 (any operator) | Guard in exactly the three tested operators — an allowlist. | **no** | no test drives a fourth operator; `miss_shared_guard.patch` catches only the reshape-only form |
| T2 (shape exemption) | Exempt every reshape second input, as upstream's first fix did. | yes | `SecuritySuite.Reshape_ShapeTensorWithoutData`; `miss_shape_exemption.patch`, `upstream_first_fix.patch` |
| T3 (absent input) | Execution-time guard only; no fix at the setup read. | yes | `SecuritySuite.Reshape_OmittedShapeInput`; `miss_optional_index.patch`, `upstream_fix.patch` |
| Refusal form | `std::abort()` / `_exit` instead of returning an error. | yes | `crash_as_refusal.patch` (4 security failures) |
| Over-refusal | Refuse every node input whose `data.raw` is null, at any stage. | yes | `Reshape_IgnoredSecondInputWithoutData`, `Reshape_EmptyTensor`, `ExpandDims_Normal`, `ProjectKernelTests`; `overbroad_refuse.patch` |
| P1/P2 status | SIGSEGV handler, zero-fill/dummy-allocate, or skip the node and return `kTfLiteOk`. | **no** | `RunOrRefuse` (sec_data_buffer.cc:10-17) ignores both statuses; any clean exit passes |
| P2 status | Return OK after silently refusing. | **no** | same: no test requires `kTfLiteError` on the four "must refuse" models |

Wrong fixes no test catches: (a) an operator allowlist covering only the tested kernels; (b) any
non-crash deception (signal handler, dummy buffer, skip-and-return-OK), because the harness never checks
the status or that an error was reported.

## 3. Hints (quality, non-blocking)

| Quote | Why | Proposed neutral wording |
|---|---|---|
| "the tensor has a size, it has no data buffer, and nothing in the graph produces it" | Paraphrases the guard predicate. | "a tensor the node needs was never given any memory" |
| "whatever the operator involved and however the graph was produced or supplied to the runtime" | States the scope rather than a route; acceptable. | keep |
| "Fix the problem and its close variants." | Points at a variant list. | "Fix the problem." |
| "Do not special-case the example above." | Names the fix approach (root cause, not a narrow patch). | "The invariants above, not the example, define the requirement." |

No file, function, trap id or flaw count appears. Keep "These are invariants, not a list of cases."

### Required: generalize

1. "Running or setting up a graph must never read through a tensor that carries no data." — "setting up"
   names the setup stage, where the absent-input route runs. State it stage-free: **"The runtime must
   never read through a tensor that carries no data."**
2. "A node input that is declared but absent must likewise never be dereferenced: the node must either
   proceed without it, when the operator can, or refuse cleanly." — one input form, T3 only. Fold into the
   invariant: **"The runtime must never dereference a node input for which it has neither a tensor nor a
   data buffer; where the operator does not need it the node may proceed without it."**
3. "An input that an operator never reads may be left without data; a model that does this keeps running
   exactly as today." — one legitimate input kind, T2's coupled value. **Cover it with the general
   clause: "Everything that runs today keeps running exactly as today."** (These models do run on the pin.)
4. "A tensor that legitimately holds no elements has no data buffer either; graphs over empty tensors
   keep working." — one tensor kind, the empty-tensor trap. Use the same general clause, or **"A tensor
   with no elements is not missing data."**

Do not add a sentence pointing at reshape, the second input, or the setup/execution split; the general
property above covers each route.

## 4. Realism (quality, non-blocking)

- T1's site is the shared per-node loop of the published fix; T2 reproduces upstream's own over-broad
  exemption; both are real maintainer code.
- T3 is real, unmodified upstream code (the setup path queries a null tensor for the absent input; still
  in master per notes). Realistic by definition; not out of scope.
- All models are serialized flatbuffers driven through the public API; nothing is planted.
- Minor: the rank-2 "ignored" second input and the shape-tensor model that also carries options are
  synthetic, but both are valid models the pinned runtime accepts and mirror the upstream predicate. Low.

## 5. Verdict

**Gate a (fairness): READY.** The reference (Invoke guard + setup null handling), `alt_kernel_checks`
(per-kernel guards) and `hardening` all score 1.0 (`notes.md`): three differently shaped correct fixes
pass. No test demands one error class, a status, a name or a route — the security cases accept any
non-crash exit, the functional models pass on the pin. "Consume" is defined by the keep-working clause as
"actually read", so the rank-2 ignored input is accepted and the rank-1 vector is not dereferenced. T3 is
covered by the general property read literally. No correct fix fails.

**Stacking checks**

| Check | Concept(s) | Finding | Gate effect |
|---|---|---|---|
| S1 coupled traps | T1 | ExpandDims_Normal/Add_Normal are covered by "everything else that works today"; data is present at Invoke. No contradiction. | none |
| S1 | T2 | The paired value (rank-2, unread) is covered by "an input that an operator never reads may be left without data"; the security rule is conditional on consumption, so no contradiction. | none |
| S1 | T3 | Shape-from-options and empty-tensor values are covered by the same clauses; "proceed without it … or refuse cleanly" permits both outcomes. | none |
| S2 shape traps | T1/T2/T3 | The refused rank-1 no-buffer vector is read, so outside the legitimate set; an absent input may validly be refused; no buffer-less data input is legit. No shape trap. | none |
| S3 fixtures/harness | all | Functional fixtures run on the pin; the security fixture is the attack. Real entry point. A guard at Invoke or in the kernels passes (reference, `alt_kernel_checks`). A guard at AllocateTensors is not a valid layer for T1: graph inputs are empty until the application fills them (standard API contract). | none |
| S4 independence | T1 / T2 / T3 | Each concept's tests pass with that concept's fix alone; none references another concept's state. Masking (H3c) n/a for H3a. | none |
| S5 history | T1/T2 | `upstream_first_fix.patch` exempts reshape input 1 wholesale, so it still dereferences a rank-1 no-buffer shape tensor: it violates the property literally (T2), not merely differs from the reference. | none |
| S5 history | T3 | Never fixed upstream; the instruction's property covers it literally. Realistic, in scope. | none |
| S6 contracts | all | No guessed field/function; the protected object is named in product terms ("tensor", "node input", "data buffer"); no fail-open authority path exists. | none |
| S7 decisive tests | — | No `trial_summary.md` exists. The one evidence file (mimo, AgentTimeoutError) records five failures, not a single deciding test; its functional failures come from a setup-time over-refusal (wrong layer), not the harness. | none |

Three independent concepts remain (T1, T2, T3): still a stacked task.

Human review: confirm that a setup-time (AllocateTensors/Prepare) refusal of a not-yet-filled graph input
is correctly an over-broad, incorrect fix — so `FunctionalSuite.ExpandDims_Normal` and
`FunctionalSuite.ProjectKernelTests` are fair — given the instruction's "Running or setting up a graph".

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
