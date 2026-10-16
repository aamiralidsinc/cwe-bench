# cloudreve (stacking) — build notes

**Gate: PASSED** (static, nop, oracle×2 identical, 3 patch checks). Ran ~3.5 min
on a loaded host because the heavy Go build layer was pre-cached.

## Commit C
`54dc81deefcd799300119d0b9bc19c935a0881b5` (2026-05-10), module
`github.com/cloudreve/Cloudreve/v4`. Verified (git merge-base --is-ancestor) to
be an ancestor of all nine v4 fix commits, and it predates the earliest fix
(2026-06-06). Every CVE-2026 advisory in the candidate is "introduced at 0" on
the v4 line, so all are simultaneously OPEN at C.

## Reproduced and included (5), each through the real HTTP API, each confirmed
present at C (exploit succeeds) and closed by the upstream fix:
- GHSA-8r7f (CWE-200/359) account search returns inactive/banned accounts.
- GHSA-g9j2 (CWE-400/409/770) thumbnail pixel-bomb: tiny PNG declaring 81 MP is
  decoded; fix refuses by declared dimensions before decode.
- GHSA-49h3 (CWE-22) WOPI PUT_RELATIVE SuggestedTarget path traversal.
- GHSA-c3jm (CWE-863) WOPI access-token secret ignored (only session id checked).
- GHSA-w8x7 (CWE-863) event-stream subscription via a single-file share.

5 security tests + 7 functional tests. On C: 5/5 security fail, 7/7 functional
pass. Oracle (combined upstream fixes, source only): 1.0.

## Dropped (could not reproduce through ordinary offline session auth)
- GHSA-x756 / GHSA-v6w6 (CWE-918 SSRF): need a configured downloader node or the
  OAuth authorization-code + scoped-token flow to reach the server-side fetch.
- GHSA-hq88 and the jwt scope bug (CWE-863): require an OAuth client + scoped
  token.
- GHSA-fg25 (CWE-79): a 3.x-era advisory, not co-present on v4 at C.
- GHSA-w5fv (WebDAV scoped-DAV ACL): could not pin to a single reachable
  commit near C within budget.

## Environment
Pure Go (CGO_ENABLED=0, modernc.org/sqlite). Boots fully offline: sqlite DB +
in-memory KV + local storage; no external services. Frontend SPA stubbed with a
minimal valid `assets.zip` (embedded via go:embed) — API only, which is what the
verifier drives. First admin is the first registered account (auto-elevated), so
test.sh registers it before the tests.

## Build cost / memory
First image build ~14 min, image 4.36 GB (Go toolchain + warmed module/build
cache baked in). Peak was inside the Docker VM; host was already under heavy
pressure (5 model-trial containers, ~7 GB swap) so `go build` ran with `-p 2` and
the VM bursted to ~230% CPU intermittently — slow but it completed cleanly, no
OOM. Verifier rebuild from /app is incremental (~9 s) against the baked cache.

## alt_correct_fix
Places the information-disclosure fix in the service layer (filter non-active
accounts after the query) instead of the data-access layer; still 1.0.

## 2026-10-16 test repair

Inputs: `build/audit/lenient_items_2026-10-16.txt` (cloudreve: 1 flagged item + 2 REC lines),
`research/own-runs/TEST-REPAIRS.md` § cloudreve, plus extra items from the caller's notes.

| # | Item | Decision | What changed |
|---|------|----------|--------------|
| 1 | Exact-403 in security tests (`test_editor_token_secret`: `code == 403`) | fix (relaxed) | Refusal = any status >= 400 (4xx, or a 5xx from a service-layer check) **plus no side effect**: the file name must not appear in the response body. Parametrised over wrong / empty / one-char-off secret. New `test_editor_forged_secret_cannot_overwrite_file`: a WOPI PutFile with a forged secret must leave the content unchanged (read back through a fresh legitimate session) and must be refused. No other security test asserted an exact status. |
| 2 | Search test lacks a 'banned' status (REC deepseek JwDetgF) | fix | `test_search_excludes_inactive_user` parametrised over `inactive`, `manual_banned`, `sys_banned` (all non-active statuses the admin API offers; the instruction says "deactivated or banned"). Asserts the status was really applied before searching. |
| 3 | Traversal test: backslash or absolute-path SuggestedTarget (REC deepseek JwDetgF) | fix (absolute), skip (backslash) | New `test_putrelative_absolute_target_cannot_escape_source_directory`: target `/../<name>` must not land in the parent folder. Backslash skipped: the server splits targets only on `/` (URI JoinRaw), so `..\..\x` cannot escape even at C; such a test would pass on vulnerable code and fail the nop gate. |
| 4 | Pixel-bomb test lenient: over-restrictive caps pass (flagged item, mimo TFwPvkf) | fix + one instruction sentence | New functional `test_camera_size_image_thumbnail_generated`: a 6000x4000 (24 MP) PNG with noise content (~7.7 MB, ~9:1 compression, so it is not itself bomb-like) must thumbnail. Instruction sentence changed (below), because the old text called "tens of millions of pixels" the bomb, and both 1.0 runs cited that phrase when choosing a 1<<24 (16.7 MP) cap; without the sentence the new test would be unfair. |

