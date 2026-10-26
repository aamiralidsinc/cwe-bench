# pv-pacioli — build notes

- **Start (UTC):** 2026-10-23T03:26Z
- **End (UTC):** 2026-10-23T04:00Z
- **Advisory:** GHSA-3HJ7-6VMJ-H8V4 / CVE-2026-107841 (john-broadway/pacioli, CWE-863)
- **Pinned (vulnerable) commit:** 3262d87a88df3a463501b1ca767472c7f42337da — verified as the parent of
  the published fix f3c7219f5dde6050bd7921e0ac55afd02771250c (`git rev-list --parents`).
- **Track:** injected (two realistic sibling gaps added to the pinned tree; see "Injected siblings").

## What the product is

`guard/pacioli_guard` is a Frappe/ERPNext app. When a credential's grant sets `require_consent`, an
act on a document (submit / cancel, plus the erasing act this tree also gates) is refused unless the
request presents a single-use *Pacioli Consent Marker* minted for that exact document and that exact
act by a different principal. The gate runs on `doc_events` handlers, so it covers every ORM path
(REST v1/v2, `frappe.client`, the desk, background jobs, the console). The framework's own
consequences of an authorised act — ledger documents the act creates and submits inside the same
write — are allowed to "ride" that act, because a human cannot mint a marker for a document whose
name does not exist until the act is already running.

## The flaw at the pinned commit

`_may_ride` (`guard/pacioli_guard/act.py:282-284`) answers the ride question with a bare
`if action == CANCEL: return True`. The stamp it reads, `_CONSENT_ESTABLISHED`, is a bare `True`, so
the ride decision can see *that* an enclosing act was authorised but never *which* act it was
authorised for. A marker minted to post one document therefore licenses a lifecycle cancel of a
different, pre-existing, caller-named document performed inside that post.

## Levers

One line each; every one is covered by the single property in `instruction.md`.

1. **Act-crossing on the ride path (how-type).** The ride predicate must know *which* act the
   enclosing authority was for, and the stamp that carries custody must carry a value, not a truth.
   Fixing it needs the mechanism understood end to end (`_flag_get`/`_flag_set`, the frame walk, both
   stamp sites), not just the `if` at `act.py:282`. Reason to dismiss: the reported site looks like a
   one-line change and the function's own docstring frames the cancel branch as a deliberate residual.
2. **Custody across a cascade (how-type, shape trap).** The authority a ridden consequence carries is
   *its own* act, not the act that authorised the act it rode. A fix that propagates the enclosing act
   keeps the crossing open one level deeper (an undo → a created submit that rides → a cancel of a
   pre-existing document). Reason to dismiss: the code comment tells you custody "must keep riding the
   original act", so propagating the original act looks like exactly the right thing to do.
3. **One request, several markers (how-type, far site, coupled).** Once a crossing is refused, a
   caller-steered consequence can no longer be performed inside the enclosing request unless that
   request can present an authorisation for it as well. The transport reader (`act._presented_token`,
   `act.py:315-327`) and the pure core that compares the token (`scope.consent_verdict`,
   `scope.py:1154-1156`) both assume one marker per header. Reason to dismiss: it is a separate
   module and reads like a separate feature; the pure core "already binds correctly".
4. **The erasing act (injected sibling, pattern B-shaped).** A third gated lifecycle event whose ride
   branch admits any enclosing governed act. Reason to dismiss: erasure is a different act from the
   one in the report and nothing in the report is about it.
5. **A marker is bound to the document it names (injected sibling, wrong-object).** The record loader
   follows one step back to the document an amendment was made from and rebinds the marker to the
   copy. Reason to dismiss: an amended copy reads as the same business document.

## Injected siblings — full candidate list and why the picks won

Candidates found by reading `guard/` (act.py, enforce.py, api.py, hooks.py, scope.py, the marker
Doctype controller) and the screener's O8/O8b leads:

| # | candidate site | kind | verdict |
|---|---|---|---|
| 1 | `hooks.py` doc_events registry + a new act handler (`on_trash`) with a ride branch copied from the cancel branch | new gated act, permissive ride | **PICKED.** Real (upstream later added exactly this gate), reachable through `doc_events`, its ride rule is how-type (which enclosing acts may license an erasure), and it sits where the published fix never touches (new handler + new registry entry). |
| 2 | A "preview" gate (O8b #2) that rides an enclosing act and stamps a bare `True` | new gated act | Rejected: a preview is rolled back, so no protected outcome is reachable; a test could only assert an internal stamp, which is not a behavioural property. |
| 3 | `_inside_another_write` returning a bare `True` from a second frame recogniser | second frame recogniser | Rejected: with an act-aware predicate, a bare-`True` stamp is read as "an act we do not know", which already refuses — the gap would be unobservable (fail-closed), so no security test can fail on it. |
| 4 | `enforce._claim_consent` read-then-write instead of the conditional UPDATE | single-use spend | Rejected: the pinned code already documents this as fixed for floor-audit F4; re-breaking it would contradict the file's own text (deceptive). |
| 5 | `PacioliConsentMarker.before_insert` fill-when-blank on `minted_by` | minter separation | Rejected: the controller's own docstring says "OVERWRITE, never fill-when-blank"; anything I write there is a planted contradiction. |
| 6 | `enforce._consent_record` following `amended_from` one step and rebinding the marker to the copy | wrong object / producer | **PICKED.** A real, plausible product argument (operators re-mint per correction), in a different module, on the producer side of the check, and the published fix never touches `enforce.py`. |
| 7 | a per-request cache of "this document was consented" in `frappe.local` | cache / state | Rejected: the module's own docstring argues at length against per-request state; writing it would look planted. |
| 8 | `_gated` skipping consent for doctypes outside the grant's resource allowlist | applicability | Rejected: a different protection (which documents a grant may touch), not act binding; it would need a second property. |
| 9 | `Document.discard` gate | new gated act | Rejected: a discard only abandons a draft and the README publishes it as deliberately out of scope, so the property could not cover it without contradicting documented design. |
| 10 | cancel-under-cancel of a caller-named pre-existing document (screener O8) | uncovered route | Rejected: the project states it is load-bearing for UNDO and has no signal to narrow it; making it a required route would make the oracle break the coupled functional behaviour. |

Pick 1 beat 2/3/5/7/9 because it is the only new-act candidate whose *ride rule* is decidable from
the property and whose bypass is observable through the real dispatch path. Pick 6 beat 4/5/7/8
because it is the only one that weakens document binding without contradicting a comment already in
the tree, and it lives in a module the published fix never edits.

## Sites, routes and input shapes the security tests cover

- Route per site: the handler registered under `hooks.doc_events["*"]` (resolved at test time, so an
  unregistered gate is a missing handler, not a pass).
- Shapes: single marker; several markers separated by whitespace; several separated by commas with
  the matching one last; stray separators (empty entries); a stamp carried across a two-level chain;
  a document that amends another; a pre-existing document named by the caller vs a document the act
  creates.

## Coupled must-keep-working behaviour (functional tests)

- A document with its own marker is submitted / erased and the marker is spent exactly once.
- A ledger document the authorised act creates while posting rides it (no marker of its own).
- An undo cascades into further undos of documents that already exist.
- A credential with no grant, and a grant with consent off, are untouched at any nesting.
- A document that amends another is submitted normally when *it* has its own marker.

## What I verified locally (before the gate)

- The attack reaches the gate through the real dispatch path on the pinned tree: submit → cascaded
  cancel of a caller-named pre-existing document is ALLOWED; two-level custody crossing is ALLOWED;
  cascaded erase under a governed submit is ALLOWED; a marker for the amended-from document
  authorises the copy (and is spent).
- The oracle refuses all four and still allows every functional behaviour above.
- The project's own suite (438 tests) passes on both the injected pinned tree and the oracle tree.
- `git rev-list --parents` confirms the pinned commit is the fix's parent; `git fetch --depth 1
  origin <sha>` works, so the image can pin it.

## What I could not verify

- ERPNext itself is not in this repository, so the real-world cascades the docstrings cite
  (`Sales Invoice.on_submit` → depreciation schedule cancel, asset-sale) were not exercised; the
  tests drive the gate through frappe's document lifecycle as the project's own tests do.
- Whether the target models fail the bar is for the trial stage, not for me.
- `repo_mb` / tiny-repo status: the checkout is ~16 MB, 176 tracked files.

## Out of scope, noticed

- The published fix commit also bundles an unrelated broker receipt feature
  (`broker/pacioli/receipt.py`, `doctor.py`, `cli.py`); not used or built on.
- `flags.ignore_validate` writes and raw `db_set`/SQL skip the lifecycle entirely; documented
  residuals, different mechanism, not built on.

## Gate runs (this build)

| stage | result |
|---|---|
| static | FAILS only on `manifest.patch_checks has no expect=pass patch with kind='blind'` — the blind patch is written after this build, by the pipeline, from `instruction.md` alone. Every other static check passes (leaks, conformance, patch files present, no exact-status assertions, no hidden-test copies in `environment/`). |
| nop | PASSED — 8 security tests, all failing on the pinned+injected tree; 296 functional tests, all passing. |
| oracle | PASSED — 3 runs, reward 1.0, identical results. |
| patches | PASSED — 13 checks: 2 `pass` (hardening, alternative design), 9 `security_fail` (one per lever and per wrong-fix class), 2 `functional_fail`. |

## Decisions worth recording

- **The functional group also runs the project's own pure-core suites** (`test_consent.py`,
  `test_scope.py`, 285 tests) as a copy, so a fix that changes the pure API's stated behaviour is
  caught. The project's `test_act.py` is deliberately NOT run: it calls the ride helper directly and
  asserts the pinned predicate's shape, so it has to change with any correct fix — running it would
  make the task unfair.
- **Project tests at the pinned+injected commit:** the full 438-test suite passes in the image (the
  injection updates the one registration assertion that names the gated events, as the maintainer who
  added the third gate would have).
- **Register rows:** none. The advisory's screener listed no uncovered routes for this candidate, and
  the one route it did consider (cancel-under-cancel of a caller-named document, O8) is a published,
  deliberate residual that cannot be closed without breaking the undo cascade the coupled functional
  test requires — it is recorded as rejected above, not built.
- **Instruction length:** 487 words.

