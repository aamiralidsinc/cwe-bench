# stk-passenger-ghsaqw8w build notes

- Start (UTC): 2026-10-26T02:10:11Z
- End (UTC): 2026-10-26T05:05:00Z (gate could not complete on the shared VM)

## What this is

Passenger's temporary working locations. The pinned commit is the direct parent of the
earlier fix A (`34b10878`, GHSA-c7j7-p5jq-26ff, CVE-2014-1831), whose reuse check for the
predictable server instance directory used `stat`, so a pre-created link to a directory
with the right mode and owner was accepted. The later fix B (`94428057`, GHSA-qw8w-2xcp-xg59)
removed the window between two checks inside `initialize()` but left every later operation
resolving the same path by name.

## Levers (one line each)

- T1 (deepseek, advisory route): `ext/common/ServerInstanceDir.h:215-225,262-284` — the
  reuse branch classifies with `stat()` and verifies the resolved target, so a prepared link
  is accepted; the mode/owner check is the reason to dismiss it.
- T2 (both, how-type): `ext/common/ServerInstanceDir.h:73,104,306-354` — generation creation
  and destruction rebuild the path and resolve it again, so a directory replaced after the
  check redirects the write and the re-permissioning; the prior verification is the reason
  to dismiss it.
- T3 (deepseek): `lib/phusion_passenger/utils/tmpdir.rb:40-66` — a second implementation of
  the same predictable name reuses any existing entry and creates a 0777-style directory;
  its own "unit tests only" comment is the reason to dismiss it.
- T4 (mimo): `lib/phusion_passenger/platform_info.rb:237-295` — the executable probe is opened
  by fixed name with `File.open('w')`, chmodded and executed; the fixed one-line content,
  0700 and the ensure-unlink are the reasons to dismiss it, and the coupled value is the
  public contract that the helper keeps returning a writable, exec-capable directory.

Concepts: `[T1, T2]` (server instance directory), `[T3]` (Ruby temporary directory),
`[T4]` (executable probe).

## Verified

- The three attacks reproduce on the pinned checkout with a neutral C++ driver and Ruby
  helpers: pinned = 6/6 security fail, 7/7 functional pass (debian bookworm, ruby 3.1, g++ 12).
- The reference fix closes all six: 6/6 security pass, 7/7 functional pass.
- The project's own `ServerInstanceDirTest` (13 cases) is rebuilt from pristine copies staged
  by `test.sh` and passes on the pinned tree and on the reference.
- `upstream_first_fix.patch` (A alone) and `upstream_fix.patch` (A+B) both leave T2, T3 and T4
  failing, while their functional tests pass.
- `miss_serverinstancedir`, `miss_rubytmpdir` and `miss_tmpexedir` each leave only their own
  concept failing. `ff-refuse-all` breaks the legitimate reuse and the project test.
  `sf-crash-as-refusal` aborts instead of refusing and fails the T1/T2 checks.
  `sf-partial-route` leaves T3/T4 failing. `pass-hardening` and `pass-alt-openat` pass.
- The Git fetch of the pinned commit by SHA, the offline C++ build and the Ruby helpers were
  exercised locally and in a bookworm container.

## Not verified / known limits

- The screener record embedded in the build prompt names an installer probe, a C++ request
  buffer and a standalone config as T1/T3/T5. The installer probe and the standalone config
  cannot be driven through a real entry point without a full nginx install/runtime; the
  `FileBackedPipe` name embeds a heap address and cannot be prepared deterministically. Those
  three were not built. The actual advisory pair is the `ServerInstanceDir` fix-of-fix, which
  the reader record identified (and marked unusable because it assumed A was already present).
  This build substitutes the advisory route T1/T2 plus two reachable same-class
  implementations (T3, T4).
- The reader record at `pipelines/stacking/out/reader/h3-ghsa-qw8w-2xcp-xg59.json` says
  `usable: false`; see the discrepancy above. Its T1/T2 group is concept 1 here.
- The residual race inside `verifyStillOurs()` (between the re-check and the write) is not
  exercised; the hidden checks only replace the directory before the later operation.
- `present_in_latest` for the register: current upstream was read at `93548bc` (2026-10-26).
  `ServerInstanceDir.h` and `utils/tmpdir.rb` no longer exist there; the `tmpexedir` pattern
  is still present.
- The listing check was not run (it needs a reviewer model; the build brief forbids running
  target models).

## Outside the advisory's own protection

The installer probe (`bin/passenger-install-nginx-module`) and the crash-dump writer
(`ext/common/agents/Base.cpp`) show the same predictable-name pattern but were not built
into the task; they need a compiler-install run or a crash, so they are noted and left out.

## Gate status

- static: PASSED (`common/gate/gate.py --only static`; `check_stack.py` conforming, 3 concepts, H3a).
- nop/oracle/patches: the first attempts were blocked by a fleet-wide Docker compose teardown hang
  on the shared VM (load average 65-102; other builders' compose processes idle for 20+ minutes at
  the same phase). The stage is being retried when the machine allows; the result is recorded in
  `gate_report*.json`.
- control: static PASSED; nop/oracle/patches left for the pipeline, as in the other stacked builds.

### Gate results (shared VM)

- static: PASSED.
- nop: PASSED — 6/6 security tests fail on the pinned code, 7/7 functional pass
  (`gate-jobs/stk-passenger-ghsaqw8w-nop-1792984156`).
- oracle: launched three times. Attempts 1-2 stalled in Harbor's compose teardown while the
  shared VM was at load 65-102 (the same phase as other builders' trials). Attempt 3 ran after
  moving the gate's temp files off the 1M-inode `/tmp` tmpfs (`TMPDIR=build/<slug>/hosttmp`),
  which fixed the "no space left on device" build failure, but it was killed by its stage
  timeout at fleet load ~161 before a trial launched; a fourth attempt (longer budget) hit fleet
  load 461 and was killed at 04:53 with no Harbor job directory created. Re-run `--only oracle`
  and `--only patches` when the machine is quiet; the local harness and every check patch are
  already verified. The shared VM is in an infrastructure storm (load average 160-460); this is
  not a task result.
