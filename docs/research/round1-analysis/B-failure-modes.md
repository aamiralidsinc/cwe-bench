# B. Where and why the models' fixes fell short (round 1)

Date: 2026-10-16. Read-only analysis; nothing was re-run. Catalogue: `B-defects.tsv` (one row per
run x defect, 33 rows).

Sources:
- the per-trial folders `~/.tb-graders/cwe/jobs/*/*/`:
  - `verifier/results.json`
  - every non-set-aside `regrade-*/REGRADE.json` and its `results.json`
  - `postmortem-*/verdict.json`
  - `final-code/changes.patch`
  - `agent/claude-code.txt` (searched by keyword)
- `build/audit/{trials.tsv, excluded_runs.tsv, task_defects.tsv, contaminated.tsv, reviews.tsv,
  lenient_items_2026-10-16.txt, offline_since.tsv, internet_use_cache.json}`
- the "2026-10-16 test repair" section of each `build/<task>/notes.md`
- `research/own-runs/{FINDINGS.md, raw/*.md}`
- the async-http-client reconstructions in `~/.tb-graders/cwe/work/async-http-client/recon/`

What counts as a real defect here:
- The model's code violates a property the instruction states, or one a competent engineer infers
  from it.
- An audit or fairness review accepted the test that exposes it.

Not counted as defects:
- test faults
- unfair tests
- set-aside regrades
- infra failures and provider stops
- runs cut at 60 min under the old limit

Defects that are real at the code level but sit in runs that cannot count are listed separately,
because they are useful for design.

## 0. Bottom line

1. **There are 23 counted real defects in 18 runs**:
   - 15 of them are in the jackson family (7 dismissed siblings, 8 coupled-binding over-breadths);
   - 8 are in other tasks: argo x4, async-http-client x2, asyncssh x1, webob x1.

   A further 10 code-level gaps sit in runs that do not count. They are useful for design.
2. **No defect came from a variant the model never found. Every miss was a judgement error about
   code the model had looked at.** In 7 of 7 jackson sibling misses, DeepSeek located the
   any-setter and argued it out of scope. Outside jackson:
   - argo templateDefaults: both models saw it and skipped it.
   - asyncssh dropbear `-= 1`: DeepSeek edited the lines next to it.
   - async-http-client: DeepSeek saw the STRICT decoder drop malformed pairs and called that
     "acceptable".
   - rclone: DeepSeek wrote the key-ID fallback on purpose.
   - webob: MiMo chose "one policy for all three APIs".
3. **Our original tests caught none of the 8 non-jackson defects.** Post-run audits flagged every
   one of them as "lenient, passing fix is incomplete", and today's repaired tests confirmed them.
   The jackson defects were caught by the original tests only because those tests were built
   around an injected sibling and a coupled-binding functional case.
4. **Only two classes recur:**
   - *Feature-absent sibling dismissed*: DeepSeek 6/6 on jackson-databind-sib, MiMo 0/2 valid runs.
   - *Over-broad fix on a coupled binding*: 8 of 27 graded jackson-family runs, both models.

   Every other class hit about half the exposed runs of a model, with n = 1-3. That is enough to
   break single runs, but not pass@3.
5. **What the models reliably got right is breadth.** Both models fixed these in every graded run:
   - every encoding variant (absolute path, embedded `../`, percent-encoding, decimal or
     IPv4-mapped IPs, C0/space prefixes);
   - every CRUD verb and every artifact operation;
   - every protocol sibling (FTP, SFTP, HTTP);
   - both roles and both directions (russh raw and legacy peers, asyncssh open-confirmation).

   Injecting more of these adds volume, not difficulty.
6. **Wording decided four outcomes:**
   - The sib7 paraphrase leaked the siblings: DeepSeek found them in 10 of 11 runs, against 0 of 6
     under the sib wording.
   - cloudreve's "tens of millions of pixels" anchored both models' 16.7 MP cap.
   - argo's "directly … for instance" was DeepSeek's stated reason to skip templateDefaults.
   - An unstated proxy interface pushed DeepSeek to fail open and MiMo to refuse everything.

   Precise preservation clauses ("exactly as it does today", "when the caller names a cookie")
   are what made the subtle defects fair to test.

