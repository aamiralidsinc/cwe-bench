# stk-avideo-ghsaghcv build notes

Start: 2026-10-23T06:13:04Z (this pass; two earlier passes on 2026-10-22/23 lost the task
directory and left the check patches, the recovered verifier suite and the scratch checkout).

Repo: WWBN/AVideo at 57f89ffbc27d37c9d9dd727212334846e78ac21a — the first parent of the earlier
advisory fix c08694bf6264 (GHSA-gph2-j4c9-vhhr); the later advisory fix is 9f3006f9a89a
(GHSA-ghcv-22jf-vfxm).

## Levers, one line each

- T1 (advisory route, C1): a browser frame carrying an executable value is relayed unchanged to
  another connection, and the recipient's page runs it (Message.php:228-244, script.js:567-568).
- T2 (uncovered upstream, C1): the default server class (loaded when pdo_sqlite exists) relays the
  same frames with no filtering at all — MessageSQLiteV2.php:282-297, 386-390.
- T3 (shape, C1): the value arrives in the message object, in the payload object beside the text,
  or at the top level; a strip of the usual sub-key leaves two carriers (Message.php:304-309,
  MessageSQLiteV2.php:386-393).
- T4 (coupled must-keep, C1): a server-issued frame keeps its executable value and its effect at
  the recipient (LiveLinks.php:407-412, YPTSocket.php:322-328), while a caller-written claim of
  being the server (frame fields, not the decrypted token) must not change how a frame is treated.
- T5 (uncovered upstream / how-type, C2): the recipient builds and runs a code string from the
  caller's function name; a plain-name check still accepts a built-in name, and a non-string value
  stringifies to one (script.js:91-95, Message.php:297-298, MessageSQLiteV2.php:380-381).
- T7 (published-fix far site, C3): the call notice picks which caller-written identity field to
  show from another caller-written identity field and inserts it as markup; the existing rewrite
  covers one field at the top level only (Message.php:230-235, caller.js:61-79/87-92).

Concepts: C1 = T1+T2+T3+T4 (executable payload relay and provenance), C2 = T5 (function-name
execution), C3 = T7 (authenticated call identity). DeepSeek-type: T2, T5. MiMo-type: T3, T4.

## Reference fix (solution/fix.patch)

Both server classes: trust only frames whose decrypted token was issued server-side; for every
other frame remove the executable field from every carrier, refuse a function name that is not a
plain string identifier, and overwrite the sender identity fields anywhere in the payload with
the token owner. Client script: resolve the named function by property lookup, refuse built-in
functions. Server-issued frames are untouched; the client-side application of the server UI
update remains (the live-link removal feature depends on it).

## Verified locally (verifier image from tests/Dockerfile, suites mounted read-only)

- Pinned: 24/24 security fail, 18/18 functional pass.
- Reference: 42/42 pass.
- Delivery-layer alternative (checks/pass-alt-delivery.patch): 42/42 pass.
- A lookup-only client fix (no built-in check) still executes through the timer: the built-in
  name lever is real, not just a pinned-code artefact.

Two harness defects inherited from the recovered snapshot were fixed:
- the schema module is loaded from a method, so the harness now publishes the variable its
  helpers read through `global` (otherwise every SQLite-implementation suite errored);
- the stand-in timer now reports itself the way a browser built-in does while still executing a
  string argument, so the "built-in function name" case measures the product, not the harness.

## Could not verify / outside scope

- The socket.io transport relays through an external binary from a separate repository
  (server.node.php:14-15); its server-side filtering cannot be inspected or fixed here — only the
  in-repo HTTP/WebSocket classes are covered.
- plugin/YPTSocket/MessageSQLite.php is not loaded by the socket host (server.php.php loads V2)
  and is excluded as a route.
- plugin/Live/getImage.php builds an executable value from request input but its send is
  commented out (getImage.php:202); excluded.
- No project test covers the socket area at the pinned commit, so no project test group runs.
- Real-browser rendering was not exercised: the product's client scripts run under Node with a
  DOM stand-in, and what the notice would receive is what the suites assert.

## Gate (builder/gate.py, stages in order)

- static: PASSED (strict: hardening + blind declared, catalogue complete).
- nop: PASSED — 24/24 security tests fail, 18/18 functional pass on the pinned tree.
- oracle: PASSED — three identical runs, reward 1.0, 42/42 each.
- patches: PASSED 15/15 — miss_executable_relay 12 sec/0 fun, miss_callback 6/0,
  miss_identity 6/0, miss_executable 6/0, sf-msg-carrier-only 4/0,
  sf-check-recipient-identity 4/0, sf-loose-callback-match 4/0, sf-fail-open-anonymous 2/0,
  ff-remove-client-eval 0/3, ff-strip-all-senders 0/4, ff-refuse-all 16/10,
  pass-hardening 1.0, pass-alt-delivery 1.0, upstream_fix (A+B) 6 security failing (fails, as
  required), upstream_first_fix (A alone) 10 security failing (fails, as required). The `blind`
  pass patch is written by the pipeline after the build (declared, not yet present).
- stacked conformance (stacking/check_stack.py): conforming, 3 concepts, pattern H3a.
- control stk-avideo-ghsaghcv-control: static PASSED; nop PASSED (6 security fail / 5 functional
  pass); oracle PASSED (3 identical runs, reward 1.0, 11/11); its patches stage PASSED 3/3 (control_malformed_identity 2 security failing / 0 functional,
  control_overbroad 0/2, control_pass_hardening 1.0).

## Audit fix 2026-10-24 (AUDIT-FIX-20261024.md)

The post-run audit attributed the failed deepseek-r1 trial to the caller harness, not the model
fix: `tests/support/caller_harness.js` stubbed `jq()` so `text()` and `html()` both returned the
stub object, which failed a correct fix that escapes the caller name on the client with the
standard jQuery idiom `$('<span>').text(name).html()`. Only that file changed:

- `.text(value)` stores the value as text and chains; `.text()` returns it;
- `.html()` returns the stored text HTML-escaped as a string (`&`, `<`, `>`, `"`, `'`);
- `.html(value)` stores markup and chains;
- the element's `textContent`/`innerHTML` expose the same content (so a DOM-property escape also
  yields a string);
- every other stub method is unchanged.

No test assertion, reference fix or instruction sentence changed. Direct probe of the shipped
harness: `$('<span>').text('Alice').html()` -> `"Alice"`; `$('<span>').text('<img src=x
onerror=...>').html()` -> the escaped string (contains no `<`); a plain string heading is
unchanged. Escape-only (server identity unfixed) still yields escaped markup containing the
literal `onerror`, so the leniency check that catches it is preserved.

Re-gate on the final tree: static PASSED; nop PASSED (24/24 security fail, 18/18 functional
pass); oracle PASSED (3 runs, reward 1.0, 42/42 each); patches PASSED (15/15 as declared).
FAIRNESS.md carries the per-concept S1-S7 stacking checks.

## End

End: 2026-10-23T08:41Z (build); 2026-10-24 (audit fix re-gate). Final state: tasks/stk-avideo-ghsaghcv and
tasks/stk-avideo-ghsaghcv-control built and gate-green; stacked conformance conforming
(3 concepts, H3a). The `blind` pass patch and FAIRNESS.md are written by the pipeline after
this build and are not part of it.
