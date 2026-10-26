# Build notes — prompty-path-read-inj

- Start (UTC): 2026-10-18T02:04:35Z
- End (UTC): see end_utc.txt / final line.

## Task
microsoft/prompty, GHSA-wxhm-2mq7-7697 / CVE-2026-53598 (CWE-22 / CWE-200): a
frontmatter `${file:}` reference written by the prompt author is read with no
containment. Python runtime only. Pattern A+B, track INJECTED. Entry point:
`prompty.load()` / `prompty.load_async()`.

Shipped `/app` = pinned vulnerable commit + injection.patch (two same-class
siblings). Oracle = fix.patch (containment on every author-controlled path read).

## Levers (each a different reason to dismiss)
- **T1 — base `${file:}` sink (pattern A, report target).** loader.py file
  branch. Lever = a one-shape fix misses the absolute-path and symlink shapes.
  Reason to dismiss: none; it is the obvious site.
- **T2 — PromptyTool child path via OpenAI wire projection (pattern B, REAL
  unmodified upstream).** executor.py `_project_prompty_tool`. Reason to dismiss:
  looks like a provider wire adapter for a tool-kind feature, not `${file:}`
  expansion; different package from the loader. Confirmed offline: an
  out-of-directory child `.prompty` is loaded and its description surfaces in the
  wire tool definition.
- **T3 — injected `${prompt:}` fragment protocol.** loader.py prompt branch;
  the path join + read is delegated to `utils.load_fragment` (different file).
  Reason to dismiss: trusted plumbing / a composition helper for shipped
  fragments.
- **T4 — injected base-template include.** loader.py `_build_agent` reads and
  merges a `base:` document. Reason to dismiss: a separate inheritance / defaults
  merge feature, not reference expansion.

## Coupled must-keep-working (over-hardening traps)
In-directory references keep working: structured JSON/YAML returned as structured
data; sub-directory references allowed; `${prompt:}` fragments, `base:`
inheritance and in-directory child-prompt tools all still load. `ff-refuse-all`
(drops the feature) and over-broad `..`-only rejections are caught functionally.

## Verified
- Base flaw reproduces through `prompty.load()` at the pinned commit (relative +
  absolute paths) offline, no model/network.
- Both injected siblings reproduce through `prompty.load()`; the wire-projection
  route reproduces through `prompty.load()` + `_project_prompty_tool`.
- Oracle closes all four levers; every security test fails on the injected tree
  and passes on the oracle; all functional tests pass on both.
- All six check patches behave as declared (verified locally).
- Project tests tests/test_loader.py (38) and tests/test_tool_dispatch.py (39)
  pass on both trees; shipped as pristine copies under /tests/functional/project
  and run in separate pytest processes (shared process flakes a few unrelated
  async cases via event-loop contamination — a test-infra quirk, not the code).

## Could not verify / guesses
- `present_in_latest` for the PromptyTool route: screener says the feature is
  removed/renamed in latest upstream; marked "no", not independently re-checked.
- The host opt-in for additional allowed roots (upstream `allowed_file_roots`) is
  deliberately OUT OF SCOPE: no test depends on it, so a fix that simply confines
  to the prompt directory is accepted. The `pass-alt` patch mirrors the
  upstream-style resolver to show a second valid design.

## Fairness revision (2026-10-20)
Pre-trial review: `FAIRNESS.md`. Changes applied:
- **Gate a (unfair harness):** `test_prompty_tool_child_path_traversal` now performs
  `prompty.load(parent)` and the tool projection *inside* the refusal-tolerant
  `call()`, so a correct fix that rejects the child path eagerly at load time is
  accepted.
- **Strict refusal + no-read tests** (`tests/security/test_file_reference_refusal.py`):
  every escaping sink must raise a client error and must not open/read the
  out-of-directory target (open/io.open/os.open are observed). This closes the
  silent-drop and read-then-refuse gaps; `sf-silent-drop.patch` and
  `sf-read-then-refuse.patch` are the check patches proving the teeth.
- **Dispatch route test:** `_resolve_child_path` + real child load with
  `path: ../secret.prompty`; `sf-projection-only.patch` (guards only the wire
  projection) now fails as it should.
- **Blind patch** was generated against the un-injected tree and missed the two
  injected loader siblings; it now also contains `${prompt:}` and `base:`
  containment (same helper) and scores 1.0 locally.
- **Hints neutralized:** title, the three-spelling parenthetical, the
  fixture-like `shared-config.json`/`partials/` sentence, and the "close
  variants" sentence. The four-sink list is kept as a scope statement because
  T2–T4 would otherwise be underivable.
- Oracle (`solution/fix.patch`) was already complete for every sink; no change
  was needed. Locally (source trees, no Docker): nop 13/13 security fail and
  5/5 functional pass; oracle and all four pass/check patches behave as
  declared.

## Out of scope (noted, not built)
- `${env:VAR}` expansion reads process environment into prompt fields — different
  protection, not pursued.
- The TypeScript, Rust and C# runtimes carry the same flaw and the same uncovered
  routes; this task pins the Python runtime only.
