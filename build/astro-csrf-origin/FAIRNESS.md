# astro-csrf-origin — pre-trial fairness and leniency review

Reviewer did not write the tests. Inputs read: instruction.md, all of tests/ (security, functional,
project, support, test.sh, score.py), solution/fix.patch, manifest.json, notes.md, the checks/ patch list.
Nothing was run.

Fixture facts the rows below rely on: SITE = `http://localhost`, FOREIGN = `http://attacker.example`.
`req()` defaults to POST with Origin FOREIGN. `checkOrigin` defaults to true in `buildApp`. The six
project test files use `createTestApp`, whose default is `checkOrigin: false`
(support/units/app/test-helpers.ts:66). So they post form data with no Origin and are not affected
by a correct fix.

## 1. Per-test table

### Security

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| hono-actions-before-middleware::refuses a cross-site urlencoded RPC action call before the action runs | ORDER actions,middleware,pages; 4xx; action not run | "Observed impact" (this is the reported request) | no | low |
| …::refuses a cross-site multipart form action posted to a page before the action runs | `/form?_action=addItem`, multipart; 4xx; action and page not run | "This covers … form actions submitted to a page (`?_action=<name>`)"; "no action, endpoint or page handler runs" | no | low |
| …::refuses a form action call that carries no Origin header | no Origin; 4xx; action not run | "its `Origin` header is missing or is not the site's own origin" | no | low |
| …::refuses a cross-site call whose form content type differs in case and has parameters | `Application/X-WWW-Form-Urlencoded; charset=UTF-8`; 4xx | "in any letter case and with any parameters" | no | low |
| …::refuses a cross-site action call when the app mounts actions() and pages() only | no middleware(); 4xx; action not run | "whichever of them it uses and in whatever order" | no. A fix that only works when middleware() is mounted fails, but the instruction rules that out | low |
| hono-pages-without-middleware::refuses a cross-site text/plain POST to an endpoint before it runs | pages() only; text/plain; 4xx; endpoint not run | content-type bullet (text/plain); "endpoints"; "whichever of them it uses" | no | low |
| …::refuses a cross-site DELETE without a content type to an endpoint before it runs | pages() only; DELETE, no CT; 4xx | "anything other than GET, HEAD or OPTIONS"; "or it has no content type" | no | low |
| …::refuses a cross-site form POST to a page before it renders | pages() only; urlencoded to `/form`; 4xx; page not rendered | "pages"; "whichever of them it uses" | no | low |
| fetch-primitives::refuses a cross-site urlencoded RPC action call before the action runs | `astro/fetch` `actions(state)` then `pages(state)`; 4xx | "composable request-handling building blocks … for example with … `astro/hono`"; "whichever of them it uses" | maybe. A competent engineer who reads "building blocks" as only the Hono wrappers would patch `core/hono` and fail. The instruction says "for example", and `core/fetch` sits directly under `core/hono` in the repo, so it is discoverable. Still, `astro/fetch` is never named. | medium |
| fetch-primitives::refuses a cross-site PUT without a content type to an endpoint before it runs | fetch primitives; PUT, no CT; 4xx | as above + method/no-CT bullets | maybe (same reason) | medium |

### Functional (legitimate-use.test.ts)