## 1. Catalogue

### 1.1 Counted real defects (18 runs, 23 defects)

| # | Task (track) | Model | Run(s) | Missed variant | Code-level reason | Saw it? | Detected by |
|---|---|---|---|---|---|---|---|
| A1-A6 | jackson-databind-sib (inj) | DS | UrYkU9y, Y7sUNWQ, DHJMrS9, pe7cTre, tFp6yZg, spxepkT | `@JsonView`-restricted `@JsonAnySetter` (Map / method / JsonNode) still filled under PublicView | edited only ExternalTypeHandler + BeanDeserializer; `SettableAnyProperty` has no view logic and was left alone | **yes, all 6**, in the first minute; dismissed ("no view matcher … out of scope"; "a grader can't test it") | original tests |
| A7 | jackson-sib7 (inj) | DS | eemmJfp | all 5 any-setter siblings | same | **yes**: its own probe printed the leak, then "implementing it is out of scope" (cost: "~10 call sites") | original |
| F1-F8 | jackson-databind (mined), -sib, -sib7 | DS x6, MiMo x2 | m45hNgn; DHJMrS9, pe7cTre, tFp6yZg, yWRg48p; azQQS2U, mGjGeey, fkF5qrx | functional: the unrestricted type-id creator param `kind` must still bind when the sibling value `asset` is hidden | the guard skips the whole ext-typed entry (or refuses to record the type id) when the value is hidden, so the visible linked param is dropped | DHJMrS9 stated it as a design choice; others not traced | original (functional) |
| E | argo-workflows (stack) | DS, MiMo | QprUNQg, b5WYen5 | sync-limit CRUD by a caller with workflow rights and no ConfigMap rights | `CanI(verb, "workflows", ns)` copied from the DB provider, not a check on the ConfigMaps actually read and written | **yes**: both read the `sync_db.go` comment "configmap version is relying on the k8s RBAC" | audit (lenient stub) → per-resource stub → regrade |
| M | argo-workflows (stack) | DS, MiMo | same runs | `spec.templateDefaults.securityContext` under template-referencing | denylist of 16 (DS) or 10 (MiMo) top-level WorkflowSpec fields; no allowlist and no sanitising of the merged spec | **yes**: DS "not 'directly' a workflow-level pod field. Skip"; MiMo "templateDefaults would override template-level settings…", then left it | audit → new test → regrade |
| B1 | asyncssh (stack) | DS | emBowC5 | a peer advertises max_pktsize 0 with a dropbear banner and compression on (the library default), so 0 becomes -1 and the endpoint spins | `if not send_pktsize` placed **after** the dropbear `send_pktsize -= 1`; the loop guard is truthy for -1 | **yes, misjudged**: final message says the workaround "is checked after the adjustment" | audit only → new test → regrade |
| C1 | async-http-client (mined) | DS | uGhFbba | caller sends `Cookie: SID=user"B; x=1` while the store holds `SID=storeval`; the store's session is sent | the STRICT (default) decoder drops the malformed SID pair, so the caller "names" only `x` and the store's SID is added | **yes, misjudged**: probed it ("SID=with space → empty … acceptable"); never traced the substitution | audit REC → new test → regrade on transcript-reconstructed code |
| C2 | async-http-client (mined) | MiMo | tfkenPc | same | its own quote-aware `names()` treats a lone `"` as opening a quote to the end of the header, so no names are extracted and the store's SID is appended | partly: it avoided the lossy decoder but not its own scanner's edge | same |
| G1 | webob (mined) | MiMo | GTgqHjZ | functional: `relative_url("//other.host/x")` must resolve as today | one shared `safe_urljoin` folds `//` for all three APIs, with no opt-out | **yes, chose it**: "Policy (shared by all three APIs)"; its own test asserts the new behaviour | audit REC → new functional test → regrade (1.0 → 0.0) |

