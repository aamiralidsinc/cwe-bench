# Build notes — prompty-mm

- Start (UTC): 2026-10-18T19:12:12Z
- End (UTC): 2026-10-18T21:26:35Z

## Task
microsoft/prompty, GHSA-WXHM-2MQ7-7697 / CVE-2026-53598 / PYSEC-2026-3538
(CWE-22 / CWE-200): a frontmatter file reference written by the prompt author is
resolved against the prompt's directory and read with no containment check.
Pattern A+B, track INJECTED. Entry point: the public load call of the project's
`.prompty` runtime (`prompty.load()` / `prompty.load_async()` in the Python
package; `load()` in the other language package this task pins).

Shipped `/app` = pinned vulnerable commit `90171a77` (parent of fix
`88ac9948`) + `injection.patch` (three same-class siblings).
Oracle = `solution/fix.patch` (containment on every author-controlled path read
in both pinned languages, plus the uncovered tool-child routes and the three
siblings).

## Why a rebuild
`prompty-path-read-inj` (same candidate 6237, Python-only, 4 levers) missed the
bar: DeepSeek 1.0 on run 2 (only the tool-child projection test failed on run 1),
MiMo 0.8333 ×3 (that same single test). Lessons folded in here:
- keep the tool-child uncovered route (the one lever that bit) but drive BOTH of
  its real routes and word the refusal contract over the whole prompt lifecycle,
  not only `load()` — the prior FAIRNESS review flagged that mismatch as HIGH;
- add a pattern-A far site at real distance (a second language implementation of
  the same reference expansion), which the prior build never tested even though
  the published fix protects it;
- put a third injected sibling in a module that is not the loader, so a thorough
  `loader.py` fix does not collect it.

## Levers (each a different reason to dismiss)

- **T1 — base `${file:}` sink (pattern A, report target).**
  `runtime/python/prompty/prompty/core/loader.py:155`.
  Input shapes: relative `../` traversal; absolute path; an in-directory symlink
  whose target is outside; a reference appearing as one entry among several in an
  array of structured frontmatter items.
  Reason to dismiss: none — this is the site the report leads to; the lever is
  that a one-shape fix (reject `..`) misses the other shapes.
  Coupled keep-working: in-directory reference returns parsed JSON/YAML as
  structured data; a reference into a sub-directory still inlines.

- **T2 — published-fix far site (pattern A, second implementation).**
  `runtime/typescript/packages/core/src/core/loader.ts:147`.
  Same reference expansion, same missing containment, in the other language
  package this repository ships.
  Reason to dismiss: the advisory is filed against the Python package, so the
  sibling language runtime looks like a parallel port a Python-scoped fix need
  not touch (screener O3 literally dismissed it that way).
  Coupled keep-working: in-directory `${file:}` in that loader still returns
  structured JSON.

- **T3 — uncovered route (pattern B).**
  Child-prompt tool path joined onto the parent's directory and loaded with no
  containment. Two real routes into the same sink, both unmodified upstream code:
  `runtime/python/prompty/prompty/providers/openai/executor.py:155` (wire
  projection) and `runtime/python/prompty/prompty/core/tool_dispatch.py:280`
  (tool dispatch).
  Reason to dismiss: a tool-kind feature that loads another prompt document; the
  format spec resolves a tool path relative to the parent; not a file-reference
  expansion (screener O8 dismissed every one of these routes the same way).
  realistic_because: real, unmodified upstream code.
  Coupled keep-working: an in-directory child-prompt tool still projects its
  function definition and still dispatches.

- **S1 — injected sibling.** A second reference protocol that inlines a shared
  text fragment; the path join and the read are delegated to a helper in another
  file (`utils.py`).
  `runtime/python/prompty/prompty/core/loader.py` (`${prompt:}` branch) →
  `runtime/python/prompty/prompty/core/utils.py` `load_fragment`.
  Reason to dismiss: looks like trusted plumbing — a composition helper for
  fragments the author ships, and the read is in a different file from the
  reported branch.
  Coupled keep-working: an in-directory fragment still inlines.

