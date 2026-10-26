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

Project root: `/home/mara/cwe-bench`. Task: `librenms-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-7W8C-QGXG-M7JX", "CVE-2026-84192"]; librenms/librenms; CWE-79 stored XSS (output encoding of device-sourced data in server-rendered legacy PHP templates)
- Pinned (vulnerable) commit: 44bb4ecc0eb9e66b39abce2b77710ebc18fd57e8. Published fix: 6782af940c3c495755923b520a302f3a1cb1ce6b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "33021",
 "advisory_ids": [
  "GHSA-7W8C-QGXG-M7JX",
  "CVE-2026-84192"
 ],
 "repo": "librenms/librenms",
 "pinned_commit": "44bb4ecc0eb9e66b39abce2b77710ebc18fd57e8",
 "fix_commits": [
  "6782af940c3c495755923b520a302f3a1cb1ce6b"
 ],
 "trust_decision": {
  "summary": "Device-supplied strings (SNMP-polled descr/name fields, syslog program/date, Oxidized node data, serialized alert details) are treated as trusted HTML and concatenated raw into legacy PHP page output; the decision to output-encode is made (or not) at each echo site in includes/html/*.",
  "evidence": [
   "includes/html/print-syslog.inc.php:11",
   "includes/html/functions.inc.php:586",
   "includes/html/pages/device/health/storage.inc.php:27",
   "includes/html/pages/routing/bgp.inc.php:329"
  ]
 },
 "landing_point": {
  "where": "includes/html/print-syslog.inc.php:11",
  "why": "The summary names Syslog data in legacy templates; the legacy syslog row printer escapes msg but echoes program and date raw."
 },
 "fix_sites": [
  {
   "where": "includes/html/functions.inc.php:511",
   "entry_point": "alerts table ajax (includes/html/table/alerts.inc.php:131 -> alert_details -> format_alert_details), bill/port/isis/sensor/service/bgp/mempool/generic/app branches 511-630",
   "module_kind": "shared HTML helper rendering deserialized alert_log details"
  },
  {
   "where": "includes/html/pages/device/health/mempool.inc.php:38",
   "entry_point": "device page, tab=health metric=mempool",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/health/sensors.inc.php:22",
   "entry_point": "device page, tab=health metric=<sensor class> (included via includes/html/pages/device/health.inc.php:113)",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/health/storage.inc.php:23",
   "entry_point": "device page, tab=health metric=storage (also JS overlib popup at :27)",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/port/vlans.inc.php:14",
   "entry_point": "device port page, view=vlans",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/processes.inc.php:84",
   "entry_point": "device page, tab=processes",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/routing/bgp.inc.php:19",
   "entry_point": "device page, tab=routing proto=bgp",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/device/showconfig.inc.php:274",
   "entry_point": "device page, tab=showconfig (Oxidized node info and version list)",
   "module_kind": "legacy page template fed by external Oxidized API"
  },
  {
   "where": "includes/html/pages/device/slas.inc.php:7",
   "entry_point": "device page, tab=slas id=<sla> (detail branch only)",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/pages/eventlog.inc.php:58",
   "entry_point": "eventlog page (reflected $vars['device'] in hidden input)",
   "module_kind": "legacy page template, request parameter not SNMP data"
  },
  {
   "where": "includes/html/pages/graphs.inc.php:194",
   "entry_point": "graphs page (graph_descr config value)",
   "module_kind": "legacy page template, config value"
  },
  {
   "where": "includes/html/pages/routing/bgp.inc.php:304",
   "entry_point": "global routing page, protocol=bgp",
   "module_kind": "legacy page template (second copy of device bgp table)"
  },
  {
   "where": "includes/html/pages/routing/vrf.inc.php:115",
   "entry_point": "global routing page, protocol=vrf",
   "module_kind": "legacy page template"
  },
  {
   "where": "includes/html/print-syslog.inc.php:9",
   "entry_point": "device overview syslog panel (includes/html/pages/device/overview/syslog.inc.php:15)",
   "module_kind": "legacy include partial"
  },
  {
   "where": "includes/html/print-vrf.inc.php:9",
   "entry_point": "device page, tab=routing proto=vrf (includes/html/pages/device/routing/vrf.inc.php:86)",
   "module_kind": "legacy include partial"
  },
  {
   "where": "resources/views/map/custom-list.blade.php:24",
   "entry_point": "custom maps list route (maps.custom.*)",
   "module_kind": "modern Blade view, user-entered map name"
  }
 ],
 "O1_entry_points": 16,
 "O2_out_of_scope_site": {
  "kind": "save_reload_or_serialization",
  "where": "includes/html/functions.inc.php:457-460 (alert_details gzuncompress/json_decode of alert_log.details written at LibreNMS/Alert/RunAlerts.php:391) rendered by format_alert_details includes/html/functions.inc.php:504-653"
 },
 "O3_reason_to_dismiss": "Alert details are a snapshot produced internally by the alerting engine and stored compressed in alert_log, not 'SNMP/syslog data in a template', and the modern alert-log view already escapes (resources/views/alerts/fault-detail.blade.php:14-18), so a solver can argue the legacy alerts table is a separate, internal-data path.",
 "O4_distance": {
  "files": 16,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Helpers return intentional HTML (generate_port_link/Url::portLink, Url::sensorLink, Url::overlibLink with graph <img> contents, describe_bgp_error_code + '<br/>' separator, SLA name wrapped in <a> for jitter-type SLAs); escaping the assembled $fault_detail / $last_error / $name / overlib contents instead of the raw fields breaks links, line breaks and popups. cleanPort already htmlentities ifAlias/ifDescr/ifName, so re-escaping its output double-encodes port labels.",
  "where": "includes/html/functions.inc.php:519-526; includes/rewrites.php:48-50; includes/html/pages/routing/bgp.inc.php:301-306; includes/html/pages/device/slas.inc.php:120-124; LibreNMS/Util/Url.php:456-476"
 },
 "O6_input_shapes": [
  "plain HTML element text (td/h3/strong content)",
  "HTML attribute value (option value= at showconfig, hidden input value= at eventlog)",
  "href path segment (print-vrf routing/vrf/<RD>/)",
  "JavaScript string inside an onmouseover attribute (storage fs_popup overlib('...'))",
  "key-dependent array branches in deserialized alert detail rows (bill, port, isis, sensor state_descr, service, bgp, mempool, generic type/label/error, app)",
  "value passed through cleanPort before vs after branch selection (isis branch previously skipped cleanPort, leaving ifAlias raw at functions.inc.php:526)",
  "ipmi vs non-ipmi sensor name (ipmiSensorName rewrite output)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "LibreNMS/Alert/RunAlerts.php:391 and LibreNMS/Alert/AlertRules.php:126 (gzcompress(json_encode(details))) consumed at includes/html/functions.inc.php:460",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "port-page sensor panel is a twin of the fixed health/sensors code (ipmi and plain branches) and prints sensor_descr raw",
   "where": "includes/html/pages/device/port/sensors.inc.php:13-23",
   "reason_to_dismiss": "it is a port sub-view, not the health tab named by the fix; sensors 'belong' to health",
   "distance": "includes/html/pages/device/port vs device/health",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "wireless sensors page prints sensor_descr raw in the panel title",
   "where": "includes/html/pages/device/wireless.inc.php:81-96",
   "reason_to_dismiss": "wireless sensors are a separate sensor family with their own table/tab",
   "distance": "includes/html/pages/device, other tab",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "SLA list branch of the same file leaves tag/owner raw when the name is wrapped in a link for jitter-type SLAs (htmlentities only in the else branch)",
   "where": "includes/html/pages/device/slas.inc.php:110-124",
   "reason_to_dismiss": "the fix escaped the identical lines at :7/:11 and the list branch already has htmlentities, so it looks handled",
   "distance": "same file as fixed site",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "format_alert_details fallback branch dumps every *id/desc/msg/last* key/value raw",
   "where": "includes/html/functions.inc.php:641-645",
   "reason_to_dismiss": "generic debug-style fallback for unknown rule types; fix added e() only to the named branches",
   "distance": "same function as fixed sites",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "global VRF page inconsistency overlib popup prints vrf_name of both VRFs raw inside JS string",
   "where": "includes/html/pages/routing/vrf.inc.php:126",
   "reason_to_dismiss": "tooltip only shown on mismatch; fix escaped the visible cells 115-117 of the same loop",
   "distance": "same file as fixed site",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "device overview storage panel passes storage_descr raw as overlibLink text (Url::overlibLink does not escape $text)",
   "where": "includes/html/pages/device/overview/storage.inc.php:77",
   "reason_to_dismiss": "overview widget, not the health/storage page that was fixed; tooltip content is escaped by generate_overlib_content so it looks safe",
   "distance": "sibling directory (overview vs health), helper in LibreNMS/Util/Url.php:473",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "MPLS LSP/path/service tables print mplsLspName and vrf_name raw (global copy)",
   "where": "includes/html/pages/routing/mpls.inc.php:141-143",
   "reason_to_dismiss": "MPLS is a neighbouring routing feature not named in the advisory",
   "distance": "same directory as fixed routing/bgp and routing/vrf",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "device MPLS page copy of the same raw mplsLspName/vrf_name cells",
   "where": "includes/html/pages/device/routing/mpls.inc.php:139-141",
   "reason_to_dismiss": "same as above; second copy",
   "distance": "same directory as fixed device/routing/bgp",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "hrDevice inventory prints hrDeviceDescr raw in link text and overlib JS popup",
   "where": "includes/html/pages/device/hrdevice.inc.php:14-17",
   "reason_to_dismiss": "inventory tab, not health/routing; nothing in the fix touches it",
   "distance": "includes/html/pages/device, other tab",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "wireless sensors edit page prints sensor_descr raw in cell and data- attribute",
   "where": "includes/html/pages/device/edit/wireless-sensors.inc.php:43",
   "reason_to_dismiss": "admin-only edit page",
   "distance": "includes/html/pages/device/edit",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "storage popup: fixed code uses e() (HTML entity) inside a JS string within an HTML attribute; the attribute parser decodes &#039; back to a quote before overlib runs",
   "where": "includes/html/pages/device/health/storage.inc.php:27",
   "reason_to_dismiss": "site already 'fixed' by the published patch, so a solver copying the patch believes it is done",
   "distance": "fixed file; correct pattern lives in LibreNMS/Util/Url.php:191 (addslashes(htmlentities(...)))",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "includes/html/functions.inc.php:615-633",
   "sibling": "another alert-detail branch (e.g. processor or storage rows) built from deserialized alert_log fields",
   "why_realistic": "format_alert_details grows one isset() branch per entity type; a maintainer adding a new type copies the old unescaped pattern"
  },
  {
   "where": "includes/html/pages/device/overview/storage.inc.php:77",
   "sibling": "overview panel for mempools/processors passing descr raw into Url::overlibLink",
   "why_realistic": "overview panels follow the same overlibLink idiom and overlibLink leaves $text unescaped by design (it also carries minigraph HTML)"
  },
  {
   "where": "LibreNMS/Util/Url.php:456",
   "sibling": "wrapper helper that builds an overlib tooltip from a descr without addslashes",
   "why_realistic": "Url.php already mixes escaped (portLink:191) and unescaped helpers"
  }
 ],
 "O9_family": "CWE-79 stored XSS (output encoding of device-sourced data in server-rendered legacy PHP templates)",
 "O9_dos": false,
 "O10_build": {
  "language": "PHP 8.2+",
  "toolchain": "composer, Laravel 12, PHPUnit 11/12 (composer.json:17,40,75)",
  "services": [
   "MySQL/MariaDB for DB-backed pages",
   "optional RRDtool"
  ],
  "offline_after_build": true,
  "project_tests": "No tests in tests/ reference alert_details, format_alert_details, print-syslog or cleanPort; legacy page includes have no unit coverage. format_alert_details is a pure function and testable in isolation; page includes need a seeded DB."
 },
 "O11_fix_minutes": 90,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "includes/html/functions.inc.php, includes/html/pages/device/health/{mempool,sensors,storage}.inc.php, includes/html/pages/device/port/vlans.inc.php, includes/html/pages/device/processes.inc.php, includes/html/pages/device/routing/bgp.inc.php, includes/html/pages/device/showconfig.inc.php, includes/html/pages/device/slas.inc.php, includes/html/pages/eventlog.inc.php, includes/html/pages/graphs.inc.php, includes/html/pages/routing/bgp.inc.php, includes/html/pages/routing/vrf.inc.php, includes/html/print-syslog.inc.php, includes/html/print-vrf.inc.php, resources/views/map/custom-list.blade.php",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Wrap program/date in e() in print-syslog.inc.php (and maybe the bgp tables) and stop, missing the alert-details renderer, the overlib JS-attribute contexts and the twin port/wireless sensor, SLA-list, MPLS and hrdevice routes."
 },
 "out_of_scope_notes": [
  "Published fix diff adds a debug line appending '<script>alert(\"hello\")</script>' to sensor_descr (fix.diff:129); it renders escaped after the fix but must not be copied into the task's reference solution.",
  "eventlog.inc.php ($vars['device'], fix.diff:323-324), graphs.inc.php (graph_descr config, fix.diff:336-337) and custom map names (fix.diff:433-434) are request/config/user-entered data, not SNMP/syslog; bundled in the same commit.",
  "includes/html/pages/device/hrdevice.inc.php:12 builds SQL by string concatenation (separate weakness, not pursued)."
 ],
 "unverified": [
  "repo_mb not measured.",
  "Whether the attribute-decoding bypass of e() inside overlib JS strings (storage.inc.php:27, vrf.inc.php:126, hrdevice.inc.php:14) actually executes was reasoned from HTML parsing rules, not run.",
  "Other legacy tabs (entphysical, ports, overview generic sensors, graphs titles) were not exhaustively audited; more uncovered routes are likely.",
  "Latest release not provided; present_in_latest is unknown for all O8 routes.",
  "Sibling advisories (c_sibling_advisories=4) not read; recall_risk medium is an estimate.",
  "Whether the device slas list page is reachable for SLA rows with tag/owner (the list query selects owner?) was not traced."
 ]
}
  ```
