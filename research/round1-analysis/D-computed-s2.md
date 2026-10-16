# D. Computed S2: named-location disparity (S2a) and data producer off the check's path (S2b)

2026-10-16. Built offline (no network, no Docker, no model runs, standard library only).
Both signals are in the index as 0-point labels; `weights.json` `symptom_fix_disparity.validated`
is `false`.

## Summary

- **Built.** S2a and S2b are computed from the cached OSV dumps and patches. They are stored with
  no schema change, and `score_detail` shows them as labels. After `remetrics`, `resignal` and
  `classify`, the ranking of the 1,462 candidates is **identical** to before. No score, status or
  reject reason changed, so no ties moved either. Backup: `sourcer/index/candidates.before-s2.sqlite`.
- **Pool firing rates.**

  | Signal | Candidates | Share of 1,462 |
  |---|---|---|
  | S2a `disparity` | 276 | 18.9% |
  | S2a `partial` | 449 | 30.7% |
  | S2a `on_named` | 445 | 30.4% |
  | S2a `unknown` | 292 | 20.0% |
  | S2b, any role pair | 164 | 11.2% (21.8% of the fixes that touch 2+ source files) |
  | S2b strict | 80 | 5.5% |
  | S2b strict + other directory | 69 | 4.7% |

- **S2a does not measure what we want.** It was checked against hand judgements on 20 single-flaw
  items: 7 mined bases, Hadi's MCP task, 10 stacking items with a cached fix, and 2 hard stacking
  items computed on their part of the task fix. Four items have the cause in another place than
  the symptom.
  - S2a `disparity` caught 0 of the 4 using the index values (precision 0/3), or 1 of 4 using
    each task's own fix (precision 1/5).
  - The reason: advisories are written by whoever found the root cause, so they usually **name
    the cause**. S2a therefore measures how precise the advisory is, not how far the symptom is
    from the cause.
  - Our instructions are symptom-only by design and name nothing, so S2a cannot be computed from
    them.
  - `on_named` leans towards "easy": 7 of its 8 items were not S2-type, against a base rate of
    15 of 20. Its median score is already 3 against 8, so the existing LOW signals mostly capture
    this.
- **S2b fires where it should, but n is tiny.**
  - It fires (strict, other package, no call between the two sites in the diff) on Hadi's
    GHSA-6qxp-vccf-f47h. That advisory is in the index (candidate, score 11, tied with 95 others at
    ranks 133-228). The roles
    found are check = `fetchToken` / `discardIfIssuerMismatch` in `packages/client/src/client/auth.ts`,
    and producer = `OAuthTokensSchema` / `OAuthClientInformationSchema` in `packages/core/src/auth.ts`.
  - It fires loose on rclone. There, the check's file calls the producer in the diff, which is
    the "check calls producer" case: DeepSeek solved it, consistent with Hadi's narrower
    hypothesis.
  - It gives one false positive (py-shiny, loose) and misses no item judged to have the split.
  - That is 2 true positives, 1 false positive and 0 misses out of n = 22, with only 1 item of
    the exact Hadi shape.
- **Proposed points: all stay 0** (reasons in section 6). Use the S2b-strict list now as the
  source of hosts for calibrating the "data producer off the check's path" trap. Points for S2b
  should be set only after the `siblings` stage fills `check_calls_producer` and that calibration
  has a second host.

## 1. What was built

