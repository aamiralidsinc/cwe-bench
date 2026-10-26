# NEEDS_HUMAN_REVIEW: stk-tensorflow-ghsajjr8 v1 (both-model BREAKER candidate), 2026-10-25T03:25Z

- DeepSeek 0/3 [0, 0, 0], MiMo 0/3 [0, 0, 0.8]; every counted run audited trustworthy model-failed (high).
  MiMo r1 timed out at 2 h and was replaced by a 3 h run (r4, 135 of 180 min used): 0.8, failed only
  SecuritySuite.Reshape_OmittedShapeInput (trap T3, never fixed upstream: reshape setup dereferences an absent
  shape input).
- Fairness (v1, 2026-10-23): READY, NEEDS_HUMAN_REVIEW: confirm that refusing a not-yet-filled graph input at
  setup time (AllocateTensors/Prepare) is an over-broad, incorrect fix, so FunctionalSuite.ExpandDims_Normal
  and FunctionalSuite.ProjectKernelTests are fair, given the instruction says "running or setting up a graph".
  Several DeepSeek runs failed exactly such functional tests.
- **Caveats:** (1) v1, never upgraded: its instruction still FAILS the listing check (2 hidden traps
  described), so it failed both models even with hints. (2) The one-bug CONTROL also fails DeepSeek 0/3, so the
  difficulty is not only from stacking. Not committed, not shipped.

## User decision (2026-10-25 ~05:50Z)
KEEP as v1 (no upgrade). Setup-time refusal of unfilled inputs = fair expert knowledge (only the uncounted timed-out run hit it). Note for Klavis: v1 instruction describes T2/T3 (listing FAIL) and the one-bug control also fails DeepSeek 3/3.
