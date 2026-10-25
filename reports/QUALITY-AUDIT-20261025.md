# Breaker quality audit: sibling injection vs stacking (2026-10-25)

Measured against the metrics agreed in `docs/BATCH-METRICS.md`. Scope: every both-model breaker in the ledger on
2026-10-25 (25 tasks): 12 sibling injection, 8 stacking, 5 precision validation (built by the sibling builder, reported
separately). Each breaker was reviewed by an Opus 5.5 (high) reviewer against one shared brief; upstream fixes were
read on GitHub for the open-internet check. Evidence: `reports/quality-audit-20261025/` (brief, data pack, one review
file per breaker).

## Headline comparison

| | Sibling injection (48 trialled) | Stacking (30 trialled) |
|---|---|---|
| Total both-model breakers (% of trialled) | 12 (25%) | 8 (27%) |
| Single-test breakers: one test decides the result (% of breakers) | 6 (50%) | 6 (75%) |
| Functionality breakers: failed only by breaking legitimate use (% of breakers) | 3 (25%) | 2 (25%) |
| Core-strong: security miss not covered upstream (% of trialled) | 7 (15%); 5 (10%) first-build | 5 (17%) |

Single-test: sibling hubuum, jetty, litellm, mockoon, openbao, tinacms; stacking dagu, filebrowser, mistral-rs,
senaite, tensorflow, vikunja. Functionality: sibling hubuum, litellm, openbao; stacking lemur, mistral-rs. The rows
overlap (a task can be both). Precision validation (sibling builder, 5 breakers): 4 single-test (80%), 0 functionality.

## Summary

1. **Strong breakers (all of E): 1 of 25.** Only stk-filebrowser passes every check, and it is weak: 5 of its 6 runs
   fail on a status code (500 instead of 4xx). The main reason almost nothing passes is **e3, fairness READY with no
   open human question, which fails on 24 of 25**. That is a process gap (questions and required rewordings left
   open), not proof the tasks are bad.
2. **Core-strong breakers** (a security miss decides it, and the public upstream fix does not cover it; e4 + e5):
   - **stacking 5 of 30 stacked tasks trialled, 17% (95% range 7–34%)**: dagu, filebrowser, senaite, tensorflow, vikunja;
   - **sibling injection 7 of 48, 15% (7–27%)**: electron-builder, grav, jetty, mockoon, seaweedfs, siyuan, theia;
     only **5 of 48 (10%)** without the dropped hardening step (grav and jetty were hardened after a solve);
   - **precision validation 1 of 61 built (pv-device-builder)**.
   The two pipelines are **level** on this measure; the samples are far too small to separate them.
3. **Injected sites rarely decide a breaker.** In 10 of the 12 sibling breakers the injected siblings were fixed in
   every finished run (or decided almost nothing); the failures came from real upstream code (routes the upstream fix
   also misses, or coupled keep-working rules). theia's injected T10/T11 are the clear exception, protobuf.js partly. In precision validation
   the injected site decided 2 of 5. **Both pipelines win the same way: by finding real routes the upstream fix
   misses.** The injection step adds build cost and realism risk (5 of 17 injections read as partly planted) without
   adding the difficulty.
4. **Five breakers are not security breakers.** lemur, mistral-rs (stacking), hubuum, litellm, openbao (sibling) fail
   only because the fix broke legitimate use. Fair, but weaker; the client may not want them as security tasks.
5. **Fragile breakers are common**: one test decides the result in 6 of 8 stacking, 6 of 12 sibling and 4 of 5
   precision-validation breakers.

**Recommendation:** the two pipelines are close to a tie on yield (25% vs 27% both-model; 15% vs 17% core-strong)
and cost (≈40 agent-hours per core-strong breaker each). The lean is toward **stacking**, for two smaller reasons: its
breakers are all first-build (two of sibling's seven core-strong ones came from the dropped hardening step, leaving
10% vs 17%), and sibling's distinctive step, injection, rarely decides a breaker. Against stacking: more of its
breakers rest on one test (75% vs 50%). Treat injection as optional rather than the main lever. Before scaling either pipeline, fix the shared process gaps below,
because they cap the strong-breaker count of both.

