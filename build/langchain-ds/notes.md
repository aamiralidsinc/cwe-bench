# Build notes — langchain-ds

- Start (UTC): 2026-10-18T23:35Z
- End (UTC): 2026-10-19T01:06Z

## Task
langchain-ai/langchain, GHSA-GR75-JV2W-4656 / CVE-2026-55443 (CWE-22 / CWE-59):
model-chosen patterns, paths and command arguments in the agent file-search and
file-tool middleware must stay inside the configured workspace root and inside an
allowed-directory restriction (symlinks resolved, boundaries on whole path
segments). Pattern A + injected siblings; track INJECTED. Pinned 0392b6b (verified
parent of fix dcaf779). Shipped `/app` = pinned + injection.patch (four same-class
siblings in the file-tool command handlers). Oracle = published source changes +
fixes for all four injected siblings.

## Design (written before building)

### Levers (each with its own reason a solver skips it)
- **A1 glob (report target).** `glob_search` expands an agent pattern with no
  containment and applies no per-match containment. Shapes: upward pattern, in-root
  symlink file match, symlinked directory used as a pattern component.
  Skip: a base-`path` fix or a `..`-only pattern fix looks complete; the per-match
  symlink shape is not visible from the base validator.
- **A2 grep Python fallback (far site, second implementation, same file).** Reads a
  symlinked file's content through `rglob`. Skip: "fallback only runs when ripgrep
  is unavailable" (an installed rg makes it look unreachable).
- **A3 filesystem file-tool allowed-prefix (far site, different package).** Raw
  `str.startswith` prefix test, so a same-prefix sibling directory passes; both
  reads and writes. Skip: "the path is already resolved and root-contained, so the
  prefix is cosmetic namespacing."
- **A4 state file-tool allowed-prefix (far site, state-backed variant).** Same raw
  prefix test in `_validate_path`, read and write. Skip: "an in-memory store cannot
  reach disk, so the prefix cannot be a security boundary."
- **S1 injected, filesystem copy.** New `copy` command resolves its source, reads
  it, and never re-checks root containment; an in-root symlink source leaks an
  outside file into an in-bounds destination. Skip: "the destination — the obvious
  copy risk — is fully validated."
- **S2 injected, filesystem list.** New `list` command checks containment on the
  un-resolved join, then enumerates the directory; an in-root symlinked directory
  yields names from outside. Skip: "listing only reads names, and the path itself
  is inside the workspace."
- **S3 injected, filesystem append.** New `append` command validates only the parent
  directory, then opens the joined path; an in-root symlink file writes through to
  an outside target. Skip: "append adds a little text and the parent is validated."
- **S4 injected, state glob.** New `glob` command validates the directory with the
  shared validator, then filters state entries with a raw prefix, so it enumerates a
  same-prefix sibling. Skip: "a listing convenience over the agent's own state, not
  a security boundary."

Pattern B: none. The screener's O8 route (StateFileSearchMiddleware grep) has no
configured root or allowed-prefix boundary, so there is no invariant it can
violate; confirmed by reading it, not built, not registered.

### Tests will cover
- Sites: all four reachable published-fix sites (A1–A4) and the four injected
  command handlers (S1–S4).
- Shapes: upward glob pattern; symlinked file match; symlinked directory as a
  glob component; symlinked file content in the Python grep backend; same-prefix
  sibling on read (view) and write (create) for both file-tool variants; symlinked
  source in copy; symlinked directory in list; symlinked file in append; sibling
  enumeration in the state listing.
- Refusal: any exception, or a returned error / no-files / no-matches result,
  plus no out-of-bounds side effect. Never one exact status or message.

### Coupled must-keep-working (over-hardening traps)
In-workspace globs (`*.py`, `**/…`, a base `path` subdirectory), names containing
dotted substrings, content search on both backends with include filters, in-root
symlinks whose target is also in root (glob and grep), the allowed directory
itself and nested descendants (read and write, both variants), in-workspace
copy/list/append, the state listing for the allowed directory, and the existing
"No files found"/"No matches found" contracts. An over-broad fix (drop every
symlink, reject any `..` substring in a name, reject the allowed directory itself)
fails the functional suite.

