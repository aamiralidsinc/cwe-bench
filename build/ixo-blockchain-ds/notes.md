# ixo-blockchain-ds — build notes

Started: 2026-10-24T05:18Z
Finished: 2026-10-24T09:20Z (gate green; the session was paused 06:30-07:48Z while the host Docker daemon was repaired)

Advisory family: missing authorization / confused deputy (CWE-862). The transaction-level IID
check binds a message's declared signer to the DID it acts for, but only for top-level messages;
handlers that resolve an account out of a DID document or compare stored DIDs with caller-supplied
DIDs never re-bind the signer.

## Levers (one line each)

- T1 `payer_account_binding` (A, how-type): a DID document may register any account as a
  verification method, so "signer controls the DID" passes while the debit resolves to another
  account; only comparing the resolved account with the signer's own address closes it
  (`x/bonds/keeper/msg_server.go:692,431,503,628,735`).
- T2 `entity_keeper_binding` (A far site): entity handlers check DID-controls-DID / the pinned
  relayer DID but never bind the signer to that DID (`x/entity/keeper/msg_server.go:157,302`).
- T3 `bond_did_equality` (B, real upstream): the stored DID is compared with a caller-supplied
  DID, which proves nothing about the signer (`x/bonds/keeper/msg_server.go:178,248,389,807`).
- T4 `dispute_deposit_resolution` (B, injected sibling): the dispute stake is funded from the
  account the named DID document registers, so a document the attacker controls debits another
  account (`x/claims/keeper/msg_server.go:635-646`).
- T5 `reserve_fee_resolution` (B, injected sibling): the reserve-withdrawal exit fee is debited
  from the account the withdrawer DID resolves to, behind a DID-equality gate that passes
  (`x/bonds/keeper/msg_server.go:849-861`).
- Coupled must-keep-working: a request may name another party as its subject (admin submits a
  claim for a service agent; the agent DID is not controlled by the signer), and a controller key
  registered under the assertion-method relationship is equally valid.

## Candidate list and why the picks won

All DID-scoped operations found at the pinned commit:

1. bonds payer handlers (MakeOutcomePayment, Buy incl. first-swapper path, Sell, Swap,
   WithdrawShare) — CHOSEN. Real, reachable, victim account is debited, and the producer
   (DID-document → account mapping) can be populated by the attacker.
2. bonds DID-equality handlers (EditBond, SetNextAlpha, UpdateBondState, WithdrawReserve) —
   CHOSEN (Pattern B). Real upstream, reachable, no signer binding at all; the published fix only
   disabled the module.
3. entity UpdateEntity / UpdateEntityVerified — CHOSEN (Pattern A far site). The published fix
   adds the same in-keeper binding to exactly these handlers.
4. entity TransferEntity — not security-tested: the DID-document rewrite is followed by a wasm NFT
   transfer by the declared owner; an unauthorised caller fails the wasm call and a real
   transaction rolls the rewrite back, so the attack does not reproduce through a signed tx.
5. entity CreateEntity (OwnerDid written as a controller) — rejected: it creates a new DID; the
   named party gains control over the attacker's entity, not the reverse (no victim harm).
6. claims DisputeClaim's missing in-keeper signer→DID binding — rejected: the deposit is debited
   from the request's own signer field, so a behavioural test cannot distinguish a spoofed field
   from a real signer; and the act-as/refer-to distinction would be ambiguous.
7. claims ClaimIntent — rejected: authorization is an admin authz grant, and the escrow funding
   comes from a collection account, not a DID-resolved debit.
8. claims AddPerformanceDeposit — rejected as a lever site: the message has no DID field, so a
   DID-resolution sibling cannot be added without a proto change.
9. claims SubmitClaim / EvaluateClaim — not security routes (the agent DID is attribution only);
   they are the coupled functional case instead.
10. iid message handlers — rejected: they already bind the declared signer to the DID through
    ExecuteOnDidWithRelationships; on a dispatch path with no ante the declared field is itself
    unauthenticated, so no keeper-level fix exists and the published fix does not attempt one.
11. names module — already has an in-keeper DID controller check (`verifyDidController`); it is
    the fair precedent the solver can follow, and there is nothing to add.