**Correction (2026-10-25, same day):** the first version counted 60 sibling tasks; that mixed the sibling batch (48
`-ds` tasks, all 12 breakers) with the older `-inj` round (11 tasks, earlier builder, 0 breakers) and one stacking
task (stk-nova) whose task file says "injected". Sibling now uses 48 and stacking 30. The stacking cost lead in the
first version (≈40 vs ≈49 hours) disappears.

## Shared process gaps (fix before scaling)

| Gap | Seen in | Effect |
|---|---|---|
| Fairness `NEEDS_HUMAN_REVIEW` left open; "Required: generalize" rewordings never applied to the instruction | 24 of 25 | e3 fails; hints stay in instructions (B7 "leaky" in 6) |
| Fairness not re-run after a test fix | dagu, siyuan, senaite, svgo | the official verdict is stale (siyuan also has a live fixture defect: snippet fixtures leave `Enabled` false) |
| Blind fix never ran or broke: the script expects `/app`, tasks use `/workspace` | all stacking; most sibling | solvability (B8) rests on the gate alone |
| Gate marker predates the upgrade that added the decisive test | electron-builder, hubuum, mockoon | the decisive tests were only checked by targeted runs |
| Stacking control never gated or trialled | 6 of 8 stacking breakers (dagu, gitpython, lemur, mistral-rs, vikunja; langflow sound but untrialled) | stacking lift (D1) unmeasured for them |
| Trap origin labels wrong in the manifest | vikunja | trap-origin counts must be checked against upstream commits |
| Short trial clock | litellm (MiMo timeouts at 2 h) | MiMo's 0/3 depends partly on the clock |

## Metrics by pipeline

| Metric | Sibling injection | Stacking | Precision validation |
|---|---|---|---|
| A1 funnel | sibling batch (`-ds`): 48 trialled → 12 both-model (116 injected builds of all eras, 93 gated sound) | 65 built (incl. controls) → 54 sound → 30 stacked + 23 controls trialled → 8 both-model | 61 built → 7 imported (both-fail on Actions) → 5 hold after audit and fairness |
| A2 both-model yield per trialled | 25% (15–39%) | 27% (14–44%) | 8% of built (4–18%) |
| A3 agent-hours per both-model breaker (builder + trials) | ≈24 | ≈25 | n/a (only survivors imported) |
| A3 per core-strong breaker | ≈40 | ≈41 | — |
| A5 repair burden on breakers | 9 upgraded, 5 fairfixed, 2 hardened | 2 test fixes, 1 fairfix | 1 test repair (svgo) |
| B1 decisive type: security miss / regression only | 9 / 3 | 6 / 2 (filebrowser mostly contract) | 5 / 0 |
| B2 one test decides | 6 of 12 | 6 of 8 | 4 of 5 |
| B5 audits: all trusted, mostly high (e2) | 12 of 12 | 7 of 8 (senaite all medium) | 0 of 5 (no code saved: medium by construction) |
| B5 fairness READY, no open question (e3) | 0 of 12 | 1 of 8 | 2 of 5 (svgo judged on its repaired tests) |
| B6 upstream fix does not cover the decisive trap (e5) | 7 of 12 | 6 of 8 | 1 of 5 |
| B7 instruction hints: none / some / leaky | 1 / 7 / 4 | 2 / 5 / 1 | 0 / 4 / 1 |
| D2 injected code reads as real | 9 plausible, 3 mixed | n/a | 3 plausible, 2 mixed |
| D1 stacking lift | — | on 23 stacked/control pairs: both-model fail 3 vs 0; DeepSeek fails 5 vs 2, MiMo 7 vs 0 | — |
| E strong breakers | 0 | 1 (filebrowser, weak) | 0 |
| e4 + e5 core-strong | 7 (5 first-build) | 5 | 1 |

