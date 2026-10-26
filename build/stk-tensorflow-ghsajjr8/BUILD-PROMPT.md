# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-tensorflow-ghsajjr8`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-qh32-6jjc-qprm; GHSA-jjr8-m8g8-p6wv
- Pinned (vulnerable) commit: 00a5ef689b0080ae2a73fe81da4673985078ec5c. Published fix: 0b5662bc2be1, f8378920345f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-jjr8-m8g8-p6wv",
 "pattern": "H3a",
 "repo": "tensorflow/tensorflow",
 "pinned_commit": "00a5ef689b0080ae2a73fe81da4673985078ec5c",
 "protections": [
  "P1 (A, CVE-2020-15209): before a node's kernel runs, a non-optional input tensor whose buffer was never allocated or written (data.raw == nullptr with bytes > 0) must be refused rather than read. In the pinned code this does not exist anywhere: the per-node input loop in Subgraph::Invoke only handles delegate staleness (tensorflow/lite/core/subgraph.cc:1023-1033).",
  "P2 (B, GHSA-jjr8-m8g8-p6wv): Reshape must not read a null-backed shape tensor through the 1-D int32 'shape from tensor' branch, while the legacy case (second input present but ignored because the shape comes from params) must keep working (tensorflow/lite/kernels/reshape.cc:108-119, 75-80).",
  "P3 (same CWE, same operator, outside A/B's guard): Reshape::Prepare must not dereference the shape-tensor pointer when input #1 is the optional index -1 (tensorflow/lite/kernels/reshape.cc:134-135)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M3",
   "origin": "advisory_route",
   "locations": [
    "tensorflow/lite/core/subgraph.cc:1023",
    "tensorflow/lite/core/subgraph.cc:1043",
    "tensorflow/lite/kernels/reshape.cc:170",
    "tensorflow/lite/kernels/expand_dims.cc:111"
   ],
   "reason_to_dismiss": "The report names Reshape, so a solver could patch only reshape.cc. Every other kernel that reads an unallocated input (for example the expand_dims memcpy) stays open, and so does Reshape's own data input at reshape.cc:170.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "tensorflow/lite/core/subgraph.cc:1023-1033 (input loop checks only delegate/data_is_stale, no data.raw check)",
    "tensorflow/lite/core/subgraph.cc:1043 (OpInvoke called unconditionally after the loop)",
    "tensorflow/lite/kernels/reshape.cc:170 (memcpy from input->data.raw)",
    "tensorflow/lite/kernels/expand_dims.cc:111 (same memcpy pattern in another kernel)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "tensorflow/lite/kernels/reshape.cc:108-111",
    "tensorflow/lite/kernels/reshape.cc:114-116",
    "tensorflow/lite/kernels/reshape.cc:75-80",
    "tensorflow/lite/kernels/reshape.cc:134-138",
    "tensorflow/lite/kernels/reshape.cc:154-155"
   ],
   "reason_to_dismiss": "Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "tensorflow/lite/kernels/reshape.cc:110-111 (ShapeIsVector checks only non-null pointer, rank 1 and int32, not data.raw)",
    "tensorflow/lite/kernels/reshape.cc:80 (reads shape->data.i32[i])",
    "tensorflow/lite/kernels/reshape.cc:118 (non-vector shape tensors fall back to params; their data is never read)",
    "tensorflow/lite/kernels/reshape.cc:134-138 (non-constant shape makes the output dynamic, so the read is deferred to Eval at :154-155)",
    "tensorflow/lite/kernels/reshape_test.cc:95-104 (InvalidShape: a rank-2 shape tensor must keep working through the params fallback)",
    "tensorflow/lite/kernels/reshape_test.cc:144-165 (LegacyScalarOutput: legacy [0] params behaviour must keep working)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "tensorflow/lite/kernels/reshape.cc:134-135",
    "tensorflow/lite/kernels/kernel_util.h:178-180"
   ],
   "reason_to_dismiss": "The report is about null data buffers and this is a null tensor pointer from an 'optional' (-1) index. An Invoke-time buffer check skips optional inputs (subgraph.cc:1025), and the crash happens in Prepare, before any such check runs.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "tensorflow/lite/kernels/reshape.cc:123 (accepts NumInputs == 2 without checking that input #1 is a real tensor)",
    "tensorflow/lite/kernels/reshape.cc:135 (IsConstantTensor(GetInput(...)) with no null check)",
    "tensorflow/lite/kernels/kernel_util.cc:78-84 (GetMutableInput returns nullptr for kTfLiteOptionalTensor)",
    "tensorflow/lite/kernels/kernel_util.h:178-179 (IsConstantTensor dereferences tensor->allocation_type)",
    "tensorflow/lite/core/subgraph.cc:568-571 (index validation lets -1 through as optional)",
    "tensorflow/lite/core/subgraph.cc:1025-1026 (the Invoke input loop skips optional indices)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "tensorflow/lite/interpreter_builder.cc:470",
    "tensorflow/lite/interpreter_builder.cc:477-486",
    "tensorflow/lite/interpreter_builder.cc:533-536",
    "tensorflow/lite/core/subgraph.cc:1261-1264",
    "tensorflow/lite/arena_planner.cc:124-169"
   ],
   "reason_to_dismiss": "Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "neither",
   "evidence": [
    "tensorflow/lite/interpreter_builder.cc:470 (buffer index 0 yields buffer_data = nullptr)",
    "tensorflow/lite/interpreter_builder.cc:479-485 (an empty buffer also yields nullptr)",
    "tensorflow/lite/interpreter_builder.cc:533-536 (such a tensor becomes ReadWrite)",
    "tensorflow/lite/core/subgraph.cc:1263 (ReadWrite tensors start with buffer=nullptr and bytes=required_bytes)",
    "tensorflow/lite/arena_planner.cc:124-140 (allocates graph inputs and variables)",
    "tensorflow/lite/arena_planner.cc:161-169 (allocates node outputs only; a tensor that is only consumed is never allocated)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T4"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "Not code-level masking. Once T1 is closed by a generic Invoke check, T2 only stays open if the solver adds a Reshape input #1 exemption to keep legacy models working. So T2 shows up as a judgement inside the T1 fix, not as a separate site.",
   "T3 is not masked by T1/T2. It fires in Prepare (reshape.cc:135), which runs from PrepareOpsAndTensors (subgraph.cc:1006, 897) before the Invoke input loop (subgraph.cc:1023)."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T2",
   "what": "The natural strict fix for T1 (refuse every null-backed non-optional input at subgraph.cc:1023) also refuses a Reshape whose second input is null-backed but ignored (non-vector or non-int32, falling back to params at reshape.cc:118). That breaks a legacy must-keep-working case. Exempting Reshape input #1 wholesale reopens T2."
  },
  {
   "a": "T1",
   "b": "T1",
   "what": "Refusing data.raw == nullptr without the bytes > 0 condition breaks zero-element tensors, which legitimately have no buffer (for example the shape {0} scalar case at reshape_test.cc:131-140 and reshape_test_common.h:109-111)."
  }
 ],
 "fairness_risks": [
  "A legacy Reshape with a second input that is never read (shape taken from ReshapeOptions) must keep working even when that input has no buffer (reshape.cc:118). A hidden test for this has to be stated in the report or the must-keep list, or a strict generic check will fail it unfairly.",
  "Zero-element tensors (bytes == 0) have data.raw == nullptr legitimately (subgraph.cc:1263 with required_bytes 0). A rule of 'no null buffers' that ignores bytes refuses a shape that legitimate scalar reshapes need (reshape_test.cc:131-140).",
  "String tensors are kTfLiteDynamic and have no buffer until they are filled (subgraph.cc:1248-1255). A generic check at Invoke must not refuse a string tensor produced earlier in the same graph. Fine if the check only fires for bytes > 0 and the tensor is reallocated before use, but unverified for every string op.",
  "For T3, refusing NumInputs == 2 with input #1 == -1 is safe only if that is treated as 'no shape tensor' or as an error. Upstream behaviour for that shape is unverified, so a hidden test should accept either a clean error or the params fallback, not one specific outcome."
 ],
 "effort_minutes": 35,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3"
  ],
  "why": "These are three independent fix sites with three different reasons to dismiss. T1 tests whether the solver lifts the fix from the named kernel into the shared Invoke layer (M3). T2 is the mimo-type coupled value: the legacy ignored-shape-input must keep working while the 1-D int32 null-backed shape is refused. That is exactly the A-to-B regression, and both over-hardening and over-exempting fail. T3 is the deepseek-type absent protection, with a strong dismissal argument (a pointer, not a buffer; optional index; Prepare, not Invoke) that a buffer-check fix does not close. T4 is left out as a separate trap because the T1 guard closes it; it only adds an alternative fix site. Weaknesses: there are only 3 groups (the floor), and T3 comes from outside A/B's advisories (same operator, same CWE)."
 },
 "unverified": [
  "The contents of the A fix (0b5662bc2be1) and the B fix (f8378920345f) are not in the pinned tree. Neither the Invoke null-buffer check nor any Reshape exemption exists here (no 'lacks data' or kTfLiteBuiltinReshape in core/subgraph.cc), so the pinned commit predates both fixes. My claim that A added a generic check in Subgraph::Invoke with a Reshape input-1 exemption, and that B narrowed that exemption to non-1-D shape tensors, comes from memory of upstream, not from the pinned code. history.a_fix_leaves_b_open and b_in_code_a_wrote rest on that.",
  "That T3 (optional -1 as Reshape input #1 reaching IsConstantTensor(nullptr)) is reachable from a flatbuffer model end to end: the index validation and GetInput behaviour are verified, but the full load path through ParseNodes for Reshape was not traced.",
  "Whether upstream ever fixed T3 separately (it would fit the 'nullptr checks when obtaining tensors' series, commits 1970c2158b1 and fff2c832628) is unverified.",
  "Prepare-time reads in other kernels: the ones sampled (expand_dims.cc:83-87) gate data reads on IsConstantTensor, and MmapRo tensors always have a non-null buffer (interpreter_builder.cc:508, 526). An ordering (M7) trap was therefore not recorded, but not every kernel was checked.",
  "Delegates: NNAPI requires a constant Reshape shape (nnapi_delegate.cc:1847-1851) and XNNPACK ignores input #1 (xnnpack_delegate.cc:159-163), so neither was recorded as a separate route. Other delegates (GPU, Hexagon, CoreML) were not checked."
 ]
}
  ```
- Published fix sites:   - tensorflow/lite/core/subgraph.cc:1023 — T1 M3 (reason to dismiss: The report names Reshape, so a solver could patch only reshape.cc. Every other kernel that reads an unallocated input (for example the expand_dims memcpy) stays open, and so does Reshape's own data input at reshape.cc:170.)
  - tensorflow/lite/core/subgraph.cc:1043 — T1 M3 (reason to dismiss: The report names Reshape, so a solver could patch only reshape.cc. Every other kernel that reads an unallocated input (for example the expand_dims memcpy) stays open, and so does Reshape's own data input at reshape.cc:170.)
  - tensorflow/lite/kernels/reshape.cc:170 — T1 M3 (reason to dismiss: The report names Reshape, so a solver could patch only reshape.cc. Every other kernel that reads an unallocated input (for example the expand_dims memcpy) stays open, and so does Reshape's own data input at reshape.cc:170.)
  - tensorflow/lite/kernels/expand_dims.cc:111 — T1 M3 (reason to dismiss: The report names Reshape, so a solver could patch only reshape.cc. Every other kernel that reads an unallocated input (for example the expand_dims memcpy) stays open, and so does Reshape's own data input at reshape.cc:170.)
  - tensorflow/lite/kernels/reshape.cc:108-111 — T2 M11 (reason to dismiss: Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.)
  - tensorflow/lite/kernels/reshape.cc:114-116 — T2 M11 (reason to dismiss: Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.)
  - tensorflow/lite/kernels/reshape.cc:75-80 — T2 M11 (reason to dismiss: Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.)
  - tensorflow/lite/kernels/reshape.cc:134-138 — T2 M11 (reason to dismiss: Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.)
  - tensorflow/lite/kernels/reshape.cc:154-155 — T2 M11 (reason to dismiss: Reshape's second input often goes unused (the shape falls back to params), so a solver who adds the generic check may exempt Reshape input #1 entirely to keep legacy models working. That leaves the 1-D int32 null-backed shape that GetOutputShapeFromTensor still reads. This is exactly the hole B reports in A's fix.)
  - tensorflow/lite/interpreter_builder.cc:470 — T4 M6 (reason to dismiss: Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.)
  - tensorflow/lite/interpreter_builder.cc:477-486 — T4 M6 (reason to dismiss: Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.)
  - tensorflow/lite/interpreter_builder.cc:533-536 — T4 M6 (reason to dismiss: Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.)
  - tensorflow/lite/core/subgraph.cc:1261-1264 — T4 M6 (reason to dismiss: Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.)
  - tensorflow/lite/arena_planner.cc:124-169 — T4 M6 (reason to dismiss: Loading is not where the crash shows. A tensor with buffer index 0 or an empty buffer becomes a valid-looking read-write tensor with a null buffer, and the planner allocates only graph inputs, variables and node outputs, so the loader looks innocent.)
- Uncovered routes to confirm (pattern B):   - tensorflow/lite/kernels/reshape.cc:134-135 — T3 M4 (reason to dismiss: The report is about null data buffers and this is a null tensor pointer from an 'optional' (-1) index. An Invoke-time buffer check skips optional inputs (subgraph.cc:1025), and the crash happens in Prepare, before any such check runs.)
  - tensorflow/lite/kernels/kernel_util.h:178-180 — T3 M4 (reason to dismiss: The report is about null data buffers and this is a null tensor pointer from an 'optional' (-1) index. An Invoke-time buffer check skips optional inputs (subgraph.cc:1025), and the crash happens in Prepare, before any such check runs.)
- Design plan from the lead: TRACK = STACKED (H3a). Build the stacked design the reader chose: traps T1, T2, T3. Why: These are three independent fix sites with three different reasons to dismiss. T1 tests whether the solver lifts the fix from the named kernel into the shared Invoke layer (M3). T2 is the mimo-type coupled value: the legacy ignored-shape-input must keep working while the 1-D int32 null-backed shape is refused. That is exactly the A-to-B regression, and both over-hardening and over-exempting fail. T3 is the deepseek-type absent protection, with a strong dismissal argument (a pointer, not a buffer; optional index; Prepare, not Invoke) that a buffer-check fix does not close. T4 is left out as a separate trap because the T1 guard closes it; it only adds an alternative fix site. Weaknesses: there are only 3 groups (the floor), and T3 comes from outside A/B's advisories (same operator, same CWE). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): A legacy Reshape with a second input that is never read (shape taken from ReshapeOptions) must keep working even when that input has no buffer (reshape.cc:118). A hidden test for this has to be stated in the report or the must-keep list, or a strict generic check will fail it unfairly. | Zero-element tensors (bytes == 0) have data.raw == nullptr legitimately (subgraph.cc:1263 with required_bytes 0). A rule of 'no null buffers' that ignores bytes refuses a shape that legitimate scalar reshapes need (reshape_test.cc:131-140). | String tensors are kTfLiteDynamic and have no buffer until they are filled (subgraph.cc:1248-1255). A generic check at Invoke must not refuse a string tensor produced earlier in the same graph. Fine if the check only fires for bytes > 0 and the tensor is reallocated before use, but unverified for every string op. | For T3, refusing NumInputs == 2 with input #1 == -1 is safe only if that is treated as 'no shape tensor' or as an error. Upstream behaviour for that shape is unverified, so a hidden test should accept either a clean error or the params fallback, not one specific outcome.. Conflicts the reader found: The natural strict fix for T1 (refuse every null-backed non-optional input at subgraph.cc:1023) also refuses a Reshape whose second input is null-backed but ignored (non-vector or non-int32, falling back to params at reshape.cc:118). That breaks a legacy must-keep-working case. Exempting Reshape input #1 wholesale reopens T2. | Refusing data.raw == nullptr without the bytes > 0 condition breaks zero-element tensors, which legitimately have no buffer (for example the shape {0} scalar case at reshape_test.cc:131-140 and reshape_test_common.h:109-111).

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-tensorflow-ghsajjr8/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-tensorflow-ghsajjr8/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-tensorflow-ghsajjr8/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-tensorflow-ghsajjr8/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-tensorflow-ghsajjr8/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-tensorflow-ghsajjr8/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-tensorflow-ghsajjr8/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-tensorflow-ghsajjr8 --only static
python3 -I builder/gate.py stk-tensorflow-ghsajjr8 --only nop
python3 -I builder/gate.py stk-tensorflow-ghsajjr8 --only oracle
python3 -I builder/gate.py stk-tensorflow-ghsajjr8 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-tensorflow-ghsajjr8/`;
  - edit only `tasks/stk-tensorflow-ghsajjr8/`, `build/stk-tensorflow-ghsajjr8/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-jjr8-m8g8-p6wv.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-tensorflow-ghsajjr8`. Control task slug: `stk-tensorflow-ghsajjr8-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-jjr8-m8g8-p6wv.json`.
