# FAIRNESS — stk-mlflow-3745

Static review only. Read: instruction.md, all 9 files under tests/, solution/fix.patch,
manifest.json, notes.md, all 14 checks/*.patch, listing.json and the trial evidence. Nothing run.

## 1. Per-test fairness

| test (file::name) | asserts | covering instruction sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/test_secret_configuration.py::test_create_rejects_loopback_upstream | create with auth_config api_base `http://127.0.0.1:9/v1` returns a 4xx and the name is not listable | "No value supplied by a user ... may cause an outbound gateway call to reach a destination that is not publicly routable"; "the configuration is refused and the request has no effect"; "A refused configuration ... reported to the client as a client error and has no effect"; "internal, loopback, link-local ... are not publicly routable" | no. Any 4xx and any layer that sees the supplied map (handler body, store, endpoint build) passes; a connect-only guard contradicts the explicit supply-time refusal, so it is a wrong fix, not a failed correct one | low |
| ::test_create_rejects_private_network_upstream | same for `http://10.1.2.3/v1` | same property; 10/8 is internal by standard expert knowledge (RFC 1918) | no | low |
| ::test_create_rejects_link_local_upstream | same for `http://169.254.169.254/...` | same property; link-local is named | no | low |
| ::test_update_rejects_internal_upstream_and_keeps_previous_value | a public create succeeds; a loopback update returns 4xx; the old `https://8.8.8.8/v1` is still returned | "The rule holds both when such a value is supplied — the configuration is refused and the request has no effect"; "no value supplied by a user" | no. A handler-level or store-level update guard both pass; status just has to be 4xx; "no effect" gives the retained value | low |
| security/test_stored_configuration.py::test_already_stored_internal_upstream_is_never_dialed | after an out-of-band write of the stored auth_config to a loopback canary, invoke makes no connection | "no such value already stored for a gateway, may cause an outbound gateway call to reach a destination that is not publicly routable" | no. A guard when the config is loaded or when the call is made both pass; the test demands no particular status | low |
| security/test_merged_configuration.py::test_encrypted_secret_value_cannot_override_the_upstream | a loopback api_base inside secret_value is either 4xx at create, or the invoke returns 4xx and never reaches the canary | "No value supplied by a user ..."; "the configuration is refused and the request has no effect" | no. Either refusal point is accepted; any 4xx | low |
| security/test_shipped_default.py::test_supplied_address_matching_the_shipped_local_default_is_refused | a supplied `http://127.0.0.1:11434/v1` on an ollama secret returns 4xx and is not stored | "No destination-forming value supplied by a user (an address, host, or any other value the call's destination is built from) ... may cause ..."; loopback is not publicly routable | no. The supplied address forms the destination, so it is refused at supply time; only a source-insensitive string carve-out fails, which the sentence forbids | low |
| security/test_derived_address.py::test_location_value_cannot_redirect_the_call | vertex_location `127.0.0.1:<port>/#` returns 4xx and the canary is untouched | "any other value the call's destination is built from ... may cause an outbound gateway call to reach a destination that is not publicly routable"; "The example above is one instance, not the full set" | no. A plain-name rule or a check of the composed host both pass; supply-time refusal is stated | medium |
| ::test_region_value_cannot_change_the_host | aws_region_name `evil.example@127.0.0.1:9/#` returns 4xx and is not stored | same | no (same) | medium |
| functional/test_configuration_lifecycle.py::test_public_configuration_round_trip | create/list/get/update with public 8.8.8.8 and 1.1.1.1 all 200, values round-trip | "Preservation. Everything that works today keeps working"; "Keep every legitimate use working" | no. Both addresses are publicly routable, so no rule forbids them; rejecting public literal IPs would be incorrect, not ambiguous | low |
| ::test_endpoint_and_model_definition_lifecycle | public secret, model definition, endpoint, get all 200 | preservation | no | low |
| functional/test_legitimate_upstreams.py::test_shipped_local_default_is_still_called | ollama secret created with no address; invoke reaches 127.0.0.1:11434 and returns 200 | preservation; the refusal is scoped to "a destination reached because of a destination-forming value a user supplied ..., or because of such a value already stored for a gateway". Choosing a provider is not a destination-forming value: no supplied or stored address, host or other destination-forming value exists here, so the property does not forbid the shipped code default | no. A correct fix scoped to destination-forming values passes; "Keep every legitimate use working" requires the default to keep working | low |
| ::test_public_third_party_configuration_still_used | a cohere secret with a public api_base plus non-address secret_value keys creates, and its model definition and endpoint create | preservation | no. A public address and a non-address key are not refused by any rule | low |
| ::test_legitimate_region_and_location_names_are_accepted | global, us-central1, europe-west4, us-east-1, eu-west-1 all accepted | preservation | no. A name is not a destination; no rule forbids it | low |

## 2. Leniency (quality)

| property / trap | most plausible WRONG fix | caught by | gap |
|---|---|---|---|
| T1 write-time supplied value | no destination check on create (`miss_write_time.patch`) | test_create_rejects_loopback_upstream (+ private, link-local) | none |
| T2 update replaces the stored configuration | validate create only (`sf-update-only.patch`) | test_update_rejects_internal_upstream_and_keeps_previous_value | none |
| T3 store persists unvalidated | validate on read only (`sf-reads-only.patch`) | the three create tests | a handler-only guard leaves the store unchecked and passes (pass-alternative scores 1.0); no test calls the store directly |
| T4 encrypted map merged over stored config | validate auth_config only (`miss_merged_config.patch`) | test_encrypted_secret_value_cannot_override_the_upstream | discarding all secret_value keys at use is not caught: the cohere functional test never invokes |
| T5 stored row reloaded / connect time | write-time only (`miss_connect_time.patch`) | test_already_stored_internal_upstream_is_never_dialed | a crash or 5xx at connect passes this test (only canary hits are asserted) |
| T6 shipped default beside a supplied value | string-equality carve-out of the shipped address (`miss_shipped_default.patch`) | test_supplied_address_matching_the_shipped_local_default_is_refused | the opposite over-block is caught by test_shipped_local_default_is_still_called (`ff-block-shipped-default.patch`) |
| T7 host composed from region/location | check URL fields only, tokens unvalidated (`miss_derived_host.patch`) | both test_derived_address.py tests | none |
| T8 provider renames of the same key | validate api_base only; ignore base_url and the endpoint-build rename | only test_create_rejects_loopback_upstream (which checks api_base) | **not caught**: no test uses base_url, and no test builds an endpoint from a supplied address that reaches the rename path |
| wrong object | validate deployment_name (`sf-wrong-object.patch`) | the create tests | none |
| refuse everything | `ff-refuse-all.patch` | test_shipped_local_default_is_still_called | none |
| crash as refusal | `sf-crash.patch` | 8 create/update/derived tests | not on the stored-row route |
| catalogue n/a | check_after_adjustment, malformed_identity, missing_authority, adjacent_api | — | I agree: no normalising step, stdlib URL parsing, no authority, defaulted argument |

Wrong fixes **no test catches**: (1) validate api_base but not base_url; (2) literal-IPv4-only
checks (`localhost`, `::1`, `[::ffff:127.0.0.1]`, `0.0.0.0` never appear); (3) refuse every
non-https URL (all functional fixtures are https, so over-refusal of a public http upstream is
unseen); (4) return a 5xx instead of a 4xx at connect on the stored-row route; (5) never implement
the operator opt-in; (6) drop all secret_value keys at use; (7) a handler-only guard (T3's store
layer is not independently exercised).

## 3. Hints (quality)

- "The rule holds both when such a value is supplied — the configuration is refused and the request
  has no effect — and again when a call is about to connect." — names both enforcement points (the
  fix approach). Neutral: "A destination that would be reached because of such a value or
  configuration is refused and has no effect."
- "For example, registering a secret whose provider address is `http://127.0.0.1:8080/v1`, creating
  an endpoint from it, and sending a chat request to that endpoint causes the gateway to open a
  connection to the local service, and the response is relayed back to the caller." — the repro
  chain and literal input. Neutral: "A user who may create gateway configuration can make the
  gateway connect to an address of their choosing inside the deployment or on the host, and the
  response is relayed back to the caller."
- "A secret carries a provider's credentials together with configuration describing where that
  provider is reached; an endpoint call makes the gateway issue a request to that destination." —
  locates the address in the secret configuration and states the mechanism. Neutral: "MLflow's AI
  Gateway lets an operator register provider credentials and route completion requests through
  them; a gateway call issues a request to the destination derived from the configuration held for
  it."
- "internal, loopback, link-local, and unspecified destinations are not publicly routable" — a
  variant list matching three of the four classes the tests use. Neutral: "destinations that are
  not publicly routable are refused" (the classes are standard expert knowledge).
- "Fix the flaw and its close variants, not just the request shown" and "The example above is one
  instance..." are generic cautions, not hints; keep.

## 3a. Required: generalize

1. "The rule holds both when such a value is supplied — the configuration is refused and the
   request has no effect — and again when a call is about to connect." Names the connect stage;
   the property over "configuration already stored" already covers that route. State the outcome
   once: "A destination that would be reached because of such a value or configuration is refused,
   and the refusal has no effect: the configuration is not stored or changed and no request reaches
   the destination."
2. "For example, registering a secret whose provider address is `http://127.0.0.1:8080/v1`,
   creating an endpoint from it, and sending a chat request to that endpoint..." Walks three
   operations and the literal input. State the impact only: "A user who may create gateway
   configuration can make the gateway connect to an address of their choosing inside the deployment
   or on the host, and the response is relayed back to the caller."
3. "an endpoint call makes the gateway issue a request to that destination." Names the operation.
   Replace with the property over the data: "a gateway call issues a request to the destination
   derived from the configuration held for it."

## 4. Realism (quality)

- T1-T6 are unmodified upstream code paths (handler copies, store writes, merge, reload, shipped
  default); each is a mistake a maintainer could have made and each is reached through the real
  handler or ASGI route.
- T7 is marked injection_room, but the values are genuine URL-authority injection against the real
  host-composition templates in vertex_ai.py/bedrock.py, reachable at secret creation. Not
  contrived.
- The raw-SQL fixture writes a row an operator could have written before the check existed; the
  instruction names exactly that state. Not a backdoor.
- No product code is planted; the wrong-object and string-carve-out behaviours exist only in
  checks/*.patch.
- Data note: `checks/upstream_fix.patch` is the unrelated raw-proxy/User-Agent commit, not a fix for
  this advisory, so the "published-fix recall" result proves nothing. Metadata only; the real
  unmodified routes it leaves open stay in scope.

## Stacking checks

| check / concept | result |
|---|---|
| S1 Coupled traps | round-trip pair: covered by "Everything that works today keeps working" / "Keep every legitimate use working"; 8.8.8.8 and 1.1.1.1 are public, no rule forbids them. Shipped-default pair: covered by preservation; the rule is scoped to destination-forming values, and choosing among the product's providers supplies none, so a code default is not forbidden. Third-party pair: client_label/version are not destination-forming values. Region/location pair: those values do compose the destination, so the security rule covers them; plain names remain inside the legitimate set. No contradiction; gate a does not fire. |
| S2 Shape traps | Refused shapes: 127.0.0.1, 10.1.2.3, 169.254.169.254, a stored loopback, a supplied 127.0.0.1:11434, "127.0.0.1:PORT/#", "evil.example@127.0.0.1:9/#". Legitimate set from fixtures: 8.8.8.8, 1.1.1.1, plain region/location names, and provider selection with no address. Every refused shape is outside it; the one same-string case (11434) is accepted only when unsupplied, and the instruction's destination-forming scope distinguishes the two because the unsupplied case forms no destination from a user or stored value. Pass. |
| S3 Fixtures and harness | Every secret, model definition and endpoint is created through the real handlers; invoke uses the real ASGI chat route; the raw-SQL row is the "configuration already stored" the instruction names. Valid layers all run: handler body, store, endpoint-config build (pass-hardening), provider, shared request primitive. Only a guard in a Flask app-level before_request or a route decorator outside the handler function is bypassed, which is not a natural layer. Pass with note. |
| S4 Concept independence | Each concept's tests pass with only that concept fixed, and each security test fails on the pinned tree through its own route (C1 create returns 200; C2 canary hit; C3 canary hit; C4 create 200; C5 create 200). No masking. 5 concepts remain. |
| S5 History | Pattern H4, not H3a/H3b: there is no checks/upstream_first_fix.patch, and F5 is not applicable. See the realism note on upstream_fix.patch. |
| S6 Contracts | Every field the tests send is an existing product field (secret_name, secret_value, auth_config, api_base, provider, vertex_project, vertex_location, aws_region_name, auth_mode); no new name to guess. The protected object is named in product terms ("configuration describing where that provider is reached", "provider address"). No fail-open authority. The opt-in interface is not stated and never exercised — quality, not a correct-fix barrier. |
| S7 Decisive tests | The mimo trial evidence records a single failing test: functional/test_legitimate_upstreams.py::test_shipped_local_default_is_still_called ("the shipped local default was not called", response 400); the post-run audit attributed it to instruction ambiguity, not to the fix being wrong. The 2026-10-25 rewording removes that ambiguity by scoping both security sentences to destination-forming values, so a correct fix following the property passes and the model's blanket guard is now plainly the wrong fix. Re-checked against S1-S6 it is fair. The deepseek 3x reward 0.0 has no per-test breakdown. NEEDS_HUMAN_REVIEW: NO. |
| C1 T1/T2/T3/T8 | Write-time check on supplied configuration: passes its 4 security tests and the round-trip functional with no other concept fixed. Note T8 has no distinct test. |
| C2 T4 | Validate the merged map: passes with only this concept (create 200 then invoke 4xx). |
| C3 T5 | Validate the stored configuration when it is used: passes with only this concept. |
| C4 T6 | Distinguish the shipped default from a supplied value: passes both tests; the security test still fails on pinned. |
| C5 T7 | Validate the region/location tokens or the composed host: passes both tests with only this concept. |

## Revision 2026-10-25 (AUDIT-FIX-20261025, instruction-only)

The post-run Opus audit of the MiMo r3 trial attributed the single decisive failure
(`functional/test_legitimate_upstreams.py::test_shipped_local_default_is_still_called`, response 400)
to instruction ambiguity: the security sentences could be read to cover a user's choice of provider,
which routes to the product's built-in destination, while preservation requires that destination to
keep working. Both security sentences are now scoped to **destination-forming values** — "an address,
host, or any other value the call's destination is built from" — so choosing among the product's
providers is not such a value. Nothing else changed: tests, solution/fix.patch, manifest, checks and
every other instruction sentence are untouched, and the built-in default is neither named nor given
an exception (it remains covered only by preservation).

Per-test re-check after the rewording: the shipped-default security test supplies a
destination-forming address and stays refused; the shipped-default functional test supplies none and
stays working; T4 (secret_value address), T5 (stored address), T7 (region/location composed into the
host) and T1/T2/T3/T8 all remain covered by "any other value the call's destination is built from" or
"such a value already stored". No test needed changing; the gate was re-run on the new wording
(static/nop/oracle/patches all PASS).

## Verdict

**READY.** Gate a asks only whether a correct fix written from instruction.md passes every test, and
it does. Every security assertion is covered, read literally, by the general property over
destination-forming values and stored destination-forming values; all refusal forms are 4xx, so any
client error works; and the two layer-shifted correct fixes provided in checks (pass-alternative at
the handler, pass-hardening at the endpoint build) both score 1.0, so no particular implementation
layer is demanded. No row has a yes or an unresolved maybe. The former borderline item — the shipped
default — is resolved by the destination-forming scope: the test that exercises it supplies no
destination-forming value, so no security rule read literally forbids it and preservation keeps it
working; the T5 raw-SQL row is exactly a stored destination-forming value the property names.
Leniency, hints and realism below do not affect the gate.

Required: generalize — see §3a: (1) the "again when a call is about to connect" stage clause;
(2) the repro chain with the literal address; (3) "an endpoint call makes the gateway issue a
request to that destination."

Quality to tighten — see §2-4: add security cases for base_url, `localhost`, `::1`, `0.0.0.0` and a
public http upstream; assert a 4xx (not just no canary hit) on the stored-row route; invoke in the
cohere functional test; add an opt-in test or drop that contract; neutralise the four hint
sentences; correct the manifest's history note about the published fix.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
