# stk-flask-reuploaded-ghsa937x — build notes

## Times

- Start (UTC): 2026-10-26T02:11:11Z (from build/start_utc.txt; the first driver attempt failed before any work)
- End (UTC): 2026-10-26T04:24:45Z

## What the task is

- Repo: `jugmac00/flask-reuploaded`, pinned at `9e813e919c4f8d9ef17c7fe8ecc0c2efa8fee118`, the direct
  parent of the first published fix `d64c6b2f71cb`; the later incomplete-fix follow-up is
  `5ded76092429`.
- Entry point: the library's public save operation, `UploadSet.save`, driven through a real Flask app
  and its per-set configuration.
- Pattern: A+B, stacked (H3b). Control task: `stk-flask-reuploaded-ghsa937x-control` (same pinned
  tree and byte-identical report; only the reported route in its security tests and reference).

## Levers (one line each)

- **T1 (concept C1, reported route, MiMo-type)** — the application-supplied stored name replaces the
  basename that the type check saw, so a refused type is written. `src/flask_uploads/flask_uploads.py:312-325,336`.
  Reason to dismiss: the docs call the name an app-controlled override that gives complete control of
  the stored file, and the trailing-dot form is documented.
- **T2 (concept C1, published-fix far site, both)** — the decision lowercases the uploaded extension
  but not the overridden one, so a mixed-case refused type passes. Same route; a single
  case-normalised re-check closes T1 and T2, so they are one concept. `flask_uploads.py:266,276-277,283`;
  `extensions.py:97-98`. Reason to dismiss: the uploaded side is already lowercased by `get_basename`.
- **T3 (concept C2, uncovered upstream, both)** — only the final dot-separated part is judged, so a
  refused type earlier in the name is stored. `extensions.py:101-106`. Reason to dismiss: the library
  has only ever judged the final suffix and its own later regression test still accepts a name whose
  earlier part is a script type.
- **T5 (concept C3, injection room / path, DeepSeek-type)** — the folder component and the resolved
  write target are joined without sanitisation or containment (relative parts, symlinked subfolder,
  dangling symlinked filename). `flask_uploads.py:312-313,327-336`. Reason to dismiss: the docs call
  the folder and name arguments app-controlled and the advisories talk about file types.

Coupled must-keep-working values (functional only, never named in the report): names with dots in
the stem, compound archive names, extensionless uploads and explicit names, explicit and implicit
subfolders, an explicitly allowed type that the preset excludes, a link that stays inside the
destination, and the stem's letter case.

## Verified locally (no Docker, project runner)

- Pinned tree: 0/8 security pass; all 10 hidden functional and all 40 project tests pass.
- Reference: 18/18 hidden and 40/40 project pass.
- Every check patch applied to a fresh pinned copy matched its declared outcome:
  - `miss_override_validation` 2 security fail / 0 functional (T1, T2)
  - `miss_multi_suffix` 2/0 (T3, both routes)
  - `miss_path_containment` 4/0 (T5, all four routes)
  - `crash_as_refusal` 2/0
  - `upstream_first_fix` (A alone) 3/0 — the plain override and path routes close, the mixed-case
    override and both multi-part routes stay open
  - `upstream_fix` (A+B) 2/0 — both multi-part routes stay open
  - `refuse_all` 0 security / 10 hidden functional fail (11 project fail)
  - `overbroad_segments` 0/1 (dots-in-stem name stops working)
  - `adjacent_api` 0/2 hidden (1 project fail)
  - `hardening` 1.0, `alternative` 1.0
- Control: pinned 0/5 security with all functional/project passing; A alone 5/5 security and all
  functional/project passing.

## Container gate (stacked task)

- static: PASSED (`gate_report.partial.json`).
- nop: PASSED — 8 security tests fail on the pin, 50 functional tests pass (10 hidden + 40 project).
- oracle: PASSED — three runs, reward 1.0 each, 58/58 tests, identical results.
- patches: PASSED — all 11 check patches matched their declared outcome:
  `adjacent_api` 0.0, `alternative` 1.0, `crash_as_refusal` 0.75, `hardening` 1.0,
  `miss_multi_suffix` 0.75, `miss_override_validation` 0.75, `miss_path_containment` 0.5,
  `overbroad_segments` 0.0, `refuse_all` 0.0, `upstream_first_fix` 0.625, `upstream_fix` 0.75.
- control (`stk-flask-reuploaded-ghsa937x-control`): static PASSED; nop PASSED (5 security fail, 50 functional pass); oracle PASSED (three runs at 1.0); patches PASSED (5 checks: `miss_override_validation` 0.0 security-only, `crash_as_refusal` 0.0 security-only, `refuse_all` 0.0 functional, `hardening` 1.0, `alternative` 1.0).

## Could not verify

- The advisory text of the two GHSAs is not present in the pin; only the reader record and the two
  fix commits were available. The mapping of the case-folding bug to GHSA-937x-gpqr-72gg comes from
  the later fix commit's message.
- That a web server treats a non-final dot part as a handler suffix is external knowledge, not
  evidenced inside the repository. The report states the property at the outcome level; a careful
  engineer needs that standard knowledge, and the project's own `extension()`/`lowercase_ext` tests
  show that only the last suffix is the library's notion of an extension.
- `pipelines/stacking/out/reader/h3-ghsa-937x-gpqr-72gg.json` does not exist in the checkout; the
  record that was used is `pipelines/stacking/out/reader-ds/h3-ghsa-937x-gpqr-72gg.json`. The
  manifest keeps the path the build prompt specified.
- The listing check was not run here (the build prompt excludes running the model reviewer).

## Scope note

Nothing outside this advisory's own protection was built on. The unrelated findings seen while
reading the pin (the `ALLOW`-over-`DENY` layering and the serving helper) were left alone.
