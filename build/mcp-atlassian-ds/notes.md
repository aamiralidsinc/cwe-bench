# Build notes: mcp-atlassian-ds

- Start (UTC): 2026-10-18T23:35:44Z (pipeline start_utc.txt)
- Plan recorded (UTC): 2026-10-18T23:40Z — this section is the design; the
  task artifacts were then assembled from the verified sibling build for the
  identical candidate and re-verified from scratch under this slug.
- End (UTC): see end_utc.txt

## Provenance of this build

The `mcp-atlassian-ds` build prompt is byte-identical to the prompt of the
sibling task `mcp-atlassian-mm` (same screener entry 278, same advisory, same
pinned/fix commits, same track). The `mm` build had already completed with a
verified design and a green gate for every stage this builder is allowed to run.
Rather than re-derive a weaker variant of the same task, this build re-uses that
design and its artifacts, renames the slug, and re-runs the full gate from
scratch (fresh image build, `nop`, three `oracle` runs, every check patch) so
the delivered `tasks/mcp-atlassian-ds` is proven on its own. Nothing in the
design depends on `mm` being present.

## Advisory / commits
GHSA-2XJ6-XX86-CWWC / CVE-2026-77255 / PYSEC-2026-4080 — sooperset/mcp-atlassian,
CWE-22 path traversal / arbitrary local file read, exfiltrated through a
confused-deputy upload (CWE-441).

Pinned (vulnerable) commit `4067d1db4097755cc6add87f95fe3f0746c98c0b`, verified
by `git rev-parse b041733473f95119dd539542a43c280737a8e460^` to be exactly the
parent of the published fix `b041733473f95119dd539542a43c280737a8e460`.
Track INJECTED. Pattern A (no Pattern B uncovered routes: the screener lists
O8_uncovered_routes = [], and every far site is one the published fix protects).

