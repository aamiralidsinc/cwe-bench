# ghost-ds — build notes

Start (UTC): 2026-10-18T19:18 (earlier attempt; this build session started 2026-10-18T22:12)
Task: `ghost-ds` — tryghost/ghost, GHSA-HQQ2-XQR2-FMX2 / BIT-GHOST-2026-105644 / CVE-2026-105644
Pinned (vulnerable): `88ae6d6d56f8a239cb38a8c89de02f034f50e2ce` (verified direct parent of the
published fix `1be06f4e95a5eb159d14abda7660e689af13cff1`). Pattern A, track injected.

## Plan (written before build)

Flaw class: bytes chosen by extension/metadata are stored in image storage and served from the
site origin; only the direct upload middleware sanitizes SVG. Stored SVG (or non-image bytes
behind an image name) becomes executable content on the site origin.

### Levers

- **T1 (A, base / reported target)** — content-import image handling (`/db` zip import and CSV
  zip asset import share it). Shapes: unsafe `.svg`; gzip `.svgz`; uppercase `.SVG`;
  SVG/non-image bytes behind `.png`/`.jpg`; AVIF bytes behind `.jpg`. Dismiss: none (reported).
- **T2 (A, far site)** — remote media inliner storage path: fetched bytes stored with the
  extension from contents/Content-Type/URL, never sanitized or content-checked. Dismiss:
  "a background remote-URL fetcher, not files inside an import archive".
- **T3 (A, far site)** — direct image upload validation: extension + client mimetype allowlist
  only, no content check. Dismiss: "the upload path already sanitizes SVG, so it is the safe one".
- **T4 (injected sibling)** — CSV content-import asset kind (`avatars`) using the generic
  content-file handler: bytes go to image storage with no validation. Dismiss: "another asset
  type handled by the generic file handler, not the image handler".
- **T5 (injected sibling)** — bookmark mention-icon cache (new oembed helper): fetches the
  publisher's icon and stores it under the response-derived extension, no validation. Dismiss:
  "publisher metadata/link-preview furniture, not post media or imports".

### Coupled must-keep-working (functional)

- valid JPEG/PNG/GIF/WebP/ICO imported and stored; `.jpeg` alias and uppercase `.JPG`;
  contents in a different allowed format than the name (PNG bytes named `.jpg`);
- unsafe SVG/SVGZ still imported (sanitized in place; SVGZ re-gzipped) — no blanket SVG rejection;
- an invalid file is skipped while valid files in the same import still import;
- media/files assets in the same archive are unaffected (files storage stays verbatim);
- inliner still stores real images and an SVG payload as an image; media/files routed to their
  own storage;
- upload accepts real images and keeps sanitizing SVG;
- valid avatar assets store; a valid mention icon caches; a failed icon fetch leaves the bookmark.

### Sites / entry points the tests drive