12. bonds EndBlock batch re-resolution of the stored AccountDid — rejected: at execution time it
    credits payouts to the stored DID's account; no victim account is debited from a DID resolved
    at execution time, and the DID's controller can only redirect their own payout.
13. CreateBond naming arbitrary Creator/Controller/Oracle DIDs — rejected: the new record belongs
    to the attacker-chosen bond DID, so the named party gains control, not harm.
14. liquidstake, epochs, mint, smart-account — no DID-resolved principal or DID-keyed record.
15. entity CreateEntityAccount / Grant / RevokeEntityAccountAuthz — address-based CheckIfOwner,
    no DID field to bind.

The injected siblings (T4, T5) were chosen because every other untouched module either lacks a
DID field on the handler, has no debit that a mismatch test can observe, or already performs the
binding. They are placed in files the published fix never edits (`x/claims/keeper/msg_server.go`
and `x/bonds/keeper/msg_server.go`), are reached through the real message service router, and are
covered only by the general property (the instruction never mentions them).

## The published fix vs the oracle

The published fix neutralises the bonds module with a kill switch (disabled msg server, no-op
EndBlocker, rejecting ante decorator) and adds a v8 ICA allow-list migration. A kill switch cannot
be graded behaviourally (legitimate bond use must keep working), and the ICA migration needs an
IBC harness. The oracle therefore keeps the published fix's per-handler entity binding and the
same signer→DID relationship contract, replaces the bonds kill switch with the equivalent
in-keeper signer and account binding, and fixes the two injected siblings. Message-wrapper
unwrapping from the published fix is not needed for these tests: the same keeper check closes an
inner message on the delegated path.

## Verified

- Gate: static PASS; nop PASS (all 13 security test cases, including the suite entry, fail on
  pinned+injected and all 100 functional test cases pass); oracle PASS three times with reward
  1.0 and identical results; patches PASS 14/14 as declared (9 security_fail, 3 functional_fail,
  the hardening and alternative designs both 1.0). Trial evidence is in
  build/ixo-blockchain-ds/gate-logs/ (logs + per-trial JSON summary).
- In-image runs: the nop/oracle/patch trials all executed the real verifier image offline as
  uid 1000, compiled the project with the warmed Go module and build caches, and produced JUnit
  XML through go-junit-report.
- All 12 hidden security tests fail on pinned+injected and pass on the oracle; all 11 hidden
  functional tests pass on both. The remaining functional test cases are the project's own tests
  for x/bonds/keeper, x/claims/keeper, x/entity/keeper, x/iid/ante, x/entity/ante and
  app/apptesting. Four upstream tests that assert the pre-fix model are skipped by name:
  TestMsgEditBond, TestMsgEditBond_WrongEditor,
  TestMsgUpdateBondState_AugmentedHatchToOpen and TestMsgUpdateEntity.
- Every wrong-fix patch was run through the real gate, not just locally; the declared outcomes
  above are the recorded reward/security/functional counts.
- Both patches apply with `patch -p1` to a fresh fetch of the pinned commit; the resulting tree is
  byte-identical to the build tree.
- Offline: the verifier image needs no network; the module cache, build cache and libwasmvm are
  baked into both images.

## Not verified / guesses

- CosmWasm stargate and ICA-host dispatch were not exercised end to end (no contract/IBC harness);
  the tests drive the same MsgServiceRouter they call, with the ante skipped as those paths do.
- `present_in_latest` for the bond routes is recorded as "no" because the module's msg server is
  disabled at the current upstream tip; the handler bodies are unchanged there.
- The published ICA allow-list migration behaviour was not reproduced.
- The solver's effort is dominated by breadth (five handler families plus two siblings); the
  core mechanism is quick to understand once the invariant is read literally.
- The blind-fix patch and the fairness review are produced after this build, by the later stages.

## Out of scope (not built on)

- x/token batch validation and the CancelToken supply-underflow panic in the same fix commit are
  input-validation/robustness issues, not signer-to-DID authorization.
- The entity-NFT ante comment admits contract-to-contract submessages and ICA still bypass that
  decorator; that is a separate protection.
