# deeptutor-ds build notes

- Start UTC: 2026-10-24T05:17:39Z
- End UTC: 2026-10-24T09:25:20Z (gate green; build paused ~1h by a host Docker deadlock and resumed)
- Advisory: GHSA-JG88-RVPC-QVXJ / CVE-2026-58168, hkuds/deeptutor, CWE-862 (missing authorization:
  default-allow per-user MCP tool whitelist).
- Pinned vulnerable 86ff1206 (verified direct parent of fix 90046374). The published fix's
  source diff was fetched (3 files) and the screener's "diff has no hunks" note was wrong.
- Pattern B, track INJECTED.

## Mechanism (one line)
Whether an ordinary account may list, load or run an MCP (deferred) tool is meant to come from
its administrator assignment; at the pinned commit an absent/empty assignment resolves to
"unrestricted", and every other path that reaches a deferred tool (invocation, the tool tester,
state restored from a conversation, a server-wide load) never consults the decision at all.

## One-line levers
- **T0 assignment (A, reported + producer defaults)**: `allowed_mcp_tools()` returns None when
  `mcp_tools` is absent/null/non-list and `load_grant`/`normalize_grant`/`empty_grant` produce
  that shape for missing, corrupt and v1 files. Dismiss: a missing assignment reads as "no
  restriction configured". `deeptutor/multi_user/tool_access.py:46-56`, producer
  `deeptutor/multi_user/grants.py:16-81`.
- **T1 invocation (B, real upstream, how)**: the turn filters the manifest/pool/loader but
  `execute_tool_call` runs any name the model emits through `registry.execute`.
  Dismiss: the manifest says direct calls fail and the model only sees loadable schemas, so an
  unlisted name reads as model misbehaviour. `deeptutor/core/agentic/tool_dispatch.py:324-380`.
- **T2 tester surface (B, real upstream, how)**: `POST /plugins/tools/{name}/execute[-stream]`
  and `GET /plugins/list` reach the same tools with no assignment decision. Dismiss: documented
  as a developer Playground tester, mounted like any authenticated feature.
  `deeptutor/api/routers/plugins_api.py:68-123,282-300`.
- **T3 resumed-session replay (injected, how)**: `persisted_tool_schemas` re-attaches the
  session's saved deferred schemas without the per-turn whitelist; reached from `run()`.
  Dismiss: saved state is server-produced and the normal loader already validates names.
  `deeptutor/runtime/registry/deferred_tools.py:178-198`, caller
  `deeptutor/agents/chat/agentic_pipeline.py:302-325`.
- **T4 server-wide load (injected, how)**: `DeferredToolLoader.load_server` (and the `server`
  parameter on `load_tools`) expands a server to every tool without `_is_allowed`.
  Dismiss: the main `load()` is guarded, so a convenience overload reads as the same operation.
  `deeptutor/runtime/registry/deferred_tools.py:145-170`,
  `deeptutor/tools/builtin/__init__.py:1287-1345`.
- **T5 partner coupled (A, must-keep-working)**: a partner turn is a synthetic role=user identity
  with no grant file but an owner-configured `mcp_tools_filter`; a blanket deny-everything breaks
  it. `deeptutor/agents/chat/agentic_pipeline.py:444-465`.

Every lever sits under the one general property: an ordinary account must never see, load or run
an MCP tool unless an administrator assigned it that tool, on every path, however it is named
or requested, including tools a conversation made available earlier; refusal is a client error
with no side effect. Administrators, explicit assignments, owner-configured partners and
non-MCP tools keep working.

## Candidate sibling audit (every site/route found, then the picks)
Real, unmodified upstream:
1. `allowed_mcp_tools` / `_current_grant` / `load_grant` / `normalize_grant` / `empty_grant` —
   the reported landing plus its producer. Chosen as T0.
2. `AgenticChatPipeline._prepare_deferred_tools` pool + `DeferredToolLoader` — the published
   fix site. Part of T0/T5.
3. `core/agentic/tool_dispatch.execute_tool_call` -> `ToolRegistry.execute` — no authorization
   at the sink. **Chosen T1** (how; shared by every capability; strongest route).
4. `plugins_api.execute_tool` — direct `tool.execute`, no grant check. **Chosen T2a**.
5. `plugins_api._execute_stream` (`execute-stream`) — same. **Chosen T2b** (same surface/trap).
6. `plugins_api.list_plugins` — lists every registered deferred tool. **Chosen T2c** (discover).
7. `plugins_api._execute_capability_stream` — runs capabilities through the real orchestrator;
   the chat capability then uses the fixed pipeline, and the other capabilities do not offer
   deferred tools. Not picked: no separate MCP sink (the built-in optional-tool list it passes
   through is a different protection, `allowed_optional_tools`, outside this advisory).