- real `ImportManager.loadFile` on a real zip (the `/db` import route's importer chain);
- real `prepareImportSource` + asset batch `store()` (the CSV content-import route);
- real media-inliner service (`init()` + `getInstance()` + `importUrl`, remote fetch stubbed);
- real express chain `upload.single` + `upload.validation({type:'images'})` via supertest;
- real `OEmbedService.buildBookmarkData` with an injected external request and the real local
  image storage.

### Out of scope (one line)

Boot-time process-wide libvips decoder restriction (decoder-confusion hardening, not SVG XSS);
theme-zip SVG assets (separate sink/trust model). Not built on.

### Not a security lever

oEmbed's pre-existing image fetch (processImageFromUrl) already content-checks at the pinned
commit; covered by functional coupling only.

## Verified

- Pinned commit is the direct parent of the published fix (`git cat-file`).
- **Gate**: static clean except the blind patch + FAIRNESS.md (written by the fairness pass);
  nop PASSED (18/18 security fail, 15/15 functional pass); oracle PASSED 3/3 at reward 1.0;
  patches PASSED 8/8 as declared (security_fail per lever with functional green, one
  functional_fail, hardening and alternative passes at 1.0).
- Every checks/ patch behaves as declared, both locally and through Harbor: five
  `security_fail` (T1-T5), one `functional_fail` (blanket SVG rejection breaks the import),
  `hardening` pass, independent `alternative` pass.
- Project unit tests for the affected area pass on the pinned + injected tree: image handler,
  upload middleware, importer index/interface counts, generic content-file handler, oembed
  service, media-inliner and content-import units (154 + 290 tests).
- `solution/fix.patch` reproduces the oracle tree from the injected tree byte-for-byte.

## Could not verify

- The published fix's `pnpm-workspace`/`sharp` version bump is not part of the oracle: none of
   the tested sinks use `sharp.block`/`unblock`, so it is decoder-confusion hardening only.
- Current upstream (`d4952f1d` at screening) was not re-read; `present_in_latest` for the two
  injected siblings does not apply (they are task-local).
- Project tests that the published fix itself rewrote (image handler fixtures) are not run as
  graded functional tests: a correct fix necessarily changes their expectations, and the solver
  may not edit tests. The environment image still runs them green at the pinned commit.

## Fairness revision (2026-10-19)

Addressed the pre-trial review in `FAIRNESS.md`:

- Instruction: removed the "other entry points" hint, dropped the name/media-type/URL
  enumeration, reworded SVG requirements as properties, scoped SVG treatment to SVG-named
  files (the upload contract), stated that files keep their archive/URL name and that ICO is
  accepted without decoding, and renamed the title. The five-entry scope list became
  "every path that writes image storage".
- `helpers.unsafeSvg()` now places the marker in a `<script>`, an `onload` attribute and a
  `foreignObject`-embedded document; a regex `<script>` stripper leaves the marker behind.
  Added `contentLeaks()` (whole content tree) so a rejected file cannot pass by being moved
  from image storage to media/files storage.
- New security tests: avatar non-image bytes, avatar AVIF, mention-icon AVIF, and a two-URL
  inliner run where a rejected file must not stop the next one. Inliner security tests now
  assert the rejected bytes were not written anywhere under the content path.
- New functional tests: an SVG mention icon is still cached (not dropped), and an AVIF
  remote response is not stored as an image (it keeps the existing files-storage routing).
- New checks: `fix-script-only-sanitizer.patch` and `fix-diverts-rejected.patch`, both
  `security_fail` with functional green; wired into `manifest.patch_checks`.
- Counts: 22 security + 17 functional.

End (UTC): 2026-10-19T04:05

## Sibling-injection upgrade (2026-10-20)

Instruction-only upgrade for the BETTER-PATTERNS §2–§8 rules:

- `instruction.md` now states one general property over the protected outcome:
  what may be stored as an image is decided by its contents, stored image
  content may carry no executable or embedded active content, a vector-named
  file is stored after that content is removed rather than discarded, and a
  non-qualifying file is neither stored nor allowed to abort the surrounding
  work. Removed every route, operation, source, channel, format and sibling
  enumeration (the archive/remote/upload/mention wording, the SVG/SVGZ/JPEG/
  PNG/GIF/WebP/ICO lists, and the "every path that writes image storage"
  asset-kind list). Coupled contracts kept in property terms: configured
  formats and alias/upper-case spellings, contents whose format differs from
  the name, an undecodable-but-accepted format, stored names unchanged,
  non-image data untouched, and an unusable image leaving its feature usable.
- Levers: the task already has how-type levers — M4 (protection never existed
  on the import, inliner, avatar and mention-icon routes), M8 (client
  extension/declared type versus contents on upload; the shallow-sanitizer and
  diversion shapes) and M11 (coupled alias/case/mismatched-name/undecodable
  values). No repo code was added, so no rebuild.
- Coverage audit: every writer of `storage:images` is driven by a failing
  security test (import images, CSV images, CSV avatars, media inliner,
  mention-icon cache, image upload). The link-preview image path already holds
  the property at the pinned commit, so a security test there would pass at
  the pin and invalidate nop; it is intentionally not added. The media-thumbnail
  path writes media storage, not image storage, and is out of the invariant.
- `manifest.json`: `lever_type` recorded for T1–T5; T6/T7 added for the two
  existing shape `security_fail` checks (script-only sanitizer, diverted
  rejected bytes); `leak_terms` extended with the route/format vocabulary to
  enforce the generalized report; upgrade note added.
- No file under `tests/`, `solution/`, `environment/` or `checks/` changed, so
  the prebuilt image and the recorded gate results stand (nop 22 security
  fail / 17 functional pass; oracle 3x 1.0; patches 10/10). Static leak scan:
  clean apart from the separately wired blind patch.


## Hardening pass (2026-10-21)

Both target models solved the previous version and every existing trap was fixed on every
graded run, so two new fair HOW-type levers were added and the task was converted to the
Frontier 1.4 delivery format.

- **T8 — archive handler fan-out.** `ImportArchive.getFiles` globs by extension in every
  directory, so an entry under the image asset directory is handed to the generic
  content-file handler as well; the file handler's own extension list already contains the
  image extensions. A file the image handler rejects is therefore stored verbatim in files
  storage. The tests drive the real `ImportManager.loadFile` + content-file importers and
  assert no rejected bytes exist under any storage. Dismissal: the file already went through
  the image pipeline, and the duplicate write is "just" a download copy.
- **T9 — media upload thumbnail.** `mediaValidation` is a second validator in the same
  upload middleware, nominally for a video upload. It checks the client extension and declared
  type and sanitizes vector thumbnails, but never checks a raster-named thumbnail's contents;
  the thumbnail is stored and served as an image. Dismissal: the media route and its
  thumbnail look auxiliary next to the reported image route.
- Coupled functional tests: an image asset and an image attached as a download still reach
  their own storage with non-image data untouched; a real video plus its PNG thumbnail still
  store, and a vector thumbnail is still stored (sanitized, not dropped).
- `solution/fix.patch` gained the fan-out filter; the media-thumbnail check was already part
  of the reference fix. New checks: `fix-misses-import-copy.patch` and
  `fix-misses-media-thumbnail.patch` (both `security_fail`, functional green). The existing
  `fix-hardening.patch` / `fix-alternative.patch` were rebuilt so both new levers are closed,
  and a locally written independent `blind.patch` was wired as the strict-gate blind pass.
- The media-thumbnail functional assertion was narrowed to the functional contract (the
  vector thumbnail is stored, not dropped, and its `<script>` element is removed); active
  content removal in every shape is left to the security suite so the script-only-sanitizer
  wrong fix stays `security_fail` with functional green.
- Frontier 1.4: `/workspace` everywhere, separate offline verifier, artifacts restore with
  `node_modules` excluded, pristine `/opt/ghost` pnpm tree rebuilt in `tests/Dockerfile` and
  overlaid with the restored submission in `test.sh`, uid-1000 non-root grading, fresh
  canary GUID.
- Counts: 27 security, 20 functional. nop 27/27 security fail and 20/20 functional pass;
  oracle 3x1.0; 13 patch checks (9 security_fail, 1 functional_fail, hardening, alternative,
  blind).

## Verifier materialization (2026-10-21, later)

The first Frontier verifier hardlinked the whole 1.2 GB pnpm tree into /workspace on every
trial (~5-6 min of I/O per trial, ~9 min per Harbor trial under shared-VM load). `tests/test.sh`
now lays down the pristine *sources* from /opt/ghost (tar, node_modules excluded), overlays the
restored submission's sources (also excluding dependency trees), and symlinks each pristine
`node_modules` directory in place. pnpm's per-package dependency links are relative and resolve
inside /opt/ghost, so the agent's source runs against the verifier's dependencies. A local
node:22 check confirmed module resolution and a mixed security/functional run in the symlinked
tree. This keeps the same /workspace run tree and runner commands; only the materialization
block changed.

## Final gate (2026-10-22)

- conformance_check: conforming
- static: PASSED (conformance + strict: blind and hardening pass patches wired)
- nop: PASSED — 27 security tests fail, 20 functional tests pass (delivered verifier, 3m40s)
- oracle: PASSED — 3 runs, each reward 1.0 (47/47)
- patches: PASSED — 13/13 as declared:
  blind 1.0; hardening 1.0; import-copy 0.9259 (2 security, 0 functional); media-thumbnail
  0.8889 (3/0); importer 0.6296 (10/0); inliner 0.7778 (6/0); upload 0.7037 (8/0);
  avatars 0.7778 (6/0); mention-icon 0.8148 (5/0); script-only-sanitizer 0.6667 (9/0);
  diverts-rejected 0.8148 (5/0); overbroad-svg functional_fail (2 security, 1 functional);
  alternative 1.0.

Check order was changed to run the pass checks and the two new-lever checks first
(blind, hardening, import-copy, media-thumbnail) so a slow shared VM cannot hide a
correctness problem behind the wrong-fix checks.
