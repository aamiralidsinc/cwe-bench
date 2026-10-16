# py-shiny — build notes

## What I verified against the real code (not the reader's notes)

- **Vulnerable parent resolved.** The fix commit
  `1d8ecb46cbc9621b7dc8812111d26692e086b376` ("Merge commit from fork") has a
  single parent `48b4faa0d651476afa84d6423d57503b60716902` (release v1.6.3),
  which is the vulnerable state installed in the image. Vulnerable range in the
  advisory is `<= 1.6.3`, first patched `1.6.4`, consistent with this parent.

- **Flaw, confirmed and reproduced through the real HTTP entry point.** With
  server-side bookmarking enabled, `GET /?_state_id_=<id>` restores saved state
  for `<id>`. The id flows unvalidated into
  `cwd/shiny_bookmarks/<id>` and the server reads `input.json` from there. A
  relative, nested, percent-encoded, or absolute id resolves OUTSIDE the store,
  so the server reads an attacker-named directory. Because a restored input
  value is rendered into the response HTML (inputs call `restore_input()` while
  the restore context is active during the root render), a planted sentinel in
  an out-of-store `input.json` appears in the returned page — a clean,
  observable end-to-end exploit driven with `starlette.testclient.TestClient`
  (no network).

- **Where the trust decision is made.** The read path is
  `RestoreContext.from_query_string` -> `_load_state_qs` (the server-store
  branch) -> `local_restore_dir` -> `_local_dir(id)`. The upstream fix adds an
  allowlist validator (`[A-Za-z0-9_-]+` fullmatch, length-capped) applied both
  at the id source in the restore path and inside `_local_dir`, and also
  restricts the disk-read branch to `bookmark_store="server"`. A secondary
  hardening in the file-input handler (`_restore_file_source`, refusing
  symlinks/out-of-dir file-input sources) is part of the same fix; the task's
  exploit targets the primary, client-id-driven read path named by the
  advisory.

## Test design

- **6 security tests, 2 input classes.** Relative-path family (`../`,
  `%2e%2e%2f`, `..%2f`, nested) and absolute-path family (two absolute targets).
  Each asserts the out-of-store sentinel does NOT appear in the HTML. The
  absolute family contains no `..`, so a fix that blocks only dotdot leaves it
  failing — this is what forces variants beyond the basic report.
- **6 functional tests.** Plain render (default value), server-store restore of
  three legit ids (including a generated-token-style id with digits/`-`/`_`),
  and url-mode restore (state encoded in the query string, never on disk) plus
  its plain render. Assertions are behavioural (the restored value must appear;
  the default must not), so over-blocking or disabling restore fails them.
- Assertions are property-based (sentinel absent / restored value present), not
  tied to the upstream implementation, so an independent correct fix also
  scores 1.0 — proven by `alt_correct_fix.patch` (canonicalise-and-contain in
  `_local_dir`, a different approach from the upstream regex allowlist): 12/12.

## Before/after (pytest from source, CPython 3.11)

- Vulnerable commit: security 0/6 pass (all 6 fail — traversal succeeds),
  functional 6/6 pass.
- Upstream source fix: security 6/6, functional 6/6.
- `shallow_literal_dotdot_only.patch` (reject `..` in id): security 4/6 pass
  (2 absolute fail), functional 6/6 -> **security_fail**.
- `disable_bookmark.patch` (never restore on a request): security 6/6 pass,
  functional 2/6 pass (4 restore tests fail) -> **functional_fail**.
- `alt_correct_fix.patch`: 12/12 -> **pass**.

## Could not fully verify / caveats

- No dedicated upstream bookmark-restore tests exist at the vulnerable parent
  (they were added by the fix commit and are excluded as ground truth).
  `tests/pytest/test_destroy.py` (adjacent bookmark machinery) passes there
  (75 passed), confirming the environment is sound.
- The authoritative result is the Docker gate run, not the local pytest.
- The flaw is not Python-version dependent; 3.11 is pinned only for leanness
  and project support (`>=3.10`).
