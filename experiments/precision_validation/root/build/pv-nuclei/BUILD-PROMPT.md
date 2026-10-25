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

Project root: `/home/mara/cwe-bench/precision_validation/root`. Task: `pv-nuclei`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-JPVM-9FRM-HJCQ", "CVE-2026-76805", "GO-2026-6571"]; projectdiscovery/nuclei; CWE-200 information disclosure through template/expression re-evaluation of untrusted runtime data (second-order template injection into the nuclei DSL renderer)
- Pinned (vulnerable) commit: parent of ccbfb12bd01447ba25f6e755dfb2bee677736da6 (parent_commit not given in candidate). Published fix: ccbfb12bd01447ba25f6e755dfb2bee677736da6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "18195",
 "advisory_ids": [
  "GHSA-JPVM-9FRM-HJCQ",
  "CVE-2026-76805",
  "GO-2026-6571"
 ],
 "repo": "projectdiscovery/nuclei",
 "pinned_commit": "parent of ccbfb12bd01447ba25f6e755dfb2bee677736da6 (parent_commit not given in candidate)",
 "fix_commits": [
  "ccbfb12bd01447ba25f6e755dfb2bee677736da6"
 ],
 "trust_decision": {
  "summary": "Runtime values (response-derived/extracted data, fuzz base values, template-context values from earlier requests) must be treated as terminal data and never re-scanned as template text (DSL expressions, {{var}} markers resolving to CLI/env vars, interactsh markers). At the pin, the shared renderer and the variable evaluator re-evaluate them in fuzz rules, variable evaluation, matchers and every protocol's request builder.",
  "evidence": [
   "pkg/fuzz/execute.go:250",
   "pkg/fuzz/execute.go:155-158",
   "pkg/protocols/common/variables/variables.go:84-87",
   "pkg/protocols/common/variables/variables.go:118-124",
   "pkg/protocols/common/expressions/expressions.go:58",
   "pkg/protocols/common/generators/options.go:36-37"
  ]
 },
 "landing_point": {
  "where": "pkg/fuzz/execute.go:250",
  "why": "The advisory names DAST/Fuzz mode. evaluateVarsWithInteractsh runs expressions.Evaluate over every merged value, including response-derived baseValues, so values that resolve to env-backed option vars get expanded."
 },
 "fix_sites": [
  {
   "where": "pkg/fuzz/execute.go:155",
   "entry_point": "CLI `nuclei -dast` fuzzing templates (no generator)",
   "module_kind": "fuzz engine (landing)"
  },
  {
   "where": "pkg/fuzz/execute.go:176",
   "entry_point": "CLI `nuclei -dast` fuzzing templates with payload generator",
   "module_kind": "fuzz engine (landing)"
  },
  {
   "where": "pkg/fuzz/execute.go:250",
   "entry_point": "CLI `nuclei -dast` (evaluateVarsWithInteractsh)",
   "module_kind": "fuzz engine (landing)"
  },
  {
   "where": "pkg/fuzz/parts.go:199-201",
   "entry_point": "CLI `nuclei -dast` payload rendering per fuzz point",
   "module_kind": "fuzz engine"
  },
  {
   "where": "pkg/protocols/common/variables/variables.go:84-87",
   "entry_point": "every protocol's Variables.Evaluate call (http, dns, ssl, websocket, whois, network, headless, js, code, flow, multiproto)",
   "module_kind": "shared variable evaluator (merge/precedence layer)"
  },
  {
   "where": "pkg/protocols/common/variables/variables.go:118-124",
   "entry_point": "EvaluateWithInteractsh from fuzz and HTTP request builder",
   "module_kind": "shared variable evaluator"
  },
  {
   "where": "pkg/protocols/common/expressions/expressions.go:58",
   "entry_point": "all template rendering (helper args with quoted {{var}} placeholders)",
   "module_kind": "lower-level expression API"
  },
  {
   "where": "pkg/operators/matchers/match.go:68",
   "entry_point": "word matchers in any template",
   "module_kind": "operators (matcher)"
  },
  {
   "where": "pkg/operators/matchers/match.go:198",
   "entry_point": "DSL matchers with unresolved {{var}} placeholders",
   "module_kind": "operators (matcher)"
  },
  {
   "where": "pkg/protocols/http/build_request.go:168-183",
   "entry_point": "HTTP templates (template context merge + interactsh replacement over payloads)",
   "module_kind": "protocol request builder"
  },
  {
   "where": "pkg/protocols/http/build_request.go:211",
   "entry_point": "HTTP templates",
   "module_kind": "protocol request builder"
  },
  {
   "where": "pkg/protocols/http/build_request.go:269",
   "entry_point": "HTTP self-contained templates",
   "module_kind": "protocol request builder (second code path)"
  },
  {
   "where": "pkg/protocols/http/build_request.go:475",
   "entry_point": "HTTP template headers",
   "module_kind": "protocol request builder"
  },
  {
   "where": "pkg/protocols/http/build_request.go:513",
   "entry_point": "HTTP template body",
   "module_kind": "protocol request builder"
  },
  {
   "where": "pkg/protocols/http/request.go:694",
   "entry_point": "HTTP executeRequest re-evaluating meta payloads against dynamic values",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/code/code.go:203-208",
   "entry_point": "code protocol templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/dns/request.go:52",
   "entry_point": "DNS templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/dns/dns.go:207",
   "entry_point": "DNS templates (custom resolvers)",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/headless/request.go:60",
   "entry_point": "headless templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/headless/engine/page_actions.go:992",
   "entry_point": "headless page action args",
   "module_kind": "protocol engine"
  },
  {
   "where": "pkg/protocols/javascript/js.go:337",
   "entry_point": "javascript protocol templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/javascript/js.go:554",
   "entry_point": "javascript protocol args interactsh replacement",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/javascript/js.go:728",
   "entry_point": "javascript protocol args evaluation",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/network/request.go:159",
   "entry_point": "network templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/network/request.go:326-335",
   "entry_point": "network template inputs",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/network/network.go:195",
   "entry_point": "network template compile-time input pre-render",
   "module_kind": "protocol compiler"
  },
  {
   "where": "pkg/protocols/ssl/ssl.go:223",
   "entry_point": "ssl templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/websocket/websocket.go:183",
   "entry_point": "websocket templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/protocols/whois/whois.go:95",
   "entry_point": "whois templates",
   "module_kind": "protocol executor"
  },
  {
   "where": "pkg/tmplexec/flow/flow_executor.go:115",
   "entry_point": "templates using `flow:`",
   "module_kind": "template executor"
  },
  {
   "where": "pkg/tmplexec/flow/flow_internal.go:20",
   "entry_point": "templates using `flow:` (re-evaluation after each protocol step)",
   "module_kind": "template executor"
  },
  {
   "where": "pkg/tmplexec/multiproto/multi.go:43",
   "entry_point": "multi-protocol templates (compile)",
   "module_kind": "template executor"
  },
  {
   "where": "pkg/tmplexec/multiproto/multi.go:122",
   "entry_point": "multi-protocol templates (re-evaluation after each protocol step)",
   "module_kind": "template executor"
  },
  {
   "where": "pkg/protocols/common/contextargs/contextargs.go:73-84",
   "entry_point": "template context store shared across protocols",
   "module_kind": "state/provenance tracking"
  },
  {
   "where": "pkg/protocols/common/interactsh/const.go:11",
   "entry_point": "interactsh marker detection (regex accepts '|' as an encoded-brace char)",
   "module_kind": "marker parser"
  },
  {
   "where": "pkg/protocols/protocols.go:207",
   "entry_point": "ExecutorOptions (new NewVariablesScope / AddTemplateCtxToVariablesScope helpers added near here)",
   "module_kind": "public SDK-facing options API"
  }
 ],
 "O1_entry_points": 13,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "pkg/protocols/common/variables/variables.go:84-87"
 },
 "O3_reason_to_dismiss": "Variable precedence lets a caller-supplied value override a template variable on purpose (workflow/flow chaining, -var). Evaluating that override is how chained {{BaseURL}}/helper variables work, so it reads as a feature of the shared variables package rather than the DAST bug.",
 "O4_distance": {
  "files": 27,
  "packages": 20,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Template-authored text must keep rendering: payload values like `jon.doe@{{Hostname}}`, helper calls over variables (`{{md5(BaseURL)}}`, `{{url_encode('{{interactsh-url}}')}}`), and DSL matchers like `contains(body, '{{server_token}}')` must still match the runtime value literally. Refusing to substitute runtime values, or stripping all {{...}}, breaks this.",
  "where": "pkg/protocols/http/build_request.go:218-221"
 },
 "O6_input_shapes": [
  "plain {{var}} marker in a runtime value",
  "general \u00a7 marker (\u00a7var\u00a7)",
  "helper call expression in a runtime value ({{helper(...)}})",
  "runtime value placed inside a quoted helper/DSL string literal (single and double quote) that breaks out of the literal",
  "raw interactsh marker {{interactsh-url}} in a runtime value",
  "URL-encoded interactsh marker %7B%7Binteractsh-url%7D%7D, plus mixed raw/encoded and '|' pseudo-brace forms",
  "runtime value colliding with a template variable name (precedence override)",
  "value persisted in template context across flow/multi-protocol steps"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "pkg/protocols/common/variables/variables.go:84-87 (merge of runtime values over template variable text before evaluation); template context store pkg/protocols/common/contextargs/contextargs.go:82-84 carries values across protocol steps",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "pkg/protocols/dns/dns.go:238",
   "sibling": "DNS query name rendered with expressions.Evaluate (helper support) over vars that include template-context/runtime values",
   "why_realistic": "Every other protocol field supports helpers. A maintainer adding helper support to the DNS name would swap the single-pass replacer for Evaluate."
  },
  {
   "where": "pkg/protocols/whois/whois.go:104",
   "sibling": "whois query rendered with Evaluate over variables that include dynamicValues/template context",
   "why_realistic": "Same reason: helper support in the query field is a natural feature request, and the variables map already mixes runtime data."
  },
  {
   "where": "pkg/authprovider/authx/dynamic.go:135-176",
   "sibling": "dynamic auth secret fields rendered with Evaluate over d.Extracted (response-extracted values)",
   "why_realistic": "Dynamic secrets already template extracted values. Adding helper support (base64, etc.) would reach the same sink, in an auth package far from fuzz/protocols."
  },
  {
   "where": "pkg/protocols/network/request.go:179",
   "sibling": "network address rendered with Evaluate over variables that include template-context values",
   "why_realistic": "Addresses are already templated with replacer; upgrading to Evaluate for helpers is a plausible change."
  }
 ],
 "O9_family": "CWE-200 information disclosure through template/expression re-evaluation of untrusted runtime data (second-order template injection into the nuclei DSL renderer)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.25.7 (go.mod)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Package unit tests: pkg/fuzz (execute_race_test.go, parts_test.go), pkg/protocols/common/variables/variables_test.go, pkg/protocols/common/expressions/expressions_test.go, pkg/operators/matchers/match_test.go, pkg/protocols/http/build_request_test.go, pkg/protocols/network/*_test.go (httptest/local listeners). Interactsh-backed tests need a live OAST server."
 },
 "O11_fix_minutes": 240,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/fuzz/execute.go, pkg/fuzz/parts.go, pkg/operators/matchers/dsl_string_markers.go (new), pkg/operators/matchers/match.go, pkg/protocols/code/code.go, pkg/protocols/common/contextargs/contextargs.go, pkg/protocols/common/expressions/expressions.go, pkg/protocols/common/interactsh/const.go, pkg/protocols/common/interactsh/interactsh.go, pkg/protocols/common/marker/marker.go, pkg/protocols/common/render/render.go (new), pkg/protocols/common/variables/scope.go (new), pkg/protocols/common/variables/variables.go, pkg/protocols/dns/dns.go, pkg/protocols/dns/request.go, pkg/protocols/headless/engine/page_actions.go, pkg/protocols/headless/request.go, pkg/protocols/http/build_request.go, pkg/protocols/http/request.go, pkg/protocols/javascript/js.go, pkg/protocols/network/network.go, pkg/protocols/network/request.go, pkg/protocols/protocols.go, pkg/protocols/ssl/ssl.go, pkg/protocols/websocket/websocket.go, pkg/protocols/whois/whois.go, pkg/tmplexec/flow/flow_executor.go, pkg/tmplexec/flow/flow_internal.go, pkg/tmplexec/multiproto/multi.go",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Skip baseValues keys in evaluateVarsWithInteractsh (pkg/fuzz/execute.go:233-256) only, leaving the variables.go precedence override, the quoted-literal injection in expressions.go, DSL/word matchers and the per-protocol builders open."
 },
 "out_of_scope_notes": [
  "The interactsh marker regex character class [B|b] also accepts '|' (pkg/protocols/common/interactsh/const.go:11); the fix hardens it, but it is a marker-parsing correctness issue rather than the disclosure itself.",
  "Env vars reach the value map only when -env-vars is set (pkg/protocols/common/generators/options.go:36-37); the same re-evaluation also allows invoking DSL helpers from response data (e.g. wait_for), which is a separate impact."
 ],
 "unverified": [
  "pinned_commit SHA not provided; assumed to be the parent of the fix commit as staged in repo/.",
  "repo_mb not measured (no shell); giant_repo/tiny_repo not assessed, though nuclei is neither tiny nor near 1.5 GB by typical size.",
  "O1 counts distinct template protocol/executor entry points (http, http self-contained, DAST fuzz, headless, network, javascript, code, dns, ssl, websocket, whois, flow, multi-protocol) plus matchers within them; exact grouping is a judgement call.",
  "O8 empty: every non-test expressions.Evaluate/EvaluateByte/Variables.Evaluate/Interactsh.Replace caller at the pin is in the fix diff. Remaining replacer.Replace callers (dns.go:238, whois.go:104, network/request.go:179, authx/dynamic.go) do single-pass substitution without helper evaluation and were judged outside the sink. Latest tree not diffed since O8 is empty.",
  "O11 is well over the 45-minute fairness budget: the published fix spans 27 source files and introduces a new render package and scope type. A task would need to be scoped down (e.g. fuzz + variables + matchers) to be fair.",
  "protection_documented_without_exceptions not checked in docs."
 ]
}
  ```
- Published fix sites:   - pkg/fuzz/execute.go:155 — entry point: CLI `nuclei -dast` fuzzing templates (no generator) [fuzz engine (landing)]
  - pkg/fuzz/execute.go:176 — entry point: CLI `nuclei -dast` fuzzing templates with payload generator [fuzz engine (landing)]
  - pkg/fuzz/execute.go:250 — entry point: CLI `nuclei -dast` (evaluateVarsWithInteractsh) [fuzz engine (landing)]
  - pkg/fuzz/parts.go:199-201 — entry point: CLI `nuclei -dast` payload rendering per fuzz point [fuzz engine]
  - pkg/protocols/common/variables/variables.go:84-87 — entry point: every protocol's Variables.Evaluate call (http, dns, ssl, websocket, whois, network, headless, js, code, flow, multiproto) [shared variable evaluator (merge/precedence layer)]
  - pkg/protocols/common/variables/variables.go:118-124 — entry point: EvaluateWithInteractsh from fuzz and HTTP request builder [shared variable evaluator]
  - pkg/protocols/common/expressions/expressions.go:58 — entry point: all template rendering (helper args with quoted {{var}} placeholders) [lower-level expression API]
  - pkg/operators/matchers/match.go:68 — entry point: word matchers in any template [operators (matcher)]
  - pkg/operators/matchers/match.go:198 — entry point: DSL matchers with unresolved {{var}} placeholders [operators (matcher)]
  - pkg/protocols/http/build_request.go:168-183 — entry point: HTTP templates (template context merge + interactsh replacement over payloads) [protocol request builder]
  - pkg/protocols/http/build_request.go:211 — entry point: HTTP templates [protocol request builder]
  - pkg/protocols/http/build_request.go:269 — entry point: HTTP self-contained templates [protocol request builder (second code path)]
  - pkg/protocols/http/build_request.go:475 — entry point: HTTP template headers [protocol request builder]
  - pkg/protocols/http/build_request.go:513 — entry point: HTTP template body [protocol request builder]
  - pkg/protocols/http/request.go:694 — entry point: HTTP executeRequest re-evaluating meta payloads against dynamic values [protocol executor]
  - pkg/protocols/code/code.go:203-208 — entry point: code protocol templates [protocol executor]
  - pkg/protocols/dns/request.go:52 — entry point: DNS templates [protocol executor]
  - pkg/protocols/dns/dns.go:207 — entry point: DNS templates (custom resolvers) [protocol executor]
  - pkg/protocols/headless/request.go:60 — entry point: headless templates [protocol executor]
  - pkg/protocols/headless/engine/page_actions.go:992 — entry point: headless page action args [protocol engine]
  - pkg/protocols/javascript/js.go:337 — entry point: javascript protocol templates [protocol executor]
  - pkg/protocols/javascript/js.go:554 — entry point: javascript protocol args interactsh replacement [protocol executor]
  - pkg/protocols/javascript/js.go:728 — entry point: javascript protocol args evaluation [protocol executor]
  - pkg/protocols/network/request.go:159 — entry point: network templates [protocol executor]
  - pkg/protocols/network/request.go:326-335 — entry point: network template inputs [protocol executor]
  - pkg/protocols/network/network.go:195 — entry point: network template compile-time input pre-render [protocol compiler]
  - pkg/protocols/ssl/ssl.go:223 — entry point: ssl templates [protocol executor]
  - pkg/protocols/websocket/websocket.go:183 — entry point: websocket templates [protocol executor]
  - pkg/protocols/whois/whois.go:95 — entry point: whois templates [protocol executor]
  - pkg/tmplexec/flow/flow_executor.go:115 — entry point: templates using `flow:` [template executor]
  - pkg/tmplexec/flow/flow_internal.go:20 — entry point: templates using `flow:` (re-evaluation after each protocol step) [template executor]
  - pkg/tmplexec/multiproto/multi.go:43 — entry point: multi-protocol templates (compile) [template executor]
  - pkg/tmplexec/multiproto/multi.go:122 — entry point: multi-protocol templates (re-evaluation after each protocol step) [template executor]
  - pkg/protocols/common/contextargs/contextargs.go:73-84 — entry point: template context store shared across protocols [state/provenance tracking]
  - pkg/protocols/common/interactsh/const.go:11 — entry point: interactsh marker detection (regex accepts '|' as an encoded-brace char) [marker parser]
  - pkg/protocols/protocols.go:207 — entry point: ExecutorOptions (new NewVariablesScope / AddTemplateCtxToVariablesScope helpers added near here) [public SDK-facing options API]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

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
- Append one row per route to `/home/mara/cwe-bench/precision_validation/root/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/pv-nuclei/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/pv-nuclei/instruction.md`)
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

## Tests (`tasks/pv-nuclei/tests/`)
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
- **Wrong-fix patches** go in `build/pv-nuclei/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/pv-nuclei/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/pv-nuclei/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/pv-nuclei/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py pv-nuclei --only static
python3 -I builder/gate.py pv-nuclei --only nop
python3 -I builder/gate.py pv-nuclei --only oracle
python3 -I builder/gate.py pv-nuclei --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/pv-nuclei/`;
  - edit only `tasks/pv-nuclei/`, `build/pv-nuclei/` and, for pattern B, the register;
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
