# stk-dompurify-ghsap98j — build notes

Start (UTC): 2026-10-26T02:07:08Z
End (UTC): 2026-10-26T03:20Z (gate stages: static PASS, nop PASS, oracle PASS 3x1.0; patches pending)

## Levers, one line each

- **T1 / concept C1 (advisory route, `both`)** — a hook detaches the element it was called on while a
  live tree is sanitized in place; the detached subtree keeps its queued `on*` handler. Guard sites:
  `src/purify.ts:1751-1830` (element hooks) and `src/purify.ts:2055-2168` (attribute hooks), with the
  neutralizer at `src/purify.ts:1310`. Reason to dismiss: hooks are trusted and the node is gone from
  the returned tree.
- **T2 / concept C1 (`mimo`, uncovered upstream)** — a hook detaches an *ancestor* of the node it was
  called on; that node keeps its parent, so a per-node detach check reports success while the armed
  subtree is skipped (`src/purify.ts:2057,2168`, harvest at `2536`). Reason to dismiss: the report
  describes removing the node the hook was called on; this is a different shape.
- **T5 / concept C1 (`deepseek`, published fix far site)** — the same hook removal inside a shadow
  root attached to the live tree, reached through the separate recursive shadow walk
  (`src/purify.ts:2176-2198`, `2433,2271`). Reason to dismiss: shadow content is assumed inert.
- **T3 / concept C2 (`deepseek`, published fix far site)** — the abort teardown detaches the live
  root's children before stripping them, so originals not yet visited stay armed after the throw
  (`src/purify.ts:1190-1220`, abort barrier at `2435,2521`). Reason to dismiss: the call throws and
  the root is emptied, so the tree looks fail-closed.
- **T4 / concept C3 (`both`, uncovered upstream)** — a hook re-enters sanitize; the nested call
  replaces the public removal inventory before the outer call drains it, so force-removed subtrees
  are never neutralized (`src/purify.ts:1138` records, `2383` replaces, `2536` harvests). Reason to
  dismiss: the nested call looks self-contained and its own harvest is assumed to clean up.

Concepts (independent edit sites in the reference fix): C1 = {T1,T2,T5} (per-hook containment guard);
C2 = {T3} (strip before the abort teardown); C3 = {T4} (neutralize at the point of detach). The
reader's T1/T2 collapse into one concept because one containment guard closes both; T4 was kept
because the reference deliberately gates the per-hook guard on registered hooks, so a re-entrant call
still loses the inventory until removals are neutralized at `_forceRemove`.

## Verified

- The template-content variant of the shadow trap was dropped from the security cases: `template.content` is inert, so a
  careful engineer could correctly dismiss it under the report's "caller's live tree" wording. The attached-shadow-root
  case (genuinely live) stays as T5.
- Every trap was reproduced behaviourally on the pinned build (`dist/purify.cjs.js` built from
  `src/purify.ts` at 0cae518) through the public API, with original-node attribute references held by
  the test: 11/11 security cases fail on the pinned tree.
- The reference fix (`solution/fix.patch`) passes 11/11 security and 14/14 own functional cases and
  the project's own pinned jsdom QUnit suite (933 tests / 1155 assertions).
- Each per-concept miss patch fails only its own concept's security tests, with all functional tests
  passing: miss_hook_detach (8/8 hook-detach cases fail), miss_abort (1 abort case fails),
  miss_removal (2 re-entrant cases fail).
- Recall: `upstream_fix.patch` (a9ca1e5+b9b9d80 source diffs) fails the two ancestor cases and
  passes functional; `upstream_first_fix.patch` (a9ca1e5 alone) fails 10 security cases.
- Alternative design (`alt_correct_fix.patch`, snapshot + post-walk sweep) and hardening
  (`hardening.patch`, reference + full departed-node sweep) both score 1.0.
- The over-broad patch (strip surviving nodes too) fails a functional case.
- Gate: static PASS; nop PASS (11 security tests all fail on the pinned code; 947/947 functional, all names unique).
  QUnit reuses test names across modules, so every project testcase is suffixed `#<n>`: otherwise the
  scorer's `classname::name` key would collapse duplicates and could hide a failing case.

## Could not verify

- The advisory text was read from the GitHub advisory API; the advisory-to-commit mapping is
  inferred from the source changes and the commit order, not from a per-advisory diff hunk.
- Upstream `present_in_latest`: read at HEAD b7e0edc; `_handleHookDetachedNode` still tests only the
  called node's own parent, so the ancestor route is still open (see the register rows).
- Queued-event execution is not observable under jsdom; cases assert the attribute invariant, as the
  project's own in-place tests do.
