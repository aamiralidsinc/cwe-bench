# stk-nanoid-7632-control — control task

One-bug twin of `stk-nanoid-7632` (stacking rule 13). Same pinned code, byte-identical
`instruction.md`, the same hidden functional suite and the same project tests; only the advisory's
own route is covered by the security cases and by the reference fix.

- Security cases: four shapes of the advisory route (zero default, zero call size, negative call
  size, negative default) through the package-root generator. They fail on the pinned tree and pass
  with `solution/fix.patch` (`size <= 0` → empty string inside the closure).
- `checks/control_miss_node.patch` applies the same published decision to the other shipped copy
  only, so the advisory route still blocks: `security_fail`, functional green.
- `checks/control_overbroad.patch` refuses every size that is not a primitive integer: it fails the
  coupled functional cases (numeric string and fractional sizes), so it is `functional_fail`.
- Instrumentation, runner and project-test staging are identical to the stacked task; see
  `build/stk-nanoid-7632/notes.md` for the verification record.
