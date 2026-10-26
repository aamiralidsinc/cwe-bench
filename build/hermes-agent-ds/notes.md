# hermes-agent-ds — build notes

- start (UTC): 2026-10-18T23:39Z
- end (UTC): 2026-10-19T00:39Z
- candidate: screener-v2 entry 317, GHSA-33QV-C5QM-799V / CVE-2026-10223 / PYSEC-2026-3575
- repo: nousresearch/hermes-agent
- pinned: b6ce7a451f72a185ceafc4a3d13a599ee00a62d5 (direct parent of fix 0dee92df22bdc0cfbcad90ca954aa14916f018de)
- pattern: A+B, track: injected
- language: Python >= 3.11

## Candidate verification

`git -C pinned rev-parse 0dee92df^` == b6ce7a451f. The fix commit is the published
security commit "promptware defense — shared threat patterns + memory load-time scan +
tool-result delimiters". The pinned tree is the fix's parent; the fix's own regression
tests are not present. The mirror of current upstream is at
`/home/mara/screen4/hosts/317/latest` (read-only lookup).

## Design (levers)

Each lever is one line: pattern, shape, site, reason a solver would skip it.

1. **T1_context_scanner** — A, landing — project instruction file / runtime-discovered
   instruction file carrying C2/promptware text, plus filler-word and extended
   invisible-unicode shapes — `agent/prompt_builder.py:55` and its entry points
   `build_context_files_prompt` / `load_soul_md` / `agent/subdirectory_hints.py:188` —
   reason: an injection scanner already exists and blocks classic phrases, so the site
   looks defended.
2. **T2_memory_write_scan** — A, far site — memory add/replace carrying promptware with no
   classic injection phrase — `tools/memory_tool.py:137` — reason: memory writes already
   run a scanner; it just misses the promptware vocabulary.
3. **T3_memory_snapshot** — A, far site (save/reload) — poisoned `MEMORY.md`/`USER.md`
   on disk, loaded into the frozen system-prompt snapshot with no scan —
   `tools/memory_tool.py:201-217` — reason: writes are already scanned, so a load-time
   re-scan looks redundant.
4. **T4_tool_envelope** — A, far site (generic message builder) + input shapes — long
   plain-string results from third-party-content tools (`web_extract`, `web_search`,
   `browser_*`, `mcp_*`, and the optional `x_search` tool) —
   `agent/tool_dispatch_helpers.py:320` — reason: the report is about project/memory
   context, and a generic message builder is not a context loader; the fix is an
   architectural envelope, not a regex.
5. **T5_provider_block** — B, uncovered — a configured memory backend's
   `system_prompt_block()` text is joined into the system prompt with no scan —
   `agent/memory_manager.py:318-335` — reason: the provider is plugin/trusted code and
   a neighbouring feature the published fix never touched.
6. **T6_recall_fence** — B, uncovered — prefetched recall is fenced as
   "authoritative reference data" with tag stripping only, no threat scan —
   `agent/memory_manager.py:227-241` — reason: it is already inside a
   `<memory-context>` fence, so it looks defended.
7. **T7_codex_mcp** — B, uncovered — the Codex app-server projector builds `role=tool`
   messages for MCP results directly, bypassing the message builder; the
   `mcp.server.tool` spelling would not match the `mcp_` prefix either —
   `agent/transports/codex_event_projector.py:217-253` — reason: a separate transport,
   alternate backend, and the Codex runtime owns its own model loop.
8. **T8_clinerules_loader** — injected sibling (context decision) — an extra
   project-instruction loader for `.clinerules` appends raw text without the scanner —
   `agent/prompt_builder.py:1426` in our copy — reason: the solver upgrades the scanner
   and assumes every loader calls it; this one does not.
9. **T9_memory_import** — injected sibling (memory decision) — a bulk `import` action
   merges §-delimited entries into live state and refreshes the frozen snapshot
   directly, bypassing both the write scanner and the load-time sanitizer —
   `tools/memory_tool.py:454` in our copy — reason: the solver fixes add/replace and
   load-from-disk and assumes every memory write funnels through them.

`x_search` is an input shape of T4, not a separate trap: it is the same envelope
mechanism with a tool the published external-tool set misses. It gets its own
uncovered-route register row.

## Sites and entry points covered by security tests

