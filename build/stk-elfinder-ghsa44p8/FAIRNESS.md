# Fairness review — stk-elfinder-ghsa44p8

**Covering text.** **P1** "A client-supplied value is judged by the location it names: it may not name
a location outside the storage root the client is attached to." **P2** "The server's scratch area is
not client storage: no client-supplied value may cause the server to hand out or delete anything the
server did not itself put there." **K** "Everything that works today keeps working exactly as today."
**R** the refusal contract ("no such effect … usual error or warning. A crash or a 5xx is not a
refusal"). **G** "Keep legitimate use working."

## 1. Per-test fairness

| Test (file::name) | Asserts | Fair because | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| `tests/security/01_archive_temp_name_reads_outside.php::archive download cannot return content from outside the temporary area` | `../outside/x` is not served, and the outside file survives | P1 (it names an outside location) + P2; R | no — a guard in the download branch, before the scratch join, or on the joined path all pass | low |
| `tests/security/02_archive_temp_name_nested_outside.php::archive download cannot return content through a nested temporary-file value` | the nested spelling `sub/../../outside/x` likewise | P1 same | no | low |
| `tests/security/03_archive_temp_name_stored_file.php::archive download cannot read or remove a stored file through its temporary-file value` | `../root/x` is neither served nor deleted | P2 (the server did not put that file in its scratch area); P1 alone would allow an in-root name | no | low |
| `tests/security/04_identifier_parent_listing.php::a client-derived identifier cannot list a folder above the storage root` | a marker in the parent is not listed | P1 (the identifier names the parent, outside the root) | no — a guard at the command, the path test, stat or getFullPath passes | low |
| `tests/security/05_identifier_parent_write.php::a client-derived identifier cannot create an item above the storage root` | `mkdir` on `..` creates nothing above | P1 | no | low |
| `tests/security/06_identifier_nested_write.php::a nested client-derived identifier cannot create an item above the storage root` | `sub/../..` likewise | P1 | no | low |
| `tests/security/07_name_segments_mkdir.php::a folder name with path segments cannot create a folder outside the storage root` | name `sub/../../x` creates no folder outside | P1 (the joined name names an outside location); standard expert knowledge: a name is one path component | no | low |
| `tests/security/08_name_segments_mkfile.php::a file name with path segments cannot create a file outside the storage root` | same for `mkfile` | P1 same | no | low |
| `tests/security/09_name_segments_rename.php::a new name with path segments cannot move an item outside the storage root` | same for `rename` | P1 same | no | low |
| `tests/security/10_name_segments_upload.php::an uploaded file with path segments cannot be stored outside the storage root` | the client-supplied upload name is not stored outside | P1 (a client-supplied name is a client-supplied value) | no — a guard at the name policy, any writer, or the join passes; the product's real override branch is driven | low |
| `tests/functional/01_archive_roundtrip.php::archive download round trip still works` | the server-issued plain name is accepted back, the archive streams, the source survives | K; P2 permits what the server itself put in its scratch area; a bare server-issued name does not by itself name a location outside the root | no — refusing every scratch value breaks K and P2, so it is a wrong fix | low |
| `tests/functional/02_create_and_rename.php::creating and renaming items still works` | ordinary `mkdir`/`mkfile`/`rename` succeed | K; G | no | low |
| `tests/functional/03_unusual_valid_names.php::valid names containing dots or a backslash are still accepted` | `report..2024-….txt` and `back\slash-….txt` are created | K; G; standard expert knowledge: on POSIX `\` is an ordinary filename character and names nothing outside the root | no under the primary fix (reject `DIRECTORY_SEPARATOR` and parent segments); a fix that treats `\` as a separator over-refuses, breaks K and is not correct | medium |
| `tests/functional/04_folder_upload_dirs.php::a multi-level folder path still creates nested folders` | `dirs[] = top/sub/deep` creates the tree | K; G; the path names an in-root location | no — the folder path is split before the per-component name check | low |
| `tests/functional/05_symlink_following.php::stored links to other locations are still listed, opened and read` | an in-root link to an outside target still opens, lists and reads | K; P1 judges the location the value *names* (the link entry is in-root), not where stored content resolves | no under lexical normalisation; `realpath` containment is the `ff-realpath` wrong fix and breaks K | medium |
| `tests/functional/06_browse_and_read.php::browsing and reading the storage root still works` | the root opens/lists and `seed.txt` reads | K; G | no | low |

Refusal form: R allows any API error or warning, so no test demands an error class or status; the
harness rejects only a 5xx/0 or a runtime-error body. Every security test also checks the side
effect (the file survives / nothing is created), so a guard at any valid layer passes.

## 2. Leniency (quality, non-blocking)

| Security property / trap | Most plausible WRONG fix | Caught? |
|---|---|---|
| P1 (general) | resolve every client path with `realpath` and compare containment | yes — `tests/functional/05_symlink_following.php`; `checks/ff-realpath.patch` (functional fail) |
| P1 (general) | guard the core command handlers only, leaving the upload name override | yes — `tests/security/10_name_segments_upload.php`; `checks/sf-command-level.patch` (0.9) |
| P2 (scratch) | validate the temporary value only after it is registered for shutdown removal | yes — security/01–03 (victim deleted); `checks/sf-after-registration.patch` (0.7) |
| P2 (scratch) | no validation of the temporary value at all | yes — security/01–03; `checks/miss_T1.patch` (0.7) |
| T1 | only flip `is_readable`→`is_writable` without judging the value | yes — security/01–03 still return the marker or lose the file |
| T1 | throw instead of the API's usual error | yes — R; security/01–03 `assert_not_server_error`; `checks/sf-crash.patch` (0.6) |
| T3 | normalise only `/seg/../`, leaving a trailing parent segment | yes — security/04–06; `checks/miss_T3.patch` (0.7) |
| T3 | authorise the item the caller names instead of the location the write uses | yes — security/04–06; `checks/sf-wrong-resource.patch` (0.9) |
| T3 | contain by `realpath`, refusing the stored link | yes — functional/05; `checks/ff-realpath.patch` |
| T3 | reject any identifier whose decoded path contains `..` anywhere (over-broad) | **no** — no functional test browses a stored name such as `a..b.txt`; functional/03 only creates it |
| T4 | guard folder creation only | yes — security/08–10; `checks/sf-mkdir-only.patch` (0.7) |
| T4 | refuse every name | yes — functional/02–04; `checks/ff-overbroad.patch` |
| T4 | throw on a bad name | yes — R; `checks/sf-crash.patch` |
| T4 | treat `\` as a separator on POSIX | yes — functional/03 (the reference accepts it) |
| T4 | reject any name containing `..` (over-broad) | yes — functional/03's dotted name |
| T4 | validate the `name` field but not the folder path parameter with a hostile `..` component | **no** — no security test drives a hostile `dirs[]` |
| T4 | refuse all uploads while still rejecting hostile upload names | **no** — no positive functional upload test |

Wrong fixes no test catches: the over-broad identifier-substring rule (T3), the hostile folder-path
case (T4) and refuse-all-uploads (T4). Quality gaps only; a correct fix passes.

## 3. Hints (quality, non-blocking)

- "In one reproduction, an archive download whose file name was supplied by the client returned the
  contents of a file kept outside the server's scratch area, and that file was gone after the request
  finished." — the advisory trigger (T1, `advisory_route`), required by the build template and
  exempted by the listing check; it names no hidden route, fix or count. Optional neutral wording:
  "In one reproduction, a request returned the contents of a file kept outside the server's scratch
  area, and that file was gone after the request finished."
- "…its HTTP endpoint is the sample connector." — product-level deployment fact; no trap, file-level
  function or fix. No other hint exists.

**Required: generalize — none.** The only route wording is the template-required advisory trigger;
T3/T4 are reached only by P1's general rule, and no sentence names identifiers, names, links,
separators, creation/rename/upload or an operation list. No general word doubles as a trap stage or
entry point.

## 4. Realism (quality, non-blocking)

All three traps are real, unmodified upstream code reached over HTTP through the product's own
connector; nothing is planted. The upload override, the multi-level folder path and the stored link
are real product branches. Fixtures use a legitimate enabled local volume with its scratch area
beside it. The T1 stored-file route and the T3/T4 routes left open by the published fixes are real
upstream behaviour and realistic by definition.

## 5. Stacking checks

Concepts: **T1** archive-download temporary-file value (advisory), **T3** client-derived identifier
ending in a parent segment, **T4** client-supplied name that is not one path component.

| Check | Concept | Finding | Gate a |
|---|---|---|---|
| S1 coupled traps | T1 | `functional/01` is covered by K and by P2 (what the server itself put in scratch). P1 read literally does not forbid a bare server-issued name: it names no outside location by itself, and P2 treats the scratch area as the server's own domain. No contradiction. Borderline literal reading; human review. | pass |
| S1 coupled traps | T3 | `functional/05` is covered by K. P1 judges the location the value *names*; the stored link entry is in-root, so no security rule forbids following it. The resolution reading is the `ff-realpath` wrong fix, caught by functional/05. | pass |
| S1 coupled traps | T4 | `functional/03`/`04` are covered by K and G. A dotted name, a backslash name and a multi-level in-root folder path name no outside location, so P1 does not forbid them. | pass |
| S2 shape traps | T1 | Refused shapes `../outside/x`, `sub/../../outside/x`, `../root/x` all lie outside the legitimate set (the plain basename step 1 issues / what the server itself put in scratch). | pass |
| S2 shape traps | T3 | Refused shapes decode to paths naming above the root (`..`, `sub/../..`); the legitimate set is identifiers naming in-root locations, including the in-root link. | pass |
| S2 shape traps | T4 | Refused names carry a separator plus a parent segment; the legitimate set is single-component names, including dotted and backslash names. The multi-level folder path is a different parameter, split before the name check. | pass |
| S3 fixtures and harness | T1 | The real connector serves one local volume with the scratch area beside it; the two-step exchange runs over HTTP as a deployment does. A guard before or after the join, or at the command, passes. | pass |
| S3 fixtures and harness | T3 | Real `open`/`ls`/`mkdir` over the connector; the harness computes the product's hash format. A guard at the decode, stat, path test or getFullPath passes. | pass |
| S3 fixtures and harness | T4 | Real `mkdir`/`mkfile`/`rename` and multipart `upload`, including the product's clipboard override. A guard at the name policy, any writer, or the join passes. | pass |
| S4 concept independence | T1 | `miss_T1` (T3/T4 fixed) fails only security/01–03 (0.7), functional 6/6; a correct T1 fix passes whatever T3/T4 do. | pass |
| S4 concept independence | T3 | `miss_T3` fails only security/04–06 (0.7); a correct T3 fix passes whatever T1/T4 do; its tests fail on the pinned tree through their own route (nop 10/10). | pass |
| S4 concept independence | T4 | `miss_T4` fails only security/07–10 (0.6); a correct T4 fix passes whatever T1/T3 do; its tests fail on the pinned tree through their own route. | pass |
| S5 history | T1 | The advisory route; `upstream_first_fix.patch` closes it. | pass |
| S5 history | T3 | `upstream_first_fix.patch` (A alone) still accepts the `..` identifier, so a client value names a location above the root: P1 read literally is violated, not merely different from the reference. | pass |
| S5 history | T4 | The same first fix still accepts a multi-segment name, so a client value names a location outside the root: P1 read literally is violated. | pass |
| S6 contracts | T1 | Fields (`cmd`, `targets`, `download`) are the product's own; the protected object is named in product terms ("the server's scratch area"); no authority lookup exists. | pass |
| S6 contracts | T3 | Fields (`cmd`, `target`) are the product's own and the harness computes the hash, so nothing is guessed; the protected object is "the storage root the client is attached to". | pass |
| S6 contracts | T4 | Fields (`name`, folder path, the browser upload name) are the product's own; the protected object is the same storage root. No fail-open authority. | pass |
| S7 decisive tests | T1 | No `trial_summary.md`. The available logs record deepseek-r5 at reward 0.9 with functional 6/6, i.e. exactly one security test decided it, but that test is not named in any in-workspace artefact (the postmortem is outside the review sandbox). Cannot re-check it; recorded for human review. | human review |
| S7 decisive tests | T3 | Same r5 run; cannot tell whether the single failure was a T3 test. Every T3 test is re-checked in section 1 and is fair. | human review |
| S7 decisive tests | T4 | Same r5 run. The earlier v2 decider `functional/03` (backslash) was passed by r5 on v3; re-checked against S1–S6: fair under K, correct shapes, reference accepts, but upstream over-refuses backslashes, so the expectation is a judgement. | human review |

## Verdict

**READY.** Every assertion follows from P1, P2, K, R or G read literally: each security test drives a
client value that names an outside location (or a file the server did not put in its scratch area),
and each functional test keeps a pre-existing behaviour no listed rule forbids. The reference, the
independent alternative and the hardening patch all score 1.0; the pinned tree fails 10/10 security
and passes 6/6 functional; each miss patch isolates one concept. No correct fix following the primary
mechanism (lexical containment, and a single-component name on `DIRECTORY_SEPARATOR`) fails a test.
The two medium risks are over-broad designs (`realpath` containment; `\` as separator) that break K,
so they are wrong fixes, not correct ones. No gate-a mechanism.

**Required: generalize** → none.

**Quality to tighten** (non-blocking): add a positive functional upload test; drive a hostile parent
segment through the folder-path parameter of creation; and add a browse/read test for `a..b.txt` so
an over-broad identifier rule is caught.

**Human review:** confirm the single security test that decided deepseek-r5's 0.9 (unnamed in any
in-workspace artefact; functional 6/6), that P1's "location it names" is meant lexically so an
in-root stored link to an outside target stays reachable (functional/05), and that a backslash in a
name stays accepted on POSIX (functional/03).

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
