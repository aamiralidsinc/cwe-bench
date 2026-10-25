# FAIRNESS — pv-pacioli

`tests/functional/project/{test_consent,test_scope}.py` are verbatim copies of the repository's own
visible pure-core suites (the solver can run them). To keep this review readable they are enumerated
by class; every method inside a class carries the same risk. Everything else is enumerated by test.

## 1. Test-by-test

`sec` = `tests/security/test_consent_binding.py`; `fn` = `tests/functional/test_authorised_acts.py`.

| test (file::name) | what it asserts | covering sentence | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| sec::TestOneActNeverRidesAnotherActsAuthority::test_a_marker_minted_to_post_a_document_does_not_reverse_another_one | a cancel of a pre-existing schedule performed inside a marked post raises the permission error; the schedule keeps its state; nothing reversed | "Authority never crosses to a different act"; the exception list allows only a created document or a reversal cascading into reversals; refusal contract | no. A guard in the dispatcher, or after the act in `on_submit`, would fail — but the instruction puts the refusal inside the lifecycle and requires the document untouched, so neither is a correct fix | low |
| …::test_a_cascade_does_not_carry_an_authority_into_a_different_act | the correction the authorised undo creates and posts may ride the undo, but its cancel of a pre-existing document is refused | "a document the authorised act itself creates may be brought into existence as part of it"; "never survives into an act other than the one that carried it"; "however deeply an act is nested" | no (a fix that propagates the *enclosing* act contradicts "never survives into an act other than the one that carried it"); see Human review | medium |
| …::test_a_marker_minted_to_post_a_document_does_not_erase_another_one | erasing a pre-existing bundle inside a marked post is refused; nothing erased | "refuses a lifecycle act … erasing it"; erasure is neither a created document nor a reversal cascade | no | low |
| …::test_a_marker_does_not_authorise_the_document_it_was_amended_into | the amended copy is refused and the original's marker stays unspent | "authorises exactly one act on exactly one document"; "never carries to a document the authorised act did not create" | no | low |
| sec::TestOneRequestMayCarrySomeonesAuthorisationForEachAct::test_whitespace_separated_markers_authorise_their_own_acts | two whitespace-separated markers each authorise their own act; both spent | Contracts: "may present more than one marker … separated by whitespace or commas. Every marker presented is still bound to one document and one act and is spent once" | no | low |
| …::test_comma_separated_markers_authorise_their_own_acts | comma separation, matching marker last, is accepted | same sentence ("commas") | no | low |
| …::test_several_markers_do_not_widen_which_document_they_authorise | a second, valid marker for a different schedule does not authorise this one; the post stands | "each act still has to find the one minted for it"; per-document binding | no | low |
| …::test_an_empty_entry_is_never_a_marker | a record minted from a blank token is not spendable through stray separators; nothing burned | "an empty entry is never a marker" (explicit) | no (a splitter that keeps empty entries is forbidden by that sentence) | low–medium |
| fn::TestAnAuthorisedActProceeds::test_a_document_with_its_own_marker_is_posted_and_the_marker_spent | own-marker post succeeds, marker spent once | Contracts: "an act with its own marker" | no | low |
| …::test_a_marker_is_spent_once_and_a_replay_is_refused | replay refused | "is spent once" | no | low |
| …::test_a_document_with_no_marker_is_refused | empty header refuses the post | "unless the request presents a single-use consent marker" (no marker → refuse) | no | low |
| …::test_a_background_context_with_no_request_is_refused | no request header → refusal | same; the ride exception does not apply (no enclosing act) | no | low |
| …::test_erasing_with_its_own_marker_is_allowed | erase with its own marker succeeds and spends it | "an act with its own marker"; erasing is a gated act | no | low |
| …::test_a_document_that_amends_another_is_posted_with_its_own_marker | the copy with its own marker posts; only its marker is spent | per-document binding; "an act with its own marker" | no | low |
| fn::TestTheFrameworksConsequencesRideTheConsentedAct::test_a_ledger_document_the_act_creates_while_posting_rides_it | a document created during the post rides it; one marker burned | "a document the authorised act itself creates may be brought into existence as part of it"; Contracts "a ledger document the act creates while posting" | no | low |
| …::test_an_undo_cascades_into_further_undos | cancel cascades into cancels of existing documents; one marker burned | "a reversal may cascade into further reversals of documents that already exist"; Contracts "an undo that cascades into further undos" | no | low |
| …::test_a_correction_the_undo_creates_and_posts_rides_the_undo | a document the undo creates and posts rides the undo | "a document the authorised act itself creates … as part of it" | no | low |
| fn::TestACredentialThatIsNotConsentGatedIsUntouched::test_no_grant_at_all | an ungated credential's nested cancel is untouched | Contracts: "every credential whose grant does not require consent" | no | low |
| …::test_a_grant_with_consent_turned_off | consent off → untouched, including erase | same | no | low |
| project/test_consent.py::TestTheRefusalTextDoesNotLie | refusal text names the right act and does not promise a CLI the package lacks | standard expert knowledge: an error message must be true; refusal contract | no | low |
| project/test_consent.py::TestConsentVerdict | single-token verdict branches (none, live, expired, burned, wrong doc/doctype, forged, precedence) | the property, read over one marker | no (the multi-marker change must stay additive; the oracle and the alternative both keep a single string working) | low |
| project/test_consent.py::TestConsentIsBoundToTheAct | a submit marker does not authorise a cancel and vice versa; unreadable act denies | "Consent is per act"; "one act" | no | low |
| project/test_consent.py::TestACredentialCannotMintItsOwnConsent | self-minted / unprovable / unknown-principal markers refused; different hand allowed | "minted … by a hand other than the one that spends it" | no | low |
| project/test_consent.py::TestDocstatusAction | act classification for the API shapes | standard expert knowledge: the framework's routes map to acts | no | low |
| project/test_consent.py::TestDocstatusTargetDocname | document resolution, deny-biased on ambiguity | "exactly one document"; standard expert knowledge | no | low |
| project/test_consent.py::TestConsentTokenHash | hash stable, differing, non-reversible | standard expert knowledge | no | low |
| project/test_consent.py::TestConsentStatusIsGrantableAsABareMethod | the probe is on SAFE_METHODS and still needs a grant | untouched pre-existing behaviour | no | low |
| project/test_consent.py::TestMintedByIsServerBound | `minted_by` is overwritten from the session | "minted by a hand other than the one that spends it" | no | low |
| project/test_consent.py::TestConsentStatusSelfReport | posture only, never doctype names; unreadable reads unknown | untouched pre-existing behaviour | no | low |
| project/test_scope.py (all classes: classify, versioned routes, is_permitted, verbs, coercion, kill switch, rate, workflow flag, body-scoped targets, hard-deny sets, control plane) | pure scoping/classification contracts | untouched pre-existing behaviour; visible to the solver | no (the fix only adds to `consent_verdict`) | low |

