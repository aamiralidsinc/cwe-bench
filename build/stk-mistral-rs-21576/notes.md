# stk-mistral-rs-21576 build notes

Start (UTC): 2026-10-23T03:03Z (this session; the pipeline re-launched the builder and the task
tree from the earlier build was gone). The earlier build's verifier suites survived in the
`mistral-verifier-dbg` image and its check patches survived in `build/stk-mistral-rs-21576/checks`,
and every gate trial record survived under `~/.tb-graders/cwe/gate-jobs/`. The tree was rebuilt
from those, byte-for-byte where the records allowed it (the six hidden-suite files md5-match the
image that produced the passing runs; `solution/fix.patch` reproduces the oracle trial's restored
`/workspace` exactly).
End (UTC): 2026-10-23T05:59Z. Main task: static (only the later blind patch missing), nop, oracle
and patches all green. Control: nop green (security 0/4, functional 10/10), oracle 1.0 three times,
patches 4/4 (sf-partial-image 0.5, ff-local-removed 0.0, ff-refuse-all 0.0, pass-hardening 1.0).

## Levers (one line each)

- T1 (A, reported, MiMo-coupled): an image source from the request body reaches a public loader that
  accepts a bare server path, a `file:` URL and any http(s) host; wiring at chat_completion.rs:929.
- T2 (A, published far site): the same logic exists a second time for the audio part
  (util.rs:80-118), wired at chat_completion.rs:938.
- T3 (A, published far site): a third copy lives in the video module, presented as frame extraction
  (video.rs:52-80), wired at chat_completion.rs:947.
- T4 (A, how-type weak guard): the attachment URL guard judges the literal host text only, so a
  bracketed IPv6 literal, an IPv4-mapped literal and a name resolving to loopback pass
  (input_files.rs:103-164).
- T5 (coupled must-keep-working, MiMo): the same public loaders are the CLI/interactive and library
  entry points, so dropping local-file support breaks trusted in-process callers.
- T8 (B-shaped, injected route where the protection never existed, DeepSeek): a request-level
  on-disk attachment path read with `tokio::fs::read`; the published fix never touches it, so the
  recall patch leaves it open.

## Concepts (independent edit sites in the reference)

1. request-side media policy (T1, T2, T3) + the coupled local-loader behaviour (T5)
2. attachment URL validation on the resolved address (T4)
3. request-level on-disk attachment path (T8)

## Verified

- Pinned 7af17b62 is the direct parent of published fix 74793379 (`git rev-parse 74793379^`).
- Neither commit adds a regression test that the pinned tree already contains.
- `environment/injection.patch` (`git diff 7af17b62 99b248e4`) reproduces the nop trial's restored
  `/workspace`; `solution/fix.patch` (`git diff 99b248e4 7328a21c`) reproduces the oracle trial's
  restored `/workspace` file for file.
- Both patches and all 15 check patches apply with `patch -p1` to their bases.
- All check patches and the reference were re-derived from the gate job artifacts and the local
  clone; the previous gate run (records re-read) had nop 0.0 with 13/13 security failing and 10/10
  functional passing, oracle 1.0 three times with identical results, and every check patch at its
  declared outcome.
- This session re-ran static (only the declared-later `blind` patch is missing) and the container
  stages on the reconstructed tree; outcomes in `gate_report*.json`. First nop attempt failed as
  infra with a Dockerfile bug (the node tarball was extracted while the image was already the
  unprivileged user); fixed by moving that layer above the user switch. Re-run: nop passed with
  security 0/13 passing and functional 10/10 passing on the pinned tree. Oracle: three runs, each
  reward 1.0 with 23/23 tests (13 security + 10 functional) and identical results. Patches: the
  stage passed with all 11 checks at their declared outcomes (security failures 0.5385, 0.7692,
  0.8462, 0.8462, 0.8462 and 0.3077 with functional green; the two over-broad fixes 0.0; the
  alternative and hardening fixes 1.0; the recall patch 0.8462, leaving exactly the two on-disk
  attachment tests open). One check trial was lost to a Harbor egress-control error
  ("network_mode='no-network' is not supported by EnvironmentType.DOCKER environment"); the stage
  was re-run unchanged and passed.
- Control task: rebuilt the same way; its suite is the four image tests plus the same ten
  functional tests, its reference guards only the reported media kind. Prior control gate: nop 0.0
  (4/4 security failing), oracle 1.0 three times, 4/4 checks as declared.

## Could not verify

- The advisory text itself; scope comes from the screener/reader record and the code.
- Redirect re-validation and DNS-rebinding resistance are part of the stated property but are not
  exercised (an offline first hop that is publicly routable is not available).
- A fix that rejects every host name, including public ones, passes the offline suite; the
  preservation clause forbids it but no offline test can.
- The project's own crate unit tests were not re-run in this session (the prototype ran them:
  63 passed, 1 ignored); the graded verifier runs the hidden suites only.

## Design deviations

- The reader's design (T1, T3, T4, T5) is entirely covered by the published fix, so the mandated
  recall check would pass and the stack would add nothing. One injected route (T8) was added: a
  plausible operator-facing server-local path option for attachments, which the published fix never
  replaces. It is the DeepSeek-type lever.
- No real pattern-B route was used: the only uncovered upstream route in scope (the Python binding)
  is a trusted in-process caller by upstream's own design, so a test there would be unfair.
- `stacking/check_stack.py` in this repo expects `expect: "security_fail"` for concept and recall
  checks (the prose addendum says `"fail"`); the manifest uses `security_fail`, which both the
  behavioural gate and the conformance check accept.
- The verifier stages a test-support module into `mistralrs-core` at grading time because the
  `Pipeline` trait names crate-private types; a model-free server state cannot be built from
  outside the crate. It is never in the agent image.
