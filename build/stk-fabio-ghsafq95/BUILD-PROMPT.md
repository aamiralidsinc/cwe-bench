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

Project root: `/home/mara/cwe-bench`. Task: `stk-fabio-ghsafq95`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-q7p4-7xjv-j3wf; GHSA-fq95-v8xc-jm3v
- Pinned (vulnerable) commit: 66acfbb02a64485b1471005df175c8408c5025cb. Published fix: fdaf1e966162, 240526a80040.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-fq95-v8xc-jm3v",
 "pattern": "H3b",
 "repo": "fabiolb/fabio",
 "pinned_commit": "66acfbb02a64485b1471005df175c8408c5025cb",
 "protections": [
  "P1: headers that fabio sets for the backend (fixed X-Real-Ip/Forwarded/X-Forwarded-* set plus the operator-named clientip, tls and requestid headers) must not be removable by a client that lists their names as Connection hop-by-hop tokens. httputil.ReverseProxy strips those tokens after fabio has set the headers.",
  "P2: a header that the operator designates as a trust header (proxy.header.clientip) must always carry the value fabio derived and never a client-supplied value.",
  "P3: on every proxy protocol path that fabio serves, operator-designated trust headers reaching the backend must come from fabio and not from the client."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "proxy/http_headers.go:51",
    "proxy/http_headers.go:81",
    "proxy/http_headers.go:92",
    "proxy/http_headers.go:96",
    "proxy/http_headers.go:100",
    "proxy/http_headers.go:124",
    "proxy/http_handler.go:18"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "proxy/http_headers.go:36 addHeaders sets the fabio headers on the inbound request",
    "proxy/http_proxy.go:182 addHeaders runs before the handler is built",
    "proxy/http_handler.go:18 the request is forwarded through a stock httputil.ReverseProxy with no Connection-token sanitising in the Director (http_handler.go:23-32)",
    "No Go file in the repo references \"Connection\" or hop-by-hop handling (repo-wide grep), so the A fix is not present at the pinned commit"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M5",
   "origin": "published_fix_far_site",
   "locations": [
    "proxy/http_headers.go:48",
    "proxy/http_headers.go:128",
    "config/load.go:149",
    "config/load.go:150"
   ],
   "reason_to_dismiss": "The header names come from operator config and are not fixed constants, so a fix that hard-codes a list of the well-known X-Forwarded-*/Forwarded/X-Real-Ip names looks complete",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "proxy/http_headers.go:45-49 sets cfg.ClientIPHeader with a runtime name",
    "proxy/http_headers.go:126-131 sets or deletes cfg.TLSHeader with a runtime name",
    "config/load.go:149-151 the names come from the proxy.header.clientip and proxy.header.tls flags"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "locations": [
    "proxy/http_proxy.go:88",
    "proxy/http_proxy.go:93",
    "config/load.go:152"
   ],
   "reason_to_dismiss": "A request id is a correlation value and not a security or trust header, and it is set in ServeHTTP outside addHeaders, so a solver who reviews only addHeaders never sees it",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "proxy/http_proxy.go:88-94 sets r.Header[p.Config.RequestID] in ServeHTTP, separately from addHeaders (proxy/http_headers.go:36)",
    "config/load.go:152 proxy.header.requestid"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "proxy/http_headers.go:45",
    "proxy/http_headers.go:47",
    "proxy/http_headers.go:51"
   ],
   "reason_to_dismiss": "Fabio keeps a client-supplied X-Real-Ip on purpose for chained proxies, and a unit test pins that behaviour, so leaving it alone looks correct",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "proxy/http_headers.go:45-47 skips setting ClientIPHeader when the operator names it X-Real-Ip",
    "proxy/http_headers.go:51-53 then sets X-Real-Ip only when the client did not send one, so the operator's designated client-IP header carries the client's value",
    "proxy/http_headers_test.go:349-357 'do not overwrite X-Real-Ip, if present' is the must-keep coupled behaviour for the default config"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "proxy/http_proxy.go:206",
    "proxy/ws_handler.go:55"
   ],
   "reason_to_dismiss": "The websocket path writes the request raw to the backend and never strips Connection tokens, so fabio's headers are not removed on this route unless a hop-by-hop-honouring intermediary sits behind fabio",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "mimo",
   "evidence": [
    "proxy/http_proxy.go:206-214 Upgrade: websocket goes to newWSHandler and not to the ReverseProxy",
    "proxy/ws_handler.go:55 r.Write(out) forwards the Connection header unchanged, so this route needs Connection: Upgrade to keep working"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "proxy/grpc_handler.go:52",
    "proxy/grpc_handler.go:58",
    "main.go:178"
   ],
   "reason_to_dismiss": "The gRPC proxy is a transparent metadata pass-through that has never set any fabio headers, so it looks like a missing feature and not a vulnerable route",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "proxy/grpc_handler.go:52-58 copies all incoming metadata verbatim to the outgoing context, including any client-sent header named like cfg.Proxy.ClientIPHeader, TLSHeader or RequestID",
    "main.go:178 the gRPC listener uses grpc_proxy.TransparentHandler with this director, and addHeaders is never called"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "proxy/http_proxy.go:195",
    "proxy/http_handler.go:18"
   ],
   "reason_to_dismiss": "A sanitiser that reads r.Header.Get(\"Connection\") and splits it on ',' looks complete for the common single-line form",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "proxy/http_proxy.go:195 the code base reads single header values with Header.Get, the idiom a solver would copy",
    "proxy/http_handler.go:18 the stdlib ReverseProxy, not repo code, performs the actual token removal (stdlib behaviour is in unverified)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3",
   "T5",
   "T7"
  ],
  [
   "T4"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "Deleting the whole Connection header, or every token in it, breaks websocket upgrades. The ws route forwards the raw request (proxy/ws_handler.go:55) and needs Connection: Upgrade, so only tokens that name fabio-managed headers may be removed."
  },
  {
   "a": "T4",
   "b": "T1",
   "what": "Always overwriting X-Real-Ip closes T4 but breaks the pinned 'do not overwrite X-Real-Ip, if present' behaviour (proxy/http_headers_test.go:349-357). It may only be overwritten when the operator names it as ClientIPHeader."
  }
 ],
 "fairness_risks": [
  "Client-supplied X-Forwarded-Proto/Port/Host and X-Real-Ip are deliberately preserved for chained proxies (proxy/http_headers.go:51,81,92,96; tests at proxy/http_headers_test.go:222,308,335,349). A hidden test that requires these to be overwritten would contradict pinned must-keep behaviour.",
  "Connection: Upgrade (and any token that does not name a fabio-managed header, such as keep-alive) must keep working on the ws route (proxy/http_proxy.go:206, proxy/ws_handler.go:55).",
  "If cfg.ClientIPHeader is X-Forwarded-For, the stdlib appends to the client chain instead of overwriting (proxy/http_headers.go:43-46). A rule demanding a single fabio-only value would break the documented XFF chaining (proxy/http_integration_test.go:57-60 expects '3.3.3.3, 127.0.0.1').",
  "T6 (gRPC) is outside the Connection-header framing of both advisories. A hidden test there needs a report that at least names the trust-header contract and not only the Connection mechanism."
 ],
 "effort_minutes": 50,
 "usable": true,
 "design": {
  "traps": [
   "T2",
   "T3",
   "T4",
   "T6"
  ],
  "why": "Only 3 independent groups exist: the Connection-token sanitiser (T1/T2/T3/T5/T7 share one fix site), the X-Real-Ip ClientIPHeader coupling (T4), and the gRPC pass-through (T6). The design reports the advisory-A surface, so T1 is described and easy. It then hides T2 (config-named headers, the actual B delta) and T3 (requestid set in ServeHTTP, which is dismissable as non-security) inside the sanitiser group. Those count as one group but force separate judgements about what goes in the list. T4 is the mimo-type coupled value against a pinned test, and T6 is the deepseek-type absent route with a strong reason to dismiss. That gives three independent groups with different dismissal reasons, one deepseek-type (T6, also T2/T3) and one mimo-type (T4). It beats a design built on T5/T7, which depend on stdlib or deployment behaviour that is hard to test fairly. The candidate is at the minimum of 3 independent groups and reaches it only if T6 is accepted as in scope."
 },
 "unverified": [
  "The content and location of the A fix (fdaf1e966162) and B fix (240526a80040) were not inspected. The claims that A hard-coded a list of well-known header names and that B added the clientip/tls/requestid names are inferred from the candidate summary.",
  "The pinned commit has no Connection handling at all (repo-wide grep), which suggests it predates A. The pinned commit's date relative to A was not checked.",
  "Go 1.24 (go.mod:3) httputil.ReverseProxy calls Director before removeHopByHopHeaders and iterates all Connection header lines with comma splitting and trimming. This is stdlib behaviour and is not vendored in the repo.",
  "Whether upstream regards T4 (ClientIPHeader=X-Real-Ip keeps client value) or T6 (gRPC metadata pass-through) as in scope of GHSA-fq95-v8xc-jm3v.",
  "T5 harm requires a hop-by-hop-honouring intermediary between fabio and the ws backend. It is not reachable against a plain backend."
 ]
}
  ```
- Published fix sites:   - proxy/http_headers.go:51 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:81 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:92 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:96 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:100 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:124 — T1 M4 (reason to dismiss: none)
  - proxy/http_handler.go:18 — T1 M4 (reason to dismiss: none)
  - proxy/http_headers.go:48 — T2 M5 (reason to dismiss: The header names come from operator config and are not fixed constants, so a fix that hard-codes a list of the well-known X-Forwarded-*/Forwarded/X-Real-Ip names looks complete)
  - proxy/http_headers.go:128 — T2 M5 (reason to dismiss: The header names come from operator config and are not fixed constants, so a fix that hard-codes a list of the well-known X-Forwarded-*/Forwarded/X-Real-Ip names looks complete)
  - config/load.go:149 — T2 M5 (reason to dismiss: The header names come from operator config and are not fixed constants, so a fix that hard-codes a list of the well-known X-Forwarded-*/Forwarded/X-Real-Ip names looks complete)
  - config/load.go:150 — T2 M5 (reason to dismiss: The header names come from operator config and are not fixed constants, so a fix that hard-codes a list of the well-known X-Forwarded-*/Forwarded/X-Real-Ip names looks complete)
  - proxy/http_proxy.go:88 — T3 M1 (reason to dismiss: A request id is a correlation value and not a security or trust header, and it is set in ServeHTTP outside addHeaders, so a solver who reviews only addHeaders never sees it)
  - proxy/http_proxy.go:93 — T3 M1 (reason to dismiss: A request id is a correlation value and not a security or trust header, and it is set in ServeHTTP outside addHeaders, so a solver who reviews only addHeaders never sees it)
  - config/load.go:152 — T3 M1 (reason to dismiss: A request id is a correlation value and not a security or trust header, and it is set in ServeHTTP outside addHeaders, so a solver who reviews only addHeaders never sees it)
- Uncovered routes to confirm (pattern B):   - proxy/http_headers.go:45 — T4 M11 (reason to dismiss: Fabio keeps a client-supplied X-Real-Ip on purpose for chained proxies, and a unit test pins that behaviour, so leaving it alone looks correct)
  - proxy/http_headers.go:47 — T4 M11 (reason to dismiss: Fabio keeps a client-supplied X-Real-Ip on purpose for chained proxies, and a unit test pins that behaviour, so leaving it alone looks correct)
  - proxy/http_headers.go:51 — T4 M11 (reason to dismiss: Fabio keeps a client-supplied X-Real-Ip on purpose for chained proxies, and a unit test pins that behaviour, so leaving it alone looks correct)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T2, T3, T4, T6. Why: Only 3 independent groups exist: the Connection-token sanitiser (T1/T2/T3/T5/T7 share one fix site), the X-Real-Ip ClientIPHeader coupling (T4), and the gRPC pass-through (T6). The design reports the advisory-A surface, so T1 is described and easy. It then hides T2 (config-named headers, the actual B delta) and T3 (requestid set in ServeHTTP, which is dismissable as non-security) inside the sanitiser group. Those count as one group but force separate judgements about what goes in the list. T4 is the mimo-type coupled value against a pinned test, and T6 is the deepseek-type absent route with a strong reason to dismiss. That gives three independent groups with different dismissal reasons, one deepseek-type (T6, also T2/T3) and one mimo-type (T4). It beats a design built on T5/T7, which depend on stdlib or deployment behaviour that is hard to test fairly. The candidate is at the minimum of 3 independent groups and reaches it only if T6 is accepted as in scope. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Client-supplied X-Forwarded-Proto/Port/Host and X-Real-Ip are deliberately preserved for chained proxies (proxy/http_headers.go:51,81,92,96; tests at proxy/http_headers_test.go:222,308,335,349). A hidden test that requires these to be overwritten would contradict pinned must-keep behaviour. | Connection: Upgrade (and any token that does not name a fabio-managed header, such as keep-alive) must keep working on the ws route (proxy/http_proxy.go:206, proxy/ws_handler.go:55). | If cfg.ClientIPHeader is X-Forwarded-For, the stdlib appends to the client chain instead of overwriting (proxy/http_headers.go:43-46). A rule demanding a single fabio-only value would break the documented XFF chaining (proxy/http_integration_test.go:57-60 expects '3.3.3.3, 127.0.0.1'). | T6 (gRPC) is outside the Connection-header framing of both advisories. A hidden test there needs a report that at least names the trust-header contract and not only the Connection mechanism.. Conflicts the reader found: Deleting the whole Connection header, or every token in it, breaks websocket upgrades. The ws route forwards the raw request (proxy/ws_handler.go:55) and needs Connection: Upgrade, so only tokens that name fabio-managed headers may be removed. | Always overwriting X-Real-Ip closes T4 but breaks the pinned 'do not overwrite X-Real-Ip, if present' behaviour (proxy/http_headers_test.go:349-357). It may only be overwritten when the operator names it as ClientIPHeader.

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

## Environment (`tasks/stk-fabio-ghsafq95/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-fabio-ghsafq95/instruction.md`)
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

## Tests (`tasks/stk-fabio-ghsafq95/tests/`)
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
- **Wrong-fix patches** go in `build/stk-fabio-ghsafq95/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-fabio-ghsafq95/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-fabio-ghsafq95/manifest.json`:**
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

**Also in `build/stk-fabio-ghsafq95/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-fabio-ghsafq95 --only static
python3 -I builder/gate.py stk-fabio-ghsafq95 --only nop
python3 -I builder/gate.py stk-fabio-ghsafq95 --only oracle
python3 -I builder/gate.py stk-fabio-ghsafq95 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-fabio-ghsafq95/`;
  - edit only `tasks/stk-fabio-ghsafq95/`, `build/stk-fabio-ghsafq95/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-fq95-v8xc-jm3v.json`. Verify each trap on the
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

Stacked task slug: `stk-fabio-ghsafq95`. Control task slug: `stk-fabio-ghsafq95-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-fq95-v8xc-jm3v.json`.
