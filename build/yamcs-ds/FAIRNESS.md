# FAIRNESS — yamcs-ds

Reviewed: 10 security + 9 functional hidden tests, `solution/fix.patch`, `manifest.json` (patch_checks, traps, wrong_fix_catalogue), `notes.md`, `checks/*.patch`. No gates run.

Table note: a guard raised in the handler or an equivalent request-time layer is valid; per-object routes accept per-item filtering; both MDB REST tests accept an error or empty data.

## 1. Test-by-test fairness

| Test (file::name) | Asserts | Covering instruction sentence | Correct fix could fail? | Risk |
|---|---|---|---|---|
| `security/SecuritySubscriptionsTest.java::packetFeedDropsPacketsTheCallerMayNotRead` | A role with ReadPacket only on `PKT1_1` receives no `PKT1_3`-sized packet | "received every packet … including packets its role excludes"; "must deliver only the objects the caller may read. It must keep delivering the authorized objects" | no — per-item filter on the archive-partition name the ordinary packet read checks | low |
| `security/…::packetFeedDeliversNoPacketOutsideTheCallersPacketNames` | A role with ReadPacket on the root container name only receives no `PKT1_1` | "No live subscription may deliver an item that the same caller would be refused when requesting it through the corresponding ordinary read" (that read keys on the archive partition); "A caller authorized for a subset of packets still receives those packets" | no — filtering on the ordinary read's name passes; filtering on the delivered root-container id delivers `PKT1_1`, contradicting the quoted sentence | medium |
| `security/…::rawPacketStreamRefusedWithoutTablePrivilege` | stream-object-only caller gets a client error and no rows on `packets?stream` | "Raw stream or table data that can carry telemetry packet bytes must not be delivered to a caller that lacks the table-reading system privilege"; "a caller lacking the privilege required by the equivalent ordinary read must be refused" | no — subscription-time ReadTables check (before or after `verifyStream`); a silent per-row filter is not the stated whole-subscription mechanism | medium |
| `security/…::overrideNotificationsRefusedWithoutMissionDatabasePrivilege` | nopriv caller gets an error and no notifications | "Override notifications require the mission-database system privilege"; "A refusal is made at subscription time" | no — a per-object filter emits nothing but no error; the bullet requires the system privilege as a whole | low |
| `security/…::algorithmStatusRefusedWithoutAlgorithmPrivilege` | nopriv caller gets an error and no status | "Live algorithm status must not be delivered to a caller lacking read privilege on that algorithm"; "When a live subscription can only be authorized as a whole … must be refused" | no — one named algorithm; request-time ReadAlgorithm check (before or after `verifyAlgorithm`) | medium |
| `security/…::genericStreamRefusedWithoutTablePrivilege` | stream-object-only caller gets an error and no "stream" rows | same raw-stream/table bullet (stream rows carry packet bytes) | no — subscription-time ReadTables check; not a shared-verifier tightening | medium |
| `security/…::overrideListDoesNotExposeOverridesToUnauthorizedCaller` | nopriv list returns an error or zero overrides | "The collection of active mission-database overrides may only be read by a caller holding the mission-database system privilege" | no — refusal and per-object filtering both accepted | low |
| `security/…::algorithmOverrideTextNotExposedToUnauthorizedCaller` | nopriv read returns an error or no text override | "Reading one algorithm's override text is permitted with that system privilege or with read privilege on that algorithm" | no — both forms accepted | low |
| `security/…::containerSubscriptionDeliversNoContainerTheCallerMayNotRead` | nopriv receives no container bytes | "No live subscription may deliver an item that the same caller would be refused when requesting it through the corresponding ordinary read" | no — request-time ReadPacket check or per-item drop both pass | medium |
| `security/…::commandUpdatesAreFilteredPerCommand` | No entry for the forbidden command after an admin issue+update | "Live command-history entries must be filtered per command by the same command-history object privilege that the stored history is filtered by, for every entry the feed emits" | no | low |
| `functional/…::authorizedPacketFeedStillDelivers` | `PKT1_1` delivered, id = root container, size = `PKT1_1` | "A caller authorized for a subset of packets still receives those packets"; "Legitimate use must keep working exactly as it does today" | no — relabelling the id would change today's behaviour, which the instruction forbids | low |
| `functional/…::authorizedRawPacketStreamStillDelivers` | stream+ReadTables caller gets rows | "A caller holding both stream access and the table-reading privilege still receives raw stream rows" | no | low |
| `functional/…::streamDescriptionStillAvailableToStreamReader` | stream-only caller can `getStream` | "a caller holding stream access can still describe that stream through the ordinary read"; legitimate-use clause | no — only the `adjacent_api` wrong fix tightens the shared verifier | low |
| `functional/…::authorizedGenericStreamStillDelivers` | stream+ReadTables caller gets "stream" rows | same contract clause; legitimate-use clause | no | low |
| `functional/…::authorizedOverrideNotificationsStillDeliver` | mission-database caller receives a notification | "Override notifications require the mission-database system privilege"; legitimate-use clause | no | low |
| `functional/…::authorizedAlgorithmStatusStillDelivers` | algorithm-reader receives status within 8 s | "a caller holding read privilege on an algorithm can follow its live status" | no | low |
| `functional/…::authorizedOverrideReadersStillWork` | mission-database caller lists ≥1; algorithm reader gets text | contract clause for both readers | no | low |
| `functional/…::authorizedContainerSubscriptionStillDelivers` | root-container reader receives the container | "A caller authorized for a subset of packets still receives those packets"; legitimate-use clause | no | low |
| `functional/…::authorizedCommandFeedStillDeliversUpdates` | `.*` reader gets creation and update entry | "A caller holding command-history privilege for a command receives both its creation entry and its later update entries" | no | low |