### Diversity (C1–C4)
- **Languages:** sibling: TypeScript 4, Go 3, Java, PHP, Rust, Python, JavaScript. Stacking: Go 3, Python 3, Rust,
  C++. Both are spread; neither repeats a repo among its breakers.
- **Mechanisms:** both cover authz, path traversal, SSRF, auth bypass and information leaks; sibling adds prototype
  pollution and trust-boundary bypass; stacking adds option injection and a C++ null dereference.
- **Most common decisive pattern, both pipelines: "missed indirect route / second copy"** (sibling 6 of 12,
  stacking 3 of 8, precision validation 2 of 5). Second: "over-blocked legitimate use" (the regression breakers).
- **Near-duplicates (C3):** lemur and mistral-rs (both SSRF fixed by over-blocking a stored or shared value) are the
  closest pair. No breaker is a re-skin of another.

### Single-model breakers (F)
| | Sibling injection | Stacking | Precision validation |
|---|---|---|---|
| F1 DeepSeek-only / MiMo-only | 7 / 3 | 3 / 4 (+2 controls DeepSeek-only) | 1 / 0 |
| F2 both-model + single-model per trialled | 22 of 48 (46%) | 15 of 30 (50%) | — |
| F4 near-miss (the solving model failed first, solved on run 2+) | 5 of 10 (airflow, flyto, keras, knowns, pimcore) | 2 of 7 (mlflow, uri-js) | 1 (spring-ws, run 4) |
Single-model failures are audited; their fairness has not been reviewed, so F3 is not assessed.

## What would change the recommendation
- Stacking yield on a second batch falling to sibling's level (the 95% ranges overlap).
- Controls for the 6 uncontrolled stacking breakers solving as often as their stacked twins (no stacking lift).
- A sibling batch built with injection off performing the same: that would confirm point 3 directly.

## Per-breaker detail

e2 = every failing run trusted, mostly high; e3 = fairness READY with no open question; e4 = a security miss decides
it; e5 = the public upstream fix does not cover the decisive trap. Full reviews: `reports/quality-audit-20261025/review/`.

### Stacking

