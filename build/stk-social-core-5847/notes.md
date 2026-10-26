# stk-social-core-5847 build notes

Start: 2026-10-25T22:54:57Z
End:   2026-10-25T23:25:04Z

Stacked task (H4) from reader record h4-5847 (the prompt names
`pipelines/stacking/out/reader/h4-5847.json`; the record actually present on disk is
`pipelines/stacking/out/reader-ds/h4-5847.json`, same candidate and traps).

## Levers (one line each)

- T1 — where, advisory route: the shared resume utility takes a flow identifier from the request and
  loads the stored flow without comparing it with the token the calling session recorded.
- T2 — where, published-fix far site: the disconnect action is a second caller of that shared
  decision and then invokes the disconnect pipeline itself rather than the resume hook.
- T3 — shape, advisory route: the identifier arrives as the explicit argument or under the
  configured request-field name, so a check written against one default field misses them.
- T4 — how, coupled value, advisory route: a flow the library set up for out-of-band completion must
  still complete from a fresh session, so a blanket session-equality rule is wrong.
- T5 — how, producer far site: the out-of-band allowance and its proof field names are recorded on
  the stored flow by the step decorator; the resume check reads that record and never calls the
  producer.
- T7 — where, uncovered upstream: the backend resume hook continues an already-loaded stored flow
  without going through the shared utility; the published fix and current origin/master leave it
  unguarded.

Dropped: screener T8 (legacy OpenID override). Checked on the pinned tree: the override passes
`response=...` together with `partial.kwargs`, which always already contains `response`, so a
product-produced stored flow raises TypeError before resuming. The route does not reproduce, so it
was not built on (manifest.verified.routes records this). No substitute injection was added; the
remaining three concepts each carry their own security_fail check.

## Verified

- Pinned tree 6fcde2c2 (parent of 04187824): all seven security cases fail through the real entry
  points; all seven hidden functional cases pass; the project's test_utils.py and test_login.py pass.
- Reference fix: 7/7 security + 7/7 functional; project tests still pass; three oracle gate runs were
  identical reward 1.0.
- Published fix as shipped (checks/upstream_fix.patch): 6/7 security + 7/7 functional; only the
  lower-level resume hook remains open, so the stack adds a concept beyond upstream.
- Each concept has a security_fail check that leaves only it open (miss_session → disconnect caller,
  miss_external → request-supplied proof, miss_continue → low-level hook). The two functional_fail
  checks break a coupled legitimate flow. The hardening and alternative-loader pass patches both
  score 1.0.
- Gate: static, nop, oracle and patches all PASS for the stacked task and for the control task;
  check_stack.py reports conforming (3 concepts, H4).
- Pattern B register: one row for T7; current origin/master (11e7b3bf) read directly and the direct
  loader + resume-hook route still has no ownership decision there.

## Could not verify / unknowns

- The advisory text beyond the screener summary was not provided; the property was derived from the
  published fix and the code.
- The reference fix is a behaviour-preserving equivalent of the published fix, not the published diff
  verbatim: the published fix requires framework strategies to implement new confirmation hooks and
  changes partial_step's stored data shape. The reference records the allowance and its proof fields
  on the stored flow and keeps the documented fresh-session completion working without a new
  application hook; the hidden functional suite also accepts a confirmation-based design (the
  strategy harness implements the published hooks, which stay inert for other designs). The
  published fix alone is still a wrong fix for the stacked task because it leaves T7 open.
- The pinned commit's own test_partial.py passes on the pinned tree and on the reference fix, but the
  published fix changes the decorator's behaviour its pinned mock asserts, so that file is not in the
  verifier's functional group; test_utils.py and actions/test_login.py are.
- The control task's instruction.md is byte-identical to the stacked one; only its security suite and
  reference are narrowed to the advisory's own route.

## Fairness notes

- The fresh-session out-of-band completion is the coupled value; the report covers it only through
  "everything that works today keeps working", never by naming the flow.
- The reference accepts the explicit-argument and configured-field shapes for the owning session, and
  the hidden functional suite keeps all of them passing.
- A refused cross-session attempt is reported as a library authentication error or a refusal
  response; the security cases reject an unclean crash.

## Outside this advisory's scope (noted, not built on)

- In the same backend file, legacy OpenID's auth_complete restores a request-supplied session id via
  strategy.restore_session without validating it first; that is a session-restore mechanism, not a
  stored-flow resume, and is out of scope here.
