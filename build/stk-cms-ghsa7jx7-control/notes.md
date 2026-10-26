# stk-cms-ghsa7jx7-control — build notes

start_utc: 2026-10-26T03:35Z (control build)
end_utc: 2026-10-26T04:07Z

## What this control is

The same pinned Craft CMS tree, the same `instruction.md` (byte-identical to the stacked
task's), and only the advisory's own route in the hidden security suite and the reference:

- four security tests against the field layout save service (`assembleLayoutFromPost'):
  a top-level class-bearing key, the same key in a namespaced submission, and the key nested
  in a tab and in an element;
- the seven functional tests of the stacked task (they pass on the pinned tree);
- the reference fix is the 4.x published fix for that route (395c64f0b80b): one recursive
  cleanser call in the layout save service.

The build/checks patches are the two wrong fixes the control must reject: a one-level
(top-only) cleanse that leaves the nested shapes reachable, and a blanket refusal that breaks
the legitimate layout save.

## Verified locally

- Pinned: 4/4 security tests fail, 7/7 functional tests pass.
- Reference: 4/4 security pass, 7/7 functional pass.
- `sf-nonrecursive.patch`: 2 nested security tests fail, functional pass.
- `ff-refuse-all.patch`: 1 functional test errors, all security pass.

## Gate

- static: PASSED.
- nop: PASSED — 4 security tests failing on the pinned tree, 7 functional tests passing.
- oracle: PASSED — 2/2 runs at reward 1.0 with identical results.
- patches: PASSED — `sf-nonrecursive.patch` fails the two nested security tests (functional
  clean); `ff-refuse-all.patch` fails the legitimate layout-save functional test.
