# Blind-fix brief (gate requirement, BUILDER.md 3f)

You write the task's second complete fix, the `kind: "blind"` pass patch. It is a SOUNDNESS
CONTROL: it shows the hidden tests accept a correct fix that is not the reference's exact code. It
is NOT a fairness test and does not show that a solver can find the fix (user rule, 2026-10-20).

You may use everything in view: `WORK/instruction.md`, the vulnerable repository at `WORK/app/`
(plus any helper jars in `WORK/libs/`), the private trap list (`WORK/injected-sites.md`), the hidden
tests, the reference fix and failing gate output. Prefer your own structure over copying the
reference (different helper, different placement, different style), but finishing the fix from
the reference or from failing tests is fine. Do not search the web or look up the upstream fix.

1. Fix the vulnerability in `WORK/app/` so the reported attack, every site in the trap list and
   every security property the report states are closed, and legitimate use keeps working exactly
   as stated. Change source only, not tests.
2. Verify what you can: write probes or tests under `WORK/probe/` (outside `app/`) and compile and
   run them where the toolchain allows. The gate is the final check: the patch must score 1.0.
3. When done, write the patch: `cd WORK && diff -ruN pristine app > WORK/blind.patch`, then make
   its paths `a/...` and `b/...` relative to the repository root (the gate applies it with
   `patch -p1` inside `/app`). Check that it applies cleanly with `patch -p1 --dry-run` to a fresh
   copy of `pristine`.
4. Write `WORK/mechanisms.md`: the fix at each site, one line each.

Fairness is judged separately, after the trial, on two checks only: the instruction and the tests
never contradict each other, and every tested sibling is covered by a general rule the instruction
states. Nothing about how this patch was written bears on either.

Return: the patch path, a 5-line summary of the fix, and the mechanisms list.
