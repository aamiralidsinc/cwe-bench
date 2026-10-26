# FAIRNESS — stk-langflow-794

Scope: instruction.md, all of `tests/`, `solution/fix.patch`, `manifest.json`, `notes.md`, `checks/*.patch`. Nothing was run; no upstream lookup.

Citation key:
**A1** = "No response the server returns may expose file content, file names, or flow identifiers that belong to an account other than the caller's."
**A2** = "Where a request is scoped to part of the caller's own material, only that part may be returned."
**C1** = "No identifier or file name passed in may make the product reach a stored file outside the container that identifier names; the data returned must come from inside it."
**K1** = "Everything that works today keeps working." / "keep legitimate use working"
**K2** = "A refusal is a client error that returns no file content. Any error status or protocol error is acceptable."
**R1** = "Resource URIs keep their current download shape."

## 1. Test fairness

| Test | Asserts | Fair because | Correct fix could fail? | Risk |
|---|---|---|---|---|
| `security/test_mcp_foreign_flow_read.py::test_foreign_flow_read_is_refused` | foreign flow's file refused; caller's own file read afterwards in the same session | A1 | no (only a refusal that tears the session down; a refusal is a per-call client error, K2) | low |
| `security/test_mcp_foreign_second_file_read.py::test_second_foreign_file_read_is_refused` | a file in a second foreign flow is refused; own read works | A1 | no | low |
| `security/test_mcp_foreign_read_after_listing.py::test_foreign_read_after_listing_is_refused` | an identifier learned from `resources/list` cannot be read; own read works | A1 | no | low |
| `security/test_mcp_cross_project_read.py::test_cross_project_read_is_refused` | the project server refuses the caller's own flow outside the project; in-project read works | A2 | no | low |
| `security/test_mcp_resources_listing_scope.py::test_resources_listing_is_scoped_to_caller` | no foreign flow id in `resources/list`; caller's own quoted file name present | A1 (flow identifiers / file names) + K1 | no (only a fix that stops listing the caller's own account-level files, contrary to K1) | low |
| `security/test_mcp_tools_listing_scope.py::test_tools_listing_is_scoped_to_caller` | no foreign flow as a tool; caller's own tool present | A1 | no | low |
| `security/test_mcp_encoded_separator_read.py::test_encoded_separator_cannot_escape_namespace` | a decoded `../` name cannot leave the addressed namespace; own read works | C1 | no | low |
| `security/test_mcp_foreign_bucket_read.py::test_foreign_bucket_read_is_refused` | another account's account-level file refused; caller's own bucket file readable | A1 + K1 | no | low |
| `security/test_lfx_storage_containment.py::test_standalone_storage_contains_names` | the lfx `LocalStorageService` refuses `../other/secret.txt`; unicode round-trip still works | C1 ("the product") | no — only an incomplete fix that hardens the server-used copy alone | medium |
| `functional/test_own_files_readable.py::test_own_namespaces_remain_readable` | own flow file, in-project file and own bucket file read with exact bytes | K1 | no (A1/A2/C1 do not forbid the caller's own data) | low |
| `functional/test_own_listings.py::test_own_items_remain_listed` | each account still sees its own flows in resources and tools | K1 | no | low |
| `functional/test_project_server_reads.py::test_project_scope_keeps_working` | the project server serves the in-project file, resource and tool | K1 | no | low |
| `functional/test_storage_roundtrip.py::test_storage_operations_roundtrip` | get/size/stream/list/delete round-trip, ASCII and unicode names | K1 | no | low |
| `functional/test_lfx_storage_roundtrip.py::test_standalone_storage_roundtrip` | same round-trip on the lfx class | K1 | no | low |
| `functional/project/test_mcp_utils.py::test_handle_list_resources_includes_flow_and_user_files` | a flow file URI and the caller's own user-file URI are built (fixed host/port) | K1 + R1 | no (only a fix that drops user files from the global listing) | low |
| `functional/project/test_mcp_utils.py::test_handle_list_tools_skips_blocked_custom_flows` | a blocked custom-component flow yields `[]`; handler called without a caller context | K1 (visible repo test) | no (only a fix that lets a caller-less direct call raise) | low |
| `functional/project/test_local_storage_service.py::TestLocalStorageServiceBasics::test_initialization` | `ready` and `data_dir` set | K1 (visible repo test) | no | low |
| `…::test_build_full_path` | path contains flow_id and name and ends with the name | K1 | no | low |
| `…::test_resolve_component_path` | resolved path contains flow dir + name, under `data_dir` | K1 | no | low |
| `…::test_resolve_component_path_malformed` | a malformed logical path is returned unchanged | K1 | no | low |
| `functional/project/test_local_storage_service.py::TestLocalStorageServiceFileOperations::test_save_and_get_file` | save/get round-trip | K1 | no | low |
| `…::test_save_file_creates_directory` | save creates `data_dir/<flow_id>` | K1 | no | low |
| `…::test_save_file_overwrites_existing` | overwrite returns new data | K1 | no | low |
| `…::test_get_file_not_found` | missing file raises `FileNotFoundError` saying "not found" | K1 | no (only a fix that rewrites missing-file errors as refusals) | low |
| `…::test_save_binary_file` | 256-byte binary round-trip | K1 | no | low |
| `…::TestLocalStorageServiceListOperations::test_list_files_empty_directory` | empty list for a missing flow | K1 | no | low |
| `…::test_list_files_with_files` | three saved files listed | K1 | no | low |
| `…::test_list_files_with_numeric_flow_id` | integer flow_id accepted | K1 | no (only a fix requiring a string id) | low |
| `…::test_list_files_async_iteration` | three files listed | K1 | no | low |
| `…::test_list_files_excludes_directories` | a flow_id containing `/` creates a subdirectory whose file is not listed at the parent | K1 | no (only a fix that also rejects separators in the flow identifier) | medium |
| `…::TestLocalStorageServiceDeleteOperations::test_delete_existing_file` | delete then get raises `FileNotFoundError` | K1 | no | low |
| `…::test_delete_nonexistent_file` | deleting a missing file does not raise | K1 | no | low |
| `…::test_delete_multiple_files` | all listed files deleted | K1 | no | low |
| `…::TestLocalStorageServiceFileSizeOperations::test_get_file_size` | size 100 | K1 | no | low |
| `…::test_get_file_size_empty_file` | size 0 | K1 | no | low |
| `…::test_get_file_size_nonexistent` | raises `FileNotFoundError` | K1 | no (only a refusal-rewriting fix) | low |
| `…::test_get_file_size_large_file` | 1 MiB size | K1 | no | low |
| `…::TestLocalStorageServiceTeardown::test_teardown` | teardown does not raise | K1 | no | low |
| `…::TestLocalStorageServiceEdgeCases::test_save_file_with_special_characters` | `test-file_2024.txt` round-trip | K1 | no | low |
| `…::test_save_file_with_unicode_content` | unicode content round-trip | K1 | no | low |
| `…::test_concurrent_file_operations` | 10 concurrent saves all listed | K1 | no | low |
| `…::test_concurrent_write_then_read` | 50 concurrent write/read pairs | K1 | no | low |

(`…` abbreviates `functional/project/test_local_storage_service.py`.)

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| A1, reads | check the flow exists / is MCP-enabled, never its owner; or fix only the HTTP route | yes — the three T1 tests; `miss_read_authz.patch` |
| A1, listings | fix reads only and leave both listings global | yes — `test_mcp_resources_listing_scope`, `test_mcp_tools_listing_scope`; `miss_resources_scope`, `miss_tools_scope` |
| A2 | add an ownership check but never pass the project scope | yes — `test_cross_project_read_is_refused`; `miss_read_authz`, `wrong_resource` |
| C1, decode | split before decoding, then trust the storage layer; ownership-only | yes — `test_encoded_separator_cannot_escape_namespace`; `miss_containment` |
| C1, storage APIs | guard only at the MCP handler, leaving the backend storage class open | **no** — only the lfx copy is driven with a traversal name |
| T1 | trust the URI namespace, or fix the project handler only | yes — the three T1 tests; `miss_read_authz` |
| T2 | ownership-only, no project scope | yes — `test_cross_project_read_is_refused` |
| T3 | fix the tools listing and forget the resources listing | yes — `test_resources_listing_is_scoped_to_caller`; `miss_resources_scope` |
| T4 | fix the resources listing and forget tools | yes — `test_tools_listing_is_scoped_to_caller`; `miss_tools_scope` |
| T5 | reject `..` before `unquote`, or trust the storage join | yes — `test_encoded_separator_cannot_escape_namespace`; `miss_containment` |
| T6 | harden only the running server's storage copy | yes — `test_standalone_storage_contains_names`; `miss_lfx_storage` |
| T7 | require an owned flow for every namespace; refuse any `%` in a name | yes — `test_own_namespaces_remain_readable`, `test_foreign_bucket_read_is_refused`, `test_own_items_remain_listed`; `drop_user_bucket`, `refuse_quoted` |
| A2, project listing | keep `if current_user:` so a project server still lists the caller's account-level files | **no** — no test asserts their absence |
| A2, project read | allow or deny the caller's own account-level bucket on a project server | **no** — untested either way |
| R1 | change the URI produced by `resources/list` and never read it back | **no** — tests substring-match; `test_mcp_foreign_read_after_listing` falls back to a hand-built URI once listings are scoped |
| Project server across accounts | filter a project listing by folder but not by user | **no** — only the project's own owner connects |

## 3. Hints (quality, non-blocking)

- Title "MCP file access is not confined to the caller's account" names the channel; neutral: "Stored file access is not confined to the caller's account."
- "The example above is one example, not the full set of affected inputs or callers" — "callers" hints at several call sites; neutral: "The example is one example; satisfy the required behaviour."

## 3a. Required: generalize

- "The same read through the ordinary HTTP download route is refused." — a sibling route and a fix hint; delete it (A1 already covers every surface).
- "whose first path segment is one of account A's flow identifiers and whose second segment is a file name that account A stored in that flow" — the URI's format/stage; reword "asks it to read a stored file that belongs to account A".
- "Resource URIs keep their current download shape." — "download" names an entry point; reword "Resource URIs keep their current shape."

## 4. Realism (quality, non-blocking)

No planted trap: T1–T6 are unmodified upstream sites and T7 is a real feature the listings advertise. Only anomaly: MiMo's 2-turn 1.0 solve (S7).

## Stacking checks

| Check | Verdict | Note |
|---|---|---|
| S1 coupled traps | pass | Values: own flow file, in-project file, own account-level bucket, quoted space/unicode names, own listing entries. Covered by K1; no security rule forbids them (A1 is other-account only, A2 permits the scoped part, C1 permits own names without separators). |
| S2 shape traps | pass | Refused shapes (foreign namespace, out-of-project namespace, decoded `../…`, foreign user-id namespace, foreign flow tool) all lie outside the legitimate set the keep-working clauses and fixtures describe; the legitimate shapes are accepted by every security test's positive control. |
| S3 fixtures/harness | pass (note) | States: two active non-superuser users, caller-owned project, MCP-enabled flows, uploads through the product's own routes, the caller's own project server — all legitimate. Real entry points everywhere; T6's entry point is a library class (Human review). |
| S4 independence | pass | Each test builds its own database; T1/T2 use different servers; T5 addresses the caller's own namespace so it does not need T1 fixed; T3/T4 do not read; `after_listing` falls back when listings are scoped. Masking H3c n/a (H4); the nop stage shows 0/9 security, so each security test fails on the pinned code through its own route. |
| S5 history | pass literally; quality note | H3a/H3b n/a (H4; `a_fix_leaves_b_open` null). `upstream_fix.patch` does violate the instruction as written — in a real DB session every read raises, breaking K1 — so it is not merely different from the reference. It also closes the same sites, so it proves no residual coverage; the failure is the upstream string-vs-UUID bug. The build's patches stage is red on this declared outcome (`functional_fail` vs `security_fail`) — a build-pipeline decision, not solver fairness. |
| S6 contracts | pass | Every name the tests touch exists at the pin (`handle_list_resources`, `handle_list_tools`, `current_user_ctx`, `session_scope`, `get_storage_service`, both `LocalStorageService` classes); the protected object is named in product terms; the authority is the authenticated caller via the existing API key / MCP session. |
| S7 decisive tests | fires → human review | No `trial_summary.md`. `trial_detail`: deepseek 3/3 at 0.8889 (8/9 security, functional green), so one security test decides each run and the artifact does not name it; MiMo's 2-turn 1.0 solve is implausible. |
| C1 (T1+T2) | pass | Read authorization + project scope; A1/A2 literal; `miss_read_authz`, `wrong_resource` caught. |
| C2 (T3) | pass | Unscoped global resources listing leaks flow ids and file names; A1 literal; `miss_resources_scope` caught. |
| C3 (T4) | pass | Unscoped tools listing embeds flow ids; A1 literal; `miss_tools_scope` caught. |
| C4 (T5) | pass | Decode-after-split escapes the addressed namespace; C1 literal; `miss_containment` caught. |
| C5 (T6) | pass (border) | Second in-repo storage implementation; C1's "the product" covers it literally; `miss_lfx_storage` caught. Entry-point judgement under Human review. |

## 5. Verdict

**GATE_A READY.** Every security test follows from A1/A2/C1; every coupled value is covered by K1; the harness drives the real app and routes, so a guard at the dispatcher, handler or storage layer passes; no test needs a guessed name. The only border is T6 (Human review).

### Quality to tighten (non-blocking)

- Assert that a project server's listing omits the caller's account-level file URIs (A2).
- Add a backend-storage traversal test (`langflow.services.storage.local.LocalStorageService`), mirroring the lfx test.
- Round-trip a server-produced own-file URI (R1).
- Pin the project-server account-bucket policy (reference denies) rather than accepting both.
- Name deepseek's deciding security test and re-check it against S1–S6; confirm the hidden `functional/project/*` copies equal the repo's visible tests; resolve `upstream_fix.patch`'s declared outcome (build gate red).

Human review: confirm C1's "the product" fairly reaches the standalone lfx `LocalStorageService` class (likely `security/test_lfx_storage_containment.py::test_standalone_storage_contains_names`), and why MiMo solved in 2 turns.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