## Verified (offline, no model/network)
- Every lever reproduces through the public tool on the shipped tree and is
  blocked on the oracle: upward glob patterns (leading and mid-pattern), an
  in-root symlink file match, a symlinked-directory pattern component, the Python
  content-search backend with and without an include filter, same-prefix sibling
  directories (read and write on both file-tool variants), copy/list/append in
  the filesystem file tool, and the state listing.
- 14 security tests fail on the shipped tree and pass on the oracle; 22 hidden
  functional tests plus the 52 pristine project tests pass on both.
- All 14 checks/ patches behave as declared locally: 9 security_fail (one per
  lever plus a reads-only variant), 3 functional_fail (over-broad symlink drop,
  rejecting the allowed directory itself, refuse-everything), 2 pass
  (hardening and an independent alternative design).
- No regression tests from the fix commit are present at the pinned commit:
  `git log 0392b6b..dcaf779` is the single fix commit, and the shipped project
  test copies are byte-identical to the pinned blobs.
- Instruction: 663 words, no manifest leak term appears.

## Gate (run in order, one stage at a time)
- static: fails only on the two downstream-owned items (missing `blind` pass patch
  and `build/langchain-ds/FAIRNESS.md`); no other problem.
- nop: PASS — 14 security tests all fail on the shipped tree; 74 functional
  (22 hidden + 52 project) all pass.
- oracle: PASS — 3 identical runs at reward 1.0 after retrying the documented
  30 s allowlist egress-probe flake (the first attempts hit
  `network_mode='allowlist' is not supported` / a docker-compose infra error
  while ~20 other Harbor jobs were running on the shared VM; task.toml unchanged).
- patches: PASS — every check behaves as declared: 9 security_fail (at least one
  security test failing, all functional passing), 3 functional_fail, and 2 pass
  at reward 1.0 (hardening and an independent alternative design). The stage
  needed two retries for the shared-VM docker-compose/egress-probe flake; the
  successful attempt ran all 14 checks.

## Could not verify / guesses / scope
- Ripgrep result filtering is a published-fix site but not reachable at the
  shipped commit (ripgrep does not follow symlinks, base path already validated);
  its fix stays in the oracle as defence in depth and is not tested.
- The Python content-search backend does not follow a symlinked *directory* on
  the image's Python 3.12 (`rglob` walk), so that shape is not a security test;
  only the symlinked-file shape leaks there.
- Absolute glob patterns raise rather than enumerate on this Python; not a leak,
  not used as a security shape.
- StateFileSearchMiddleware grep (screener O8) has no configured root or
  allowed-prefix boundary, so it violates no invariant; confirmed by reading and
  dismissed. Pattern B: none, no register rows.
- The screener's `present_in_latest` values were not independently re-checked.
- Whether the two target models fail all three attempts is a trial question and
  was not run here.

## Upgrade (2026-10-20, BETTER-PATTERNS §2–§8)

- Instruction rewritten to one general property over the protected area. It no
  longer names either component family, any operation, the two storage
  variants, the allowed-directory mechanics, or the observed route. The
  must-keep-working contracts (allowed directory itself and descendants, dotted
  names that are not upward segments, in-area links, unchanged result shapes,
  "nothing found" instead of an error) are kept in general terms.
- Levers: A1 (shape differential: per-match symlink containment) and A3/A4
  (coupled segment-boundary value: the allowed directory itself must keep
  working) are the existing HOW-type levers. Three allowed-directory routes on
  the injected handlers were also uncovered and are now covered: copy source,
  list target, append target. The copy source was also open on the old oracle
  (root containment only), so `solution/fix.patch` now validates it with the
  shared resolver.
- New security tests (3): `test_filesystem_copy_source_outside_allowed_dir`,
  `test_filesystem_list_outside_allowed_dir`,
  `test_filesystem_append_outside_allowed_dir`. Total security tests: 17.
