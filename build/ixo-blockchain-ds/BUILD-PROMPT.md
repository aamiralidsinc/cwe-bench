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

Project root: `/home/mara/cwe-bench`. Task: `ixo-blockchain-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-W3RP-4CM2-4WGC", "CVE-2026-61604", "GO-2026-6595"]; ixofoundation/ixo-blockchain; missing authorization / confused deputy: authorization is enforced only in the tx ante, and keeper handlers act for a DID-resolved principal on routes that skip the ante (CWE-862/CWE-285)
- Pinned (vulnerable) commit: 155fdc7831319216ff5ff9651615696c41a0de59. Published fix: 09a51da9a512779d1fb16c9a11e113f760a70921.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "19512",
 "advisory_ids": [
  "GHSA-W3RP-4CM2-4WGC",
  "CVE-2026-61604",
  "GO-2026-6595"
 ],
 "repo": "ixofoundation/ixo-blockchain",
 "pinned_commit": "155fdc7831319216ff5ff9651615696c41a0de59",
 "fix_commits": [
  "09a51da9a512779d1fb16c9a11e113f760a70921"
 ],
 "trust_decision": {
  "summary": "Whether the tx signer (proto signer field) controls the DID a message acts as. At the pinned commit only the IID ante decides this, for top-level IidTxMsgs only. Keeper handlers spend funds or mutate state for a DID-resolved address or a DID-equality match without re-binding it to the signer, so routes that skip the ante (authz MsgExec inner msgs, CosmWasm-dispatched msgs, ICA host with allow-all) are unchecked.",
  "evidence": [
   "x/iid/ante/iidtx.go:27",
   "x/iid/ante/iidtx.go:55",
   "x/bonds/keeper/msg_server.go:694-715",
   "x/entity/keeper/msg_server.go:165-171",
   "app/upgrades/v4/upgrades.go:238-242"
  ]
 },
 "landing_point": {
  "where": "x/bonds/keeper/msg_server.go:692",
  "why": "The summary names an 'x/bonds DID-resolved payer drain'. MakeOutcomePayment resolves SenderDid's fragment to an address (line 698) and deposits from it (line 715) without comparing it to SenderAddress."
 },
 "fix_sites": [
  {
   "where": "x/bonds/module.go:120",
   "entry_point": "all x/bonds Msg RPCs (tx / authz MsgExec / wasm / ICA), replaced by a disabled msg server (fix.diff:837, fix.diff:742-819)",
   "module_kind": "module wiring / msg server registration"
  },
  {
   "where": "x/bonds/module.go:144",
   "entry_point": "bonds EndBlock batch processing (orders stored by MsgBuy/MsgSell/MsgSwap), made a no-op (fix.diff:852-856)",
   "module_kind": "end-blocker (stored-state consumer)"
  },
  {
   "where": "app/ante.go:95",
   "entry_point": "every signed tx; new RejectBondsMsgDecorator (fix.diff:21-23, fix.diff:482-559)",
   "module_kind": "ante decorator chain"
  },
  {
   "where": "x/iid/ante/iidtx.go:27",
   "entry_point": "any tx carrying an IidTxMsg nested in authz.MsgExec (fix.diff:1646-1653, fix.diff:1671-1693)",
   "module_kind": "ante check (wrapper unwrapping)"
  },
  {
   "where": "x/entity/ante/decorators.go:27",
   "entry_point": "wasm MsgExecuteContract on the entity NFT contract nested in authz.MsgExec (fix.diff:1097-1141)",
   "module_kind": "ante decorator (wrapper unwrapping)"
  },
  {
   "where": "x/entity/keeper/msg_server.go:165",
   "entry_point": "MsgUpdateEntity via any route (fix.diff:1245-1247)",
   "module_kind": "keeper msg handler"
  },
  {
   "where": "x/entity/keeper/msg_server.go:229",
   "entry_point": "MsgTransferEntity via any route (fix.diff:1260-1262)",
   "module_kind": "keeper msg handler"
  },
  {
   "where": "x/entity/keeper/msg_server.go:310-314",
   "entry_point": "MsgUpdateEntityVerified via any route (fix.diff:1275-1277)",
   "module_kind": "keeper msg handler"
  },
  {
   "where": "x/claims/types/tx.go:10-11",
   "entry_point": "MsgSubmitClaim / MsgEvaluateClaim / MsgCreateClaimAuthorization taken out of the IidTxMsg set (fix.diff:1019-1054)",
   "module_kind": "message type interface membership"
  },
  {
   "where": "app/upgrades/v4/upgrades.go:240",
   "entry_point": "ICA host AllowMessages param '*' replaced by an allow-list in a new v8 upgrade handler (fix.diff:395-442, fix.diff:474-477)",
   "module_kind": "chain param / upgrade handler"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "x/iid/ante/iidtx.go:27 (iterates top-level tx.GetMsgs() only; authz.MsgExec inner msgs skip the check) and the ICA host allow-all param at app/upgrades/v4/upgrades.go:240"
 },
 "O3_reason_to_dismiss": "The ante already checks signer-vs-DID for IidTxMsgs, and authz itself requires the grantee to hold a grant from the granter. ICA/wasm dispatch is 'by design' and set in an old v4 upgrade handler, so a solver patching bonds handlers can argue the wrapper and transport routes are a neighbouring feature.",
 "O4_distance": {
  "files": 16,
  "packages": 12,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Authz-delegated claims. In MsgSubmitClaim/MsgEvaluateClaim the signer is the collection admin, while AgentDid names a different party and is attribution only. A blanket 'signer must control every *_did' rule breaks delegated submission and evaluation. The fix removed these from IidTxMsg for that reason. Also, the IID ante accepts the AssertionMethod relationship as well as Authentication. A legitimate MsgExec with an authorized granter must also keep passing.",
  "where": "x/claims/types/tx.go:34; x/claims/types/tx.go:47; x/claims/types/tx.go:143; x/iid/ante/iidtx.go:18-24; x/claims/keeper/disputes.go:198-201"
 },
 "O6_input_shapes": [
  "top-level message",
  "message nested in authz.MsgExec",
  "message nested in multiple MsgExec layers (depth cap 6)",
  "message dispatched without ante (wasm / ICA host / router direct)",
  "DID fragment whose verification method resolves to an address other than the signer"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "x/iid/types/iid.go:587 (GetVerificationMethodBlockchainAddress maps a DID#fragment to the address that bonds spends from)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "MsgCreateEntity: OwnerDid is written as a controller of the new entity DID with no in-keeper signer-to-OwnerDid binding. The fix added the keeper check to the other three entity handlers but not this one.",
   "where": "x/entity/keeper/msg_server.go:81",
   "reason_to_dismiss": "Create only makes a new entity; no existing victim state is mutated, so 'acting as' another DID looks harmless.",
   "distance": "same file as three fixed sites",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "MsgDisputeClaim: DisputerDid is recorded from AgentDid, and the keeper relies on the IID ante for the signer-to-AgentDid binding (comment says so).",
   "where": "x/claims/keeper/msg_server.go:576-577",
   "reason_to_dismiss": "Comment says the ante validates it, the fix's own comments say MsgDisputeClaim correctly stays IidTxMsg, and the field is attribution only.",
   "distance": "other package (x/claims/keeper) from landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "MsgClaimIntent: still an IidTxMsg via GetIidController; the keeper stores AgentDid on the intent without binding it to AgentAddress.",
   "where": "x/claims/keeper/msg_server.go:1116",
   "reason_to_dismiss": "Authorization is the authz SubmitClaimAuthorization grant check (lines 959-966), so AgentDid looks like attribution only.",
   "distance": "other package (x/claims/keeper)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Bonds DID-equality gates (EditBond CreatorDid==EditorDid, UpdateBondState ControllerDid==EditorDid, SetNextAlpha OracleDid, WithdrawReserve ControllerDid==WithdrawerDid) never bind signer to DID in-keeper. The published fix closed them only by disabling the module.",
   "where": "x/bonds/keeper/msg_server.go:185",
   "reason_to_dismiss": "The report leads to payer-drain handlers (Buy/Sell/MakeOutcomePayment); DID-equality gates look like they already 'check authorization'.",
   "distance": "same file as landing point",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "x/entity/keeper/msg_server.go:340",
   "sibling": "An entity-account handler that resolves the owner via a DID instead of CheckIfOwner on OwnerAddress.",
   "why_realistic": "The same file mixes DID-based and address-based owner checks; a maintainer adding a DID-keyed variant would copy the UpdateEntity pattern."
  },
  {
   "where": "x/bonds/keeper/batch.go:212-216",
   "sibling": "Batch end-blocker re-resolves the stored order's AccountDid fragment to an address at execution time (save/reload of a DID reference).",
   "why_realistic": "The order stores only the DID fragment (msg_server.go:476), so re-resolving at batch time is the natural implementation; a check at message time does not cover it."
  }
 ],
 "O9_family": "missing authorization / confused deputy: authorization is enforced only in the tx ante, and keeper handlers act for a DID-resolved principal on routes that skip the ante (CWE-862/CWE-285)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.22.11, cosmos-sdk v0.50.11-lsm fork, wasmd with CGO libwasmvm v1.5.4",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Keeper/ante suites: x/iid/ante/decorators_test.go, x/entity/ante/decorators_test.go, x/entity/keeper/wasm_test.go; app/apptesting/test_suite.go:174 RunMsg dispatches through the MsgServiceRouter without the ante, which suits no-ante behavioural tests"
 },
 "O11_fix_minutes": 120,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "app/ante.go, app/app.go, app/upgrades/v8/constants.go, app/upgrades/v8/upgrades.go, x/bonds/ante/disabled.go, x/bonds/keeper/msg_server_disabled.go, x/bonds/module.go, x/bonds/types/errors.go, x/claims/types/tx.go, x/entity/ante/decorators.go, x/entity/keeper/auth.go, x/entity/keeper/msg_server.go, x/iid/ante/iidtx.go, x/token/keeper/batch.go, x/token/keeper/msg_server.go, x/token/types/errors.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a signer==resolved-address check to MakeOutcomePayment (and maybe Buy/Sell) only, trusting the IID ante for entity and claims and for MsgExec/wasm/ICA routes."
 },
 "out_of_scope_notes": [
  "x/token ValidateTokenBatch (mixed-contract batch, empty batch) and the CancelToken supply-underflow panic are bundled in the same commit but are input-validation/robustness issues, not this advisory's signer-to-DID property (fix.diff:1781-2003).",
  "The fix's entity-NFT ante comment admits that contract-to-contract submessages and ICA still bypass BlockNftContractTransferForEntityDecorator (fix.diff:1088-1091); that is a separate protection."
 ],
 "unverified": [
  "The published fix neutralises bonds with a kill switch (disabled msg server, no-op EndBlocker, ante reject) rather than a signer check. Hidden tests asserting ErrBondsModuleDisabled would be unfair; graders would need rewriting as behavioural 'unauthorized signer rejected, authorized passes' tests. This is the main task-design risk but not a listed red-flag enum.",
  "The ICA allow-list part of the fix is a state migration in a new upgrade handler; it is hard to test behaviourally without an IBC harness, and a solver would not naturally add an upgrade.",
  "O11 of ~120 min exceeds the 45-min budget for the full published scope; a task would need trimming (e.g. bonds payer binding + entity keeper binding + MsgExec unwrapping).",
  "Whether CosmWasm contracts at the pinned commit can dispatch arbitrary ixo Msgs (Any/Stargate CosmosMsg) to the router was not traced in wasmd configuration (app/keepers/keepers.go:505 enables 'stargate').",
  "repo_mb unknown (no shell size check); tiny_repo/giant_repo not assessed but a Cosmos chain repo is very likely between 5 MB and 1.5 GB.",
  "present_in_latest is unknown for all O8 routes (no latest release given)."
 ]
}
  ```
