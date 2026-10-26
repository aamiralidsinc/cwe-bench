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

Project root: `/home/mara/cwe-bench`. Task: `stk-convoy-18562`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 18562; IDOR / missing tenant authorization on object lookup (CWE-639)
- Pinned (vulnerable) commit: 8c38a84fb8e649a5ca500349ef6bc4e8b3bf6be6. Published fix: 1cc67cd16fb1f8890cc83a3998d3f92dceb7fd06.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-18562",
 "pattern": "H4",
 "repo": "frain-dev/convoy",
 "pinned_commit": "8c38a84fb8e649a5ca500349ef6bc4e8b3bf6be6",
 "protections": [
  "A source row may only be read by a caller authorized on the row's project: FindSourceByID must constrain the fetch to the caller's project before returning the source, its verifier and its pub-sub config.",
  "A source row may only be written inside its own project: UPDATE convoy.sources must be constrained to the project as well as the source id, not keyed on the id alone.",
  "A subscription may only reference sources that belong to the subscription's project: every source_id accepted on create and on update must be resolved within that project.",
  "A project-scoped subscription read must not surface another project's source: the subscription-to-source join must be constrained to s.project_id = sm.project_id, because it selects the source's verifier secrets.",
  "Unauthenticated ingest and CRC capability lookups by mask id stay project-agnostic: the request carries no project and the mask id is the capability."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "internal/sources/impl.go:436",
    "internal/sources/impl.go:437",
    "internal/sources/queries.sql:145",
    "api/handlers/source.go:107"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "internal/sources/impl.go:436-447: FindSourceByID(ctx, projectID, id) accepts projectID and never uses it; it calls s.repo.FetchSourceByID(ctx, id)",
    "internal/sources/queries.sql:143-145: FROM convoy.sources AS s ... WHERE s.id = @id AND s.deleted_at IS NULL",
    "internal/sources/queries.sql:178: the by-name sibling does filter on s.project_id, so the intended pattern is visible next door",
    "internal/sources/impl.go:273-277 with datastore/models.go:1303,1580-1597: the returned Source carries Verifier (hmac secret, basic-auth password, api-key header value)",
    "api/handlers/source.go:107,171,238: three project-scoped handlers pass project.UID into the unscoped fetch and render the source back"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "api/handlers/source.go:171",
    "api/handlers/source.go:238",
    "services/create_subscription.go:69",
    "services/update_subscription.go:85"
   ],
   "reason_to_dismiss": "The report names the GET route; the PUT/DELETE handlers and the two subscription call sites already pass project.UID, so they look project-aware where they are written.",
   "distance": {
    "files": 4,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "api/api.go:450,453,454 and api/api.go:684,687,688: GET, PUT and DELETE /v1/projects/{projectID}/sources/{sourceID} all land on the same unscoped fetch",
    "api/handlers/source.go:171-190: PUT loads the foreign row and then renders the updated source (with verifier secrets) back to the caller",
    "api/handlers/source.go:238-249: DELETE loads the foreign row before the already-scoped DeleteSource (internal/sources/queries.sql:374) runs",
    "services/create_subscription.go:69 and services/update_subscription.go:85: the subscription paths reuse the same unscoped FindSourceByID"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "internal/sources/impl.go:375",
    "internal/sources/impl.go:383",
    "internal/sources/queries.sql:99",
    "internal/sources/queries.sql:108"
   ],
   "reason_to_dismiss": "The handler reads the source through FindSourceByID first and the RowsAffected check reports a foreign id as 'source not found', so once the read is scoped this write is unreachable from HTTP.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "internal/sources/impl.go:360: UpdateSource(ctx, projectID, source) takes the project id",
    "internal/sources/impl.go:375-391: projectID is passed only as the new value of the project_id column, never as a filter",
    "internal/sources/queries.sql:90-108: UPDATE convoy.sources SET project_id = @project_id ... WHERE id = @id AND deleted_at IS NULL",
    "internal/sources/impl.go:397-399: a zero row count is reported as ErrSourceNotFound, so a foreign id is indistinguishable from a missing one for a caller that already holds the row",
    "internal/sources/queries.sql:374: DeleteSource is project-scoped, which shows the write-side pattern was applied to delete and not to update"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "services/update_subscription.go:74",
    "services/update_subscription.go:85",
    "services/update_subscription.go:116",
    "internal/subscriptions/queries.sql:110"
   ],
   "reason_to_dismiss": "UpdateSubscription already resolves the source inside the project at line 85, so the path reads as guarded; the skipping shape exists only because that whole block is nested under endpoint_id.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "services/update_subscription.go:74-90: the FindSourceByID guard sits inside if !util.IsStringEmpty(s.Update.EndpointID) and only runs for datastore.IncomingProject",
    "services/update_subscription.go:116-118: subscription.SourceID = s.Update.SourceID whenever source_id is non-empty, outside that block",
    "internal/subscriptions/queries.sql:105-110,650: UPDATE sets source_id = @source_id WHERE id = @id AND project_id = @project_id; the row is scoped, the referenced source is not",
    "api/models/subscription.go:50-85: UpdateSubscription has no required field, so a body of only {\"source_id\": ...} validates",
    "api/api.go:427,662,863: PUT /v1/projects/{projectID}/subscriptions/{subscriptionID} and the portal-link variant reach this service"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "services/create_subscription.go:65",
    "services/create_subscription.go:69",
    "services/create_subscription.go:93"
   ],
   "reason_to_dismiss": "source_id is an incoming-project field, so for an outgoing project a reviewer assumes it is not used rather than stored and returned.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "services/create_subscription.go:65-74: the entire source check is gated on s.Project.Type == datastore.IncomingProject",
    "services/create_subscription.go:88-102: SourceID is copied into the subscription unconditionally, and internal/subscriptions/impl.go:195 persists it",
    "api/models/subscription.go:14-44: source_id is accepted for every project type; only endpoint_id is required",
    "services/create_subscription.go:61-63: the endpoint is checked against the project, so the create path looks fully project-aware"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "internal/subscriptions/queries.sql:204",
    "internal/subscriptions/queries.sql:444",
    "internal/subscriptions/helpers.go:640",
    "api/handlers/subscription.go:148"
   ],
   "reason_to_dismiss": "The subscription itself is fetched with s.project_id = @project_id, so the response is already project-scoped; the source is only display metadata.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "internal/subscriptions/queries.sql:202-206: LEFT JOIN convoy.sources sm ON s.source_id = sm.id with WHERE s.id = @id AND s.project_id = @project_id; the join has no project condition",
    "internal/subscriptions/queries.sql:187-205: the query selects sm.mask_id, sm.project_id and every source_verifiers secret column",
    "internal/subscriptions/queries.sql:442-447: FetchSubscriptionsPaginated has the same unconstrained source join",
    "internal/subscriptions/helpers.go:299-307,640-648: those columns are rebuilt into the response's source_metadata.verifier",
    "api/handlers/subscription.go:148-170: GET .../subscriptions/{subscriptionID} renders the subscription unchanged"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M11",
   "origin": "uncovered_upstream",
   "locations": [
    "internal/sources/impl.go:467",
    "internal/sources/queries.sql:211",
    "api/ingest.go:41",
    "api/ingest.go:448",
    "internal/pkg/crc/crc.go:49"
   ],
   "reason_to_dismiss": "The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "internal/sources/impl.go:467-478: FindSourceByMaskID takes no project and calls FetchSourceByMaskID(ctx, maskID)",
    "internal/sources/queries.sql:180-211: WHERE s.mask_id = @mask_id AND s.deleted_at IS NULL",
    "api/ingest.go:41,448: both calls come from the unauthenticated /ingest/{maskID} and CRC routes",
    "services/create_source.go:41: MaskID = uniuri.NewLen(16), so the mask id itself is the shared secret",
    "internal/sources/impl.go:161-279: rowToSource is the shared mapper for by-id, by-name, by-mask-id and paged rows, so a project check added there would also gate ingest",
    "internal/pkg/crc/crc.go:33-49: the CRC path needs the source row (and its verifier) to answer, so the lookup cannot 404 on a missing project"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3"
  ],
  [
   "T4",
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T3's unscoped UPDATE is only reachable while T1's read returns a foreign row (api/handlers/source.go:171 -> services/update_source.go:83); scoping the read hides the write for HTTP callers without making UPDATE convoy.sources (internal/sources/queries.sql:108) safe for service-level callers.",
   "The pinned tree already scopes FetchSourceByName (internal/sources/queries.sql:178) and DeleteSource (queries.sql:374) while leaving FetchSourceByID (queries.sql:145) unscoped, so the earlier project-scoping work left this fetch open; the unscoped fetch is a sibling query, not code the earlier fix wrote.",
   "T4/T5 and T6 cover each other: validating source ownership on write stops new bad rows but not rows already stored, and constraining the join stops the leak from any bad row but not the bad write. Fixing one makes the other invisible to a naive test."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T7",
   "what": "Scoping the by-id fetch in the shared mapper (internal/sources/impl.go:161-279) or in a shared query would also gate FetchSourceByMaskID and 404 every unauthenticated ingest and CRC request (api/ingest.go:41,448; internal/pkg/crc/crc.go:33)."
  },
  {
   "a": "T3",
   "b": "T7",
   "what": "Adding project_id to UPDATE convoy.sources must keep the CRC writer working: internal/pkg/crc/crc.go:49 passes source.ProjectID taken from the mask-id lookup, so the WHERE must use the row's stored project, never a request project."
  },
  {
   "a": "T6",
   "b": "T3",
   "what": "The unscoped UPDATE can already have moved a source out of its project, so once the subscription-to-source join is constrained by project an existing subscription can legitimately lose its source_metadata; the invariant must be enforced at write and read together, not inferred from stored rows."
  }
 ],
 "fairness_risks": [
  "Ingest and CRC must stay unauthenticated and project-agnostic (api/ingest.go:41,448; internal/pkg/crc/crc.go:33): the rule 'every source lookup filters by project' contradicts a route that must keep working.",
  "Rejecting a non-empty source_id on a subscription in an outgoing project refuses a shape the current public API accepts (api/models/subscription.go:14-44); clients that send it today would start getting 4xx.",
  "The subscription-to-source join must stay a LEFT JOIN constrained by sm.project_id = s.project_id, so same-project subscriptions still render source_metadata (api/handlers/subscription.go:169) and subscriptions with no source still render.",
  "DELETE /sources/{sourceID} must keep returning the same status for a foreign id through the read at api/handlers/source.go:238; the already-scoped DeleteSource (queries.sql:374) currently turns it into a 400 after the read succeeds, so a fix must choose one status deliberately.",
  "internal/sources/get_source_test.go:253-261 accepts either outcome (ErrSourceNotFound or the foreign row), so it will not fail a correct fix and must not be read as proof that the scope is enforced."
 ],
 "effort_minutes": 45,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T4",
   "T5",
   "T6",
   "T7"
  ],
  "why": "T1 anchors the stack: it is the reported bug and one small guard (compare the fetched row's ProjectID, or filter by project_id in internal/sources/queries.sql:145) closes the GET/PUT/DELETE handlers and both subscription call sites at once. T4 and T5 move the same protected asset (a source's verifier secrets) into a different module with the two most seductive dismissals: 'the check is right there at line 85' inside a block that is skipped when endpoint_id is absent, and 'source_id only matters for incoming projects' for a project type that stores it unchecked. T6 is a read-side fix in internal/subscriptions SQL that stays necessary after any write-side validation, because it covers rows already stored, and it carries the strongest dismissal ('the subscription row is already project-scoped'). T7 punishes over-hardening: it is the M11 coupled value, the only trap whose correct handling is to leave the lookup project-agnostic, and that is the documented MiMo failure. The four groups sit in four places (internal/sources, services/create_subscription.go, services/update_subscription.go, internal/subscriptions) with four different reasons to dismiss; this beats designs built only from T1/T2/T3, which collapse into one edit and one dismissal, and it beats a design that includes the mask-id route as something to scope, which would break a must-keep-working route."
 },
 "unverified": [
  "No shell or git access in this environment: the referenced fix commit 1cc67cd16fb1f8890cc83a3998d3f92dceb7fd06 and the repository history were not inspected; every claim above is read from the pinned tree at 8c38a84.",
  "Whether the published fix also scopes the UPDATE in internal/sources/queries.sql:108, or only the read, is unknown from the pinned tree.",
  "Whether hidden tests exercise the subscription paths (services/create_subscription.go, services/update_subscription.go, internal/subscriptions/queries.sql) or only the source handler cannot be determined from the pinned tree.",
  "Whether the latest release still leaves FetchSourceByMaskID project-agnostic, or has since added a source cache under datastore/cached (there is no source wrapper there today), was not checked.",
  "The project test harness (internal/sources/test_helpers_test.go) launches docker-backed Postgres, so offline-after-build was not verified here.",
  "The JWT blacklist-key canonicalization change at auth/realm/jwt/jwt.go:132-134 belongs to a different advisory carried by the same fix commit and is deliberately excluded; it shares no sink with the source-IDOR family."
 ]
}
  ```
- Published fix sites:   - internal/sources/impl.go:436 — T1 M4 (reason to dismiss: none)
  - internal/sources/impl.go:437 — T1 M4 (reason to dismiss: none)
  - internal/sources/queries.sql:145 — T1 M4 (reason to dismiss: none)
  - api/handlers/source.go:107 — T1 M4 (reason to dismiss: none)
  - api/handlers/source.go:171 — T2 M1 (reason to dismiss: The report names the GET route; the PUT/DELETE handlers and the two subscription call sites already pass project.UID, so they look project-aware where they are written.)
  - api/handlers/source.go:238 — T2 M1 (reason to dismiss: The report names the GET route; the PUT/DELETE handlers and the two subscription call sites already pass project.UID, so they look project-aware where they are written.)
  - services/create_subscription.go:69 — T2 M1 (reason to dismiss: The report names the GET route; the PUT/DELETE handlers and the two subscription call sites already pass project.UID, so they look project-aware where they are written.)
  - services/update_subscription.go:85 — T2 M1 (reason to dismiss: The report names the GET route; the PUT/DELETE handlers and the two subscription call sites already pass project.UID, so they look project-aware where they are written.)
- Uncovered routes to confirm (pattern B):   - internal/sources/impl.go:375 — T3 M4 (reason to dismiss: The handler reads the source through FindSourceByID first and the RowsAffected check reports a foreign id as 'source not found', so once the read is scoped this write is unreachable from HTTP.)
  - internal/sources/impl.go:383 — T3 M4 (reason to dismiss: The handler reads the source through FindSourceByID first and the RowsAffected check reports a foreign id as 'source not found', so once the read is scoped this write is unreachable from HTTP.)
  - internal/sources/queries.sql:99 — T3 M4 (reason to dismiss: The handler reads the source through FindSourceByID first and the RowsAffected check reports a foreign id as 'source not found', so once the read is scoped this write is unreachable from HTTP.)
  - internal/sources/queries.sql:108 — T3 M4 (reason to dismiss: The handler reads the source through FindSourceByID first and the RowsAffected check reports a foreign id as 'source not found', so once the read is scoped this write is unreachable from HTTP.)
  - services/update_subscription.go:74 — T4 M8 (reason to dismiss: UpdateSubscription already resolves the source inside the project at line 85, so the path reads as guarded; the skipping shape exists only because that whole block is nested under endpoint_id.)
  - services/update_subscription.go:85 — T4 M8 (reason to dismiss: UpdateSubscription already resolves the source inside the project at line 85, so the path reads as guarded; the skipping shape exists only because that whole block is nested under endpoint_id.)
  - services/update_subscription.go:116 — T4 M8 (reason to dismiss: UpdateSubscription already resolves the source inside the project at line 85, so the path reads as guarded; the skipping shape exists only because that whole block is nested under endpoint_id.)
  - internal/subscriptions/queries.sql:110 — T4 M8 (reason to dismiss: UpdateSubscription already resolves the source inside the project at line 85, so the path reads as guarded; the skipping shape exists only because that whole block is nested under endpoint_id.)
  - services/create_subscription.go:65 — T5 M1 (reason to dismiss: source_id is an incoming-project field, so for an outgoing project a reviewer assumes it is not used rather than stored and returned.)
  - services/create_subscription.go:69 — T5 M1 (reason to dismiss: source_id is an incoming-project field, so for an outgoing project a reviewer assumes it is not used rather than stored and returned.)
  - services/create_subscription.go:93 — T5 M1 (reason to dismiss: source_id is an incoming-project field, so for an outgoing project a reviewer assumes it is not used rather than stored and returned.)
  - internal/subscriptions/queries.sql:204 — T6 M4 (reason to dismiss: The subscription itself is fetched with s.project_id = @project_id, so the response is already project-scoped; the source is only display metadata.)
  - internal/subscriptions/queries.sql:444 — T6 M4 (reason to dismiss: The subscription itself is fetched with s.project_id = @project_id, so the response is already project-scoped; the source is only display metadata.)
  - internal/subscriptions/helpers.go:640 — T6 M4 (reason to dismiss: The subscription itself is fetched with s.project_id = @project_id, so the response is already project-scoped; the source is only display metadata.)
  - api/handlers/subscription.go:148 — T6 M4 (reason to dismiss: The subscription itself is fetched with s.project_id = @project_id, so the response is already project-scoped; the source is only display metadata.)
  - internal/sources/impl.go:467 — T7 M11 (reason to dismiss: The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.)
  - internal/sources/queries.sql:211 — T7 M11 (reason to dismiss: The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.)
  - api/ingest.go:41 — T7 M11 (reason to dismiss: The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.)
  - api/ingest.go:448 — T7 M11 (reason to dismiss: The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.)
  - internal/pkg/crc/crc.go:49 — T7 M11 (reason to dismiss: The ingest route is public and the mask id is the capability; the request carries no project and the handler never returns the source row, so the lookup must stay project-agnostic and touching it only breaks ingestion.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T4, T5, T6, T7. Why: T1 anchors the stack: it is the reported bug and one small guard (compare the fetched row's ProjectID, or filter by project_id in internal/sources/queries.sql:145) closes the GET/PUT/DELETE handlers and both subscription call sites at once. T4 and T5 move the same protected asset (a source's verifier secrets) into a different module with the two most seductive dismissals: 'the check is right there at line 85' inside a block that is skipped when endpoint_id is absent, and 'source_id only matters for incoming projects' for a project type that stores it unchecked. T6 is a read-side fix in internal/subscriptions SQL that stays necessary after any write-side validation, because it covers rows already stored, and it carries the strongest dismissal ('the subscription row is already project-scoped'). T7 punishes over-hardening: it is the M11 coupled value, the only trap whose correct handling is to leave the lookup project-agnostic, and that is the documented MiMo failure. The four groups sit in four places (internal/sources, services/create_subscription.go, services/update_subscription.go, internal/subscriptions) with four different reasons to dismiss; this beats designs built only from T1/T2/T3, which collapse into one edit and one dismissal, and it beats a design that includes the mask-id route as something to scope, which would break a must-keep-working route. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Ingest and CRC must stay unauthenticated and project-agnostic (api/ingest.go:41,448; internal/pkg/crc/crc.go:33): the rule 'every source lookup filters by project' contradicts a route that must keep working. | Rejecting a non-empty source_id on a subscription in an outgoing project refuses a shape the current public API accepts (api/models/subscription.go:14-44); clients that send it today would start getting 4xx. | The subscription-to-source join must stay a LEFT JOIN constrained by sm.project_id = s.project_id, so same-project subscriptions still render source_metadata (api/handlers/subscription.go:169) and subscriptions with no source still render. | DELETE /sources/{sourceID} must keep returning the same status for a foreign id through the read at api/handlers/source.go:238; the already-scoped DeleteSource (queries.sql:374) currently turns it into a 400 after the read succeeds, so a fix must choose one status deliberately. | internal/sources/get_source_test.go:253-261 accepts either outcome (ErrSourceNotFound or the foreign row), so it will not fail a correct fix and must not be read as proof that the scope is enforced.. Conflicts the reader found: Scoping the by-id fetch in the shared mapper (internal/sources/impl.go:161-279) or in a shared query would also gate FetchSourceByMaskID and 404 every unauthenticated ingest and CRC request (api/ingest.go:41,448; internal/pkg/crc/crc.go:33). | Adding project_id to UPDATE convoy.sources must keep the CRC writer working: internal/pkg/crc/crc.go:49 passes source.ProjectID taken from the mask-id lookup, so the WHERE must use the row's stored project, never a request project. | The unscoped UPDATE can already have moved a source out of its project, so once the subscription-to-source join is constrained by project an existing subscription can legitimately lose its source_metadata; the invariant must be enforced at write and read together, not inferred from stored rows.

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

## Environment (`tasks/stk-convoy-18562/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-convoy-18562/instruction.md`)
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

## Tests (`tasks/stk-convoy-18562/tests/`)
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
- **Wrong-fix patches** go in `build/stk-convoy-18562/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-convoy-18562/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-convoy-18562/manifest.json`:**
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

**Also in `build/stk-convoy-18562/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-convoy-18562 --only static
python3 -I common/gate/gate.py stk-convoy-18562 --only nop
python3 -I common/gate/gate.py stk-convoy-18562 --only oracle
python3 -I common/gate/gate.py stk-convoy-18562 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-convoy-18562/`;
  - edit only `tasks/stk-convoy-18562/`, `build/stk-convoy-18562/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-18562.json`. Verify each trap on the
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

Stacked task slug: `stk-convoy-18562`. Control task slug: `stk-convoy-18562-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-18562.json`.
