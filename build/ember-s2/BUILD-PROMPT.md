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

Project root: `/home/mara/cwe-bench`. Task: `ember-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-X3G7-QRWC-F6C5", "CVE-2026-54162", "GO-2026-6270"]; alexandre-daubois/ember; CWE-150 improper neutralization of escape, meta or control sequences (terminal escape-sequence injection into an operator TUI)
- Pinned (vulnerable) commit: 9f19916c7aa0112310967b7b0ccee80da2eddc70. Published fix: fcb7160e58dba58d6f9b5033cc312fdedc8c9f6b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash[1m]",
 "entry_id": "19743",
 "advisory_ids": [
  "GHSA-X3G7-QRWC-F6C5",
  "CVE-2026-54162",
  "GO-2026-6270"
 ],
 "repo": "alexandre-daubois/ember",
 "pinned_commit": "9f19916c7aa0112310967b7b0ccee80da2eddc70",
 "fix_commits": [
  "fcb7160e58dba58d6f9b5033cc312fdedc8c9f6b"
 ],
 "trust_decision": {
  "summary": "Externally-sourced strings that reach the operator's terminal must have C0 (0x00-0x1F), DEL (0x7F) and C1 (0x80-0x9F) code points stripped at the render boundary, while the parsed values themselves stay raw for --json/metrics and for aggregation keys; the fix decides this in internal/ui only, at every row/detail/status renderer.",
  "evidence": [
   "internal/ui/logtable.go:275-352",
   "internal/ui/logtable.go:18-28",
   "internal/ui/certificates.go:89-121",
   "internal/ui/app.go:364-369",
   "internal/ui/workerlist.go:139-149"
  ]
 },
 "landing_point": {
  "where": "internal/ui/logtable.go:275",
  "why": "The report says Caddy log fields reach the operator's TUI, so the first place an engineer reads is formatLogRow, the row renderer every access-log entry goes through (URI/host/method/raw line via fitCellLeft/fitCellRight at internal/ui/logtable.go:18-43)."
 },
 "fix_sites": [
  {
   "where": "internal/ui/logtable.go:18-28",
   "entry_point": "ember (default command -> runTUI, internal/app/run.go:124-128) - Logs tab",
   "module_kind": "internal/ui TUI renderer (shared fitCellLeft helper)"
  },
  {
   "where": "internal/ui/logtable.go:33-43",
   "entry_point": "ember (Logs tab, duration column)",
   "module_kind": "internal/ui TUI renderer (shared fitCellRight helper)"
  },
  {
   "where": "internal/ui/app.go:364-369",
   "entry_point": "ember (View status/error line, every tab)",
   "module_kind": "internal/ui TUI renderer (frame status line)"
  },
  {
   "where": "internal/ui/certificates.go:90-96",
   "entry_point": "ember (Certificates tab row)",
   "module_kind": "internal/ui TUI renderer (certificate table)"
  },
  {
   "where": "internal/ui/certificates.go:106-109",
   "entry_point": "ember (Certificates tab row, issuer column)",
   "module_kind": "internal/ui TUI renderer (certificate table)"
  },
  {
   "where": "internal/ui/detail.go:56-57",
   "entry_point": "ember (FrankenPHP tab -> thread detail panel)",
   "module_kind": "internal/ui TUI renderer (detail panel)"
  },
  {
   "where": "internal/ui/detail.go:59-62",
   "entry_point": "ember (FrankenPHP tab -> thread detail panel, URI)",
   "module_kind": "internal/ui TUI renderer (detail panel)"
  },
  {
   "where": "internal/ui/hostdetail.go:21-33",
   "entry_point": "ember (Caddy tab -> host detail panel, breadcrumb)",
   "module_kind": "internal/ui TUI renderer (host detail panel)"
  },
  {
   "where": "internal/ui/hostdetail.go:96-102",
   "entry_point": "ember (Caddy tab -> host detail panel, Methods table)",
   "module_kind": "internal/ui TUI renderer (host detail panel)"
  },
  {
   "where": "internal/ui/hosttable.go:89-95",
   "entry_point": "ember (Caddy tab host table, host column)",
   "module_kind": "internal/ui TUI renderer (host table)"
  },
  {
   "where": "internal/ui/logs.go:208-223",
   "entry_point": "ember (Logs tab empty-state hint)",
   "module_kind": "internal/ui TUI renderer (empty hint)"
  },
  {
   "where": "internal/ui/logsidepanel.go:233-245",
   "entry_point": "ember (Logs tab sidepanel host labels)",
   "module_kind": "internal/ui TUI renderer (sidepanel)"
  },
  {
   "where": "internal/ui/routestable.go:125-128",
   "entry_point": "ember (Logs -> By Route table, method column)",
   "module_kind": "internal/ui TUI renderer (routes table)"
  },
  {
   "where": "internal/ui/workerlist.go:139-149",
   "entry_point": "ember (FrankenPHP tab worker/thread list, method + URI)",
   "module_kind": "internal/ui TUI renderer (worker list)"
  },
  {
   "where": "fix.diff:171-199",
   "entry_point": "ember (shared helper called from every render sink above)",
   "module_kind": "new file internal/ui/sanitize.go"
  }
 ],
 "O1_entry_points": 1,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "internal/app/diff.go:317"
 },
 "O3_reason_to_dismiss": "`ember diff` is a non-interactive text report over snapshot files, not the operator's TUI, and its input already passed through JSON encoding, which escapes control bytes - so the argument goes that the advisory's TUI protection never covered it.",
 "O4_distance": {
  "files": 13,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Raw values must survive outside the terminal: JSONL emits hosts[].host and threads[].currentUri/currentMethod verbatim (internal/app/json.go:183-207, 223-244), route keys are built from the unmodified URI (internal/model/routepattern.go:36-62) and the typed filter matches those raw strings (internal/ui/logs.go:129-140); certificate sorting/filtering also uses raw Issuer/DNSNames (internal/ui/certificates.go:172, 182-197). A fix placed at ParseLogLine or NormalizeURI - the obvious single place - would change JSON output, merge or split route buckets and break filter matches. Separately, fitCellLeft must keep counting emoji/CJK as 2 display cells (internal/ui/logtable.go:12-17).",
  "where": "internal/app/json.go:183-207"
 },
 "O6_input_shapes": [
  "C0 controls 0x00-0x1F (ESC, BEL, CR, LF, TAB, NUL) in URI, host, method, logger, message, raw line",
  "DEL 0x7F",
  "C1 controls U+0080-U+009F supplied as UTF-8 multi-byte code points (CSI 0x9B, OSC 0x9D, ST 0x9C)",
  "OSC sequence, BEL-terminated (ESC ] ... BEL) - window-title spoof and OSC52 clipboard write",
  "OSC sequence, ST-terminated (ESC ] ... ESC backslash)",
  "CSI sequence (ESC [ 2J screen erase, SGR colour)",
  "control bytes carried in a query string of a request URI",
  "raw non-JSON log line (ParseError path)",
  "error strings that echo an external label (metrics parse error -> status line)",
  "printable multi-byte UTF-8 (emoji, CJK, accented Latin) must pass through unchanged",
  "invalid UTF-8 bytes collapse to U+FFFD",
  "empty and already-clean strings (no-op, no allocation)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "internal/fetcher/logentry.go:106-135",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "`ember diff` prints each per-host name from a snapshot with fmt.Fprintf to stdout, with no neutralisation (host = per-host metric label, ultimately the Host header)",
   "where": "internal/app/diff.go:317",
   "reason_to_dismiss": "diff is a text report over JSON files, not the TUI; JSON already escapes control bytes, so the value is 'trusted' by the time diff reads it",
   "distance": "one package away from internal/ui (internal/app), fed by internal/app/json.go:185 from internal/model/state.go:509-512",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "plugin tab error text is rendered raw into the TUI content area when a plugin group's Fetch failed",
   "where": "internal/ui/app.go:356-360",
   "reason_to_dismiss": "plugin errors come from locally installed plugin code and its own Fetch, not from Caddy log lines",
   "distance": "same file as the fixed status line, seven lines above it",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "upstream address, health URI/interval and LB policy are formatted straight into Upstreams table rows through fmt.Sprintf with no fitCell/sanitize helper",
   "where": "internal/ui/upstreamtable.go:122-126",
   "reason_to_dismiss": "upstream addresses and health URIs come from operator-authored Caddy config, not from request/log data",
   "distance": "internal/ui, a different tab and a different fetcher route (doFetchRPConfig) from the log path",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "internal/ui/config.go:359-364",
   "sibling": "config key rendered raw while string values go through %q",
   "why_realistic": "the Config tab already renders arbitrary Caddy JSON through a tree walker, so a maintainer wiring a remote/dynamic config source would hit the same raw-key render path and only quote values"
  },
  {
   "where": "internal/ui/plugin_bridge.go:100-107",
   "sibling": "third-party plugin View text rendered verbatim into the TUI frame",
   "why_realistic": "plugins receive live Caddy data through SafeFetch (docs/plugins.md) and return pre-rendered strings, so a plugin echoing a host or URI is a natural sibling sink"
  },
  {
   "where": "internal/ui/upstreamtable.go:170-174",
   "sibling": "upstream/health/LB columns built with fmt.Sprintf instead of a sanitising cell helper",
   "why_realistic": "the Upstreams tab is a newer table with its own config fetcher; a maintainer adding a table from a new data source would copy the older raw-format row style"
  },
  {
   "where": "internal/app/diff.go:314-319",
   "sibling": "a CSV/JSONL/text export subcommand that prints access-log fields to stdout",
   "why_realistic": "diff, status and init already form a family of non-TUI printers over the same collector, so an `ember logs`/`export` printer next to them is a natural addition"
  }
 ],
 "O9_family": "CWE-150 improper neutralization of escape, meta or control sequences (terminal escape-sequence injection into an operator TUI)",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.26 (go.mod:3), go modules pinned by go.sum, cobra CLI, bubbletea/lipgloss TUI; `go build ./...` and `go test ./internal/ui/...` need no services",
  "services": [],
  "offline_after_build": true,
  "project_tests": "internal/ui has broad unit coverage: logs_test.go, logtable_test.go, routestable_test.go, certificates_test.go, hosttable_test.go, hostdetail_test.go, logsidepanel_test.go, workerlist_test.go, detail_test.go, app_test.go, all using stripANSI (dashboard_test.go:228); fuzz targets config_fuzz_test.go and internal/fetcher/logentry_fuzz_test.go. Integration tests are build-tagged (`integration`, `integration_docker`) and need a live Caddy (internal/app/integration_test.go:1, internal/app/multi_caddy_smoke_test.go:1). At the pinned commit there is no test for control-byte injection in rendered output, and the helper newLogsApp used by the fix's added tests already exists (internal/ui/logs_test.go:17)."
 },
 "O11_fix_minutes": 45,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "internal/ui/app.go, internal/ui/certificates.go, internal/ui/detail.go, internal/ui/hostdetail.go, internal/ui/hosttable.go, internal/ui/logs.go, internal/ui/logsidepanel.go, internal/ui/logtable.go, internal/ui/routestable.go, internal/ui/sanitize.go, internal/ui/workerlist.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "strip control bytes once in fetcher.ParseLogLine (or NormalizeURI) so every consumer 'inherits' the fix"
 },
 "out_of_scope_notes": [
  "The Prometheus export path is a non-terminal HTTP sink and escapes only backslash, quote and newline (internal/exporter/exporter.go:745); not pursued."
 ],
 "unverified": [
  "repo_mb could not be measured (no shell/du in this session); tiny_repo is inferred from 133 Go files and 33,199 non-empty Go lines (~1.4 MB of source).",
  "Latest code was supplied as 'none', so present_in_latest/latest_where for every O8 route is unknown.",
  "The advisory body beyond the supplied summary was not available; scope reading rests on the summary plus the fix diff.",
  "O13 recall risk was assessed from project size and fix shape only; write-up breadth could not be checked offline."
 ]
}
  ```
