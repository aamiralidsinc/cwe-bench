# stk-uri-js-ghsagcv8 — build notes

Start: 2026-10-23T07:41:02Z (pipeline restart; this build session)
End:   2026-10-23T08:35:00Z

Stacked H3a task on medialize/URI.js. Pinned 622db6d8d6e650d6de4300c97779de50e3331095
(1.19.6); `git log` in the pinned clone confirms it is the first parent of A's fix
ac43ca8f80c0 (1.19.7). B's fix 6ea641cc8648 (1.19.8) is one release later on the same line.

This session rebuilt the task after `stacking/stacking_restart.sh` deleted `tasks/<slug>`,
`tasks/<slug>-control` and `build/<slug>/manifest.json` and relaunched the queue. The recovered
`build/<slug>/checks/*.patch`, the variant sources and the notes survived; the verifier image
`stk-uri-js-ghsagcv8__*__verifier__trial-main` still held the full `/tests` tree, which was
extracted and reused verbatim (instruction.md and task.toml were rewritten; both were deleted).

## Levers (one line each)

- **T1 (A, advisory route)** — the authority marker after a web scheme may be written as any run
  of slashes/backslashes, including none; the parser only accepts exactly two. src/URI.js:523,529,534.
  Reason to dismiss: the reported example is one delimiter shape, so checking the two characters
  after the colon looks complete.
- **T2 (A, same concept)** — the same normalisation with an upper/mixed-case scheme. src/URI.js:525,529.
  Reason to dismiss: a lower-case web-scheme allowlist looks complete.
- **T3 (B, uncovered upstream, DeepSeek-type)** — scheme-relative references whose leading run is
  not exactly `//` (`\\host`, `/\host`, `///host`) are parsed as paths. src/URI.js:516,519,521.
  Reason to dismiss: no scheme in the input, so it reads as a path-relative reference outside a
  report about the scheme delimiter. Real upstream; fixed later in 1.19.11 (88805fd).
- **T4 (coupled, MiMo-type)** — the normalisation must stay scoped: food:///, file:///,
  `user:pass@host` as a URN, mailto:, javascript:, data:, tel, custom:, an empty-scheme authority,
  plain paths and literal spaces keep their exact parse and must not gain a host.
  src/URI.js:523,529,535,536. Tested functionally; the over-broad normaliser is the
  `functional_overbroad` patch.
- **T5 (B, uncovered upstream, DeepSeek-type)** — leading C0/space and tab/CR/LF are not dropped
  before the scheme is classified; embedded tab/LF inside the delimiter break it.
  src/URI.js:490,516,523,526. Reason to dismiss: an untrimmed string is not a well-formed URL and
  trimming looks like the caller's job. Real upstream; fixed later in 1.19.9 (86d1052) and
  1.19.11 (b0c9796).

Concepts (manifest.stacking.concepts): [T1,T2,T4] (one edit site: the scoped delimiter
normalisation), [T3], [T5]. T4 is grouped with the delimiter concept because the same edit has to
scope it; a fix that "misses T4" is necessarily the over-broad normaliser, which breaks the
functional values rather than leaving a security test failing — so T4 cannot carry its own
security_fail check without contradicting the score contract (security_fail requires all functional
tests pass). Every other trap is a security concept with its own miss patch.

## Verified in this session

- Pinned behaviour, locally with node before any container run: 30/30 security cases fail on the
  pinned tree; 20/20 functional API cases pass; the recovered project fixtures are byte-identical
  to the pinned `test/` files.
- Every check variant re-run locally: upstream_first_fix 18 security failing; upstream_fix 13;
  miss_delimiter 18; miss_case_variant 5; miss_scheme_relative 6; miss_whitespace 7;
  functional_overbroad 0 security / 9 of 20 API functional cases failing; alt_correct_fix and
  hardening clean. Matches the pre-reset build's gate numbers.
- The reference `fix.patch` reproduces the reference source exactly (sha256 match) and closes
  30/30 security with 20/20 functional.
- `stacking/check_stack.py`: conforming (3 concepts, H3a).
- Container gate: static PASSED (main and control), nop PASSED, oracle PASSED (3 runs, 1.0).

## Could not verify / guesses

- Which schemes count as "web": upstream's later fix used http, https, ftp, ws, wss. `file:` is
  special to browsers but the project's own fixtures require it to keep an empty host, so it is
  not normalised and no hidden test requires it.
- `src/URI.min.js` is a shipped build artifact of `src/URI.js`; the hidden suites target
  `src/URI.js` (package.json `main`), because a source fix does not regenerate the artifact.
- The report's invariant is browser-parity of the reported host, stated over any URL string,
  with a preservation clause for today's host-less parses, stored scheme case and scheme-less
  references. The example is marked as one illustration, not the full set.
- `run_blindfix.sh` extracts `/app`, while the harness requires `/workspace`; the environment
  image therefore also carries a pristine read-only copy at `/app` (never part of the artifact),
  so the blind stage can run. Its patch paths are repo-relative and apply to `/workspace`.
- Trials were not run (the build prompt forbids running target models here); the bar is unknown
  until the trial batch.

## Container gate

- static: PASSED (main and control)
- nop: PASSED — 30/30 security fail on the pinned tree, 186/186 functional pass
- oracle: PASSED — 3 identical runs at reward 1.0
- patches: PASSED 9/9 (the blind entry is skipped until run_blindfix produces checks/blind.patch)
  - miss_delimiter — 18 security failing (T1 12, T2 5, plus the combined leading-space/no-slash
    case), functional all pass
  - miss_case_variant — 5 security failing (T2), functional all pass
  - miss_scheme_relative — 6 security failing (T3), functional all pass
  - miss_whitespace — 7 security failing (T5), functional all pass
  - functional_overbroad — 36 functional failing, security all pass
  - upstream_fix (A+B) — 13 security failing (T3 6, T5 7), functional all pass
  - upstream_first_fix (A alone) — 18 security failing (T1 12, T2 5, T5 7, minus overlaps), functional all pass
  - alt_correct_fix — reward 1.0
  - hardening — reward 1.0
- control task (`stk-uri-js-ghsagcv8-control`, advisory route only; 17 security cases):
  static PASSED; nop PASSED (17 security failing, 186 functional passing); oracle PASSED
  (2 identical runs at 1.0); patches PASSED 2/2 (control_miss_case_variant security_fail 5/0;
  control_overbroad functional_fail 36).

Each stage was run separately (`--only`), which is why only `gate_report.partial.json` exists in
this directory; the queue's full `gate.py` run writes the final report. All four stages printed
PASSED. The host's Harbor egress-kernel probe is the known flake under load; no stage needed a
retry in this run.