| Part | Where | Stored in |
|---|---|---|
| Named locations in the advisory: functions and methods (`fetchToken`, `foo.bar()`, `Class#m`, `A::b`, CamelCase identifiers), files (paths and bare `x.rs` with a source extension, GitHub `blob/` links), HTTP endpoints (`GET /x`, backticked `/api/...`), CLI commands (backticked `prog sub ...`) | `osv_sourcer.named_locations()`, called from `text_signals()` (`parse` and `resignal`) | `adv_signals.named` = `{func, file, endpoint, command}`, 15 per kind at most |
| Where the fix lands: changed source files, function names from hunk headers, and the enclosing definition of every changed code line (the nearest definition line in the hunk, else the hunk header) | `patchmetrics.location_metrics()` inside `parse_patch()` (`diffs` and `remetrics`) | commit `shape`: `changed_files`, `hunk_funcs`, `units` = `[file, name, role, basis]`, `n_units` |
| S2b role per unit, and the pair test | `patchmetrics.site_role()` and `location_metrics()` | commit `shape.s2b`: `fires`, `strict`, `diff_dir`, `linked_in_diff`, `check_files`, `producer_files`, `check_names`, `producer_names`, `check_calls_producer` (**null placeholder** for the `siblings` stage) |
| S2a state | `osv_sourcer.s2a_signal()` (in `compute_signals`, as the transient `_s2a`) | `score_detail` label only |
| Weights | `weights.json` `symptom_fix_disparity`: `s2a_disparity`, `s2a_partial`, `s2a_on_named`, `s2a_unknown`, `s2b_check_and_producer_in_other_file`, `s2b_bonus_other_directory`, `s2b_bonus_strict_roles`, `s2b_check_does_not_call_producer`, all 0, `validated: false`, S2b credited to Hadi 2026-10-15 | version stays 3 |
| Counts | `stats` prints `pool_s2_computed` | |

**How S2a decides.** Advisory text inside code blocks is ignored, and so are the PoC,
references, credits and workaround sections. Named items equal to the package or repository name
are dropped, as are commands whose first word is not the program.

| State | Rule |
|---|---|
| `unknown` | nothing is named |
| `disparity` | the fix touches none of the named locations. "Touched" is lenient, which makes `disparity` conservative: a named function or class counts as touched if it equals a hunk-header name, a changed line's enclosing definition, or a changed file's basename. A named file counts if its path suffix or basename matches. An endpoint or command counts if one of its segments names a changed definition, file or directory. |
| `on_named` | every changed site lies in a named function, a named class, or a named file |
| `partial` | the fix touches some named locations and also changes code elsewhere |

`partial` is a fourth state, added because Hadi's case is exactly "lands on the named check and
also somewhere else", and a −1 for `on_named` must not fire there.

**How S2b decides.** The role comes from the definition's own name first:
1. Its leading verb: parse, load, decode, serialize, new, from, migrate for a producer; check,
   validate, verify, auth, guard for a check.
2. Then its head noun: schema, serializer, parser, loader, decoder, codec, model(s), types,
   constructor, migration, store for a producer; auth, permission, policy, guard, middleware,
   validator, verifier, check, access, acl, token for a check.
3. Then any word, but only when the words point one way.
4. Only if the name says nothing: the file name, then the three nearest directories.

`__init__`, `constructor`, `__construct` and `New*` count as producers.

| Flag | Meaning |
|---|---|
| `fires` | there is a check unit in file A and a producer unit in a different file B |
| `diff_dir` | some such pair is in different directories |
| `strict` | some pair has both roles taken from the name, the producer is not a bare constructor, and the two files are not linked in the diff: neither file's added lines call a definition the fix changed in the other |
| `linked_in_diff` | every pair is linked in the diff |

The diff-level link is only a hint. "The check does not reach the producer" needs the vulnerable
tree and is left to the `siblings` stage.

## 2. Ground truth: hand judgements vs computed values

Hand judgements come from `instruction.md` (where the symptom shows) and `solution/fix.patch`
(where the fix lands), and for stacking items from the advisory and the upstream diff.

- **H-sym**: is the cause in another function, file or layer than where the symptom shows?
- **H-split**: does the fix need a check and a data producer in different files?