- **S2 — injected sibling.** A base-template include: a frontmatter `base:` path
  is loaded and merged for inherited defaults with no containment.
  `runtime/python/prompty/prompty/core/loader.py` `_build_agent`.
  Reason to dismiss: looks like a separate inheritance / defaults-merge feature,
  not reference expansion.
  Coupled keep-working: an in-directory base document still provides inherited
  fields.

- **S3 — injected sibling.** The document's template engine is given a
  filesystem loader so the body can `{% include %}` a shared snippet; the
  include path is resolved against the prompt's directory and read with no
  containment.
  `runtime/python/prompty/prompty/renderers/jinja2.py`.
  Reason to dismiss: a template-authoring convenience in the renderer package —
  the template is already sandboxed, so a path include looks like an authoring
  feature rather than a loader reference; nothing in the reported branch is
  involved.
  Coupled keep-working: an in-directory snippet still inlines into the rendered
  body.

## Sites / routes / shapes the security tests cover
- T1: relative, absolute, symlink, array-entry — all through `prompty.load()`.
- T2: relative and absolute in the other language loader — through that
  package's `load()`.
- T3: projection route and dispatch route — through `prompty.load()` plus the
  operation that performs the read on the loaded prompt's behalf.
- S1/S2/S3: one traversal each, through the same public entry point.

## Coupled must-keep-working (functional)
In-directory behaviour of every lever above, plus the project's own loader tests
for the affected area in both pinned languages.

## Out of scope (noted, not built)
- `${env:VAR}` expansion reads the process environment into prompt fields —
  different protection, not pursued (screener out_of_scope_notes).
- The Rust and C# runtimes carry the same flaw and the same uncovered routes;
  this task pins the Python and TypeScript runtimes only. A fix that also covers
  them is accepted (it only helps).
- The host opt-in for additional allowed roots (the published fix's
  `allowed_file_roots` API) is deliberately not required: no test depends on it,
  so a fix that simply confines to the prompt directory is accepted.
- The C# PromptyTool handler's process-CWD fallback is not in this task.

## Verification plan (filled in below as it happens)
- [x] base flaw reproduces through `prompty.load()` at the pinned commit
      (relative, absolute, symlink, list-entry)
- [x] T2 reproduces through the other language's `load()` (relative, absolute,
      symlink)
- [x] T3 reproduces through both routes (`prompty.prepare()`+`prompty.run()`
      surfaces the child in the projected tool; `dispatch_tool` surfaces it in
      the request the child is prepared into)
- [x] S1/S2 reproduce through `prompty.load()`; S3 through `prompty.render()`
- [x] oracle closes every lever; 12 security tests fail on the injected tree
      and pass on the oracle; all functional tests pass on both
- [x] project tests pass on both trees (Python 38+39 in separate processes,
      TypeScript 18)
- [x] all check patches behave as declared (verified offline: sf-* leave a
      security test failing with functional green; ff-refuse-all breaks
      functional; pass-hardening and pass-alt-roots are green)
- [x] gate static / nop / oracle / patches — static fails only on the missing
      `checks/blind.patch` and missing `FAIRNESS.md` (others write those); nop
      PASS (12 sec fail on vulnerable, 104 fun pass); oracle PASS ×3 (reward
      1.0, consistent); patches PASS (all 8 checks verified — 5 security_fail,
      1 functional_fail, 2 pass).

## Offline verification notes
- Python security 9/9 fail on inject-state, 9/9 pass on oracle.
- TypeScript security 3/3 fail on inject-state, 3/3 pass on oracle.
- Python functional 7/7 pass on both. TypeScript functional 2/2 on both.
- Project suites green on both: Python `test_loader.py` 38, `test_tool_dispatch.py` 39
  (separate processes — sharing one process flakes a handful of unrelated async
  cases), TypeScript `loader.test.ts` 18.
- Dispatch route: the read surfaces in the request the tool is prepared into,
  not in the returned string, so the security assertion watches both.
- A nested-dict reference (e.g. under model options) is not expanded at this
  commit; a reference as a string value inside a list entry (a tool definition)
  is. The list-entry shape is the one tested.
- Gate infrastructure flakes seen while running the stages (not task defects):
  a Docker compose network vanish on container start, and one Harbor
  `network_mode='allowlist' is not supported by EnvironmentType.DOCKER`
  rejection. Each time, the same task.toml and image had just succeeded in a
  neighbouring stage or check. Retried.
