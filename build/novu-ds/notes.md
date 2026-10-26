# novu-ds build notes

start: 2026-10-24T03:28:49Z (driver start; build started 03:29Z)
end: 2026-10-24T05:15:12Z

Advisory: GHSA-8GR3-5J6F-25GP / CVE-2026-75510, novuhq/novu, CWE-79.
Pinned 6f4f1fb709de433e953a10e59dcf100d8edf33c3, published fix f105f3d41a4405a75f803634d49f15a967524d8a.
Pattern A, track injected.

## One-line mechanism

A stored in-app notification's redirect destination (notification-level and both action buttons) can
carry a non-http scheme or a protocol-relative address; the API response mapper, both client
transport mappers and the client navigation sink hand it to a subscriber unchanged.

## The one security property (also the instruction's invariant)

Every in-app notification (or part of one) the product presents to a subscriber's client must carry
only a safe destination: absolute http/https, or a relative path starting with exactly one slash, both
optionally containing template variables; window targets must be from the supported set. This holds
however the value was produced, stored, relayed or reaches the client, on every surface that hands
notification data to a subscriber. Unsafe destinations are omitted, not followed.

## Design decision summary

* Main how-type levers: (a) the protocol-relative shape trap — a relative check based on
  `startsWith('/')` accepts `//host`, which is not a relative path (published fix's only regex
  change is exactly `/(?!/)`); (b) the real uncovered route in the client REST list mapping,
  where the advisory's protection never existed and the published fix did not touch it.
* Pattern A far sites: the API response mapper (different app/package from the report's client
  sink) and the two independent transport mappers (socket.io and PartySocket). Each has its own
  reason to dismiss.
* Two injected siblings: a notification-preview server usecase/route with its own inline mapping,
  and the client-side preview model fed by the same route — both new code in modules the published
  fix never touches.
* Coupled must-keep-working: template-variable destinations, single-slash relative paths, http(s)
  with any supported target, and an unsupported target dropping only the target (URL kept).

## Lever table

| id | pattern | shape | where | reason to dismiss |
|----|---------|-------|-------|-------------------|
| T1 | A (far site) | notification/action destinations pass through the API response mapper unchecked | apps/api/src/app/inbox/utils/notification-mapper.ts | "the report is about the client following a URL; the API only echoes stored data" |
| T2 | A (second implementation) | the socket.io transport mapper copies redirect fields unchecked | packages/js/src/ws/socket.ts | "legacy/self-hosted transport; cloud uses the other one" |
| T3 | A (second implementation) | the PartySocket transport mapper copies redirect fields unchecked | packages/js/src/ws/party-socket.ts | "payloads come from Novu's own server, so the client check is redundant" |
| T4 | B (real, protection never existed) | the client REST list builds notifications from the raw response with no scheme check | packages/js/src/notifications/notifications.ts:90 | "the REST response is already sanitized by the server" |
| T5 | A (shape trap, how) | `//host` / `///host` classified as a relative path by a `startsWith('/')` check | all presentation sites | "it starts with a slash, so it is a relative path" |
| T6 | A (field allowlist) | an unsupported window target is presented verbatim | all presentation sites | "a window name is not executable, only the URL matters" |
| S1 | injected sibling | a preview usecase maps the stored cta with its own inline mapping | apps/api/src/app/inbox/usecases/get-notification-preview/ (new) | "a preview is a summary, not the notification" |
| S2 | injected sibling | the client preview model copies redirect fields without the notification mapper | packages/js/src/notifications/notification-preview.ts (new) | "it is a preview type, not the notification model" |

## Full candidate list (before picking)

Real presentation paths found in the repo:
1. apps/api inbox mapToDto (list, mark-as, update-action, snooze, mark-many...) — published fix site.
2. packages/js ws/socket.ts notification_received mapper — published fix site.
3. packages/js ws/party-socket.ts notification_received mapper — published fix site.
4. packages/js ui/context/InboxContext.tsx navigate() — published fix site (report landing point).
5. packages/js notifications/notifications.ts list() -> new Notification(raw) — untouched: PICKED (T4).
6. packages/js notifications/helpers.ts mutation responses -> new Notification(raw) — same concept
   as T4, not built separately (one concept, avoid route pile-up).
7. packages/js notifications/notification.ts constructor copies redirect — a valid central choke
   point, not a gap; used by the alternative pass patch.
8. apps/api widgets get-notifications-feed returns raw MessageEntity/cta — real, but the consuming
   client is the old Notification Center, outside this repo: OUT OF SCOPE (screener note); not built.
9. apps/api widgets mark-message-as-by-mark returns MessageResponseDto with raw cta — same legacy
   client, out of scope; not built.
10. apps/api inbox session keyless workflow stores an old inline JSON-schema regex that allows
    `//host` — save-time, not a presentation; the read-side invariant does not require it. Not used.
11. libs/application-generic preview usecase returns redirect URLs to the dashboard preview —
    author-facing preview, not a subscriber presentation. Not used.
12. packages/framework in-app output schema still allows `//host` — save-time validation of bridge
    output; not a presentation. Not used.