| Item | H-sym | S2a (index, upstream commit) | S2a (task fix) | H-split | S2b | Note |
|---|---|---|---|---|---|---|
| russh | no | on_named | on_named | no | – | fix at negotiation and at the read path; the instruction requires the handshake to refuse |
| webob | no | on_named | on_named | no | – | fix at each redirect API plus a shared helper |
| jackson-databind | no | partial | **disparity** | no | – | the advisory names the 3.x location (`BeanDeserializer`); the 2.x task fix is in `ExternalTypeHandler` (backport artefact) |
| async-http-client | no | **disparity** | **disparity** | no | – | the advisory names caller API (`setHeader`, `addHeader`, `addCookie`); the fix is in request building, where the header is written |
| rclone | partly | partial | partial | **yes** (check calls producer) | loose, `linked_in_diff` | the secret producer is the proxy (`proxy.go`), the check is in `s3/server.go`; roles are labelled the other way round, but the pair is found |
| hickory-dns | **yes** | partial | **disparity** | no | – | symptom at `Resolver::lookup`; fix in the caching client and error layer |
| py-shiny | no | n/a (pending, no diff) | **disparity** | no | **loose (FP)** | named only `ui.input_file`; S2b pairs a new validator with the restore parser |
| MCP SDK (Hadi) | **yes** | partial | partial | **yes** (off-path) | **strict, other dir** | the producer is the zod schemas in `packages/core/src/auth.ts` |
| asyncssh pktsize (GHSA-rw4j) | **yes** | n/a (pending) | on_named (its files in the task fix) | no | – | the advisory names `connection.py` and `channel.py`, so "the fix is named" |
| argo templateDefaults (GHSA-3775) | **yes** | n/a (deferred) | partial (its files in the task fix) | no | – | the advisory names `setExecWorkflow`, where the gate is |
| asyncssh scp (GHSA-2wxc) | no | partial | | no | – | |
| cloudreve GHSA-49h3 | no | partial | | no | – | |
| cloudreve GHSA-8r7f | no | on_named | | no | – | |
| cloudreve GHSA-g9j2 | no | on_named | | no | – | |
| cloudreve GHSA-w8x7 | no | on_named | | no | – | |
| cloudreve GHSA-c3jm | no | on_named | | no | – | |
| filament GHSA-7m6h | no | unknown | | no | – | |
| filament GHSA-r3j6 | no | unknown | | no (same file) | – | |
| filament GHSA-xwpv | no | **disparity** | | no | – | names the user-model hook `canAccessPanel()`; the fix is in `Login::authenticate` |
| trigger-dev GHSA-59h8 | no | on_named | | no | – | |
| rclone-sib | partly | (as rclone) | partial | yes | strict | the strict pair is `ftp.go` `CheckPasswd` vs `s3/server.go` `parseAccessKeyID`: a pair across injected siblings, so spurious |
| jackson-databind-sib, jackson-sib7, russh-sib | no | (as base) | partial / partial / on_named | no | – | their difficulty is undisclosed siblings (S8), not S2 |

**S2a, n = 20 single-flaw items (sibling tasks excluded: same advisory as their base). H-sym is
yes for 4 (hickory, MCP, asyncssh pktsize, argo) and partly for rclone.**

| Rule | Precision | Recall |
|---|---|---|
| S2a `disparity`, index value (task fix where the index has none) | 0/3 (async-http-client, py-shiny, filament xwpv) | 0/4 |
| S2a `disparity`, task-fix value | 1/5 | 1/4 (hickory only) |
| S2a `on_named` as an "easy" marker | 7/8 not S2-type (base rate 15/20 = 75%) | – |

Why S2a misses:
1. **Advisories name the cause.** asyncssh pktsize names `connection.py`. argo names
   `setExecWorkflow`. MCP names `fetchToken` and `OAuthTokensSchema`.
2. **Disparity fires on incidental names**: caller APIs, a framework hook, an API mentioned in
   passing.
3. **Backports**: the advisory names the main-line location, and the older line's fix is
   elsewhere.

**S2b, n = 22.** The 20 items above plus rclone-sib and MCP judged at task level. Sibling and
stacking task-level S2b values are not counted, because a combined patch of several flaws pairs
sites from different flaws: on the combined fixes it fires for argo, asyncssh, cloudreve,
filament and stigmem, and none of those firings is real. H-split is yes for MCP, rclone and
rclone-sib.