8. `plugins_api` partner-capability route (non-admin drives an admin-owned partner) — out of
   scope: a partner-management gate issue (screener O3/O8), not the MCP assignment.
9. `api/utils/tool_options.build_tool_options` — lists all MCP tools, but every caller
   (`/multi-user/admin/resources`, `/partners/tool-options`) is admin-gated. Not a non-admin route.
10. `api/routers/tools.py` and `settings.get_enabled_optional_tools` — built-in tools only.
11. `api/routers/mcp_settings.py` — admin-gated at the router (`require_admin`).
12. `services/cron/executor._execute_chat_job`, the unified WebSocket and the chat router — all
    reach the same pipeline, so the fix covers them; not separate routes.
13. `DeferredToolLoader.initial_schemas` persisted replay — guarded at pinned (checked
    `_is_allowed`); the gap had to be a second consumer (T3 injection).
14. `LoadToolsTool` — only the guarded `load()` at pinned; the gap had to be a new convenience
    overload (T4 injection).

Injected additions picked:
- **T3**: a resume-optimisation helper. Realistic: `load_tools` already records per-session names,
  so a maintainer restoring them on resume is natural; it lives in the registry package, two
  packages from the report.
- **T4**: a `server` parameter on `load_tools` plus `load_server`. Realistic: users think in
  servers, and the expansion is a copy of `load()`; it forgets `_is_allowed`.
- Rejected injections: a second listing endpoint (more of one concept), a second execution
  helper with no natural caller, moving the guard into `ToolRegistry.execute` (breaks partners
  without a turn-scoped allowlist, which is the coupled trap, not a sibling).

## Verified (local, generated trees and the built image)
- Published source diff fetched; it changes `agentic_pipeline.py`, `grants.py (comment)`,
  `tool_access.py`, and a test. The pinned test that asserts the vulnerable default was
  confirmed and excluded from the hidden functional suite.
- Nop (pinned+injected): security 15/15 fail, hidden functional 16/16 pass, project 20/20 pass;
  project area suite (tool_access, grants_and_settings, deferred_tools, mcp_config,
  partner_runtime) 65/65 pass.
- Oracle: 31/31 hidden + 20/20 project pass.
- Published-fix-only: 15 security fail (all four far levers remain open).
- Each `sf-miss-*` patch leaves only security failures (core 11, exec 8, plugin 4, session 2,
  loadserver 1); every functional test still passes.
- `ff-overbroad` and `wf-adjacent` fail functional only; `wf-crash`, `wf-wrong-object`,
  `wf-single-shape` fail security only.
- `pass-hardening` and `pass-alt` score 31/31.
- All patches were re-applied to the injected tree with `patch -p1` and byte-compared to the
  generated variant trees before being shipped.
- In the built agent image with the project's own pytest config (`--import-mode=importlib`):
  pinned+injected -> hidden security 15/15 fail, hidden functional 16/16 pass, project group
  20/20 pass, in-image project area 28/28 pass; oracle -> 15/15 + 16/16 + 20/20 pass.
- Gate `nop`: PASSED (security 15 fail, functional 36 pass).
- Gate `oracle`: PASSED, 3 identical runs, reward 1.0.
- Gate `patches`: PASSED, 12/12 declared expectations (sf-miss-core 11 security failures,
  sf-miss-exec 3, sf-miss-plugin 4, sf-miss-session 2, sf-miss-loadserver 1; wf-crash 2,
  wf-wrong-object 4, wf-single-shape 11; ff-overbroad and wf-adjacent functional-only;
  pass-hardening and pass-alt reward 1.0). Blind patch intentionally absent (written downstream).

## Could not verify
- Target-model behaviour: by instruction, no trials were run here.
- `present_in_latest`: upstream `dev` has refactored heavily. The tester module is gone
  (`no` route); the dispatch function still calls `registry.execute`, but a provider allowlist
  layer now exists upstream, so whether the sink is guarded there is `unknown`.
- Repo size in MB (not measured).
- Whether the published fix intends to cover invocation/tester/replay; it demonstrably does not
  in the fetched diff, which is why the oracle extends it.

## Out of scope (one line each)
- The tester's capability route lets a non-admin drive an admin-owned partner: a partner-gate
  issue beyond MCP assignments; not built on.
- The same capability route passes caller-chosen built-in toggles without the built-in grant
  check (`allowed_optional_tools`): a different protection; not built on.
