# livewire-ds — build notes

Start: 2026-10-24T05:17Z
End:   2026-10-24T06:22Z

## Levers (one line each)

- **T1 (A, reported site; how)** — the page-address parser splits a bracketed name into dot
  segments and creates each container as a plain `{}`, so a segment such as `__proto__` or
  `constructor.prototype` at any nested position writes onto a shared prototype; the same parse
  reached through a named prefix or an index container behaves the same. js/plugins/history/index.js:260-274.
  Reason to dismiss: the top-level object is already null-prototype and carries a comment saying
  that is what stops the injection, so a guard that only covers the reported direct nesting looks
  complete.
- **T2 (injected sibling; how)** — a second address feature reads the page fragment with its own
  segment walker and the same unfiltered container building. js/features/supportHashQueryString.js:36-50.
  Reason to dismiss: the report's example is the query part of the address, and the fragment
  feature is a separate module with its own parser.
- **T3 (A, coupled must-keep-working; how)** — nested objects and lists written in bracket
  notation, scalar and empty values and names that only resemble a prototype name must keep
  round-tripping. js/plugins/history/index.js:225-303. Reason to dismiss: refusing all bracketed
  parameters is the smallest change that stops the attack.
- **Coverage (A, far sites; where)** — every consumer of server instructions reads a plain object
  whose prototype is shared, and the saved-state path copies inherited names back into the DOM.
  js/features/{supportMorphDom,supportJsEvaluation,supportScriptsAndAssets,supportRedirects,
  supportNavigate,supportFileDownloads,supportDispatches,supportListeners,supportLaravelEcho}.js,
  js/request/commit.js:122, js/component.js:169-181. These are closed by a complete address fix,
  so they are covered by security tests but are not separate levers (a patch that removes one
  guard still passes once the address parser refuses every shape). The saved-state writer is the
  producer-off-the-reader's-path case and is tested through a navigation re-save.

## Sites/routes/shapes the security tests cover

- Parsed address: nested prototype segment, constructor chain, named prefix, index container,
  a second bound property name; each drives a real page boot and the shipped public history API.
- Fragment address: nested, constructor chain, script, and a second bound name.
- Consumers: rendered markup, expression, script, callable, dispatch, listener, Echo
  subscription, redirect, forced visit, download, returned value, and replay from saved state.
- The refusal contract is "skipped, page keeps working" — no test asserts a status or an error.

## Verified locally (before the container gate)

- Pinned+injected tree: 20/20 security fail, 13/13 functional pass, project suite 18/18 pass.
- Reference fix: 33/33 pass, project suite 18/18 pass; identical JUnit across repeats.
- Wrong-fix patches: miss_nested_shape 18/20 security + 13/13 functional; miss_constructor_chain
  18/20 + 13/13; miss_hash_source 16/20 + 13/13; check_after_parse 0/20 + 13/13;
  refuse_brackets 20/20 + 9/13; crash_on_bracket breaks functional; alt_fix and
  alt_safe_containers 33/33; hardening 33/33.
- `alt_safe_containers` is the upstream parser change without its explicit name guard: own
  containers plus an own-property test are sufficient in this parser, so the guard is
  defence-in-depth and the tests must (and do) accept the guard-free design.
- Verifier layout simulated outside Harbor: workspace copy + pristine dependency tree at
  /opt-equivalent + the real test.sh command lines; pinned → 20 security fail / 13 functional
  pass / 18 project pass, reference fix → all pass.
- Container gate under a task-private dockerd (the shared daemon's /info endpoint was wedged):
  static PASS; nop PASS (20 security failing, 31 functional passing); oracle PASS (3 identical,
  reward 1.0); patches PASS 9/9.
- The first container run exposed a Node-22 difference: the download path takes `window.webkitURL`
  when present, and a recorder installed only on the global URL object was not the one the page
  used. The verifier setup now registers the recorder as `webkitURL` too; the download tests then
  behaved identically on the pinned and fixed trees.

## Could not verify / guesses

- `supportHotReloading.js` is not imported by js/features/index.js in this bundle, so its effect
  handler is unreachable from a page boot and has no behavioural test. It is a published-fix site
  only in the preview/Electron entry.
- The inherited `url` binding (js/features/supportQueryString.js:10) cannot be observed
  independently in jsdom: poisoning that key puts an object on the shared prototype that the DOM
  URL implementation reads as its own parse state and crashes before the handler's own effect is
  visible. The reported parser route is covered directly instead.
- js/utils.js dataSet and the lazy-loading memo lookups are real inherited-property readers but
  are not reachable from the page address; they were left out rather than tested through
  application glue.
- The PHP/Dusk browser tests for the query-string feature need headless Chrome and a Laravel test
  application; the affected code is the client bundle, so the project's own JavaScript unit suite
  is the project test that runs.
- Repo size and whether the advisory text names the far sites were not measured.

## Scope notes

- dist/ build output is not part of the artifact and no test imports it; only js/ sources are
  exercised.