| Rule | Hits and false positives | Recall |
|---|---|---|
| any S2b | MCP, rclone, rclone-sib, plus FP py-shiny | 3/3 |
| strict | MCP and rclone-sib (the rclone-sib pair is the spurious cross-sibling one) | MCP only, among Hadi-shape items |
| the off-path shape (Hadi), n = 1 | MCP: strict, not linked | 1/1 |
| on-path rclone | correctly not strict, `linked_in_diff` = 1 | – |

All four counts fit, but with one positive of the exact shape this cannot support a weight.

## 3. Hadi's advisory GHSA-6qxp-vccf-f47h

- It is in the index: entry 9213, candidate, fix `edd12e28`, score 11 under v3. It ranks 133-228
  of 1,462 (96 candidates share score 11).
- **S2b fires**, strict, in another directory, not linked in the diff.
  - Check sites: `packages/client/src/client/auth.ts` (`fetchToken`, `executeTokenRequest`,
    `discardIfIssuerMismatch`), `authErrors.ts`, `authExtensions.ts` (the providers),
    `crossAppAccess.ts`, `server-legacy/.../proxyProvider.ts`.
  - Producer sites: `packages/core/src/auth.ts` (`OAuthTokensSchema`,
    `OAuthClientInformationSchema`), plus the provider constructors in `authExtensions.ts`.
- S2a is `partial`: the advisory names `fetchToken`, `auth()` and the bundled providers, which
  the fix touches, and the fix also changes code elsewhere.
- Hadi's task `fix.patch`, a subset of the upstream fix, gives the same result: S2b strict across
  directories, S2a `partial` from both the advisory and the instruction.

## 4. Relation to round-1 outcomes

Source: `A-task-outcomes.tsv` (offline, no-lookup runs; `diff_composite` is the difficulty
composite). Descriptive only.

| Task | DeepSeek | MiMo | Composite | S2a (task fix) | S2b |
|---|---|---|---|---|---|
| async-http-client | 1/2 solved, defect | 3/3, defect | 0.660 | disparity | – |
| jackson-databind | 2/3, over-broad defect | 3/3 | 0.566 | disparity | – |
| webob | 2/2 | 1/2, regression | 0.458 | on_named | – |
| rclone | 1/1, fail-open defect | 1/1 | 0.420 | partial | loose (linked) |
| hickory-dns | 1/1 | 1/1 | 0.375 | disparity | – |
| russh | 1/1 | 2/2 | 0.361 | on_named | – |
| py-shiny | 10/10 | 1/1 | 0.188 | disparity | loose |
| jackson-databind-sib (only failure) | **0/6** | 1/2 | 0.819 | partial | – |
| MCP SDK (Hadi) | **0/3** | not run | – | partial | **strict** |

- **S2a does not separate harder tasks.** Over the 7 mined bases, `disparity` has a mean
  composite of 0.447 (n = 4) against 0.413 (n = 3) for the rest. The index value flags only
  async-http-client, which is the hardest mined base, but that is n = 1 and a false positive by
  hand judgement.
- **S2b.** The one task in our data with S2b strict, MCP, is a DeepSeek 0/3. The loose,
  linked-in-diff rclone was solved. Its DeepSeek defect is still telling: it fell back to the
  access key when the proxy (the producer) returned no secret. py-shiny (loose, false positive)
  is the easiest task.
- **The only round-1 failure has neither signal.** jackson-databind-sib is hard because of S8
  (undisclosed sibling paths). The stacking tasks with real defects (argo, asyncssh) are S2-type
  by hand, but their items are outside the recency window or not fetched, and S2a computed on
  their part of the fix does not flag them.

## 5. Pool statistics

- **S2a** (n = 1,462): disparity 276 (18.9%), partial 449 (30.7%), on_named 445 (30.4%),
  unknown 292 (20.0%).
  - Advisories name at least one function in 1,090 cases, a file in 662, an endpoint in 335 and
    a command in 159.
  - S2a `disparity` overlaps the old wording proxy `c_cause_layer_hint` in only 73 of its 276.
  - Median score is 7 vs 7 with and without `disparity`, and 3 vs 8 for `on_named` vs the rest.