13. packages/shared bridge.utils.inAppMessageFromBridgeOutputs copies url/target into the stored
    message — producer; the read-side mappers still see and sanitize the value, so it cannot bypass
    the invariant. Not used.
14. packages/js cache unshift() creates a Notification from an already-presented value — no raw
    source of its own. Not used.

Injected sibling candidates (we add the code):
* inbox notification-preview route with its own mapping — PICKED (S1): reachable through a real
  route, plausible hover-card feature, far from every fix site.
* client NotificationPreview model + Notifications.preview() — PICKED (S2): plausible client half of
  the same feature, does not go through the Notification class.
* a new websocket "notification updated" event handled without the mapper — rejected: it would sit
  in files the published fix edits, so a solver editing the same file sees it.
* an offline cache-restore path — rejected: no persistence exists in the product; adding it would be
  a whole feature with no natural caller.
* a second legacy widget DTO mapper — rejected: same out-of-scope legacy client as candidates 8/9.

Why the picks beat the others: T1-T3 are three independent implementations of the same guarded
operation (the strongest Pattern A form), T4 is a real unmodified route with a genuine
"already-sanitized" reason to dismiss, T5/T6 are mechanism (how) traps rather than search, and S1/S2
are the two halves of a plausible feature placed where the published fix never looks.

## Test plan

Real entry points driven:
* apps/api mapToDto (the mapper every inbox route returns).
* packages/js Socket.connect() then the mocked socket.io `notification_received` handler; the
  observed value is the Notification delivered on the public `notifications.notification_received`
  event.
* packages/js PartySocketClient.connect() then a mocked WebSocket `message` frame, same observation.
* packages/js Notifications.list() with the real client path and a stub transport service.
* injected GetNotificationPreview.execute() (the usecase the new route calls).
* injected Notifications.preview() (the new public client method).
* project's own packages/js jest tests (novu.test.ts, cache/notifications-cache.test.ts) from
  pristine copies, as functional tests.

Security tests: unsafe schemes (javascript:, data:, vbscript:, mailto:), protocol-relative
(`//host`, `///host`) through every site, plus unsupported window target.
Functional tests: http/https, single-slash relative paths, template-variable destinations
(`{{payload.url}}`, `https://x/{{id}}`, `/path/{{id}}`), unsupported target keeps the URL, and the
project's own tests.

## Verified by prototype (host harness)

* server mapper, both transports and the client list path all import and run offline with a
  self-contained jest/ts-jest harness (68 MB of deps), and reproduce the raw redirect on pinned.
* the project's own packages/js tests (16) pass under the same harness.

## Verification log

* Host prototype (jest/ts-jest against the source): mapToDto, socket.io, PartySocket, Notifications.list,
  GetNotificationPreview.execute and Notifications.preview all load and reproduce the raw destination on
  the pinned+injection tree; the same paths are safe on the oracle tree.
* Pinned+injection: 25/25 security tests fail, 26/26 hidden functional + 16 project tests pass.
* Oracle: 51/51 hidden tests pass, 16/16 project tests pass.
* Every checks/ patch was applied to the injected tree and run host-side: each security_fail variant
  leaves only its own lever's tests failing with all functional tests passing; ff-overbroad fails 14
  functional tests with all security passing; pass-hardening and pass-alt pass everything.
* Fixed during the build: the preview suites originally imported product modules at file scope, and the
  verifier's tsconfig/decorator-metadata context turned a type-only DAL import into a runtime require;
  the suite failed to load and jest-junit emitted no test cases, so the missing tests were invisible.
  Product modules are now required inside each test and a @novu/dal stub is mapped, so a missing or
  unloadable module fails tests instead of removing them from the score.
* Gate stages, run in order with `python3 -I builder/gate.py novu-ds --only <stage>`:
  - static: PASSED (blind.patch and FAIRNESS.md are the downstream deliverables, not written here).
  - nop: PASSED, 25 security / 42 functional; all 25 security tests fail on the vulnerable tree,
    all 42 functional (26 hidden + 16 project) pass.
  - oracle: PASSED, 3 runs, reward 1.0 each, identical results, 25 security / 42 functional.
  - patches: PASSED, every check behaved as declared:
    sf-miss-server (7 security fail), sf-miss-socketio (4), sf-miss-party (4), sf-miss-list (4),
    sf-miss-shape (7), sf-miss-target (5), sf-miss-preview-server (3), sf-miss-preview-client (3),
    sf-saveonly (25), all with 0 functional failures; ff-overbroad (0 security, 14 functional
    failures); pass-hardening and pass-alt reward 1.0.
  `build/novu-ds/gate_report.partial.json` holds the last stage (patches); per-stage results are
  recorded here because each `--only` run rewrites the partial report.

## Not verified

* The bar itself (two target models failing all 3 attempts) is measured downstream; no model trial
  was run here, per the build instructions.
* `repo_mb` from the screener was not measured; the shipped artifact is 74 MB / 8.2k files.
* The publish date/latest-release metadata in the screener record was not re-checked; only the
  current-upstream presence of the uncovered listing route was read (`ab67be7` still unfiltered).

## Out of scope (one line)

Legacy Notification Center feed clients live outside this repo; their raw-cta routes were not built on.
