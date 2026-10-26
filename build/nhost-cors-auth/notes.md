# nhost-cors-auth — build notes

- Start (UTC): 2026-10-17T06:25:25Z
- End (UTC): 2026-10-17T06:48:58Z
- Pattern A, track mined. Pinned da4e00011f77 (verified direct parent of fix e407511627d2).

## Levers (one line each)
- T1 (A, producer/loader): stored secret values must be withheld where the loader fills the store, so the listing and resolved-config queries are both covered — cli/cmd/configserver/local.go:94-105. Reason to dismiss: the report reads as a cross-origin problem; hiding values in the listing resolver looks enough.
- T2 (A, save path): with values withheld, secret edits must keep stored values for untouched entries — local.go:164-180. Reason to dismiss: looks like plain persistence code unrelated to CORS. Tested functionally.
- T3 (input shapes): lookalike host ending, other *.local.nhost.run host, multi-label subdomain, localhost dev server; preflight and response — configserver.go:170. Reason to dismiss: a looser origin checker already exists in the same process to copy.
- T4 (second API on same engine): logs GraphQL under the same rule — configserver.go:174. Reason to dismiss: the report's example names the configuration API.
- T5 (coupled): dashboard origins keep CORS; shared CORS helper keeps its defaults for auth/storage.

## Verified
- Flaw reproduces through the real entry point (configserver.Command() in-process on loopback): ACAO "*" for every origin on both APIs; real secret values in appSecrets/appsSecrets/config(resolve:true)/configRawJSON(resolve:true).
- Local runs in the task image: nop 0/8 security, 39/39 functional; oracle 1.0; all 11 checks/ patches behave as declared.
- Project tests: logsapi (helpers) and oapi middleware CORS tests pass at pinned and with the oracle; configserver + dockercompose tests pass with the oracle (oracle carries upstream's local_test.go update).
- No regression tests of the fix exist at the pinned commit.

## Not verified / not tested
- App-ID randomisation (published) is in the oracle but not tested: testing it would require naming the flag/env in the instruction.
- The shared CORS lib's new predicate option is not required; any origin-policy implementation passes (alt_rscors.patch proves rs/cors works).
- Out of scope (not built): logs websocket origin checker accepts localhost and multi-label hosts (cli/cmd/configserver/logsapi/router.go:27-44); not tested either way and its project test was excluded from grading to stay neutral.
- Out of scope: secrets inserted/updated through the API are held in memory and returned by later queries (upstream fix does the same); tests check only values that were on disk at start. The instruction now scopes the rule to values read from the secrets file (FAIRNESS item 1, option a); option b was not taken because mimir caches the resolved config computed with the new real value inside updateSecret, out of the plugin's reach, so re-masking would need changes far beyond the published fix and would invalidate alt_rscors/hardening/blind.
- Out of scope: dashboard compose env embeds the Hasura admin secret (cli/dockercompose/compose.go:344).
- services/storage does not build with CGO_ENABLED=0 (vips); unrelated, pre-existing.

## Fairness revision (2026-10-17)
- Instruction: secret rule scoped to values read from the secrets file; test constraint now "Do not weaken or delete tests; tests asserting the old insecure behaviour may be updated" (oracle updates local_test.go); no-Origin clients keep working "apart from the secret-value rule"; added must-keep sentence that the dashboard's queries/mutations keep succeeding incl. reading the configuration with secrets filled in; T2 sentence softened; dropped "(configuration, secrets or logs)" and "whatever query is used".
- Added security tests TestSecNullOrigin and TestSecBareDashboardDomainOrigin (T3).
- Not done (recommended only): run-service fixture with runServiceConfigs(resolve:true).