- Published fix sites:   - includes/html/functions.inc.php:511 — entry point: alerts table ajax (includes/html/table/alerts.inc.php:131 -> alert_details -> format_alert_details), bill/port/isis/sensor/service/bgp/mempool/generic/app branches 511-630 [shared HTML helper rendering deserialized alert_log details]
  - includes/html/pages/device/health/mempool.inc.php:38 — entry point: device page, tab=health metric=mempool [legacy page template]
  - includes/html/pages/device/health/sensors.inc.php:22 — entry point: device page, tab=health metric=<sensor class> (included via includes/html/pages/device/health.inc.php:113) [legacy page template]
  - includes/html/pages/device/health/storage.inc.php:23 — entry point: device page, tab=health metric=storage (also JS overlib popup at :27) [legacy page template]
  - includes/html/pages/device/port/vlans.inc.php:14 — entry point: device port page, view=vlans [legacy page template]
  - includes/html/pages/device/processes.inc.php:84 — entry point: device page, tab=processes [legacy page template]
  - includes/html/pages/device/routing/bgp.inc.php:19 — entry point: device page, tab=routing proto=bgp [legacy page template]
  - includes/html/pages/device/showconfig.inc.php:274 — entry point: device page, tab=showconfig (Oxidized node info and version list) [legacy page template fed by external Oxidized API]
  - includes/html/pages/device/slas.inc.php:7 — entry point: device page, tab=slas id=<sla> (detail branch only) [legacy page template]
  - includes/html/pages/eventlog.inc.php:58 — entry point: eventlog page (reflected $vars['device'] in hidden input) [legacy page template, request parameter not SNMP data]
  - includes/html/pages/graphs.inc.php:194 — entry point: graphs page (graph_descr config value) [legacy page template, config value]
  - includes/html/pages/routing/bgp.inc.php:304 — entry point: global routing page, protocol=bgp [legacy page template (second copy of device bgp table)]
  - includes/html/pages/routing/vrf.inc.php:115 — entry point: global routing page, protocol=vrf [legacy page template]
  - includes/html/print-syslog.inc.php:9 — entry point: device overview syslog panel (includes/html/pages/device/overview/syslog.inc.php:15) [legacy include partial]
  - includes/html/print-vrf.inc.php:9 — entry point: device page, tab=routing proto=vrf (includes/html/pages/device/routing/vrf.inc.php:86) [legacy include partial]
  - resources/views/map/custom-list.blade.php:24 — entry point: custom maps list route (maps.custom.*) [modern Blade view, user-entered map name]
