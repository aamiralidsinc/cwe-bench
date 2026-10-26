# stk-froxlor-ghsa75h4 — build notes

Start (UTC): 2026-10-26T02:03:16Z
End (UTC): pending (Harbor gate in progress)

## What this task is

Stacked (H3b2) task on froxlor/froxlor at `a7b66227e6a41978ff7591eea8e82c48b6bedda1`, the first
parent of the earlier fix A (`9e8f32f1e860`, GHSA-4jch-8qq5-hqg6). The later fix B
(`2987b0e8806e`, GHSA-75h4-c557-j89r) is the advisory the task is named after. Reference fix =
A + B (source only) + fixes for the two uncovered routes.

## Levers (one line each)

- **T1 (A, advisory route)** — `DataDump.php:86-93,133`: the export destination is only normalised
  lexically and joined onto the document root, so a link inside the customer's folder is accepted;
  reason to dismiss: the join makes the path look forced under the home directory.
- **T3 (A, shape, MiMo-type)** — same call site: the destination does not exist yet, so the check
  has to resolve the deepest existing ancestor and follow a link to a link; reason to dismiss: a
  check can "just resolve the full path", and nobody needs a folder that does not exist.
- **T4 (A, far site, DeepSeek-type)** — `ExportCron.php:64-74,215-216`: the privileged consumer
  trusts the destination recorded in the task table and creates/exports into/re-owns it; reason to
  dismiss: the request command validates and is the only producer of these jobs.
- **T7 (B, uncovered upstream)** — `ExportCron.php:98-101,157-158,182-183,191-192,212-213`: the
  destination is inside the customer's folder but the customer owns its contents, so a per-format
  working folder can already be a link; reason to dismiss: everything below the destination already
  belongs to the customer.
- **T10 (B, uncovered upstream)** — `Statistics.php:156-161`: a second privileged implementation
  re-owns a directory built from the document root during the traffic run; reason to dismiss: the
  sub-directory name is a fixed setting and the path is built from the customer's own tree.

Concepts: `[T1,T3]`, `[T4]`, `[T7]`, `[T10]`. The reference fix's independent edit sites are: the
directory helper's containment boundary + the request call site; the consumer's stored-destination
re-check; the consumer's working-directory re-checks; the statistics ownership pass.

## Verified (locally, with the built images, by running the verifier's test.sh)

- Pinned tree: 8/8 security tests fail, 17/17 functional tests pass (7 hidden + 10 from the
  project's own `tests/Backup/DataDumpTest.php`).
- Reference fix: 25/25, reward 1.0.
- `upstream_first_fix.patch` (A alone): all security tests fail, every functional test passes.
- `upstream_fix.patch` (A + B together): the T4, T7 and T10 security tests still fail, every
  functional test passes — the stack adds more than upstream shipped.
- Each `miss_c*.patch` leaves only its own concept's security tests failing and all functional
  tests passing (independence of the four concepts).
- `functional_overbroad.patch` (any link below the folder refused): the two legitimate in-folder
  link tests fail.
- `alt_correct_fix.patch` (a realpath-resolver design without the shared helper's signature change)
  and `hardening.patch` (reference plus defensive checks in the privileged directory creation and
  before the working directory is removed): both 25/25, reward 1.0.
- Mechanism checks in the container: `chown -R` and `rm -rf` follow a command-line link with a
  trailing slash; `mkdir -p` succeeds through a link to an existing directory; a non-root process
  can hand its own file to its own primary group, which is how the ownership side effects are
  observed without running the suites as root.
- The project's own DataDumpTest passes on the pinned tree and on the reference fix, against a
  MariaDB loaded from the pinned schema by the verifier.
- Control task (`stk-froxlor-ghsa75h4-control`, published A+B reference, request route only):
  pinned tree 4 security failures / 17 functional passes; reference 21/21; `miss_c1` leaves the
  4 request security tests failing; the over-broad patch breaks the two legitimate in-folder-link
  functional tests.
- Exact local counts: pinned 17/25; reference 25/25; miss_c1 21/25 (4 security); miss_c2 24/25
  (1 security); miss_c3 23/25 (2 security); miss_c4 24/25 (1 security); A alone 17/25 (8
  security); A+B 21/25 (4 security); over-broad 23/25 (2 functional); alternative 25/25;
  hardening 25/25.

## Could not verify / guesses

- Harbor gate so far (2026-10-26): static PASSED; nop PASSED twice (trial
  `stk-froxlor-ghsa75h4-nop-1792983538/...__nCUD5Ze` and `-1792984497/...__NvTqsZx`: reward 0.0,
  8/8 security failing, 17/17 functional passing); oracle trials all scored 1.0 with identical
  (empty) failure sets (`stk-froxlor-ghsa75h4-oracle{1,2,3}-1792985*`). The oracle wrapper first
  reported `infra` only because three `harbor run` CLIs hung in post-trial cleanup on the
  saturated Docker daemon and had to be terminated; the trials themselves were complete. The
  oracle and patches stages are being re-run; see the gate report files for the final verdicts.
- The shared VM was heavily loaded throughout (load average 70-140 from other builders' trials);
  `harbor run` cleanup can take 15-20 minutes per trial there.
- The reader record is at `pipelines/stacking/out/reader-ds/h3-ghsa-75h4-c557-j89r.json`; the
  build prompt's `pipelines/stacking/out/reader/...` does not exist. The manifest points at the
  real path.
- The published fix commits were readable here (`git show`), unlike the screener's session, so the
  A/B split is confirmed rather than inferred: A touches the directory helper and its callers, B
  touches the export request and the consumer's final ownership step.
- Later upstream commits on the 2.x line (`de01620b`, `ea558864`, `0805a7e1`, 2026) close some of
  these shapes; they are *not* part of the task's reference fix, and the A+B recall check proves
  the reference stays short of them. The current `origin/main` is a restructured codebase and was
  not analysed.
- Whether the two target models actually fail all three attempts is for the trial stage; the reader
  scored this candidate 0.717 with p_fail3_deepseek 0.913 and p_fail3_mimo 0.786.

## Fairness notes (my own reading)

- The T4 route is only reachable with a task row that the request command would not produce today
  (a job recorded before the fix, or one recorded when the customer's folder looked different).
  The hidden test drives the real consumer with a row in the task table's own shape; the report
  covers it only through the general property. A blind solver has to decide, from the property
  alone, that the privileged consumer must not trust the stored destination. That is the
  DeepSeek-type difficulty the reader predicted, and it is the lever I would watch in a listing
  review.
- The keep-working values are deliberately generous (a not-yet-existing destination, a legitimate
  in-folder link, a name with dot runs, an export that still runs end to end, the statistics pass
  still handing ownership to the customer). They exist to fail an over-broad "no links anywhere"
  fix, which is the likely MiMo over-hardening.
- The report says nothing about which part of the system performs the privileged work, and no
  sentence was added for any one route.

## Out of scope, not built on

- The reader's T8/T9 (directory options, domain document roots) and the administrator-driven home
  creation task go through the same directory-creation helper and are hardened by the reference
  patch, but they are not tested; one line in the manifest records this.
