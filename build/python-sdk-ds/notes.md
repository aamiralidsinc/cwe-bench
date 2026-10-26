# python-sdk-ds — build notes

Slug: `python-sdk-ds` · repo: modelcontextprotocol/python-sdk · pattern A+B · track injected
Pinned (vulnerable): ce267b6fc515dc4efc1dc70b6975b16ff0feef0a
Published fix: 62137874ff26dd74d2fea80ff528a7fd9ca7a5e7
Start: 2026-10-24T02:44:37Z · End: 2026-10-24T03:45Z

## What the product is

The MCP Python SDK. A server built on it can run a tool call as a *task*: the client gets a task
id back immediately and later reads the task's status (`tasks/get`), its payload (`tasks/result`),
enumerates tasks (`tasks/list`) or cancels one (`tasks/cancel`). One `Server` process serves many
client sessions against one `TaskStore`; task ids are bare `uuid4`s with no creator identity, and
the four default handlers enabled by `server.experimental.enable_tasks()` resolve a task by id
alone. Any session that learns another session's task id can read its status and payload, list it,
cancel it.

Confirmed behaviourally on the pinned tree (work/python-sdk-ds/repro.py, real `ClientSession` over
in-memory streams, two sessions): session B reads session A's task status (`completed`), its
payload (`secret:ada`), sees it in `tasks/list`, and cancels A's running task.

## The property (written once, in the instruction)

A client session may use only the tasks its own session created. No message a session receives —
request response or notification — may reveal the existence, identifier, status, messages or
result of a task created by another session, and no request may change, complete or remove such a
task. Tasks the application creates without associating them with a session (an identifier the
application chose itself, or a deployment where a session does not survive to the next request)
stay usable by anyone presenting the exact identifier and are never enumerated.

## Levers

Main lever is HOW-type (the mechanism has to be understood; finding the site is not enough):

- **T1 (how-type — coupled must-keep-working value + fail-open shape).** Creator identity does
  not exist anywhere at the pinned commit: it has to be produced when the task is created (or
  recorded on a side table at creation) and travel with the task; the check in the handlers never
  calls the producer. The natural strict fix — bind every task to the session that created it —
  breaks the two coupled values: a task the application created with an identifier it chose
  itself must stay reachable by that identifier from any session and must never be listed, and a
  deployment where each request runs as a fresh session must still serve a task created by an
  earlier request. The same code path also tempts a fail-open: "the requestor has no session
  identity, so allow" makes a session with no identity a superuser over every scoped task.
  Sites: task creation in `src/mcp/server/experimental/request_context.py:213`,
  per-session setup in `src/mcp/server/experimental/task_support.py:86-99` and
  `src/mcp/server/lowlevel/server.py:670` (stateless flag), per-session state in
  `src/mcp/server/experimental/session_features.py:41`; the check lands in
  `src/mcp/server/lowlevel/experimental.py:128-186`.
  Reason a solver dismisses it: "the handlers are the vulnerability; creation and transport setup
  are not, and binding every task to its creating session is the strictest fix."
- **T2 (how-type — a shape a plausible check mishandles: the listing cursor).** `tasks/list` is
  paginated over the shared store and the next cursor *is a raw task id belonging to whichever
  task happens to fall on the page boundary* (`src/mcp/shared/experimental/tasks/in_memory_task_store.py:180-184`).
  A fix that filters the page's task objects but forwards the store's `nextCursor` still hands the
  caller another session's task id, and a fix that filters after slicing can also silently drop
  the caller's own tasks. In `src/mcp/server/lowlevel/experimental.py:172-175`.
  Reason a solver dismisses it: "once the returned task objects are filtered, the listing is
  closed" — the cursor is not an object in the list.
- **T3 (route where the protection never existed — injected).** A `tasks/delete` default handler
  (new module `src/mcp/server/experimental/task_housekeeping.py`, registered from `enable_tasks()`)
  destroys a task by id, over the store's unused `delete_task`. Nothing in the published fix or
  the report mentions removal.
  Reason a solver dismisses it: "housekeeping/cleanup, not task access."