## 2. Leniency (quality, non-blocking)

| Trap / property | Most plausible wrong fix | Caught? |
|---|---|---|
| `packets_processor_per_item` | filter on the delivered container id (`checks/sf_container_name_feed.patch`) | yes — `packetFeedDeliversNoPacketOutsideTheCallersPacketNames`; also breaks `authorizedPacketFeedStillDelivers` |
| `packets_processor_per_item` | refuse the whole processor feed unless all packets are readable (`checks/func_refuse_all.patch`) | yes — `authorizedPacketFeedStillDelivers` |
| `packets_stream_readtables` | check the `Stream` object privilege | yes — `rawPacketStreamRefusedWithoutTablePrivilege` (no error) |
| `packets_stream_readtables` | tighten shared `TableApi.verifyStream` (`checks/func_tighten_verify_stream.patch`) | yes — `streamDescriptionStillAvailableToStreamReader` |
| `mdb_changes_subscription` | per-algorithm filtering instead of the system privilege | yes — test requires an error (`awaitRefusal`) |
| `algorithm_status_subscription` | system-privilege check, or per-item filtering with no error | yes — `awaitRefusal` |
| `table_stream_subscription` | check the `Stream` object privilege (`checks/wrong_resource.patch`) | yes — `genericStreamRefusedWithoutTablePrivilege` |
| `mdb_override_rest_readers` | check one reader only (`checks/sf_mdb_rest.patch`) | yes — `overrideList…` / `algorithmOverrideText…` |
| `mdb_override_rest_readers` | over-restrict `getAlgorithmOverrides` to the system privilege | yes — `authorizedOverrideReadersStillWork` |
| `containers_subscription_injected` | no check (`checks/sf_containers.patch`), or require ReadTables | yes — security test / `authorizedContainerSubscriptionStillDelivers` |
| `command_updates_injected` | keep the creation check only (`checks/sf_cmd_update.patch`); drop all updates | yes — security test / `authorizedCommandFeedStillDeliversUpdates` |

Wrong fixes no test catches:
- Accepting `ControlArchiving` in lieu of `ReadTables` (`checks/blind.patch` passes): no `ControlArchiving`-only user exists.
- Command feed: refusing the whole subscription for a caller without `CommandHistory` on every command; `cmdpartial` sees an empty feed (test passes) and `cmdfull` holds `.*`.
- Container subscription: checking only the requested/root name instead of each name in `Names`; every container test uses `/REFMDB/ccsds-default`.
- Command update filter keyed on a wrong attribute (e.g. origin).
- `manifest.json` labels `sf_container_name_feed.patch` `functional_fail`, although it also fails `packetFeedDeliversNoPacketOutsideTheCallersPacketNames`; recheck that post-build entry.

## 3. Hints (quality, non-blocking)

- "Other live feeds behave the same way." → delete.
- "opened the processor's live packet feed with the standard client subscription call" → "opened a live subscription".
- "When the ordinary read authorizes each requested object separately…" → "apply the equivalent ordinary read to each item".
- "the same command-history object privilege that the stored history is filtered by, for every entry the feed emits" → "the caller's command-history privilege for the command it concerns".

## 3a. Required: generalize

- "or every object of a processor" → "or all objects".
- "including a caller that may access the stream as an object" → delete.
- The MDB bullet ("The collection … may only be read … Reading one algorithm's override text … Override notifications require …") → "Mission-database override data may only reach a caller holding the mission-database system privilege, except that read privilege on an algorithm permits reading that algorithm's override text."
- "A caller holding both stream access and the table-reading privilege … describe that stream through the ordinary read." → delete; "Legitimate use must keep working exactly as it does today." covers it.
- "A caller holding the mission-database privilege can list overrides; … follow its live status." → delete; legitimate-use sentence covers it.
- "both its creation entry and its later update entries" → "all of its entries".
- "A caller authorized for a subset of packets still receives those packets." → "A caller authorized for only some items keeps receiving those items."

## 4. Realism (quality, non-blocking)

Published-fix sites and the two pattern-B routes are real; the two injected siblings are plausible maintainer omissions on real websocket topics. No flags.

## Verdict

**READY (gate a).** The natural correct fix — request-time checks on whole-subscription routes and per-item filtering keyed to the name the ordinary packet read authorizes — passes all 19 tests. Failing alternatives (silent per-row filtering; root-container-id filtering) contradict the stated mechanism, so they are leniency, not unfairness. No instruction/test contradiction.

**Quality to tighten:** add a `ControlArchiving`-only user, a partial-command functional user and a second named container; recheck `sf_container_name_feed`'s label; apply the rewordings above.

**Human review:** Confirm (a) the packet-feed filter may fairly key on the archive-partition name rather than the delivered root-container id, and (b) "must not be delivered" plus the whole-subscription clause fairly requires a subscription-time error rather than silent filtering on stream and algorithm-status feeds.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