- **S2b**: fires on 164 (11.2%); strict 80 (5.5%); strict with another directory 69 (4.7%);
  linked in the diff 30.
  - It fires on 21.8% of the 753 fixes that touch 2+ source files.
  - Per language (fires / strict / n): Go 57/27/387, Python 35/18/263, TypeScript 34/20/201,
    Java 14/6/188, PHP 10/1/192, JavaScript 2/1/110, Rust 8/7/71.
  - Java, PHP and Python fire less because git's hunk header names the class, not the indented
    method, unless the method's definition line is inside the hunk.
  - S2b and S2a `disparity` together: 19. Median score 9 vs 6 with and without S2b (it rides on
    multi-file fixes); 28 of the top 150.

**Top 20 candidates where S2b fires (by current score):**

| # | Pool rank | Advisory | Repo | Lang | Score | Strict | Other dir | Check site(s) | Producer site(s) | S2a |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 4 | GHSA-38c3-wv3c-v3xj | acacode/swagger-typescript-api | TypeScript | 15 | yes | yes | remote-schema-fetch.ts `RemoteSchemaFetchPolicy` | resolved-swagger-schema.ts `getRemoteRequestHeaders`; `isExplicitSpecUrl`; `ResolvedSwaggerSchema` +1 | partial |
| 2 | 5 | GHSA-392p-2q2v-4372 | better-auth/better-auth | TypeScript | 15 | yes | no | revoke.ts `revokeRefreshToken`; token.ts `invalidateRefreshFamily`; token.ts `createRefreshToken` +1 | schema.ts `schema` | partial |
| 3 | 10 | GHSA-3wr7-993q-jrff | corazawaf/coraza | Go | 15 | yes | yes | magefile_adr.go `checkADR` | multipart.go `percentDecodeLenient`; `fromHex`; transaction.go `NewTransactionVariables` +2 | partial |
| 4 | 16 | GHSA-8cfw-pcwh-v63w | wintercms/winter | PHP | 15 | no | yes | SecurityPolicy.php `SecurityPolicy`; `checkSecurity`; `checkMethodAllowed` +28 | GetAttrNode.php `__construct`; SecurityPolicy.php `__construct`; SafeCollection.php `__construct` +1 | partial |
| 5 | 17 | GHSA-2gpf-2492-q9jh | mervinpraison/praisonai | Python | 14 | yes | yes | url_safety.py `validate_searxng_url`; auth_service.py; agent_invoke.py `_call_auth_disabled` +2 | agent_invoke.py `_bind_host_from_request`; core.py `_load_yaml_file`; sandlock.py `__init__` | partial |
| 6 | 18 | GHSA-2jgc-f764-c5r2 | mervinpraison/praisonai | Python | 14 | no | yes | server.py `_authorise_request`; serve.py `_install_api_key_middleware`; `APIKeyMiddleware` +3 | file_memory.py `__init__`; server.py `__init__`; http_stream.py `__init__` | partial |
| 7 | 21 | GHSA-5wx6-mg75-v57r | pnpm/pnpm | TypeScript | 14 | yes | yes | approveBuilds.ts `handler`; getAutomaticallyIgnoredBuilds.ts; index.ts `isBuildExplicitlyDisallowed` +28 | index.ts `allowBuildKeyFromIgnoredBuild`; config.ts `AllowBuild`; `AllowBuildContext` +5 | partial |
| 8 | 29 | GHSA-6r3q-mjv7-xr8m | corazawaf/coraza | Go | 14 | no | yes | transaction.go `checkArgumentLimit` | waf.go `newTransaction`; url.go `ParseQuery`; `doParseQuery` +2 | partial |
| 9 | 30 | GHSA-prj9-97mp-mwh2 | olivetin/olivetin | Go | 14 | yes | yes | sanitize.go `validateReservedActionArgumentNames`; `validateReservedArgumentNames` | executor.go `stepParseArgs` | partial |
| 10 | 35 | GHSA-6qvr-wjmv-v8mm | koel/koel | PHP | 14 | yes | yes | HasAudioContentType.php `validate`; SafeUrl.php `validate`; SafeHttp.php `pinAndValidateMiddleware` | SafeHttp.php `__construct`; RadioStationStoreRequest.php `rules`; HasAudioContentType.php `__construct` +5 | partial |
| 11 | 36 | GHSA-95jh-7r58-xmxw | wwbn/avideo | PHP | 14 | no | no | registerWebhook.json.php; webhook.php | AuthorizeNet.php `parseWebhookRequest` | partial |
| 12 | 38 | GHSA-26c4-7vv6-867j | keras-team/keras | Python | 13 | yes | yes | saving_lib.py `_verify_group`; `_verify_dataset` | legacy_h5_format.py `load_model_from_hdf5`; `load_weights_from_hdf5_group`; `..._by_name` +4 | partial |
| 13 | 42 | GHSA-889w-m37p-88m5 | pyload/pyload | Python | 13 | no | yes | user_database.py `set_user_permission` | `__init__.py` `__init__` | partial |
| 14 | 43 | GHSA-8mgp-746c-j5xp | nltk/nltk | Python | 13 | yes | no | perceptron.py `_authorize_private_dir`; `_validate_name_component` | crf.py `set_model_file`; hunpos.py `__init__`; stanford.py `__init__` | partial |
| 15 | 45 | GHSA-pr7f-p5mw-fc87 | vllm-project/vllm | Python | 13 | no | yes | sparse_utils.py `check_sparse_tensor_invariants_threadsafe` | audio.py `load_bytes`; `load_file`; image.py `_load_pickled_torch` +2 | partial |
| 16 | 46 | GHSA-q4c3-7575-55j2 | apache/airflow | Python | 13 | yes | yes | scheduler_job_runner.py `check_awaiting_input_timeouts` | trigger.py `_decode_next_kwargs`; `_fail_unresumable_task_instance`; `handle_event_submit` | unknown |
| 17 | 50 | GHSA-5rr4-8452-hf4v | better-auth/better-auth | TypeScript | 13 | yes | yes | discovery.ts `validateSkipDiscoveryEndpoint`; `validateSkipDiscoveryEndpoints` | types.ts `DiscoveryErrorCode`; schemas.ts `oidcConfigSchema`; sso.ts `ssoProviderBodySchema` | partial |
| 18 | 54 | GHSA-8r5x-fm3f-whwj | handlebars-lang/handlebars.js | JavaScript | 13 | yes | no | compiler.js `validateDepth`; `validateLiteral`; `validateStringArray` +2 | base.js `parseWithoutProcessing` | partial |
| 19 | 65 | GHSA-c36x-h252-g9x2 | openbao/openbao | Go | 13 | yes | no | request_handling.go `IsSSCToken` | expiration.go `loadEntry` | unknown |
| 20 | 72 | GHSA-9rm7-3qhh-h2mc | square/wire | Kotlin | 13 | no | no | ReadBuffer.swift `verifyAdditional` | ProtoDecoder.swift `ProtoDecoder` | partial |