## 2. Verdict

**READY.** Every graded test drives the lifecycle handler and asserts only what the stated property
yields read literally: consent per act and per document; a consequence rides only as a created
document or a reversal cascading into reversals, carrying the act it performed; several markers per
request widen nothing; a refusal is `frappe.PermissionError` and spends nothing. The two subtle rows
follow from the instruction's own words. A dispatcher-only or post-act guard would fail, but the
instruction puts the refusal inside the lifecycle and leaves the document untouched, so neither is a
correct fix. No row is "yes"; row 2 is the only "medium".

**Required: generalize**
- "The refusal is raised inside the document lifecycle, so the gate covers every way a document is
  posted, including the paths an API-key check never sees." → "No route to an act escapes the gate,
  whatever surface the call arrives through."
- "posting it, reversing it, or erasing it" → "a lifecycle act on a bookkeeping document".
- "Markers travel in the `X-Pacioli-Consent` request header." → "A request carries its markers
  itself." (that constant is already in the repository).
- "`POST /api/resource/Sales Invoice/ACC-SINV-0001` … named an existing asset depreciation schedule"
  → "posted one document while the same request also named another, pre-existing one."
- "an empty entry is never a marker" → fold into "each act still has to find the marker minted for
  it".

**Quality to tighten**
- Leniency: nothing checks a presented-but-unused marker stays unspent; add
  `burn_state(ADS, "ADS-0002") == 0`.
- Leniency: no test pins whether a created/cascaded *erasure* rides; the two `pass` patches
  disagree and both pass. Pin one.
- Leniency: the helper writes the outer docstatus after the handler, so inferring the act from
  `doc.docstatus` passes. Add a cascade before that write.
- Hint: the exception sentence duplicates the Contracts bullet and hands over the ride decision
  table; keep the bullet.
- Realism: all five traps are maintainer-plausible and reachable through `hooks.doc_events["*"]`;
  nothing planted. The visible `test_act.py` pins `_may_ride(doc, action)` and goes red for any
  correct fix (correctly ungraded) — pre-update it.

Human review: confirm test 2's custody reading — "only with that act's own authority" versus "never
survives into an act other than the one that carried it".

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