- Published fix sites:   - internal/ui/logtable.go:18-28 — entry point: ember (default command -> runTUI, internal/app/run.go:124-128) - Logs tab [internal/ui TUI renderer (shared fitCellLeft helper)]
  - internal/ui/logtable.go:33-43 — entry point: ember (Logs tab, duration column) [internal/ui TUI renderer (shared fitCellRight helper)]
  - internal/ui/app.go:364-369 — entry point: ember (View status/error line, every tab) [internal/ui TUI renderer (frame status line)]
  - internal/ui/certificates.go:90-96 — entry point: ember (Certificates tab row) [internal/ui TUI renderer (certificate table)]
  - internal/ui/certificates.go:106-109 — entry point: ember (Certificates tab row, issuer column) [internal/ui TUI renderer (certificate table)]
  - internal/ui/detail.go:56-57 — entry point: ember (FrankenPHP tab -> thread detail panel) [internal/ui TUI renderer (detail panel)]
  - internal/ui/detail.go:59-62 — entry point: ember (FrankenPHP tab -> thread detail panel, URI) [internal/ui TUI renderer (detail panel)]
  - internal/ui/hostdetail.go:21-33 — entry point: ember (Caddy tab -> host detail panel, breadcrumb) [internal/ui TUI renderer (host detail panel)]
  - internal/ui/hostdetail.go:96-102 — entry point: ember (Caddy tab -> host detail panel, Methods table) [internal/ui TUI renderer (host detail panel)]
  - internal/ui/hosttable.go:89-95 — entry point: ember (Caddy tab host table, host column) [internal/ui TUI renderer (host table)]
  - internal/ui/logs.go:208-223 — entry point: ember (Logs tab empty-state hint) [internal/ui TUI renderer (empty hint)]
  - internal/ui/logsidepanel.go:233-245 — entry point: ember (Logs tab sidepanel host labels) [internal/ui TUI renderer (sidepanel)]
  - internal/ui/routestable.go:125-128 — entry point: ember (Logs -> By Route table, method column) [internal/ui TUI renderer (routes table)]
  - internal/ui/workerlist.go:139-149 — entry point: ember (FrankenPHP tab worker/thread list, method + URI) [internal/ui TUI renderer (worker list)]
  - fix.diff:171-199 — entry point: ember (shared helper called from every render sink above) [new file internal/ui/sanitize.go]
