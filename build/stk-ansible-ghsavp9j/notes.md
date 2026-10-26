# stk-ansible-ghsavp9j — build notes

- Pipeline job start: 2026-10-26T02:03:53Z (the job's own build run failed with
  `claude-code:unrecognized_model`; this build was done manually in the builder session).
- Build work: 2026-10-26T02:10Z – 2026-10-26T04:20Z.
- Pinned commit `378434a148558c6f2d80e430aee3d5c7c3773bf3` (ansible stable-2.9).

## Advisory-input mismatch (read this first)

The build prompt names GHSA-g4mq-6fp5-qwcf / GHSA-vp9j-rghq-8jhh and published fixes
80b9a0a, 8251d9f, ecf99d5, 77d0eff, 84afa8e, ffd3757. Those are CVE-2020-1733 and CVE-2020-10744,
the **become-user remote temporary-directory pair**. I verified the pinned commit is the direct
parent of 80b9a0a and that the six commits touch only `lib/ansible/plugins/shell/__init__.py`,
`lib/ansible/plugins/action/__init__.py` and `lib/ansible/plugins/shell/powershell.py`.

The reader output (`pipelines/stacking/out/reader-ds/h3-ghsa-vp9j-rghq-8jhh.json`) and the host
notes describe the **vault temporary-file exposure** at the same pinned tree: a different
published advisory, GHSA-vcg8-98q8-g7mj / CVE-2020-1740, fixed by 28f9fbdb (devel) and 685a4b6d
(stable-2.9, 26 commits after the pin). The lead explicitly instructed building the reader's
design (traps T1–T5), and that design reproduces at the pin (verified below). The become-temp-dir
pair supports only two independent protections (the non-recursive leaf creation and its quoting;
verified by probing the pinned `mkdtemp` command, and the PowerShell copy already fails on an
existing target under `Set-StrictMode`), so it cannot meet the stacked ≥3-concept rule without
inventing a lever. I therefore built the reader's design and used the **real vault fix** for the
recall checks. If the intended task was the become-temp-dir pair, this task is a different (also
real and published) advisory; the pipeline inputs are inconsistent.

The prompt's `reader_record` path `pipelines/stacking/out/reader/h3-ghsa-vp9j-rghq-8jhh.json` does
not exist; the actual reader output is under `pipelines/stacking/out/reader-ds/`.

## Levers (one line each)

- T1 (deepseek, advisory_route; the permissions facet of the reported edit route): the library edit copy is written with the process default
  permissions; only a CLI-wide umask guards it — `lib/ansible/parsing/vault/__init__.py:1043-1082`.
  Reason to dismiss: the umask makes every CLI run look solved.
- T2 (both, advisory_route): the file receiving decrypted content is unlinked and re-created by
  name — `lib/ansible/parsing/vault/__init__.py:845-879,1076-1082`. Reason to dismiss: `mkstemp`
  already made a 0600 file.
- T3 (both, published_fix_far_site): the second decryption path creates its copy in the shared
  system temp dir and cleanup only unlinks it — `lib/ansible/parsing/dataloader.py:321-336,377-393`.
  Reason to dismiss: it writes through the mkstemp descriptor, so it looks like it follows the
  private-file convention.
- T4 (deepseek, uncovered_upstream): the final shred is not on every exit; a read/encrypt failure
  after the editor abandons the edited plaintext — `lib/ansible/parsing/vault/__init__.py:862-879`.
  Reason to dismiss: the editor-error and no-change paths already shred.
- T5 (mimo, coupled value): an existing encrypted file keeps its mode and ownership when rewritten
  — `lib/ansible/parsing/vault/__init__.py:1084-1097,1018-1022`. A blanket 0600 rule changes the
  users' files and breaks the coupled functional tests.

## Verified

- Pinned tree (Python 3.9.25, `python:3.9-slim-bookworm`): 0/4 security tests pass, 9/9 hidden
  functional pass, 23/23 project vault tests pass.
