# FAIRNESS review — hermes-agent-ds

Reviewed all listed task, build and checks files; nothing was run. Legend: S1 = general property
(untrusted-party text never reaches the model with user authority; wherever assembled); S2 =
`[BLOCKED:` replacement without echo; S3 = machine-vs-human reading is adversarial; S4 = tool-result
envelope; S5 = refusal (success:false, error, atomic); S6 = retention; S7 = preservation; S8 =
shapes; S9 = keep legitimate uses working.

## 1. Test-by-test fairness

### 1.1 Security (28)

| test (file::name) | asserts | fair basis | could a correct fix fail? | risk |
|---|---|---|---|---|
| `test_context_files::test_project_instruction_file_promptware_blocked` | clean + C2 `AGENTS.md` → marker, payload absent | S1+S2 | no | low |
| `…::test_hermes_project_file_promptware_blocked` | same for `.hermes.md` | S1 | no | low |
| `…::test_alternate_project_instruction_file_promptware_blocked` | same for `.clinerules` | S1 (route-neutral) | no — leaving this loader unguarded is incomplete | low |
| `…::test_runtime_discovered_instruction_promptware_blocked` | runtime-discovered hint → marker | S1 | no | low |
| `…::test_filler_word_variant_blocked` | filler-word injection blocked | S3 + close variants | no | low |
| `…::test_invisible_unicode_variant_blocked` | U+2062 file → marker, marker text absent | S3 | no — whole-file block is the existing scanner unit; sentence granularity is not the mechanism | low |
| `…::test_held_out_c2_paraphrase_blocked` | differently worded C2 → marker | S1+S3+close variants | no — detection, not matching, required | low |
| `…::test_identity_file_promptware_blocked` | poisoned `SOUL.md` → marker | S1 | no | low |
| `test_memory_snapshot::test_poisoned_memory_file_replaced_in_snapshot` | per-entry marker, `CLEAN-OK` kept | S1+S2+S6 | no | low |
| `…::test_poisoned_user_file_replaced_in_snapshot` | same for `USER.md` | S1 | no | low |
| `…::test_promptware_planted_after_clean_entry_blocked` | ordering cannot hide poison | S1 | no | low |
| `test_memory_sources::test_backend_prompt_block_blocked` | provider block → marker | S1 "whichever producer" | no | low |
| `…::test_recalled_context_blocked` | recalled text → marker, no echo | S1+S2 | no — marker required; dropping the block is not the stated replacement | low |
| `test_memory_writes::test_add_promptware_refused` | `success:false`, error, unchanged | S5 | no | low |
| `…::test_add_promptware_leaves_disk_unchanged` | no marker on disk | S5 | no | low |
| `…::test_replace_with_promptware_refused` | replace refused; clean survives | S5 | no | low |
| `…::test_bulk_import_promptware_refused` | import refused; clean entries not applied | S5 "no part of a refused change is applied" | no — atomic refusal explicit | low |
| `test_tool_results::test_external_tool_result_enveloped[web_extract]` | tags, source=tool, payload intact, DATA wording | S4 | no — primary mechanism is the message builder | low |
| `…[web_search]` | same | S4 | no | low |
| `…[browser_navigate]` | same | S1+S4 | no | low |
| `…[browser_snapshot]` | same | S1+S4 | no | low |
| `…[mcp_linear_get_issue]` | same | S1+S4 | no | low |
| `…[mcp_filesystem_read]` | same | S1+S4 | no | low |
| `…[mcp_notion_search]` | same | S1+S4 | no | low |
| `…[x_search]` | same | S1 "a party other than the user can influence" | no — a third-party-post search API is literally covered | low |
| `…::test_envelope_is_not_content_conditional` | benign long result enveloped | S4 "even when it looks harmless" | no | low |
| `test_codex_transport::test_codex_mcp_result_enveloped` | Codex MCP projection enveloped | S1 "wherever assembled"+S4 | no — the projector is that path's only assembly point | low |
| `…::test_codex_mcp_namespaced_tool_name_keeps_envelope` | source has mcp/evil/read; recorded name unchanged | S4 "name under which the call is recorded" | no | low |

### 1.2 Hidden functional (29)