- `build_context_files_prompt(cwd=...)` — startup project context load.
- `load_soul_md()` — identity context load (same scanner; no separate lever).
- `SubdirectoryHintTracker.check_tool_call(...)` — runtime-discovered context.
- `MemoryStore.load_from_disk()` + `format_for_system_prompt(...)` — frozen snapshot.
- `MemoryStore.add` / `replace` and `memory_tool(action=...)` — write validator.
- `memory_tool(action="import", ...)` — injected bulk import.
- `make_tool_result_message(...)` — tool-result message builder.
- `MemoryManager.add_provider` + `build_system_prompt()` — provider block.
- `build_memory_context_block(...)` — recalled-context fence.
- `CodexEventProjector.project(...)` — Codex MCP tool projection.

## Coupled must-keep-working behaviour (functional tests)

- Clean project instruction files still load unchanged; absent optional files are a
  no-op; the first-wins priority among the existing context files is unchanged.
- Clean memory entries still pass into the snapshot; a blocked entry stays in live
  state, is visible via the memory read response and can still be removed by
  substring; an entry already starting `[BLOCKED:` is not wrapped twice; the snapshot
  stays frozen across mid-session `add`s.
- Message builder: low-risk tools (`terminal`, `read_file`, `memory`, `write_file`,
  `patch`) unchanged; strings under 32 chars unchanged; non-string/multimodal content
  keeps its exact identity; already-enveloped content not wrapped again; the envelope
  preserves the original payload and names the source.
- Memory sources: clean provider blocks still included; clean recalled context still
  fenced with the system note; empty recall still returns "".
- Codex projector: clean MCP result still projected with role `tool`, the same
  deterministic call id, and the same payload; command/file-change/agent-message
  projections unchanged.
- Project's own tests for the area: `tests/tools/test_memory_tool.py`,
  `tests/tools/test_memory_tool_schema.py`,
  `tests/agent/test_prompt_builder.py`, `tests/agent/test_subdirectory_hints.py`,
  `tests/agent/transports/test_codex_event_projector.py`.

## Interface contract stated to the solver

- Envelope: content begins `<untrusted_tool_result source="<tool>">`, ends
  `</untrusted_tool_result>`, keeps the payload, and contains framing that the content
  is DATA, not instructions.
- Blocked content replaced by a placeholder beginning `[BLOCKED:`.
- Refused memory write: `success: false` plus an `error` string, no disk change.
- 32-character threshold, non-string pass-through, already-enveloped pass-through,
  low-risk tools unchanged.

## Oracle

`solution/fix.patch` = published source changes (shared pattern library, context
scanner migration, memory write + load-time scan, tool-result envelope) plus:

- B1/B2: sanitize provider blocks and recalled context.
- B3: envelope MCP results in the Codex projector through a shared public wrapper.
- x_search added to the external-tool classification.
- S1: scan the added `.clinerules` loader.
- S2: scan/refuse bulk imports before any side effect.

## Patch checks planned

- security_fail per lever (T1–T8, x_search).
- functional_fail: over-broad wrapping of every tool result; dropping blocked entries
  from live state/disk; blocking every context file.
- pass/hardening: oracle + normalization/defanging hardening.
- pass/alternative: a second valid design (per-call-site envelopes rather than the
  shared builder).

## Verified

- Pinned commit is the direct parent of the published fix.
- All six published fix sites exist in the pinned tree with the stated shapes.
- The four Pattern-B routes exist unchanged in the pinned tree and are re-confirmed
  behaviourally by the nop run (security tests fail on pinned).
- Current upstream (2026-10-17 mirror) still lacks the provider/recall scan, the
  Codex MCP envelope, and `x_search` in the external-tool set.

## Could not verify / open

- No shell access to the advisory prose; the fix diff and the screener record are the
  basis.
- Whether Codex-projected messages are replayed to a model in every runtime; the
  projector's entry point is real and tested directly.
- The exact upstream post-fix hardening (latest adds a delimiter-token defang); our
  hardening patch mirrors it but the published fix does not.

## Fairness revision (pre-trial, 2026-10-20)

Applied the `build/hermes-agent-ds/FAIRNESS.md` §5a required changes:

- Bulk import: the instruction now requires every write path (including a bulk import or
  merge) to refuse matching content before changing state, and `test_bulk_import_promptware_refused`
  now asserts a partially matching import applies nothing.
- Recall: dropped the unstated `<memory-context>` fence assertion from
  `test_recalled_context_blocked`; clean-recall fencing is still pinned by the functional test.
- Invisible unicode: the instruction now states that invisible/bidirectional control
  characters used to conceal instructions must be blocked.
