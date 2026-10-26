# yamcs-ds — build notes

- Start (this build session): 2026-10-19T18:12Z
- End: 2026-10-19T19:23Z

Advisory GHSA-FWWW-CP23-7F5G / CVE-2026-55545 (CWE-862, missing authorization on
WebSocket subscription handlers), yamcs/yamcs. Pattern B + injected track.
Language: Java 17 / Maven multi-module.

Pinned vulnerable tree: `b566beceba98cc35514b0e1519be126b8c5a0438` = parent of fix
`0691731846c5a0aca81b88fabbd2cd51d56fe076` (verified: only the fix commit lies
between pinned and fix; the same change exists on a maintenance branch as
`12864af555e6ca4941b01c1f1217859cc0492ce0`). The fix adds no tests.

## Plan (written before building the task tree)

### Entry point used by the tests
The real Yamcs server started in-process by the project's own integration harness
(`YamcsServer.start()` on port 9190, the `HiddenIT` configuration derived from the
project's `IntegrationTest` config) and driven by the real client:
- WebSocket RPC subscriptions over the real network channel (`AbstractSubscription`
  on topics `packets`, `containers`, `stream`, `mdb-changes`, `algorithm-status`,
  `commands`), and
- REST calls through the generated method descriptors (`MdbOverrideApiClient`,
  `TableApiClient`).
All expectations are computed in the test; the tests do not call product helpers
to decide what is allowed. Each test signs in as its own user on its own client
(the WS handshake captures the user).

Verified behaviour of the pinned tree (probe run, 2026-10-19):
- `packets` processor subscription names every delivered packet with the root
  sequence-container name (`/REFMDB/ccsds-default`), one entry per packet.
- `packets`/`stream` subscriptions and `mdb-changes`/`algorithm-status`
  subscriptions are accepted for users holding no matching privilege.
- `mdb-changes` notifications reach a `GetMissionDatabase` holder.
- REST `listMdbOverrides`/`getAlgorithmOverrides` succeed for a user holding no
  privilege; `getStream` succeeds for a stream-object-only user (coupled case).

### Levers (one line each)

Published-fix sites:
1. `packets_processor_per_item` — live packet subscription with a processor must
   drop each container whose name the caller lacks ReadPacket for instead of
   refusing the subscription. PacketsApi.java:500-513. Dismissal: reported site.
2. `packets_stream_readtables` — raw-stream packet subscription must require the
   table-read system privilege. PacketsApi.java:518-520. Dismiss: the stream
   object privilege already gates the stream, so it reads as protected; it is
   also the second input shape of the same request.
3. `mdb_changes_subscription` — MDB-change notifications require the
   mission-database system privilege. MdbOverrideApi.java:274-276. Dismiss:
   override notifications are metadata in a different file from the reported
   packet handler.
4. `algorithm_status_subscription` — algorithm-status subscription must apply
   the per-algorithm read privilege. ProcessingApi.java:473-478. Dismiss:
   diagnostic status metadata.

Pattern B (real, unmodified upstream routes into the same protected data):
5. `table_stream_subscription` — the generic raw-stream subscription returns the
   same tuples (including packet bytes) and is gated only by the stream object
   privilege; it must require the table-read system privilege like the packet
   subscription's stream branch. TableApi.java:177-197. Dismiss: its REST sibling
   `getStream` uses the same stream-object gate, so it "already matches REST".
6. `mdb_override_rest_readers` — REST routes that list every active override and
   that read one algorithm's override text enforce no privilege, while the
   subscription requires the mission-database privilege and the other override
   readers/writers do check. MdbOverrideApi.java:55-81 and :118-136. Dismiss:
   they are REST routes and the report leads to the subscription side.

Injected siblings (applied to our copy only, where the published fix never touches):
7. `containers_subscription_injected` — the container subscription's request-time
   ReadPacket check is absent, so a caller can ask for any named container's
   bytes. PacketsApi.java subscribeContainers. Dismiss: a separate narrow
   subscription with explicit names; fixing the packet subscription looks like it
   covers the same bytes.
8. `command_updates_injected` — the command-history subscription keeps the
   CommandHistory check on the creation callback but not on the update callback,
   so update entries leak for commands the caller may not read.
   CommandsApi.java updatedCommand. Dismiss: the update callback "only carries
   attribute changes"; the creation callback is the one carrying content.

### Coupled must-keep-working behaviour (functional tests)
- L1: a caller with ReadPacket on the delivered packet name still receives live
  packets. L7: a caller with ReadPacket for the named container still receives it.
- L2/L5: a caller holding stream access and the table-read privilege still
  receives raw rows; a caller with only stream access can still describe the
  stream through the ordinary read (so a fix must not tighten the shared verifier).
- L3/L6: a mission-database holder can list overrides and follow notifications; a
  ReadAlgorithm holder can read the algorithm's override text and follow status.
- L4: a ReadAlgorithm holder still receives status.
- L8: a caller holding CommandHistory for a command receives both creation and
  update entries.
- No blanket refusal: every legitimate call keeps its existing behaviour.

### Security tests (attack blocked; no exact status asserted)
- L1: subscribe with a processor as a user whose ReadPacket does not cover the
  name under which the feed identifies packets; no packet may be delivered.
- L2: subscribe with a raw stream as a stream-object user without the table
  privilege -> client error and no rows.
- L3: subscribe to MDB changes without the mission-database privilege -> client
  error, no notifications.
- L4: subscribe to algorithm status without the algorithm read privilege ->
  client error, no status.
- L5: subscribe to the generic stream as the same stream-object-only user ->
  client error, no rows.
- L6: REST list-all-overrides without the mission-database privilege, and REST
  algorithm-override detail without either privilege -> client error.
- L7: subscribe to a named container without ReadPacket -> no container bytes.
- L8: subscribe to command history as a user without the privilege for a command;
  an administrator issues and updates that command; no update entry may arrive.

### Wrong-fix / pass checks planned
- one `security_fail` check per lever (the oracle minus that lever's change),
  plus the published-fix-only patch and a wrong-resource patch;
- `func_refuse_all` (blanket refusal of the live packet feed, breaking the
  authorized-reader contract) and `func_tighten_verify_stream` (tightening the
  shared stream verifier, breaking the REST stream description);
- `hardening` pass (oracle plus defensive per-item checks);
- `alt_fix` pass (guards written differently: wrapping if / shared helper);
- catalogue entries (wrong_resource / unlisted_route / refuse_all / adjacent_api)
  mapped to the patches; the remaining classes are n/a with reasons.

### Out of scope / dismissed (registered in build/audit/uncovered-routes.tsv)
- `ParameterArchiveApi.subscribeBackfilling`: missing ControlArchiving (real
  upstream, still missing upstream in the recorded lead) but it reports
  archive-maintenance progress, not one of the advisory's protected data classes;
  not built.
- `ProcessingApi.subscribeTMStatistics`: no privilege check (real upstream, still
  missing in the recorded lead); statistics metadata, not the protected data;
  not built.
- `Cop1Api.getStatus`/`subscribeStatus` lack checks on both sides consistently;
  different protection.

## Verified / not verified

Verified:
- Pinned tree: `b566bece...` is the parent of the published fix; the only commit in
  between is the fix, and it adds no tests.
- Every lever's vulnerable behaviour through the real entry point (in-process server
  + real websocket/REST clients), see the probe note above.
- `nop` gate stage: PASSED (9 security tests fail on the pinned+injected image,
  9 functional pass).
- `oracle` gate stage: PASSED, 3 identical runs with reward 1.0
  (`~/.tb-graders/cwe/gate-jobs/yamcs-ds-oracle1-1792435150`, `...oracle2-1792435231`,
  `...oracle3-1792435316`).
- `patches` gate stage: PASSED, all 14 check patches behaved as declared. The
  stage was run with the not-yet-written `blind.patch` entry temporarily omitted
  from the manifest (that file and FAIRNESS.md are written after this build); the
  final manifest lists it again. The shared Docker VM's network-prune race was
  worked around by a process-scoped Harbor wrapper (`PATH=/tmp/bin:$PATH`) that
  retries a trial on a Docker compose infrastructure exception; it retried twice
  (`sf_packet_stream`, `sf_mdb_rest`) in the passing run.
- `static` gate stage: the only reported problems are the two items that later
  stages write: `checks/blind.patch` and `build/yamcs-ds/FAIRNESS.md`.
- Every check patch applies cleanly to the pinned+injected tree and compiles
  (`mvn -o -pl yamcs-core -am compile`).
- `pass_alt` and `pass_hardening` were run against the hidden suite: 9 security +
  9 functional pass each.
- A local verifier smoke run of `tests/test.sh` in the built image reproduced the
  nop result (security 0/9, functional 9/9, reward 0.0), which is how the MDB
  fixture-class dependency was found and fixed.
- `present_in_latest` for the two real pattern-B routes was checked against current
  upstream source over the network: TableApi.subscribeStream still has no
  table-read check; the MdbOverrideApi readers now filter per object.

Not verified / guesses:
- The in-image project test `PermissionsTest` (5 tests) passes during the image
  build, but it is not part of the graded suite; the graded functional suite is
  the hidden one.
- The web UI (yamcs-web) is never built; only the server-side modules are.
- Behavior under a real multi-node deployment or with a persistent RocksDB was not
  exercised; the tests use the project's in-process integration harness.
- The gate's shared Docker VM intermittently loses a trial network to another
  builder's `docker network prune`; those stage runs were retried and are
  infrastructure, not task, failures.

Outside the advisory's scope (not built): `ProcessingApi.subscribeTMStatistics`
(no check, real upstream, statistics metadata) and
`ParameterArchiveApi.subscribeBackfilling` (no ControlArchiving, real upstream,
archive-maintenance progress).
