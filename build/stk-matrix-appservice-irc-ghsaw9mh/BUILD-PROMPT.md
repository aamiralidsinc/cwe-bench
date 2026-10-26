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

Project root: `/home/mara/cwe-bench`. Task: `stk-matrix-appservice-irc-ghsaw9mh`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-wm4w-7h2q-3pf7; GHSA-w9mh-5x8j-9754
- Pinned (vulnerable) commit: fb339d0c06e17a198931509331bc5aafc39286c0. Published fix: 4af7d3009f10, 1835e047f269.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-w9mh-5x8j-9754",
 "pattern": "H3a",
 "repo": "matrix-org/matrix-appservice-irc",
 "pinned_commit": "fb339d0c06e17a198931509331bc5aafc39286c0",
 "protections": [
  "When the bridge resolves a Matrix event referenced from message content (reply source, edit original), it must return only content the referring user may read in that room, using the referring user's own authority instead of the appservice bot's read access (MatrixHandler.ts:1067, 1288).",
  "A Matrix message is relayed to IRC only when the homeserver-asserted sender is actually authorised in that room, not merely when the sender is not a virtual IRC user (MatrixHandler.ts:884-891, 924, 985-997).",
  "Admin-room commands are executed only for the user who owns that admin room (or a configured bridge admin), not for any sender whose event names the admin room (MatrixHandler.ts:927-941, 258-290; AdminRoomHandler.ts:206-211, 831-844).",
  "Truncation and preview length arithmetic stays safe for homeserver-controlled values, so a long media URI cannot produce a negative length or throw (MatrixHandler.ts:1141, 1152-1156; TrimString.ts:23-29).",
  "Cached message bodies used as reply/edit sources honour redactions and later removal (MatrixHandler.ts:1091-1099, 1383-1396; IrcBridge.ts:1169-1229).",
  "The message-age/replay filter cannot be bypassed by a homeserver omitting or forging origin_server_ts (IrcBridge.ts:1169-1179).",
  "Event content is type-validated (body must be a string) before it is used (MatrixAction.ts:189, 196; MatrixHandler.ts:875, 879)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M2",
   "origin": "advisory_route",
   "locations": [
    "src/bridge/MatrixHandler.ts:1284",
    "src/bridge/MatrixHandler.ts:1288",
    "src/bridge/MatrixHandler.ts:1291",
    "src/bridge/MatrixHandler.ts:1303",
    "src/bridge/MatrixHandler.ts:1323"
   ],
   "reason_to_dismiss": "getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/bridge/MatrixHandler.ts:1284",
    "src/bridge/MatrixHandler.ts:1288",
    "src/bridge/MatrixHandler.ts:1292",
    "src/bridge/MatrixHandler.ts:1303",
    "src/bridge/MatrixHandler.ts:1323"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "src/bridge/MatrixHandler.ts:1052",
    "src/bridge/MatrixHandler.ts:1060",
    "src/bridge/MatrixHandler.ts:1067",
    "src/bridge/MatrixHandler.ts:1070",
    "src/bridge/MatrixHandler.ts:1078"
   ],
   "reason_to_dismiss": "An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/bridge/MatrixHandler.ts:1052",
    "src/bridge/MatrixHandler.ts:1055",
    "src/bridge/MatrixHandler.ts:1060",
    "src/bridge/MatrixHandler.ts:1065",
    "src/bridge/MatrixHandler.ts:1067",
    "src/bridge/MatrixHandler.ts:1078"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/MatrixHandler.ts:884",
    "src/bridge/MatrixHandler.ts:924",
    "src/bridge/MatrixHandler.ts:985",
    "src/bridge/MatrixHandler.ts:995"
   ],
   "reason_to_dismiss": "The appservice protocol has the homeserver authenticate senders, so event.sender is treated as authoritative; the only sender check the bridge needs is the virtual-user claim check added for user spoofing.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/bridge/MatrixHandler.ts:884",
    "src/bridge/MatrixHandler.ts:924",
    "src/bridge/MatrixHandler.ts:985",
    "src/bridge/MatrixHandler.ts:987",
    "src/bridge/MatrixHandler.ts:995"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/MatrixHandler.ts:927",
    "src/bridge/MatrixHandler.ts:265",
    "src/bridge/MatrixHandler.ts:274",
    "src/bridge/MatrixHandler.ts:388",
    "src/bridge/AdminRoomHandler.ts:206",
    "src/bridge/AdminRoomHandler.ts:831"
   ],
   "reason_to_dismiss": "Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/bridge/MatrixHandler.ts:927",
    "src/bridge/MatrixHandler.ts:934",
    "src/bridge/MatrixHandler.ts:265",
    "src/bridge/MatrixHandler.ts:274",
    "src/bridge/MatrixHandler.ts:388",
    "src/bridge/AdminRoomHandler.ts:206",
    "src/bridge/AdminRoomHandler.ts:831",
    "src/datastore/postgres/PgDataStore.ts:485"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/MatrixHandler.ts:1141",
    "src/bridge/MatrixHandler.ts:1152",
    "src/bridge/MatrixHandler.ts:1155",
    "src/util/TrimString.ts:23"
   ],
   "reason_to_dismiss": "Media identifiers are normally short 24-character values generated by the homeserver, so the max-line budget minus the explanation URL and channel name is assumed to stay positive.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/bridge/MatrixHandler.ts:1129",
    "src/bridge/MatrixHandler.ts:1141",
    "src/bridge/MatrixHandler.ts:1152",
    "src/bridge/MatrixHandler.ts:1155",
    "src/util/TrimString.ts:23",
    "src/util/TrimString.ts:24"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/MatrixHandler.ts:1091",
    "src/bridge/MatrixHandler.ts:1284",
    "src/bridge/MatrixHandler.ts:1383",
    "src/bridge/IrcBridge.ts:1169"
   ],
   "reason_to_dismiss": "A cached body only exists for messages the bridge already relayed, so a later reply to a redacted message reveals nothing that the same IRC channel did not already see.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/bridge/MatrixHandler.ts:1091",
    "src/bridge/MatrixHandler.ts:1383",
    "src/bridge/MatrixHandler.ts:1387",
    "src/bridge/MatrixHandler.ts:1393",
    "src/bridge/IrcBridge.ts:1169",
    "src/bridge/IrcBridge.ts:1227"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M10",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/IrcBridge.ts:1170",
    "src/bridge/IrcBridge.ts:1172"
   ],
   "reason_to_dismiss": "origin_server_ts is the only timestamp available and the homeserver is its authority; the sample config already documents that clocks differ between homeservers.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "src/bridge/IrcBridge.ts:1170",
    "src/bridge/IrcBridge.ts:1172",
    "src/bridge/IrcBridge.ts:1173",
    "config.sample.yaml:20"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "src/bridge/MatrixHandler.ts:875",
    "src/bridge/MatrixHandler.ts:879",
    "src/models/MatrixAction.ts:189",
    "src/models/MatrixAction.ts:196"
   ],
   "reason_to_dismiss": "Matrix clients always send string bodies, and the fetched-event path already type-checks the body, so the inbound event is assumed well-formed.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/bridge/MatrixHandler.ts:875",
    "src/bridge/MatrixHandler.ts:879",
    "src/models/MatrixAction.ts:189",
    "src/models/MatrixAction.ts:196",
    "src/bridge/MatrixHandler.ts:1292"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
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
   "If the reply fetch (T1) is closed by trusting only the in-memory cache, the FIFO eviction at MatrixHandler.ts:1387-1390 (eventCacheSize defaults to 4096 at MatrixHandler.ts:56) lets a sender flush the target event out of the cache and re-open the homeserver fetch route, so a cache-only fix and the fetch fix interact.",
   "If the reply/edit fetch (T1/T2) is restricted to the referring user's authority, the cache path (T6) remains the route for bodies the bridge once observed, including messages later redacted, so the disclosure surface only becomes visible at the second site after the first is fixed."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T6",
   "what": "The natural fix for T1 treats the in-memory cache as the only data the bridge itself observed and therefore trustworthy, while T6 shows that same cache is exactly the store that outlives a redaction; dropping cache use to satisfy T6 removes the path T1 relies on, and honouring redactions needs redaction plumbing that the event dispatcher does not have."
  },
  {
   "a": "T3",
   "b": "T1",
   "what": "Both need the sender/room lookup at MatrixHandler.ts:985-994; a fail-closed membership check for T3 drops the messages whose reply source T1 must still resolve, while a fail-open one leaves T3 unfixed."
  }
 ],
 "fairness_risks": [
  "Forbidding the homeserver fetch for reply sources contradicts the must-keep-working behaviour that a reply to a message the bridge never cached still shows a truncated source and the original nick; spec/integ/matrix-to-irc.spec.js:527-575 stubs the bot client's getEvent and expects exactly that, so a cache-only fix breaks a legitimate flow.",
  "A 'sender must be joined' rule conflicts with the current fallback at MatrixHandler.ts:987-994, which continues with the profile displayname when the member state cannot be fetched; failing closed would drop legitimate messages from users whose state the bridge cannot read.",
  "An admin-room ownership rule must not strand admin rooms stored without a user id (the owner column is only written by storeAdminRoom at PgDataStore.ts:478); a fail-closed comparison would disable commands in existing rows.",
  "Requiring origin_server_ts for the age filter would drop events from homeservers that omit it, which config.sample.yaml:20-26 already warns about.",
  "A strict same-room reply rule must still accept thread fallbacks, which are replies with rel_type m.thread (CHANGELOG.md:75, #1697).",
  "Refusing a non-string body is safe, but the same validation must not reject legitimate formatted/HTML events whose content shape differs from plain text."
 ],
 "effort_minutes": 120,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "The stack is built on the content-disclosure feature itself: the reply source (T1) and the edit original (T2) are two separate resolutions of a homeserver-named event with the bot's authority, and they are the A-to-B pair, so a solver who generalises from the report must handle both sites while keeping the ghost-reply fetch working. Around it sit three judgements with genuinely different reasons to dismiss: sender membership is never checked because the appservice is assumed to authenticate senders (T3, absent route plus a strong dismissal, the deepseek-type trap), admin-room commands are authorised by a member-count proxy rather than by the stored room owner (T4, wrong-object/how-type, the mimo-type trap), and the pastebin preview arithmetic can be driven negative by a homeserver-supplied media URI (T5, a how-type value coupled to the reply formatting). That mix defeats both failure modes in the priors: a model that only fixes the reported surface misses T3, and a model that over-hardens the truncation/reply formatting breaks the must-keep-working ghost reply. A stack of only T1+T2 has a single shared guard idea, and a stack built on the replay or type-validation traps is weaker because their natural fixes are ambiguous."
 },
 "unverified": [
  "The text and fix diff of GHSA-wm4w-7h2q-3pf7 (a_fix 4af7d3009f10) are not present in the pinned tree; identifying the edit branch at MatrixHandler.ts:1049-1083 as the A site is an inference from the symmetric privileged getEvent call (1067 versus 1288) and from the H3a 'B elsewhere' label, not from the advisory record.",
  "Whether Intent.getEvent with the appservice bot token can read events in rooms the bot is not joined to, and whether the homeserver applies the impersonated user's history visibility when getIntent(userId) is used, could not be verified because matrix-appservice-bridge is not vendored in the tree.",
  "Whether a rejected onMessage promise escapes as a process-level unhandled rejection (the impact of T5/T8) depends on matrix-appservice-bridge's outcomeFrom implementation, which is not present in the tree.",
  "The exact default of ircClient.getMaxLineLength() (matrix-org-irc) is not in the tree; the negative-length condition depends on it plus the length of the homeserver-supplied media URI.",
  "Whether the hidden fix for the reply route uses getIntent(event.sender) (CWE-280) or checks eventContent.room_id against event.room_id was not verifiable offline; both are consistent with the missing protection recorded in T1."
 ]
}
  ```
- Published fix sites:   - src/bridge/MatrixHandler.ts:1284 — T1 M2 (reason to dismiss: getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.)
  - src/bridge/MatrixHandler.ts:1288 — T1 M2 (reason to dismiss: getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.)
  - src/bridge/MatrixHandler.ts:1291 — T1 M2 (reason to dismiss: getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.)
  - src/bridge/MatrixHandler.ts:1303 — T1 M2 (reason to dismiss: getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.)
  - src/bridge/MatrixHandler.ts:1323 — T1 M2 (reason to dismiss: getEvent is already called with event.room_id and the cache is room-keyed, so the homeserver is assumed to enforce same-room access, and the response's sender/room_id are treated as authoritative.)
  - src/bridge/MatrixHandler.ts:1052 — T2 M1 (reason to dismiss: An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.)
  - src/bridge/MatrixHandler.ts:1060 — T2 M1 (reason to dismiss: An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.)
  - src/bridge/MatrixHandler.ts:1067 — T2 M1 (reason to dismiss: An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.)
  - src/bridge/MatrixHandler.ts:1070 — T2 M1 (reason to dismiss: An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.)
  - src/bridge/MatrixHandler.ts:1078 — T2 M1 (reason to dismiss: An edit diff only repeats text of a message that was already delivered to the same IRC channel when it was bridged, and the FIXME at 1055-1057 presents the fetch as a known accepted limitation.)
- Uncovered routes to confirm (pattern B):   - src/bridge/MatrixHandler.ts:884 — T3 M4 (reason to dismiss: The appservice protocol has the homeserver authenticate senders, so event.sender is treated as authoritative; the only sender check the bridge needs is the virtual-user claim check added for user spoofing.)
  - src/bridge/MatrixHandler.ts:924 — T3 M4 (reason to dismiss: The appservice protocol has the homeserver authenticate senders, so event.sender is treated as authoritative; the only sender check the bridge needs is the virtual-user claim check added for user spoofing.)
  - src/bridge/MatrixHandler.ts:985 — T3 M4 (reason to dismiss: The appservice protocol has the homeserver authenticate senders, so event.sender is treated as authoritative; the only sender check the bridge needs is the virtual-user claim check added for user spoofing.)
  - src/bridge/MatrixHandler.ts:995 — T3 M4 (reason to dismiss: The appservice protocol has the homeserver authenticate senders, so event.sender is treated as authoritative; the only sender check the bridge needs is the virtual-user claim check added for user spoofing.)
  - src/bridge/MatrixHandler.ts:927 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/MatrixHandler.ts:265 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/MatrixHandler.ts:274 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/MatrixHandler.ts:388 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/AdminRoomHandler.ts:206 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/AdminRoomHandler.ts:831 — T4 M10 (reason to dismiss: Admin rooms are treated as 1:1 because the bridge leaves when a third joined member appears, so membership of the room is taken as the authorisation token and the sender is never compared with the stored room owner.)
  - src/bridge/MatrixHandler.ts:1141 — T5 M8 (reason to dismiss: Media identifiers are normally short 24-character values generated by the homeserver, so the max-line budget minus the explanation URL and channel name is assumed to stay positive.)
  - src/bridge/MatrixHandler.ts:1152 — T5 M8 (reason to dismiss: Media identifiers are normally short 24-character values generated by the homeserver, so the max-line budget minus the explanation URL and channel name is assumed to stay positive.)
  - src/bridge/MatrixHandler.ts:1155 — T5 M8 (reason to dismiss: Media identifiers are normally short 24-character values generated by the homeserver, so the max-line budget minus the explanation URL and channel name is assumed to stay positive.)
  - src/util/TrimString.ts:23 — T5 M8 (reason to dismiss: Media identifiers are normally short 24-character values generated by the homeserver, so the max-line budget minus the explanation URL and channel name is assumed to stay positive.)
  - src/bridge/MatrixHandler.ts:1091 — T6 M4 (reason to dismiss: A cached body only exists for messages the bridge already relayed, so a later reply to a redacted message reveals nothing that the same IRC channel did not already see.)
  - src/bridge/MatrixHandler.ts:1284 — T6 M4 (reason to dismiss: A cached body only exists for messages the bridge already relayed, so a later reply to a redacted message reveals nothing that the same IRC channel did not already see.)
  - src/bridge/MatrixHandler.ts:1383 — T6 M4 (reason to dismiss: A cached body only exists for messages the bridge already relayed, so a later reply to a redacted message reveals nothing that the same IRC channel did not already see.)
  - src/bridge/IrcBridge.ts:1169 — T6 M4 (reason to dismiss: A cached body only exists for messages the bridge already relayed, so a later reply to a redacted message reveals nothing that the same IRC channel did not already see.)
  - src/bridge/IrcBridge.ts:1170 — T7 M10 (reason to dismiss: origin_server_ts is the only timestamp available and the homeserver is its authority; the sample config already documents that clocks differ between homeservers.)
  - src/bridge/IrcBridge.ts:1172 — T7 M10 (reason to dismiss: origin_server_ts is the only timestamp available and the homeserver is its authority; the sample config already documents that clocks differ between homeservers.)
  - src/bridge/MatrixHandler.ts:875 — T8 M8 (reason to dismiss: Matrix clients always send string bodies, and the fetched-event path already type-checks the body, so the inbound event is assumed well-formed.)
  - src/bridge/MatrixHandler.ts:879 — T8 M8 (reason to dismiss: Matrix clients always send string bodies, and the fetched-event path already type-checks the body, so the inbound event is assumed well-formed.)
  - src/models/MatrixAction.ts:189 — T8 M8 (reason to dismiss: Matrix clients always send string bodies, and the fetched-event path already type-checks the body, so the inbound event is assumed well-formed.)
  - src/models/MatrixAction.ts:196 — T8 M8 (reason to dismiss: Matrix clients always send string bodies, and the fetched-event path already type-checks the body, so the inbound event is assumed well-formed.)
- Design plan from the lead: TRACK = STACKED (H3a). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: The stack is built on the content-disclosure feature itself: the reply source (T1) and the edit original (T2) are two separate resolutions of a homeserver-named event with the bot's authority, and they are the A-to-B pair, so a solver who generalises from the report must handle both sites while keeping the ghost-reply fetch working. Around it sit three judgements with genuinely different reasons to dismiss: sender membership is never checked because the appservice is assumed to authenticate senders (T3, absent route plus a strong dismissal, the deepseek-type trap), admin-room commands are authorised by a member-count proxy rather than by the stored room owner (T4, wrong-object/how-type, the mimo-type trap), and the pastebin preview arithmetic can be driven negative by a homeserver-supplied media URI (T5, a how-type value coupled to the reply formatting). That mix defeats both failure modes in the priors: a model that only fixes the reported surface misses T3, and a model that over-hardens the truncation/reply formatting breaks the must-keep-working ghost reply. A stack of only T1+T2 has a single shared guard idea, and a stack built on the replay or type-validation traps is weaker because their natural fixes are ambiguous. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Forbidding the homeserver fetch for reply sources contradicts the must-keep-working behaviour that a reply to a message the bridge never cached still shows a truncated source and the original nick; spec/integ/matrix-to-irc.spec.js:527-575 stubs the bot client's getEvent and expects exactly that, so a cache-only fix breaks a legitimate flow. | A 'sender must be joined' rule conflicts with the current fallback at MatrixHandler.ts:987-994, which continues with the profile displayname when the member state cannot be fetched; failing closed would drop legitimate messages from users whose state the bridge cannot read. | An admin-room ownership rule must not strand admin rooms stored without a user id (the owner column is only written by storeAdminRoom at PgDataStore.ts:478); a fail-closed comparison would disable commands in existing rows. | Requiring origin_server_ts for the age filter would drop events from homeservers that omit it, which config.sample.yaml:20-26 already warns about. | A strict same-room reply rule must still accept thread fallbacks, which are replies with rel_type m.thread (CHANGELOG.md:75, #1697). | Refusing a non-string body is safe, but the same validation must not reject legitimate formatted/HTML events whose content shape differs from plain text.. Conflicts the reader found: The natural fix for T1 treats the in-memory cache as the only data the bridge itself observed and therefore trustworthy, while T6 shows that same cache is exactly the store that outlives a redaction; dropping cache use to satisfy T6 removes the path T1 relies on, and honouring redactions needs redaction plumbing that the event dispatcher does not have. | Both need the sender/room lookup at MatrixHandler.ts:985-994; a fail-closed membership check for T3 drops the messages whose reply source T1 must still resolve, while a fail-open one leaves T3 unfixed.

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

## Environment (`tasks/stk-matrix-appservice-irc-ghsaw9mh/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-matrix-appservice-irc-ghsaw9mh/instruction.md`)
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

## Tests (`tasks/stk-matrix-appservice-irc-ghsaw9mh/tests/`)
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
- **Wrong-fix patches** go in `build/stk-matrix-appservice-irc-ghsaw9mh/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-matrix-appservice-irc-ghsaw9mh/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-matrix-appservice-irc-ghsaw9mh/manifest.json`:**
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

**Also in `build/stk-matrix-appservice-irc-ghsaw9mh/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-matrix-appservice-irc-ghsaw9mh --only static
python3 -I common/gate/gate.py stk-matrix-appservice-irc-ghsaw9mh --only nop
python3 -I common/gate/gate.py stk-matrix-appservice-irc-ghsaw9mh --only oracle
python3 -I common/gate/gate.py stk-matrix-appservice-irc-ghsaw9mh --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-matrix-appservice-irc-ghsaw9mh/`;
  - edit only `tasks/stk-matrix-appservice-irc-ghsaw9mh/`, `build/stk-matrix-appservice-irc-ghsaw9mh/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-w9mh-5x8j-9754.json`. Verify each trap on the
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

Stacked task slug: `stk-matrix-appservice-irc-ghsaw9mh`. Control task slug: `stk-matrix-appservice-irc-ghsaw9mh-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-w9mh-5x8j-9754.json`.
