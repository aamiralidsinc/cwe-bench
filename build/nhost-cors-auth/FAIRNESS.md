# nhost-cors-auth: fairness and leniency review

Reviewer: blind pre-trial review. I read instruction.md, every file in tests/, solution/fix.patch,
manifest.json, notes.md and checks/*.patch. Nothing was run. Statements about how the check patches
behave come from manifest `verified.local_runs`; I did not re-check them.

## 1. Tests

Hidden tests start the real `configserver.Command()` on loopback. Test files: `sec` = security/.../sec_test.go,
`func` = functional/.../func_test.go.

| Test | Asserts | Instruction basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| sec::TestSecForeignWebsiteOrigin | `https://evil.example`: the preflight to /v1/configserver/graphql is not allowed, the appSecrets POST response does not grant the origin, and .secrets is unchanged | "A web page may make CORS-preflighted requests … only if it comes from an origin the local dashboard is served from"; "must not grant it in its CORS answer … may also reject … with a client error" | no. Both a missing grant and a 4xx pass. | low |
| sec::TestSecLookalikeHostEndingOrigin | Same checks for `https://local.dashboard.local.nhost.run.evil.example` | "No other origin may, however closely it resembles one of these" | no | low |
| sec::TestSecOtherLocalServiceHostOrigin | Same checks for `https://attacker.local.nhost.run` | "That includes other hosts" | no | low |
| sec::TestSecNestedSubdomainOrigin | Same checks for `https://a.b.dashboard.local.nhost.run` | "`<subdomain>` is a single DNS label" | no | low |
| sec::TestSecLocalDevServerOrigin | Same checks for `http://localhost:3000` | "local development servers on the developer's machine" | no | low |
| sec::TestSecLogsAPIForeignWebsiteOrigin | Same checks on /v1/logs/graphql | Intro names `/v1/logs/graphql`; "(configuration, secrets or logs)" | no | low |
| sec::TestSecSecretListingHidesValues | No on-disk secret value appears in the appSecrets or appsSecrets response, even for the dashboard origin | "No response from the service may contain the value … This holds for the dashboard and every other client" | no. The test only checks for substrings, so any mask works. A null `value` would cause a GraphQL error and fail mustOK. Standard GraphQL knowledge says a non-null field must not be nulled. | low |
| sec::TestSecResolvedConfigHidesValues | No secret value appears in `config(resolve:true)` or `configRawJSON(resolve:true)` | "whatever query is used" | no | low |
| func::TestFuncDashboardOriginsAllowed | For 6 dashboard origins (both host forms, http/https, ports), on both APIs: the preflight is 2xx with ACAO = the origin or `*`, Allow-Methods contains POST (or `*`), Allow-Headers contains content-type (or `*`), and the POST returns 200 with a grant | "The dashboard on its origins works exactly as today"; the origin rule with "over http or https, with or without a port"; logs API named | no. Credentialed use and specific header values are not required. | low |
| func::TestFuncRequestWithoutOrigin | A POST with no Origin returns 200 with no GraphQL errors | "Clients that send no `Origin` header … keep working" | no | low |
| func::TestFuncSecretNamesListed | appSecrets returns exactly the 6 names | "Secret names stay visible"; "listing secret names" | no | low |
| func::TestFuncUpdateSecretKeepsOthers | updateSecret writes the new value, keeps the entry count, and leaves the other values on disk unchanged | "adding, changing and deleting secrets"; "Its values change only when a user explicitly sets or deletes that secret" | maybe. A fix whose mask breaks validation of the resolved config could fail it. The likely case is an empty-string mask against min-length or required fields. The oracle's comment says such rules exist. alt_rscors (8-char mask) passes on this fixture. | low |
| func::TestFuncSuccessiveSecretEdits | Two updates in a row both land and the others are unchanged | same | maybe (same mask caveat) | low |
| func::TestFuncInsertSecretKeepsOthers | insertSecret writes the new value and the others are unchanged | same | maybe (same) | low |
| func::TestFuncDeleteSecretKeepsOthers | deleteSecret removes the entry and the others are unchanged | same | maybe (same) | low |
| func::TestFuncResolvedConfigSettings | `config(resolve:true)` succeeds and contains versions and clientUrl | "browsing the configuration (including the configured service versions and settings)" | **maybe**. A competent engineer who sees `resolve:true` as the leak may refuse or error it for secret-bearing configs, or error whenever secrets are masked. The instruction never says the dashboard uses the resolved form. A solver can only learn that from the dashboard/ TypeScript code. | **medium** |
| func::TestFuncUnresolvedConfigShowsReferences | `config(resolve:false)` shows `{{ secrets.X }}` | "without losing its `{{ secrets.NAME }}` references" | no | low |
| func::TestFuncUpdateConfigKeepsReferences | updateConfig persists the change, keeps the references in nhost.toml, and leaves .secrets untouched | "editing it without losing its … references"; "Its values change only when …" | maybe (mask/validation caveat, as above) | low |
| project::TestCORS (oapi middleware, pristine copy) | Semantics of the shared CORS helper: nil list allows all, empty list denies all, a disallowed preflight gets 204 with no headers, and so on | "Keep legitimate use working". Standard expert knowledge: don't change the defaults of a shared library used by other services. | maybe, if a solver changes how the shared helper handles a refused origin (for example 403 for everyone). Not needed for a correct fix. | low |
| project::TestTimeRangeCheck (logsapi helpers) | Unrelated logs helper | n/a (regression) | no | low |

Excluded project tests (correctly): logsapi `TestCheckWebSocketOrigin` (asserts that localhost is accepted) and
configserver `local_test.go`. A correct fix breaks local_test.go (see §5, item 2).

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 loader/producer | Fix CORS only and leave the secrets unredacted | yes: TestSecSecretListingHidesValues and TestSecResolvedConfigHidesValues (cors_only.patch) |
| T1 | Mask only the listing resolvers | yes: TestSecResolvedConfigHidesValues (listing_redaction_only.patch) |
| T1 | Mask at the resolver layer and miss `runServiceConfig(s)(resolve:true)` | **no**. The fixture configures no run services. |
| T2 save path | Redact in the loader without merging, so stand-ins overwrite real values | yes, functionally: the 4 *KeepsOthers/SuccessiveEdits tests (redact_no_merge.patch) |
| T3 origin shapes | Unanchored regex | yes: TestSecLookalikeHostEndingOrigin (unanchored_origin.patch) |
| T3 | Copy the websocket checker (suffix + localhost) | yes: Nested + LocalDevServer (hostname_suffix_check.patch) |
| T3 | Grant every preflight and restrict only response reads | yes: the preflight half of every TestSec*Origin (preflight_open.patch) |
| T3 | Accept `null` origin, bare `dashboard.local.nhost.run`, trailing path/slash, `local.dashboard.nhost.run.evil.example`, or a scheme other than http/https | **no**. None are tested. The manifest's O6 lists bare host, trailing path and empty origin as shapes, but no test exercises them. |
| T4 logs API | Path-scoped restriction | yes: TestSecLogsAPIForeignWebsiteOrigin (config_path_only.patch) |
| T5 over-hardening | Deny all origins | yes: TestFuncDashboardOriginsAllowed (refuse_all.patch) |
| T5 | Change the shared helper's nil default | yes: project TestCORS (adjacent_api.patch) |
| "No side effect" | Server still runs a mutation for a refused origin | Not really tested: the security POST is a read. The gap is not exploitable, because the JSON-only POST transport forces a preflight. |
| Secret redaction for values set via the API | After updateSecret/insertSecret, later appSecrets and resolve:true return the **new real value** | **no**, and the **oracle itself does this** (notes.md "Out of scope"). This contradicts the instruction (§5). |
| Logs websocket origin check (localhost, multi-label) | Left as is | **no**. The oracle leaves it too. The instruction's "Browser access is for the dashboard only … logs" arguably covers it. |

Wrong fixes no test catches: resolver-layer masking that misses runServiceConfig resolve; the untested origin shapes above; leaking API-set secret values; the loose logs websocket origin check.

## 3. Hints

- "(configuration, secrets or logs)" names the T4 second API. The intro already lists both endpoints, so this can become "requests to the service". Low.
- "however closely it resembles one of these. That includes other hosts and local development servers on the developer's machine" paraphrases the T3 variants: lookalike, sibling host, localhost. **Keep it.** It is needed for fairness: the repo's websocket checker accepts localhost, so refusing it is otherwise a guess.
- "whatever query is used" hints that more than one query leaks (T1). Neutral version: drop it, because "No response from the service" already covers it. Low.
- "The secrets file stays the authority for secret values. Its values change only when a user explicitly sets or deletes that secret." This is a strong paraphrase of the T2 merge trap. Neutral version: "Editing one secret from the dashboard leaves the others as they are." That is still a must-keep, but it doesn't describe the mechanism. Medium.
- "CORS-preflighted requests … or read its responses" hints at preflight_open. It is needed to define the property. Keep it.
- The origin pattern is spelled out in full. That is specification, needed for the Nested test. Keep it.
- No file, function, flaw count or fix approach is named.

## 4. Realism

All trap sites are upstream code at the pinned parent: `cors.Default()`, the GetApps loader, UpdateSecrets, the logs API on the same engine, and the shared oapi CORS helper. None are planted. The entry point is the real hidden `configserver` command. The looser websocket origin checker is genuine upstream code, which makes the T3 copy temptation natural. Nothing looks contrived.

## 5. Verdict: NOT READY

Required changes:

1. **The instruction and the oracle disagree on API-set secrets.** The instruction says "No response … may contain the value of a secret stored in the project's secrets file". After updateSecret, the oracle returns the new (stored) value from appSecrets and resolve:true. Pick one:
   - (a) Reword to "No response from the service may contain a secret value it read from the project's secrets file."
   - (b) Better: make the oracle re-mask after persisting, and add a security test (update, then query, then assert the new value is absent).
2. **"Do not modify or add tests"** conflicts with the fix. Any loader-level redaction breaks the existing `cli/cmd/configserver/local_test.go` (TestLocalGetApps asserts real values; TestLocalUpdateSecrets asserts the old write-through). The oracle edits that file. It is not graded, but it may push solvers away from the correct design, and the oracle visibly breaks the constraint. Fix: drop local_test.go edits from the oracle, or reword the constraint to "Do not weaken or delete tests. Existing tests that assert the old, insecure behaviour may be updated."
3. **"Clients that send no Origin header … keep working exactly as today"** contradicts the redaction rule ("every other client"). Reword to "keep working as today, apart from the secret-value rule above".
4. **TestFuncResolvedConfigSettings (medium).** Add a neutral must-keep sentence: "The dashboard's existing queries and mutations keep succeeding, including reading the configuration with its secrets filled in." Alternatively, accept the risk and point solvers to dashboard/ usage. I prefer the sentence.

Recommended, not blocking: soften the T2 sentence (§3). Add one security case each for `null` origin and bare `dashboard.local.nhost.run`, and a run-service fixture with `runServiceConfigs(resolve:true)`.