A quick reading of these 20, by names only and without opening the code:
- **About 10 look like a real check plus producer split**: better-auth ×2 (DB schema / SSO schemas
  next to a token or endpoint check), keras, airflow, openbao, olivetin, handlebars, wire, pnpm,
  coraza GHSA-6r3q.
- **About 4 are sibling loaders** that need the same check (vllm, nltk, keras partly). That is S8
  rather than S2b.
- **About 6 are noise**:
  - a build script (coraza `magefile_adr.go`);
  - constructors of check classes (winter, koel, praisonai GHSA-2jgc, pyload);
  - mixed multi-fix commits (praisonai GHSA-2gpf);
  - the domain word "schema" in swagger-typescript-api.

Whether the check reaches the producer is unknown for all of them until the `siblings` stage runs.

## 6. Proposed points

| Key | Now | Proposal | Reason |
|---|---|---|---|
| `s2a_disparity` | 0 | **keep 0** | 0 of 4 S2-type items caught on index values (1 of 4 on task fixes), precision 0/3 to 1/5. Advisories name the cause, so the signal measures how precise the advisory is. Fires on 19% of the pool. |
| `s2a_partial` | 0 | keep 0 | 31% of the pool, uninformative |
| `s2a_on_named` | 0 | keep 0 (−1 is defensible later) | 7 of 8 were not S2-type, but the base rate is 75%; on_named candidates already score lower (median 3 vs 8) through the compact-fix and one-site LOW signals. Revisit with round-2 outcomes. |
| `s2a_unknown` | 0 | keep 0 | |
| `s2b_check_and_producer_in_other_file` (loose) | 0 | **keep 0** | 11% of the pool; the loose form includes constructors and linked pairs (one FP: py-shiny) |
| `s2b_bonus_strict_roles` | 0 | 0 now; **+2 after trap calibration** | fires on the one confirmed Hadi-shape case (MCP, DeepSeek 0/3) and not on the on-path rclone; 5.5% of the pool |
| `s2b_bonus_other_directory` | 0 | keep 0 | 135 of 164 firings already cross directories; adds little |
| `s2b_check_does_not_call_producer` | 0 | **+3 once computed** | the actual Hadi condition (DeepSeek 8/8 misses); needs the vulnerable tree (`siblings` stage) |