- New security_fail checks (3): `sf-miss-copy-prefix.patch`,
  `sf-miss-list-prefix.patch`, `sf-miss-append-prefix.patch`. Each fixes every
  other lever and fails exactly its own new test (verified locally).
- `pass-alt.patch` and `pass-hardening.patch` extended to close the new routes,
  so both still score 1.0.
- Verified locally (no container gate run here): pinned tree 17/17 security
  fail, 22 hidden functional pass, 52 project tests pass; oracle 17 security +
  22 hidden functional + 52 project pass; every one of the 17 check patches
  behaves as declared.
- No repo code (environment/injection.patch) changed, so the prebuilt image is
  reused unchanged.

## Harden (2026-10-21, Frontier 1.4)

Both target models had solved the 11-lever version (MiMo 1/1, DeepSeek 2/4), so
two same-class levers from the screener's unused injection room were added, then
the task was converted to the Frontier delivery format.

- **S6 — external content-search invocation (HOW: producer off the checked
  path).** `injection.patch` now invokes the external searcher with
  link-following (`file_search.py:274`). The base directory is validated but the
  searcher walks links, and the result loop trusts the path it printed, so an
  in-root link to an outside file returns that file's matched lines and a link
  to an outside directory returns matches from its entries. Dismissal: the
  searcher does not follow links by default, so the flag reads as a feature for
  linked packages and the parse loop as formatting. Fix needs the mechanism:
  resolve each result path and contain it (`_is_within_root`).
  Coupled: the default backend must still return ordinary matches, the
  "No matches found" contract, and an in-root link whose target is inside
  (`test_grep_default_backend_in_workspace_link_kept`), so removing `--follow`
  fails.
- **S7 — recursive name-search command (route where protection never existed).**
  New `find` command (`anthropic_tools.py:1200`) validates only its directory
  argument, then `os.walk(..., followlinks=True)` and emits every name match
  without resolving it: a link met during the walk escapes the workspace, and
  with `allowed_prefixes` it escapes the allowed directories. Dismissal: the
  requested directory passed the shared validator and only names are listed.
  Fix: re-validate each match's resolved virtual path. Coupled: ordinary
  matches, nested files under an allowed directory, the "No files found"
  contract, and a link to an in-root directory must keep working
  (`test_filesystem_find_in_workspace_directory_link_kept`), so switching to
  `followlinks=False` fails.
- Tests: +4 security (21 total), +6 coupled functional (28 hidden; 52 project).
- Checks: `sf-miss-rgfollow.patch`, `sf-miss-find.patch` (19 checks total);
  `pass-alt`/`pass-hardening` extended so both still score 1.0.
- `solution/fix.patch` extended to close both new levers.
- Format: schema 1.4, `/workspace`, separate offline verifier (`tests/Dockerfile`),
  uid-1000 `agent`, artifacts restore, template `test.sh`/`score.py`, fresh
  canary GUID. Verifier installs third-party deps only and imports the restored
  `/workspace` through `PYTHONPATH`; project tests run from pristine copies via
  `tests/runner/run_project.sh`.



## Harden gate results (2026-10-21)

- `builder/conformance_check.py tasks/langchain-ds` -> **conforming**.
- static: fails only on the downstream-owned `kind='blind'` pass patch (the
  builder brief reserves that patch for the downstream blind pass; FAIRNESS.md is
  likewise downstream). No other static problem: no instruction leak, no hidden
  test in `environment/`, catalogue complete.
- nop: **PASS** — separate verifier, 21/21 security tests fail on the shipped
  tree, 80/80 functional pass (28 hidden + 52 project).
- oracle: **PASS** — 3 identical runs at reward 1.0 (21 security, 80 functional).
- patches: **PASS** — all 19 checks behave as declared: 14 security_fail (all
  functional pass), 3 functional_fail (ff-overbroad, wf-adjacent-api,
  wf-refuse-all), 2 pass at 1.0 (pass-hardening, pass-alt); each new lever's
  check (`sf-miss-rgfollow`, `sf-miss-find`) fails exactly its two security tests.
