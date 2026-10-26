# Fairness review: tinacms-ds

Reviewed offline: instruction.md, all tests, solution/fix.patch, manifest.json, notes.md, checks/*.patch.
No Docker/trial/gate was run.

## Covering properties (verbatim from instruction.md)

- **P1**: "No caller-supplied object key, directory, file name, list of keys, or pair of keys used together may cause a read, write, copy, move, delete, presigned write URL or listing outside the media area the backend serves. When a media root is configured, every key used with the storage service must resolve at or below that root."
- **P2**: "The rule holds for every operation the media API exposes and every storage backend the project ships, including backends that have no configured root. Where no root is configured, a key must still be relative and must not be absolute or climb above the area being served."
- **P3**: "The rule holds for every input shape: a single value, a repeated value (a list), a key split across route segments, and a directory and file name supplied in a multipart or form body."
- **P4**: "A key that is absolute (a leading separator or a Windows drive letter), contains a NUL byte or a backslash, is empty, or uses `..` to climb above the area is refused with a client error (a 4xx response). No storage operation may be carried out for such a value."
- **P5** (keep-working): "Ordinary use must behave as it does today: uploading to, listing, and deleting objects inside the media area"; "deleting an item using the identifier the listing returned — that identifier may already include the configured root and must not be prefixed a second time"; "names containing a literal percent sign (they must not be decoded again)"; "an inner `..` that still resolves inside the area (it is collapsed, not refused)"; "a key spread over several route segments, and directories with leading or trailing slashes"; "listing the root of the area and any directory below it"; "copying between two keys that are both inside the area."
- **P6**: "Ordinary use must behave as it does today" (same sentence as P5).

## 1. Test-by-test fairness

"Correct fix could fail?" is judged against the fix that follows the primary mechanism (resolve the caller value against the area and refuse invalid values; preserve today's per-adapter handling where the instruction says ordinary use must keep working). "Maybe" entries are alternative-implementation readings discussed in §5.

| Test | What it asserts | Covering sentence | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| s3_upload::refuses an absolute object key | GET ?key=/etc/passwd -> 4xx, no presign | P1, P4 | no | low |
| s3_upload::refuses a relative key that walks above the root | ?key=../secrets -> 4xx, no presign | P1, P4 | no | low |
| s3_upload::refuses an inner climb that leaves the root | photos/../../outside -> 4xx | P1, P4 | no | low |
| s3_upload::refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| s3_upload::refuses an absolute windows drive key | C:/Windows -> 4xx | P4 | no | low |
| s3_upload::refuses an invalid key when the query value is a list | array whose first item escapes -> 4xx | P3, P4 | no (map-and-validate or first-element both refuse) | low |
| s3_upload::never mints a url for a bucket key outside the root | private/config.json -> 4xx or rooted presign | P1 | no (expectConfined allows refuse or prefix) | low |
| s3_delete_list::delete refuses a key that walks above the root | DELETE media ../secret -> 4xx | P1, P4 | no | low |
| s3_delete_list::delete refuses an absolute key | DELETE /etc/passwd -> 4xx | P4 | no | low |
| s3_delete_list::delete refuses an inner climb that leaves the root | photos/../../outside -> 4xx | P1, P4 | no | low |
| s3_delete_list::delete refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| s3_delete_list::delete refuses an empty key | DELETE media "" -> 4xx | P4 | no | low |
| s3_delete_list::delete never deletes a bucket key outside the root | private/config.json -> 4xx or rooted delete | P1 | no | low |
| s3_delete_list::listing refuses a directory that walks above the root | directory ../ -> 4xx | P1, P4 | no | low |
| s3_delete_list::listing refuses a leading-slash traversal directory | /../ -> 4xx | P4 | no | low |
| s3_delete_list::listing refuses an inner climb that leaves the root | a/../../outside -> 4xx | P1, P4 | no | low |
| s3_delete_list::listing refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| dos::upload refuses a directory that walks above the root | multipart ../outside -> 4xx, no PutObject | P1, P3, P4 | no | low |
| dos::upload refuses an inner climb that leaves the root | a/../../../outside -> 4xx | P1, P3, P4 | no | low |
| dos::upload refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| dos::upload refuses a directory containing a NUL byte | ../\0outside -> 4xx | P4 | no | low |
| dos::delete refuses a key that walks above the root | DELETE ../secret -> 4xx | P1, P4 | no | low |
| dos::delete refuses a key split across route segments that walks above the root | ['media','..','..','secret.png'] -> 4xx | P3, P4 | no | low |
| dos::delete refuses an absolute key | DELETE /etc/passwd -> 4xx | P4 | no | low |
| dos::delete refuses an empty key | DELETE "" -> 4xx | P4 | no | low |
| dos::delete never deletes a space key outside the root | private/config.json -> 4xx or rooted delete | P1 | no | low |
| dos::listing refuses a directory that walks above the root | directory .. -> 4xx | P1, P4 | no | low |
| dos::listing refuses a leading-slash traversal directory | /../x -> 4xx | P4 | no | low |
| dos::listing refuses an inner climb that leaves the root | a/../../outside -> 4xx | P1, P4 | no | low |
| dos::listing refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| azure::upload refuses a directory that walks upward | form directory ../outside -> 4xx, no upload | P2, P3, P4 | no | low |
| azure::upload refuses an inner climb that leaves the area | a/../../../outside -> 4xx | P2, P3, P4 | no | low |
| azure::upload refuses an absolute directory | form directory /etc -> 4xx | P2, P4 ("absolute ... refused") | maybe: a fix that strips leading slashes from every directory accepts it; primary fix validates the joined blob name and refuses | medium |
| azure::upload refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| azure::upload refuses a bare parent directory | ../a.png -> 4xx | P2, P4 | no | low |
| azure::delete refuses a blob name that walks upward | DELETE ../secret.png -> 4xx | P2, P4 | no | low |
| azure::delete refuses an absolute blob name | DELETE /etc/passwd -> 4xx | P4 | no | low |
| azure::delete refuses an empty blob name | DELETE "" -> 4xx | P4 | no | low |
| azure::listing refuses a directory that walks upward | directory ../ -> 4xx | P2, P4 | no | low |
| azure::listing refuses a leading-slash traversal directory | /../x -> 4xx | P4 | no | low |
| azure::listing refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| cloudinary::upload refuses a folder that walks upward | folder ../outside -> 4xx, no upload | P2, P3, P4 | no | low |
| cloudinary::upload refuses an inner climb that leaves the area | a/../../../outside -> 4xx | P2, P3, P4 | no | low |
| cloudinary::upload refuses a leading-slash traversal folder | /../outside -> 4xx | P3, P4 | no (strip leading slash then traversal still refuses) | low |
| cloudinary::upload refuses a folder containing a NUL byte | ../\0outside -> 4xx | P4 | no | low |
| cloudinary::upload refuses a filename that walks upward | folder photos, originalname ../evil.png -> 4xx | P3, P4 | no (file name is a listed input; must be validated) | low |
| cloudinary::delete refuses a public id that walks upward | DELETE ../secret -> 4xx | P2, P4 | no | low |
| cloudinary::delete refuses an absolute public id | DELETE /etc/passwd -> 4xx | P4 | no | low |
| cloudinary::delete refuses an empty public id | DELETE "" -> 4xx | P4 | no | low |
| cloudinary::listing refuses a directory that walks upward | directory ../ -> 4xx | P2, P4 | no | low |
| cloudinary::listing refuses an inner climb that leaves the area | a/../../outside -> 4xx | P2, P4 | no | low |
| cloudinary::listing refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| batch_delete::refuses a key that walks above the root | keys ['../secrets.png'] -> 4xx, no DeleteObjects | P1, P3, P4 | no | low |
| batch_delete::refuses an inner climb that leaves the root | a/../../outside -> 4xx | P1, P3, P4 | no | low |
| batch_delete::refuses an absolute key | /etc/passwd -> 4xx | P4 | no | low |
| batch_delete::refuses a windows-style separator | ..\outside -> 4xx | P4 | no | low |
| batch_delete::refuses the whole batch when one key is invalid | [valid, ../outside] -> 4xx, zero operations | P1, P4, P3 | maybe: a filter-out-invalid-and-delete-valid fix would return 200; primary map-and-validate refuses the request | low |
| batch_delete::never deletes a batch key outside the root | [rooted, private/config.json] -> 4xx or all rooted | P1 | no | low |
| app_router::presign refuses an absolute key | GET key=%2Fetc%2Fpasswd -> 4xx | P1, P4 | no | low |
| app_router::presign refuses a key that walks above the root | key=..%2Foutside -> 4xx | P1, P4 | no | low |
| app_router::presign never mints a url for a bucket key outside the root | key=private/config.json -> 4xx or rooted | P1 | no | low |
| app_router::direct upload refuses a key that walks above the root | POST key=../outside -> 4xx, no PutObject | P1, P4 | no | low |
| app_router::direct upload never writes a bucket key outside the root | key=private/config.json -> 4xx or rooted | P1 | no | low |
| app_router::delete refuses a key that walks above the root | DELETE ../secret -> 4xx | P1, P4 | no | low |
| app_router::delete never deletes a bucket key outside the root | private/config.json -> 4xx or rooted | P1 | no | low |
| app_router::listing refuses a directory that walks above the root | directory=..%2F -> 4xx | P1, P4 | no | low |
| app_router::listing refuses a windows-style separator | directory=..\outside -> 4xx | P4 | no | low |
| copy::refuses a source that walks above the root | from ../secrets -> 4xx, no CopyObject | P1, P4 | no | low |
| copy::refuses a destination that walks above the root | to ../outside -> 4xx | P1, P4 | no | low |
| copy::refuses an absolute source | from /etc/passwd -> 4xx | P4 | no | low |
| copy::refuses an inner climb in the destination | a/../../../outside -> 4xx | P1, P4 | no | low |
| copy::never copies a bucket key outside the root | from private/config.json -> 4xx or rooted | P1 | no | low |
| copy::never copies to a bucket key outside the root | to private/archive -> 4xx or rooted | P1 | no | low |
| s3::mints an upload url for a nested key | photos/summer/a.png -> 200, one presign | P5/P6 | no | low |
| s3::accepts a name containing a literal percent sign | photos/100%off.png -> 200 | P5 ("must not be decoded again") | no (a fix that re-decodes fails; that is non-compliant) | low |
| s3::accepts an inner parent segment that stays inside the root | photos/../a.png -> 200 | P5 ("collapsed, not refused") | no | low |
| s3::deletes the identifier the listing returned, without re-prefixing it | delete media/photos/a.png once | P5 (no second prefix) | no | low |
| s3::deletes a relative key given inside the root | delete photos/a.png -> rooted key | P6 | no (root resolution is P1) | low |
| s3::lists the root of the media area | GET {} -> Prefix media/ | P5 | no (must treat missing directory as root) | low |
| s3::lists a directory with leading and trailing slashes | /photos/ -> Prefix media/photos/ | P5 | no | low |
| s3::treats an empty key as a listing request | GET ?key= -> 200 listing, no presign | P6 (today's handler shape: no key means list) | maybe: an unconditional empty-key refusal returns 400; primary fix keeps the existing `if (key)` branch | low |
| dos::stores a file in a directory inside the root | directory photos -> Key media/photos/a.png | P6 | no | low |
| dos::accepts leading and trailing slashes on the directory | /photos/ -> Key media/photos/a.png | P5 | no (trim then root) | low |
| dos::accepts a filename containing a literal percent sign | 100%off.png preserved | P5 | no | low |
| dos::deletes the identifier the listing returned | media/photos/a.png not double-prefixed | P5 | no | low |
| dos::deletes a key split across route segments | photos,a.png joined and rooted | P5 | no | low |
| dos::lists the root of the media area | Prefix media/ | P5 | no | low |
| dos::lists a directory inside the root | photos -> Prefix media/photos/ | P5 | no | low |
| azure::uploads a file into a directory | directory photos, filename a.png -> photos/a.png | P6 | no | low |
| azure::deletes a blob by name | media/photos/a.png -> photos/a.png | P6 | no | low |
| azure::lists the root | no directory -> prefix "" | P5 | no | low |
| azure::lists a directory | photos -> prefix photos/ | P5 | no | low |
| cloudinary::uploads into a folder | folder photos recorded | P6 | no | low |
| cloudinary::strips a leading slash from the folder | /photos -> folder photos, 200 | P5 ("directories with leading or trailing slashes"; "as it does today" strips) | maybe: a fix that refuses every absolute directory returns 400; primary fix preserves today's strip | medium |
| cloudinary::deletes a public id | photos/a.png destroyed | P6 | no | low |
| cloudinary::lists the root | folder="" search | P5 | no | low |
| cloudinary::lists a folder | folder="photos" search | P5 | no | low |
| injected_routes::deletes several listed identifiers | batch of rooted ids deletes unchanged | P5 | no | low |
| injected_routes::mints a presigned upload url for a nested key | app-router GET key=photos%2Fa.png -> 200 | P6 | no | low |
| injected_routes::accepts a direct upload for a nested key | POST key=photos%2Fa.png -> rooted PutObject | P6 | no | low |
| injected_routes::deletes a listed identifier | app-router delete media/photos/a.png unchanged | P5 | no | low |
| injected_routes::lists a directory | app-router Prefix media/photos/ | P5 | no | low |
| injected_routes::copies between two in-root keys | CopySource/Copy keys unchanged | P5 | no | low |

## 2. Leniency (quality, non-blocking)

Security property P1 (in-root confinement, root-configured backends):
- Wrong fix: guard only the reported presigned-upload branch. Caught by `security/s3_delete_list.test.ts` and `security/dos.test.ts` (`checks/sf-miss-s3-delete-list.patch`, `sf-miss-dos.patch`).
- Wrong fix: check `..` after joining with the root (join collapses it). Caught by `s3_upload` absolute/`../` tests (`checks/caf-after-join.patch`).
- Wrong fix: `startsWith(root)` without a `/` boundary (accepts `mediaevil/x` and sends it outside). **No test catches**; every root case uses `private/config.json` or traversal.
- Wrong fix: validate after the storage call. Caught by `expectRefused`/`expectConfined` (operations length 0) in every security test.

P2 (every backend, including no-root):
- Wrong fix: skip Azure/Cloudinary because no root is configured. Caught by `security/azure.test.ts` and `security/cloudinary.test.ts` (`checks/sf-miss-azure-cloudinary.patch`).
- Wrong fix: leave the Azure `delivery-handlers.ts` read SAS unbounded. **No test catches**; the oracle leaves it open. It is a real route where protection never existed, so it is realistic that it is open; it is a coverage gap, not an out-of-scope excuse.

P3 (every input shape):
- Wrong fix: handle only a string query, not a repeated array. Caught by `s3_upload` list test (`checks/malformed-array.patch`).
- Wrong fix: not joining split route segments. Caught by `dos` split-segment delete test.
- Wrong fix: validate the Azure/DOS multipart directory but not the client file name. Caught only for Cloudinary (`cloudinary::refuses a filename that walks upward`); **no Azure/DOS filename test**.

P4 (4xx, no storage operation):
- Wrong fix: crash/500. Caught: `expectRefused` requires 4xx and the manifest's crash-as-refusal is n/a.
- Wrong fix: return 4xx after a partial operation. Caught by operation-length assertions (`s3_upload`, `batch_delete`, `copy`, `dos`, `azure`, `cloudinary`).

P5/P6 (keep working; over-broad fixes):
- Refuse all `..` -> caught by `functional/s3::accepts an inner parent segment that stays inside the root`.
- Re-decode percent -> caught by `functional/s3` and `functional/dos` literal-percent tests.
- Always prefix the root -> caught by all three delete-identifier tests (`functional/s3`, `functional/dos`, `functional/injected_routes`).
- Reject empty/missing listing directory -> caught by all `lists the root` tests.
- Partial batch delete -> caught by `batch_delete::refuses the whole batch when one key is invalid`.
- Refuse all leading-slash directories -> caught by `functional/cloudinary::strips a leading slash from the folder`.

Layer placement: the suite imports the exported handler factories, so a guard placed only in an outer Next route/middleware dispatcher is bypassed and would fail. For a shipped library package that is not a correct fix (it would not protect other consumers); validating in the exported handler or a helper it calls is the valid layer. Guards before or after multer/SDK setup both pass, because the tests count only storage/SAS calls; any 4xx status (400/403/422) satisfies `expectRefused` and only a 5xx/crash fails.

Traps:
- T1: fix only the upload branch -> caught by `s3_delete_list` (`sf-miss-s3-delete-list`) and `s3_upload` (`sf-miss-s3-upload`).
- T2: fix S3 only, skip the DOS sibling -> caught by `security/dos.test.ts` (`sf-miss-dos`).
- T3: skip no-root adapters -> caught by `azure`/`cloudinary` (`sf-miss-azure-cloudinary`).
- I1: fix single delete, ignore batch -> caught by `injected_batch_delete` (`sf-miss-batch-delete`); a filter-and-delete fix is caught by the whole-batch test.
- I2: fix pages-router only -> caught by `injected_app_router` (`sf-miss-app-router`).
- I3: fix upload/delete, skip copy; or one side only -> caught by `injected_copy` (`sf-miss-dos-copy`), which asserts both source and destination.

Wrong fixes no test catches: root-prefix boundary (`mediaevil/x`); Azure delivery read handler; Cloudinary search-expression injection via `"` in `directory` (oracle leaves raw; notes call it a follow-up); NUL bytes on S3/Azure/copy (NUL is tested only for DOS upload and Cloudinary upload); backslash on copy; Azure/DOS multipart filename traversal.

## 3. Hints (quality, non-blocking)

- "names containing a literal percent sign (they must not be decoded again)" -> "names containing a literal percent sign must be preserved exactly."
- "an inner `..` that still resolves inside the area (it is collapsed, not refused)" -> "an inner `..` that still resolves inside the area must be accepted."
- "must not be prefixed a second time" -> "must target the same object."
- "the object-store prefix (folder)" -> "the root prefix that bounds the media area."
- "A signed-in editor asks the media API for an upload URL ... for example an object at the bucket root or in another application's prefix" is the report's example; keep, but it is the least-neutral sentence. Neutral: "A signed-in editor asks the media API ... for a key outside the configured media area."

## 3a. Surface descriptions — Required: generalize

1. "The same unchecked value is used by the delete and listing operations, and by the other storage backends the project ships." This points at T1's delete/list branches, T2 and T3. General rewording: delete it; P1 already says "every operation the media API exposes and every storage backend the project ships."
2. "Some backends offer that setting; others currently do not." This is a class split that exists to cover T3. General rewording: delete it; P2 already says "including backends that have no configured root."
3. "an object store or an image service. The project ships several such backends behind the same media API." Product-term backend taxonomy. General rewording: "whichever storage service the deployment is configured to use"; retain the single coverage sentence in P2.

## 4. Realism (quality, non-blocking)

- T1 (S3 pages handler), T2 (DOS adapter), T3 (Azure/Cloudinary adapters): real upstream adapter code at the pinned commit; the sites are reachable through the exported factories. No planting concerns.
- I1 (S3 batch delete), I2 (S3 app-router handlers), I3 (DOS copy/move): builder-injected modules, not upstream, but written in the style of the surrounding adapters (auth, method check, error helper), plausible as parity/multi-select/move features, and exported from each package index. They are the package's public entry points, so reachable; the only realism caveat is that no Next route file in the repo mounts them. Not contrived in shape.
- No trap looks planted for the sake of a test: each wrong-fix check removes exactly one natural guard. `checks/pass-alt.patch` (stack normaliser) and `checks/pass-hardening.patch` (control-char/length checks) both score 1.0, and the independent fresh-agent `checks/blind.patch` scores 1.0, showing the routes are solvable from the visible material.
- Keep the Azure delivery read handler and the Cloudinary search-expression injection in the leniency list, not as "beyond the advisory": they are real routes where protection never existed.

## 5. Verdict

**Gate a (fairness): READY.** Every security test maps to P1–P4 read literally, every functional test to P5–P6. Oracle, `pass-alt`, `pass-hardening` and the independent fresh-agent `checks/blind.patch` all score 1.0 (73/73 security, 30/30 functional). The four "maybe" rows are alternative readings, not failures of the primary-mechanism fix: Azure `upload('/etc')` (strip-everywhere accepts; primary validates the joined blob name and refuses), Cloudinary `upload('/photos')` (refuse-all-absolute rejects; primary preserves today's strip), S3 empty `?key=` (the existing no-key-means-list shape is preserved), batch delete (map-and-validate refuses before send; filtering is the alternative). The blind fix independently chose the primary mechanism and passed every test; no contradiction, underivable assertion, hostile harness or impossible spec fires.

**Required: generalize** — (1) drop "The same unchecked value is used by the delete and listing operations, and by the other storage backends the project ships"; (2) drop "Some backends offer that setting; others currently do not"; (3) replace "an object store or an image service ... several such backends" with "whichever storage service the deployment is configured to use."

**Quality to tighten** — add tests for the six §2 gaps (root-prefix boundary, Azure delivery read, Cloudinary search injection, NUL on S3/Azure/copy, backslash on copy, Azure/DOS filename traversal); neutralize §3 wording; wire or document the injected siblings as package entry points.

Human review: confirm the leading-slash-directory reading — "directories with leading or trailing slashes" permits stripping only where the adapter already strips (Cloudinary `/photos`) while an absolute form directory becoming an absolute blob name (Azure `/etc`) must be refused — and that empty `?key=` on the S3 pages GET remains a listing request, not an empty-key refusal.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