Use it now, without points: take hosts for calibrating the "data producer off the check's path"
trap from the S2b-strict list (`score_detail` label "strict (both by name)"). The plausible ones
from the top 20 are a reasonable start (better-auth, keras, airflow, openbao). Calibrate on at
least 2 hosts × both models, then set the strict points.

## 7. What did not work or is limited

- **S2a's premise.** Advisories describe the root cause, often by name, and our instructions are
  symptom-only with no names. So neither text gives "where the symptom shows" reliably. A useful
  S2a would need the symptom location from a stack trace or the exploit's entry point, for
  example the PoC section, which is now excluded.
- **Hunk headers.** For indented methods (Java, Python, PHP, Kotlin) git's default hunk header
  names the class. The method is known only when its definition line falls inside the hunk.
  S2a/S2b therefore fall back to file names more often in these languages.
- **Role keywords are crude.**
  - "auth" and "token" inside identifiers make most sites in auth code check-role.
  - Domain uses of "schema" and "model" count as producers.
  - Constructors of check classes count as producers; strict excludes them.
  - Rust inline tests and build scripts are counted as source.
  - Roles can also come out the wrong way round: rclone's producer, the proxy, is labelled the
    check.
- **Combined patches.** On stacking and sibling tasks, a combined patch pairs sites from
  different flaws, so S2b is meaningful only per advisory, which is how the pool computes it.
- **Plain unified diffs.** `parse_patch` needs `diff --git` headers. Two task patches (russh-sib,
  ruby-saml) are plain unified diffs and were converted in the validation script. The sourcer only
  reads GitHub `.patch` files, so it is not affected.
- **Missing cached fixes.** py-shiny, the asyncssh pktsize item and argo's items have no cached
  upstream fix in the index (pending or deferred). Their values come from the task fix.patch.
- **Small numbers.** n is tiny everywhere: 4 S2-type items and 1 off-path item. Every rate above
  is descriptive.

## Files

- `sourcer/patchmetrics.py`: `def_name`, `name_words`, `role_of_words`, `site_role`,
  `location_metrics`. Hunks also keep their context lines (`seq`) for finding definitions.
  Existing metrics are unchanged; verified on all 1,997 cached commits.
- `sourcer/osv_sourcer.py`: `named_locations`, `s2a_signal`; S2a/S2b labels in `score_entry`;
  `pool_s2_computed` in `stats`.
- `sourcer/weights.json`: the `symptom_fix_disparity` block.
- `sourcer/README.md`: the scoring section.
- `sourcer/index/candidates.before-s2.sqlite`: backup taken before the stages ran.
- `research/round1-analysis/D-computed-s2-validate.py`: the computed columns of section 2.