- **T4 (route where the protection never existed — injected, push channel).** A `tasks/watch`
  default handler (new module `src/mcp/server/experimental/task_watch.py`, registered from
  `enable_tasks()`) subscribes the calling session to a task's status notifications; the
  fan-out hook lives in `ServerTaskContext._send_notification`
  (`src/mcp/server/experimental/task_context.py`), which the published fix never touches.
  Reason a solver dismisses it: "notifications are server-push plumbing, not an authorization
  surface", and it is a different direction of traffic from the four request handlers.
- Coupled must-keep-working behaviours tested functionally next to every lever: own-task
  get/result/list/cancel/delete/watch; listing across more than one store page; explicit-id tasks
  reachable by id from any session and never listed; tasks created on a session with no identity
  reachable by id from another session.

## Sites and routes the security tests cover

Published (all four default handlers, one test each): `tasks/get`, `tasks/result`,
`tasks/list`, `tasks/cancel` — foreign session refused, no side effect, session still usable.
Published producer/coupled: a session with no identity must not be a superuser; the listing
cursor must not identify a foreign task even when the creator has more than one page.
Injected: `tasks/delete`, `tasks/watch`.
Input shapes: SDK-minted ids; an application-chosen id (`the-nightly-export`); ids created
directly in the store; a session with no identity (stateless); a listing that spans store pages.

## Candidate sibling sites and routes (everything found), and why the two picks won

