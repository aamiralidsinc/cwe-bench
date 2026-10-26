# stk-passenger-ghsaqw8w-control build notes

- Start (UTC): 2026-10-26T02:10:11Z
- End (UTC): pending (gate running)

This is the one-bug control for `stk-passenger-ghsaqw8w`. It uses the same pinned commit,
the same `instruction.md` (byte-identical) and the same image, but only the advisory's own
route is in the security tests and in the reference.

## Levers (one line each)

- T1 (deepseek, advisory route): `ext/common/ServerInstanceDir.h:215-225,262-284` — the
  reuse branch classifies with `stat()` and verifies the resolved target, so a prepared link
  to a directory with the right mode and owner is accepted; the mode/owner check is the
  reason to dismiss it.
- T2 (both, how-type): `ext/common/ServerInstanceDir.h:73,104,306-354` — generation creation
  and destruction rebuild the path and resolve it again, so a directory replaced after the
  check redirects the write and the re-permissioning.

## Verified

- Pinned: 4/4 security fail, 7/7 functional pass.
- Reference (the server-instance-directory part of the stacked fix): 4/4 security pass,
  7/7 functional pass.
- `upstream_first_fix.patch` (A alone) and `upstream_fix.patch` (A+B) both leave T2 failing
  while their functional tests pass.
- `ff-refuse-all` breaks the legitimate reuse and the project test; `sf-crash-as-refusal`
  aborts and fails the security checks; `pass-hardening` passes everything.
- The project's own `ServerInstanceDirTest` (13 cases) passes on the pinned tree and on the
  reference.

## Not verified / known limits

- The same build-window limits as the stacked task: the current-upstream read and the
  listing review were not done here.
