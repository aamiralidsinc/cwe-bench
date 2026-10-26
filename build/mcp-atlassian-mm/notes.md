# Build notes: mcp-atlassian-mm

- Start (UTC): 2026-10-18T22:08:08Z (pipeline start_utc.txt)
- Plan written (UTC): 2026-10-18T22:14:32Z — this section is the design, written
  before any task file is created.
- End (UTC): (see end_utc.txt)

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

## Wrong-fix patches (build/mcp-atlassian-mm/checks/)

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

Local runs against the scratch tree
(`~/.tb-graders/cwe/work/mcp-atlassian-mm/repo`, branches `injbranch` =
pinned+inject, `oracle` = +fix; venv via `uv`, Python 3.13):

| suite | pinned+injected | oracle |
|-------|-----------------|--------|
| tests/security (23) | 23 FAIL (attack succeeds) | 23 PASS |
| tests/functional (17, excl. project/) | 17 PASS | 17 PASS |
| project area (293 after 16 deselected) | 293 PASS | 293 PASS |

Check patches, each applied to pinned+injected and run against the hidden suite:

| patch | security | functional | declared |
|-------|----------|------------|----------|
| sf-miss-jira-upload | 9 fail / 14 pass | 17 pass | security_fail |
| sf-miss-conf-upload | 4 fail / 19 pass | 17 pass | security_fail |
| sf-miss-content-file | 4 fail / 19 pass | 17 pass | security_fail |
| sf-miss-create-attach | 3 fail / 20 pass | 17 pass | security_fail |
| sf-miss-desc-file | 1 fail / 22 pass | 17 pass | security_fail |
| sf-miss-comment-file | 2 fail / 21 pass | 17 pass | security_fail |
| ff-overbroad | 23 pass | 1 fail / 16 pass | functional_fail |
| pass-hardening | 23 pass | 17 pass | pass |
| pass-alt | 23 pass | 17 pass | pass |

The tempting wrong fix (confine only the named `attachments` argument of the
issue-update tool, leaving the sink alone) was applied as a throwaway patch: the
JSON-array and comma-separated named-argument tests pass, and the two
smuggled-`attachments`-inside-the-field-payload tests still fail. So that input
shape is load-bearing against exactly the fix the screener flags as tempting.

## Gate

- static: only `checks/blind.patch` and `build/.../FAIRNESS.md` missing — the
  two items this brief says others write after me. Nothing else outstanding.
- nop: PASS.
- oracle: PASS.
- patches: PASS on retry attempt 4 (2026-10-18T23:49Z), after three
  infrastructure flakes on the VM's `docker network prune -f` race
  (attempts 1–3 each reached 5–7 of 9 checks: `chk-ff-overbroad` ×2,
  `chk-sf-miss-desc-file` ×1, under load average ~20–43 with ~10 concurrent
  gate jobs from other sessions). Retry loop: 12 attempts, 25 s backoff,
  flake-only (`Docker compose command failed|network .* not found|ValueError`).
  Task.toml and the Dockerfile are unchanged. `manifest.patch_checks` lists
  `blind.patch` (kept in the manifest; the file itself is written downstream).

## Fairness (builder's own view; FAIRNESS.md is written downstream)

Every lever is findable by a blind engineer from instruction.md plus the code:
the invariant covers both mechanisms (a path that is uploaded as an attachment,
and a path whose contents become an item body) across every tool that accepts
such a path, and names no identifiers. The pre-existing download-side use of the
same confinement helper is a fair in-repo hint, not a leak of this fix. The
invariant's "wherever in the request the path appears" covers the smuggled
payload route without listing it; "a path the platform expands on the caller's
behalf" covers home expansion without naming the parameter.

## End (UTC): see end_utc.txt
