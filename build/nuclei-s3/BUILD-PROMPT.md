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

Project root: `/home/mara/cwe-bench`. Task: `nuclei-s3`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-JPVM-9FRM-HJCQ", "CVE-2026-76805", "GO-2026-6571"]; projectdiscovery/nuclei; template/DSL expression injection from untrusted runtime data: response-derived values re-evaluated as template source, exposing environment variables (CWE-200 information exposure)
- Pinned (vulnerable) commit: 1e294aa7b908bc7dd89aa0b6e1b586eb4e47ab12. Published fix: ccbfb12bd01447ba25f6e755dfb2bee677736da6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "18195",
 "advisory_ids": [
  "GHSA-JPVM-9FRM-HJCQ",
  "CVE-2026-76805",
  "GO-2026-6571"
 ],
 "repo": "projectdiscovery/nuclei",
 "pinned_commit": "1e294aa7b908bc7dd89aa0b6e1b586eb4e47ab12",
 "fix_commits": [
  "ccbfb12bd01447ba25f6e755dfb2bee677736da6"
 ],
 "trust_decision": {
  "summary": "Decided once, at the boundary where a string enters evaluation: template-variable declarations and template-authored payload text are SOURCE and may be rendered, while values coming from runtime data, CLI options, constants and the cross-protocol template context are DATA and must never be re-scanned or compiled. The pinned code has no such notion: expressions.evaluate substitutes map values into the expression string before govaluate compiles it (expressions.go:58-61), and variables.EvaluateWithInteractsh uses an already-present runtime value as the string to evaluate (variables.go:117-124).",
  "evidence": [
   "pkg/protocols/common/expressions/expressions.go:55-61",
   "pkg/protocols/common/variables/variables.go:117-126",
   "pkg/protocols/common/variables/variables.go:146-153",
   "pkg/fuzz/execute.go:151-159",
   "pkg/fuzz/execute.go:233-256"
  ]
 },
 "landing_point": {
  "where": "pkg/fuzz/execute.go:151-159",
  "why": "The advisory names DAST/fuzz mode; the fuzz rule merges response/runtime values into input.Values and then re-evaluates every value of that map (execute.go:222-257), which is the first place an engineer reading the summary looks."
 },
 "fix_sites": [
  {
   "where": "pkg/fuzz/execute.go:151-159",
   "entry_point": "fuzzing/DAST rules attached to http: and headless: templates (fuzz.Rule.Execute)",
   "module_kind": "protocol engine (fuzz/DAST)"
  },
  {
   "where": "pkg/fuzz/parts.go:194-203",
   "entry_point": "fuzz payload rendering per component (executeEvaluate)",
   "module_kind": "protocol engine (fuzz/DAST)"
  },
  {
   "where": "fix.diff:771",
   "entry_point": "dsl: matchers on any template (new dsl_string_markers.go)",
   "module_kind": "operators/matchers (shared, second implementation)"
  },
  {
   "where": "pkg/operators/matchers/match.go:196-207",
   "entry_point": "matchers type dsl and type word (Matcher.MatchDSL / MatchWords)",
   "module_kind": "operators/matchers (shared, second implementation)"
  },
  {
   "where": "pkg/protocols/code/code.go:196-212",
   "entry_point": "code: templates (Request.ExecuteWithResults)",
   "module_kind": "protocol (code)"
  },
  {
   "where": "pkg/protocols/common/contextargs/contextargs.go:73-84",
   "entry_point": "cross-protocol template context store used by multiprotocol/flow and workflows",
   "module_kind": "shared state (context store)"
  },
  {
   "where": "pkg/protocols/common/contextargs/contextargs.go:196-204",
   "entry_point": "template-context Clone at every nested protocol/subtemplate dispatch",
   "module_kind": "shared state (save/reload boundary)"
  },
  {
   "where": "pkg/protocols/common/expressions/expressions.go:55-89",
   "entry_point": "expressions.Evaluate / EvaluateByte, reached by every protocol render",
   "module_kind": "shared expression evaluator"
  },
  {
   "where": "pkg/protocols/common/interactsh/const.go:11",
   "entry_point": "interactsh marker detection used by all protocols",
   "module_kind": "shared (marker parsing)"
  },
  {
   "where": "pkg/protocols/common/interactsh/interactsh.go:276-290",
   "entry_point": "Client.Replace called by http, network, headless, javascript, code, fuzz",
   "module_kind": "shared (marker allocation)"
  },
  {
   "where": "pkg/protocols/common/marker/marker.go:1-10",
   "entry_point": "marker constants used by every render site",
   "module_kind": "shared (marker parsing)"
  },
  {
   "where": "fix.diff:1975",
   "entry_point": "new render.Render/RenderMap boundary consumed by all protocols (pkg/protocols/common/render/render.go)",
   "module_kind": "shared render boundary (new package)"
  },
  {
   "where": "fix.diff:2446",
   "entry_point": "new variables.Scope used by every EvaluateScope caller (pkg/protocols/common/variables/scope.go)",
   "module_kind": "shared variable scope (new file)"
  },
  {
   "where": "pkg/protocols/common/variables/variables.go:104-128",
   "entry_point": "variables: section evaluation for every protocol type",
   "module_kind": "shared variables"
  },
  {
   "where": "pkg/protocols/dns/dns.go:204-214",
   "entry_point": "dns: templates (resolvers)",
   "module_kind": "protocol (dns)"
  },
  {
   "where": "pkg/protocols/dns/request.go:45-53",
   "entry_point": "dns: templates (Request.ExecuteWithResults)",
   "module_kind": "protocol (dns)"
  },
  {
   "where": "pkg/protocols/headless/engine/page_actions.go:974-998",
   "entry_point": "headless: step arguments (Page.getActionArg)",
   "module_kind": "protocol (headless)"
  },
  {
   "where": "pkg/protocols/headless/request.go:52-63",
   "entry_point": "headless: templates (Request.ExecuteWithResults)",
   "module_kind": "protocol (headless)"
  },
  {
   "where": "pkg/protocols/http/build_request.go:211-241",
   "entry_point": "http:/requests: templates, raw and self-contained (requestGenerator.Make)",
   "module_kind": "protocol (http)"
  },
  {
   "where": "pkg/protocols/http/request.go:685-697",
   "entry_point": "http request execution re-evaluating generatedRequest.meta",
   "module_kind": "protocol (http)"
  },
  {
   "where": "pkg/protocols/javascript/js.go:340-353",
   "entry_point": "javascript: templates (Request.executeWithResults)",
   "module_kind": "protocol (javascript)"
  },
  {
   "where": "pkg/protocols/javascript/js.go:723-739",
   "entry_point": "javascript: args rendering (Request.evaluateArgs)",
   "module_kind": "protocol (javascript)"
  },
  {
   "where": "pkg/protocols/network/network.go:191-198",
   "entry_point": "network: templates at compile time (Request.Compile)",
   "module_kind": "protocol (network)"
  },
  {
   "where": "pkg/protocols/network/request.go:322-337",
   "entry_point": "network: templates (Request.executeRequestWithPayloads)",
   "module_kind": "protocol (network)"
  },
  {
   "where": "pkg/protocols/protocols.go:206-250",
   "entry_point": "ExecutorOptions.GetTemplateCtx/AddTemplateVars, used by every multiprotocol/flow dispatch",
   "module_kind": "shared executor options"
  },
  {
   "where": "pkg/protocols/ssl/ssl.go:216-232",
   "entry_point": "ssl: templates (Request.ExecuteWithResults)",
   "module_kind": "protocol (ssl)"
  },
  {
   "where": "pkg/protocols/websocket/websocket.go:177-206",
   "entry_point": "websocket: templates (Request.executeRequestWithPayloads)",
   "module_kind": "protocol (websocket)"
  },
  {
   "where": "pkg/protocols/websocket/websocket.go:300-317",
   "entry_point": "websocket: inputs (readWriteInputWebsocket)",
   "module_kind": "protocol (websocket)"
  },
  {
   "where": "pkg/protocols/whois/whois.go:92-97",
   "entry_point": "whois: templates (Request.ExecuteWithResults)",
   "module_kind": "protocol (whois)"
  },
  {
   "where": "pkg/tmplexec/flow/flow_executor.go:110-120",
   "entry_point": "flow: templates (FlowExecutor.Compile)",
   "module_kind": "template engine (flow)"
  },
  {
   "where": "pkg/tmplexec/flow/flow_internal.go:17-24",
   "entry_point": "flow: per-protocol variable refresh (requestExecutor defer)",
   "module_kind": "template engine (flow)"
  },
  {
   "where": "pkg/tmplexec/multiproto/multi.go:34-47",
   "entry_point": "multiprotocol templates (MultiProtocol.Compile)",
   "module_kind": "template engine (multiproto)"
  }
 ],
 "O1_entry_points": 12,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "pkg/operators/matchers/match.go:196-207"
 },
 "O3_reason_to_dismiss": "Matchers are not DAST/fuzz payload rendering: the advisory is about fuzzing mode, the DSL expression is template-authored, and the response value only appears as a literal inside an already-quoted string, so it reads as a matcher-semantics question rather than the fuzzing disclosure.",
 "O4_distance": {
  "files": 29,
  "packages": 20,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A runtime value must still shadow a declared template variable (server-issued login token replaces a declared empty token; a server-edited upload filename replaces the initial one) - it just must stop being rendered as template text.",
  "where": "pkg/protocols/common/variables/variables.go:117-126"
 },
 "O6_input_shapes": [
  "raw {{interactsh-url}} vs fully percent-encoded %7B%7Binteractsh-url%7D%7D vs mixed raw/encoded brace pairs",
  "runtime value substituted inside a single-quoted vs double-quoted DSL string literal",
  "{{name}} parenthesis marker vs the general section marker form",
  "scalar string value vs []interface{} slice payload (slices are copied, never evaluated)",
  "value strings containing quotes, backslashes, newlines, tabs and carriage returns",
  "template-authored helper call wrapping a marker, e.g. {{url_encode('{{interactsh-url}}')}}",
  "marker that only appears after a first render pass, i.e. produced by a payload/variable indirection"
 ],
 "O7_producer": {
  "kind": "cache",
  "where": "pkg/protocols/common/contextargs/contextargs.go:196-204 (Clone of the template-context store) fed by pkg/protocols/protocols.go:226-250 AddTemplateVars from response output events",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [],
 "O8b_injection_room": [
  {
   "where": "pkg/authprovider/authx/dynamic.go:131-177",
   "sibling": "a third substitution subsystem that inserts extracted response values into headers/cookies/params with replacer.Replace",
   "why_realistic": "dynamic secrets are already computed from a login response; a maintainer adding helper evaluation for 'secret derived from the login page' would land here, and the fix never touches pkg/authprovider"
  },
  {
   "where": "pkg/operators/extractors/extract.go:177-193",
   "sibling": "an extractor twin of MatchDSL that resolves markers before evaluating",
   "why_realistic": "ExtractDSL already mirrors MatchDSL's compile/evaluate shape; adding marker resolution to it is a natural symmetry change"
  },
  {
   "where": "pkg/protocols/common/interactsh/interactsh.go:282-290",
   "sibling": "Client.ReplaceWithMarker still takes a caller-supplied regex and stays exported",
   "why_realistic": "a new protocol or a custom transport would naturally reuse this exported helper on whatever string it has, including runtime data"
  },
  {
   "where": "pkg/protocols/http/request.go:1110-1114",
   "sibling": "a render step in output-event shaping (responseToDSLMap + template context merge)",
   "why_realistic": "this is where response fields become variables for the next step, so a maintainer adding 'evaluate the output template' would put it here"
  }
 ],
 "O9_family": "template/DSL expression injection from untrusted runtime data: response-derived values re-evaluated as template source, exposing environment variables (CWE-200 information exposure)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.25.7 (go.mod:3); standard go build ./... and go test ./..., cgo not required for the affected packages",
  "services": [],
  "offline_after_build": true,
  "project_tests": "pkg/protocols/common/expressions/expressions_test.go (already has the partial protection test TestEvaluateDoesNotExecuteHelpersFromResolvedValues), pkg/protocols/common/variables/variables_test.go, pkg/protocols/common/contextargs/contextargs_test.go, pkg/operators/matchers/match_test.go, pkg/protocols/http/build_request_test.go, pkg/fuzz/execute_race_test.go; pkg/fuzz/parts_test.go is only a two-line 'TODO: Write tests' stub, so the DAST/fuzz rendering path itself has no test at the pin"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "pkg/fuzz/execute.go, pkg/fuzz/parts.go, pkg/operators/matchers/dsl_string_markers.go, pkg/operators/matchers/match.go, pkg/protocols/code/code.go, pkg/protocols/common/contextargs/contextargs.go, pkg/protocols/common/expressions/expressions.go, pkg/protocols/common/interactsh/const.go, pkg/protocols/common/interactsh/interactsh.go, pkg/protocols/common/marker/marker.go, pkg/protocols/common/render/render.go, pkg/protocols/common/variables/scope.go, pkg/protocols/common/variables/variables.go, pkg/protocols/dns/dns.go, pkg/protocols/dns/request.go, pkg/protocols/headless/engine/page_actions.go, pkg/protocols/headless/request.go, pkg/protocols/http/build_request.go, pkg/protocols/http/request.go, pkg/protocols/javascript/js.go, pkg/protocols/network/network.go, pkg/protocols/network/request.go, pkg/protocols/protocols.go, pkg/protocols/ssl/ssl.go, pkg/protocols/websocket/websocket.go, pkg/protocols/whois/whois.go, pkg/tmplexec/flow/flow_executor.go, pkg/tmplexec/flow/flow_internal.go, pkg/tmplexec/multiproto/multi.go",
  "j_sibling_sites": "no",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Stop re-rendering map values in the fuzz path only (drop or gate the evaluateVarsWithInteractsh loop), which leaves variables.Evaluate's data-override path, MatchDSL's recompile and the other protocols still executing response-derived markers."
 },
 "out_of_scope_notes": [
  "The fix commit also reflows the field alignment of ExecutorOptions.Copy (pkg/protocols/protocols.go) - whitespace only, no behaviour; counted as one touched file.",
  "Nothing outside this advisory's protection was pursued."
 ],
 "unverified": [
  "Repository source size in MB - no shell available, so repo_mb is null (652 .go files under pkg alone, clearly above 5 MB and below 1.5 GB).",
  "Exact fix-site count from the candidate metadata (76 sites / 27 files) - I counted 29 non-test source files by hand from the diff.",
  "O8: no route into the same sink that the published fix left untouched could be found at the pin; every pinned expressions.Evaluate caller is converted by the diff, so O8 is empty rather than unknown.",
  "Latest-release tree was not provided, so present_in_latest for any route would be unknown; O8 has no routes.",
  "Recall risk is a judgement from advisory ids and recency (published 2026-09-22), not measured."
 ]
}
  ```
- Published fix sites:   - pkg/fuzz/execute.go:151-159 — entry point: fuzzing/DAST rules attached to http: and headless: templates (fuzz.Rule.Execute) [protocol engine (fuzz/DAST)]
  - pkg/fuzz/parts.go:194-203 — entry point: fuzz payload rendering per component (executeEvaluate) [protocol engine (fuzz/DAST)]
  - fix.diff:771 — entry point: dsl: matchers on any template (new dsl_string_markers.go) [operators/matchers (shared, second implementation)]
  - pkg/operators/matchers/match.go:196-207 — entry point: matchers type dsl and type word (Matcher.MatchDSL / MatchWords) [operators/matchers (shared, second implementation)]
  - pkg/protocols/code/code.go:196-212 — entry point: code: templates (Request.ExecuteWithResults) [protocol (code)]
  - pkg/protocols/common/contextargs/contextargs.go:73-84 — entry point: cross-protocol template context store used by multiprotocol/flow and workflows [shared state (context store)]
  - pkg/protocols/common/contextargs/contextargs.go:196-204 — entry point: template-context Clone at every nested protocol/subtemplate dispatch [shared state (save/reload boundary)]
  - pkg/protocols/common/expressions/expressions.go:55-89 — entry point: expressions.Evaluate / EvaluateByte, reached by every protocol render [shared expression evaluator]
  - pkg/protocols/common/interactsh/const.go:11 — entry point: interactsh marker detection used by all protocols [shared (marker parsing)]
  - pkg/protocols/common/interactsh/interactsh.go:276-290 — entry point: Client.Replace called by http, network, headless, javascript, code, fuzz [shared (marker allocation)]
  - pkg/protocols/common/marker/marker.go:1-10 — entry point: marker constants used by every render site [shared (marker parsing)]
  - fix.diff:1975 — entry point: new render.Render/RenderMap boundary consumed by all protocols (pkg/protocols/common/render/render.go) [shared render boundary (new package)]
  - fix.diff:2446 — entry point: new variables.Scope used by every EvaluateScope caller (pkg/protocols/common/variables/scope.go) [shared variable scope (new file)]
  - pkg/protocols/common/variables/variables.go:104-128 — entry point: variables: section evaluation for every protocol type [shared variables]
  - pkg/protocols/dns/dns.go:204-214 — entry point: dns: templates (resolvers) [protocol (dns)]
  - pkg/protocols/dns/request.go:45-53 — entry point: dns: templates (Request.ExecuteWithResults) [protocol (dns)]
  - pkg/protocols/headless/engine/page_actions.go:974-998 — entry point: headless: step arguments (Page.getActionArg) [protocol (headless)]
  - pkg/protocols/headless/request.go:52-63 — entry point: headless: templates (Request.ExecuteWithResults) [protocol (headless)]
  - pkg/protocols/http/build_request.go:211-241 — entry point: http:/requests: templates, raw and self-contained (requestGenerator.Make) [protocol (http)]
  - pkg/protocols/http/request.go:685-697 — entry point: http request execution re-evaluating generatedRequest.meta [protocol (http)]
  - pkg/protocols/javascript/js.go:340-353 — entry point: javascript: templates (Request.executeWithResults) [protocol (javascript)]
  - pkg/protocols/javascript/js.go:723-739 — entry point: javascript: args rendering (Request.evaluateArgs) [protocol (javascript)]
  - pkg/protocols/network/network.go:191-198 — entry point: network: templates at compile time (Request.Compile) [protocol (network)]
  - pkg/protocols/network/request.go:322-337 — entry point: network: templates (Request.executeRequestWithPayloads) [protocol (network)]
  - pkg/protocols/protocols.go:206-250 — entry point: ExecutorOptions.GetTemplateCtx/AddTemplateVars, used by every multiprotocol/flow dispatch [shared executor options]
  - pkg/protocols/ssl/ssl.go:216-232 — entry point: ssl: templates (Request.ExecuteWithResults) [protocol (ssl)]
  - pkg/protocols/websocket/websocket.go:177-206 — entry point: websocket: templates (Request.executeRequestWithPayloads) [protocol (websocket)]
  - pkg/protocols/websocket/websocket.go:300-317 — entry point: websocket: inputs (readWriteInputWebsocket) [protocol (websocket)]
  - pkg/protocols/whois/whois.go:92-97 — entry point: whois: templates (Request.ExecuteWithResults) [protocol (whois)]
  - pkg/tmplexec/flow/flow_executor.go:110-120 — entry point: flow: templates (FlowExecutor.Compile) [template engine (flow)]
  - pkg/tmplexec/flow/flow_internal.go:17-24 — entry point: flow: per-protocol variable refresh (requestExecutor defer) [template engine (flow)]
  - pkg/tmplexec/multiproto/multi.go:34-47 — entry point: multiprotocol templates (MultiProtocol.Compile) [template engine (multiproto)]
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
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/nuclei-s3/environment/Dockerfile`)
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

## Report to the solver (`tasks/nuclei-s3/instruction.md`)
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

## Tests (`tasks/nuclei-s3/tests/`)
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
- **Wrong-fix patches** go in `build/nuclei-s3/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/nuclei-s3/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/nuclei-s3/manifest.json`:**
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

**Also in `build/nuclei-s3/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py nuclei-s3 --only static
python3 -I common/gate/gate.py nuclei-s3 --only nop
python3 -I common/gate/gate.py nuclei-s3 --only oracle
python3 -I common/gate/gate.py nuclei-s3 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/nuclei-s3/`;
  - edit only `tasks/nuclei-s3/`, `build/nuclei-s3/` and, for pattern B, the register;
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
