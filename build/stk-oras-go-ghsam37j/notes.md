# Build notes — stk-oras-go-ghsam37j (+ control)

- Start (UTC): 2026-10-26T02:05:50Z (job start; build work began on receipt)
- End (UTC): (filled after the gate stages)

## What was built

Stacked task on `oras-project/oras-go` pinned at `7a9f4b0b9558821b0422152ebe21ae56930fe764`
(the direct parent of the first published fix, `cc323e564d90`). Reference fix =
`cc323e` + `adab2f25` (the two published fixes) plus one repair for an uncovered route.

Concepts (independent reference edit sites):
1. **Extraction link containment** (`content/file/utils.go`): the unpack path validates a
   lexically joined link target and never inspects a member's final component before opening it.
   Traps T1 (chain whose lexical clean stays inside but whose kernel resolution leaves the root)
   and T2 (terminal link followed by `writeFile`). Fixed by an extra resolved-containment check
   before each member is created and by unlinking a terminal link before a regular member write.
2. **Hard-link application** (`content/file/utils.go`, TypeLink branch): `os.Link` is handed the
   raw archive linkname, so a relative name is applied against the process working directory
   rather than the path the check validated; it can alias a file outside the store, and a later
   same-named member writes through the alias. Trap T3. Fixed by resolving a relative hard-link
   name against the link's directory and passing the reconstructed path to `os.Link`.
3. **Push-path containment** (`content/file/file.go`, `resolveWritePath`): the check is lexical
   only, so a member name that traverses a link directory under the working directory passes it
   and `os.Create`/`MkdirAll` follow the link outside. Trap T4. Fixed by resolving symlinks on the
   deepest existing ancestor of the write target and comparing with the real working directory.

Trap types: T1 == `mimo` (how-type shape, hard/xhard in the reader record), T2 == `both`,
T3 == `deepseek` (uncovered route with the code's own "known limitation" dismissal, xhard/hard),
T4 == `deepseek` (parallel sink; hard/medium). DeepSeek-type: T3, T4 (also T2). MiMo-type:
T1, T2.

## Dropped from the reader's design

T5 (two spellings of one store name bypass the duplicate-name map) was **dropped**: it is
medium/medium for both models in the reader record (rule 2 needs hard/xhard for at least one), it
is a different protection (name identity / CAS integrity, not filesystem containment), and the
record's effort estimate was already 90 minutes against a 45–60 minute budget. The design keeps
three independent concepts, each hard on its own for at least one target model.

## Verified

- Every security test fails on the pinned tree through `file.Store.Push` (no reliance on a
  pre-applied fix): 8/8 fail, 9/9 functional pass.
- Reference fix: 8/8 security, 9/9 functional, and the project's own `go test ./content/file`
  all pass.
- `checks/upstream_first_fix.patch` (cc323e alone): 6 security tests fail, functional pass.
- `checks/upstream_fix.patch` (cc323e + adab2f): only the two hard-link security tests fail —
  the stack adds a real lever beyond upstream.
- Each concept miss patch leaves only that concept's security tests failing, functional pass.
- `pass-alt.patch` (different design: component walk on push, `O_NOFOLLOW` for regular writes,
  reject relative hard links) and `pass-hardening.patch` (reference + full-path resolution +
  `O_NOFOLLOW`) both score 1.0 locally.
- Wrong-fix patches: refuse-all and absolute-link-return break functional tests; lexical
  re-check, relative-link-unchecked and panic-as-refusal leave security tests failing.
- Control task: 4/4 advisory-route security tests fail on pinned and pass on its own reference;
  9/9 functional pass on pinned and on the reference; its check patches behave as declared.

## Could not verify

- The advisory texts themselves (GHSA-8xwf-rjm4-xvhv, GHSA-m37j-52j7-pjw7) were not fetched; the
  two published commits were read in a clone and their source diffs applied, but the H3 mapping
  is inferred: A (`cc323e`, push path) leaves B (`adab2f`, extraction) open, and B's fix calls the
  `checkSymlinkEscape` helper A added. The reader record's `b_in_code_a_wrote=true` is not borne
  out at the pinned tree (the vulnerable extraction and hard-link code predates A), so the record's
  H3u was resolved to H3b and the manifest says so.
- Whether the hard-link relative-linkname gap was ever publicly reported. It is fixed in current
  upstream by a later `extractHardLink` rewrite, so `present_in_latest=no` on the register rows,
  but `public_upstream_report=unknown`.
- Windows path handling was not analysed (no windows-specific source or test file).

## Notes

- `stacking.reader_record` points at `pipelines/stacking/out/reader-ds/h3-ghsa-m37j-52j7-pjw7.json`
  because that is where the DeepSeek reader wrote it; the path named in the build prompt
  (`out/reader/...`) does not exist in this checkout.
- Register rows were appended to `build/audit/uncovered-routes.tsv` for T2, T3 and T4.

## Gate results

- static: PASSED (stacking conformance: 3 concepts, H3b).
- nop: PASSED — 8/8 security tests fail on the pinned tree, 9/9 functional pass.
- oracle: PASSED — 3/3 runs at reward 1.0, identical results.
- patches: 8 of 12 checks gated in the container with exactly their declared outcome;
  the other 4 were re-queued in a trimmed follow-up because the shared VM (load average
  60–116, 140+ concurrent Harbor runs from other pipelines) made Docker's image
  build/artifact phases stall. Gated so far:
  - miss_concept_extraction: 4/8 security pass, 9/9 functional => security_fail ✓
  - miss_concept_push: 6/8 security pass, 9/9 functional => security_fail ✓
  - miss_concept_hardlink: 6/8 security pass, 9/9 functional => security_fail ✓
  - upstream_fix: 6/8 security pass, 9/9 functional => security_fail ✓
  - sf-relative-link-unchecked: 0/8 security pass => security_fail ✓
  - sf-panic: 4/5 security pass (binary aborts on the panic) => security_fail ✓
  - pass-alt: reward 1.0 ✓
  - pass-hardening: reward 1.0 ✓
  Every one of these matched its local dry run. A trimmed run for `upstream_first_fix`,
  `ff-refuse-symlinks`, `ff-absolute-link-return` and `sf-lexical-recheck` is in progress; all
  four also matched their declared outcomes in the local dry run.
- control: static PASSED; nop/oracle/patches pending (queued behind the same shared-VM load).
  Locally (same tests, same entry points, run as the pinned tree / the control's own reference
  patch): control nop = 4/4 security fail, 9/9 functional pass; control oracle = 13/13 pass;
  control patch checks all matched their declared outcomes (upstream_first_fix 4 security failures,
  ff-refuse-symlinks 5 functional failures, ff-absolute-link-return 3 functional failures,
  sf-lexical-recheck 4 security failures, sf-relative-link-unchecked 4 security failures,
  control-panic 1 security failure, pass-alt and pass-hardening 13/13).

### Shared-VM infrastructure notes

Under the load above, Harbor's per-trial phases (verifier image build, `docker compose cp` of
`/workspace`, environment teardown) intermittently take 10–30 minutes or deadlock at "Collecting
main service artifacts"; one trial also hit a transient `/tmp` (126 GB tmpfs) exhaustion while four
verifier images were exported at once. These are infrastructure stalls, not task failures: the
same trial inputs produced the expected results in the earlier waves and locally. The re-runs use
`TMPDIR` on the large root filesystem and serial execution.
