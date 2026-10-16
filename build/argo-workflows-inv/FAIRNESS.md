# argo-workflows-inv: fairness map

Old instruction 548 words; new instruction 628 words. The new one is longer because it adds the
standard constraints block and an Environment section (about 90 words; the old instruction had
neither) and states the contracts as rules, not as per-flaw stories. Tests are unchanged
(identical to `tasks/argo-workflows/tests`, as repaired on 2026-10-16: 17 security, 10 functional).

## Per-test justification

| Test (file::name) | What it asserts | Sentence of the new instruction (or standard knowledge) that makes it fair | Risk |
|---|---|---|---|
| server/workflowtemplate::TestSecZZWorkflowTemplateGetRequiresAuthz | Caller denied read verbs on `workflowtemplates` in the template's namespace `default` (all other resources/verbs granted; cluster-wide review of `workflowtemplates` denied) gets an error and no template body from Get | "hands a stored workflow template to a caller only if the cluster's access control lets that caller read that template: a namespaced template by the caller's rights in its namespace" + "A refused request gets an error and nothing else: no template body". The report's example is this attack. A check on another resource (repair item 2) is not a check of "that template"; a cluster-wide check is not "rights in its namespace" (repair item 3). Using the caller's own identity for the review: "with its own cluster identity ... exactly what the cluster's access control grants that identity", and the repo's existing server-side access checks already do this | low |
| server/clusterworkflowtemplate::TestSecZZClusterWorkflowTemplateGetRequiresAuthz | Caller denied read verbs on `clusterworkflowtemplates` at cluster scope (namespaced reviews of it granted) gets an error and no body | "a cluster-wide template by the caller's cluster-wide rights" + refusal sentence. Also standard Kubernetes knowledge: a cluster-scoped resource is authorised with no namespace | low |
| server/workflowtemplate::TestFuncZZWorkflowTemplateGetAuthorised | Authorised caller gets `zz-wftmpl` | "A caller allowed to read a template receives it" (exactly as today) | low |
| server/clusterworkflowtemplate::TestFuncZZClusterWorkflowTemplateGetAuthorised | Authorised caller gets `zz-cwftmpl` | Same sentence | low |
| server/sync::TestSecZZSyncGetRequiresAuthz | Caller with no ConfigMap rights in `victim-ns` (full rights in the server namespace `argo`, all other resources granted) gets an error from Get of a CONFIGMAP limit and no limit value | "A caller may read a limit only if they may read, in that namespace, the cluster objects that hold the limits ... Rights held in other namespaces do not count." + "no limit value". The protected object class is named ("the cluster objects that hold the limits"), so the neighbouring `workflows` precedent is visibly the wrong target (round-1 §4 rule 3); for the ConfigMap-backed type those objects are ConfigMaps, which the code reads and writes | low-medium |
| server/sync::TestSecZZSyncCreateRequiresAuthz | Read-only (get/list/watch) ConfigMap caller: Create errors and no new ConfigMap exists | "may create, change or remove a limit only if they may change those objects in that namespace" + "no change to any stored limit". A read-verb-only check (repair item 3) fails "may change" | low |
| server/sync::TestSecZZSyncUpdateRequiresAuthz | Read-only caller: Update errors, stored limit still 5 | Same two sentences | low |
| server/sync::TestSecZZSyncDeleteRequiresAuthz | Read-only caller: Delete errors, stored limit still 5 | Same ("remove ... only if they may change those objects"); any write verb passes the stub | low |
| server/sync::TestFuncZZSyncAuthorisedRoundTrip | Caller with all ConfigMap verbs in `victim-ns` only (none cluster-wide) creates a limit and reads back 7 | "A caller who holds the rights above in a namespace, and none cluster-wide, creates, reads, changes and removes limits there" (exactly as today). A cluster-wide check (`sync_cluster_scope_fix`) breaks this | low |
| server/sync::TestFuncZZSyncAuthorisedGet | Same caller reads the existing limit 5 | Same sentence | low |
| server/sync::TestFuncZZSyncAuthorisedUpdateDelete | Same caller updates to 9, then deletes the key | Same sentence ("changes and removes") | low |
| workflow/artifacts/logging::TestSecZZArtifactLoadNoCredLeak | Logging wrapper around a fake driver whose exported `SecretKey` holds a secret: Load writes nothing containing the secret to the log | "Repository credentials (access keys, secret keys, passwords, tokens) never appear in log output, for any artifact operation and any kind of repository." "Any kind of repository" covers the test's fake driver, so a per-driver redaction of known types does not satisfy it | low |
| workflow/artifacts/logging::TestSecZZArtifactSaveNoCredLeak | Same for Save | Same sentence ("any artifact operation") | low |
| workflow/artifacts/logging::TestSecZZArtifactOpenStreamNoCredLeak | Same for OpenStream | Same | low |
| workflow/artifacts/logging::TestSecZZArtifactDeleteNoCredLeak | Same for Delete | Same | low |
| workflow/artifacts/logging::TestSecZZArtifactListObjectsNoCredLeak | Same for ListObjects | Same | low |
| workflow/artifacts/logging::TestSecZZArtifactIsDirectoryNoCredLeak | Same for IsDirectory | Same | low |
| workflow/artifacts/logging::TestFuncZZArtifactDelegates | The wrapper still delegates Load/Save/OpenStream/Delete/ListObjects to the driver without error | "What must keep working, exactly as today: Every artifact operation; only what reaches the log changes." | low |
| server/auth/webhook::TestSecZZWebhookRejectsOversizedBody | 128 MiB body with matching Content-Length: response is 4xx and the body was not read in full | "No one can make the server read or buffer an arbitrarily large request body before the request is authenticated. An oversized webhook delivery is refused." + "Over HTTP it is a client error (4xx)." The cap is the fix's choice; standard knowledge puts webhook body limits in the low megabytes (GitHub caps deliveries at 25 MB), far below 128 MiB, and both a 2 MB and a 10 MiB cap pass (gate) | low |
| server/auth/webhook::TestFuncZZWebhookNormalRequestProcessed | A small correctly signed Bitbucket delivery is not 403 and gets `Bearer my-bitbucket-token` attached | "a correctly signed delivery from a configured provider is accepted and acted on under that provider's identity" (exactly as today) | low |
| server/auth/webhook::TestFuncZZWebhookSmallBodyPassedThrough | A small body matching no provider is not 403 | "a request matching no configured provider is passed on" (exactly as today) | low |
| workflow/controller::TestSecZZRefModeRejectsHostNetwork | Secure referencing, workflow sets `spec.hostNetwork`: phase Error | "if anything the submitter supplies would end up in the specification of the pods the workflow runs, by whatever field or route, the submission is rejected" + "rejected the way the restriction rejects submissions today: it ends in the error state". Host networking is a pod-spec field (standard knowledge) | low |
| workflow/controller::TestSecZZRefModeRejectsServiceAccount | Same, `spec.serviceAccountName`: phase Error | Same; the service account is a pod-spec field | low |
| workflow/controller::TestSecZZRefModeRejectsSecurityContext | Same, `spec.securityContext.runAsUser=0`: phase Error | Same; the pod security context is a pod-spec field | low |
| workflow/controller::TestSecZZRefModeRejectsTemplateDefaultsSecurityContext (2026-10-16 repair) | Same, `spec.templateDefaults.securityContext.runAsUser=0`: phase Error | Same sentence: it is stated in terms of the sink ("would end up in the specification of the pods") and "by whatever field or route", with no restricting adverb and no example list (round-1 §4 rule 2). Verified on the vulnerable code that this value reaches the pod (UID 0) | low |
| workflow/controller::TestFuncZZRefModeLegitWorkflowRuns | A referencing workflow that sets nothing extra: phase Running | "a referencing workflow that overrides nothing runs" (exactly as today); "Apart from the inputs the template declares (its parameters)" keeps an allowlist from refusing legitimate input | low |
| workflow/controller::TestFuncZZRefModePodSpecPatchStillRejected | Strict referencing, `spec.podSpecPatch` set: phase Error | "everything rejected today stays rejected" (preservation), and the patch also ends up in the pod specification, so the main rule covers it too. "The template-referencing restriction" covers every enforcing mode, Strict and Secure | low |

