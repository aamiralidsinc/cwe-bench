# librenms-ds — build notes (build-v1)

- Start (UTC): 2026-10-24T02:42:29Z
- End (UTC): TBD
- Repo: librenms/librenms, pinned 44bb4ecc0eb9e66b39abce2b77710ebc18fd57e8,
  published fix 6782af940c3c495755923b520a302f3a1cb1ce6b (16 files, `e()` at each echo).
- CWE-79 stored XSS in server-rendered legacy templates. Pattern A+B, injected track.

## Security property (stated once, general)

No value that a monitored device supplies, or that the monitoring system records from it, may
become markup or code in any page. Wherever such a value is shown — in element content, in an
attribute value, or inside an event-handler script — it must stay inert text: it must not create
an element, execute script, or break out of the surrounding code. This holds on every page that
shows device data, including values recorded earlier and re-displayed later.

## Levers (one line each)

1. **L1 main, how-type — entity decoding in a JS string inside an HTML attribute.**
   The same value is escaped for HTML but interpolated into an inline `overlib('…')` handler; the
   HTML parser decodes `&lt;`/`&#039;` back before JS parses the string, so `e()` leaves it
   executable. Sites actually reachable at the pinned commit: device overview storage / mempools /
   processor / generic-sensor panels, health/processor popup, inventory hrdevice popup, and the
   injected process-command tooltip. (The published fix also edits the health/storage `$fs_popup`
   string, but that variable is built and never printed at this commit — dead code, so it is not a
   lever; recorded here.) Reason to dismiss: it already uses the project's escaping idiom; the
   output *looks* encoded in `view-source`.
2. **L2 how-type — coupled must-keep-working: the alert-details renderer assembles HTML.**
   Links, `<br>`, `&nbsp;` and `Url::portLink`/`sensorLink` output are intentional HTML, and
   `cleanPort()` already `htmlentities()`s ifAlias/ifName/ifDescr, so escaping the assembled
   string (or re-escaping cleaned fields) breaks links or double-encodes labels. Reason to
   dismiss: "escape the output" is the obvious move.
3. **L3 route where protection never existed (Pattern B).** Device-data sinks the published fix
   never touched: port-page sensor panel, health/processor, health/diskio, wireless sensors,
   MPLS LSP/VRF tables (device + global), ISIS adjacency table, SLA list jitter branch,
   alert-details fallback branch, overview storage/mempool/sensor panels. Reason to dismiss:
   different tab/feature from the one the advisory names.
4. **L4 shape trap — branch-conditional cleaning in the alert-details renderer.**
   Upstream moved `cleanPort()` above the ISIS branch because the branch previously skipped it
   and left `ifAlias` raw; the fallback branch dumps every `*id/*desc/*msg/*last` key raw. Reason
   to dismiss: each branch reads as already handled by its neighbours.
5. **INJ-1 injected sibling — processor branch in the alert-details renderer.** A maintainer
   copied the mempool branch; `processor_descr` and the linked label are raw. Reason to dismiss:
   looks exactly like the other branches, and it is not in the report's list.
6. **INJ-2 injected sibling — process command tooltip.** The processes page (device-sourced
   `command`) gets a new "info" anchor whose `onmouseover` interpolates the full command raw,
   while the table cell itself is escaped. Same value, two sinks, only one obvious. Reason to
   dismiss: the column next to it is the one you would fix.

## Sites / routes / shapes the security tests cover

Real HTTP entry points (Laravel test client dispatches the real routes; legacy controllers and
`includes/html/pages/**` execute as in a request) plus the real `html/ajax_table.php` endpoint
for the alerts table (the script the bootgrid calls).

- Alert details (alerts table endpoint): mempool, service, BGP, port (incl. ISIS branch),
  app, generic `type/label/error`, fallback `k => 'v'`, injected processor branch. Each alert
  test runs in its own process because the demo endpoint uses `include_once`.
- Device pages: health storage (element text only; its popup string is dead code at this commit),
  health sensors (plain + ipmi), health mempool, health processor (title + popup), health diskio,
  processes (cell + injected tooltip), port VLAN view, port sensor view, routing BGP,
  routing VRF, routing ISIS, routing MPLS, SLA detail, SLA list jitter row, inventory (hrdevice
  text + popup), wireless.
- Global routing: BGP, VRF.
- Device overview: storage panel (element text + JS tooltip tag and quote payloads), mempool panel,
  generic sensor panel (JS-string contexts).

Out of scope, recorded and not built on: eventlog hidden input (`$vars['device']`, request data),
graphs `graph_descr` (configuration), custom-map name (user-entered data), showconfig Oxidized
node data (external service needs run-time network), admin-only wireless edit page.

## Coupled must-keep-working values (functional)

- Alert-details port row keeps its anchor and shows a cleaned label exactly once (no double
  encoding); sensor row keeps `<br>`/limits structure and links; mempool/BGP/service rows keep
  their anchors and separators.
- Health storage page keeps its heading; the overview storage panel keeps its overlib tooltip
  (description text and graph image still present) for a legitimate description containing `&`
  and `'`.
- BGP/VRF/MPLS/SLA pages keep rendering legitimate values that contain `&`, `'`, `(`.
- Project tests: the project has no tests for the affected legacy templates (upstream tests/ never
  references them), so none are run; the coupled behaviour is covered by our functional suite.

## Candidate list (every sibling site/route found) and picks