- Published fix sites:   - x/bonds/module.go:120 — entry point: all x/bonds Msg RPCs (tx / authz MsgExec / wasm / ICA), replaced by a disabled msg server (fix.diff:837, fix.diff:742-819) [module wiring / msg server registration]
  - x/bonds/module.go:144 — entry point: bonds EndBlock batch processing (orders stored by MsgBuy/MsgSell/MsgSwap), made a no-op (fix.diff:852-856) [end-blocker (stored-state consumer)]
  - app/ante.go:95 — entry point: every signed tx; new RejectBondsMsgDecorator (fix.diff:21-23, fix.diff:482-559) [ante decorator chain]
  - x/iid/ante/iidtx.go:27 — entry point: any tx carrying an IidTxMsg nested in authz.MsgExec (fix.diff:1646-1653, fix.diff:1671-1693) [ante check (wrapper unwrapping)]
  - x/entity/ante/decorators.go:27 — entry point: wasm MsgExecuteContract on the entity NFT contract nested in authz.MsgExec (fix.diff:1097-1141) [ante decorator (wrapper unwrapping)]
  - x/entity/keeper/msg_server.go:165 — entry point: MsgUpdateEntity via any route (fix.diff:1245-1247) [keeper msg handler]
  - x/entity/keeper/msg_server.go:229 — entry point: MsgTransferEntity via any route (fix.diff:1260-1262) [keeper msg handler]
  - x/entity/keeper/msg_server.go:310-314 — entry point: MsgUpdateEntityVerified via any route (fix.diff:1275-1277) [keeper msg handler]
  - x/claims/types/tx.go:10-11 — entry point: MsgSubmitClaim / MsgEvaluateClaim / MsgCreateClaimAuthorization taken out of the IidTxMsg set (fix.diff:1019-1054) [message type interface membership]
  - app/upgrades/v4/upgrades.go:240 — entry point: ICA host AllowMessages param '*' replaced by an allow-list in a new v8 upgrade handler (fix.diff:395-442, fix.diff:474-477) [chain param / upgrade handler]
