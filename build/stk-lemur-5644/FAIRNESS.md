# Fairness review — stk-lemur-5644

Read: `tasks/stk-lemur-5644/instruction.md`, every file in `tasks/stk-lemur-5644/tests/`,
`solution/fix.patch`, `build/stk-lemur-5644/manifest.json`, `notes.md` and `checks/*.patch`
(including `blind.patch`, `pass-*`, `miss_*`, `sf-*`, `ff-*`, `upstream_fix.patch`). No Docker,
trial or gate was run by this review.

**Covering text.**
**P** = the Required property: “A directory address must be checked when it arrives in a user
request, before it is stored or fetched by the backend: it must be an HTTPS URL whose host is on
the configured allowlist of permitted directory hosts. A request carrying any other directory
address must fail with a client error and have no effect, leaving stored state unchanged.”
**K** = “Everything that works today keeps working.”
**G** = “Fix the problem and its close variants.” / “Keep legitimate use working.”

## 1. Per-test fairness

| Test (file::name) | What it asserts | Instruction sentence / expert knowledge that makes it fair | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/test_authority_update_options.py::test_update_refuses_disallowed_directory_address[http://169.254.169.254/…] | update PUT answers ≥400 and stored options are byte-identical | P: “A request carrying any other directory address must fail with a client error and have no effect” (not HTTPS) | no — a view, schema, service or handler guard all refuse and the test accepts any ≥400 | low |
| …::test_update_refuses_disallowed_directory_address[https://169.254.169.254/…] | same, host is an unlisted IP literal | P: “host is on the configured allowlist of permitted directory hosts” | no | low |
| …::test_update_refuses_disallowed_directory_address[http://acme-v02.api.letsencrypt.org/directory] | same, allowlisted host but wrong scheme | P: “it must be an HTTPS URL” | no | low |
| …::test_update_refuses_every_disallowed_entry[good+http] | every entry of the submitted list is judged; refusal and no store | P over every address in the request; G: “close variants” | no — a per-entry loop, not first-match | low |
| …::test_update_refuses_every_disallowed_entry[http+good] | a leading disallowed entry is refused | P + G | no | low |
| …::test_update_refuses_every_disallowed_entry[email + https link-local] | a disallowed entry among legitimate ones is refused | P + G | no | low |
| security/test_authority_options_writer.py::test_options_writer_refuses_disallowed_directory[http, https] | bulk options PUT answers ≥400, options unchanged | P (“when it arrives in a user request, before it is stored”) — the bulk PUT is such a request; the general property is read literally, no route name required | no — view-layer (`pass-alt-view-guards`) and writer-layer (reference) guards both pass | low |
| …::test_options_writer_refuses_disallowed_entry_among_others | one bad option entry in the bulk payload is refused | P + G | no | low |
| security/test_acme_directory_check.py::test_supplied_directory_is_not_contacted_http | no connection to the supplied plain-HTTP address, ≥400, options unchanged | P: “…before it is … fetched by the backend” and the refusal contract | no — route/schema guard or handler guard before the client is built | low |
| …::test_supplied_directory_is_not_contacted_https | same for an HTTPS loopback address not on the configured allowlist | P: host allowlist, not scheme or IP class alone | no | low |
| functional/test_authority_updates.py::test_allowlisted_directory_can_be_saved | the allowlisted HTTPS entry list is stored verbatim and the route answers 200 | K; P permits it (“HTTPS URL whose host is on the … allowlist”) | no | low |
| …::test_options_without_plugin_names_are_saved | `[{"updated": "bar"}]` is stored and 200 | K; no directory address arrives, so P does not apply | no — only a wrong check that indexes `entry["name"]` fails | low |
| …::test_non_acme_authority_options_are_saved | ordinary non-ACME option entries are stored | K; no directory address | no | low |
| …::test_allowlisted_directory_can_be_saved_by_options_writer | the bulk route stores an allowlisted HTTPS entry | K; P permits it | no | low |
| …::test_internal_option_writes_keep_working | the internal writer still stores a non-directory list | K (“everything that works today”); P is scoped to addresses arriving in a user request | no | low |
| functional/test_legacy_directory.py::test_stored_directory_is_still_contacted | a row stored before the change is still contacted (probe carries `acmeUrl: ""`) | K; P judges a value on arrival in a request, not a value already in place | no — an over-fix that re-validates stored values at fetch fails, but that contradicts K; an explicit empty field carries no address and today means the stored/default directory | medium |
| …::test_configured_directory_is_still_contacted | the operator’s configured fallback is still contacted (empty override) | K; the configured default is not an address arriving in the request | no — same over-fix caveat; a guard that treats an explicit empty `acmeUrl` as an address would also fail, but that is over-strict against K | medium |
| …::test_allowed_override_is_still_contacted | an HTTPS override on a host the test configures into `ACME_DIRECTORY_HOST_ALLOWLIST` is contacted | P permits it (HTTPS + configured allowlist); K | no — a hardcoded allowlist would fail, which is the point; the existing validator reads config at call time | low |
| …::test_account_write_back_keeps_legacy_directory | the internal write-back keeps the legacy stored URL and adds the account keys | K; the write-back is not a user request, so P does not re-judge it | no — a view-layer guard or a changed-only writer passes; an unconditional service-level re-validation of unchanged stored values fails, but that contradicts K | medium |
| project `lemur.tests.test_authorities` (incl. `test_authorities_put_update_options[token0-100-200]`, which PUTs `[{"updated": "bar"}]` and expects 200) | the product’s own authority behaviour is intact | K + G; standard expert knowledge: a fix must not break the project’s tests | no | low |
| project `lemur.plugins.lemur_acme.tests.test_acme_dns` (incl. the `setup_acme_client*` tests) | the handler still uses the configured directory (acme-v01, not on the default allowlist) and has no regression | K; standard expert knowledge | no — only an over-fix at the fetch site fails (`ff-validate-at-sink`) | low |
| project `lemur.plugins.lemur_acme.tests.test_acme_handler` | handler behaviour and registration paths are intact | K; standard expert knowledge | no | low |

## 2. Leniency (quality, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught by |
|---|---|---|
| P (update route), T1 | Fix only the creation path / leave the update route as-is | `test_update_refuses_*` — `miss_c1.patch` 6 security fails; the published `upstream_fix.patch` does close this route |
| P (bulk route), T4, T6 | Assume the lower-level writer is internal and fix only the reported PUT | `test_options_writer_*` — `miss_c2.patch` 3 security fails |
| P (probe), T7 | Fix both write routes and treat the request-supplied address as stored configuration | `test_supplied_directory_is_not_contacted_*` — `miss_c3.patch` 2 security fails |
| T2 | Validate only the first `acme_url` entry | `test_update_refuses_every_disallowed_entry[entries0]` — `sf-first-acme-entry-only.patch` |
| T3 | Index `entry["name"]` or reject unnamed entries | `test_options_without_plugin_names_are_saved` + project `test_authorities_put_update_options` — `ff-keyerror-shape.patch` |
| T5 | Validate the effective stored/configured address at the fetch | `test_stored/configured/write_back` + project `test_acme_dns`/`test_acme_handler` setup tests — `ff-validate-at-sink.patch` (7 functional fails) |
| ordering | Check after the options were persisted | `sf-check-after-store.patch` (6 security fails) |
| refusal form | Refuse all option changes / the probe | `ff-refuse-all.patch` (10 functional fails) |
| P (all) | Return 200 while silently dropping the bad entry | the security tests’ `status_code >= 400` |
| P (all) | A private/loopback/link-local IP denylist (or “block the reported 169.254.169.254”) instead of the host allowlist, with the allowlist consulted only for such hosts: `https AND (not a private IP OR allowlisted)` | **not caught for public hosts** — the only refused hosts are the two IP literals and the wrong *scheme* case; F8 forces the allowlist to be honoured for the loopback override, so this rule passes every test yet accepts `https://acme.example.net/directory` (a public host off the allowlist). A pure denylist that rejects 127.0.0.1 outright is caught by F8 |
| P (all) | A host-matching bug that accepts lookalikes (`acme-v02.api.letsencrypt.org.evil.example`, suffix/prefix match) or parser differentials (`https://acme-v02.api.letsencrypt.org@169.254.169.254/`, backslash/percent forms) | **not caught** — no test uses a lookalike or userinfo/escape form |
| refusal contract | Refuse the address but still apply `owner`/`description`/`active`/`roles` | **not caught** — the security tests compare only `options`, not the whole row |
| P (all) | Accept a non-string `acme_url` value, or an options payload shaped as a JSON object rather than a list | **not caught** — all fixtures use string values in lists |
| exact error class | Return 500 for a refusal although P says “client error” | **not caught** (tests accept any ≥400; the reference itself returns 500) |

## 3. Hints (quality, non-blocking)

No file, function, fix-approach, trap list or flaw count is named. Two sentences are worth quoting:
- “An authority that issues certificates through the ACME protocol stores a directory address in
  its plugin options, and Lemur’s backend fetches that address when the authority is used.” This is
  product context for the property (the value and why it matters), not a fix site; no rewording is
  needed for fairness.
- “A user who has a role on an existing ACME authority can send `PUT /api/1/authorities/<id>` with a
  body such as …” and the literal `acme_url` payload: the reported request, needed for a realistic
  report; it points at the exploit, not at the fix. Keep.
- “Do not special-case the example.” is a standard constraint, not a trap pointer.

## 3a. Surface descriptions — Required: generalize

**None.** The instruction names the protected data (“a directory address”, “its plugin options”),
the reported request and the general property; it does not describe the bulk options route, the
connectivity probe, any sibling writer, stage or format. No general word in it is also the name of
one stage or entry point.

## 4. Realism

T1–T5 are real, unmodified upstream code and fixtures: the update path stores options verbatim; the
lower-level writer has no check and its in-tree caller re-saves trusted rows; the options list is
free-form, so a name-less entry is real; stored and configured addresses are documented in-tree as
trusted. T6 (`PUT /authorities/<id>/options`) and T7 (`POST /authorities/<id>/acme-directory`) are
injected resources, but they call the real service writer and the real `AcmeHandler` and are
reachable through real HTTP entry points; both are maintainer-plausible, not planted. Real routes
the published fix left open are in scope by definition.

## Stacking checks

Concepts: **C1** = T1/T2/T3 (authority update); **C2** = T4/T6 (lower-level writer and its bulk
route); **C3** = T7 (request-supplied address at the probe). T5 is the must-keep-working value
spanning C2/C3, not a concept.

| Check | Concept | Finding | Gate a |
|---|---|---|---|
| S1 coupled traps | C1 | Must-keep values: the allowlisted HTTPS directory, the name-less list, the non-ACME list. Covered by K (+G); P permits the allowlisted value and does not reach payloads with no directory address. No security rule read literally forbids them. | pass |
| S1 coupled traps | C2 | Must-keep values: the allowlisted bulk write and the internal writer. Covered by K; P is scoped to addresses arriving in a user request, so re-saving a stored value internally is outside it. No contradiction. | pass |
| S1 coupled traps | C3 | Must-keep values: the stored row, the configured default, the allowlisted override. Covered by K; the first two carry no arriving address and the third is HTTPS on the configured allowlist, which P permits. No contradiction. | pass |
| S2 shape traps | C1 | Refused shapes: non-HTTPS scheme, HTTPS off-allowlist host, and both inside a multi-entry list. The stated legitimate set is HTTPS + allowlisted host; unnamed entries carry no address. Every refused shape is outside the legitimate set. | pass |
| S2 shape traps | C2 | The same shapes through the bulk route; the legitimate set is the same (allowlisted HTTPS entry, unnamed entries). Nothing refused lies inside it. | pass |
| S2 shape traps | C3 | Refused shapes: plain HTTP and HTTPS on a loopback host not on the configured allowlist; the legitimate override (HTTPS + allowlisted, with the test configuring `127.0.0.1`) is accepted. | pass |
| S3 fixtures and harness | C1 | Factory-created authorities, the product’s admin token and the real update route; state read back from the DB. View (`pass-alt-view-guards`) and service (reference) guards both pass. All states are legitimate. | pass |
| S3 fixtures and harness | C2 | The bulk route calls the real writer; the internal call drives the real service function. A guard in the route or the writer passes; all states are legitimate. | pass |
| S3 fixtures and harness | C3 | The probe drives the real handler through the real route; the test’s allowlist configuration is legitimate. A guard at the route, the schema or the merge point passes. | pass |
| S4 concept independence | C1 | `miss_c1` (C2+C3 correct) → 6 security fails, 0 functional; a correct C1 fix passes whatever C2/C3 do. Not masking: all 11 security tests fail on the pinned tree through their own routes (nop). | pass |
| S4 concept independence | C2 | `miss_c2` (C1+C3 correct) → 3 security fails, 0 functional; the writer tests fail through their own route on the pinned tree. | pass |
| S4 concept independence | C3 | `miss_c3` (C1+C2 correct) → 2 security fails, 0 functional; the probe tests fail through their own route on the pinned tree. | pass |
| S5 history | C1 | The advisory’s own route; `checks/upstream_fix.patch` (the published first fix; no `upstream_first_fix.patch` exists for this H4 build) closes it and satisfies P here. | pass |
| S5 history | C2 | `upstream_fix.patch` leaves the bulk write storing a request-supplied off-allowlist address, violating P read literally, not merely differing from the reference. | pass |
| S5 history | C3 | The same patch leaves a request-supplied override fetched unchecked, violating P read literally. | pass |
| S6 contracts | C1 | Fields are the product’s own (`options` entries with name/value); the protected object is named in product terms; the allowlist is the existing configured one. No guessed name. | pass |
| S6 contracts | C2 | The bulk route/schema are visible in the repo and call the product’s own writer; the refusal contract is stated. No guessed name. | pass |
| S6 contracts | C3 | The probe body field is the injected, visible schema field; the override is handled by the real handler; the refusal contract is stated. No fail-open authority lookup. | pass |
| S7 decisive tests | C1 | No `trial_summary.md`. `trial_detail_deepseek.json` records deepseek 0/3 and `runs_mimo.log` mimo 0/1, all reward 0.0; no per-test breakdown is present in `build/`. `blind.patch` scores 1.0, so the suite is satisfiable. Needs the human check below. | see note |
| S7 decisive tests | C2 | Same evidence; the most likely single decider, if any, is `functional/test_legacy_directory.py::test_account_write_back_keeps_legacy_directory`. | see note |
| S7 decisive tests | C3 | Same evidence; the second candidate decider is `test_configured_directory_is_still_contacted` / `test_stored_directory_is_still_contacted`. | see note |

## Verdict

**Gate a: READY.** Each security assertion is P read literally over the route it drives: the update
PUT, the bulk options PUT and the probe POST all carry a directory address in a user request and
must be checked before storage or fetch, with an error and unchanged options. Each keep-working
value is covered by K (and G): stored, configured and internally re-saved values are outside P’s
arrival scope, and name-less/non-ACME payloads carry no address. A correct fix passes at the view,
schema, service-writer or handler layer: the reference, `pass-alt-view-guards`, `pass-hardening`
and the fresh-agent `blind.patch` all score 1.0. The only “maybe” shapes are over-strict guards
treating an explicit empty `acmeUrl` as an address or re-validating unchanged stored values in a
service writer; both contradict K, so they are wrong fixes. No gate-a mechanism fires.

**Required: generalize → none.**

**Quality to tighten:** (1) add an HTTPS public host not on the allowlist on all three routes,
which catches an IP-denylist rule that allows public hosts; (2) add lookalike/parser-differential
hosts (`…letsencrypt.org.evil.example`, `…letsencrypt.org@169.254.169.254/`); (3) compare the whole
authority row, not only `options`, for “have no effect”; (4) do not tighten the accepted error to
4xx without also changing the reference, which returns 500 while P says “client error”.

**Human review:** confirm which test decided deepseek 0/3 (`trial_detail_deepseek.json`) and mimo
0/1 (`runs_mimo.log`) — no `trial_summary.md` or per-test breakdown is in `build/`; the likely
single decider, re-checked here and found fair, is
`functional/test_legacy_directory.py::test_account_write_back_keeps_legacy_directory`.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