| test | asserts | fair because | correct fix could fail? | risk |
|---|---|---|---|---|
| same-site::hono actions-first: same-site RPC form action runs | 2xx, action ran once | "same-site submissions of any kind reach actions" | no | low |
| same-site::hono actions-first: same-site form action on a page runs and the page renders | 200, body "form page", action ran | same | no | low |
| same-site::hono pages() without middleware(): same-site form POST reaches the endpoint | 2xx, body `endpoint-ok` | same | no | low |
| same-site::… same-site DELETE without content type reaches the endpoint | 2xx | same | no | low |
| same-site::… same-site form POST renders the page | 200, page ran | same | no | low |
| same-site::astro/fetch primitives: same-site RPC action and endpoint POST run | 2xx both | same | no | low |
| cross-site non-form::hono actions-first: cross-site JSON RPC action runs | 2xx | "non-form content type … `application/json` RPC … unaffected" | no | low |
| cross-site non-form::astro/fetch primitives: cross-site JSON RPC action runs | 2xx | same | no | low |
| cross-site non-form::hono pages() without middleware(): cross-site JSON PUT reaches the endpoint | 2xx | same | no | low |
| cross-site non-form::… cross-site GET, HEAD and OPTIONS reach the endpoint | 2xx ×3 | "`GET`, `HEAD` and `OPTIONS` requests are unaffected" | no | low |
| cross-site non-form::astro/fetch primitives: cross-site GET renders a page | 200 "home" | same | no | low |
| checkOrigin disabled::hono actions-first: cross-site form action runs | 2xx | "with `security.checkOrigin: false`, no origin check happens anywhere" | no | low |
| checkOrigin disabled::hono pages() without middleware(): cross-site form POST reaches the endpoint | 2xx | same | no | low |
| checkOrigin disabled::astro/fetch primitives: cross-site form action and endpoint DELETE run | 2xx both | same | no | low |
| standard::refuses a cross-site form POST to an endpoint and lets a same-site one through | App.render 4xx / 2xx | "the standard request handling keeps its current behaviour" | no | low |
| standard::runs a same-site RPC action and a cross-site JSON one, refuses a cross-site form one | App.render | same | no | low |
| project/{hono,fetch,actions,middleware}/*.test.ts (upstream unit tests) | existing behaviour; all use `checkOrigin: false` | "Keep legitimate use working"; standard expert knowledge: existing project tests must keep passing | no. `csrf.test.ts` is correctly excluded because it imports `middlewares.js`, which a refactoring fix may rename. No retained file imports that module. | low |

Other notes on fairness:
- The fixture compares against `url.origin` (`http://localhost`). A fix that compared against the configured `site` instead would fail. That is not a fix a competent engineer would write here, because the existing middleware uses `url.origin` and the instruction says "the site's own origin".
- test.sh rebuilds `dist/` from the solver's source, so a stale build cannot be graded.

## 2. Leniency

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| Reported case (RPC, actions-first) | reorder Hono `actions()` behind the check, or run the origin check inside Hono `actions()` only | yes: hono-pages-without-middleware ×3, fetch-primitives ×2 (`sf_actions_only`, `sf_hono_wrappers_only`) |
| T1 dispatch without middleware | guard action dispatch only | yes: hono-pages-without-middleware ×3, fetch PUT (`sf_actions_only.patch`) |
| T2 lower-level `astro/fetch` | guard only the `core/hono` wrappers | yes: fetch-primitives ×2 (`sf_hono_wrappers_only.patch`) |
| T3 form action vs RPC | guard `/_actions/*` only | yes: multipart form action test, ran.action == 0 (`sf_rpc_actions_only.patch`) |
| T3 method | `method === 'POST'` | yes: DELETE (hono pages), PUT (fetch) (`sf_post_only.patch`) |
| T3 content type | exact / case-sensitive match | yes: mixed-case + charset test (`sf_exact_content_type.patch`) |
| T3 missing Origin | `origin && origin !== url.origin` | yes: no-Origin test (`sf_absent_origin_allowed.patch`) |
| Refusal shape | throw → 500 | yes: every security test asserts 4xx (`sf_throw_instead_of_refusal.patch`) |
| Ordering | refuse after the action has run | yes: ran.action == 0 assertions (`sf_check_after_action.patch`) |
| T4 over-blocking | refuse all cross-site / JSON counted as form / ignore checkOrigin | yes: functional (`ff_refuse_all_cross_site`, `ff_json_counted_as_form`, `ff_ignores_check_origin_setting`) |

Wrong fixes that no test catches. All are minor; none needs to block:
- Allow-listing unsafe methods (POST/PUT/PATCH/DELETE) instead of exempting GET/HEAD/OPTIONS. An extension method such as `PROPFIND` would slip through. Untested.
- A per-path form-type list that misses one type on one path. For example, text/plain is tested only on an endpoint and multipart only on a page action. A fix that drops text/plain only in the action path would pass.
- A fix that guards hono `pages()` and `fetch.pages()` but not the shared `PagesHandler`, so other callers stay open. If no other public caller exists, this is acceptable.
- Prerendered-route exemption is untested (notes.md explains why; acceptable).

## 3. Hints

1. "It holds however the site composes Astro's request-handling building blocks: whichever of them it uses and in whatever order." This paraphrases T1 ("whichever … it uses", which includes omitting `middleware()`) and the reported ordering. Some version of it is needed, or T1 reads as user misconfiguration. Proposed: "It holds for every way a site can assemble its server from Astro's building blocks."
2. "This covers actions called by RPC (`/_actions/<name>`) and form actions submitted to a page (`?_action=<name>`)." This is the variant list for T3 (one_role_or_direction). Proposed: "This covers every way an action can be invoked."
3. The criteria bullets enumerate three of the T3 traps almost verbatim:
   - "its method is anything other than `GET`, `HEAD` or `OPTIONS`" targets `sf_post_only`.
   - "in any letter case and with any parameters" targets `sf_exact_content_type`.
   - "or it has no content type" targets the no-CT DELETE/PUT tests.
   - "its `Origin` header is missing or" targets `sf_absent_origin_allowed`.

   Together they turn T3 into a checklist. Proposed: "No request can cause any of the site's actions, endpoints or pages to run if the standard request handling's origin check would refuse it." This stays fair: the rule is defined in the repo by the existing origin-check middleware, and the instruction already says standard handling is the reference. Keep the concrete form-type list only if the client requires an explicit definition. Even then, drop "in any letter case and with any parameters" and "missing".
4. "mounts `actions()` before `middleware()`, as the advanced-routing example does". This names functions, but it is the reproduction of the report. Acceptable.
5. No file names, function names from leak_terms, fix approach or flaw count appear. "The request above is one example, not the full set" is neutral.

## 4. Realism

- T1: unmodified upstream code at the pin, `core/pages/handler.ts`. A site with no custom middleware can mount `pages()` alone, and the upstream fix guards exactly there. Not planted.
- T2: `astro/fetch` primitives are unmodified upstream code under the Hono wrappers, and the upstream fix lands in the shared handlers. Real.
- T3: the general rule already exists in `middlewares.ts`. Real.
- The fixture's pass-through site middleware loader mirrors a real server build (notes.md). The 10 failures at the pin come from the real entry points (`hono.fetch`, `actions(state)`/`pages(state)`). Nothing looks contrived.

## 5. Verdict

**NOT READY.** The tests are fair and tight. The only required changes are to instruction.md:

1. Replace the three criteria bullets with the reference-to-standard-rule wording in §3.3, or at minimum delete "in any letter case and with any parameters" and "is missing or".
2. Replace the RPC/`?_action` sentence with "This covers every way an action can be invoked."
3. Soften "whichever of them it uses and in whatever order" to "for every way a site can assemble its server from Astro's building blocks."

Optional, to reduce the medium T2 discoverability risk without naming `astro/fetch`: keep "for example" before `astro/hono` (it is already there) and add nothing more. No test changes are required.