| Task | Language / mechanism | Decisive failure | Upstream fix covers it? | Hints | One test decides? | e2 e3 e4 e5 | Main concern |
|---|---|---|---|---|---|---|---|
| stk-dagu-ghsaph8x | go / path traversal (percent-encoded entry name decoded and joine | missed indirect route | uncovered | some | yes | ✓ ✗ ✓ ✓ | Single test decides all 6 runs (every run 0.8, one test short): fragile. |
| stk-filebrowser-ghsa8wc8 | go / path traversal / scope escape via symlinks (link-following w | wrong refusal status (error swallowed by aggregation) | uncovered | some | yes | ✓ ✓ ✓ ✓ | 5 of 6 runs are contract-only: the outside victim is unchanged and the only failure is 500 instead of 4xx on the copy route; this breaker is mostly decided by a |
| stk-gitpython-ghsawvpp | Python / argument/option injection leading to command execution and a | missed option alias (DeepSeek); screened names not values (MiMo) | partly | some | no | ✓ ✗ ✓ ✗ | Open internet: every decisive trap has a public upstream fix - T1/T2 in the advisory fixes, T5 (and T6) in later commit 1b0d2d9b shipped in 3.1.62+; a model tha |
| stk-lemur-5644 | Python (Flask) / SSRF via a stored ACME directory URL (allowlist bypass on wr | over-validated stored data | partly | none | no | ✓ ✗ ✗ ✓ | Pure keep-working breaker: 0 security misses in 6 runs. Reward 0 comes only from functional over-fix; models secured every route. |
| stk-mistral-rs-21576 | Rust / SSRF + local file read via request-supplied media/attachment | over-blocked legitimate use (changed shared public API) | covered | none | yes | ✓ ✗ ✗ ✗ | Pure keep-working breaker: 0 security misses. The only uncovered-upstream element (injected T8) was solved by every model. |
| stk-senaite-core-4280 | Python 2.7 / Plone-Zope / missing authorization: a data-returning route invokes caller | missed indirect route (state change through a read route) | uncovered | some | yes | ✗ ✗ ✓ ✓ | Single trap decides every run (the T9 pair = one fixture method, two callers): fragile. |
| stk-tensorflow-ghsajjr8 | C++ / null pointer dereference: a model-supplied tensor with no da | missed setup-stage route (absent optional input) | partly | leaky | yes | ✓ ✗ ✓ ✓ | Fragile: 2 tests decide everything, and one security test (Reshape_OmittedShapeInput) carries 7/8 runs. 4 of 8 runs were one test short of 1.0. |
| stk-vikunja-ghsaxv7q | Go / authentication bypass / account takeover through OIDC email- | missed existing account-state protection on the matched record | partly | some | yes | ✓ ✗ ✓ ✓ | The decisive T4 depends on a vague sentence ('protections the product already applies'). Reading a provider-verified address as satisfying local confirmation is |

### Sibling injection

| Task | Language / mechanism | Decisive failure | Upstream fix covers it? | Hints | One test decides? | e2 e3 e4 e5 | Main concern |
|---|---|---|---|---|---|---|---|
| electron-builder-ds | TypeScript/Node / credential leak on cross-origin redirect + secret in diagnos | missed indirect route (second redirect path in a separate subsystem) | partly | some | no | ✓ ✗ ✓ ✓ | Injection contributed nothing: all 6 runs fixed the 3 injected Gitea traps. The breaker rests on real upstream code (differential downloader) and published-fix  |
| grav-ds | PHP (Twig) / information exposure: sandbox escape of config through templ | missed alias/derived copy of protected data | uncovered | none | no | ✓ ✗ ✓ ✓ | Not a first-build breaker: v1 was solved by both models and v2 by DeepSeek. The decisive levers (theme alias, container self-alias, ambient variables) were adde |
| hubuum-client-rust-ds | Rust / info leak: server content/secrets in default Display/Debug/s | over-redacted coupled identifier | covered | some | yes | ✓ ✗ ✗ ✗ | Single functional test decides all 7 runs, and every run is otherwise perfect (24/24 security). |
| jetty.project-ds | Java / authentication bypass: lossy secret representation lets a di | missed producer off the check path (config loader normalises the secret) | uncovered | some | yes | ✓ ✗ ✓ ✓ | Hardened breaker, not first-build: v3 was solved by DeepSeek 3/4 and MiMo 1/1. The decisive lever was added afterwards and tuned to 'DeepSeek's known miss'. |
| litellm-ds | Python (FastAPI) / SSRF with forwarding of configured credentials to a caller-c | dropped operator opt-in exception (over-blocked legitimate use) | covered | leaky | yes | ✓ ✗ ✗ ✗ | One functional test decides every graded run, and 5/6 runs were one test from 1.0. |
| mockoon-ds | TypeScript/Node / missing authentication on the management API + credential re | missed value copy outside the redacted slot | partly | leaky | yes | ✓ ✗ ✓ ✓ | Very thin margin: rewards 0.926-0.963. One upgrade-added test (T8) decides every run and is the only decider in 2. |
| openbao-ds | Go / authorization pattern injection via identity-template substi | over-blocked legitimate use (global metacharacter set instead of per-matcher) | covered | leaky | yes | ✓ ✗ ✗ ✗ | No security miss anywhere: the breaker is entirely keep-working regressions; the injection design (2 injected siblings, far sites, identity sources) was solved  |
| protobuf.js-ds | JavaScript (Node 20, npm) / prototype pollution / inherited-property confusion (untruste | missed second copy (code-generator output) + missed final-segment guard | partly | some | no | ✓ ✗ ✓ ✗ | Open human-review question on the S2 tests (does an ignored final __proto__ segment still create the parent `features` container; does setOption count as 'recor |
| seaweedfs-ds | Go / authz / tenant isolation: principal mis-derivation (shared a | missed indirect route (second front end, name-only caller) / over-blocked legitimate use | partly | some | no | ✓ ✗ ✓ ✓ | Injected siblings contributed nothing: no run failed T8/T9/T10, so this is effectively a mined real-code breaker; it says little in favour of the injection pipe |
| siyuan-ds | Go (gin) / missing authorization / information leak: publish-mode reade | missed describing endpoint (listing/catalog) + over-blocked legitimate use | partly | some | no | ✓ ✗ ✓ ✓ | LIVE fairness defect, not in FAIRNESS.md: snippet fixtures have Enabled=false while the instruction requires 'any enabled or active state' for publication. 4 fu |
| theia-ds | TypeScript (npm, inversify DI) / trust-boundary bypass / authz: untrusted-workspace configura | missed indirect route (unguarded config reader) + missed second copy (unwrapped sibling co | partly | some | no | ✓ ✗ ✓ ✓ | Open human-review question in FAIRNESS.md (harness stubs could fail alternative correct designs: eventless preference mutation in functional/04, no trust bindin |
| tinacms-ds | TypeScript (Next.js API route handlers, AWS/Azure/Cloudinary SDKs) / path traversal / object-key confinement (caller-chosen stora | normalised instead of refused (stripped an absolute directory) + over-blocked legitimate u | covered | leaky | yes | ✓ ✗ ✓ ✗ | Fragile: one test (azure 'refuses an absolute directory') fails all 6 runs. FAIRNESS.md rated it medium-risk 'maybe'. It conflicts with the keep-working clause  |

### Precision validation (sibling builder)

| Task | Language / mechanism | Decisive failure | Upstream fix covers it? | Hints | One test decides? | e2 e3 e4 e5 | Main concern |
|---|---|---|---|---|---|---|---|
| pv-apostrophe | JavaScript (Node/npm, mocha) / stored XSS through a bypass of the HTML sanitizer's URL-sche | missed derived destination (embedded URL in a non-URL attribute) / incomplete grammar | partly | some | yes | ✗ ✗ ✓ ✗ | The decisive refresh route is fixed in public upstream (f84fd41 on main, 2026-09-30; advisory published 2026-10-20, before the trials). With open internet and n |
| pv-device-builder | Python (aiohttp) / missing authentication: fail-open credential resolution afte | missed allowlisted bypass surface | uncovered | some | yes | ✗ ✓ ✓ ✓ | The breaker rests on two planted single-site tests. The pre-auth test fails in all 6 runs and alone decides MiMo run 1 (0.8). |
| pv-pacioli | Python (Frappe/ERPNext app, unittest) / authorization: binding of a consent marker to the act and do | missed nested propagation (authority carried at second level) + missed relationship fallba | partly | leaky | no | ✗ ✗ ✓ ✗ | The human-review question on the decisive cascade test is open. |
| pv-quarkus | Java (Quarkus, vert.x HTTP, Undertow; JUnit/Maven) / authorization bypass by path normalisation (encoded separato | missed second copy (second authz implementation) + over-normalised into a weaker rule | partly | some | yes | ✗ ✗ ✓ ✗ | The upstream fix covers the servlet trap, so a model that looks it up could clear DeepSeek runs 2 and 3. |
| pv-svgo | JavaScript (Node/npm) / XSS through an incomplete SVG script-removal sanitiser (fore | missed indirect route (animation-applied URL) + over-blocked foreign-vocabulary elements | partly | some | yes | ✗ ✓ ✓ ✗ | The official fairness verdict is stale NOT_READY. The repaired tests have no fresh official review, and the runs were graded on the pre-repair tests and cannot  |
