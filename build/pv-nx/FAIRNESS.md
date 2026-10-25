# FAIRNESS review — pv-nx

Reviewer did not write these tests. Materials read: `tasks/pv-nx/instruction.md`,
`tests/security/*.test.js`, `tests/functional/cache.test.js`, `tests/support/*`,
`solution/fix.patch`, `build/pv-nx/manifest.json`, `notes.md`, `checks/*.patch`.

## 1. Tests — fairness of each test against instruction.md

| test (file::name) | what it asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/store.test.js::sec-store: a linked output directory is not read through when storing | a symlinked output dir is stored as a link; the target's content is not in the entry | "An output that is itself a symbolic link stays a link with the same target… the link is kept as a link, not as a copy of what it points at" | no | low |
| security/store.test.js::sec-store: an output that climbs out of the workspace is not stored outside the entry | nothing lands beside the entry; the stray file is unchanged | "declared outputs…must resolve inside the project"; "nothing else…created, changed or deleted"; refusal wrapped in try/catch | no | low |
| security/store.test.js::sec-store: an absolute output that resolves inside the workspace is still stored | an in-project absolute output is stored at `dist/a.txt` | "An output given as an absolute path is still valid when it lies inside the project" | no | low |
| security/batch.test.js::sec-batch: a batch restore writes only the declared outputs | `dist/main.js` restored; `.git/hooks/pre-commit` and `package.json` absent | general property: "the declared outputs of the task it belongs to"; "nothing else…" — covers whatever operation drives it | no | low |
| security/batch.test.js::sec-batch: a batch restore does not write through an existing workspace link | `outside/payload.js` absent | "The link is only a pointer: nothing may be written through it"; refusal accepted | no | low |
| security/restore.test.js::sec-restore: only the declared outputs are restored | declared `dist` restored; `.git` hook and `package.json` not | "the declared outputs of the task it belongs to" | no | low |
| security/restore.test.js::sec-restore: restoring does not write through an existing workspace link | `outside/payload.js` absent **and** `ws/dist/payload.js` reads `PWNED` (so the pre-existing `ws/dist` symlink must be replaced by a real dir) | first half: "nothing may be written through it". Second half has **no** covering sentence; "If a request cannot satisfy this, it is refused: the unsafe part is not applied" sanctions refusing/skipping instead | **maybe → yes**: a correct fix that refuses or skips when a parent of a declared output is a link (a standard fail-closed guard) leaves it unrestored and fails line 52; a fix that resolves `dist/payload.js` through the link reads it as outside the project and must refuse | high |
| security/restore.test.js::sec-restore: an absolute output outside the workspace is not applied | victim file unchanged | "Only outputs that resolve outside the project are invalid"; refusal wrapped | no | low |
| security/restore.test.js::sec-restore: a remote artifact is applied only within the declared outputs | `dist/app.js` restored; `.git` hook not | "its own directory inside the cache" + declared outputs | no | low |
| security/extract.test.js::sec-extract: parent-directory entries stay inside the cache entry | nothing appears above the entry | "Whatever the entry contains, however its paths are written…nothing else…created" | no | low |
| security/extract.test.js::sec-extract: absolute entry names stay inside the cache entry | no file at the absolute path | same sentence | no | low |
| security/extract.test.js::sec-extract: a symlink entry cannot be used to write outside | no write passes through the link entry | "nothing may be written through it" | no | low |
| security/extract.test.js::sec-extract: a hardlink entry cannot pull in outside content | no entry file carries the outside secret | "it cannot borrow or expose content from elsewhere on the machine" | no | low |
| security/extract.test.js::sec-extract: traversal split across separators is contained too | nested traversal does not escape | "however its paths are written" | no | low |
| security/extract.test.js::sec-extract: the legacy cache route is contained as well | no escape on the `/api/v1/cache/…` route | the general property, read literally, applies to this operation; a route need not be named | no | low |
| functional/cache.test.js::fun-cache: a directory output round-trips through the cache | dir output restored with contents | "directory outputs…keep working"; "public behaviour" | no | low |
| functional/cache.test.js::fun-cache: several declared outputs are restored together | both outputs restored | "Multiple outputs…keep working" | no | low |
| functional/cache.test.js::fun-cache: a glob output restores every matching file | glob match restored | "glob patterns keep working" | no | low |
| functional/cache.test.js::fun-cache: a symlinked output file is restored as a link | link recreated, same target | "stays a link with the same target" | no | low |
| functional/cache.test.js::fun-cache: a link that points elsewhere is restored as a pointer, not followed | link kept pointing outside; nothing written through | "even when that target lies elsewhere" | no | low |
| functional/cache.test.js::fun-cache: a declared output missing from the artifact is skipped | absent output skipped | "an output that the artifact does not contain is skipped" | no | low |
| functional/cache.test.js::fun-cache: applying a remote result records its output and exit code | code and terminalOutput recorded | "keep their public behaviour for legitimate artifacts"; standard expert knowledge: apply records them | no | low |
| functional/cache.test.js::fun-cache: a normal remote artifact extracts and reports its result | code 0, terminal output, output file present | same public-behaviour sentence; artifact is legitimate | no | low |

## 2. Leniency (quality, non-blocking)

Wrong fixes per property / trap (catch cited):

