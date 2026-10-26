# nuxt-s2 build notes

Start: 2026-10-25T23:09:51Z
End:   2026-10-26T00:09:50Z
Repo: nuxt/nuxt, pinned 0704254 (parent of published fix 6199633; ad624a7 is an unrelated release commit).
Pattern: A+B, track: injected (source = mined+injected).

## The defect (one line each)

- App-side: route-rule keys are added verbatim to the compiled rou3 matcher while the lookup path is
  lowercased, so a mixed-case rule key never matches any request casing (CWE-178 -> CWE-863 for an
  `appMiddleware` auth gate).
- The published fix compiles a verbatim and a folded matcher and picks one at runtime from
  `router.options.sensitive`; it also folds the keys used by the build-time prerender/manifest hooks.

## Security property (written once, general)

A route rule attaches behaviour to the application route it names. Every request the router resolves
to that route must receive exactly that rule and its values, whatever letter case the request path
uses, unless the application is configured for case-sensitive route matching -- then letter case is
part of the route identity and a rule must bind only to its own casing. (Also: rules are matched the
same way on the server, which serves the request.)

## Levers (all tested through real entry points)

- T0 (reported, pattern A, where-type baseline): mixed-case keys never match for any casing.
  Site: packages/nitro-server/src/index.ts:351-408 + packages/nuxt/src/app/composables/manifest.ts:71-79.
  Reason to dismiss: none, the report leads here.
  Tests: getRouteRules({path}) for exact/upper/lower casings, wildcard key, deprecated string arg.
- T1 (pattern B, real unmodified upstream, how-type: route where the protection never existed):
  server-side application of the same rules runs through Nitro's own case-sensitive matcher, so a
  request in another casing gets no redirect / no ssr:false. Published fix does not touch it (later
  upstream added a separate case-fold plugin, confirming it is a real gap).
  Site: packages/nitro-server/src/runtime/handlers/renderer.ts:118 + nitropack runtime route rules.
  Reason to dismiss: "that is Nitro's own matcher in a dependency; the advisory's fix is the
  app-side matcher" (the screener dismissed it the same way).
  Tests: nuxt build of a fixture, real HTTP requests with several casings.
- T2 (coupled must-keep-working, how-type): `router.options.sensitive: true` must keep keys verbatim
  and distinct; blanket folding (the tempting wrong fix) breaks it, and the switch is merged in a
  runtime template (`#build/router.options.mjs`), not at the reported site.
  Site: manifest.ts:71-79 + nitro-server template + pages/module.ts router.options template.
  Reason to dismiss: opt-in edge mode; the reported app uses defaults.
  Tests: sensitive project exact-case binding (security, fails at pinned) plus default-mode
  must-keep-working functional tests.
- T3 (candidate, DROPPED after behavioural verification): the pages module builds its own rou3
  router from the same rule keys to inject `prerender: true` pages. At the pinned commit its check
  can never fire: `findAllRoutes(...)` returns `{data, params}` entries and the hook reads
  `rules.prerender` without `.data`, so the published fix's folding there is unobservable (confirmed
  with an instrumented build: every lookup yields `{"data":{...}}`). A mixed-case `prerender: true`
  page is still prepared through the app-side matcher used by the prerender plugin, so the built
  output test is kept as an entry point of T0, not a lever, and no `miss_prerender` check exists.
- T4 (injected sibling, security): `#build/payload-rules.mjs`, a second compiled matcher for payload
  cache decisions (cache/isr/swr) built with the pre-fix pattern (verbatim keys + lowercased lookup);
  `isCachedPayloadRoute` uses it. Reason to dismiss: payload decisions look like a separate
  optimisation and "rule lookups are fixed by the shared matcher". Site: nitro-server index.ts
  payload template + nuxt/src/app/composables/payload.ts.
- T5 (injected sibling, security): `isPrerendered`/`shouldLoadPayload` fold the URL before calling the
  shared lookup, so case-sensitive routing binds the payload decision to the wrong route.
  Reason to dismiss: the helpers call the shared composable, so they look like they inherit its fix.
  Site: payload.ts.

