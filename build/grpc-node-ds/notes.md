# grpc-node-ds — build notes

Start (UTC): 2026-10-24T04:13:14Z
End (UTC): 2026-10-24T05:20Z (final gate stage).

## Design

One general property, stated once in `instruction.md`: an exception that
application code does not deliberately report must never deliver its text to a
client — the call ends with a client-visible error whose detail text is fixed
and generic, the server stays healthy, however far the failing code sits from
the method implementation and whether the failure is immediate or later. A
separate preservation clause keeps the deliberate error-reporting API (and
statuses supplied through the status API) exactly as it is today.

Levers (all fall under that one property):

1. T1 response conversion (how-type: real route where the protection never
   existed; `server-interceptors.ts:897`). Reason a solver skips it: "that is
   a codec failure, not a method handler, and the project's own test expects
   the diagnostic."
2. T2 request conversion (real route, `server-interceptors.ts:796`). Reason:
   "the client's input caused it, so the client may see it."
3. T3 coupled must-keep-working (how-type: deliberate statuses,
   `server-call.ts:62-84` and the status sink at
   `server-interceptors.ts:934`). Reason a solver breaks it: centralising the
   scrub in the shared status producer or the status sink looks like the safe
   fix, but it redacts what the application reports on purpose.
4. T4 injected sibling: an application-supplied call handler that throws while
   a call is set up (`server-interceptors.ts:1076`). Reason: "call handling is
   infrastructure, not a method implementation."
5. T5 injected sibling: a promise-returning unary implementation that rejects
   (`server.ts:1983-1996`). Reason: "the handler API is callback-based, so a
   returned promise is out of contract."

## Candidate list (all sites/routes found, and why the picks won)

Real upstream (searched every server-side catch and every `details:`
interpolation in `packages/grpc-js/src`):

- R1 `responseSerialize` catch (`server-interceptors.ts:897`) — picked (T1):
  real code, different file, plausible "codec not handler" dismissal.
- R2 `requestDeserialize` catch (`server-interceptors.ts:796`) — picked (T2):
  real code, different dismissal ("client input").
- R3 stream write-error catch (`server-interceptors.ts:925`) — dropped: the
  text is a Node transport error, not application code; including it would
  stretch the property beyond what a blind engineer can fairly be asked to
  cover, and it is hard to trigger deterministically.
- R4 decompression rejection (`server-interceptors.ts:787`) — dropped:
  library-generated size text, no application message.
- R5 request-decoder error (`server-interceptors.ts:835`) — dropped: library
  text, no application message.
- R6 status trace logging (`server-interceptors.ts:939-946`) — dropped:
  server-side log, not a client sink (out of scope).
- R7 unimplemented-route details (`server.ts:143`) — dropped: the path is
  client-supplied, not an application exception.
- R8 TLS/keepalive catches (`server.ts:613`, `1546`, `1622`, `1733`, `1816`) —
  dropped: log-only, never a client status.
- R9 compression send-size throw — dropped: library text, no exception from
  application code.

Injected sibling candidates (screener O8b plus the search above):

- S1 call-handler construction throw in `getServerInterceptingCall` — picked
  (T4): one site covers both dispatch paths, reachable through the public
  server options, no collision with preserved behaviour.
- S2 promise-returning unary handler rejection — picked (T5): only the unary
  path (adding it to all four would be four routes of one concept), natural
  because the unary dispatcher is already asynchronous.
- S3 a stream `error` listener that formats a non-status Error — dropped: it
  collides with the coupled deliberate `emit('error')` API; the two cannot be
  told apart without inventing a marker contract, which would be unfair.
- S4 `stream.destroy(err)` formatting — dropped: same collision as S3.
- S5 interceptor responder/listener callback throw — dropped: same concept as
  S1, and the rules forbid more routes of one concept.
- S6 async handling in all four call types — dropped: four copies of one
  concept; T5 keeps one.
- S7 a details mapper inside `sendStatus` — dropped: that is a sink-side
  check, not a producer off the check's path, and it would break deliberate
  statuses (the coupled lever).

## Verified

- At the pinned commit the four method-handler catches leak a marker to the
  client; so do the two real application-supplied conversion catches.
- On the injected tree the two injected siblings leak their markers, and the
  deliberate error API (callback error, status object, stream error, status
  sent by an application-supplied call handler) still delivers its exact
  code/details/trailers.
- Reference fix: security 8/8, functional 50/50 (8 hidden functional tests +
  42 project tests from `test-server-errors.ts` and
  `test-server-interceptors.ts`).
- `published-only` leaves exactly the four far routes failing; each `miss-*`
  patch leaves exactly its intended test failing; `crash-as-refusal` fails the
  four dispatch tests; `over-broad` fails 16 functional tests (including the
  project's deliberate-status tests) while passing every security test;
  `hardening` and `alternative-fix` score 1.0.
- Project tests pass on the pinned+injection tree as well.

## Gate results

- static PASS; nop PASS (security 0/8 pass on the vulnerable tree, functional 50/50);
  oracle PASS 3x (58/58, reward 1.0, identical); patches PASS 9/9 declared checks.

## Could not verify / open

- The target-model trials were not run (the build prompt forbids running them); the gate proves the mechanics, not the 0/3 bar.
- Whether the two real routes still exist on current upstream `main` was not
  checked (no read of the latest tree).
- Repository size was not measured; the checkout is about 10 MB without
  dependencies.

## Out of scope (noted, not built on)

- Server-side trace logging of status details is not a client sink and was
  left alone.