- DATA framing: `helpers._DATA_RE` accepts any "data … not … instructions" wording
  in the envelope.
- x_search: the instruction now says search APIs returning third-party posts are included.
- Codex source: the instruction now states that `source` names the tool and MCP results
  use `mcp.<server>.<tool>`.

Quality tightening also applied: neutralised the verbatim-payload and "not only …"
hints; added a held-out C2 paraphrase security case; added a poisoned home identity
file case; added over-broad-heuristic clean fixtures; added an echo guard to
`assert_blocked`; added a benign long external result (structural envelope) case; and
added a third-party MCP tool outside the original seven names.

## Gate log

- static: PASS except the two items intentionally left for the fairness reviewer
  (`pass`/`kind=blind` patch, `build/hermes-agent-ds/FAIRNESS.md`). No leak, metadata,
  image-test, exact-status or catalogue problems.
- nop: PASSED. Untouched injected image: security 0/24 passing (all 24 fail), functional
  259/259 passing (27 hidden + 232 project tests).
- oracle: PASSED. 3/3 runs at reward 1.0 (24/24 security, 259/259 functional) with identical results.
- patches: PASSED (20/20 per-check gate runs). Run per-check because the shared machine's Docker-network-prune race makes a
  20-trial stage flaky; each declared check is invoked through the gate's `--only patches`
  stage on its own and retried on infrastructure flakes, then the full manifest is restored.

## Patch-check execution note

The patches stage was split into one gate invocation per declared check.  Each invocation is
the gate's own `--only patches` logic and writes a per-check report; infrastructure failures
(`failed to set up container networking: network ... not found`, caused by concurrent gates
pruning networks on the shared host) were retried, and no expectation was relaxed.  The final
manifest lists all 20 checks again.  Per-check reports: `build/hermes-agent-ds/check_report_*.json`
and `patch_check_results.json`.

## Sibling-injection upgrade (2026-10-20, instruction-only)

Before: the report was a three-part checklist. It named the landing site ("workspace-discovered
guidance", "instruction-file convention and every discovery path", "home directory"), the memory
route list ("every memory write path, including any bulk import or merge action"), the tool channel
list ("search APIs that return third-party posts"), a source format (`mcp.<server>.<tool>`) and a
count ("results shorter than 32 characters").

After: one general property over the protected outcome — adversarial guidance in text a party
other than the user can influence must never reach the model with the authority of the user's
instructions, whichever producer supplies it, however it is written/stored/encoded, and wherever
it is assembled; guidance is withheld behind `[BLOCKED:`, and third-party tool results are framed
as untrusted data. No route, producer, operation, channel, object-kind, stage, format, file,
function or count is named. The hidden-unicode/filler and source-naming fairness clauses are kept
in general form ("text that would read differently to the model than to a human", "the name under
which the call is recorded"). The refusal/atomicity, retention, preservation and shape contracts
are kept, stated generally.

Levers unchanged; at least three are how-type, so no new lever and no repo-code change:
- T3_memory_snapshot — producer the write check never calls (M6): content arrives from disk after
  the write path, straight into the frozen snapshot.
- T4_tool_envelope — coupled must-keep-working values/shapes (M11): low-risk tools, short strings,
  non-string identity, already-framed content and the message schema must all survive the
  classification; content-conditional framing fails the benign-long-result test.
- T5_provider_block / T6_recall_fence / T7_codex_mcp — real routes where the protection never
  existed (M4), all left open by the published fix.
- T9_memory_import is also a producer the write check never calls (M6).
T1, T2 and T8 are where-type siblings.

Coverage unchanged and complete for the stated property: every route the property covers literally
is already asserted, including the published-fix gaps (provider block, recalled context, Codex MCP
projection, x_search) and never-protected paths (load-time snapshot, tool results, alternate
loader, bulk import). No security test, check patch or oracle change was needed.

Changed files: `tasks/hermes-agent-ds/instruction.md` and `build/hermes-agent-ds/manifest.json`
(leak_terms extended with the route/source/stage/count words the rewrite forbids: "instruction
file", "workspace", "home directory", "memory store", "provider", "recall", "transport",
"bulk import", "merge", "search api", "session start", "system prompt", "multimodal",
"32 characters", "at startup"; status updated) plus this note. No change under tests/, solution/,
environment/ or checks/. No image rebuild; the prebuilt image is reused.

Static: `python3 -I builder/gate.py hermes-agent-ds --only static` reports only the separately
wired missing blind pass patch; no leak, metadata, file-name or count problem.