- Uncovered routes to confirm (pattern B):   - x/entity/keeper/msg_server.go:81 — MsgCreateEntity: OwnerDid is written as a controller of the new entity DID with no in-keeper signer-to-OwnerDid binding. The fix added the keeper check to the other three entity handlers but not this one. (reason to dismiss: Create only makes a new entity; no existing victim state is mutated, so 'acting as' another DID looks harmless.; still in latest: unknown)
  - x/claims/keeper/msg_server.go:576-577 — MsgDisputeClaim: DisputerDid is recorded from AgentDid, and the keeper relies on the IID ante for the signer-to-AgentDid binding (comment says so). (reason to dismiss: Comment says the ante validates it, the fix's own comments say MsgDisputeClaim correctly stays IidTxMsg, and the field is attribution only.; still in latest: unknown)
  - x/claims/keeper/msg_server.go:1116 — MsgClaimIntent: still an IidTxMsg via GetIidController; the keeper stores AgentDid on the intent without binding it to AgentAddress. (reason to dismiss: Authorization is the authz SubmitClaimAuthorization grant check (lines 959-966), so AgentDid looks like attribution only.; still in latest: unknown)
  - x/bonds/keeper/msg_server.go:185 — Bonds DID-equality gates (EditBond CreatorDid==EditorDid, UpdateBondState ControllerDid==EditorDid, SetNextAlpha OracleDid, WithdrawReserve ControllerDid==WithdrawerDid) never bind signer to DID in-keeper. The published fix closed them only by disabling the module. (reason to dismiss: The report leads to payer-drain handlers (Buy/Sell/MakeOutcomePayment); DID-equality gates look like they already 'check authorization'.; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

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

## Environment (`tasks/ixo-blockchain-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/ixo-blockchain-ds/instruction.md`)
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

## Tests (`tasks/ixo-blockchain-ds/tests/`)
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
- **Wrong-fix patches** go in `build/ixo-blockchain-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/ixo-blockchain-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ixo-blockchain-ds/manifest.json`:**
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

**Also in `build/ixo-blockchain-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py ixo-blockchain-ds --only static
python3 -I builder/gate.py ixo-blockchain-ds --only nop
python3 -I builder/gate.py ixo-blockchain-ds --only oracle
python3 -I builder/gate.py ixo-blockchain-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ixo-blockchain-ds/`;
  - edit only `tasks/ixo-blockchain-ds/`, `build/ixo-blockchain-ds/` and, for pattern B, the register;
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