## Candidate sibling sites considered (full list)

1. nitro-server index.ts:424-437 payload `/_payload.json` key derivation (real upstream, untouched) --
   rejected: the derived keys are only consumed by Nitro's own matcher, so a fix needs the same
   server-side lookup fold as T1 and adds no independent test (plus the same `.data` reading issue).
2. pages/module.ts:495-505 redirect stub routes (real upstream) -- rejected: vue-router matches its
   stub case-insensitively already; no observable gap in default mode.
3. pages/utils.ts:746-765 toRou3Patterns -> Nitro ssrRoutes (real upstream) -- rejected: not a route
   rule; it selects SSR vs SPA fallback, so the general property would not cover it literally.
4. payload.ts:141-155 app-manifest `prerendered` exact string compare (real upstream, present in
   latest) -- rejected: the manifest holds concrete prerendered URLs, not route-rule identity; the
   screener dismissed it for the same reason. Not a rule application.
5. Nitro's own runtime route-rules matcher -- PICKED as T1.
6. nuxt-layout.ts:63/175 direct compiled-matcher consumer -- rejected as a sibling: it is fixed by the
   same upstream template change, so it is an entry point, not a separate gap.
7. prerender.server.ts:34 direct matcher -- same as 6, and only runs during prerender.
8. Injected payload pre-fold in isPrerendered/shouldLoadPayload -- PICKED as T5.
9. Injected second payload matcher -- PICKED as T4.
10. Injected pre-fold in nuxt-layout -- rejected: only differs in sensitive mode, exactly T5's shape,
    and needs a full layout fixture to observe.
11. Injected pre-fold in the universal router (pages:false) -- rejected: same shape as T5 and harder
    to mount.

## Test plan

- Fast vitest Nuxt-environment projects (real compiled template, real composable, real router options):
  security for T0/T2/T4/T5, functional for default-mode legitimate matching, rule precedence, value
  normalisation, sensitive-mode non-leak, payload helpers.
- Build + real server project (node environment): T1 (redirect and ssr:false for several casings) and
  the T0 entry point that prepares the page route's prerendered output. One default fixture, one
  sensitive fixture.
- Copy of the project's own route-rules unit test as a functional test.

## Local validation before the gate

- pinned+injected tree: 12/12 security tests fail (all assertion errors), 14/14 functional pass.
- reference fix: 12/12 security and 14/14 functional pass.
- Each check patch run against both suites after a full rebuild:
  miss_server 2 security fail / functional pass; miss_payload_matcher 1 / pass;
  miss_payload_fold 1 / pass; miss_wildcard 1 / pass; late_fold 3 / pass;
  match_everything 6 functional fail; hardening and alt_fix both 1.0.
- Project tests on the pinned+injected tree: route-rules.test.ts 2 pass; the composables
  'compiled route rules' block 3 pass (after `nuxt prepare`).
- The patches only validate with a full `pnpm build` of every package: rebuilding one package left a
  stale matcher in another and produced a false pass/fail (late_fold run 1).

## Gate (real Docker/Harbor verifier)

- static: PASSED (only the downstream blind patch / FAIRNESS.md remain, as expected).
- nop: PASSED -- 12/12 security tests fail on the pinned+injected tree, 14/14 functional pass.
- oracle: PASSED -- 3 runs, reward 1.0, identical results (12/12 + 14/14 each).
- patches: PASSED -- 8/8 checks behave as declared:
  miss_server (2 security fail / functional pass), miss_payload_matcher (1/0),
  miss_payload_fold (1/0), miss_wildcard (2/0), late_fold (3/0),
  match_everything (2 security + 7 functional fail), hardening 1.0, alt_fix 1.0.

## Status checklist

- [x] injection.patch (T4/T5) written and validated on pinned
- [x] oracle (published fix + T1 + T4/T5 fixes) validated
- [x] instruction.md (356 words)
- [x] tests security/functional + verifier configs
- [x] environment + verifier Dockerfiles, task.toml, test.sh, score.py
- [x] gate static / nop / oracle / patches (all PASSED)
