# stk-tensorflow-ghsajjr8-control — build notes

- Start (UTC): 2026-10-23T02:05:00Z (rebuilt from the preserved work tree at 08:23Z after a queue reset)
- End (UTC): 2026-10-23T09:25:48Z
- Control for the stacked task: same pinned tree (00a5ef689b0080ae2a73fe81da4673985078ec5c), same instruction.md,
  but only the advisory's own route (a node input with a size and no data buffer) is exercised by the
  security suite, and the reference fix is the earlier published fix alone (0b5662bc2be13a8c8f044d925d87fb6e56247cd8).
- It is used to separate the effect of stacking from the effect of the host.

## What it contains

- 4 security cases: EXPAND_DIMS, ADD and RESHAPE (twice, different shapes) consuming a buffer-less input.
- The same 6 behavioural functional cases as the stacked task plus the project's own reshape/expand-dims
  gtest cases (45), so the coupled "input the operator never reads" value is still enforced.
- Check patches: miss_shared_guard (reshape-only fix, leaves the route open), overbroad_refuse
  (functional failure), crash_as_refusal (security failure), alt_kernel_checks and hardening (pass).

## Gate (deterministic, builder/gate.py, full run)

- static: PASSED.
- nop: PASSED (4/4 security fail on the pinned tree, 7/7 functional pass).
- oracle: PASSED (3 identical runs at 1.0; the reference is the earlier published fix alone).
- patches: PASSED — miss_shared_guard 0.0 (all 4 security cases still fail, functional clean),
  overbroad_refuse 0.0 (3 functional failures), crash_as_refusal 0.0 (security failures, functional clean),
  alt_kernel_checks 1.0, hardening 1.0.
- Verdict: pass (build/stk-tensorflow-ghsajjr8-control/gate_report.json).
