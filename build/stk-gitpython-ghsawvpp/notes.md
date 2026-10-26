# stk-gitpython-ghsawvpp — build notes

Start (UTC): 2026-10-23T02:59:27Z
Reconstruct + re-verify start (UTC): 2026-10-23T03:00Z
End (UTC): 2026-10-23T05:58:22Z

Stacked H3a task on gitpython-developers/GitPython. Pinned faf3c09038b03bc2bdd8545ef34bbf6d7f1cd11f,
which `git rev-parse e8d0fbf774d1^` confirms is the direct parent of fix A. Fix B
96a888f4d782bc2e is on the same line (its parent a495ccd3 contains A). The pinned tree contains
neither A's nor B's regression tests (`git show e8d0fbf/96a888f4 -- test/` only adds them).

The task tree was reconstructed from the surviving verified scratch snapshot
(`~/.tb-graders/cwe/work/stk-gitpython-ghsawvpp/snapshot`) with the complete reference recovered
from `reference.patch` (the snapshot's own `solution/fix.patch` was an earlier truncated artifact),
and every check patch was stripped of the fuzzing-symlink noise the earlier patch generator carried.

## Levers (one line each)

- **T1 (advisory route, both models).** `Git._option_candidates` (`git/cmd.py:1039-1047`) screens only
  the keyword name, so a dash-prefixed value of a split single-character clone option becomes its own
  argv token, and the joined `-<char><value>` token under `split_single_char_options=False` never
  reaches the checker; scalars and sequences alike. Reason to dismiss: the reported example is one
  spelling, so the name-level check looks complete.
- **T2 (published-fix far site, DeepSeek).** The same builder backs `Repo.archive`
  (`git/repo/base.py:1680-1692`); a dash-prefixed value becomes `--output=<path>`. Reason to dismiss:
  the report names clone, and archive's output option writes a file rather than running a command.
- **T5 (uncovered upstream, DeepSeek).** The remote-listing blocklist (`git/cmd.py:650-655`, guard at
  `git/cmd.py:1117-1119`) names `--upload-pack` but not git's `--exec` alias, which runs the program
  (verified on git 2.47.3: `git ls-remote --exec=<prog>` executes it). Reason to dismiss:
  "upload-pack is already blocked".
- **T6 (uncovered upstream, DeepSeek).** `Diffable.diff` (`git/diff.py:188-277`) forwards caller
  keywords with no screening while sibling revision operations screen theirs; `--output` writes the
  caller's path (git diff has no short `-o`, so the reference's `-o` entry is defensive). Reason to
  dismiss: diff reads as a read-only comparison and its keywords as developer flags.
- **T7 (coupled MiMo value).** The legitimate joined rendering must keep working: `-oupstream`
  (multi_options), `o="upstream"`, `-bcurrent`, and the joined `-M75%` similarity value. An
  over-broad character scan or a refused split mode breaks them (`checks/adjacent_api.patch`).

Concepts (one reference-fix edit site each): C1 = [T1,T2,T7] (`_option_candidates`), C2 = [T5]
(remote-listing blocklist), C3 = [T6] (diff guard). T7 sits in C1 because it is the coupled value of
the same builder, so it cannot carry its own `security_fail` check (that contract requires every
functional test to pass); the over-broad form is the `functional_fail` check instead.

## Verified

- All cleaned patches apply to the pinned copy (`git apply --check`).
- No-Docker reproduction with the project's own runner on fresh pinned copies: pinned 0/8 security
  pass with all 28 functional/project tests passing; reference 8/8 and 28/28. Every one of the 18
  executable check patches (10 main, 8 control) reproduced its declared outcome in that harness, and
  the container gate then reproduced the same outcomes (below).
- `stacking/check_stack.py` reports conforming (3 concepts, pattern H3a); `conformance_check.py`
  passes for both the task and the control; gate `static` passes for the task.
- Current upstream `origin/main` (ccc48117) contains both `--exec` in the remote-listing blocklist
  and a diff-path guard (commit 1b0d2d9b, later advisories GHSA-5xxx-qhh7-9287 /
  GHSA-3wxw-xv34-2frg), confirming T5/T6 are real unmodified code at the pin that this advisory's
  published fixes never touched.

## Container gate

Run one stage at a time through a probe-gated retry loop because the shared VM's Harbor
`network_mode='no-network'` egress probe intermittently exceeds its 30 s budget under load.

- static: PASSED.
- nop: PASSED — 8/8 security tests fail on the pinned code, 28/28 functional tests (8 hidden +
  20 project) pass.
- oracle: PASSED — 3 runs, reward 1.0 and identical (8/8 security, 28/28 functional each).
- patches: PASSED — all 10 checks matched their declared outcome (two internal `harbor run`
  startup probes flaked under load; the stage was re-run and passed): `missing_candidate_builder`
  5 security fail / 0 functional; `missing_diff_guard` 2 / 0; `missing_remote_alias` 1 / 0;
  `upstream_first_fix` (A alone) 5 / 0; `upstream_fix` (A+B) 3 / 0; `hardening` 1.0;
  `alternative` 1.0; `refuse_all` 0 / 19; `crash_as_refusal` 6 security + 5 functional;
  `adjacent_api` 0 / 3.

The control task's stages follow.

## Control task

`stk-gitpython-ghsawvpp-control` uses the same pinned code and the same report, but only the reported
clone route (4 security tests) and the published A+B fix as its reference. Its gate is green (see
below).

## Control task gate (`stk-gitpython-ghsawvpp-control`)

- static: PASSED.
- nop: PASSED — 4/4 security tests fail on the pinned code, 28/28 functional tests pass.
- oracle: PASSED — 3 runs at reward 1.0 and identical (4/4 security, 28/28 functional each).
- patches: PASSED — all 8 checks matched: `upstream_first_fix` security_fail (2/0),
  `missing_candidate_builder` security_fail (4/0), `upstream_fix` pass 1.0, `hardening` pass 1.0,
  `alternative` pass 1.0, `refuse_all` 0/19 functional, `crash_as_refusal` 2/5,
  `adjacent_api` 0/3.

## Could not verify / guesses / fairness judgement

- **`--exec` discoverability (main fairness call).** `git ls-remote -h` and the 2.47.3 man page list
  only `--upload-pack`; `--exec` is accepted and visible in the binary, and later upstream added it
  as dangerous. The report says "whatever the option is called"; the lever rests on git knowledge
  beyond the man page. Recorded as the task's hardest fairness judgement.
- T5's exploit shape (remote listing running the program) is git-binary behaviour and was verified
  inside the verifier container, not in the repository.
- Diff's short `-o` does not exist in git 2.47.3, so that entry in the reference blocklist is
  defensive; the tests use `--output`.
- The archive route is exercised through a dash-prefixed value in split rendering only; clustered
  `-vo<path>` is rejected by git 2.47.3, so no joined-token archive test exists.
- Trials were not run here (the build prompt forbids running target models); the bar is unknown
  until the trial batch.
- **Tooling conflict (reported, not worked around).** `run_blindfix.sh` still extracts `/app` from
  the task image, while the Frontier 1.4 template used here keeps the checkout in `/workspace`.
  The pipeline's blind step will fail with "could not extract /app" until that script is updated;
  adding a duplicate `/app` tree would deviate from the template.
- The main task's `crash_as_refusal` also breaks 5 project tests because the published API's
  documented error type changes; that is why it is declared `functional_fail`, not `security_fail`.

## Outside scope (one line)

The later upstream commit 1b0d2d9b (other advisories) also closes T5/T6; nothing was built on
those advisories' other changes.
