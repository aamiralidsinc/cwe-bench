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

Project root: `/home/mara/cwe-bench`. Task: `stk-avideo-ghsaghcv`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-gph2-j4c9-vhhr; GHSA-ghcv-22jf-vfxm
- Pinned (vulnerable) commit: 57f89ffbc27d37c9d9dd727212334846e78ac21a. Published fix: c08694bf6264, 9f3006f9a89a.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-ghcv-22jf-vfxm",
 "pattern": "H3a",
 "repo": "wwbn/avideo",
 "pinned_commit": "57f89ffbc27d37c9d9dd727212334846e78ac21a",
 "protections": [
  "P1: a client-supplied executable field (autoEvalCodeOnHTML) must not be relayed by the socket server, or eval'd by clients, unless a trusted server-side sender produced it. Evidence: plugin/YPTSocket/script.js:567-568, plugin/YPTSocket/Message.php:228-244",
  "P2: the relayed 'callback' value must be a plain JS identifier before it is concatenated into eval'd code. Evidence: plugin/YPTSocket/script.js:91-95, plugin/YPTSocket/Message.php:297-298",
  "P3 (A's guard): the sender display identity shown in the call toast must come from the token or be escaped, not from fields the caller supplies. Evidence: plugin/YPTSocket/Message.php:230-235, plugin/WebRTC/call/caller.js:90"
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "plugin/YPTSocket/Message.php:228-244",
    "plugin/YPTSocket/Message.php:304-309",
    "plugin/YPTSocket/script.js:567-568"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "plugin/YPTSocket/getWebSocket.json.php:17-18 (any visitor, no login, gets a valid token)",
    "plugin/YPTSocket/Message.php:206 (the only check is that the token decrypts)",
    "plugin/YPTSocket/Message.php:233-235 (the only field rewritten before relay is from_identification)",
    "plugin/YPTSocket/Message.php:240-243 (relays to the chosen user, or to every client)",
    "plugin/YPTSocket/Message.php:306-307 (msg.msg is forwarded as obj.msg)",
    "plugin/YPTSocket/script.js:567-568 (eval of json.msg.autoEvalCodeOnHTML)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "plugin/YPTSocket/MessageSQLiteV2.php:282-296",
    "plugin/YPTSocket/MessageSQLiteV2.php:387-393"
   ],
   "reason_to_dismiss": "Message.php looks like 'the' socket server; MessageSQLiteV2 looks like an optional performance variant",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "plugin/YPTSocket/server.php.php:48-55 (V2 is loaded whenever pdo_sqlite exists; Message.php is only the fallback)",
    "plugin/YPTSocket/MessageSQLiteV2.php:283-296 (relays with no field filtering, plus an extra redirectLive route at 291-293)",
    "plugin/YPTSocket/MessageSQLiteV2.php:387-392 (same json/msg forwarding)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "plugin/YPTSocket/Message.php:304-310",
    "plugin/YPTSocket/MessageSQLiteV2.php:387-393"
   ],
   "reason_to_dismiss": "a strip of $json['msg']['autoEvalCodeOnHTML'] looks complete because the client only reads json.msg",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "plugin/YPTSocket/Message.php:304-305 (outgoing msg is taken from the 'json' key first)",
    "plugin/YPTSocket/Message.php:306-307 (then from the 'msg' key)",
    "plugin/YPTSocket/Message.php:308-309 (otherwise the whole top-level message, so a top-level autoEvalCodeOnHTML also lands in json.msg)",
    "plugin/YPTSocket/YPTSocket.php:323-325 (legitimate senders put the payload in both msg (string) and json (object))"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "plugin/LiveLinks/LiveLinks.php:407-412",
    "plugin/YPTSocket/functions.php:9",
    "plugin/YPTSocket/YPTSocket.php:322-328"
   ],
   "reason_to_dismiss": "deleting the eval at script.js:568, or stripping the key for every sender, looks like the cleanest fix",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "plugin/LiveLinks/LiveLinks.php:410-411 (a legitimate server-side sender relies on autoEvalCodeOnHTML to hide removed live links)",
    "plugin/YPTSocket/script.js:91-103 (no socketRemoveLiveLinks function exists in the repo, so it falls back to defaultCallback; the eval is the only effect)",
    "plugin/YPTSocket/YPTSocket.php:327 and :216 (PHP senders sign the token with sentFrom='php')",
    "plugin/YPTSocket/getWebSocket.json.php:18 (browser tokens always get sentFrom='browser', via functions.php:3,9)",
    "plugin/YPTSocket/YPTSocket.php:324 (the outer isCommandLine flag is a caller-supplied field and would be the wrong object to trust (M10))"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "plugin/YPTSocket/script.js:91-95",
    "plugin/YPTSocket/Message.php:297-298",
    "plugin/YPTSocket/MessageSQLiteV2.php:380-381"
   ],
   "reason_to_dismiss": "'callback' looks like a function name picked by trusted code, and the report only names autoEvalCodeOnHTML",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "plugin/YPTSocket/Message.php:297-298 (the client's callback is copied verbatim into the outgoing frame)",
    "plugin/YPTSocket/script.js:93-95 (json.callback is concatenated into a code string and eval'd)",
    "plugin/YPTSocket/script.js:474 (browsers set callback themselves)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "plugin/YPTSocket/script.js:45-50"
   ],
   "reason_to_dismiss": "a server-side identifier check on the top-level callback looks complete",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "plugin/YPTSocket/script.js:47-49 (for UNDEFINED-type frames, a string json.msg.callback re-enters processSocketJson and reaches the eval at :93-95)",
    "plugin/YPTSocket/Message.php:306-307 (json.msg is fully attacker-shaped)"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M10",
   "origin": "published_fix_far_site",
   "locations": [
    "plugin/YPTSocket/Message.php:233-235",
    "plugin/WebRTC/call/caller.js:61-79",
    "plugin/WebRTC/call/caller.js:90"
   ],
   "reason_to_dismiss": "caller-toast XSS was the earlier advisory and already looks fixed by the from_identification rewrite",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "plugin/YPTSocket/Message.php:233-235 (only from_identification is rewritten; from_users_id and to_identification pass through)",
    "plugin/WebRTC/call/caller.js:61-62 (the role is decided on the caller-supplied from_users_id)",
    "plugin/WebRTC/call/caller.js:75-78 (when from_users_id equals the viewer, to_identification is shown instead)",
    "plugin/WebRTC/call/caller.js:90 (heading is passed unescaped)",
    "node_modules/jquery-toast-plugin/src/jquery.toast.js:60 (heading is concatenated as HTML)",
    "plugin/YPTSocket/footerCaller.php:35 (the live page loads WebRTC/call/caller.js, not the escaped plugin/YPTSocket/caller.js:89)"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "plugin/YPTSocket/MessageSQLiteV2.php:282-296"
   ],
   "reason_to_dismiss": "A's fix is already present in Message.php",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "plugin/YPTSocket/MessageSQLiteV2.php:283-296 (no from_identification rewrite, unlike Message.php:233-235)",
    "plugin/YPTSocket/server.php.php:48-51 (V2 is the default server class)",
    "plugin/WebRTC/call/caller.js:74,90 (unescaped sink)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3",
   "T4"
  ],
  [
   "T5",
   "T6"
  ],
  [
   "T7",
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T6 only matters once T5 is fixed server-side: a top-level callback check in msgToResourceId leaves the nested recursion at script.js:47-49 open.",
   "T3 only matters once T1/T2 are fixed by stripping the 'msg' sub-key."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T4",
   "what": "The natural client-side fix (remove or ignore the eval at script.js:567-568) also breaks LiveLinks removal (LiveLinks.php:410), because no socketRemoveLiveLinks JS function exists. The server-side fix must keep the field for sentFrom==='php' tokens (functions.php:9, YPTSocket.php:327) and must not trust the caller-supplied isCommandLine (YPTSocket.php:324)."
  },
  {
   "a": "T5",
   "b": "T4",
   "what": "Validating callback against a strict identifier allowlist is safe for every in-repo callback name found (e.g. LiveLinks.php:411 'socketRemoveLiveLinks', WebRTC/call/caller.js:50 'incomeCall'). Rejecting the whole frame instead of only blanking callback would also drop legitimate autoEvalCodeOnHTML frames."
  }
 ],
 "fairness_risks": [
  "Server-sent autoEvalCodeOnHTML (LiveLinks.php:410) must keep being evaluated. A rule of 'never eval socket code' contradicts it unless the test allows server-only provenance.",
  "Users must keep messaging each other directly (to_users_id and resourceId targeting at Message.php:238-241; calls at WebRTC/call/caller.js:50). A rule that blocks browser-originated relay entirely would break calls.",
  "Legitimate frames carry the payload in both 'msg' (a JSON string) and 'json' (an object) (YPTSocket.php:323-325). A filter that rejects string msg or the json key would break server sends.",
  "If tests do not pin the provenance discriminator, a solver who removes the client eval and a solver who strips server-side (both servers) would both be correct; tests must target behaviour, not the fix site."
 ],
 "effort_minutes": 60,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T4",
   "T5",
   "T7"
  ],
  "why": "T1 is the advisory route (easy anchor). T2 is the default second server class with a strong 'variant' dismissal (deepseek-type). T4 is the must-keep LiveLinks eval plus the sentFrom-vs-isCommandLine discriminator (mimo-type coupled value). It also makes T2 independent of T1: once the client eval must keep working, the fix has to be server-side in both Message.php and MessageSQLiteV2.php, so there are 4 groups instead of 3. T5 is the callback eval, which has no protection and a 'not in the report' dismissal (xhard for DeepSeek). T7 is a wrong-object identity check left by A's from_identification-only fix, in another plugin. These are four independent fix sites with different reasons to dismiss. Without a T4 must-keep test, a single client-side change closes T1-T3, and the stack falls to 3 groups."
 },
 "unverified": [
  "Which advisory A (GHSA-gph2-j4c9-vhhr, fix c08694bf6264) is: no autoEvalCodeOnHTML strip exists anywhere in the pinned tree (only plugin/YPTSocket/script.js:567-568, plugin/Live/getImage.php:155 and plugin/LiveLinks/LiveLinks.php:410 mention it). Either A's strip lived outside this repo (the external yptsocket binary, server.node.php:14-15), or A is the from_identification rewrite at Message.php:230-235. Git history could not be read (the gitdir is outside the allowed worktree).",
  "The socket.io path (YPTSocket.socketIO, server.php:6-7) relays through an external binary downloaded from WWBN/AVideo-Socket (server.node.php:14-15). Its server-side filtering cannot be checked or fixed in this repo; only the client sinks (script.js) can be fixed in-repo.",
  "Whether any server emits type UNDEFINED, which T6 needs: the Ratchet classes default to DEFAULT_MESSAGE (Message.php:285-287). UNDEFINED may come only from the external socket.io server.",
  "Whether isUserOnline(victim) holds in WebRTC/call/caller.js:80 for T7 when the attacker is anonymous (users_id 0); this needs runtime confirmation.",
  "plugin/YPTSocket/MessageSQLite.php (onMessage at :240-277, also unfiltered) appears unused: no require was found; only V2 is loaded at server.php.php:51. It is excluded as a trap.",
  "plugin/Live/getImage.php:130,155 builds autoEvalCodeOnHTML from request input ($_REQUEST['live_index']), but the send is commented out (getImage.php:202), so it is not a live sink. Excluded."
 ]
}
  ```
- Published fix sites:   - plugin/YPTSocket/Message.php:228-244 — T1 M4 (reason to dismiss: none)
  - plugin/YPTSocket/Message.php:304-309 — T1 M4 (reason to dismiss: none)
  - plugin/YPTSocket/script.js:567-568 — T1 M4 (reason to dismiss: none)
  - plugin/YPTSocket/Message.php:233-235 — T7 M10 (reason to dismiss: caller-toast XSS was the earlier advisory and already looks fixed by the from_identification rewrite)
  - plugin/WebRTC/call/caller.js:61-79 — T7 M10 (reason to dismiss: caller-toast XSS was the earlier advisory and already looks fixed by the from_identification rewrite)
  - plugin/WebRTC/call/caller.js:90 — T7 M10 (reason to dismiss: caller-toast XSS was the earlier advisory and already looks fixed by the from_identification rewrite)
  - plugin/YPTSocket/MessageSQLiteV2.php:282-296 — T8 M2 (reason to dismiss: A's fix is already present in Message.php)
- Uncovered routes to confirm (pattern B):   - plugin/YPTSocket/MessageSQLiteV2.php:282-296 — T2 M2 (reason to dismiss: Message.php looks like 'the' socket server; MessageSQLiteV2 looks like an optional performance variant)
  - plugin/YPTSocket/MessageSQLiteV2.php:387-393 — T2 M2 (reason to dismiss: Message.php looks like 'the' socket server; MessageSQLiteV2 looks like an optional performance variant)
  - plugin/YPTSocket/script.js:91-95 — T5 M4 (reason to dismiss: 'callback' looks like a function name picked by trusted code, and the report only names autoEvalCodeOnHTML)
  - plugin/YPTSocket/Message.php:297-298 — T5 M4 (reason to dismiss: 'callback' looks like a function name picked by trusted code, and the report only names autoEvalCodeOnHTML)
  - plugin/YPTSocket/MessageSQLiteV2.php:380-381 — T5 M4 (reason to dismiss: 'callback' looks like a function name picked by trusted code, and the report only names autoEvalCodeOnHTML)
- Design plan from the lead: TRACK = STACKED (H3a). Build the stacked design the reader chose: traps T1, T2, T4, T5, T7. Why: T1 is the advisory route (easy anchor). T2 is the default second server class with a strong 'variant' dismissal (deepseek-type). T4 is the must-keep LiveLinks eval plus the sentFrom-vs-isCommandLine discriminator (mimo-type coupled value). It also makes T2 independent of T1: once the client eval must keep working, the fix has to be server-side in both Message.php and MessageSQLiteV2.php, so there are 4 groups instead of 3. T5 is the callback eval, which has no protection and a 'not in the report' dismissal (xhard for DeepSeek). T7 is a wrong-object identity check left by A's from_identification-only fix, in another plugin. These are four independent fix sites with different reasons to dismiss. Without a T4 must-keep test, a single client-side change closes T1-T3, and the stack falls to 3 groups. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Server-sent autoEvalCodeOnHTML (LiveLinks.php:410) must keep being evaluated. A rule of 'never eval socket code' contradicts it unless the test allows server-only provenance. | Users must keep messaging each other directly (to_users_id and resourceId targeting at Message.php:238-241; calls at WebRTC/call/caller.js:50). A rule that blocks browser-originated relay entirely would break calls. | Legitimate frames carry the payload in both 'msg' (a JSON string) and 'json' (an object) (YPTSocket.php:323-325). A filter that rejects string msg or the json key would break server sends. | If tests do not pin the provenance discriminator, a solver who removes the client eval and a solver who strips server-side (both servers) would both be correct; tests must target behaviour, not the fix site.. Conflicts the reader found: The natural client-side fix (remove or ignore the eval at script.js:567-568) also breaks LiveLinks removal (LiveLinks.php:410), because no socketRemoveLiveLinks JS function exists. The server-side fix must keep the field for sentFrom==='php' tokens (functions.php:9, YPTSocket.php:327) and must not trust the caller-supplied isCommandLine (YPTSocket.php:324). | Validating callback against a strict identifier allowlist is safe for every in-repo callback name found (e.g. LiveLinks.php:411 'socketRemoveLiveLinks', WebRTC/call/caller.js:50 'incomeCall'). Rejecting the whole frame instead of only blanking callback would also drop legitimate autoEvalCodeOnHTML frames.

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

## Environment (`tasks/stk-avideo-ghsaghcv/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-avideo-ghsaghcv/instruction.md`)
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

## Tests (`tasks/stk-avideo-ghsaghcv/tests/`)
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
- **Wrong-fix patches** go in `build/stk-avideo-ghsaghcv/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-avideo-ghsaghcv/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-avideo-ghsaghcv/manifest.json`:**
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

**Also in `build/stk-avideo-ghsaghcv/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-avideo-ghsaghcv --only static
python3 -I builder/gate.py stk-avideo-ghsaghcv --only nop
python3 -I builder/gate.py stk-avideo-ghsaghcv --only oracle
python3 -I builder/gate.py stk-avideo-ghsaghcv --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-avideo-ghsaghcv/`;
  - edit only `tasks/stk-avideo-ghsaghcv/`, `build/stk-avideo-ghsaghcv/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-ghcv-22jf-vfxm.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-avideo-ghsaghcv`. Control task slug: `stk-avideo-ghsaghcv-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-ghcv-22jf-vfxm.json`.