| test (file::name) | asserts | fair basis | could a correct fix fail? | risk |
|---|---|---|---|---|
| `test_context_legit::test_clean_agents_md_loads` | clean loads | S7+S9 | no | low |
| `…::test_clean_cursorrules_loads` | clean loads | S7+S9 | no | low |
| `…::test_clean_clinerules_loads` | clean loads | S7+S9 | no | low |
| `…::test_priority_unchanged_and_clinerules_additive` | priority/additivity | S9 + visible behaviour | no — scanning does not change load order | low |
| `…::test_absent_additional_file_adds_nothing` | absent file no-op | S9 | no | low |
| `…::test_classic_injection_still_blocked` | existing block kept | S7+S9 | no | low |
| `…::test_clean_operational_wording_loads` | node/network/script/"you must" clean | S7 | no — over-blocking is not preservation | low |
| `…::test_clean_soul_md_loads` | clean identity file loads | S7 | no | low |
| `test_memory_legit::test_clean_entries_pass_through_snapshot` | clean entries, no marker | S7 | no | low |
| `…::test_clean_operational_wording_passes_snapshot` | operational wording clean | S7 | no | low |
| `…::test_poisoned_entry_stays_in_live_state_and_is_removable` | raw entry live; removable; disk cleared | S6 | no | low |
| `…::test_already_blocked_entry_is_not_double_blocked` | one marker | S7 + idempotent marker | no — placeholder matches no pattern | low |
| `…::test_snapshot_frozen_across_mid_session_add` | snapshot frozen | S9 + visible behaviour | no | low |
| `…::test_clean_memory_add_and_replace` | clean writes succeed | S7 | no | low |
| `…::test_clean_bulk_import_works` | clean import applies | S7+S9 | no | low |
| `…::test_clean_import_deduplicates` | dedupes | S9 visible behaviour | no | low |
| `test_memory_sources_legit::test_clean_provider_block_included` | clean block included | S7 | no | low |
| `…::test_two_clean_provider_blocks_joined` | both joined | S7 | no | low |
| `…::test_clean_recall_fenced_with_system_note` | fence/system note kept | S7 + visible wrapper | no — no reason to rewrite the fence | low |
| `…::test_empty_recall_returns_empty` | empty → "" | S9 | no | low |
| `test_tool_result_shapes::test_low_risk_tool_unchanged` | local tools raw | S8 "tools that work only on the user's own machine and its inputs" | no — memory/skill_view/terminal/read/write/patch are literal local tools | low |
| `…::test_short_external_result_unchanged` | 13-char result raw | S8 "too short to carry an instruction" | no — 13 chars is far below any plausible instruction threshold | low |
| `…::test_multimodal_content_keeps_list_identity` | list object identity | S8 "not a plain string keeps its exact shape" | no — the non-string exemption makes pass-through primary; identity follows | medium |
| `…::test_already_enveloped_content_not_wrapped_again` | no double framing | S8 | no | low |
| `…::test_none_and_empty_content_unchanged` | `None`/`""` raw | S8 | no | low |
| `…::test_message_schema_fields_preserved` | role/name/tool_name/call id | S8 "keeps its existing fields" | no | low |
| `test_codex_legit::test_clean_mcp_result_keeps_role_id_and_payload` | role/id/payload | S7+S8 | no | low |
| `…::test_command_projection_not_enveloped` | command output raw | S8 local-tool exemption | no | low |
| `…::test_agent_message_projection_unchanged` | assistant text raw | S9 | no | low |

### 1.3 Project tests (232, pristine visible copies)

Grouped by file: visible repo tests restored before grading; the same judgement applies throughout.

| file (count) | asserts | fair basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `project/test_memory_tool.py` (61) | memory API, drift guard, snapshot, scanner messages | visible repo tests; S9 + "do not modify tests" | no — keep `_scan_memory_content`/`ENTRY_DELIMITER`/`MEMORY_SCHEMA` and error strings | low |
| `project/test_memory_tool_schema.py` (3) | schema; action enum `add/replace/remove` | visible repo test | no — exposing injected `import` in the schema is an unnecessary feature change | low |
| `project/test_prompt_builder.py` (124) | discovery/priority, scanner reactions, SOUL, truncation | visible repo test | no — keep `_scan_context_content` and fixtures | low |
| `project/test_subdirectory_hints.py` (13) | discovery, truncation, permission errors | visible repo test | no | low |
| `project/test_codex_event_projector.py` (31) | projection shapes, ids, role alternation | visible repo test | no — wrapping short/clean MCP output keeps payload substrings | low |

## 2. Leniency (QUALITY, non-blocking)