### 1.2 Real at code level, not counted (useful for design)

| Id | Task / model / run | Gap | Why it does not count |
|---|---|---|---|
| D1 | rclone / DS / rEMTRVZ | `verificationSecrets()`: tries 5 guessed field names, then any config value, then **falls back to the access key ID and md5(key ID)**. The code comment says "so the request must still be signed with something". | It ran before the 01:57 instruction fix that states `_secret_access_key`. The defect is real (carol, signing with her own key ID, was served alice's file). |
| I1, I2 | rclone-sib / MiMo / StBjAQQ, ypUhTQw | **Refuse-all** in proxy mode: with no shared secret, nothing is served. This mirrors D1. | Unstated-contract era (before 01:57). ypUhTQw was audited as a test fault. |
| H x2 | cloudreve / both / JwDetgF, TFwPvkf | Thumbnail cap at 1<<24 (16.7 MP); a 24 MP photo would be refused. | The requirement exists only in the instruction sentence added today. Both transcripts cite the old "tens of millions of pixels". |
| H | filament / MiMo / nQD6JG9 | Refuses with its own `Exception`, which becomes HTTP 500 instead of a 4xx. Nothing is staged, so there is no security defect. | Set aside: the refusal rule was added after the run. |
| J x2 | stigmem / DS UusDPh3, MiMo UC3PPQh | Unsigned-plugin acknowledgement checked in the startup lifespan only; the plugin CLI path stays open. | The runs are excluded (test-fault era). Never tested. The instruction says "at startup", so fairness is unsettled. |
| K x2 | stigmem / MiMo / KCFDjFF, qTbSDP7 | Deliberate carve-out: an explicit `signing_required=False` argument skips the acknowledgement, "because hidden-test fixtures would pass it". | Test-fault era (the test called an internal function); qTbSDP7 is excluded. |

### 1.3 Below 1.0 but not a model defect

These runs scored below 1.0 for reasons unrelated to the model's fix; excluded per
`excluded_runs.tsv`, `task_defects.tsv` and `reviews.tsv`:
- **Test faults:**
  - actualbudget MiMo x3: the test called the product helper the model had hardened;
  - argo VSELT69: a 5 MiB body against an unstated 2 MB constant;
  - stigmem v2/v3/v4 (all runs): the tests varied `node_url` and called an internal function;
  - trigger-dev Gts23hz / eQ9xLN3: an exact-405 assertion and a nonexistent batch;
  - webob eSAv3oh / CeNzGqe: a bare-`//` test outside the instruction.
- **Harness failures:**
  - trigger-dev wEafvJY / Jqy5Sqn: the webapp build failed in grading;
  - the jackson-databind-sib MiMo gUSEhL9 provider stop.
- **Runs cut at 60 min:**
  - async-http-client diNL3jn;
  - asyncssh 666Zvjv and 2AsC7RG (2AsC7RG broke per-user pubkey login; it was cut mid-work and
    is not classified);
  - cloudreve pe6Ft9Q;
  - stigmem KCFDjFF / UC3PPQh.

## 2. Failure classes

### 2.1 Counts (counted defects only; n is tiny)

"Hit / exposed" counts the graded runs of that model on that task that could show the defect.
- **Offline runs:** the attempt rates are low, but some lookups may have worked.
- **Online runs:** included only where the final code was regraded on the repaired test, or where
  the original test already covered the variant.

| Class | Description | DS | MiMo | Track | Hit / exposed |
|---|---|---|---|---|---|
| A | **Sibling dismissed as out of scope.** The mechanism lacks the security feature entirely, and the model reads the absence as design ("no view matcher, so not a restricted property"). | 7 | 0 | injection | DS 6/6 (sib), 1/11 (sib7, leaked wording); MiMo 0/2 valid |
| F | **Over-broad on a coupled binding.** Hiding value A also drops the linked, visible B that the same handler entry binds. | 6 | 2 | mined 1, injection 7 | DS 6/20, MiMo 2/7 (jackson family) |
| E | **Authorises a neighbouring resource.** Copies a nearby precedent that checks a proxy permission (workflows) instead of the object actually touched (configmaps). | 1 | 1 | stacking | DS 1/2, MiMo 1/2 offline |
| M | **Denylist of the instruction's examples instead of a structural fix.** Misses a merged-source route (templateDefaults) to the same sink. | 1 | 1 | stacking | DS 1/2, MiMo 1/2 offline |
| B | **Check placed after a local adjustment.** It tests equality where a range is needed, and the adjustment turns the stated bad value into an unchecked one (0 → -1). | 1 | 0 | stacking | DS 1/1, MiMo 0/1 (regradable offline runs) |
| C | **Parser mismatch on the protected item's identity.** The guard's name extraction fails on a malformed value, so the fallback source (the cookie store) supplies the privileged value. | 1 | 1 | mined | DS 1/3, MiMo 1/4 (0/3 fresh) |
| G | **Over-generalisation across sibling APIs.** One shared helper or policy is applied to APIs with different contracts, which breaks a stated "as today" behaviour. | 0 | 1 | mined | MiMo 1/2, DS 0/2 offline |
| D (not counted) | **Fail-open fallback when authoritative data is missing**, hedging an unknown interface. | (1) | 0 | mined | DS 1/3 |
| I (not counted) | **Refuse-all under interface uncertainty** (the mirror of D). | 0 | (2) | injection | – |
| H (not counted) | **Over-restriction induced by wording** (anchored threshold; unstated refusal mode). | (1) | (2) | stacking | both cloudreve runs |
| J, K (not counted) | **Fix at one caller rather than the shared sink**; **carve-out driven by guessing the grader**. | (1) | (3) | stacking | – |

Totals (counted):
- by model: DeepSeek 17, MiMo 6;
- by track: injection 14, stacking 5, mined 4.

Without the jackson family, the two models are level: DeepSeek 4, MiMo 4.

### 2.2 What the classes have in common

- **Judgement, not search.** Every counted defect except the untraced F runs was located in the
  transcript. The models decide a case does not matter for three reasons:
  - **the code already "doesn't support" it** (A: jackson; M: "not directly a pod field");
  - **a neighbour does it that way** (E: the sync_db precedent; G: the shared helper);
  - **malformed input is out of scope** (C, and B: "checked after the adjustment").

  Three facts about this:
  - Neither model ran the attack against the specific case it dismissed. The one exception is
    eemmJfp, which ran it and still dismissed it.
  - MiMo's advantage on A is that it probes: pvqkL7s and yWRg48p reproduced the any-setter leak
    before fixing it.
  - On B, C, E, M and G, MiMo did no better.
- **Second-order consequences.** In B, C and D the first-order fix is right: 0 is refused, the
  caller's header is honoured, an empty secret is refused. The defect is what happens next in the
  pipeline:
  - B: an adjustment turns 0 into -1;
  - C: a parse failure means the store fills the name;
  - D: a missing secret means a public value is used instead.

  These are exactly the cases our reference-informed tests did not think to probe.
- **Grader modelling.** Both models reason about what the grader can test:
  - DeepSeek tFp6yZg: "a grader can't test it";
  - MiMo stigmem: carve-outs "because hidden fixtures would pass it";
  - DeepSeek rclone: guessing the hidden field names.

  Wherever scope is arguable, this reasoning resolves it toward less work or toward a hedge.
- **Instance thinking.** A and M both treat the instruction's examples or the reported shape as
  the whole set. Once a concept is accepted, its routes fall together: sib7's five any-setter
  routes were closed 10/10 by DeepSeek and 3/3 by MiMo whenever the concept was accepted. So
  difficulty comes from *concepts* a model rejects, not from more routes of an accepted concept.

### 2.3 What the models reliably got right (not worth injecting)

Every graded run fixed these (per test, latest grading, both models where graded; online-era
runs included):
- **Encoding and spelling variants of a stated input:**
  - py-shiny's 6 traversal forms (DS 21/21);
  - asyncssh absolute and embedded SCP names and embedded usernames;
  - the webob C0/space/tab prefixes on all three APIs (5/5 each);
  - trigger-dev SSRF via decimal IP, `[::ffff:169.254…]` and `localhost`.

  cloudreve's new variants were never run on model code, because no final code was saved.
- **The same check over every verb or operation:**
  - actualbudget file authorisation (metadata, rename, key, overwrite, reset, download);
  - argo artifact credential logging (6 operations);
  - rclone empty secret on List, Get, Put and Delete.
- **Protocol and role siblings:**
  - rclone-sib FTP, SFTP and HTTP wrong and empty passwords;
  - russh and russh-sib raw and legacy peers in both roles and both directions, including
    re-keying to the null kex;
  - asyncssh pktsize in open-confirmation, and the second pre-kex message type per direction.
- **A stated check at the named entry point:**
  - filament (8/8);
  - ruby-saml (5/5, including the parse-spy and timing checks);
  - hickory bogus answers, including forged CNAMEs;
  - stigmem v1, v5 and v6;
  - trigger-dev cross-env cancel and cross-org batch;
  - argo template Get authorisation and the webhook cap;
  - the hostNetwork, securityContext and serviceAccount fields the instruction names.

"Fix in one role or direction only" is a class we designed patch checks for (russh, russh-sib,
asyncssh). **No model run ever made that mistake.** The same holds for "skip one CRUD verb" and
"handle the reported encoding only".

## 3. What to inject and how to test it

### 3a. Ranked sibling-injection recipes

The ranking weighs three things: whether it beat both models, how consistently, and whether it is
fair under the two criteria (a stated property, plus a clue in the visible code near the fix).
Every n is 1-3 per model, so treat the ranks as hypotheses.

| Rank | Recipe | Beat | Fairness hook (instruction) / visible clue (code) | Example from our tasks |
|---|---|---|---|---|
| 1 | **Coupled visible binding next to the hidden one.** The fix must hide A while a linked B, handled by the same entry, stays live. Inject or choose B, and test it functionally. | both, ~30% of runs, in every variant | "visible properties must keep binding even when a sibling value is hidden"; the shared handler entry is visible | jackson `TypeIdCreatorContainer`: `asset` hidden, `kind` (type id, visible) must still bind |
| 2 | **Merged or defaults route to the same sink.** The restricted value can also arrive through a defaults, merge, patch or inheritance field that the instruction's examples do not name. | both, 1/2 each offline | state the sink ("anything the submitter supplies that ends up in the pod"), not the entry; a merge function (`mergedTemplateDefaultsInto`, `StrategicMergePatch`) sits downstream of the check | argo `spec.templateDefaults.securityContext` |
| 3 | **Neighbour-precedent authorisation.** A sibling backend or provider authorises a proxy resource; the natural fix copies it. The test denies exactly the object touched. | both, 1/2 each offline | name the protected object class ("the objects holding the limits"); the precedent and a comment pointing at the real object are visible | argo sync: the DB provider checks `workflows`; the CM provider must check `configmaps` |
| 4 | **Feature-absent sibling, plus one omitted call site.** One mechanism ignores the security feature entirely (beats reasoning-first models). To beat probe-first models, add a second sibling where the feature is honoured on N-1 paths and skipped on one, so a probe of the common path passes. | DS 6/6 (feature-absent alone); MiMo 0/2; the omitted-call-site half is untested | a property-level "on every binding path"; a member annotation that is visibly ignored | jackson-databind-sib any-setter (`SettableAnyProperty` has no view code) |
| 5 | **Post-adjustment value.** The stated attacker input passes through a library-internal adjustment (a compatibility workaround, offset, clamp or unit conversion) before the natural check site, which turns the bad value into a different bad value. | DS 1/1; MiMo 0/1 | the abuse is stated as the attacker's input ("advertises zero"); the adjustment sits a few lines above the check | asyncssh dropbear `send_pktsize -= 1` with compression |
| 6 | **Parser differential on the identity of the protected item, plus a privileged fallback.** The guard must decide whether the caller "named" X. A malformed-but-plausible spelling makes the extractor return nothing, and a fallback supplies a privileged X. | DS 1/3, MiMo 1/4 | "when the caller names X, the caller's value wins"; a lax/strict decoder flag or two parsers are visible | async-http-client `Cookie: SID=user"B; x=1` with the store's `SID` |
| 7 | **Missing-authority fallback.** The authority (proxy, IdP, policy store) returns no secret or role; the fix must fail closed. | DS 1/3 (uncounted era) | "accepted only when it verifies against the secret the authority supplies"; the existing code already has a default-secret path | rclone proxy returning no secret (key-ID / md5 fallback) |
| 8 | **Shared helper with divergent contracts.** A family of APIs shares a helper; one API must keep a legacy behaviour that the security rule would change. | MiMo 1/2 | an explicit "X must resolve exactly as it does today"; the helper's other callers are visible | webob `relative_url("//host")` vs `Response.location` |

How to use these:

- **Stack different classes, not routes of one class.** Routes of one concept fall together once
  the concept is accepted (sib7). Classes 2, 3, 5, 6 and 8 have different "reasons to dismiss",
  so their misses are less likely to be correlated. That is untested.
- **Honest arithmetic.** Suppose a task holds four independent traps, each missed in half of a
  model's runs. Then P(a run solves) = 0.5^4 ≈ 6%, and P(pass@3 = 0) = 0.94^3 ≈ 0.82. With three
  such traps, P(pass@3 = 0) ≈ 0.67. In practice misses are probably positively correlated (a
  careful run catches all of them), so these figures are upper bounds.
- **Only class A reached a model consistently.** For a robust both-model breaker, pair one A-type
  sibling (it fixes DeepSeek's outcome) with at least three traps from classes 1-3 and 5-8.
- **Keep each sibling un-diffable.** Place siblings where the upstream patch never touches. A
  model that ports upstream will port its `<= 0`, its allowlist and its `configmaps` check, so the
  recipes above only bite on the injected part. We saw this: online runs that copied upstream
  passed E, M and B.

### 3b. Test-design rules (what caught each defect)

| Defect | Test shape that caught it | Rule |
|---|---|---|
| A (sibling) | one security test per declaration form of the sibling (Map, method, JsonNode) | one security test per *form* of each injected sibling, written against the stated property |
| F (coupled) | functional: hide A, assert that the linked visible B is still bound (`visibleTypeIdCreatorPropStillBound`) | for every "hide or refuse X", add a functional test on the thing most tightly coupled to X: the same handler entry, object or request |
| B (adjustment) | the attacker still sends exactly the stated value (0), while legitimate environment knobs that alter the value path are set: dropbear banner, compression on. Hang detected by timeout. | for each numeric or attacker-sized input, find every transformation between parse and check, and add a scenario that drives each one with the stated bad value |
| C (parser) | the caller's header with a malformed-but-plausible value plus a same-named privileged value in the fallback source; assert the privileged value is never sent; accept refusal or dropping | for each "whose value wins" rule, test a malformed spelling of the caller's item while the fallback holds a privileged item of the same name |
| D / I (missing data) | the authority returns nothing, and the request is signed with every publicly derivable credential (empty, the ID, a hash of the ID): require refusal. Plus positive correct-credential tests per verb (GET, PUT, DELETE). | pair every "refuse the bad credential" test with (a) "the authority says nothing" and (b) "a good credential works for each verb" |
| E (wrong object) | an RBAC-like stub that denies exactly the touched resource, allows its neighbours, and answers per verb and namespace | permission stubs answer per resource, verb and namespace; deny the real object and allow the plausible proxy |
| M (merged route) | a probe through one non-example route into the same sink, verified to reach the sink on the vulnerable code | test at least one route the instruction does not list but its property covers, after proving it reaches the sink at the vulnerable commit |
| G (shared helper) | a preservation test of the sibling API's adjacent behaviour, with the expected value computed from the vulnerable code | for each API that shares the fixed helper, add one "unchanged from today" functional case near the security edge |
| H (wording) | a functional test at a legitimate magnitude just above the anchored number (a 24 MP photo) | when an attack magnitude is given, also test (and state) a legitimate one of the same dimension |

Gate-level consequence:
- None of the 8 non-jackson defects was caught by tests written with the reference in hand. Each
  was found only by a post-run audit. Today's patch checks already include the bite patches:
  - `pktsize_eq_zero_only`, `fix_strict_decode`;
  - `reads_only_proxy`, `reject_all_proxy`;
  - `sync_wrong_resource_fix`, `refmode_denylist_fix`;
  - `relative_url_folds_protocol_relative`.
- Make these six "neighbour" families a builder checklist item (§3f): for each item, add a test
  and a `security_fail` / `functional_fail` patch for every family that applies:
  - adjustment
  - malformed identity
  - missing authority
  - wrong object
  - unlisted route
  - adjacent-API preservation
- That way the audit finds less, and the trap exists before the runs.

### 3c. Screener-level signals that predict such siblings

Each signal is computable from the vulnerable tree near the fix site:

| Signal (grep-able near the fix) | Recipe | Evidence |
|---|---|---|
| A linked value shares the handler, record or entry with the restricted one (type id + value; header + store; one handler entry binds two members) | 1 | jackson, 8/27 runs |
| A merge, defaults, patch or inheritance step downstream of the restricted fields (`StrategicMergePatch`, `*Defaults*`, template inheritance, config overlays) | 2 | argo |
| Two or more providers or backends for one operation with different authorisation models, or comments such as "relies on k8s RBAC" / "checked elsewhere" | 3 | argo |
| A mechanism with no reference at all to the security feature that sibling mechanisms use (grep for the feature's API in each sibling class) | 4 | jackson (`SettableAnyProperty` has 0 `View` hits) |
| Arithmetic, clamps or version-keyed workarounds on an attacker-supplied number between parse and use (`-= 1`, `min(`, `if b'peer' in version`) | 5 | asyncssh |
| Two or more parsers or decoders of the same input, or a lax/strict switch (`LAX ? … : STRICT`, a custom splitter next to a library decoder) | 6 | async-http-client |
| A fallback or default source next to an identity or credential decision (`or default`, a store merged with caller input, "if missing use …") | 6, 7 | async-http-client, rclone |
| One helper called by several public APIs with different documented semantics | 8 | webob |

Signals that did **not** predict difficulty in round 1, so give them weight 0 for difficulty
(they may still matter for injectability):
- the same check needed on N verbs or operations;
- client/server role symmetry and send/receive direction;
- several protocols sharing one auth layer;
- encoding variants of one input;
- the number of stacked items;
- the CWE class.

The screener's S1 (multi-site) is about injectability. These new signals are about *which kind*
of sibling the site can host. I propose adding them as a "trap affordance" tally: count the
distinct recipe classes 1-8 available within about 50 lines of the fix. Prefer candidates with
three or more distinct classes.

## 4. How much instruction wording drove outcomes

| Case | Wording | Effect |
|---|---|---|
| jackson-sib7 leak | one added sentence listing "field, setter method, or constructor parameter, whatever its declared type … paths that gather input during construction" | DeepSeek went from 0/6 (sib) to 10/11 runs finding the any-setter siblings, decoding them within 15-40 s. The siblings themselves added nothing (all 5 routes fell together). |
| cloudreve cap | "a tiny file that claims, say, *tens of millions of pixels*" | Both 1.0 runs capped at 16.7 MP and cited the phrase; DeepSeek weighed a 6000x4000 photo and rejected it. Fixed by adding "for example an ordinary 24-megapixel camera photo". |
| filament refusal | no rule for how to refuse | MiMo refused with a server error (500). A rule was added ("answer it as a client error"); the run was set aside. |
| argo ref-mode | "set pod-level fields *directly* on the referencing workflow — *for instance* host networking, …" | DeepSeek r11 skipped templateDefaults explicitly because it is "not 'directly' a workflow-level pod field". The examples were read as the set, and both r11 runs built a denylist of them. Both r12 runs (same wording) included templateDefaults, so wording made the miss possible but did not force it. |
| argo sync | "permitted to modify *configuration* in that namespace" | The protected object is not named, and both r11 runs copied the `workflows` precedent. Auditors judged the test fair at *medium* confidence for this reason. |
| rclone / rclone-sib | the proxy secret field was unstated until 01:57 | The same gap pushed DeepSeek to fail open (guessed fields, then fall back to the key ID) and MiMo to refuse everything. Both runs are excluded. |
| stigmem / trigger-dev | "bound to" vs the tested `node_url`; "must not exist" vs an exact 405 | Test faults (already in BUILDER §3g); listed for completeness. |
| webob, async-http-client, asyncssh (positive) | "must resolve *exactly as it does today*"; "when the caller *names* a cookie, the caller's value … must be sent"; "*advertises* a maximum packet size of zero" | These clauses made the G, C and B defects fair to test without naming them: the property is stated in terms of the attacker's or caller's input, not the code path. |

Rules for writing instructions:

1. **State the property and its scope; never list a sibling's forms, types or phases.** Run the
   blind "name the mechanism" check (BUILDER §3f) on every instruction. sib7 passed the
   literal-term leak check and still leaked through paraphrase.
2. **Phrase the security property in terms of the attacker's input and the protected sink, not the
   entry point.** For example: "anything a submitter supplies that would reach the pod
   specification", not "pod-level fields set directly". Avoid restricting adverbs ("directly",
   "only via"), and say that examples are examples ("these are examples, not the full set").
   Models read example lists as exhaustive.
3. **Name the protected object class** ("the objects that hold the limits"), so the
   correct authorisation target is not left to a neighbouring precedent. Keep the API names out.
4. **Never give a bare attack magnitude.** Either give none, or give a legitimate magnitude of the
   same dimension next to it.
5. **State the refusal contract once, in boilerplate.** For example: "refuse as a client error,
   with no side effect". State every interface a test needs (field names the authority returns).
   An unstated interface produces both fail-open and refuse-all hedges.
6. **Write preservation clauses for adjacent APIs and linked values** ("must behave exactly as
   today", "visible properties must keep binding even when a sibling is hidden"). They are the fair
   hooks for classes F and G, which beat both models.
7. **Do not try to argue the model out of "out of scope".** The sib wording already said "any
   mechanism by which otherwise-unmapped input can still be routed into a restricted property", and
   DeepSeek still dismissed the sibling six times. The fair fix is in the visible material, not more
   prose. For example, an existing repo test or doc that shows the security annotation on the
   sibling's member type makes the sibling clearly in scope without naming it. Untested.

## 5. Limits

- **Small n.** About 20 tasks and 38 pairs. Each non-jackson class rests on 1-2 runs per model.
  The "1/2" hit rates have huge intervals, and no correlation here should be read as established.
- **Jackson runs predate the offline switch.** They had no upstream to look up (0 lookups).
- **async-http-client verdicts rest on reconstructed code.** The C1/C2 verdicts use transcript
  reconstructions (checked against every later Read, 0 mismatches), not harvested code.
- **"Saw it" comes from keyword searches of transcripts.** Absence of a hit (the F runs other than
  DHJMrS9, and C2's quote edge) means "not found", not "not seen".
- **Some fixes are inferred, not regraded.** The cloudreve and stigmem gaps come from transcripts
  and audits.
- **trigger-dev tests are still in flux.** No trigger-dev defect is counted.
- **Online-era passes that copied upstream are not evidence of skill against these classes.** The
  recipes are calibrated on the offline and no-upstream runs only.