### Contracts kept on purpose (minimum wording)

- Refusal form: any error, plus no data and no side effect ("no template body, no limit value, no
  change to any stored limit"); over HTTP a 4xx. Needed by the 2026-10-16 relaxed checks (repair item 4).
- Ref-mode rejection form: the workflow ends in the error state (phase `Error`, not `Failed`), tied
  to the restriction's existing behaviour.
- Template authorisation scope (repair items 2-3): the object is "that template"; namespaced by its
  namespace, cluster-wide by cluster-wide rights.
- Sync authorisation (repair items 1, 3, 6): the protected object class ("the cluster objects that
  hold the limits"), read vs change rights, "in that namespace", "Rights held in other namespaces do
  not count", and the functional "in a namespace, and none cluster-wide".
- Ref-mode scope (repair item 5): sink wording plus "by whatever field or route".
- Credentials: "any kind of repository" (the test uses its own fake driver).
- Preservation: template read, limit management, every artifact operation, webhook handling
  (signed provider and unmatched pass-through), legitimate referencing workflow and existing
  ref-mode rejections, all "exactly as today".

### Patch checks (gate, 2026-10-16) and the sentence each one breaks

| Patch | Breaks |
|---|---|
| sync_wrong_resource_fix | "the cluster objects that hold the limits" |
| template_wrong_resource_fix | "lets that caller read that template" |
| sync_read_verb_fix | "may create, change or remove a limit only if they may change those objects" |
| sync_wrong_namespace_fix | "in that namespace ... Rights held in other namespaces do not count" |
| sync_cluster_scope_fix (functional) | "holds the rights above in a namespace, and none cluster-wide" |
| refmode_denylist_fix | "anything the submitter supplies ... by whatever field or route" |
| larger_cap_fix, alt_correct_fix (pass) | no cap or layer is stated, so both remain valid |

## Details removed from the old instruction

- Per-flaw sections and headings (five), and with them the count of problems ("several ways").
- Interface names: "gRPC/HTTP API surface", "get template API", "synchronization-limit API",
  "event/webhook entry point", "workflow-execution path" as entry points.
- Mechanism of the template read: "an access review for that caller would deny it".
- Sync-limit wording: "create, read, update, and delete" as a list of operations; "without ever
  checking"; "permitted to modify configuration in that namespace" (replaced by the named object
  class and read/change rights, per round-1 §4 rule 3).
- Log mechanism: "writes a description of the configured artifact backend to the log"; the list of
  operations "loads, saves, streams, lists, or deletes".
- Webhook mechanism: "accepts unauthenticated POST requests and buffers the entire request body into
  memory before it verifies any signature"; "forces a correspondingly large allocation"; "refused
  up front".
- Ref-mode mechanism and example list: "set pod-level fields directly on the referencing workflow,
  for instance host networking, a pod security context, or the service account identity" (the
  word "directly" and the list are what round-1 runs read as the full set; replaced by the sink).
- "a 'template referencing' restriction intended to lock down what submitters may run" (kept only
  as the product feature name).
- Added (not in the old text): the general refusal sentence (error, no data, no side effect, 4xx
  over HTTP, error state for workflows), the parameters exception, the standard constraints block,
  and the Environment section (`/app`, offline, in-process tests against a stand-in cluster).