- Reference (`solution/fix.patch`, the CVE-2020-1740 fix plus the two uncovered-route fixes):
  4/4 security, 9/9 functional, 23/23 project.
- All 12 check patches were applied to a fresh pinned copy and matched their declared outcome:
  `reference`, `hardening`, `alternative` pass; `upstream_first_fix`, `upstream_fix`,
  `miss_write_data`, `miss_failure_shred`, `miss_dataloader` leave a security test failing with all
  functional tests passing; `refuse_all`, `crash_as_refusal`, `wrong_resource`, `adjacent_api`
  break at least one functional test.
- Gate: static PASSED (stacked and control); nop PASSED (4 security tests fail on the pinned code,
  9 hidden + 23 project functional tests pass).
- Oracle: two completed trials returned reward 1.0 (`oracle1` finished 03:49, `oracle2` finished 03:53);
  the third was cancelled by the builder's 50-minute background limit, not by a task failure. A
  three-run re-run was started but stopped when the shared Docker daemon saturated and queued it
  behind the patches stage; the two 1.0 runs, the local reference runs (4/4, 9/9, 23/23) and the
  `hardening`/`alternative` pass patches (which must also score 1.0) are the oracle evidence.
- Patches: every declared check was applied to a fresh pinned tree and run with the project's
  native runner in Python 3.9; all 12 matched their declared outcome (see `verified.local_runs`).
  The container patches stage could not start: the shared Docker daemon was at load 77–119 on
  8 CPUs with 105 running containers from an unrelated scale batch, so the 8 queued check trials
  stayed pending for >5 minutes and were stopped to reduce pressure. This is an infra block, not a
  task result; `build/stk-ansible-ghsavp9j/gate_summary.md` records the exact stage evidence.
- Control: container static PASSED; local suites pinned 0/4 security + 9/9 functional + 23/23
  project, reference (the published vault fix alone) 4/4 + 9/9 + 23/23. The control's container
  nop/oracle/patches were not run for the same shared-Docker-saturation reason.
- Container environment: the first nop attempt failed as an infra flake (Harbor's temporary compose
  file vanished under `/tmp` inode pressure, 84% of the tmpfs inodes in use by concurrent jobs).
  The gate must be run with `TMPDIR` pointing at a directory on `/` (the shared-VM workaround); the
  retry passed. No task content changed for the retry.
- Pattern B register rows appended for T3 and T4.

## Could not verify / unknowns

- The published become-temp-dir fixes cannot be used as this task's recall checks: they do not
  touch the vault. The recall checks use the real vault fix (28f9fbdb / 685a4b6d equivalent) and a
  later editor-exit fix; both still leave T3/T4 open on current devel (checked 2026-10-26).
- I did not run target-model trials (not allowed for the builder). The `score_at_build` row is
  copied verbatim from `pipelines/stacking/out/stack_scores_ds.tsv`; it scores the reader's
  four-group vault design, while this reference has three independent edit sites because T1/T2
  share one write path and T5 is the coupled value.
- The H3b1 label is the pipeline's; structurally this is an earlier-fix-residual (H3c-like) shape:
  the pinned tree already contains the 2015 umask/mkstemp hardening (00bc74404a8), and the later
  published fix (28f9fbdb/685a4b6d) completes part of it. Both recall checks are provided because
  the build prompt requires them for H3b1.
- `python:3.9-slim-bullseye` cannot be used: its Debian security archive moved and apt 404s. Both
  images use `python:3.9-slim-bookworm`; ansible's vendored `six` needs Python < 3.12.

## Scope note

The become-user temp-directory pair (CVE-2020-1733 / CVE-2020-10744) named in the build-prompt
inputs is a different advisory; I verified it but did not build on it because it cannot satisfy
the stacked rules. Not counted: the controller-side persistent-connection control directory and
socket (a different advisory family).
