# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-djust-6530`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 6530; improper authorization / missing authentication check on a live event-
- Pinned (vulnerable) commit: 3b369d0c1a5e1efd6d63ad244ef5874440675bd2. Published fix: 1ae8aa9246b80477de7ddc4d90319a3b267bef04.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-6530",
 "pattern": "H4",
 "repo": "djust-org/djust",
 "pinned_commit": "3b369d0c1a5e1efd6d63ad244ef5874440675bd2",
 "protections": [
  "P1: a mount denied by view-level auth (login_required / permission_required / check_permissions) or by an on_mount hook must not leave a live event-dispatch channel: the WebSocket is closed (the sibling PermissionDenied branch closes 4403) or the view is unmounted, so post-denial frames cannot reach an @event_handler (websocket.py:1976-1978, 1979-1986, 2005-2007; event gate websocket.py:2722-2724).",
  "P2 (must-keep-working): a denial inside a multiplexed mount_batch must NOT terminate the shared socket - the redirect is reported in the batch's navigate[] array and sibling views keep serving events (websocket.py:2524-2537, 2571-2596, 2671-2679; contract test test_wire_protocol_snapshots.py:249-262; client 03-websocket.js:529-539).",
  "P3: every transport that implements mount must apply the same deny -> teardown rule; the SSE mount is a second hand-written implementation of the same operation (sse.py:155-246).",
  "P4: an event must be authorized on the dispatch, not only at mount, for a session whose auth posture changed after the mount (websocket.py:2722-2724; websocket_utils.py:200-291 covers handler- and object-level only; docs/guides/authentication.md:197-206 calls mount-only auth a deliberate trade-off).",
  "P5: a redirect target produced by developer hooks must be validated same-origin before it is sent to the client (mixins/request.py:84-99 does this for the HTTP path)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "python/djust/websocket.py:1795",
    "python/djust/websocket.py:1979-1986",
    "python/djust/websocket.py:2722-2724"
   ],
   "reason_to_dismiss": "The denial frame ({\"type\":\"navigate\"}) is sent and the handler returns, which reads as 'handled'; the wire-protocol snapshot pins the navigate frame as the correct auth-redirect response (python/djust/tests/test_wire_protocol_snapshots.py:525-528), so nothing at that site says the socket must also die.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "python/djust/websocket.py:1795 - self.view_instance = view_class() runs before any auth check and is never cleared on the redirect path",
    "python/djust/websocket.py:1969-1978 - the PermissionDenied denial shape does await self.close(code=4403), so a guard exists one branch earlier",
    "python/djust/websocket.py:1979-1986 - the redirect branch sends navigate and returns: no close, no self.view_instance = None",
    "python/djust/websocket.py:2722-2724 - handle_event gates only on 'self.view_instance is truthy', so every later {type:event} frame dispatches to the denied view",
    "python/djust/websocket.py:1834/1844 - the denied view is still registered in the observability registry and joined to its push channel group",
    "python/djust/static/djust/src/03b-sse.js:270-273 vs python/djust/static/djust/src/03-websocket.js:303-975 - the SSE client has a 'navigate' case; the WebSocket client switch has none, so on WS the frame does not even redirect"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "python/djust/websocket.py:2002-2007",
    "python/djust/websocket.py:4290-4291",
    "python/djust/hooks.py:71-88"
   ],
   "reason_to_dismiss": "A hook redirect is developer-defined control flow rather than an authentication denial, and a second redirect branch twenty lines below the first looks like the same code path already fixed.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "python/djust/hooks.py:71-88 - run_on_mount_hooks returns an arbitrary string from developer code",
    "python/djust/websocket.py:2002-2007 - the hook redirect sends navigate and returns, leaving view_instance set and the socket open",
    "python/djust/websocket.py:4290-4291 - handle_live_redirect_mount re-enters handle_mount on an already-open socket, so this exit is also reachable mid-session (second entry point, same sink)",
    "python/djust/websocket.py:2722-2724 - the same undifferentiated event gate"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "python/djust/websocket.py:2524-2537",
    "python/djust/websocket.py:2571-2596",
    "python/djust/websocket.py:2671-2679"
   ],
   "reason_to_dismiss": "Closing the socket is the obvious minimal fix, and mount_batch is 'just a lazy-hydration optimisation' that the report never mentions, so its contract is easy to overlook.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "python/djust/websocket.py:2524-2527 - _mount_one swaps only send_json for a collector; self.close is NOT swapped, so a close inside the redirect branch hits the real shared socket",
    "python/djust/websocket.py:2571-2596 - a navigate frame captured from handle_mount is returned to the batch caller instead of being dropped",
    "python/djust/websocket.py:2664-2679 - handle_mount_batch appends it to navigate[] and sends the batch response only after the loop",
    "python/djust/tests/test_wire_protocol_snapshots.py:249-262 - pins the mount_batch envelope with navigate[] after failed[]; a close or dropped navigate breaks it",
    "python/djust/static/djust/src/03-websocket.js:529-539 - the client forwards batch navigate entries as a live_redirect on the same socket",
    "python/djust/websocket.py:2722-2724 - view_instance is a single slot: clearing it unconditionally in the redirect branch also removes the event target of the sibling views mounted in the same batch"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "python/djust/sse.py:229",
    "python/djust/sse.py:236-244",
    "python/djust/sse.py:785-810"
   ],
   "reason_to_dismiss": "SSE is the documented degraded fallback transport and /event/ is the documented legacy endpoint (docs/sse-transport.md:17,21-22); the advisory and its remediation speak only about WebSocket close codes, so the SSE mount can be argued out of scope.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "python/djust/sse.py:229 - session.view_instance = view_instance is assigned before the auth check",
    "python/djust/sse.py:236-244 - both denial shapes (PermissionDenied -> error frame; redirect_url -> navigate frame) push and return, leaving session.view_instance set and the SSE session registered/active",
    "python/djust/sse.py:730 - DjustSSEStreamView.get always mounts through _sse_mount_view",
    "python/djust/sse.py:352-355 - _sse_handle_event dispatches whenever session.view_instance is set",
    "python/djust/sse.py:364-366 - only _validate_event_security runs (handler permission + object permission), never check_view_auth",
    "python/djust/sse.py:785-810 - DjustSSEEventView.post accepts {event, params} for any live session",
    "python/djust/runtime.py:336-341 - the newer ViewRuntime path DOES clear self.view_instance on an auth block, showing the correct model and the divergence from the legacy mirror",
    "docs/sse-transport.md:10-22 - presents SSE as the proxy-blocked fallback and /event/ as the legacy endpoint"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "python/djust/sse.py:245-246",
    "python/djust/sse.py:248-269"
   ],
   "reason_to_dismiss": "A defensive except Exception around an optional auth check reads as resilience, and no advisory mentions the error path.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "python/djust/sse.py:245-246 - except Exception: logger.warning('SSE: auth check error: %s', exc) with no return, so the flow falls through",
    "python/djust/sse.py:248-269 - mount kwargs are resolved and view_instance.mount() is called unconditionally afterwards",
    "python/djust/websocket.py:2215-2224 - the WebSocket counterpart routes an unexpected exception to handle_exception and returns (fail closed), so the two implementations disagree"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "python/djust/websocket.py:2722-2724",
    "python/djust/websocket_utils.py:200-291"
   ],
   "reason_to_dismiss": "docs/guides/authentication.md:197-206 states mount-time-only view-level auth as a conscious trade-off shared with Phoenix and Livewire, so a per-event re-check can be called a new feature rather than part of this fix.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "python/djust/websocket.py:2722-2724 - handle_event's only view-level gate is 'self.view_instance truthy'",
    "python/djust/websocket_utils.py:200-218 - per-event check is check_handler_permission (decorator metadata) only",
    "python/djust/websocket_utils.py:220-291 - per-event object check runs only for views that override get_object",
    "python/djust/auth/core.py:38-112 - check_view_auth (login_required / permission_required / check_permissions) is the view-level check and is never called from the event path",
    "docs/guides/authentication.md:197-206 - documents the gap as deliberate",
    "docs/website/guides/authorization.md:13 - claims the opposite ('runs your check at mount AND on every event handler dispatch'), a doc contradiction a solver would hit"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "python/djust/websocket.py:2005-2007",
    "python/djust/mixins/request.py:84-99"
   ],
   "reason_to_dismiss": "The hook redirect URL comes from developer code and is therefore trusted; same-origin validation is an HTTP-layer nicety, and this is an open-redirect concern (CWE-601), not the advisory's missing-auth concern.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "python/djust/hooks.py:79-87 - the redirect string is whatever the hook returns",
    "python/djust/websocket.py:2005-2007 - the WS path sends it to the client verbatim",
    "python/djust/mixins/request.py:84-99 - the HTTP path calls url_has_allowed_host_and_scheme and falls back to '/', with a comment naming open-redirect"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4",
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "The T1 fix cannot simply close: inside mount_batch (T3) the close is suppressed so sibling views survive, which leaves the batch-mounted denied view still installed on the consumer unless it is explicitly cleared; the suppression hides the residual exposure behind a passing batch response.",
   "In the SSE mount, T4 is reachable only because view_instance is assigned before the auth check (sse.py:229); fixing only the redirect branch still leaves the PermissionDenied branch (sse.py:238-240) and the fail-open exception path (sse.py:245-246) dispatching, so the sibling branches mask each other."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "The natural fix for T1/T2 - an unconditional await self.close(code=4403) in the redirect branch - kills a multiplexed mount_batch: _mount_one swaps only send_json (websocket.py:2524-2527), the batch response carrying navigate[] is sent after the loop (2671-2679), and the client turns batch navigate entries into a live_redirect on that same socket (03-websocket.js:529-539, pinned by test_wire_protocol_snapshots.py:249-262)."
  },
  {
   "a": "T1",
   "b": "T2",
   "what": "The same close applied on the handle_live_redirect_mount entry (websocket.py:4290-4291) terminates an already-open SPA session on a mid-session login redirect, so the fix must distinguish a first mount from a re-mount on an open socket instead of closing blindly."
  }
 ],
 "fairness_risks": [
  "A blanket 'any mount denial closes the socket' rule contradicts the mount_batch contract that a redirect must be reported in navigate[] while the socket keeps serving sibling views (websocket.py:2671-2679, test_wire_protocol_snapshots.py:249-262, 03-websocket.js:529-539).",
  "The WebSocket client has no 'navigate' case (03-websocket.js:303-975; only 03b-sse.js:270-273 handles it), so a rule that accepts 'send navigate and return' as the fix would keep the broken behaviour; the graded behaviour has to be socket termination or unmount, not the frame.",
  "A per-event view-level re-check (T6) contradicts the documented trade-off at docs/guides/authentication.md:197-206 and costs a query per interaction; if graded, a documented legitimate design is called a regression.",
  "Closing on a redirect during handle_live_redirect_mount refuses a shape a legitimate SPA navigation needs (a user whose login expired mid-navigation must be able to log in and return), so 'close on every redirect' is too broad.",
  "'Legacy' is not the same as unused for SSE: DjustSSEStreamView.get (?view=) is the mount the current SSE client still uses (03b-sse.js:51-59, sse.py:730), so a rule that simply disables that endpoint breaks the shipped fallback transport.",
  "If the per-event re-check is added, views whose handlers were written against mount-only auth (docs/guides/authentication.md:195-206) start erroring after logout; the refused shape (events after revocation) is exactly the shape the documented design permits."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4"
  ],
  "why": "T1/T2 give the report-described base (a redirect exit that leaves a live channel, on both the auth and the on_mount producer, plus the live_redirect_mount re-entry) and are cheap for both models. T3 is the MiMo-shaped trap: the obvious close breaks a pinned, client-consumed batch contract, so the solver must suppress the close in the batch path AND still clear the denied view from the single view_instance slot. T4 is the DeepSeek-shaped trap: a second, hand-written mount implementation in another module whose docstring claims the same security model, with a real reason to dismiss it as the degraded fallback transport. T5 rides along in T4's fix site. That is three independent groups with three different reasons to dismiss (batch contract, developer-hook semantics, legacy fallback transport), one deepseek-type and one mimo-type. T6 (per-event re-auth) would be a strong fourth group and the hardest deepseek-type, but only if graders accept it as in scope; T7 (hook-redirect host validation) is real and evidence-backed but a different protection class (CWE-601) and is left out of the design."
 },
 "unverified": [
  "The advisory text (GHSA-XX4J-W367-7247 / CVE-2026-55571 / PYSEC-2026-3829) is not in the worktree; the report wording used here comes from the screener record, not from a document I read.",
  "The published fix commit 1ae8aa92 is not present in this worktree (HEAD is the pinned pre-fix commit 3b369d0c), so which sites the fix touches could not be checked; that T4/T5 are uncovered by the fix rests on the screener's fix_sites list, not on a diff I read.",
  "Whether graders treat the missing per-event view-level re-check (T6) as in scope for this task is unknown; docs/website/guides/authorization.md:13 and docs/guides/authentication.md:197-206 contradict each other about whether per-event view auth is even intended.",
  "Whether graders treat the open-redirect divergence (T7) as in scope is unknown; it is a different protection (CWE-601) from the advisory's missing-auth family.",
  "No build or test run was performed (no shell available in this session), so every claim is source-reading only; the Rust/PyO3 extension and the pytest suite were not exercised.",
  "Repo size in MB could not be measured for the same reason."
 ]
}
  ```
- Published fix sites:   - python/djust/websocket.py:1795 — T1 M4 (reason to dismiss: The denial frame ({"type":"navigate"}) is sent and the handler returns, which reads as 'handled'; the wire-protocol snapshot pins the navigate frame as the correct auth-redirect response (python/djust/tests/test_wire_protocol_snapshots.py:525-528), so nothing at that site says the socket must also die.)
  - python/djust/websocket.py:1979-1986 — T1 M4 (reason to dismiss: The denial frame ({"type":"navigate"}) is sent and the handler returns, which reads as 'handled'; the wire-protocol snapshot pins the navigate frame as the correct auth-redirect response (python/djust/tests/test_wire_protocol_snapshots.py:525-528), so nothing at that site says the socket must also die.)
  - python/djust/websocket.py:2722-2724 — T1 M4 (reason to dismiss: The denial frame ({"type":"navigate"}) is sent and the handler returns, which reads as 'handled'; the wire-protocol snapshot pins the navigate frame as the correct auth-redirect response (python/djust/tests/test_wire_protocol_snapshots.py:525-528), so nothing at that site says the socket must also die.)
  - python/djust/websocket.py:2002-2007 — T2 M1 (reason to dismiss: A hook redirect is developer-defined control flow rather than an authentication denial, and a second redirect branch twenty lines below the first looks like the same code path already fixed.)
  - python/djust/websocket.py:4290-4291 — T2 M1 (reason to dismiss: A hook redirect is developer-defined control flow rather than an authentication denial, and a second redirect branch twenty lines below the first looks like the same code path already fixed.)
  - python/djust/hooks.py:71-88 — T2 M1 (reason to dismiss: A hook redirect is developer-defined control flow rather than an authentication denial, and a second redirect branch twenty lines below the first looks like the same code path already fixed.)
  - python/djust/websocket.py:2524-2537 — T3 M11 (reason to dismiss: Closing the socket is the obvious minimal fix, and mount_batch is 'just a lazy-hydration optimisation' that the report never mentions, so its contract is easy to overlook.)
  - python/djust/websocket.py:2571-2596 — T3 M11 (reason to dismiss: Closing the socket is the obvious minimal fix, and mount_batch is 'just a lazy-hydration optimisation' that the report never mentions, so its contract is easy to overlook.)
  - python/djust/websocket.py:2671-2679 — T3 M11 (reason to dismiss: Closing the socket is the obvious minimal fix, and mount_batch is 'just a lazy-hydration optimisation' that the report never mentions, so its contract is easy to overlook.)
- Uncovered routes to confirm (pattern B):   - python/djust/sse.py:229 — T4 M2 (reason to dismiss: SSE is the documented degraded fallback transport and /event/ is the documented legacy endpoint (docs/sse-transport.md:17,21-22); the advisory and its remediation speak only about WebSocket close codes, so the SSE mount can be argued out of scope.)
  - python/djust/sse.py:236-244 — T4 M2 (reason to dismiss: SSE is the documented degraded fallback transport and /event/ is the documented legacy endpoint (docs/sse-transport.md:17,21-22); the advisory and its remediation speak only about WebSocket close codes, so the SSE mount can be argued out of scope.)
  - python/djust/sse.py:785-810 — T4 M2 (reason to dismiss: SSE is the documented degraded fallback transport and /event/ is the documented legacy endpoint (docs/sse-transport.md:17,21-22); the advisory and its remediation speak only about WebSocket close codes, so the SSE mount can be argued out of scope.)
  - python/djust/sse.py:245-246 — T5 M4 (reason to dismiss: A defensive except Exception around an optional auth check reads as resilience, and no advisory mentions the error path.)
  - python/djust/sse.py:248-269 — T5 M4 (reason to dismiss: A defensive except Exception around an optional auth check reads as resilience, and no advisory mentions the error path.)
  - python/djust/websocket.py:2722-2724 — T6 M4 (reason to dismiss: docs/guides/authentication.md:197-206 states mount-time-only view-level auth as a conscious trade-off shared with Phoenix and Livewire, so a per-event re-check can be called a new feature rather than part of this fix.)
  - python/djust/websocket_utils.py:200-291 — T6 M4 (reason to dismiss: docs/guides/authentication.md:197-206 states mount-time-only view-level auth as a conscious trade-off shared with Phoenix and Livewire, so a per-event re-check can be called a new feature rather than part of this fix.)
  - python/djust/websocket.py:2005-2007 — T7 M2 (reason to dismiss: The hook redirect URL comes from developer code and is therefore trusted; same-origin validation is an HTTP-layer nicety, and this is an open-redirect concern (CWE-601), not the advisory's missing-auth concern.)
  - python/djust/mixins/request.py:84-99 — T7 M2 (reason to dismiss: The hook redirect URL comes from developer code and is therefore trusted; same-origin validation is an HTTP-layer nicety, and this is an open-redirect concern (CWE-601), not the advisory's missing-auth concern.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4. Why: T1/T2 give the report-described base (a redirect exit that leaves a live channel, on both the auth and the on_mount producer, plus the live_redirect_mount re-entry) and are cheap for both models. T3 is the MiMo-shaped trap: the obvious close breaks a pinned, client-consumed batch contract, so the solver must suppress the close in the batch path AND still clear the denied view from the single view_instance slot. T4 is the DeepSeek-shaped trap: a second, hand-written mount implementation in another module whose docstring claims the same security model, with a real reason to dismiss it as the degraded fallback transport. T5 rides along in T4's fix site. That is three independent groups with three different reasons to dismiss (batch contract, developer-hook semantics, legacy fallback transport), one deepseek-type and one mimo-type. T6 (per-event re-auth) would be a strong fourth group and the hardest deepseek-type, but only if graders accept it as in scope; T7 (hook-redirect host validation) is real and evidence-backed but a different protection class (CWE-601) and is left out of the design. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): A blanket 'any mount denial closes the socket' rule contradicts the mount_batch contract that a redirect must be reported in navigate[] while the socket keeps serving sibling views (websocket.py:2671-2679, test_wire_protocol_snapshots.py:249-262, 03-websocket.js:529-539). | The WebSocket client has no 'navigate' case (03-websocket.js:303-975; only 03b-sse.js:270-273 handles it), so a rule that accepts 'send navigate and return' as the fix would keep the broken behaviour; the graded behaviour has to be socket termination or unmount, not the frame. | A per-event view-level re-check (T6) contradicts the documented trade-off at docs/guides/authentication.md:197-206 and costs a query per interaction; if graded, a documented legitimate design is called a regression. | Closing on a redirect during handle_live_redirect_mount refuses a shape a legitimate SPA navigation needs (a user whose login expired mid-navigation must be able to log in and return), so 'close on every redirect' is too broad. | 'Legacy' is not the same as unused for SSE: DjustSSEStreamView.get (?view=) is the mount the current SSE client still uses (03b-sse.js:51-59, sse.py:730), so a rule that simply disables that endpoint breaks the shipped fallback transport. | If the per-event re-check is added, views whose handlers were written against mount-only auth (docs/guides/authentication.md:195-206) start erroring after logout; the refused shape (events after revocation) is exactly the shape the documented design permits.. Conflicts the reader found: The natural fix for T1/T2 - an unconditional await self.close(code=4403) in the redirect branch - kills a multiplexed mount_batch: _mount_one swaps only send_json (websocket.py:2524-2527), the batch response carrying navigate[] is sent after the loop (2671-2679), and the client turns batch navigate entries into a live_redirect on that same socket (03-websocket.js:529-539, pinned by test_wire_protocol_snapshots.py:249-262). | The same close applied on the handle_live_redirect_mount entry (websocket.py:4290-4291) terminates an already-open SPA session on a mid-session login redirect, so the fix must distinguish a first mount from a re-mount on an open socket instead of closing blindly.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-djust-6530/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-djust-6530/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-djust-6530/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-djust-6530/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-djust-6530/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-djust-6530/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-djust-6530/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-djust-6530 --only static
python3 -I common/gate/gate.py stk-djust-6530 --only nop
python3 -I common/gate/gate.py stk-djust-6530 --only oracle
python3 -I common/gate/gate.py stk-djust-6530 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-djust-6530/`;
  - edit only `tasks/stk-djust-6530/`, `build/stk-djust-6530/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-6530.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-djust-6530`. Control task slug: `stk-djust-6530-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-6530.json`.