| property / trap | most plausible wrong fix | caught by (test; check patch) | gap |
|---|---|---|---|
| P1/T1 context | old regexes only; miss a loader; miss runtime; miss `SOUL.md`; hard-code report phrases; over-block | variant/runtime/alternate/identity/held-out tests; `sf-no-context`, `sf-exact-phrases`, `sf-no-clinerules`, `ff-block-all-context` | only AGENTS/.hermes/.clinerules/SOUL/subdir-AGENTS poisoned; `CLAUDE.md`, `.cursorrules`, subdir variants clean-only |
| P2/T2 writes | reuse old scanner; raise; accept then sanitise; only `add`; scan after merge; over-block | write/import tests; `sf-no-memwrite`, `sf-crash-on-poison`, `ff-drop-blocked-entries` | memory C2 cases all use `PAYLOAD`; dispatcher-only guard leaves `import_entries` open |
| P2/T3 snapshot | no load scan; drop blocked entries; block whole file | snapshot tests; `sf-no-memload`; functional live-state/`CLEAN-OK` | none material |
| P3/T4 envelope | wrap all/stringify/rewrap/short/content-conditional; only or no `x_search`; miss Codex | shape + `test_envelope_is_not_content_conditional`; `ff-wrap-everything`, `sf-xsearch-only`, `sf-no-xsearch`, `sf-no-tool`, `sf-no-codex` | allowlist pinned to eight names; no unlisted third-party name; caller-layer placement unobserved |
| P3/T5 provider | untouched; drop block; over-block clean | `test_backend_prompt_block_blocked`; `sf-no-provider`; clean-provider tests | only one poisoned provider (first-only sanitizer passes) |
| P3/T6 recall | tag-stripping only; drop block; block all recall | `test_recalled_context_blocked`; `sf-no-recall`; clean-recall tests | none material |
| P3/T7 Codex | fix builder only; classify by `mcp_`; over-wrap commands | codex tests; `sf-no-codex`; `test_command_projection_not_enveloped` | MCP error results need only contain "error" (not enveloped) |
| P1/T8 `.clinerules` | no scan; fold into priority chain; over-block | `test_alternate_…`; `sf-no-clinerules`; priority/clean tests | none material |
| P2/T9 import | leave it; partial apply; scan after merge | `test_bulk_import_promptware_refused`; `sf-no-import`; clean-import tests | dispatcher-only guard leaves the store method; no direct test |
| x_search | omit; wrap only it | `[x_search]`; `sf-no-xsearch`, `sf-xsearch-only` | none material |

Uncaught: (1) memory detector hard-coded to `PAYLOAD`; (2) tool allowlist pinned to the eight
names; (3) caller-level envelope outside the tested builder; (4) hardening only tested loaders
(`CLAUDE.md`/`.cursorrules` clean-only); (5) marker echoing a non-tell fragment; (6)
first-provider-only sanitization; (7) `import_entries` guarded only in the dispatcher. All
catalogue entries map to a catching patch; both `pass` patches score 1.0.

## 3. Hints (QUALITY, non-blocking)

| quote | gives away | neutral wording |
|---|---|---|
| "A short "housekeeping" paragraph that enrols the agent with an outside coordinator, gives it another name, and tells it to act covertly…" | paraphrases the payload's tells; invites phrase-matching | "An ordinary-looking paragraph contributed by another party is followed as though the user wrote it." |
| "A variant wording, filler inserted into a tell-tale phrase, or a character a human reader cannot see…" | names the filler and invisible-character variants | "How text is worded, formatted, or encoded does not change how it is treated; text a human reader would not perceive as written is itself adversarial and is withheld." |
| "Results of tools that work only on the user's own machine and its inputs…" | product-level tool classification | "Results whose content the user alone controls…" |

No file, function, package, route, stage or flaw count is named.

## 3a. Required: generalize

none — the property is stated once over the protected outcome; the envelope-tag, `[BLOCKED:` and
field sentences are the asserted interface, not route pointers.

## 4. Realism (QUALITY, non-blocking)

T1–T8 are plausible, reachable maintainer code; T5–T7 are unmodified upstream routes the published
fix left open (realistic by definition); `x_search` is a real optional tool. Flag **T9 (medium)**:
`import` is absent from `MEMORY_SCHEMA` and `_refresh_snapshot` has no other caller, so it reads
bolted on — expose `import` in the schema (updating the visible test) or route it through an
existing action.

## 5. Verdict

**a. UNFAIRNESS gate — READY.** Every security test asserts a literal consequence of S1–S4/S5;
every functional test asserts S7/S8 preservation. The natural fix (scanner in every loader,
load-time snapshot sanitization, atomic write/import refusal, envelopes in the builder and Codex
projector, provider/recall sanitization) passes. Builder-vs-dispatcher is the only correct-fix risk;
the primary-mechanism rule resolves it for the builder, where a result is presented. S8's explicit
exemptions resolve "too short" and non-string shape.

**Quality to tighten:** add a held-out memory C2 case; an unlisted third-party tool name; a
dispatch-path integration test; poison cases for `CLAUDE.md`/`.cursorrules` and subdir variants; an
anti-echo assertion; a second poisoned provider; a direct `import_entries` test; value-equality in
the multimodal test; schema-reachable import (or drop T9); neutralize the three hints.

Human review: confirm the builder-layer reading and the unquantified "too short"/"exact shape"
clauses (13-char and list-identity assertions), and that T9's schema-invisible `import` is
acceptable realism.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
