# Build notes: mcp-atlassian-path-inj

- Start (UTC): 2026-10-18 10:07
- End (UTC): 2026-10-18 (see end_utc.txt)

## Advisory / commits
GHSA-2XJ6-XX86-CWWC / CVE-2026-77255 — sooperset/mcp-atlassian, CWE-22 arbitrary
local file read + CWE-441 confused-deputy exfiltration. Pinned (vulnerable)
`4067d1db4097755cc6add87f95fe3f0746c98c0b`, verified parent of fix
`b041733473f95119dd539542a43c280737a8e460`. Track INJECTED, pattern A + injected
siblings. Shares the sibling-injection recipe with [[langchain-path-escape-inj-build]].

## Mechanism (one line)
A caller-supplied local file path (MCP tool argument / fetcher public API) is
read by the server and sent to Atlassian; it must be confined to the working
directory (symlinks resolved). The published fix routes it through
`validate_safe_path`.

## Levers (6; all verified nop-fail / oracle-pass offline)
- T1 base (A, report): Jira attachment upload (`jira/attachments.py` upload_attachment,
  + upload_attachments list, + update_issue attachments). Shapes: absolute-outside,
  relative `../`, in-workspace symlink, list entry, update_issue. Dismiss: none.
- T2 far 2nd-impl (A): Confluence attachment upload (`confluence/attachments.py`).
  Dismiss: different product package.
- T3 far wrapper (A): page body from `content_file` in create_page/update_page
  (`servers/confluence.py` _resolve_page_content). Dismiss: documented as accepting a
  filesystem path, reads like an intended feature.
- S1 injected: create_issue attachments inline `add_attachment` loop (`jira/issues.py`),
  bypasses the shared confined helper. Dismiss: solver fixes the shared helper, assumes
  create routes through it.
- S2 injected: create_issue `description_file` (`servers/jira.py` _resolve_issue_description),
  cross-package twin of the Confluence body-from-file helper. Dismiss: solver fixing the
  Confluence helper misses the Jira equivalent in another module.
- S3 injected: add_comment `body_file` inline read (`servers/confluence.py`), not routed
  through the shared page helper. Dismiss: copy-paste twin; fixing the shared helper misses it.

Distinct reasons-to-skip: none / different-product / intended-feature /
shared-helper-assumption / cross-package-twin / inline-duplicate.

## Verified
- Flaw reproduces at pinned through the real surfaces: fetcher upload API
  (bare mixin / real `JiraFetcher`) and the MCP tools via an in-memory FastMCP
  client (as the project's own server tests do). Atlassian client always a
  MagicMock; no network.
- Oracle (`solution/fix.patch`) closes all 6 and legit use (incl. absolute-inside,
  list, base64 in-memory upload, inline bodies) keeps working. 13 security / 13
  functional task tests: 13 fail on pinned, all pass on oracle; functional all
  pass on both trees.
- Project area tests: 309 pass on pinned (injected). 16 cases encode the pre-fix
  abspath / unconfined-content_file behaviour the published fix rewrote; they are
  deselected in test.sh (a correct fix changes that behaviour). The remaining 293
  pass on both pinned and oracle.
- All 9 check patches behave as declared (6 security_fail each isolating one
  lever, 1 functional_fail, 2 pass). Verified by applying each to pinned+injected
  and running the hidden suite.
- `fix.patch` and every `checks/*.patch` apply with `patch -p1` on the
  pinned+injected tree.

## Could not verify / notes
- `present_in_latest` for the injected siblings is n/a (they are our-copy-only).
- The published fix is an omnibus (~15 advisories: SSRF DNS pinning, JQL/CQL
  allowlist, call-time tool auth, OAuth file perms, callback XSS, download-into-CWD-root
  code-exec). Only the upload/content_file hunks are in scope; the oracle carves those
  out and does NOT include the download-root guard or any other bundled advisory.
- Out of scope (one line): the download-side `validate_safe_path` confinement and
  `test_io.py` already exist at the pinned commit (a different, earlier protection) —
  kept untouched; not this advisory's upload-side flaw.
- Scratch: ~/.tb-graders/cwe/work/mcp-atlassian-path-inj/ (repo branches
  injbranch=pinned+inject, oracle=+fix; injection.patch, fix.patch; venv via uv).

## Fairness
Every lever is findable by a blind engineer from instruction.md + code: the
invariant covers both mechanisms (attachment path, file-sourced body) across
every tool that accepts such a path, and names no identifiers. The pre-existing
download-side use of the same confinement helper is a fair in-repo hint, not a
leak of this fix.