- Uncovered routes to confirm (pattern B):   - includes/html/pages/device/port/sensors.inc.php:13-23 — port-page sensor panel is a twin of the fixed health/sensors code (ipmi and plain branches) and prints sensor_descr raw (reason to dismiss: it is a port sub-view, not the health tab named by the fix; sensors 'belong' to health; still in latest: unknown)
  - includes/html/pages/device/wireless.inc.php:81-96 — wireless sensors page prints sensor_descr raw in the panel title (reason to dismiss: wireless sensors are a separate sensor family with their own table/tab; still in latest: unknown)
  - includes/html/pages/device/slas.inc.php:110-124 — SLA list branch of the same file leaves tag/owner raw when the name is wrapped in a link for jitter-type SLAs (htmlentities only in the else branch) (reason to dismiss: the fix escaped the identical lines at :7/:11 and the list branch already has htmlentities, so it looks handled; still in latest: unknown)
  - includes/html/functions.inc.php:641-645 — format_alert_details fallback branch dumps every *id/desc/msg/last* key/value raw (reason to dismiss: generic debug-style fallback for unknown rule types; fix added e() only to the named branches; still in latest: unknown)
  - includes/html/pages/routing/vrf.inc.php:126 — global VRF page inconsistency overlib popup prints vrf_name of both VRFs raw inside JS string (reason to dismiss: tooltip only shown on mismatch; fix escaped the visible cells 115-117 of the same loop; still in latest: unknown)
  - includes/html/pages/device/overview/storage.inc.php:77 — device overview storage panel passes storage_descr raw as overlibLink text (Url::overlibLink does not escape $text) (reason to dismiss: overview widget, not the health/storage page that was fixed; tooltip content is escaped by generate_overlib_content so it looks safe; still in latest: unknown)
  - includes/html/pages/routing/mpls.inc.php:141-143 — MPLS LSP/path/service tables print mplsLspName and vrf_name raw (global copy) (reason to dismiss: MPLS is a neighbouring routing feature not named in the advisory; still in latest: unknown)
  - includes/html/pages/device/routing/mpls.inc.php:139-141 — device MPLS page copy of the same raw mplsLspName/vrf_name cells (reason to dismiss: same as above; second copy; still in latest: unknown)
  - includes/html/pages/device/hrdevice.inc.php:14-17 — hrDevice inventory prints hrDeviceDescr raw in link text and overlib JS popup (reason to dismiss: inventory tab, not health/routing; nothing in the fix touches it; still in latest: unknown)
  - includes/html/pages/device/edit/wireless-sensors.inc.php:43 — wireless sensors edit page prints sensor_descr raw in cell and data- attribute (reason to dismiss: admin-only edit page; still in latest: unknown)
  - includes/html/pages/device/health/storage.inc.php:27 — storage popup: fixed code uses e() (HTML entity) inside a JS string within an HTML attribute; the attribute parser decodes &#039; back to a quote before overlib runs (reason to dismiss: site already 'fixed' by the published patch, so a solver copying the patch believes it is done; still in latest: unknown)
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

## Environment (`tasks/librenms-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/librenms-ds/instruction.md`)
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

## Tests (`tasks/librenms-ds/tests/`)
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
- **Wrong-fix patches** go in `build/librenms-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/librenms-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/librenms-ds/manifest.json`:**
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

**Also in `build/librenms-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py librenms-ds --only static
python3 -I builder/gate.py librenms-ds --only nop
python3 -I builder/gate.py librenms-ds --only oracle
python3 -I builder/gate.py librenms-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/librenms-ds/`;
  - edit only `tasks/librenms-ds/`, `build/librenms-ds/` and, for pattern B, the register;
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
