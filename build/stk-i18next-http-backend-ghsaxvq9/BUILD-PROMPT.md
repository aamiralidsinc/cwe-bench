# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-i18next-http-backend-ghsaxvq9`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-q89c-q3h5-w34g; GHSA-xvq9-wjp8-hwqf
- Pinned (vulnerable) commit: 4cbc48741128d9b1f6cceb43edabfbec84c92615. Published fix: 4cee84f229c6, 07e028862b25.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-xvq9-wjp8-hwqf",
 "pattern": "H3b",
 "repo": "i18next/i18next-http-backend",
 "pinned_commit": "4cbc48741128d9b1f6cceb43edabfbec84c92615",
 "protections": [
  "P1 (absent in the pin): every outbound translation URL is validated against an allowed destination before dispatch - reads built from loadPath (string, function or promise) plus interpolated lng/ns (lib/index.js:55-66) and writes built from addPath (lib/index.js:118-125).",
  "P2 (absent in the pin): the validation binds to the request actually performed - the transport chosen at lib/request.js:162-170, an app-supplied request/alternateFetch (lib/index.js:12, lib/request.js:95) and the final redirect target."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "lib/index.js:55",
    "lib/index.js:64",
    "lib/index.js:65",
    "lib/index.js:74",
    "lib/request.js:162"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "lib/index.js:55",
    "lib/index.js:60",
    "lib/index.js:63",
    "lib/index.js:64",
    "lib/index.js:65",
    "lib/index.js:74",
    "lib/index.js:150",
    "lib/index.js:156",
    "lib/request.js:155",
    "lib/request.js:162",
    "lib/request.js:167"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/index.js:110",
    "lib/index.js:123",
    "lib/index.js:125",
    "lib/index.js:7",
    "README.md:140"
   ],
   "reason_to_dismiss": "create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/index.js:7",
    "lib/index.js:110",
    "lib/index.js:112",
    "lib/index.js:118",
    "lib/index.js:120",
    "lib/index.js:123",
    "lib/index.js:125",
    "README.md:140",
    "README.md:142",
    "test/http.spec.js:262"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "lib/index.js:56",
    "lib/index.js:60",
    "lib/index.js:64",
    "lib/utils.js:47",
    "lib/index.js:123"
   ],
   "reason_to_dismiss": "loadPath/addPath is trusted app configuration and lng/ns are normally plain language and namespace codes, so checking the configured string or the raw language argument looks sufficient.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "lib/index.js:56",
    "lib/index.js:60",
    "lib/index.js:62",
    "lib/index.js:63",
    "lib/index.js:64",
    "lib/utils.js:46",
    "lib/utils.js:47",
    "lib/utils.js:48",
    "test/http.spec.js:164",
    "test/http.spec.js:197"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/index.js:69",
    "lib/index.js:74",
    "index.d.ts:125"
   ],
   "reason_to_dismiss": "loadUrl is an internal chokepoint the backend calls itself; it appears in the public typings but is never documented in the README, so apps are not expected to call it with their own URL.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/index.js:69",
    "lib/index.js:73",
    "lib/index.js:74",
    "index.d.ts:125",
    "index.d.ts:130"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/request.js:115",
    "lib/request.js:128",
    "lib/request.js:162",
    "lib/request.js:167"
   ],
   "reason_to_dismiss": "fetch is the modern default path; the XMLHttpRequest implementation is a legacy fallback exercised only by the polyfill test script, so a fetch-side check looks complete.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/request.js:115",
    "lib/request.js:128",
    "lib/request.js:162",
    "lib/request.js:167",
    "lib/request.js:169",
    "package.json:85",
    "package.json:86",
    "test/http.spec.js:60",
    "test/fixtures/xmlHttpRequest.cjs:2"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/index.js:12",
    "lib/index.js:74",
    "lib/index.js:125",
    "lib/request.js:95"
   ],
   "reason_to_dismiss": "options.request and options.alternateFetch are application-supplied code - the app already owns the destination - so validating inside the default transport seems sufficient.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "lib/index.js:12",
    "lib/index.js:74",
    "lib/index.js:125",
    "lib/request.js:58",
    "lib/request.js:60",
    "lib/request.js:95",
    "lib/index.js:19",
    "index.d.ts:26",
    "index.d.ts:77",
    "test/http.spec.js:232"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/request.js:68",
    "lib/request.js:90",
    "lib/index.js:19",
    "lib/request.js:127"
   ],
   "reason_to_dismiss": "the configured load/add host is trusted and following redirects is normal HTTP; revalidating or refusing redirects would break CDN canonicalisation and is outside a URL-prefix check.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "lib/request.js:66",
    "lib/request.js:68",
    "lib/request.js:70",
    "lib/request.js:89",
    "lib/request.js:90",
    "lib/index.js:19",
    "lib/request.js:127",
    "lib/request.js:146"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "lib/index.js:6",
    "lib/index.js:7",
    "lib/index.js:63",
    "lib/request.js:162",
    "lib/request.js:38"
   ],
   "reason_to_dismiss": "the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "lib/index.js:6",
    "lib/index.js:7",
    "lib/index.js:63",
    "lib/request.js:38",
    "lib/request.js:46",
    "lib/request.js:162",
    "test/http.spec.js:231",
    "test/http.spec.js:252",
    "test/http.spec.js:263",
    "test/http.spec.js:313",
    "README.md:119",
    "README.md:134",
    "CHANGELOG.md:100",
    "test/request.spec.js:20"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T3",
   "T4",
   "T5",
   "T6"
  ],
  [
   "T2"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T7 (redirect) only becomes reachable once an origin/host check exists on the constructed URL: a blocked URL is still reachable through a redirect served by an allowed origin.",
   "T2 (create/addPath) is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112; README.md:140).",
   "T3's promise-valued loadPath branch only runs when the app passes a function returning a promise (lib/index.js:60; test/http.spec.js:197)."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T8",
   "what": "A rule that requires an absolute http(s) URL before dispatch rejects the default relative loadPath (lib/index.js:6; README.md:134) and the relative path custom request handlers currently receive verbatim (test/http.spec.js:231, test/http.spec.js:252)."
  },
  {
   "a": "T2",
   "b": "T8",
   "what": "Holding addPath to the loadPath origin rejects the default relative addPath (lib/index.js:7; test/http.spec.js:263) and legitimate CDN-read plus own-API-write setups."
  },
  {
   "a": "T6",
   "b": "T8",
   "what": "Resolving or normalising the URL for validation changes the string handed to options.request, which the tests assert exactly (test/http.spec.js:252, test/http.spec.js:263)."
  },
  {
   "a": "T5",
   "b": "T8",
   "what": "A scheme allowlist that drops non-http(s) URLs breaks the Node file:// loading path the XHR branch exists to serve (lib/request.js:162; CHANGELOG.md:100)."
  }
 ],
 "fairness_risks": [
  "Relative loadPath/addPath are the documented defaults (lib/index.js:6-7, README.md:134, README.md:142) and are passed unchanged to custom request handlers (test/http.spec.js:250-252, test/http.spec.js:262-263); a rule that refuses relative URLs or rewrites them breaks normal browser use.",
  "The falsy-loadPath abort must still resolve with {} and no error (README.md:119; lib/index.js:63; test/http.spec.js:313), so a rule that rejects an empty or non-absolute URL breaks a documented feature.",
  "file:// loading in Node is a legitimate non-http use (lib/request.js:162; CHANGELOG.md:100); a scheme allowlist must not refuse it.",
  "queryStringParams are appended by the transport (lib/request.js:38-49, lib/request.js:122-123) and must keep working (test/request.spec.js:18-26), so a rule that rejects URLs carrying query strings is over-broad.",
  "Multi-load joins languages and namespaces with '+' (lib/index.js:64; README.md:124) and language tags contain '-' (region/script); a charset rule on lng/ns must accept these shapes.",
  "Function-valued and promise-valued loadPath must keep working (lib/index.js:56-63; test/http.spec.js:161-165, test/http.spec.js:189-222), so a rule that only accepts string loadPath options breaks supported configuration."
 ],
 "effort_minutes": 75,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T7",
   "T8"
  ],
  "why": "Four independent judgements on top of one shared read-side guard. T1 is the reported URL-validation route and is fast to find; T2 is the same request sink reached from create/addPath, which a load-path guard never touches, is dormant by default and has a strong reason to be dismissed (deepseek-type). T7 defeats any URL check through a redirect served by an allowed origin, protection never existed there and it reads as normal HTTP (deepseek-type). T8 forces the rule to stay origin/scheme-scoped rather than absolute-only so the relative defaults, falsy abort, file://, query strings and the custom-request contract keep working (mimo-type; over-hardening is the failure mode). T3/T4/T5/T6 are shape and placement variants of the same read-side guard and are kept in group one rather than counted as separate stack members. The remaining groups are the write dispatch (T2), the transport/redirect policy (T7) and the rule-shape constraint (T8)."
 },
 "unverified": [
  "The A fix (4cee84f229c6) and B fix (07e028862b25) are not present in the pinned checkout, and the worktree contains no validator at all (only url.indexOf('file:') at lib/request.js:162), so a_fix_leaves_b_open=true and b_in_code_a_wrote=false are inferred from the candidate metadata (link = previous patch, szz_status H3b2) rather than read from the fix diffs.",
  "The GHSA/CVE texts were not available in the worktree; which route the B advisory names (loadPath read route versus addPath write route) is inferred from the code, not from the advisory wording.",
  "Fetch follows redirects by default and XHR cannot restrict redirect targets; those are platform behaviours, not lines in this repository (the repo only omits any redirect option: lib/index.js:19-23, lib/request.js:89-94, lib/request.js:146-149).",
  "Whether the hidden behavioural tests call loadUrl directly, install a custom request spy, enable saveMissing, or serve an HTTP redirect is unknown, so the relative weight of T2/T4/T6/T7 is not verified.",
  "cross-fetch 4.1.0 is only a fallback fetch implementation (package.json:29-31, lib/request.js:28-36); no advisory fix appears to belong to a dependency upgrade, but no dependency changelog was inspected beyond package.json."
 ]
}
  ```
- Published fix sites:   - lib/index.js:55 — T1 M4 (reason to dismiss: none)
  - lib/index.js:64 — T1 M4 (reason to dismiss: none)
  - lib/index.js:65 — T1 M4 (reason to dismiss: none)
  - lib/index.js:74 — T1 M4 (reason to dismiss: none)
  - lib/request.js:162 — T1 M4 (reason to dismiss: none)
  - lib/index.js:110 — T2 M1 (reason to dismiss: create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.)
  - lib/index.js:123 — T2 M1 (reason to dismiss: create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.)
  - lib/index.js:125 — T2 M1 (reason to dismiss: create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.)
  - lib/index.js:7 — T2 M1 (reason to dismiss: create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.)
  - README.md:140 — T2 M1 (reason to dismiss: create() is dormant unless saveMissing is enabled and addPath is truthy (lib/index.js:112); it is an opt-in write endpoint the app configures, while the advisory is about loading translations.)
  - lib/index.js:69 — T4 M4 (reason to dismiss: loadUrl is an internal chokepoint the backend calls itself; it appears in the public typings but is never documented in the README, so apps are not expected to call it with their own URL.)
  - lib/index.js:74 — T4 M4 (reason to dismiss: loadUrl is an internal chokepoint the backend calls itself; it appears in the public typings but is never documented in the README, so apps are not expected to call it with their own URL.)
  - index.d.ts:125 — T4 M4 (reason to dismiss: loadUrl is an internal chokepoint the backend calls itself; it appears in the public typings but is never documented in the README, so apps are not expected to call it with their own URL.)
  - lib/request.js:115 — T5 M2 (reason to dismiss: fetch is the modern default path; the XMLHttpRequest implementation is a legacy fallback exercised only by the polyfill test script, so a fetch-side check looks complete.)
  - lib/request.js:128 — T5 M2 (reason to dismiss: fetch is the modern default path; the XMLHttpRequest implementation is a legacy fallback exercised only by the polyfill test script, so a fetch-side check looks complete.)
  - lib/request.js:162 — T5 M2 (reason to dismiss: fetch is the modern default path; the XMLHttpRequest implementation is a legacy fallback exercised only by the polyfill test script, so a fetch-side check looks complete.)
  - lib/request.js:167 — T5 M2 (reason to dismiss: fetch is the modern default path; the XMLHttpRequest implementation is a legacy fallback exercised only by the polyfill test script, so a fetch-side check looks complete.)
  - lib/index.js:12 — T6 M2 (reason to dismiss: options.request and options.alternateFetch are application-supplied code - the app already owns the destination - so validating inside the default transport seems sufficient.)
  - lib/index.js:74 — T6 M2 (reason to dismiss: options.request and options.alternateFetch are application-supplied code - the app already owns the destination - so validating inside the default transport seems sufficient.)
  - lib/index.js:125 — T6 M2 (reason to dismiss: options.request and options.alternateFetch are application-supplied code - the app already owns the destination - so validating inside the default transport seems sufficient.)
  - lib/request.js:95 — T6 M2 (reason to dismiss: options.request and options.alternateFetch are application-supplied code - the app already owns the destination - so validating inside the default transport seems sufficient.)
  - lib/request.js:68 — T7 M4 (reason to dismiss: the configured load/add host is trusted and following redirects is normal HTTP; revalidating or refusing redirects would break CDN canonicalisation and is outside a URL-prefix check.)
  - lib/request.js:90 — T7 M4 (reason to dismiss: the configured load/add host is trusted and following redirects is normal HTTP; revalidating or refusing redirects would break CDN canonicalisation and is outside a URL-prefix check.)
  - lib/index.js:19 — T7 M4 (reason to dismiss: the configured load/add host is trusted and following redirects is normal HTTP; revalidating or refusing redirects would break CDN canonicalisation and is outside a URL-prefix check.)
  - lib/request.js:127 — T7 M4 (reason to dismiss: the configured load/add host is trusted and following redirects is normal HTTP; revalidating or refusing redirects would break CDN canonicalisation and is outside a URL-prefix check.)
  - lib/index.js:6 — T8 M11 (reason to dismiss: the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.)
  - lib/index.js:7 — T8 M11 (reason to dismiss: the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.)
  - lib/index.js:63 — T8 M11 (reason to dismiss: the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.)
  - lib/request.js:162 — T8 M11 (reason to dismiss: the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.)
  - lib/request.js:38 — T8 M11 (reason to dismiss: the visible values here are the legitimate ones - relative defaults, falsy abort, file:// in Node, query strings and a verbatim URL handed to custom request - so an absolute-http(s)-only rule looks like the safe reading of the advisory.)
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T7, T8. Why: Four independent judgements on top of one shared read-side guard. T1 is the reported URL-validation route and is fast to find; T2 is the same request sink reached from create/addPath, which a load-path guard never touches, is dormant by default and has a strong reason to be dismissed (deepseek-type). T7 defeats any URL check through a redirect served by an allowed origin, protection never existed there and it reads as normal HTTP (deepseek-type). T8 forces the rule to stay origin/scheme-scoped rather than absolute-only so the relative defaults, falsy abort, file://, query strings and the custom-request contract keep working (mimo-type; over-hardening is the failure mode). T3/T4/T5/T6 are shape and placement variants of the same read-side guard and are kept in group one rather than counted as separate stack members. The remaining groups are the write dispatch (T2), the transport/redirect policy (T7) and the rule-shape constraint (T8). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Relative loadPath/addPath are the documented defaults (lib/index.js:6-7, README.md:134, README.md:142) and are passed unchanged to custom request handlers (test/http.spec.js:250-252, test/http.spec.js:262-263); a rule that refuses relative URLs or rewrites them breaks normal browser use. | The falsy-loadPath abort must still resolve with {} and no error (README.md:119; lib/index.js:63; test/http.spec.js:313), so a rule that rejects an empty or non-absolute URL breaks a documented feature. | file:// loading in Node is a legitimate non-http use (lib/request.js:162; CHANGELOG.md:100); a scheme allowlist must not refuse it. | queryStringParams are appended by the transport (lib/request.js:38-49, lib/request.js:122-123) and must keep working (test/request.spec.js:18-26), so a rule that rejects URLs carrying query strings is over-broad. | Multi-load joins languages and namespaces with '+' (lib/index.js:64; README.md:124) and language tags contain '-' (region/script); a charset rule on lng/ns must accept these shapes. | Function-valued and promise-valued loadPath must keep working (lib/index.js:56-63; test/http.spec.js:161-165, test/http.spec.js:189-222), so a rule that only accepts string loadPath options breaks supported configuration.. Conflicts the reader found: A rule that requires an absolute http(s) URL before dispatch rejects the default relative loadPath (lib/index.js:6; README.md:134) and the relative path custom request handlers currently receive verbatim (test/http.spec.js:231, test/http.spec.js:252). | Holding addPath to the loadPath origin rejects the default relative addPath (lib/index.js:7; test/http.spec.js:263) and legitimate CDN-read plus own-API-write setups. | Resolving or normalising the URL for validation changes the string handed to options.request, which the tests assert exactly (test/http.spec.js:252, test/http.spec.js:263). | A scheme allowlist that drops non-http(s) URLs breaks the Node file:// loading path the XHR branch exists to serve (lib/request.js:162; CHANGELOG.md:100).

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-i18next-http-backend-ghsaxvq9/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-i18next-http-backend-ghsaxvq9/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-i18next-http-backend-ghsaxvq9/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-i18next-http-backend-ghsaxvq9/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-i18next-http-backend-ghsaxvq9/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-i18next-http-backend-ghsaxvq9/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-i18next-http-backend-ghsaxvq9/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-i18next-http-backend-ghsaxvq9 --only static
python3 -I common/gate/gate.py stk-i18next-http-backend-ghsaxvq9 --only nop
python3 -I common/gate/gate.py stk-i18next-http-backend-ghsaxvq9 --only oracle
python3 -I common/gate/gate.py stk-i18next-http-backend-ghsaxvq9 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-i18next-http-backend-ghsaxvq9/`;
  - edit only `tasks/stk-i18next-http-backend-ghsaxvq9/`, `build/stk-i18next-http-backend-ghsaxvq9/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-xvq9-wjp8-hwqf.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-i18next-http-backend-ghsaxvq9`. Control task slug: `stk-i18next-http-backend-ghsaxvq9-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-xvq9-wjp8-hwqf.json`.