- Uncovered routes to confirm (pattern B):   - internal/app/diff.go:317 — `ember diff` prints each per-host name from a snapshot with fmt.Fprintf to stdout, with no neutralisation (host = per-host metric label, ultimately the Host header) (reason to dismiss: diff is a text report over JSON files, not the TUI; JSON already escapes control bytes, so the value is 'trusted' by the time diff reads it; still in latest: unknown)
  - internal/ui/app.go:356-360 — plugin tab error text is rendered raw into the TUI content area when a plugin group's Fetch failed (reason to dismiss: plugin errors come from locally installed plugin code and its own Fetch, not from Caddy log lines; still in latest: unknown)
  - internal/ui/upstreamtable.go:122-126 — upstream address, health URI/interval and LB policy are formatted straight into Upstreams table rows through fmt.Sprintf with no fitCell/sanitize helper (reason to dismiss: upstream addresses and health URIs come from operator-authored Caddy config, not from request/log data; still in latest: unknown)
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

## Environment (`tasks/ember-s2/environment/Dockerfile`)
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

## Report to the solver (`tasks/ember-s2/instruction.md`)
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

## Tests (`tasks/ember-s2/tests/`)
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
- **Wrong-fix patches** go in `build/ember-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/ember-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ember-s2/manifest.json`:**
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

**Also in `build/ember-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py ember-s2 --only static
python3 -I common/gate/gate.py ember-s2 --only nop
python3 -I common/gate/gate.py ember-s2 --only oracle
python3 -I common/gate/gate.py ember-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ember-s2/`;
  - edit only `tasks/ember-s2/`, `build/ember-s2/` and, for pattern B, the register;
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