Instruction change (one sentence, in the thumbnail paragraph):
- old: "... before any full decode is attempted, while normal images must still thumbnail."
- new: "... before any full decode is attempted, while normal images (for example an ordinary
  24-megapixel camera photo) must still thumbnail."

New patch checks (`build/cloudreve/checks/`, listed in manifest):
- `search_inactive_only.patch` (security_fail): reference fix but the search filter is
  `StatusNEQ(inactive)`; banned accounts still leak.
- `traversal_clean_check.patch` (security_fail): validates `filepath.Clean(name)` does not start
  with `..` but joins the raw name; `/../x` cleans to `/x` and escapes after the leading `/` is dropped.
- `token_fileinfo_only.patch` (security_fail): secret compared only in the file-info handler
  (refuses with 500, which the relaxed read test accepts); forged-token writes are still accepted.
- `thumb_tight_cap.patch` (functional_fail): reference fix with a 16*1024*1024 pixel cap; the
  24 MP photo is refused.

Helper change: `lib/cr.py viewer_session()` now retries a failed editor-session creation up to 5x
(1 s apart) and reports the response if it never succeeds. One oracle run (~05:20 UTC, before the
disk-full windows) failed only because `PUT /file/viewerSession` returned no `data` once, right
after an upload. It is a precondition, not an assertion. New helpers: `wopi_put_file`,
`wopi_get_file`, `photo_like_png`.

Gate (`build/slot.py 2 -- builder/gate.py cloudreve`, started ~07:23 UTC, finished ~07:43): **PASSED**. Earlier
attempts were stopped by the coordinator (slot cap change, slot.py bug), not test results.
- nop: 11 security tests all fail (each for the intended reason), 8 functional pass (the 24 MP
  photo thumbnails at C).
- oracle x2: 1.0, identical.
- patches: subset_fix security_fail (events); disable_feature functional_fail; alt_correct_fix
  1.0; search_inactive_only fails [manual_banned, sys_banned] only; traversal_clean_check fails
  the absolute-target test only; token_fileinfo_only fails the forged-write test only;
  thumb_tight_cap fails the 6000x4000 test only.
- No `hardening` / `blind` pass patches (task predates strict_gate; warnings only).

Regrade: **none possible**. No cloudreve trial has `final-code/changes.patch`:
| trial | old | new | note |
|---|---|---|---|
| cloudreve-deepseek-seq1-1792023049/cloudreve__JwDetgF | 1.0 | not regraded | no final code |
| cloudreve-mimo-r1-20261015-031109-n002/cloudreve__TFwPvkf | 1.0 | not regraded | no final code |
| cloudreve-mimo-r1-20261015-021015-n001/cloudreve__pe6Ft9Q | 0.0 | not regraded | no final code; all 5 security failed (agent timeout, no effective fix), so the relaxed token test cannot change it |
Expected effect, from the audits' diffs rebuilt from the transcripts: both 1.0 runs pass the new
security cases (StatusEQ(active), path.Base on the target, whole-token compare in the middleware).
But both capped the thumbnail at 1<<24 (16.7 MP) and would FAIL
`test_camera_size_image_thumbnail_generated`. Both transcripts cite the old instruction's "tens
of millions of pixels" as the reason for that cap (deepseek even weighed a 6000x4000 normal
image and rejected it). That requirement exists only in the new instruction sentence, so those
two runs should keep their 1.0. Do not downgrade them against tests their instruction did not
support.
Not added (possible later hardening): a UTF-7-encoded SuggestedTarget (the header is
UTF-7-decoded server side), which would catch fixes that validate the raw header.