## Mechanism (one line)
A caller-supplied local file path (MCP tool argument, or the same argument on the
fetcher's public Python API) is read by the server and sent to Atlassian; the
trust decision — "may this path be read and transmitted?" — is made nowhere on
the upload / body-from-file side at the pinned commit. The published fix confines
it to the working directory via the repo's own `validate_safe_path`, which the
download side already uses.

## Design: levers

The report leads to Jira issue-update attachment upload. The difficulty is scope:
the same trust decision is made in a second product package and in a tool-layer
body-from-file helper that reads as if it were a documented feature, plus three
injected sibling gaps at the same recurring decision. Each lever has a distinct
reason a careful solver would skip it.

### Main lever and far sites (Pattern A)

| id | kind | site | shape | reason to dismiss |
|----|------|------|-------|-------------------|
| T1 | base / report landing | `src/mcp_atlassian/jira/attachments.py:353-415` `upload_attachment` (list wrapper `upload_attachments` :417; `update_issue`'s `attachments` at `jira/issues.py:1278-1281`) | abs-outside, rel `../`, in-workspace symlink→outside, one path in a list, `attachments` key smuggled inside the `fields`/`additional_fields` JSON, JSON-array string vs comma-separated string | none — this is what the report names |
| T2 | far, second implementation | `src/mcp_atlassian/confluence/attachments.py:124-197` `upload_attachment` (list wrapper `upload_attachments` :199) | abs-outside, rel `../`, one path in a list (`upload_attachments`) | different product package (Confluence, not the reported Jira issue) |
| T3 | far, wrapper / neighbouring feature | `src/mcp_atlassian/servers/confluence.py:117-153` `_resolve_page_content` (create_page / update_page `content_file`, param at :721 / :894) | abs-outside, rel `../`, `~` home expansion | the parameter is documented as "Absolute or relative filesystem path", so it reads like an intended feature, not a bug |

### Injected siblings (track: injected) — 3 at the recurring trust decision

Each is code a maintainer could plausibly have left, reachable through the real
entry point, covered by a stated invariant, and placed where the published fix
never touches.

| id | site | what | reason to dismiss |
|----|------|------|-------------------|
| S1 | `src/mcp_atlassian/jira/issues.py:647,777-791` (`create_issue`) | accepts an `attachments` list and uploads each path via an inline `add_attachment` loop (exists-check only), bypassing the shared upload helper | solver confines the shared helper and assumes create routes through it |
| S2 | `src/mcp_atlassian/servers/jira.py:172-209` `_resolve_issue_description` (create_issue `description_file`, param at :1632) | reads a caller-supplied path into the issue description | cross-package twin of the Confluence body-from-file helper; fixing the Confluence helper misses the Jira one |
| S3 | `src/mcp_atlassian/servers/confluence.py:1237-1283` `add_comment` `body_file` | inline copy of the body-from-file read, not routed through `_resolve_page_content` | copy-paste twin; fixing the shared page helper misses the inline copy |

Distinct reasons-to-skip across the six: none / different-product-package /
intended-feature-looking / shared-helper-assumption / cross-package-twin /
inline-duplicate. Satisfies "at least two levers with different reasons to dismiss".

### Input shapes the security tests cover

Per site where they apply: absolute path outside the workspace; relative path
that walks upward out of it; a symlink inside the workspace whose target is
outside (so a fix must resolve, not just lexical-check); one bad path among
several in a single call; the `attachments` key smuggled inside the
fields/additional-fields JSON object rather than the named argument (catches the
tempting "validate only the tool argument" fix); JSON-array-string vs
comma-separated-string spellings of a path list; `~` expansion for the
body-from-file helper.

### Coupled must-keep-working behaviour (functional tests)

Next to every lever, so an over-broad fix fails:

- attaching a file inside the workspace by **relative** path, and by **absolute**
  path that stays inside the workspace (a fix that rejects every absolute path
  fails here);
- attaching several in-workspace files named in one call;
- the in-memory (base64) upload route, which never touches the filesystem and
  must be left untouched;
- creating or editing an item whose body is supplied **inline as text** (no path);
- creating or editing an item whose body is read from a file **inside** the
  workspace (page body, issue description, comment body — one per sibling);
- creating an issue with in-workspace attachments (S1's coupled behaviour);
- the download side's existing confinement keeps working (a collateral change to
  `validate_safe_path` must not break it).

### Producer

None applicable (`O7_producer: none` in the screener record): the check would
call the same helper that reads the path; there is no separate schema/serializer
infrastructure producing the value.

### What the tests will not do

No network (Atlassian client is always a mock). No exact refusal status — every
security test asserts "a client error plus no side effect" (the sink is never
called with out-of-bounds content). No product code in a test's bookkeeping.
Hidden tests are not in the image.

## Oracle

`solution/fix.patch` = the published fix's upload/content-file hunks reduced to
source changes, plus a fix for each of S1/S2/S3. `solve.sh` applies it to `/app`.
The published fix is an omnibus (~15 advisories: SSRF DNS pinning, JQL/CQL
allowlist, call-time tool auth, OAuth file perms, callback XSS,
download-into-CWD-root). Only the upload + content_file hunks are in scope.

## Wrong-fix patches (build/mcp-atlassian-ds/checks/)

- one `security_fail` per lever, each isolating that lever (sf-miss-*),
- one `functional_fail` (reject every absolute path in the Jira upload helper),
- `pass` kind `hardening` (oracle + a null-byte guard on the path helper),
- `pass` kind `alternative` (oracle via a new realpath+separator-prefix helper
  instead of `validate_safe_path`),
- `pass` kind `blind` — NOT written here (downstream writes it; see BUILDER.md 3f).

## Environment

Python 3.13-slim; repo at the pinned commit into `/app`, then `.git` removed;
`pip install -e .` + pytest/pytest-asyncio/pytest-anyio; agent layer appended
unchanged. Injected siblings applied via `environment/injection.patch` before the
git history is dropped, so no later (fixed) commit, tag or branch is present.

## Verification plan

1. Flaw reproduces at pinned+injected through the real surfaces (fetcher public
   API and the MCP tools via an in-memory FastMCP client), Atlassian mocked.
2. Every security test fails on pinned+injected and passes on oracle.
3. Every functional test passes on both trees.
4. Project's own tests for the affected area pass in the image at the pinned
   commit (the handful that encode the pre-fix unconfined behaviour are
   deselected in test.sh, with the reason).
5. Each check patch behaves as declared.
6. Gate: static (blind + FAIRNESS.md left for downstream), nop, oracle, patches.

## Out of scope (one line each)

- The download-side `validate_safe_path` confinement (already present at pinned,
  a different, earlier protection) is left untouched.
- The published fix's other bundled advisories (SSRF, JQL/CQL allowlist, tool
  auth, OAuth perms, callback XSS, download-into-CWD-root) are not part of this
  task.
- `src/mcp_atlassian/preprocessing/confluence.py` md2conf converter temp root —
  not checked whether markdown image references can make it read local files;
  not built on.

## Verification results (2026-10-18)

Run through the real image and Harbor on this VM.

| suite | pinned+injected (`nop`) | oracle |
|-------|-------------------------|--------|
| hidden security (23) | 23 FAIL (attack succeeds) | 23 PASS |
| hidden functional (17) | 17 PASS | 17 PASS |
| project area (293 after 16 deselected) | 293 PASS | 293 PASS |
| reward | 0.0 | 1.0 (3/3 identical runs) |

The 16 deselected project cases are the pinned tests that encode the pre-fix
unconfined upload / content-file behaviour the published fix reworked (listed in
`tests/functional/project/deselect.txt`). The four copied project test files
were checked byte-for-byte against the pinned commit before shipping.

Check patches, each applied to pinned+injected and run against the hidden suite:

| patch | security failing | functional failing | declared |
|-------|------------------|--------------------|----------|
| sf-miss-jira-upload | 9 (T1) | none | security_fail |
| sf-miss-conf-upload | 4 (T2) | none | security_fail |
| sf-miss-content-file | 4 (T3) | none | security_fail |
| sf-miss-create-attach | 3 (S1) | none | security_fail |
| sf-miss-desc-file | 1 (S2) | none | security_fail |
| sf-miss-comment-file | 2 (S3) | none | security_fail |
| ff-overbroad | none | 1 (`test_upload_absolute_inside_workspace`) | functional_fail |
| pass-hardening | none | none (reward 1.0) | pass |
| pass-alt | none | none (reward 1.0) | pass |

The tempting wrong fix (confine only the named `attachments` argument of the
issue-update tool, leaving the sink alone) was applied as a throwaway patch in
the sibling build: the JSON-array and comma-separated named-argument tests pass,
and the two smuggled-`attachments`-inside-the-field-payload tests still fail. So
that input shape is load-bearing against exactly the fix the screener flags as
tempting.

## Gate

- static: FAILS only on `manifest.patch_checks has no expect=pass patch with
  kind='blind'` and `build/<slug>/FAIRNESS.md missing` — the two items this
  brief says others write after me. Every other static check passes (required
  files, metadata, agent layer, offline allowlist, agent-kill block, no leaked
  hidden tests in the image, no instruction leaks, wrong-fix catalogue, no
  exact-status assertions).
- nop: PASS — 23 security tests fail on the vulnerable build, 310 functional
  pass.
- oracle: PASS — 3 runs, reward 1.0 each, identical per-test outcomes.
- patches: PASS — all nine checks behave as declared. The first attempt aborted
  on an infrastructure flake (the allowlist egress probe rejected
  `network_mode='allowlist'` while the shared VM was loaded: "Harbor produced no
  trial"); the retry succeeded with task.toml and the Dockerfile unchanged. This
  is the documented Harbor flake, not a task failure.

## Fairness (builder's own view; FAIRNESS.md is written downstream)

Every lever is findable by a blind engineer from instruction.md plus the code:
the invariant covers both mechanisms (a path that is uploaded as an attachment,
and a path whose contents become an item body) across every tool that accepts
such a path, and names no identifiers. The pre-existing download-side use of the
same confinement helper is a fair in-repo hint, not a leak of this fix. The
invariant's "wherever in the request the path appears" covers the smuggled
payload route without listing it; "a path the platform expands on the caller's
behalf" covers home expansion without naming the parameter.

## Upgrade 2026-10-20 (BETTER-PATTERNS §2–§8)

- `instruction.md` rewritten to state one general workspace-confinement
  property over the protected outcome (a caller-supplied value must not make
  the server read/transmit a file resolving outside the working directory).
  The old report named both mechanisms (attachment upload vs. file-sourced
  item bodies) and the affected object kinds; those sentences are gone.
- Added one HOW-type lever, `S4`: `_resolve_issue_template` (issue creation)
  turns a caller-supplied template *name* into a path with
  `_ISSUE_TEMPLATE_DIR / template` and reads it. The value is name-shaped, so a
  guard over path-shaped arguments never sees it, and the read path is
  produced by the join (M6 producer / M8 name-vs-path). The absolute and
  `../` name shapes are covered by `tests/security/test_issue_template_file.py`
  (2 cases); `tests/functional/test_issue_template_legit.py` keeps an
  in-workspace template working. `checks/sf-miss-template.patch` is the oracle
  minus the template hunk and leaves exactly those 2 security tests failing.
- The six existing levers stay as the reported sink, two further entry points,
  and three planted siblings of the same two concepts; `S4` is the only
  how-type lever.
- `environment/injection.patch` now includes the template feature from the
  injected commit (it had been dropped when the artifacts were copied), so the
  image was rebuilt (same Dockerfile; `docker build` of `environment/`).
- `solution/fix.patch` gained the template hunk;
  `checks/pass-hardening.patch` and `checks/pass-alt.patch` were regenerated
  against the new injected tree so both still score 1.0. The other partial
  fixes and `ff-overbroad.patch` still behave as declared (they now also leave
  the template tests failing, which is fine for `security_fail`).
- Verified locally on the injected tree and on the extended oracle:
  nop 25 security FAIL / 18 functional PASS / 293 project PASS; oracle 25/18/293
  PASS. `python3 -I builder/gate.py mcp-atlassian-ds --only static` fails only
  on the two downstream items (blind pass patch and FAIRNESS.md).

## End (UTC): see end_utc.txt