Real, unmodified upstream (Pattern B candidates):
1. `includes/html/pages/device/port/sensors.inc.php:14-17` — sensor_descr raw (twin of health/sensors).
2. `includes/html/pages/device/wireless.inc.php:81-97` — sensor_descr raw in panel title.
3. `includes/html/pages/device/health/processor.inc.php:16,26` — processor_descr raw in title + JS popup.
4. `includes/html/pages/device/health/diskio.inc.php:21` — diskio_descr raw in overlibLink text.
5. `includes/html/pages/device/overview/storage.inc.php:77` — storage_descr raw in overlibLink text; tooltip text only HTML-escaped.
6. `includes/html/pages/device/overview/mempools.inc.php:69,84` — mempool_descr raw in tooltip JS + link text.
7. `includes/html/pages/device/overview/processors.inc.php:41,50` — processor_descr raw (cpu_details mode).
8. `includes/html/pages/device/overview/generic/sensor.inc.php:25,52,66-68` — group + sensor_descr raw into overlibLink/tooltip.
9. `includes/html/pages/device/routing/mpls.inc.php:139-141` — mplsLspName, vrf_name raw.
10. `includes/html/pages/routing/mpls.inc.php:141-143` — same, global copy (not rendered in the harness; global page protocol parse did not select it, see below).
11. `includes/html/pages/device/routing/isis.inc.php:31-40` — adjacency address/system-id/area/type/admin state raw.
12. `includes/html/pages/device/slas.inc.php:110-124` — jitter-row tag/owner raw (else branch escapes).
13. `includes/html/functions.inc.php:641-645` — alert-details fallback `k => 'v'` raw.
14. `includes/html/pages/routing/vrf.inc.php:126` — VRF mismatch popup raw (needs two devices; not tested).
15. `includes/html/pages/device/hrdevice.inc.php:14-17` — hrDeviceDescr raw in link text + JS popup.
16. `includes/html/pages/device/edit/wireless-sensors.inc.php:43` — admin-only edit page (not tested).
17. `includes/html/pages/device/overview/transceivers.inc.php` — Blade view, correctly escaped.
18. `includes/html/pages/device/overview/services.inc.php` — correctly escaped.

Picks: 1,2,3,4,5,6,8,9,11,12,13,15 are used in tests (they are the most complex/far ones and
have distinct dismissal reasons); 10,14,16 recorded but not built (unreachable/hard to drive
deterministically); 17/18 are correctly escaped, no gap.

Injected (placed where the published fix never touches):
- INJ-1: new `processor` branch in `format_alert_details` (shared renderer, raw descr in an anchor).
- INJ-2: new command tooltip in `includes/html/pages/device/processes.inc.php` (raw command in a JS
  attribute while the cell is escaped).

## Verification notes

- Flaw reproduces at the pinned commit through real entry points: confirmed by rendering every
  route on SQLite in-memory inside the project's own Laravel test harness (see `build/` scratch).
- The project's DB layer works on SQLite in-memory (`testing_memory`), migrations in ~3 s.
- Legacy page controllers emit `ob_end_clean()` warnings when a page raises; hidden bootstrap
  reduces error_reporting for warnings/notices only (PHPUnit still sees exceptions).
- Global MPLS page (`/routing/protocol=mpls`) did not render table rows in the harness (route
  parameter not selected); device MPLS page does, so only the device copy is tested.
- Cannot verify in a browser; the JS-context oracle parses the returned HTML with DOMDocument and
  inspects decoded attribute values / created elements, which is the browser's view of the
  attribute. Stated as a guess: no real browser is used.

## Check-patch validation (sandbox, before the gate)

Full suites run against each candidate patch on the injected pinned tree:

| patch | security (total/failing) | functional (total/failing) | expected |
|---|---|---|---|
| functional-fail-overescape | 35/0 | 11/2 | functional_fail |
| inj1-miss-processor-branch | 35/1 | 11/0 | security_fail |
| inj2-miss-process-tooltip | 35/2 | 11/0 | security_fail |
| l1-html-escape-only | 35/8 | 11/0 | security_fail |
| l2-miss-alert-branches | 35/6 | 11/0 | security_fail |
| l3-uncovered-routes | 35/13 | 11/0 | security_fail |
| l4-branch-blind | 35/1 | 11/0 | security_fail |
| pass-hardening | 35/0 | 11/0 | pass (reward 1.0) |
| pass-alternative | 35/0 | 11/0 | pass (reward 1.0) |

Nop (pinned+injected, no fix): gate PASSED — 35/35 security tests fail, 11/11 functional tests
pass (sandbox and the real separate verifier after the `html/build` artifact fix).
Oracle in the built environment image, run as uid 1000 exactly as test.sh does: 35/35 security,
11/11 functional, score.py reward 1.0 (46/46).

## Verifier-environment gotcha (root cause: artifact exclude)

The first nop gate runs failed all device-page functional tests with HTTP 500. The application log
in the replicated verifier showed `Vite manifest not found at: /workspace/html/build/manifest.json`.
LibreNMS ships its compiled frontend under the tracked directory `html/build/` (1.2 MB) and the page
layout requires `manifest.json`; the template's artifact exclude list contained `"build"`, so
Harbor dropped `/workspace/html/build` from the artifact and the verifier workspace could not render
any Blade page (the alert-table endpoint, which renders no Blade view, still worked). Removing
`"build"` from `task.toml` `artifacts.exclude` fixes it; verified in a container holding the exact
failed artifact with `html/build` restored.

The harness also boots each test application with `useBootstrapPath()`/`useStoragePath()` under a
private `/tmp` tree and logs to `APP_LOG` under `/tmp`, so a restored workspace whose ownership
does not match the uid-1000 test user cannot cause the same class of failure.