1. `TaskResultHandler.handle()` (`task_result_handler.py:85-139`) — public lower-level API serving
   any task's queued messages and result to the calling session; the published fix adds only a
   docstring (custom handlers are the server author's job). **Rejected**: reachable only from a
   custom handler the test would have to write, so the product has no real entry point.
2. Response router `route_response`/`route_error` (`task_result_handler.py:201-235`) registered on
   every session (`session.py` `add_response_router`) — no session check; a response from another
   session can complete a task's queued input. **Rejected**: request ids embed `id(params)`, so a
   test could only pass by guessing a memory address; not fairly testable.
3. `cancel_task(store, task_id)` helper (`shared/experimental/tasks/helpers.py:53-102`) — no
   requestor scoping. **Rejected as a site**: no client-facing call site of its own (the default
   handler that calls it is already the published site); a new call site would be a plant with no
   product wiring. Used instead as a place the hardening patch proves harmless.
4. `ServerTaskContext` store lookups (`task_context.py`) — server-side work code, no client input.
   **Rejected**.
5. Store primitives `InMemoryTaskStore.list_tasks/delete_task` — no session context; only reachable
   through handlers. **Chosen as the substrate for T3**: a new default handler over the unused
   `delete_task` is exactly what a maintainer would add, and it is a client-facing destructive
   route.
6. Task status notification fan-out, `ServerTaskContext._send_notification`
   (`task_context.py:228-253`) — creator-only today. **Chosen as the substrate for T4**: a
   watch/subscribe route plus fan-out is the natural way a maintainer would let a UI follow a task
   without long-polling, and the fan-out hook is in a file the published fix never touches.
7. Client-side task handlers (`client/experimental/task_handlers.py`) — a client serves one peer
   server; not multi-tenant. **Rejected** (out of scope).
8. `ExperimentalServerSessionFeatures` (`session_features.py`) — server→client direction; the
   remote client is the tenant there. **Rejected** (out of scope).

Picks: 5 (delete) and 6 (watch) — both reachable through the real client entry point, both
covered by the one property, neither named in the report, both in code the published fix does not
touch. They beat 1–2 because those cannot be driven through a product entry point without the test
inventing the caller; they beat 3–4 because those have no client-facing route at all; 5 and 6 each
add a different operation class (destructive maintenance vs. a push channel) rather than a second
copy of "read a task".

## Injected code (see environment/injection.patch)

- `src/mcp/types.py`: `DeleteTaskRequest/Result`, `WatchTaskRequest/Result` (+ the client request
  union).
- `src/mcp/server/experimental/task_housekeeping.py` (new): default `tasks/delete` handler.
- `src/mcp/server/experimental/task_watch.py` (new): default `tasks/watch` handler + watcher
  registry + fan-out helper.
- `src/mcp/server/experimental/task_context.py`: `_send_notification` also publishes to watchers.
- `src/mcp/server/lowlevel/experimental.py`: `enable_tasks()` registers both new handler sets
  (the published fix's hunks start at `_register_default_task_handlers`, so they never touch this).

## Verification plan / record

Reproduced on the pinned tree with real clients (work/python-sdk-ds/repro.py, repro2.py): a second
session reads the first session's task status, its payload, sees it in `tasks/list`, cancels it,
follows its status notifications and deletes it.

Local runs of the hidden suites (venv + editable source, branch per variant):

| tree | security | functional (hidden 9 + project 135) |
|---|---|---|
| pinned + injection (`inj`) | 0 / 11 | 144 / 144 |
| oracle (`fix`) | 11 / 11 | 144 / 144 |
| alternative design (`pass-alt`) | 11 / 11 | 144 / 144 |
| hardening (`pass-hardening`) | 11 / 11 | 144 / 144 |
| published fix only | 9 / 11 (delete, watch fail) | 144 / 144 |
| get only | 2 / 11 | 144 / 144 |
| reads only | 7 / 11 | 144 / 144 |
| cursor forwarded | 10 / 11 | 144 / 144 |
| no delete scope | 10 / 11 | 144 / 144 |
| no watch scope | 10 / 11 | 144 / 144 |
| stateless superuser | 9 / 11 | 144 / 144 |
| crash as refusal | 3 / 11 | 144 / 144 |
| session-bound over-broad | 10 / 11 | 142 / 144 |
| explicit id rejected | 10 / 11 | 143 / 144 |
| refuse all | 2 / 11 | 131 / 144 |

Project tests run (copied into tests/project/): the pinned tree's `tests/experimental/tasks` area
minus `server/test_server.py`, which asserts the vulnerable listing behaviour and is changed by the
published fix. 135 passed; the pinned tree's test_spec_compliance.py is left out (93 TODO-marked skips).

Gate stages (run 2026-10-24):
- static: fails only on the missing `kind=blind` pass patch (written after this build by the separate
  blind-fix step); conformance, leak, exact-status and catalogue checks are green.
- nop: PASSED (security 0/11, functional 144/144).
- oracle: PASSED — 3 runs, each reward 1.0 (11/11 security + 144/144 functional) and identical.
- patches: PASSED 13/13 as declared — sf-published-only 2 security failures / 0 functional; sf-get-only
  9/0; sf-reads-only 4/0; sf-cursor-forwarded 1/0; sf-no-delete 1/0; sf-no-watch 1/0;
  sf-stateless-superuser 2/0; sf-crash-refusal 8/0; ff-session-bound 0.0 with 2 functional failures;
  ff-explicit-id-rejected 0.0 with 1; ff-refuse-all 0.0 with 13; pass-hardening 1.0; pass-alt 1.0.

## What I could not verify

- Whether either target model fails: no trials were run (the brief forbids running them).
- `present_in_latest` of the three real O8 routes: only the pinned commit and the published fix
  were fetched; no current upstream tree was read.
- The published fix's behaviour under a *different* store implementation than the bundled one is
  covered by the application-store test only as an `InMemoryTaskStore` subclass; a genuinely
  remote store was not available offline.
- Whether `uv-dynamic-versioning` would accept the source tree without git history: avoided
  entirely by shipping only the distribution record that `mcp.__version__` reads.

## Fairness self-check

- Every requirement the tests enforce is either in `instruction.md` (property, refusal form,
  preservation of application-chosen identifiers and of deployments without a surviving session,
  listing completeness) or standard expert knowledge (a session may not read another's data).
- The instruction names no file, function, route added by the task, or mechanism, and states the
  property once; the injected routes fall under it as written.
- The two preservation clauses have to be explicit, which makes the "identity at creation" lever
  findable; the difficulty that remains is breadth (every route over the same store, including
  the pagination state and the push channel) and the fail-open shape.

## Scope notes

- Outside this advisory's protection and not used: the client-side task handlers (single peer),
  the server→client session features, and the public `TaskResultHandler.handle()` /
  `cancel_task()` helpers, which have no client-facing route of their own at the pinned commit.
