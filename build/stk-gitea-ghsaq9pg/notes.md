# stk-gitea-ghsaq9pg — build notes

## Times
- Start (UTC): 2026-10-23T07:13:32Z (this rebuild; the first pass ran 2026-10-22T21:30Z–2026-10-23T02:50Z)
- End (UTC): 2026-10-23T09:10Z

## Rebuild provenance
- The stacking restart (`stacking/stacking_restart.sh`) deletes `tasks/<slug>` and `tasks/<slug>-control`
  by design, so the task tree was rebuilt rather than re-designed.
- The verifier image from the first pass (`stk-gitea-ghsaq9pg__anszkgx__verifier__trial-main`,
  `04406e1064a2`) still existed and `tests/Dockerfile` copies the whole `tests/` directory into
  `/tests`. The hidden suites (security, functional, support), `tests/Dockerfile`, `tests/test.sh`
  and `tests/score.py` were recovered byte-for-byte from it.
- `checks/*.patch` and the reference patch (`oracle.patch`) were recovered from `build/stk-gitea-ghsaq9pg/`
  and the scratch tree. The pinned checkout in `~/.tb-graders/cwe/work/stk-gitea-ghsaq9pg/src` is at
  `5f8e19f…`; all 15 patches apply cleanly with `git apply --check`.