- **restore-beyond-outputs (A)** — "contain the reported extraction and keep the whole-artifact copy": caught by sec-restore declared-outputs + remote-artifact, and `secfail_restore` (3 security fails). "Restore only declared outputs but still write through links already in the workspace": caught by sec-restore writethrough and `secfail_extraction_only` (9 fails).
- **declared-output-paths (A)** — "reject every absolute output": caught by sec-store absolute-inside and `functional_fail_overbroad` (2 functional fails). "Delete expanded outputs before validating": caught by sec-restore absolute-outside and `wrong_check_after_delete` (1 fail). "Strip only a leading `..`": caught by `wrong_malformed_identity` (4 fails: absolute entry, nested traversal, absolute output, legacy route).
- **store-link-follow (A)** — "fix only the restore side, keep `is_dir()` before `is_symlink()`": caught by sec-store linked-output-dir; `secfail_store_symlink` (1 fail).
- **legacy-extract-route (B)** — "fix only the primary extractor": caught by sec-extract legacy; `secfail_legacy` (1 fail).
- **batch-restore-route (B)** — "fix only `applyRemoteCacheResults`": caught by both sec-batch tests; `secfail_batch` (2 fails).

Wrong fixes **no test catches**: (a) a declared output naming a path *beneath* a symlink directory carried by the artifact — the fixed per-output restore can read the link target's content into the workspace (notes.md residual); no test drives it. (b) A fix that silently skips (no replace, no error) an output whose parent is a workspace link is caught only by the contested line 52 — see §5.

## 3. Hints (quality, non-blocking)

- "The same holds when the output is copied into the cache — the link is kept as a link, not as a copy of what it points at." — names the store stage/direction. Neutral: fold into the single property, "preserving an output never reads or writes anything but the output itself; a link is copied as a link and never followed".
- "An output given as an absolute path is still valid when it lies inside the project: it denotes the same place as the equivalent project-relative path. Only outputs that resolve outside the project are invalid." — names the path form. Neutral: "A declared output is valid exactly when it denotes a place inside the project, whatever form its path is written in."
- "Multiple outputs, directory outputs and glob patterns keep working, and an output that the artifact does not contain is skipped." — variant list. Neutral: "Declared outputs of any supported form keep working; an output the artifact does not contain is skipped."
- "The same artifact also brought in content that was never a declared output of the task." — exists only to cover the restore trap; the general property already forbids it. Delete.
- "Fix the underlying problem and its close variants rather than that particular input." — signals a variant set/flaw count > 1. Neutral: "Fix the underlying problem rather than the particular input."

### Required: generalize

1. "The same holds when the output is copied into the cache — the link is kept as a link, not as a copy of what it points at." → state the link property once over the output, direction-agnostic (wording above).
2. "An output given as an absolute path is still valid when it lies inside the project…" → replace with the form-agnostic resolution sentence above.
3. "Multiple outputs, directory outputs and glob patterns keep working…" → replace with the generic "any supported form" sentence (or drop; the public-behaviour bullet already covers it).
4. "The same artifact also brought in content that was never a declared output of the task." → delete; the "two kinds of place" property already covers undeclared content.

## 4. Realism (quality, non-blocking)

Traps 1–3 are real, unmodified upstream code and reachable through the real entry points — not flagged. I1 (legacy fallback on a primary-route 404, with its own duplicated extractor) reads like a genuine compatibility route and is reached from `retrieve`; plausible. I2 (batch twin) is reachable from `cache.ts` `getBatch` and its napi export, but the body inlines a duplicate of the vulnerable whole-artifact copy rather than delegating to the single-entry apply — mildly contrived; a maintainer would more likely loop over the same code. Not planted enough to block, but it reads as engineered.

## 5. Verdict

**NOT READY (gate a).** `sec-restore: restoring does not write through an existing workspace link` asserts both that `outside/payload.js` is absent **and** that `ws/dist/payload.js` reads `PWNED`. Because `ws/dist` is a symlink to `outside`, line 52 passes only if the restore replaces that pre-existing link with a real directory. The instruction's refusal clause ("If a request cannot satisfy this, it is refused: the unsafe part is not applied") equally sanctions refusing or skipping; a literal reader also has `dist/payload.js` resolving outside the project, and must refuse. That fix scores 0.9333 — a correct fix fails. The batch twin covers the same case and accepts refusal.

Required change: make lines 52–53 a disjunction — nothing outside written, and **either** the call threw **or** `ws/dist` is no longer a symlink and its `payload.js` reads `PWNED`. If replacement is intended, state it in the general property, not only in the test.

**Required: generalize** — (1) "The same holds when the output is copied into the cache…" → direction-agnostic link property; (2) "An output given as an absolute path…" → "valid exactly when it denotes a place inside the project, whatever form its path takes"; (3) "Multiple outputs, directory outputs and glob patterns…" → "declared outputs of any supported form"; (4) "The same artifact also brought in content that was never a declared output" → delete.

**Quality to tighten** — test the notes.md residual (a declared output beneath an artifact symlink dir), refusal-agnostic; align the two writethrough tests on refusal; neutralize the five hints (§3); batch twin should delegate, not duplicate.

**Human review:** confirm whether refusing/skipping a declared output whose parent is an existing workspace symlink is a correct fix; if yes, line 52 is unfair.

GATE_A: NOT_READY
NEEDS_HUMAN_REVIEW: YES