- Only the report (`instruction.md`), `task.toml` and `environment/Dockerfile` were rewritten. The
  environment Dockerfile was reconstructed from the first pass's build log and the template; its
  project-test warm step passes (the log's `PASS` line) as uid 1000.
- Rebuild gotchas:
  - Harbor passes `task.toml` `artifacts.exclude` to `tar --exclude`, whose patterns are unanchored:
    `data/*` and `log/*` also stripped real source directories (`modules/log`, and
    `tests/testdata/data`), so the verifier image could not resolve the project's own module
    (`go: finding module for package code.gitea.io/gitea/modules/log`) with the network off. The
    delivered exclude list is only `.git`, `gitea.db`, `gitea.db-*`.
  - The environment image warms its caches as the unprivileged agent user, so the image build does
    not do a recursive ownership pass over the multi-GB Go cache (the first reconstruction did and
    spent minutes in that `chown`).

## Levers (one line each)
- T1 (reported route / fix B, both-type): every UUID download address of a draft release attachment
  serves the file to readers and anonymous callers — the shared web download handler never consults
  the release's draft state. `routers/web/repo/attachment.go:131-173` at pin.
- T2 (fix A, far site, deepseek-type): the release metadata API returns a draft release to any repo
  reader — `routers/api/v1/repo/release.go:54-69`. Reason to dismiss: reads as the earlier advisory's
  scope, and the by-tag sibling already has the gate.
- T3 (fix A, far site, deepseek-type, masked by T1): the release asset API lists and describes a
  draft release's attachments to readers — `routers/api/v1/repo/release_attachment.go:23-38,76-97,130-148`.
  Reason to dismiss: once the download is gated, only metadata leaks.
- T4 (uncovered route, wrong object, deepseek-type): a linked attachment is authorised against the
  repository named in the request, not the repository that owns it; the legacy cutoff comment frames
  the skip as compatibility — `routers/web/repo/attachment.go:136,154-167`.
- T5 (coupled must-keep-working, mimo-type): a linked attachment stored before `repo_id` was written
  (`repo_id=0`) must still be served in its own repository; the naive repo-id comparison breaks it.
  `models/repo/release.go:96-98`; `routers/web/repo/attachment.go:136`.

## Concepts
- C1 = T1 (web draft download gate)
- C2 = T2 (API release metadata)
- C3 = T3 (API release assets)
- C4 = T4 + T5 (attachment ownership + legacy repo_id=0)

## Verified on the host (first pass, pinned tree, in-process router, SQLite)
- T1: all three UUID download addresses returned 200 anonymously and to a signed reader on the pinned
  code; 404 for both after the oracle; writer still 200.
- T2: `GET /api/v1/repos/user2/repo1/releases/4` returned 200 anonymously and with a read-scoped token
  on the pinned code; 404 after the oracle; a write-scoped token of the owner still 200.
- T3: asset list and asset detail returned 200 with the attachment name/uuid on the pinned code; 404
  after the oracle; writer still 200.
- T4: fixture attachment 12 belongs to private repo 2; anonymous and user8 could fetch it through
  public repo 1's two repository-scoped download routes (200) on the pinned code; 404 after the oracle.
- T5: an inserted linked attachment with `repo_id=0` and an old `created_unix` is served in repo 1 on
  the pinned code and after the oracle (via the release's repo id); the naive `attach.RepoID` comparison
  (ff-legacy-break) 404s it.
- Functional on the pinned code: published release assets (all three web routes and
  `/releases/download/{tag|latest}/file`), writer access to a draft asset, unlinked uploader access,
  the API reader/writer cases, and the four selected project tests all pass.

## Wrong-fix checks (first pass, host and gate)
| check | kind | result |
|---|---|---|
| sf-no-web-draft-gate | security_fail (T1) | 1 sec fail (web draft), 0 fun fail |
| sf-no-api-release-gate | security_fail (T2) | 1 sec fail (API metadata), 0 fun fail |
| sf-no-api-assets-gate | security_fail (T3) | 1 sec fail (API assets), 0 fun fail |
| sf-no-repo-match | security_fail (T4) | 1 sec fail (ownership), 0 fun fail |
| sf-anon-only | security_fail (T1) | 1 sec fail (web draft), 0 fun fail |
| sf-read-instead-of-write | security_fail (T1) | 1 sec fail (web draft), 0 fun fail |
| sf-global-route-only | security_fail (T1) | 1 sec fail (web draft), 0 fun fail |
| sf-crash | security_fail (T1) | 1 sec fail (500 refused as non-4xx), 0 fun fail |
| sf-after-side-effect | security_fail (T1) | 1 sec fail (download counter changed), 0 fun fail |
| ff-legacy-break | functional_fail | 2 fun fail (unlinked + legacy), 0 sec fail |
| ff-refuse-all | functional_fail | 5 fun fail, 0 sec fail |
| pass-alt | pass | 0/0 failures |
| pass-hardening | pass | 0/0 failures |
| upstream_first_fix (A alone) | security_fail | 2 sec fail (T1, T4), 0 fun fail |
| upstream_fix (A+B) | security_fail | 1 sec fail (T4), 0 fun fail |

Prior gate jobs that completed before the restart reproduced the four concept misses and both recall
checks (rewards 0.9/0.3/0.9/0.9, upstream_first_fix 0.2, upstream_fix 0.9) and pass-alt/pass-hardening
1.0; ff-legacy-break 0.0 with the two functional tests failing.

## Project tests
- Run in the verifier functional group: `TestAttachments`, `TestDownloadReleaseAttachment`,
  `TestAPIGetDraftReleaseByTag`, `TestAPIEditReleaseAttachmentWithUnallowedFile`.
- `TestAPIUploadAssetRelease` is not used: at the pinned commit it hard-codes a PNG byte length (104)
  that the Go 1.27 encoder produces as 101, so it fails on the untouched pinned tree.

## Gate results (this rebuild)
- static: PASSED (main and control)
- nop: PASSED — 10/10 security fail, 28/28 functional pass
- oracle: PASSED — three runs, reward 1.0, identical (10/10 security, 28/28 functional each)
- patches: PASSED — all nine declared checks behaved as declared:
  sf-no-web-draft-gate (reward 0.3, only the web-draft security tests fail), sf-no-api-release-gate
  (0.9, T2 only), sf-no-api-assets-gate (0.9, T3 only), sf-no-repo-match (0.9, T4 only),
  ff-refuse-all (0.0, functional only), pass-hardening and pass-alt (1.0), upstream_first_fix
  (security fail on T1+T4) and upstream_fix (security fail on T4).
- control gate: static PASSED; nop PASSED (7/7 security fail, 28/28 functional pass); oracle PASSED
  (three runs, reward 1.0, 7/7 and 28/28); patches PASSED (sf-no-web-draft-gate security_fail 0.0,
  ff-refuse-all functional_fail 0.0, pass-hardening 1.0, pass-alt 1.0).

### Main patch-check detail (this rebuild, `gate_report.partial.json`)
| patch | expect | reward | failing |
|---|---|---|---|
| sf-no-web-draft-gate | security_fail | 0.3 | T1 (parent + 6 subtests) |
| sf-no-api-release-gate | security_fail | 0.9 | T2 |
| sf-no-api-assets-gate | security_fail | 0.9 | T3 |
| sf-no-repo-match | security_fail | 0.9 | T4 |
| ff-refuse-all | functional_fail | 0.0 | 7 functional |
| pass-hardening | pass | 1.0 | — |
| pass-alt | pass | 1.0 | — |
| upstream_first_fix (A alone) | security_fail | 0.2 | T1 + T4 |
| upstream_fix (A+B) | security_fail | 0.9 | T4 |

## What I could not verify
- The published fix commits were not available as local refs in the first pass; the four patch files
  were downloaded from the GitHub commit pages, and the parents were checked through the commit API
  (A's first commit parent is exactly the pinned commit).
- The upstream fixes' own integration tests were not run against the pinned tree; the hidden tests
  create the rows they need.
- Harbor's artifact restore of `/workspace` was verified this rebuild (nop, 3 oracle runs and 9 patch
  trials); the verifier image warms caches from `/tmp/warm` and the artifact supplies `/workspace`.

## Scope notes
- Everything is inside GHSA-x92v-f5gc-r34v / GHSA-q9pg-jj6x-j9p6's repository at the pinned commit.
  T4 is a repository-ownership check in the same download sink; it is within the same protection family
  (an attachment's authorisation) and is covered by the report's second property.
- The release-list draft filter is part of the reference fix but is not a hidden test route.
