# CWE-bench: sibling-injection patterns, and how each built task uses them

Contents:
1. [The crux](#1-the-crux)
2. [Pattern catalogue](#2-pattern-catalogue)
3. [Counts: what was built and what bit](#3-counts-what-was-built-and-what-bit)
4. [How the symptom points to the sibling](#4-how-the-symptom-points-to-the-sibling)
5. [Every task at a glance](#5-every-task-at-a-glance)
6. [Per-task detail](#6-per-task-detail)
7. [Appendices: tasks without siblings, unbuilt prompts, method and caveats](#7-appendices)

---

## 1. The crux

**What a sibling is.** A task pins a real repo at a vulnerable commit and gives the solver a short
report. The report shows one symptom through one route: the **base** bug. A **sibling** is another
place where the same protection is missing, which the report does not name. A fix of the reported
site alone therefore scores below 1.0. Siblings are recorded in `manifest.traps`, one entry per
trap. Each entry gives the location, the shape, a "reason to dismiss", the security tests that
catch a missed sibling, and the functional tests that catch an over-broad fix.

**How many patterns.** Every trap is classified on two axes.

- **Origin: where the sibling comes from. Three sibling sources, plus three trap kinds that are not
  siblings.**

  | Code | Name | Sibling? |
  |---|---|---|
  | `A-FAR` | **Pattern A**: a site the real upstream fix also changed, which the report does not lead to | yes |
  | `B-ROUTE` | **Pattern B**: a real, unmodified upstream route with the same gap, which the upstream fix never touched | yes |
  | `INJ` | **Injected**: code we planted into our copy | yes |
  | `SHAPE TRAP` | **Shape trap**: an input form of an existing route that a plausible check mishandles. Pure spelling or encoding variants are always caught; shapes that hide a parser differential (M8) are missed | no |
  | `COUPLED TRAP` | **Coupled trap**: a must-keep-working legitimate value next to the hidden one, tested functionally, so an over-broad fix scores 0. **MiMo generally fails it**, since it tends to over-harden; DeepSeek breaks coupled values too (jackson) | no |
  | `BASE` | the reported site itself | no |

- **Mechanism: how the sibling relates to the base bug, which is why a model skips it. Twelve
  patterns.** Nine are true sibling mechanisms (M1-M7, M9, M10). M8 and M12 are mostly variants of
  the base input. M11 is the over-broad-fix trap.

**The answer in numbers.** 471 of the 609 trap rows are siblings:

| Origin | Siblings | Siblings with per-test trial data | Missed in at least one run |
|---|---|---|---|
| Pattern A, published-fix far sites | 171 | 98 | 19 (19%) |
| Pattern B, real uncovered routes | 134 | 77 | 19 (25%) |
| Injected, planted by us | 166 | 98 | **5 (5%)** |

The other 138 rows are 73 base sites, 46 shape traps and 19 coupled traps.

**Five findings.**
1. **Planted siblings almost never bite.** 124 of the 166 injected siblings are M1 (another entry
   point to the same sink) or M2 (a second copy of the same logic). Both are routes of the concept
   the report already states. The instructions do not name the siblings (no file, function or
   field; the leak check holds), but they describe each sibling's surface in product terms. Once a model
   accepts the concept, it closes all its routes together, as round 1 already showed (sib7: 10/10).
   - Only 5 injected siblings were ever missed, 4 of them by MiMo in a single run each: mockoon T6,
     n8n T5, compliance-trestle-ds S1 and litellm-ds T7.
   - The fifth, vitest-api-fs-authz-inj S-CMD (DeepSeek 3/3), is probably a test-layer artifact.
2. **What bites is real code with a reason to dismiss.**
   - Highest miss rates, among siblings with trial data:
     - **M4 feature-absent:** 7 of 22 missed;
     - **M6 producer off the check's path:** 5 of 17;
     - **M2 second implementation:** 14 of 73;
     - **M10 wrong object:** 2 of 11.
   - Lowest: **M1 parallel entry**, 12 of 99, and **M8 parser differential** as a sibling, 1 of 18.
     M3 and M9 were never missed.
3. **The only both-model breaker uses no planted code.** jackson-databind-sib2 (both models 0/3,
   audited) is entirely Pattern B. It stacks four traps of different kinds:
   - M4: the any-setter route ignores views entirely;
   - M10+M11: an object-id stand-in property;
   - M5: an array-shaped or merge update;
   - a coupled visible value that an over-broad fix breaks.
4. **Several apparent misses are probably test artifacts.** The tests, not the model, may be wrong
   in:
   - vitest-api-fs-authz-inj: the browser-command tests call the functions directly, so they reject
     a correct guard placed at the dispatcher;
   - backstage-ds (confirmed 2026-10-19): both models fail the same 4 tests in about 10 runs. In
     DeepSeek r2 the fix was correct and no SCM read happened, but the test's mock context crashed
     (`TypeError`) before the check, and the test demands `InputError`;
   - litellm-ds: a functional test contradicts the instruction's "never";
   - prompty T2: part of the miss is a wording gap;
   - hazelcast-ds: a contract the fairfix tightened;
   - protobuf.js-ds: a coupled contract the instruction never states;
   - flowise: the 0.0 runs ran 0 or 16 of 32 tests (infrastructure).

   Re-check each before counting it.
5. **Model-built tasks read like checklists.** The DeepSeek-built (`-ds`) and MiMo-built (`-mm`)
   instructions do not name the siblings, but they describe each sibling's surface in product
   terms, often one clause per trap: typo3, yamcs, fission, gogs, theia, rsdoctor, orval, pimcore,
   olivetin. That hands the solver a list of where to look. See `BETTER-PATTERNS.md`.

---

## 2. Pattern catalogue

Each count covers sibling rows only (A-FAR, B-ROUTE or INJ). "Missed" means the sibling was missed
in at least one run with per-test data, by DeepSeek / MiMo / both. A row coded with two mechanisms
is counted under each.

| Code | Pattern | Definition: what the sibling is, relative to the base bug | Typical reason a model skips it | Siblings (A / B / INJ) | Tasks | With trial data | Missed DS / MiMo / both | Example |
|---|---|---|---|---|---|---|---|---|
| **M1** | Parallel entry point | Another handler, command, endpoint, tool, RPC or option reaches the same protected sink without the guard | "Different feature; the report is about X" | 167 (45 / 57 / 65) | 74 | 99 | 4 / 6 / 2 | prompty T2: child-prompt tool path loaded during wire projection (missed by both) |
| **M2** | Second implementation | A duplicate copy of the guarded logic: another package, fallback backend, adapter, inline copy | "That path uses its own helper" / "only a fallback" | 132 (53 / 20 / 59) | 62 | 73 | 4 / 6 / 4 | electron-builder T2: differential downloader follows redirects with every header |
| **M3** | Shared layer | The fix belongs in a lower shared primitive; the symptom shows only at the top | Fixes the caller where the symptom shows | 13 (13 / 0 / 0) | 14 | 6 | 0 / 0 / 0 | astro: low-level fetch primitives under the reported integration |
| **M4** | Feature absent | The mechanism never had the protection, so its absence reads as design | "Unsupported combination; not a security boundary" | 32 (13 / 15 / 4) | 28 | 22 | 2 / 1 / 4 | jackson any-setter has no view code (DS 6/6); hermes T4 tool-result envelope |
| **M5** | Merged or defaults route | The restricted value arrives through a defaults, merge, inheritance, patch or stored-config route | Treats the report's example fields as the whole set | 31 (17 / 6 / 8) | 26 | 14 | 1 / 0 / 1 | protobuf.js T4: `setOption` / `util.merge` treat inherited values as set |
| **M6** | Producer off the check's path | A schema, serializer, loader or config resolver feeds the check through a path the check never calls | Follows calls into the check, never asks where its data comes from | 21 (11 / 7 / 3) | 22 | 17 | 1 / 0 / 4 | mcp-ts-sdk P1: zod schema strips the issuer on reload (Hadi; DS 8/8); airflow T3 env-var spelling |
| **M7** | Ordering | Check after an adjustment, or a side effect (mkdir, delete, copy, chmod) before validation; TOCTOU | First-order check looks right | 7 (1 / 4 / 2) | 13 | 2 | 0 / 0 / 0 | flyto-core: output directory cleared before it is validated |
| **M8** | Parser differential | Canonicalisation mismatch: string prefix vs path segment, case, symlink, host spelling, nested expression | A plausible check passes the odd spelling | 24 (8 / 5 / 11), plus 45 base or shape rows | 43 | 18 | 0 / 0 / 1 | langchain: raw string-prefix allowlist (`/memories2`); airflow T10 team name with a separator |
| **M9** | Fail-open fallback | A missing authority or value falls back to "allow" | Keeps a fallback "for compatibility" | 13 (3 / 7 / 3) | 12 | 9 | 0 / 0 / 0 | portainer, seaweedfs: open default when no authenticator is set |
| **M10** | Wrong object | Authorises a neighbouring or proxy object, or trusts an attacker-chosen identity field | Copies a nearby precedent | 25 (3 / 11 / 11) | 15 | 11 | 0 / 1 / 1 | seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET |
| **M11** | Coupled contract | A linked visible value or shared helper must keep working; the natural fix breaks it | Over-broad fix | 4 sibling rows, plus 19 coupled traps | 19 | 2 (coupled traps: 15) | coupled traps: 0 / 1 / 3 | jackson: the visible type-id must still bind (broken in 4/6 runs on sib2) |
| **M12** | Input variants | Encoding, spelling, verb, protocol or role variants of a stated input | Rarely skipped: models catch these | 2, plus 44 base or shape rows | 34 | 0 | – | typo3: soft-delete and partial-update verbs |

**Origin × outcome, all 609 rows:**

| Origin | Rows | With trial data | Missed DS / MiMo / both |
|---|---|---|---|
| A-FAR (Pattern A) | 171 | 98 | 3 / 5 / 11 |
| B-ROUTE (Pattern B) | 134 | 77 | 8 / 5 / 6 |
| INJ (planted) | 166 | 98 | 1 / 4 / 0 |
| SHAPE TRAP | 46 | 28 | 3 / 1 / 2 |
| COUPLED TRAP | 19 | 15 | 0 / 1 / 3 |
| BASE | 73 | 44 | 0 / 0 / 1 |

Where the earlier catalogues fit:
- `research/round1-analysis/B-failure-modes.md` §3a ranks 8 recipes. Coupled binding = M11, merged
  or defaults = M5, neighbour precedent = M10, feature-absent = M4, post-adjustment = M7, parser
  differential = M8, missing-authority fallback = M9, shared helper = M11.
- Hadi's producer-off-path shape is M6.
- The build prompts' "Pattern A / B / injected" labels are the origin axis.

---

## 3. Counts: what was built and what bit

**Tasks covered (93), by builder:**

| Builder and generation | Tasks | Siblings (A / B / INJ) |
|---|---|---|
| Opus, round 1 hand-built (10-14/15) | 4 | 0 / 8 / 4 |
| Opus, round 2 hand-built (10-16) | 6 | 3 / 10 / 0 |
| Opus, build-v1 template, batch 1 (10-17) | 12 | 19 / 21 / 0 |
| Opus, build-v1 template, injected track (`-inj` and jenkins, 10-17/18) | 13 | 16 / 6 / 27 |
| DeepSeek-built pilot (`-ds`, 10-18/19) | 49 | 110 / 74 / 113 |
| MiMo-built pilot (`-mm`, 10-18/19) | 9 | 23 / 15 / 22 |
| **Total** | **93** | **171 / 134 / 166** |

The model-built pilot holds 135 of the 166 planted siblings. Batch 1 planted none: it is Pattern A
and B on real code.

**Every sibling that was missed in a run with per-test data** (raw, unaudited; "?" marks a suspected
test artifact):

| Task | Sibling | Origin / mechanism | Missed by | What it is |
|---|---|---|---|---|
| jackson-databind-sib | S1, S3 (+ S2 shape) | B / M4, M2 | DS 6/6 (audited) | `@JsonAnySetter` Map, method and JsonNode forms fill under a restricted view |
| jackson-databind-sib2 | S1 | B / M4 | both (audited) | the same any-setter route |
| jackson-databind-sib2 | T1 | B / M10+M11 | both (audited) | object-id generator property written through a view-less stand-in |
| jackson-databind-sib2 | T2 | B / M5 | DS | array-shaped in-place update or merge has no view check |
| jackson-databind-sib2 | C1 | COUPLED TRAP / M11 | both | the visible type-id must still bind |
| mcp-ts-sdk-oauth (Hadi's original) | P1 | A / M6 | DS 8/8 | zod schemas strip the issuer, so a reloaded credential passes |
| airflow-ds, airflow-info-exposure-inj | T3 | A / M6 | both | config loader's team env-var spelling |
| airflow-ds | T10 | SHAPE TRAP / M8 | both | team name containing a separator |
| airflow-* | T5, T6, T7 | SHAPE TRAP, B / M12, M2 | DS or MiMo | per-key backend kwargs; start-up masker; `_cmd` / `_secret` forms |
| backstage-ds | T4, T5 | A / M2, M6 | both, ? | `fetch:template` actions read SCM content with integration credentials |
| compliance-trestle-ds | S1 | INJ / M10 | MiMo, once | inheritance-view folder name joined under the checked output |
| electron-builder-* | T2 | B / M2 | both | differential-download redirects keep credentials |
| electron-builder-* | T3, T4 | A / M4 | both | free-text secret redaction: debug body, error text, child-command output |
| ghost-ds | T2, T3 | A / M1, M8 | MiMo; both | remote media inliner; direct upload trusts extension and mimetype |
| flyto-core-path-traversal | T8 | SHAPE TRAP / M8 | both, once | qrcode `.png` → `.svg` rewrite after the check |
| hazelcast-ds | nested_positions, record_implementation | A / M1, M2 | MiMo, ? | nested readers and the record serializer instantiate restricted types |
| hermes-agent-ds | T4, T7 | A / M4; B / M2 | both | tool-result untrusted envelope; Codex MCP projector |
| litellm-ds | T2, T5, T7 | A / M2; B / M1; INJ / M2 | MiMo r1 only, ? | image, queue and moderation routes |
| mockoon-ds | T6 | INJ / M1 | MiMo, once | management WebSocket stream outside the Express auth layer |
| n8n-ds | T5 | INJ / M1 | MiMo, once | attachment-by-path option |
| prompty-path-read-inj, prompty-ds | T2 | B / M1 | both, ? | child-prompt tool path loaded during wire projection |
| protobuf.js-ds | T3, T4, T7 (+ R2) | A / M6, M5, M2 | both, ? | enum table, option merge and generated table inherit `Object.prototype` |
| siyuan-ds | T3, T6 | A / M1+M4; B / M1 | DS | template export; marketplace listings for readers |
| vitest-api-fs-authz-inj | A-FAR, S-CMD | A / M2; INJ / M1 | DS 3/3, MiMo 1/3, ? | browser-mode file commands (test calls the functions, not the dispatcher) |

**Breaker status.** Only jackson-databind-sib2 is an audited both-model breaker.
- **Single-model leads:**
  - vitest-api-fs-authz-inj (DS-only; probably an artifact);
  - prompty-path-read-inj (MiMo-only; fairness NOT READY);
  - airflow-info-exposure-inj (MiMo 0/3, with an over-broad functional failure every run);
  - electron-builder-credential-leakage (MiMo 0.8 / 0.9 / 0.8);
  - stigmem (round 1, no sibling).
- **Possible new both-model leads:** litellm-ds (both 0.0, but a fairness defect) and backstage-ds
  (both around 0.91, suspected artifact). Neither is confirmed.

---

## 4. How the symptom points to the sibling

Every build brief uses the same contract between the report and the siblings:
- **The report shows one impact through the base route only:** one actor, one trigger, one example.
- **Invariants state the property abstractly**, wide enough to cover every sibling. Examples:
  - "No argument of any agent tool that names a file … whatever the path's spelling or wherever it
    ultimately resolves";
  - "including credentials saved earlier";
  - "whatever the operation is called, whichever fields it carries, and whoever invokes it".
- **Must-keep-working clauses** ("works exactly as today") cover the coupled traps.
- **Never** a file, function, field or CVE name (`manifest.leak_terms`), and never the sibling's
  mechanism.

So the link from symptom to sibling is always **the invariant, not the example**. A solver must read
"every route that ends in this sink" and go looking.

**What decides the outcome is how much work the invariant leaves to the solver:**
- **Siblings that bite:** the invariant covers them only by implication, and the code gives a
  plausible reason to call them out of scope.
  - jackson: "upstream never supported views on any-setters";
  - Hadi: the data arrives through a reload the check never calls;
  - hermes: tool results look already trusted.
- **Siblings that do not bite:**
  - the invariant enumerates them ("create, change, remove or re-activate", "as a tool argument, a
    request parameter, or a location recorded in a run's own data");
  - or they are one more route of a concept the solver has already accepted.

Each task in §6 quotes its impact sentence and its covering invariants, and fills the column "What in
the symptom or invariant points to it" for every trap.

---

## 5. Every task at a glance

Columns:
- **Built by:** R1 / R2 = Opus hand-built in rounds 1 and 2; B1 = Opus build-v1 batch 1; inj = Opus
  build-v1 injected track; DeepSeek / MiMo = model-built pilot.
- **Gate:** SOUND / UNSOUND from the pipeline's `.sound` / `.unsound` markers; pass / FAIL from
  `gate_report.json`.
- **DS raw / MiMo raw:** chronological rewards from the run logs (1 = solved); they include runs
  from before a fairfix.
- **Siblings missed:** traps missed by DeepSeek, MiMo or both, in runs with per-test data or with
  audits.

| # | Task | Built by | Siblings A / B / INJ (+shape traps, coupled traps) | Main sibling mechanisms | Gate | Fairness | DS raw | MiMo raw | Siblings missed (who) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [jackson-databind-sib](#jackson-databind-sib) | Opus R1 | 0 / 2 / 0 (+1, +2) | M4, M2 | pass | – | 0 0 .62 | 0 | S1 (DS); S2 (DS); S3 (DS); C1 (both) |
| 2 | [jackson-sib7](#jackson-sib7) | Opus R1 | 0 / 3 / 0 (+2, +2) | M4, M2, M1 | pass | – | – | 1 | S1 (DS); S2 (DS); S3 (DS); S4 (DS); S5 (DS); C1 (both) |
| 3 | [rclone-sib](#rclone-sib) | Opus R1 | 0 / 0 / 4 (+0, +1) | M2×4 | pass | – | 1 | 1 .82 1 1 | C1 (MiMo) |
| 4 | [russh-sib](#russh-sib) | Opus R1 | 0 / 3 / 0 (+2, +2) | M1×3 | pass | – | 1 | – | none |
| 5 | [jackson-databind-sib2](#jackson-databind-sib2) | Opus R2 | 0 / 3 / 0 (+0, +1) | M4, M11, M10, M5 | pass | READY | 0 0 0 .58 | 0 0 0 .58 0 | S1 (both); C1 (both); T1 (both); T2 (DS) |
| 6 | [jackson-databind-readonly](#jackson-databind-readonly) | Opus R2 | 0 / 1 / 0 (+0, +2) | M6, M4 | pass | READY | 1 | 1 | none |
| 7 | [marshmallow-readonly-sib](#marshmallow-readonly-sib) | Opus R2 | 0 / 2 / 0 (+0, +1) | M4, M1 | pass | NOT READY | 1 | 0 1 | none |
| 8 | [class-transformer-exclude-sib](#class-transformer-exclude-sib) | Opus R2 | 0 / 2 / 0 (+0, +0) | M4, M10 | – | – | – | – | not trialled |
| 9 | [better-auth-sso-endpoints](#better-auth-sso-endpoints) | Opus R2 | 2 / 0 / 0 (+1, +1) | M5×2 | pass | READY | 1 | 1 | none |
| 10 | [mcp-ts-sdk-oauth](#mcp-ts-sdk-oauth) | Opus R2 | 1 / 2 / 0 (+1, +1) | M6, M1, M9 | FAIL | READY | – | – | P1 (DS) |
| 11 | [airflow-ds](#airflow-ds) | DeepSeek | 3 / 2 / 2 (+2, +0) | M1×2, M2×2, M3, M6 | SOUND | NOT READY | .97 1 | 0 | T3_env_var_spelling (both); T7_per_key_backend_kwargs (MiMo); T10_arbitrary_team_name (both) |
| 12 | [airflow-info-exposure-inj](#airflow-info-exposure-inj) | Opus inj | 3 / 2 / 2 (+1, +0) | M1×2, M2×2, M3, M6 | – | – | .95 0 1 | 0 0 0 | T3_env_var_spelling (both); T5_cmd_secret_shapes (MiMo); T6_log_redaction (MiMo); T7_per_key_backend_kwargs (DS) |
| 13 | [arc-ds](#arc-ds) | DeepSeek | 0 / 2 / 2 (+1, +0) | M1×3, M5, M2 | SOUND | – | 1 | 1 | none |
| 14 | [astro-csrf-origin](#astro-csrf-origin) | Opus B1 | 2 / 0 / 0 (+1, +1) | M1, M3 | pass | NOT READY | 1 | 1 | none |
| 15 | [astro-ds](#astro-ds) | DeepSeek | 2 / 0 / 3 (+1, +1) | M1×2, M2×2, M3 | UNSOUND | – | – | – | not trialled |
| 16 | [backstage-ds](#backstage-ds) | DeepSeek | 4 / 0 / 2 (+0, +0) | M2×5, M6 | SOUND | READY | 1 .91 .91 | .91 | T4 (both); T5 (both) |
| 17 | [ckan-mcp-server-ds](#ckan-mcp-server-ds) | DeepSeek | 2 / 0 / 2 (+0, +0) | M1×2, M2, M9 | SOUND | – | 1 | 1 | none |
| 18 | [compliance-trestle-ds](#compliance-trestle-ds) | DeepSeek | 2 / 3 / 3 (+0, +0) | M1×4, M3, M6, M7 | SOUND | – | 0 1 | 0 1 | S1 (MiMo) |
| 19 | [compliance-trestle-mm](#compliance-trestle-mm) | MiMo | 2 / 4 / 3 (+0, +0) | M1×2, M10×2, M3, M6 | – | – | – | – | not trialled |
| 20 | [compliance-trestle-path-traversal](#compliance-trestle-path-traversal) | Opus B1 | 2 / 3 / 0 (+0, +0) | M1×2, M3, M6, M7 | pass | NOT READY | 1 | 1 | none |
| 21 | [composer-symlink-path-inj](#composer-symlink-path-inj) | Opus inj | 1 / 0 / 2 (+1, +0) | M2×3 | – | – | 1 1 1 | 1 1 1 | none |
| 22 | [coreutils-ds](#coreutils-ds) | DeepSeek | 0 / 1 / 2 (+0, +0) | M2, M1, M8 | UNSOUND | – | – | – | not trialled |
| 23 | [django-cms-ds](#django-cms-ds) | DeepSeek | 2 / 3 / 3 (+0, +0) | M10×4, M6×2, M1, M3 | SOUND | – | 1 | 1 | none |
| 24 | [django-cms-object-level](#django-cms-object-level) | Opus B1 | 1 / 2 / 0 (+0, +0) | M1, M6, M2 | pass | NOT READY | 1 | 1 | none |
| 25 | [docling-file-disclosure](#docling-file-disclosure) | Opus B1 | 0 / 2 / 0 (+3, +0) | M1×2 | pass | READY | 1 | 1 | none |
| 26 | [ec2-fleet-plugin-ds](#ec2-fleet-plugin-ds) | DeepSeek | 2 / 0 / 2 (+1, +0) | M1×2, M2, M8 | SOUND | – | 1 | 1 | none |
| 27 | [jenkins-ec2fleet-authz-inj](#jenkins-ec2fleet-authz-inj) | Opus inj | 2 / 0 / 2 (+1, +0) | M1×2, M2, M8 | – | NOT READY | 1 1 1 | 1 1 1 | none |
| 28 | [electron-builder-credential-leakage](#electron-builder-credential-leakage) | Opus B1 | 1 / 1 / 0 (+0, +0) | M2, M4 | FAIL | NOT READY | 1 | .80 .90 .80 | T2 (MiMo); T3 (MiMo) |
| 29 | [electron-builder-ds](#electron-builder-ds) | DeepSeek | 2 / 1 / 3 (+0, +0) | M2×3, M4×3 | SOUND | READY | .88 .69 .88 .88 .75 .94 | .62 1 | T2_block_based_download_redirects (both); T3_runtime_redaction (both); T4_build_config_redaction (both) |
| 30 | [fission-ds](#fission-ds) | DeepSeek | 2 / 1 / 3 (+0, +0) | M1×3, M5, M7, M8 | SOUND | – | 1 | 1 | none |
| 31 | [fission-podspec-passthrough](#fission-podspec-passthrough) | Opus B1 | 2 / 1 / 0 (+0, +0) | M1×2, M5 | pass | NOT READY | 1 | 1 | none |
| 32 | [flowise-cross-tenant-inj](#flowise-cross-tenant-inj) | Opus inj | 0 / 1 / 2 (+0, +0) | M1×3 | FAIL | NOT READY | 0 1 | 0 0 0 | none |
| 33 | [flowise-ds](#flowise-ds) | DeepSeek | 1 / 1 / 2 (+0, +0) | M1×4 | SOUND | – | 0 0 1 | 0 1 | none |
| 34 | [ghost-ds](#ghost-ds) | DeepSeek | 2 / 0 / 2 (+0, +0) | M1×2, M8, M2 | SOUND | NOT READY | 1 | .86 .86 1 | T2 (MiMo); T3 (both) |
| 35 | [gogs-ds](#gogs-ds) | DeepSeek | 0 / 2 / 2 (+0, +0) | M2×2, M4, M1 | SOUND | – | 1 | 1 | none |
| 36 | [flyto-core-path-traversal](#flyto-core-path-traversal) | Opus B1 | 2 / 4 / 0 (+4, +0) | M1×4, M4, M8 | pass | NOT READY | .96 1 | .96 1 | T8 (both) |
| 37 | [flyto-core-ds](#flyto-core-ds) | DeepSeek | 3 / 6 / 3 (+0, +0) | M1×6, M4×2, M10×2, M8 | UNSOUND | – | – | – | not trialled |
| 38 | [flyto-core-mm](#flyto-core-mm) | MiMo | 3 / 5 / 3 (+4, +0) | M1×7, M4×2, M8, M10 | – | – | – | – | not trialled |
| 39 | [grav-info-exposure-inj](#grav-info-exposure-inj) | Opus inj | 0 / 0 / 2 (+0, +0) | M2×2 | FAIL | NOT READY | 1 1 1 | 1 1 1 | none |
| 40 | [grav-ds](#grav-ds) | DeepSeek | 0 / 2 / 3 (+0, +0) | M2×3, M1, M6 | SOUND | – | 1 | 1 | none |
| 41 | [grav-mm](#grav-mm) | MiMo | 0 / 2 / 2 (+0, +0) | M2×2, M1, M6 | – | – | – | – | not trialled |
| 42 | [handlebars-path-read-inj](#handlebars-path-read-inj) | Opus inj | 1 / 0 / 2 (+1, +0) | M2×2, M1 | – | – | – | – | not trialled |
| 43 | [hazelcast-ds](#hazelcast-ds) | DeepSeek | 3 / 3 / 2 (+0, +0) | M9×5, M2×2, M1 | SOUND | NOT READY | 1 1 | .84 .79 | nested_positions (MiMo); record_implementation (MiMo) |
| 44 | [hermes-agent-ds](#hermes-agent-ds) | DeepSeek | 3 / 3 / 2 (+0, +0) | M2×3, M1×3, M5, M4 | SOUND | – | .54 .62 1 | .92 0 .62 | T1_context_scanner (both); T4_tool_envelope (both); T7_codex_mcp (both) |
| 45 | [hubuum-client-rust-ds](#hubuum-client-rust-ds) | DeepSeek | 3 / 3 / 2 (+0, +0) | M4×5, M2×2, M1 | SOUND | – | 1 | 1 | none |
| 46 | [jetty.project-ds](#jettyproject-ds) | DeepSeek | 1 / 1 / 2 (+0, +0) | M2×4 | SOUND | – | 1 | 1 | none |
| 47 | [keras-ds](#keras-ds) | DeepSeek | 2 / 2 / 2 (+1, +0) | M2×4, M1, M9 | UNSOUND | – | – | – | not trialled |
| 48 | [knowns-ds](#knowns-ds) | DeepSeek | 4 / 0 / 3 (+0, +0) | M2×3, M1×2, M5×2 | UNSOUND | – | – | – | not trialled |
| 49 | [knowns-mm](#knowns-mm) | MiMo | 3 / 0 / 2 (+0, +0) | M2×2, M1×2, M5 | – | – | – | – | not trialled |
| 50 | [langchain-path-escape-inj](#langchain-path-escape-inj) | Opus inj | 3 / 0 / 2 (+0, +0) | M8×4, M2 | FAIL | NOT READY | 1 | 1 | none |
| 51 | [langchain-ds](#langchain-ds) | DeepSeek | 3 / 0 / 4 (+0, +0) | M8×6, M2 | SOUND | – | 1 | 1 | none |
| 52 | [limesurvey-ds](#limesurvey-ds) | DeepSeek | 2 / 1 / 2 (+1, +0) | M1×5 | SOUND | – | 1 | 1 | none |
| 53 | [litellm-ds](#litellm-ds) | DeepSeek | 3 / 1 / 2 (+0, +0) | M2×2, M6×2, M8×2, M5 | SOUND | – | 0 0 0 | 0 0 | T2_image_second_implementation (MiMo); T5_queue_route (MiMo); T7_moderation_path_model (MiMo) |
| 54 | [mcp-atlassian-path-inj](#mcp-atlassian-path-inj) | Opus inj | 2 / 0 / 3 (+0, +0) | M2×4, M4 | – | – | 1 1 0 | 0 1 1 | none |
| 55 | [mcp-atlassian-ds](#mcp-atlassian-ds) | DeepSeek | 2 / 0 / 3 (+0, +0) | M2×4, M4 | SOUND | – | 1 | 0 0 1 | none |
| 56 | [mcp-atlassian-mm](#mcp-atlassian-mm) | MiMo | 2 / 0 / 3 (+0, +0) | M2×4, M4 | UNSOUND | – | – | – | not trialled |
| 57 | [mockoon-ds](#mockoon-ds) | DeepSeek | 4 / 0 / 2 (+0, +0) | M2×2, M1×2, M4, M11 | SOUND | – | 1 | .96 1 | T6 (MiMo) |
| 58 | [n8n-ds](#n8n-ds) | DeepSeek | 1 / 1 / 2 (+1, +0) | M2×2, M1×2 | SOUND | – | 1 1 1 | .88 1 1 | T5_injected_attachment_path (MiMo) |
| 59 | [new-api-ds](#new-api-ds) | DeepSeek | 2 / 1 / 3 (+0, +0) | M1×4, M4, M2 | SOUND | – | 1 | 1 | none |
| 60 | [nhost-cors-auth](#nhost-cors-auth) | Opus B1 | 2 / 0 / 0 (+1, +2) | M6, M1 | FAIL | NOT READY | 1 | 1 | none |
| 61 | [olivetin-allowlist-inj](#olivetin-allowlist-inj) | Opus inj | 1 / 0 / 2 (+0, +0) | M7, M1, M2 | – | – | – | – | not trialled |
| 62 | [openbao-ds](#openbao-ds) | DeepSeek | 3 / 0 / 2 (+2, +0) | M2×4, M1 | – | – | – | – | not trialled |
| 63 | [openbao-mm](#openbao-mm) | MiMo | 3 / 0 / 2 (+2, +0) | M2×4, M1 | – | – | – | – | not trialled |
| 64 | [orval-ds](#orval-ds) | DeepSeek | 6 / 6 / 2 (+0, +0) | M2×10, M1×2, M3, M5 | UNSOUND | – | – | – | not trialled |
| 65 | [pimcore-ds](#pimcore-ds) | DeepSeek | 1 / 1 / 3 (+0, +0) | M1×2, M3, M2, M4 | UNSOUND | – | – | – | not trialled |
| 66 | [portainer-ds](#portainer-ds) | DeepSeek | 2 / 0 / 2 (+0, +0) | M1×3, M2, M9, M6 | SOUND | – | 1 0 1 | 0 0 1 | none |
| 67 | [prompty-path-read-inj](#prompty-path-read-inj) | Opus inj | 0 / 1 / 2 (+0, +0) | M1×2, M5 | FAIL | NOT READY | .83 1 | .83 .83 .83 | T2 (both) |
| 68 | [prompty-ds](#prompty-ds) | DeepSeek | 0 / 1 / 4 (+0, +0) | M1×3, M5, M6 | SOUND | – | .87 1 | .87 .87 1 | T2 (both) |
| 69 | [prompty-mm](#prompty-mm) | MiMo | 1 / 2 / 3 (+0, +0) | M1×4, M2, M5 | – | – | – | – | not trialled |
| 70 | [protobuf.js-ds](#protobufjs-ds) | DeepSeek | 6 / 2 / 2 (+0, +0) | M2×4, M1×2, M5×2, M6 | SOUND | – | .89 0 0 | 0 0 0 | T3 (both); T4 (both); T7 (both); R2 (MiMo) |
| 71 | [protobuf.js-mm](#protobufjs-mm) | MiMo | 7 / 0 / 2 (+0, +0) | M2×4, M1×2, M6, M5 | – | – | – | – | not trialled |
| 72 | [rsdoctor-ds](#rsdoctor-ds) | DeepSeek | 4 / 0 / 2 (+0, +1) | M2×2, M8, M3, M1 | – | – | – | – | not trialled |
| 73 | [seaweedfs-s3tables-authz](#seaweedfs-s3tables-authz) | Opus B1 | 2 / 3 / 0 (+0, +0) | M10×4, M9, M2 | FAIL | NOT READY | 1 | 1 | none |
| 74 | [seaweedfs-ds](#seaweedfs-ds) | DeepSeek | 2 / 4 / 3 (+0, +0) | M10×6, M9, M2, M7 | – | – | – | – | not trialled |
| 75 | [siyuan-ds](#siyuan-ds) | DeepSeek | 3 / 2 / 2 (+1, +0) | M1×6, M9, M4 | SOUND | – | 0 0 .94 | 1 | T3_templates_export (DS); T6_marketplace_listings (DS) |
| 76 | [summarize-ds](#summarize-ds) | DeepSeek | 1 / 2 / 2 (+0, +0) | M1×4, M2, M8 | SOUND | – | – | – | not trialled |
| 77 | [suneditor-xss-inj](#suneditor-xss-inj) | Opus inj | 1 / 2 / 2 (+0, +0) | M4×2, M8×2, M2 | – | – | 1 1 1 | 1 0 1 | none |
| 78 | [surrealdb-ds](#surrealdb-ds) | DeepSeek | 2 / 2 / 1 (+1, +0) | M1×2, M11, M5, M4 | SOUND | – | – | – | not trialled |
| 79 | [theia-ds](#theia-ds) | DeepSeek | 5 / 3 / 2 (+0, +0) | M5×6, M1×2, M3, M4 | UNSOUND | – | – | – | not trialled |
| 80 | [tinacms-ds](#tinacms-ds) | DeepSeek | 2 / 0 / 3 (+0, +0) | M2×3, M1×2, M4 | UNSOUND | – | – | – | not trialled |
| 81 | [traefik-header-name](#traefik-header-name) | Opus B1 | 1 / 4 / 0 (+1, +0) | M1×3, M2, M11 | pass | NOT READY | 1 | 1 | none |
| 82 | [traefik-ds](#traefik-ds) | DeepSeek | 1 / 5 / 2 (+1, +0) | M1×3, M2×2, M8×2, M11 | – | – | – | – | not trialled |
| 83 | [trivy-path-traversal-inj](#trivy-path-traversal-inj) | Opus inj | 1 / 0 / 2 (+0, +0) | M1×2, M5 | FAIL | NOT READY | 1 | 1 | none |
| 84 | [trivy-ds](#trivy-ds) | DeepSeek | 2 / 0 / 1 (+1, +0) | M1×2, M5 | UNSOUND | – | – | – | not trialled |
| 85 | [typo3-ds](#typo3-ds) | DeepSeek | 2 / 1 / 1 (+1, +0) | M12×2, M1, M11, M2 | SOUND | – | – | – | not trialled |
| 86 | [vibe-trading-path-read](#vibe-trading-path-read) | Opus B1 | 3 / 1 / 0 (+2, +0) | M1×2, M2, M6 | pass | NOT READY | 0 1 | 1 | none |
| 87 | [vibe-trading-ds](#vibe-trading-ds) | DeepSeek | 3 / 1 / 3 (+2, +0) | M1×3, M2, M6, M5 | – | – | – | – | not trialled |
| 88 | [vitest-api-fs-authz-inj](#vitest-api-fs-authz-inj) | Opus inj | 1 / 0 / 2 (+0, +0) | M1×2, M2 | FAIL | NOT READY | .62 .62 .62 | 1 1 .62 | A-FAR (DS); S-CMD (DS) |
| 89 | [vitest-ds](#vitest-ds) | DeepSeek | 2 / 1 / 2 (+0, +0) | M1×3, M2, M9 | SOUND | – | 1 | – | none |
| 90 | [vitest-mm](#vitest-mm) | MiMo | 2 / 2 / 2 (+0, +0) | M9×2, M1×2, M2, M5 | – | – | – | – | not trialled |
| 91 | [whistle-cwe-path](#whistle-cwe-path) | Opus B1 | 1 / 0 / 0 (+0, +1) | M1, M4 | pass | NOT READY | 1 | 1 | none |
| 92 | [whistle-ds](#whistle-ds) | DeepSeek | 0 / 1 / 2 (+0, +0) | M10×3, M1×2 | SOUND | – | 1 | 0 1 | none |
| 93 | [yamcs-ds](#yamcs-ds) | DeepSeek | 3 / 2 / 2 (+0, +0) | M1×5, M10, M2 | UNSOUND | – | – | – | not trialled |

---

## 6. Per-task detail

The blocks run in the order of the §5 table:
- round-1 and round-2 hand-built tasks first;
- then the rest, alphabetically by host, with each host's builds side by side.

In each table, the trap columns hold the origin and mechanism codes from §1-§2.

### jackson-databind-sib
**Host / advisory:** FasterXML jackson-databind @ d627a8a, GHSA-mhm7-754m-9p8w, CWE-863, Java · **Built by:** Opus hand-built, round 1 (10-14/15) · **Pattern label:** none (manifest `pattern: None`; 0 structured traps, ids assigned here from notes.md / B-failure-modes) · **Traps:** 5 (3 sibling forms + 2 coupled)
**Base bug:** `@JsonView` is not honoured on the external-type-id polymorphic path (`deser/impl/ExternalTypeHandler`); a property restricted to AdminView is bound under PublicView. The report leads straight there (sibling-discriminator example).
**Symptom as reported:** "the privilege check is silently skipped on this binding path, so the restricted value is bound anyway." Invariant covering the siblings: a hidden property "must never be populated from the input — on **every** binding path … and any mechanism by which otherwise-unmapped input can still be routed into a restricted property." Coupled: "Properties that *are* visible … must continue to bind even when a sibling value on the same object is hidden, and a property that carries no view restriction at all must keep binding." All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| S1 | B-ROUTE | M4 | Nothing planted: admin-only `@JsonAnySetter` Map field collects unknown keys under PublicView (`deser/SettableAnyProperty.deserializeAndSet`, 0 `View` references in the file) | Same rule, different binding mechanism the upstream fix never touched | The mechanism has no view code at all, so it reads as unsupported ("no view matcher … out of scope", "a grader can't test it") | "any mechanism by which otherwise-unmapped input can still be routed into a restricted property" |
| S2 | SHAPE TRAP | M12 | Same gap, any-setter as a two-arg setter method (same `deserializeAndSet` site) | Declaration-form variant of S1 | Falls with S1 | same clause |
| S3 | B-ROUTE | M2 | Same gap, JsonNode any-setter field (`JsonNodeFieldAnyProperty.deserializeAndSet` override) | Override that bypasses a guard placed in the base method | Falls with S1 if the concept is accepted | same clause |
| C1 | COUPLED TRAP | M11 | Functional: the visible type-id creator param `kind` must still bind when `asset` is hidden (ExternalTypeHandler entry binds both) | Same handler entry as the base flaw | Skipping the whole ext-typed entry hides the value and silently drops the visible id | "visible … must continue to bind even when a sibling value on the same object is hidden" |
| C2 | COUPLED TRAP | M11 | Functional: admin/no-view catch-all still fills; a catch-all with no `@JsonView` keeps binding under PublicView (`disable_feature.patch` = functional_fail) | Over-restriction guard for S1-S3 | Easiest S1 fix is "drop all extras when any view is active" | "a property that carries no view restriction at all must keep binding under any active view" |

**Outcome:** gate PASSED (no fairness review on record). Bundle raw: DS 0.0, 0.0, 0.625; MiMo 0.0. Ledger (audited): DS **failed 0/6** (0.625, 0.625, 0, 0, 0, 0.625); MiMo SOLVED 1/2 (+1 provider stop). DS missed S1-S3 in 6/6 runs (saw `SettableAnyProperty` in the first minute and dismissed it); 3 DS runs (the 0.0s: DHJMrS9, pe7cTre, tFp6yZg) also broke C1. MiMo yWRg48p (0.0) closed S1-S3 but broke C1; pvqkL7s solved. No per-test file in the bundle; mapping from B-failure-modes §1.1.
**Read:** S1 is a genuinely different concept to the models (feature absent → "design"), and it beat DS consistently; MiMo probes and reproduced the leak, so it falls. S2/S3 are forms of one concept and fall together. Realistic: nothing planted.

### jackson-sib7
**Host / advisory:** FasterXML jackson-databind @ d627a8a, GHSA-mhm7-754m-9p8w, CWE-863, Java · **Built by:** Opus hand-built, round 1 · **Pattern label:** none (0 structured traps; S1-S5 ids come from the manifest `sibling_paths`) · **Traps:** 7 (5 siblings + 2 coupled)
**Base bug:** same as jackson-databind-sib (`ExternalTypeHandler` ignores the active view); the report leads to that path.
**Symptom as reported:** same impact text as jackson-databind-sib. The invariant adds: "whether that collection point is declared as a field, as a setter method, or as a constructor parameter, and whatever its declared type … neither is closing only the paths that bind a value directly onto an already-constructed object while leaving the paths that gather input during construction open." This sentence paraphrases the sibling forms (B-failure-modes §4: the wording leak).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| S1 | B-ROUTE | M4 | Nothing planted: admin-only any-setter Map field (`SettableAnyProperty.deserializeAndSet`, guard site 1) | Same rule, mechanism with no view code | Absence reads as design | "any mechanism by which otherwise-unmapped input …", "declared as a field" |
| S2 | SHAPE TRAP | M12 | Any-setter as two-arg setter method (guard site 1) | Form variant of S1 | Falls with S1 | "as a setter method" |
| S3 | B-ROUTE | M2 | JsonNode any-setter field (`JsonNodeFieldAnyProperty.deserializeAndSet` override, guard site 2) | Override bypassing a base-method guard | Falls with S1 | "whatever its declared type" |
| S4 | B-ROUTE | M1 | Map constructor-parameter any-setter: `BeanDeserializer._deserializeUsingPropertyBased` → `bufferAnyParameterProperty`, never calls `deserializeAndSet` (guard site 3) | Different invocation route of the same mechanism | A guard in `deserializeAndSet` looks complete (the sib reference = `partial_fix.patch`) | "as a constructor parameter", "paths that gather input during construction" |
| S5 | SHAPE TRAP | M12 | JsonNode constructor-parameter any-setter (guard site 3) | Value-type variant of S4 | Falls with S4 | same |
| C1 | COUPLED TRAP | M11 | Functional: visible type-id creator param must bind when the value is hidden (inherited) | Same handler entry as the base | Skipping the whole entry drops the visible id | "visible … continue to bind even when a sibling value … is hidden" |
| C2 | COUPLED TRAP | M11 | Functional: admin/no-view/un-annotated catch-alls (field and ctor-param) keep binding (`disable_feature.patch`) | Over-restriction guard for S1-S5 | Drop-all-extras fix | "no view restriction at all must keep binding" |

**Outcome:** gate PASSED. Bundle raw: DS none recorded; MiMo 1.0. Ledger: DS SOLVED 1/4 (+4 ungraded), MiMo SOLVED 1/2 (+1 ungraded) → rejected. DS found the siblings in 10/11 runs; one DS run (eemmJfp) printed the leak and still left all 5 open (S1-S5). Three sib7 runs (azQQS2U, mGjGeey, fkF5qrx; both models) broke C1. No per-test file in the bundle.
**Read:** S1-S5 are routes of one accepted concept and fell together whenever the concept was accepted (DS 10/10, MiMo 3/3). The added creator route did not add difficulty, and the wording leak removed the class-A dismissal that made the sib version work.

### rclone-sib
**Host / advisory:** rclone @ b3cf044, GHSA-xwwr-4h3p-r22c, CWE-287, Go · **Built by:** Opus hand-built, round 1 · **Pattern label:** none (0 structured traps; ids assigned here from the manifest `variants`) · **Traps:** 5 (4 injected + 1 coupled)
**Base bug:** `serve s3 --auth-proxy` verifies the SigV4 signature against an empty secret when the proxy supplies none, so knowing an access key ID is enough (`cmd/serve/s3` + `cmd/serve/proxy`).
**Symptom as reported:** "a request is accepted if its signature was computed with an **empty** secret" and "On the username/password surfaces, a client that presents a **valid username** is accepted even when the password is wrong or empty." Invariant: accept "**only** when the secret or password … verifies against the real secret … This must hold on every affected serve surface"; the proxy's `_secret_access_key` field is named. All four protocol surfaces (S3, HTTP, FTP, SSH) are named in the summary, so the siblings are stated outright.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| S1 | INJ | M2 | Single-user basic auth no longer compares the password (`lib/http`, `serve http --user/--pass`) | Same CWE-287 class, separate credential check per surface | Hardly any: the surface is named and the missing compare is visible | "every affected serve surface", "username/password surfaces" |
| S2 | INJ | M2 | htpasswd check accepts any listed user regardless of password (`lib/http` htpasswd) | Second implementation inside the HTTP surface | Could be missed if only `--user/--pass` is fixed | same |
| S3 | INJ | M2 | FTP credential check drops the password comparison (`cmd/serve/ftp`) | Separate per-protocol check | None; named | "an FTP service" |
| S4 | INJ | M2 | SSH password callback no longer compares the password (`cmd/serve/sftp`) | Separate per-protocol check | None; named | "an SSH (sftp) service" |
| C1 | COUPLED TRAP | M11 | Functional + security: the correct secret/password is still served on every verb (S3 PUT/GET/DELETE, FTP/SFTP list/download/upload); refuse-all patches fail | Guards the base's missing-secret fix and the sibling fixes against refuse-all | Under an unstated proxy contract MiMo refused everyone (I1/I2) | "A client that presents the correct secret … must still be served"; "rejects correctly authenticated clients is not an acceptable fix" |

**Outcome:** gate PASSED (2026-10-16 repair gate also PASSED). Bundle raw: DS 1.0; MiMo 1.0, 0.8182, 1.0, 1.0. Ledger: both SOLVED (+6 task-leaked runs each, excluded). The MiMo 0.8182 run (StBjAQQ) is the refuse-all-in-proxy-mode run (B-failure-modes I1, before the 01:57 instruction fix, not counted), so C1 was hit, not a sibling. No sibling missed in any counted run; regraded solves stayed 1.0.
**Read:** the injected siblings are the same concept on surfaces the report names. They add volume, not difficulty ("protocol siblings": always fixed). They are also recoverable by diffing against public upstream, a realism and leak concern. The only real lever was the missing-authority contract (M9 base / refuse-all C1), and that came from unstated wording.

### russh-sib
**Host / advisory:** russh @ 3430fd2, GHSA-p8qx-h547-fjw9 (CVE-2026-102822), CWE-287/345/354, Rust · **Built by:** Opus hand-built, round 1 · **Pattern label:** none (0 structured traps; ids assigned here from the manifest `siblings` and 10-16 repair) · **Traps:** 7 (5 sibling/variant + 2 coupled)
**Base bug:** algorithm agreement accepts `mac=none` with a MAC-requiring block cipher (CTR/CBC/3DES), giving an integrity-free session; the upstream fix hardened MAC selection in the shared handshake routine.
**Symptom as reported:** a peer can steer the handshake into "a session that carries **no confidentiality, no integrity, and/or no server authentication**"; all three routes are listed ("No key agreement…", "Plaintext with no integrity", "Integrity silently dropped"). Invariant: refuse "the null key exchange, or … a cipher that provides no integrity of its own … in **either** direction". Every sibling is named; no fairness gap.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| S1 | B-ROUTE | M1 | Nothing planted: `kex::NONE` (`skip_exchange()`) is selectable; no DH, no host-key signature (KEX stage, shared handshake) | Other negotiation stage reaching "unprotected session" | Little: the instruction names it | "steer key exchange to the `none` exchange" |
| S2 | B-ROUTE | M1 | `cipher::NONE`/`CLEAR` map to `Clear` with `needs_mac()==false`, so the upstream MAC refusal never fires (CIPHER stage) | Same sink; the base guard's predicate excludes it | A port of the upstream `needs_mac` check looks complete | "the `none`/`clear` (no-encryption) cipher while the MAC choice is `none`" |
| S3 | SHAPE TRAP | M12 | Role/direction variants: library on one side only vs a vulnerable-commit peer (`legacy_*` tests; client/server `select` are separate) | Same checks in both roles | Fixing one role only | "in **either** direction"; "whichever side makes the offending offer" |
| S4 | SHAPE TRAP | M12 | Cipher-name variants: 3des-cbc, aes128-ctr/cbc, aes192-ctr, `clear` alias | Variants of the base and S2 | Fixing only named ciphers (`named_ciphers_only.patch`) | "the CTR and CBC family, and triple-DES" |
| S5 | B-ROUTE | M1 | Re-key to the null kex on an established session (client side) | S1 in a later handshake phase | Refusing null kex only on the initial exchange | "A handshake that would settle on the null key exchange" |
| C1 | COUPLED TRAP | M11 | Functional: AEAD (aes-gcm, chacha20-poly1305) with `mac=none` must still connect; mlkem kex uses aes-gcm+none | Over-broad fix bans mac=none everywhere (`disable_feature.patch`) | Simplest blanket fix | "pairing one of them with the null MAC is valid and must still connect" |
| C2 | COUPLED TRAP | M11 | Functional: a real re-key keeps the session; legacy default peers interoperate | Guards S5 fixes that refuse every re-key | Refuse-all-rekey shortcut | "Every real key exchange must continue to work" |

**Outcome:** gate PASSED (and again after the 10-16 repair). Bundle raw: DS two ungraded timeouts, then 1.0; MiMo none recorded. Ledger: DS SOLVED 1/1, MiMo SOLVED 1/1 → rejected. B-failure-modes: no graded run of either model ever made the one-role or one-direction mistake; re-keying to null kex was always caught. No traps missed.
**Read:** all siblings are stated routes or variants of one accepted concept ("refuse unprotected sessions"), so models fix them together. They are real multi-sink code, but they add test volume and no difficulty.

### jackson-databind-sib2
**Host / advisory:** FasterXML jackson-databind @ d627a8a, GHSA-mhm7-754m-9p8w, CWE-863, Java · **Built by:** Opus hand-built, round 2 (10-16) · **Pattern label:** none (track mined+injected+trap-stack) · **Traps:** 2 structured (T1, T2) + inherited any-setter sibling and coupled type-id test (ids S1, C1 assigned here) = 4
**Base bug:** `ExternalTypeHandler` ignores the active view, so a polymorphic AdminView property whose subtype comes from a sibling `kind` field is bound under PublicView. The report's single example leads there.
**Symptom as reported:** "`asset` is filled from the request even though the caller's view does not include it … This is one example, not the whole problem." Invariant: "no input may set a property that is restricted … whatever the type looks like, however the object is built or populated, and whether the input creates a new object or is applied to an existing one." Coupled: visible properties keep binding "including when they sit next to a hidden value or depend on one." No mechanism is named. The fairness review rated every test low or medium-low risk; T1's coupling relies only on "depend on one".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| S1 | B-ROUTE | M4 | Nothing planted: admin-only `@JsonAnySetter` (Map, method, JsonNode) fills under PublicView (`SettableAnyProperty`, no view code) | Same rule, mechanism with no protection | "Upstream doesn't support it", "any-setter isn't a restricted property" | "whatever the type looks like" |
| C1 | COUPLED TRAP | M11 | Functional: visible type-id creator param must bind when `asset` is hidden (`ExternalTypeHandler` entry) | Same handler entry as the base | An early skip in the loop also skips the visible id assignment | "including when they sit next to a hidden value or depend on one" |
| T1 | B-ROUTE | M10+M11 | `@JsonIdentityInfo(PropertyGenerator)` id: the stand-in `ObjectIdValueProperty` carries no views and writes the admin-only id (`deser/impl/ObjectIdValueProperty`, `PropertyValueBuffer.handleIdValue` for creators; `BeanDeserializerBuilder` 425/497) | View check consults the proxy, not the real property; the id must still register for visible links | Copying the view check checks the stand-in's empty views; skipping the whole id breaks links | "however the object is built"; "… or depend on one" |
| T2 | B-ROUTE | M5 | Array-shaped bean in-place update (`BeanAsArrayDeserializer.deserialize(p,ctxt,bean)`) has no view check, reached by `readerForUpdating(...).withView` and `@JsonMerge` defaults; the fresh-read methods next to it do check | Update/merge route to the same sink | "Array beans already have view checks" (N-1 paths checked) | "whether the input creates a new object or is applied to an existing one" |

**Outcome:** gate PASSED (strict), fairness READY, blind Opus fix 1.0. Bundle raw: DS 0.0, 0.0, 0.0, 0.5833; MiMo 0.0, 0.0, 0.0, 0.5833, 0.0 (3 outage-cut runs excluded). **Audited: both failed 3/3, the only audited both-model breaker.** Per breaker report §3: S1 missed in 6/6 (both); T1 write left open in 5/6 (DS a2, a3; MiMo a1, a2, a3), and T1 links broken by DS a1 and MiMo a3; C1 broken in 4/6 (DS a1, a2; MiMo a1, a3); restricted type id (base variant) left open by DS a1, a2 and MiMo a1; T2 missed only by DS a2.
**Read:** the traps are genuinely different concepts: feature-absent (S1), proxy-object check plus coupling (T1), update route (T2), each with its own dismissal reason, so the misses are not correlated. S1 and T1 did the work and T2 was mostly caught. Realistic (nothing planted). The fairness risk sits on T1's coupled-links test, but it was reviewed READY and the blind fix found it.

### jackson-databind-readonly
**Host / advisory:** FasterXML jackson-databind @ d627a8a, no advisory (real unfixed gaps, unchanged in 2.20.0), CWE-915, Java · **Built by:** Opus hand-built, round 2 · **Pattern label:** none (source=injected, nothing planted) · **Traps:** 3 (T1 security; T2, T3 coupled)
**Base bug:** a getter-only `READ_ONLY` POJO property is merged from input when merging is on (`setDefaultMergeable`, configOverride, `@JsonMerge`), because the merge branch of `BeanDeserializerFactory.addBeanProps` has no ignorable guard; the #1805 guard 12 lines above is the obvious precedent.
**Symptom as reported:** "Afterwards `account.getQuota().limit` is 1000000 … This is one example, not the whole problem." Invariant: "No input may set a property declared read-only, however the object is built, populated or updated, and whatever the type looks like … including changing the contents of an object, collection or map." Coupled: "writable properties (also a writable property that shares its JSON name with a read-only one) … input that is not aimed at a read-only property, wherever that input is delivered today." Catch-all types are never mentioned (notes: low/medium risk).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | B-ROUTE | M4+M6 | With an `@JsonAnySetter`, `addBeanProps` (553-566) never registers read-only names, so the #1805 guard (`hasIgnorable`) and creator marking (`BeanDeserializerBase.resolve` 523-532 → `PropertyBasedCreator`) both see an empty set: merge, getter-as-setter List, ctor param and record component leak | Root cause upstream of the base: the producer of the ignored-names set is skipped on the catch-all branch | In-code comment "for now only consider unless there's any setter" reads as deliberate; copying the precedent guard passes every probe of the example type | "whatever the type looks like", "however the object is built" |
| T2 | COUPLED TRAP | M11 | Functional: `@JsonIgnore`d keys must still reach the catch-all (jackson's own `AnySetterTest` in /app; `always_register.patch` = functional_fail) | Same ignored-names set carries read-only and `@JsonIgnore` names | The root fix the comment invites blocks both | "input that is not aimed at a read-only property, wherever that input is delivered today" |
| T3 | COUPLED TRAP | M11 | Functional: a WRITE_ONLY `owner` setter sharing the JSON name of a READ_ONLY getter must bind (`POJOPropertyBuilder`; `drop_readonly_names.patch`) | Read-only name sits in the ignored set | Treating the set as hard ignorals | "also a writable property that shares its JSON name with a read-only one" |

**Outcome:** gate PASSED (strict), fairness READY. Raw: DS 1.0; MiMo 1.0 → both solved first try; rejected. No per-test data.
**Read:** T1 is a real different concept (producer off the check's path, feature-absent branch), but it sits in the same method as the landing site, about 50 lines away, so a model reading `addBeanProps` sees it. That distance was too short. The coupled traps were stated explicitly and both models kept them.

### marshmallow-readonly-sib
**Host / advisory:** marshmallow @ d08471b (4.3.1 dev), no advisory (real unreported gaps), CWE-915, Python · **Built by:** Opus hand-built, round 2 · **Pattern label:** none (source=injected, nothing planted) · **Traps:** 3 (T1, T0b security; T3 coupled); T0 is the example
**Base bug (T0):** `Schema.__init__` sets `load_only/dump_only = constructor_set or Meta_set` (`schema.py:431-432`), so any extra declaration, including an enclosing schema's dotted name passed to a nested schema class, discards the nested schema's own Meta lists.
**Symptom as reported:** "The client chose its own role. This is one example … other schemas of ours let read-only values in, or write-only values out." Invariant: read-only "by any of the means above and at any depth, is never set from input, whichever way the input reaches it"; "Declarations add up"; and "The schema it encloses keeps behaving exactly as its own declarations say wherever else it is used". The fairness review said NOT READY (the "at any depth" promise exceeded the first reference). Fix A followed; no later READY is recorded.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | B-ROUTE | M4 | Nothing planted: `Nested.schema`'s schema-object branch (`Nested(S())`, `Nested(lambda: S())`, in List/Dict, data_key spelling, depth 2) applies dotted only/exclude/many but never load_only/dump_only (`fields.py:580-595`; the class branch at 597-612 does) | Same rule, nesting form that never had the feature | Nested docstring "the instance's exclude, only, and many attributes will be respected" reads as design | "by any of the means above and at any depth … whichever way the input reaches it" |
| T3 | COUPLED TRAP | M11 | Functional: `copy.copy(nested)` shares field objects, so marking the copy's fields read-only leaks the restriction to the original object and to other nestings (`fields.py:581`, `schema._bind_field`) | The natural T1 fix mutates the shared object | Copying the only/exclude precedent onto the shallow copy | "keeps behaving exactly as its own declarations say wherever else it is used" |
| T0b | B-ROUTE | M1 | Direct constructor use `MemberSchema(dump_only=…)` drops Meta lists (same `schema.py:431` line); manifest labels it a rank-2 merged route | The base flaw reached without an enclosing schema | Only if the fix lands in the nesting path; manifest calls it weak | "Declarations add up … in any place" |

**Outcome:** gate PASSED (strict); fairness NOT READY before Fix A, no later verdict recorded. Raw: DS 1.0 (in ~10 min per the class-transformer notes); MiMo 0.0 then 1.0 → both solved; rejected. No per-test data for the MiMo 0.0 run.
**Read:** T1 is a real feature-absent concept, but the working class branch sits three lines below in a small file, so the gap is visible by comparison and the class-A dismissal never happened. The coordinator's lesson: class A needs distance in a large codebase.

### class-transformer-exclude-sib
**Host / advisory:** typestack/class-transformer @ a2734a5 (0.5.1), no advisory (open upstream issues #1030, #1832, #95, #1097), CWE-915, TypeScript · **Built by:** Opus hand-built, round 2 · **Pattern label:** none (source=injected, nothing planted) · **Traps:** 3 (T0 example, T1, T2)
**Base bug (T0):** `TransformOperationExecutor.getKeys` (478-513) filters input keys by exclusion, version and groups using the plain (JSON) key, so restrictions on an `@Expose({name})`-renamed property are skipped on input.
**Symptom as reported:** "A customer chose their own credit limit. This is one example …". Invariants: never set or written "at any depth … and whichever JSON name the input uses"; "Restrictions declared on a class, on its properties or on the class as a whole, also apply when transforming any of its subclasses"; "When a subclass restricts an inherited property further, the restriction applies to the subclass; the base class keeps behaving as it declares." Both siblings are stated nearly verbatim (notes: needed for fairness, so T1 may be a search problem, not a dismissal).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T0 | BASE | M8 | Restrictions are checked on the plain key before it is mapped to the property name (`TransformOperationExecutor.ts` 478-513 vs 175-181); 7 tests (groups, toClassOnly, version, excludeExtraneousValues, nested, existing object) | The example | n/a | the example plus "whichever JSON name the input uses" |
| T1 | B-ROUTE | M4 | Whole-class `@Exclude()` + `@Expose()` whitelist is not inherited: `MetadataStorage.getStrategy` (98-105) reads only the class's own metadata while property lookups walk ancestors | Same protection, class-level form that never had inheritance | "TS class decorators are not inherited" | "also apply when transforming any of its subclasses, however many levels down" |
| T2 | B-ROUTE | M10 | `findExposeMetadataByCustomName` (88-92) returns ancestors' records first while `findExposeMetadata` returns the subclass's own first; a T0 fix that checks the record found by JSON name misses a subclass tightening an inherited renamed property | The natural T0 fix consults the wrong metadata record | The name lookup looks like the right helper | "When a subclass restricts an inherited property further …; the base class keeps behaving as it declares" |

**Outcome:** PARKED at 13:25 UTC (coordinator: small libraries are poor class-A hosts). Docker gate never run (only local nop/oracle/patches, all as declared; status "no gate marker"); no fairness review; never trialled (no DS or MiMo rewards).
**Read:** T1 and T2 are different concepts from T0 (inheritance; wrong record), but the instruction states both outright and the library is small, so they would likely be found. T0 and T1 are public open issues a model may remember.

### better-auth-sso-endpoints
**Host / advisory:** better-auth @ 23094a6, GHSA-5rr4-8452-hf4v, CWE-918, TypeScript · **Built by:** Opus hand-built, round 2 · **Pattern label:** none (manifest shape "DeepSeek shape 2", source=mined) · **Traps:** 3 structured (BASE, T1, T2) + host-spelling variants and the trustedOrigins coupling (ids V1, C1 assigned here) = 5
**Base bug:** the SSO plugin persists user-supplied OIDC endpoints (token/userInfo/jwks) at registration with no routability check and fetches them at the OIDC callback. The report leads to the callback fetch; the only existing validation (`discovery.ts validateDiscoveryUrl`) runs only on the runtime-discovery path, which stored skip-discovery providers bypass.
**Symptom as reported:** "our server sent requests to a service bound to loopback … In another case it sent them to the cloud instance-metadata address." Invariant: "No provider configuration that a caller entitled to manage SSO can supply through the public API may cause the server to send a request to a host the deployment does not permit … however the address is written." Preservation: trustedOrigins providers keep working "over HTTP or HTTPS". Registration, update and override are deliberately not named (fairness round 1); all traps are covered by "no provider configuration … through the public API".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| BASE | BASE | M6 | Nothing planted: `routes/sso.ts registerSSOProvider` stores raw endpoints (skipDiscovery); the callback reloads them (`safeJsonParse`) and fetches; the check on the discovery path never sees them | The producer (registration) is off the fetch's path (save and reload); the upstream fix sits at the producer | Adding validation on the discovery/fetch path looks complete (`callback_discovery_path_only.patch`) | "No provider configuration … may cause the server to send a request" |
| T1 | A-FAR | M5 | `routes/providers.ts updateSSOProvider → mergeOIDCConfig` merges new endpoints into a stored allow-listed provider | Upstream fix's second site, a different file | A fix only at registration (`miss_update.patch`) | "No provider configuration … through the public API" |
| T2 | A-FAR | M5 | With discovery on, `discoverOIDCConfig` lets `existingConfig?.tokenEndpoint` override the discovered value, stored unvalidated (`oidc/discovery.ts`, `sso.ts` ~675). Origin unclear: whether upstream's registration check covers it is not stated | User value wins over discovered default | Discovery looks like the trusted path; fixing only the skip branch misses it (`skip_branch_only.patch`) | same |
| V1 | SHAPE TRAP | M8 | Host spellings: `127.1`, `localhost:8080`, `0.0.0.0`, 10.0.0.5, 192.168.1.20, 169.254.169.254 | Variants of the base input | A loopback-only blocklist (`loopback_only.patch`) | "for example a loopback, private-network, link-local or cloud instance-metadata address, however the address is written" |
| C1 | COUPLED TRAP | M11 | Functional: an internal IdP on a trustedOrigins loopback origin works end to end; skip-discovery, discovery, update and public-host (8.8.8.8) sign-ins work (`block_trusted_loopback.patch`, `disable_feature.patch`) | Over-broad SSRF block | Blocking all private hosts | "a provider whose addresses are on origins listed in `trustedOrigins` … keeps working end to end" |

**Outcome:** gate PASSED (strict), fairness READY (third round). Raw: DS 1.0 (~20 min); MiMo 1.0 (~27 min) → both solved first run; rejected. No traps missed.
**Read:** all traps belong to the one accepted concept "validate stored endpoints". The producer is the request handler the attacker calls, which models read whole (BRIEF-trap-stack: the producer must be infrastructure the attacker never calls). T1 and T2 are standard extra routes.

### mcp-ts-sdk-oauth
**Host / advisory:** modelcontextprotocol/typescript-sdk @ ef39308, GHSA-6qxp-vccf-f47h, CWE-522, TypeScript · **Built by:** Opus hand-built, round 2, ported from Hadi's task (credit: Hadi, base task and DeepSeek finding) · **Pattern label:** none (manifest traps have no ids; ids assigned here: P1 and H1-H2 from Hadi's base tests, T1-T2 from the manifest, C1) · **Traps:** 6
**Base bug:** `fetchToken()` never checks the provider's issuer stamp against the authorization server the MCP server names, so a malicious MCP server collects the client credentials. The report leads to `fetchToken()`.
**Symptom as reported:** "The attacker's authorization server ended up with our client secret, even though the provider was pinned to our own authorization server." Invariants: "never be presented to a different authorization server … whichever of the SDK's OAuth client functions the application uses"; "credentials the application saved from an earlier sign-in there, however that sign-in was done". Nothing points at reloading through the SDK's schemas: the blind Opus fix missed P1 (fairness gap; see Outcome).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| P1 | A-FAR | M6 | Nothing planted: the core zod auth schemas (`OAuthTokensSchema`, `OAuthClientInformation[Full]Schema`) strip `issuer`, so saved credentials reloaded through them are unstamped and fall through the check (5 tests via transport, `auth()`, `withOAuth()`) | Producer in another package feeding the check via save/reload; part of the upstream fix | The check never calls the schemas; "no stamp → allow" looks like legacy compatibility | only "credentials the application saved … however that sign-in was done" |
| H1 | BASE | M7 | Lazily loaded credentials are read inside `prepareTokenRequest`, after a check placed at the top of `fetchToken` (`check_before_prepare_only.patch`) | Placement variant of the base check | Checking before the credentials exist | "credentials configured on a provider" |
| H2 | SHAPE TRAP | M8 | Lookalike tenant on the same IdP host: origin-only or prefix compare passes (`origin_only` / prefix patches) | Identity-comparison variant of the base | Origin compare looks sufficient | "a different authorization server" |
| T1 | B-ROUTE | M1 | `refreshAuthorization()` / `exchangeAuthorization()` → `executeTokenRequest()` (`client/auth.ts` 2343, 2280, 2168) send stamped client info, refresh token or code to any server; the upstream fix checks only `fetchToken()` | Sibling public helpers reaching the same token-request sink | Helper "given explicit credentials and a destination is the caller's responsibility" | "whichever of the SDK's OAuth client functions the application uses" |
| T2 | B-ROUTE | M9 | Tokens returned by `fetchToken()`/`refreshAuthorization()` carry no issuer; `auth()`'s legacy back-stamp (`auth.ts` 1369-1375) binds them to the attacker's AS and refreshes there | Fail-open on "no stamp", second-order after the check | The back-stamp is deliberate for pre-upgrade storage | "however that sign-in was done" |
| C1 | COUPLED TRAP | M11 | Functional: same-server refresh (incl. trailing-slash URL), app-driven code exchange, legacy unbound storage, providers without `expectedIssuer`, and an MCP server moving to a new AS where DCR re-registers (`refuse_unbound`, `throw_on_mismatch_in_auth`, `disable_feature` = functional_fail) | Guards T1, T2 and base fixes against refuse-all | Throwing on every mismatch or refusing unstamped tokens | "Legitimate use keeps working as it does today: …" (each listed) |

**Outcome:** fairness READY, but the strict gate FAILED: the blind Opus patch scored 0.7778 (closed T1 and T2, missed P1: 4 schema tests). SHELVED by user decision, never trialled in this form. Hadi's original (P1, H1, H2 only): DS 0.6429 x3 under terminus-2, missing P1 in 8/8 runs; MiMo solved.
**Read:** P1 is a genuinely different concept (hidden infrastructure producer) and it is what beat DS. It is also what the blind fix could not find from this wording, so it sits on the fairness edge. T1 and T2 are real, distinct concepts (unlisted helper route; fail-open back-stamp) but untested on models.

### airflow-ds
**Host / advisory:** apache/airflow, GHSA-C56V-8W4G-3MFM / CVE-2026-65017, CWE-200, Python · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18/19); trap set reuses airflow-info-exposure-inj T1-T9 almost word for word · **Pattern label:** A+B · **Traps:** 10
**Base bug:** Whether a value is sensitive is decided by a literal `(section, key)` lookup in the shared parser's `sensitive_config_values`, so a team-scoped spelling (`[team_a=database]`) is not recognised. The report leads to the single-option REST route (`routes/public/config.py:160`).
**Symptom as reported:** "`GET /api/v2/config/section/team_a=database/option/sql_alchemy_conn` returns the full connection string". Invariants: "No value of a team-scoped override of a sensitive option may be shown ... over the REST API, on the command line, in the configuration view for one team, or in the process logs ... however the team-scoped value is supplied, and whatever the team is called — team names are arbitrary labels"; "covers the command or secret reference"; "must be redacted from Airflow's logs". Every trap has a covering invariant.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_landing_single_option | BASE | M8 | single-option route checks only the literal registered pair; routes/public/config.py | reported site | none (landing) | the example request |
| T2_listing_file_sections | A-FAR | M3 | full and section listing masks by iterating the registry; shared parser.py as_dict | same lookup in the shared parser library | lower-level library, not the API route | "for the whole configuration, one section, or one option" |
| T3_env_var_spelling | A-FAR | M6 | config loader splits a team env var into section `<team>`, key `_<section>__<key>`; parser.py _include_envs | producer emits a spelling the check never maps | odd section name looks like an unknown option | "however the team-scoped value is supplied" |
| T4_cli_listing | A-FAR | M1 | `config list --hide-sensitive` render path repeats the literal lookup; parser.py write | same check on the CLI channel | local admin CLI run by the config owner | "on the command line" |
| T5_cmd_secret_shapes | SHAPE TRAP | M12 | team `_cmd`/`_secret` fallbacks never resolved, and the existing exemption leaves them visible; parser.py | spelling variant of the sensitive option | existing code deliberately does not hide cmd/secret entries | "covers the command or secret reference" |
| T6_log_redaction | B-ROUTE | M2 | start-up masker registers only base-section values; airflow-core configuration.py mask_secrets | separate iteration over the registry for logs | different output channel (logs) | "must be redacted from Airflow's logs" |
| T7_per_key_backend_kwargs | B-ROUTE | M2 | per-key secrets-backend kwarg masking keyed on literal `secrets`/`workers` names; services/public/config.py | second masking implementation | upstream argues the backend is not team aware | "secrets-backend parameters" listed as sensitive; "however supplied" |
| T8_injected_team_view | INJ | M5 | `GET /config?team_name=` copies team overrides over the masked listing, skipping only options whose base is already hidden; services/public/config.py + route | merged override reaches output past a base-only guard | guard defers to the already-masked listing, so it looks complete | "in the configuration view for one team" |
| T9_injected_get_value_hide | INJ | M1 | new `config get-value --hide-sensitive` flag using the literal lookup; cli/commands/config_command.py | another CLI entry | get-value prints raw values by design; admin CLI | "on the command line ... one option" |
| T10_arbitrary_team_name | SHAPE TRAP | M8 | team names containing `=` or `.` across all routes; base_section_name must split from the right | resolution spelling of the base fix | a first-separator split passes every single-separator test | "nothing may be assumed about the characters a name contains" |

**Outcome:** gate SOUND; fairness NOT READY (a fairness revision was applied 10-19, 33 security tests). Header raw rewards: DS 0.9697, 1.0; MiMo 0.0. Per-test rows after the fairness revision (351 tests): MiMo r1 0.0, failing only the functional `test_listing_keeps_team_non_kwarg_secrets_option` (over-broad masking at the T3/T7 coupling); MiMo r2 0.8485, missed T7 (all four kwarg tests) plus T10's kwarg case; MiMo r3 0.0, missed T3 (single-option env spelling) plus the same functional failure. DS 0.9697 missed T3 (single-option env spelling); DS 1.0. Older DS rows (343 tests, before the revision): 0.0 (T3 plus 3 over-broad functional failures) and 0.7692 twice (T10 separator cases; r3 also T3).
**Read:** T6/T7 (other masking implementations) and T10 (separator spelling) are what bit. T3's single-option form recurs for both models. MiMo's zeros are mostly over-broad fixes, not missed siblings. T8/T9 (injected) were never missed. The siblings are mostly more routes to one accepted concept ("resolve the team spelling to the base option"), but T7 and T10 need a different step and do separate the models.

### airflow-info-exposure-inj
**Host / advisory:** apache/airflow, GHSA-C56V-8W4G-3MFM / CVE-2026-65017, CWE-200, Python · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B · **Traps:** 9
**Base bug:** Same as airflow-ds: a literal `(section, key)` sensitivity lookup misses team-scoped spellings. The report leads to `routes/public/config.py:160`.
**Symptom as reported:** Same example request. Invariants: "anywhere Airflow shows configuration with sensitive values hidden — over the REST API or on the command line, for all of the configuration, one section, one option, or the configuration as one team sees it"; "however the team-scoped value is supplied ... covers the command or secret reference"; "redacted from Airflow's logs". The hidden form allows "`< hidden >` (or it is left out)". All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_landing_single_option | BASE | M8 | literal-pair check in the single-option route; routes/public/config.py | reported site | none | example request |
| T2_listing_file_sections | A-FAR | M3 | registry-iterating listing mask; shared parser.py as_dict | shared-library copy of the lookup | lower-level library | "all of the configuration, one section" |
| T3_env_var_spelling | A-FAR | M6 | loader spells team env vars as `<team>` / `_<section>__<key>`; parser.py _include_envs | producer off the check's mapping | looks like an unknown option | "however the team-scoped value is supplied" |
| T4_cli_listing | A-FAR | M1 | `config list --hide-sensitive` write path; parser.py write | CLI channel | admin CLI | "on the command line" |
| T5_cmd_secret_shapes | SHAPE TRAP | M12 | team `_cmd`/`_secret` entries not resolved; parser.py | spelling variant | cmd/secret entries visible by design | "command or secret reference" |
| T6_log_redaction | B-ROUTE | M2 | start-up masker registers base sections only; airflow-core configuration.py | second iteration for logs | different channel | "redacted from Airflow's logs" |
| T7_per_key_backend_kwargs | B-ROUTE | M2 | per-key kwarg masking keyed on literal section names; services/public/config.py | second masking implementation | backend not team aware | sensitive backend parameters; "however supplied" |
| T8_injected_team_view | INJ | M5 | team view merges overrides over the masked listing, guarded by "base already hidden"; services/public/config.py | merged override past a base-only guard | defers to the masked listing | "the configuration as one team sees it" |
| T9_injected_get_value_hide | INJ | M1 | `config get-value --hide-sensitive` with the literal lookup; config_command.py | another CLI entry | get-value prints raw values by design | "on the command line ... one option" |

**Outcome:** no gate marker in the bundle (the build notes record nop/oracle/patches PASS). DS 0.95 / 0.0 / 1.0; MiMo 0.0 / 0.0 / 0.0. DS r1 missed T7 (team env backend kwarg). DS r2 missed T3 (single-option env spelling) plus the over-broad functional failure `test_listing_keeps_team_non_kwarg_secrets_option`. MiMo r1 missed T3 plus that functional failure. MiMo r2 missed T5 (both cmd/secret listing tests) and T3, plus the functional failure. MiMo r3 missed T5, T3, the env-var log redaction test (listed under both T3 and T6), plus the functional failure.
**Read:** This is the earlier variant. airflow-ds keeps the same T1-T9, adds T10 (arbitrary team-name characters) and extra cases (success status, CLI cmd/secret, workers kwargs, kwarg in the team view), and removes "or it is left out" from the hidden form. Every MiMo zero includes the same over-broad functional failure, so MiMo's 0/3 is partly breaking the coupled contract rather than only missing siblings. The real misses are T3's spelling and T5, which are variants of the reported concept.

### arc-ds
**Host / advisory:** basekick-labs/arc, GHSA-P2J4-C4G6-RPF5 / CVE-2026-47735, CWE-200/22/918, Go · **Built by:** DeepSeek-built pilot (build-v1 template, injected track) · **Pattern label:** A+B · **Traps:** 6
**Base bug:** User SQL runs on a shared embedded DuckDB whose only protection is a text denylist in the query handler (`internal/api/query.go:1830`). DuckDB I/O table functions therefore read arbitrary local files and fetch URLs. The published fix adds a DuckDB sandbox in `internal/database/duckdb.go` configureDatabase.
**Symptom as reported:** "`SELECT * FROM read_text('/home/arc/notes.txt')` ... returned the contents"; "also made the server fetch a remote URL". Invariants: "No request to Arc's HTTP API may make the server open, read, list, return, copy or transmit a local file that is not part of Arc's own storage ... for every route and for every caller-supplied value — query text, filter text"; "No request may make the server contact a network address supplied by the caller"; "whichever pooled database connection serves it". All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_io_function_family | BASE | M8 | I/O function family, quoted/case spellings, admin token, 16 pooled connections; query.go ValidateSQLRequest / duckdb.go | reported site | "add the missing names to the denylist" | example request; "whichever pooled database connection" |
| T2_remote_url | SHAPE TRAP | M12 | `read_csv_auto` over a caller http:// URL; same sink | SSRF impact of the same functions | "files only" | "must not contact a network address supplied by the caller" |
| T3_measurement_route | B-ROUTE | M1 | GET /query/{measurement}?where= builds its own SQL and skips the validator; query.go queryMeasurement | another entry to DuckDB | neighbouring route with its own validator | "filter text"; "every route" |
| T4_continuous_query | B-ROUTE | M1+M5 | stored continuous-query SQL executed later; continuous_query.go | stored object reaching the same engine | admin-only background job | "every route ... anything else the request carries" |
| T5_preview_helper | INJ | M2 | POST /query/preview opens its own in-memory DuckDB outside configureDatabase; query_preview.go | second database handle that a sandbox fix misses | helper that only previews | "whichever ... connection serves it"; "every route" |
| T6_export_download | INJ | M1 | GET /export/download?path= joins a caller path without containment (os.ReadFile); export_download.go | different sink (plain file read), same property | static-file helper, not SQL | "open, read ... a local file ... every route" |

**Outcome:** gate SOUND (no fairness status). DS 1.0; MiMo 1.0 (one trial each, 18 tests, no failures). No sibling was missed.
**Read:** Once the solver adopts the structural fix (sandbox in the DB layer plus checks on every route), T1-T5 fall together. T6 is a plain path traversal, a different concept, but the "every route" invariant points straight at it and both models fixed it. With only one trial per model, this looks too easy rather than near the bar.

### astro-csrf-origin
**Host / advisory:** withastro/astro, GHSA-8MV7-9C27-98VC / CVE-2026-73423, CWE-352, TypeScript · **Built by:** Opus build-v1 template, batch 1 (10-17) · **Pattern label:** A · **Traps:** 4
**Base bug:** The origin (CSRF) check lives only in the middleware chain. The composable `astro/hono` pipeline that mounts `actions()` before `middleware()` runs the action first. The report leads to action dispatch in `packages/astro/src/actions/handler.ts` (it has no BASE row in this manifest).
**Symptom as reported:** a cross-site urlencoded form to `POST /_actions/deleteAccount` runs "although the origin check is enabled". Invariants: "No request can cause any of the site's actions, endpoints or pages to run if the standard request handling's origin check would refuse it"; "covers every way an action can be invoked ... every way a site can assemble its server from Astro's building blocks". Must-keep-working: cross-site JSON, GET/HEAD/OPTIONS, `checkOrigin: false`. All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1-dispatch-without-middleware | A-FAR | M1 | `pages()` without `middleware()` reaches page/endpoint dispatch; core/pages/handler.ts | another dispatch path outside the chain | leaving out middleware() looks like user misconfiguration | "actions, endpoints or pages"; "every way a site can assemble" |
| T2-lower-level-fetch-api | A-FAR | M3 | `astro/fetch` actions(state)/pages(state) under the Hono wrapper; core/fetch/index.ts | fix belongs in the shared handlers below both APIs | report names only astro/hono | "every way a site can assemble its server" |
| T3-input-shapes | SHAPE TRAP | M12 | RPC vs form action, missing content type, non-POST, content-type case/params, missing Origin; core/app/middlewares.ts rule | variants of the general rule | a hand-rolled urlencoded check looks complete | "if the standard ... origin check would refuse it" |
| T4-coupled-must-keep-working | COUPLED TRAP | M11 | cross-site non-form, safe methods, checkOrigin:false must pass | over-broad fix catcher | n/a | "Legitimate use must keep working" list |

**Outcome:** gate passed; fairness NOT READY. DS 1.0, MiMo 1.0 (two rounds each per the per-test rows, 164 tests, no failures).
**Read:** All siblings are more routes to one accepted concept: "run the existing origin rule in the shared dispatch handlers". Fixing it once at the shared layer covers everything, so the models fix the siblings together.

### astro-ds
**Host / advisory:** withastro/astro, GHSA-8MV7-9C27-98VC / CVE-2026-73423, CWE-352, TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template; notes say injected track, bundle says track None) · **Pattern label:** A · **Traps:** 8
**Base bug:** Same as astro-csrf-origin: the origin check exists only in the middleware chain, so a composed pipeline runs actions, endpoints and pages before or without it. The landing is action dispatch (`actions/handler.ts:33-45`).
**Symptom as reported:** The instruction is identical to astro-csrf-origin: "every way an action can be invoked ... every way a site can assemble its server from Astro's building blocks". The injected primitives (endpoints(), formActions(), partials()) are building blocks, so they are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1-action-dispatch | BASE | M7 | action runs before or without the origin middleware; actions/handler.ts | reported site | none | example request |
| T2-dispatch-without-middleware | A-FAR | M1 | pages() dispatch without middleware; core/pages/handler.ts | another dispatch path | middleware() looks mandatory | "actions, endpoints or pages" |
| T3-lower-level-fetch-api | A-FAR | M3 | astro/fetch primitives under Hono; core/fetch/index.ts | shared handlers below both APIs | report names astro/hono | "every way a site can assemble" |
| T4-input-shapes | SHAPE TRAP | M12 | non-safe methods, form content types in any case, absent content type or Origin, RPC vs form; core/app/origin-check.ts | variants of the general rule | a POST/urlencoded check looks complete | "would refuse it" |
| T5-coupled-must-keep-working | COUPLED TRAP | M11 | non-form cross-site, safe methods, checkOrigin:false, injected primitives' legit use | over-broad fix catcher | n/a | "Legitimate use must keep working" |
| S1-endpoint-only-dispatcher | INJ | M1 | new `endpoints()` primitive renders the endpoint itself, outside middleware and the shared dispatch; core/endpoints/handler.ts | new entry that bypasses the shared-handler fix | endpoints are "dispatched by pages()" | "endpoints"; "every way ... building blocks" |
| S2-form-action-dispatcher | INJ | M2 | new `formActions()` runs the action itself, bypassing the action-handler class; actions/form-handler.ts | second action-execution implementation | all actions assumed to go through the handler class | "every way an action can be invoked" |
| S3-fragment-dispatcher | INJ | M2 | new `partials()` with a hand-rolled check covering only POST + exact urlencoded; core/pages/partial-handler.ts | duplicate, incomplete guard | "this primitive already has an origin check" | "would refuse it"; building blocks |

**Outcome:** gate UNSOUND (pipeline ledger: "nop/oracle/patches not all ok", later re-gate unsound; the builder notes blame Docker/egress infrastructure errors). Not trialled: no DS or MiMo rewards.
**Read:** Compared with astro-csrf-origin (T1-T4: A-far sites, shapes, coupled), this variant adds a BASE row and three injected composable dispatchers that sit outside the shared handlers the published fix guards. Those dispatchers are the only siblings a shared-layer fix would not cover by itself. S3's "check already present" is the most distinctive dismissal reason. It is untested because the gate never went SOUND.

### backstage-ds
**Host / advisory:** backstage/backstage, GHSA-29GX-H2M3-XW44 / CVE-2026-106462, CWE-441/863, TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, injected track) · **Pattern label:** A · **Traps:** 7
**Base bug:** Scaffolder SCM actions silently fall back to the instance's privileged integration credential when no user `token` is given. The base site is the shared GitHub helper `getOctokitOptions` (`scaffolder-backend-module-github/src/util.ts:188`). The task requires a new opt-in `scaffolder.requireScmUserCredentials` mode.
**Symptom as reported:** "the repository was created and pushed as the instance's integration identity". Invariants: "No scaffolder step in scope may perform any SCM operation, read or write, unless the step input carries a non-empty user credential"; "must not construct an SCM client at all"; "Only GitHub and GitLab locations"; "A relative location whose template base location is an SCM host is a remote read and requires a user credential"; "Enabling the setting in the instance configuration must be sufficient at startup". All traps are covered (the fetch actions are covered by "some fetch template content" and "read or write").

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M9 | shared GitHub credential helper falls back to the integration credentials; github util.ts | reported site | none (landing) | the observed impact |
| T2 | A-FAR | M2 | pull-request action builds its client through an injectable factory outside the helper; githubPullRequest.ts | second client-construction path | "the helper is fixed" | "every affected step" |
| T3 | A-FAR | M2 | whole GitLab module (three helpers plus an inline publish client) and privileged ownership paths; gitlab util.ts / gitlab.ts | second implementation in another package | report is about GitHub | "GitHub and GitLab"; "inherently needs the instance's identity must be refused" |
| T4 | A-FAR | M2 | four built-in fetch actions read SCM content through the URL reader using integration credentials; scaffolder-backend fetch/{plain,plainFile,template,templateFile}.ts | separate credential path in the core plugin | read-only template fetchers, not publish | "read or write"; relative-location rule |
| T5 | A-FAR | M6 | setting read from root config in each module/plugin init and passed to actions; github module.ts, ScaffolderPlugin.ts | producer (wiring) off the decision path | checks added in actions, wiring forgotten | "sufficient at startup" |
| S1 | INJ | M2 | `github:release:create` resolves its own credential from the credentials provider; githubRelease.ts | bypasses the shared helper | "every GitHub action uses the helper" | "every affected step" |
| S2 | INJ | M2 | `gitlab:projectMember:create` builds its GitLab client inline with the same fallback; gitlabProjectMemberCreate.ts | bypasses the GitLab helpers | "all GitLab actions use the helpers" | "every affected step" |

**Outcome:** gate SOUND; fairness READY (two fairness rounds on 10-19). Header raw: DS 1.0, 0.9149, 0.9149; MiMo 0.9149. Final 132-test rows: both models consistently miss `fetch:template` and `fetch:template:file`, both the direct factory and the plugin-startup registration (T4, plus the T5b wiring case). `fetch:plain` and every GitHub/GitLab sibling are fixed. Earlier 128-test rows scored 0.0 because of over-broad Bitbucket Server functional failures, before the F2 scope clarification. The 108-test rows were 0.9412 with the same two template misses.
**Read:** The siblings are mostly second implementations of "no fallback credential", and models handle them well, including the injected S1/S2. The one persistent miss is the template-rendering fetchers in the core plugin, missed identically across about 10 runs from two models. That bites, but an identical miss of exactly these four tests calls for a test-artifact or fairness check (for example, whether `fetch:template` reaches the URL reader through a path the instruction never makes visible) before it counts.

### ckan-mcp-server-ds
**Host / advisory:** ondata/ckan-mcp-server, GHSA-798P-78G2-V556 / CVE-2026-61612, CWE-918, TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, injected track) · **Pattern label:** A+B (no fair B route was built; it is A + injected) · **Traps:** 5
**Base bug:** The SSRF guard `validateServerUrl` checks only the literal host string, so a host name that resolves to loopback or private space is fetched (`src/utils/http.ts:245`, used at `:387`).
**Symptom as reported:** "a dataset search whose portal address is a host name resolving to `127.0.0.1` returns a successful result"; "also when a portal redirects ... and when an address the server obtained from a portal's own response is used". Invariants: "No address supplied with a tool call ... may cause the server to open a network connection to a loopback, private ... address. Judge the address the connection actually uses"; "every one of them must be acceptable"; and an explicit startup rule: "A server started as a network-facing HTTP service must refuse to start unless ... `CKAN_ALLOWED_DOMAINS`". All traps are covered. T3 is spelled out almost literally.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_base | BASE | M8 | host-string check vs resolved IP (multi-address name, redirect, ckan:// resource); utils/http.ts | reported site | string denylist looks complete | the example; "after any name resolution" |
| T2_sparql | A-FAR | M2 | fetch-based SPARQL client imports the validator but never resolves; tools/sparql.ts | second client implementation | HTTPS-only and already validated | "No address supplied with a tool call" |
| T3_transport | A-FAR | M9 | HTTP transport starts with no permitted-hosts list; transport/http.ts | config/startup gate | deployment concern | explicit `CKAN_ALLOWED_DOMAINS` startup rule |
| T4_registry | INJ | M1 | new `registry_url` argument fetched with raw axios; tools/portal-discovery.ts | new entry to an outbound fetch without the guard | third-party directory override, not a CKAN request | "No address supplied with a tool call" |
| T5_preview | INJ | M1 | new `ckan_resource_preview` tool fetching a caller download URL with raw fetch; tools/preview.ts | new entry to an outbound fetch | display helper; URL normally from metadata | "address taken from a portal's response" |

**Outcome:** gate SOUND (recovered on re-gate). DS 1.0; MiMo 1.0 (one trial each, 99 tests, no failures).
**Read:** Every sibling is an outbound fetch, and the invariant ("judge the address the connection actually uses") invites a single resolve-then-check helper applied at every client. These are routes to one concept, and the startup trap is stated almost verbatim, so the siblings did not bite.

### compliance-trestle-ds
**Host / advisory:** oscal-compass/compliance-trestle, GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171, CWE-22, Python · **Built by:** DeepSeek-built pilot (build-v1 template, injected track; a rebuild of compliance-trestle-path-traversal) · **Pattern label:** A+B · **Traps:** 8
**Base bug:** User-chosen output names are joined onto the workspace without confirming the result stays inside it. The landing is `author catalog-generate -o` (`trestle/core/commands/author/catalog.py:90`). It has no trap row of its own.
**Symptom as reported:** "`trestle author catalog-generate -n nist -o /tmp/elsewhere` ... writes ... outside the workspace". Invariants: "No name that a user gives a trestle command for something the command produces or replaces, whatever its form and whichever command, option or mode it is given to, may cause a file or directory outside the workspace ... to be created, modified or deleted"; "a name that leaves the workspace once links are followed also counts as outside"; "including before the command fails". The instruction also mentions "a name for a related artifact", which hints at S1-S3. All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M3 | shared name check accepts absolute and inner `..` names (component-generate -o, docs/folders -tn); common/file_utils.py | lower-level shared rule | looks like a naming convention | "whichever command, option" |
| T2 | A-FAR | M1 | create/replicate write into another trestle workspace; create.py, replicate.py | other commands | "must be in a trestle project" check looks sufficient | "Any location not inside that workspace" |
| T3 | B-ROUTE | M1 | `import -o` writes into another workspace; import_.py | uncovered sibling command | import reads external content | "whichever command" |
| T4 | B-ROUTE | M6 | save-by-name mapper turns a model name into `<ws>/<dir>/<name>` for 7 assemble/resolve/filter/inherit commands; common/model_utils.py | producer off the check's path | a model name is not a path | "whatever its form" |
| T5 | B-ROUTE | M7 | component-generate `--force-overwrite` clears the folder before the name check; author/component.py | side effect before validation | opt-in flag; name check exists | "including before the command fails" |
| S1 | INJ | M10 | ssp-generate `--inheritance-view` folder name joined under the checked markdown output; author/ssp.py | child name under a judged parent | auxiliary subfolder of a checked output | "a name for a related artifact" |
| S2 | INJ | M1 | `assemble -o` output file name joined into dist; assemble.py | another option, unchecked | dist is internal; looks cosmetic | "whichever command, option or mode" |
| S3 | INJ | M1 | component-generate `--index` companion file name joined onto the workspace; author/component.py | another option, unchecked | convenience file, not a named result | "a name for a related artifact" |

**Outcome:** gate SOUND (recovered). DS 0.0 then 1.0; MiMo 0.0 then 1.0. DS r1 failed only two project functional tests (`ssp_test::test_ssp_filter`, `test_ssp_filter_control_origination`): an over-broad fix, no sibling missed. MiMo r1 missed S1 (inheritance view, absolute and parent) and failed the same two functional tests. Both second runs scored 1.0.
**Read:** S1 is the one sibling that bit (MiMo once). Its "child of an already-checked parent" shape is a genuinely different reason to skip. The rest are routes to one concept, and both models closed them once they had a central helper. The 0.0s come mainly from the over-broad fix breaking ssp-filter.

### compliance-trestle-mm
**Host / advisory:** oscal-compass/compliance-trestle, GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171, CWE-22, Python · **Built by:** MiMo-built pilot (build-v1 template; notes say injected track, bundle says track None) · **Pattern label:** A+B · **Traps:** 9
**Base bug:** Same as compliance-trestle-ds: user-chosen (and content-derived) names are turned into workspace paths without a containment check. The landing is catalog-generate `-o` (`author/catalog.py:90`). It has no trap row of its own.
**Symptom as reported:** The same example, plus "an existing directory ... is deleted first, even when the command then fails". Invariants: "No name trestle turns into a path under the workspace, whatever that name is, how it is spelled or where it comes from"; "including another trestle workspace"; "The rule has to hold for every name trestle turns into a path, on every command"; and the System text: "names trestle takes from the content it is working on". All traps are covered. T6 (content-derived) is pointed at explicitly.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M3 | shared name rule (absolute, inner `..`) via catalog/profile-generate -o and docs/folders -tn; common/file_utils.py | lower-level shared rule | looks like a naming convention | "how it is spelled" |
| T2 | A-FAR | M1 | create/replicate into a neighbouring workspace; create.py, replicate.py | other commands | a plain outside path is already refused | "including another trestle workspace" |
| T3 | B-ROUTE | M1 | `import -o` into a neighbouring workspace; import_.py | uncovered sibling command | import already deals with outside content | "on every command" |
| T4 | B-ROUTE | M6 | save-by-name mapper for catalog/component-assemble, profile-resolve; common/model_utils.py | producer off the check's path | a model name is not a path | "every name trestle turns into a path" |
| T5 | B-ROUTE | M7 | force-overwrite empties the folder before the name is judged (component and catalog generate); author/component.py | side effect before validation | opt-in flag; check exists | "deleted first, even when the command then fails" |
| T6 | B-ROUTE | M5 | `component.title` from the model JSON becomes the markdown subfolder; author/component.py | name from stored content, not the CLI | a title is display text | "where it comes from"; "names ... from the content" |
| T7 | INJ | M10 | docs create-sample `--sample-name` joined onto the judged task folder; author/docs.py | child of a judged parent | parent is known good | "every name ... on every command" |
| T8 | INJ | M2 | folders create-sample name joined after a local check that only rejects empty and reserved first components; author/folders.py | duplicate, incomplete guard | already goes through a name rule | "how it is spelled" |
| T9 | INJ | M10 | component-generate naming option joins a subfolder under the judged `-o`; author/component.py | child of a judged output | documented output is validated | "every name trestle turns into a path" |

**Outcome:** no gate marker in the bundle. Not trialled: no DS or MiMo rewards.
**Read:** Compared with compliance-trestle-ds (T1-T5 + S1-S3 option siblings), this variant keeps T1-T5, adds a content-derived name (T6), and replaces the option siblings with two "child of a judged parent" joins (T7, T9) and one incomplete local guard (T8). That leans more on the concept that bit MiMo in -ds (S1). The instruction is much more explicit ("every name ... where it comes from"), which raises fairness but may lower the bite. One consistency issue: the plan names T8/T9 options `--instance-name` / `--component-name`, while the manifest leak terms list `--sample-name` / `--component-name`. Exact option names are unclear.

### compliance-trestle-path-traversal
**Host / advisory:** oscal-compass/compliance-trestle, GHSA-R4VP-3VW6-R2X5 / CVE-2026-57171, CWE-22, Python · **Built by:** Opus build-v1 template, batch 1 (10-17) · **Pattern label:** A+B · **Traps:** 5
**Base bug:** Same CWE-22: output names are joined onto the workspace unchecked. The landing is `author catalog-generate -o` (`author/catalog.py:90`). It has no trap row of its own.
**Symptom as reported:** The same example. Invariants: "No name a user gives any trestle command for something it produces or replaces, whatever its form, may cause a file or directory outside the workspace ... to be created, modified or deleted"; "Any location not inside that workspace counts as outside, whatever it contains"; "including before the command fails". All traps are covered (T2/T3 rely on "whatever it contains" to include another workspace).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M3 | shared name check (absolute, inner `..`) via component-generate -o and docs/folders -tn; common/file_utils.py | lower-level shared rule | looks like a naming convention | "any trestle command ... whatever its form" |
| T2 | A-FAR | M1 | create/replicate into a sibling workspace; create.py, replicate.py | other commands | existing project check looks sufficient | "whatever it contains" |
| T3 | B-ROUTE | M1 | `import -o` into a sibling workspace; import_.py | uncovered sibling command | import reads external content | "any trestle command" |
| T4 | B-ROUTE | M6 | save-by-name mapper for 7 assemble/resolve/filter/inherit commands; common/model_utils.py | producer off the check's path | a model name is not a path | "whatever its form" |
| T5 | B-ROUTE | M7 | component-generate `--force-overwrite` clears before the name check; author/component.py | side effect before validation | opt-in; check exists | "including before the command fails" |

**Outcome:** gate passed; fairness NOT READY (a fairness revision on 10-17 added the prefix fixtures and the remaining mapper routes). DS 1.0 and MiMo 1.0 in both rounds (449, then 454 tests, no failures).
**Read:** This is the original variant. compliance-trestle-ds keeps T1-T5 and adds three injected option siblings (S1-S3), and -mm adds a content-derived name plus "child of a judged parent" joins. Here all five siblings are routes to one concept that a central workspace-containment helper closes, which matches the 1.0s.

### composer-symlink-path-inj
**Host / advisory:** composer/composer, GHSA-96H3-5X6V-M776 / CVE-2026-59944, CWE-22/59/732, PHP · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B (no real B route; two injected siblings) · **Traps:** 5
**Base bug:** A dependency's declared bin that resolves outside its package install directory (an in-package symlink pointing out, or `..` metadata) is chmod'd and proxied by `BinaryInstaller::installBinaries` (`src/Composer/Installer/BinaryInstaller.php:103`).
**Symptom as reported:** "follows a binary entry that actually refers to a file outside the package's own install directory, and changes that outside file's permissions". Invariants: "No binary a package declares may cause the tool to read, mark executable, proxy, or otherwise act on any file that lies outside that package's own install directory ... whether the declared path steps up and out ... or names an in-directory file that is itself a link leading outside ... no matter which install, download or refresh step"; "If the tool cannot determine with certainty ... it must not act on it". All traps are covered. The "download or refresh step" wording points at L3/S1/S2.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| L1 | BASE | M8 | in-package symlink bin resolving outside; BinaryInstaller.php installBinaries | reported site | none (landing) | the observed impact |
| L2 | SHAPE TRAP | M5 | `..` metadata reaching the installer via reinstall from installed.json, skipping the solver-time validator; BinaryInstaller.php | stored-metadata route past the lexical validator | "the `..` validator already covers this" | "steps up and out of the directory" |
| L3 | A-FAR | M2 | single-file downloader chmods bins itself; Downloader/FileDownloader.php install | second chmod loop in a lower layer | single-file dists "cannot be symlinks" | "no matter which install, download ... step" |
| S1 | INJ | M2 | new `BinaryInstaller::ensureBinariesExecutable` exec-bit refresh without containment, wired into ensureBinariesPresence | duplicate chmod loop | refresh "just delegates" to the guarded installer | "refresh step" |
| S2 | INJ | M2 | new `FileDownloader::ensureBinariesExecutable` used by PathDownloader | duplicate chmod loop | path repository is a trusted local source | "download or refresh step" |

**Outcome:** no gate marker in the bundle (the build notes record a fast-harness pass; no Harbor gate is recorded). DS 1.0 ×3; MiMo 1.0 ×3 (23 tests, no failures).
**Read:** Every sibling is a copy of the same chmod loop in a small, readable codebase, and the instruction lists every step type. Models fix them together with one containment helper. This is a clear case of more routes to one accepted concept.

### coreutils-ds
**Host / advisory:** uutils/coreutils, GHSA-GWM6-Q8CH-HCFR / CVE-2026-35356, CWE-367/59, Rust · **Built by:** DeepSeek-built pilot (build-v1 template, injected track) · **Pattern label:** A+B · **Traps:** 4
**Base bug:** `install -D` creates the destination's leading directories with path-based `fs::create_dir_all`, which follows a symlink standing where a missing directory must be created (`src/uu/install/src/install.rs:699`).
**Symptom as reported:** "If `/srv/app/data/plugins` is a symbolic link to a directory elsewhere, the tree is created at the link's target". Invariants: "Whenever `install` creates directories for a destination or places the destination file, a symbolic link at a path component must not redirect the work: nothing may be created, overwritten, renamed or removed at a link's target"; "hold for every way `install` can be asked to create a directory or write the destination". L4 (backup rename through a destination link) is covered by "renamed or removed". There is a tension with the must-keep-working "symlinked destination file is replaced" behaviour, so L4's boundary is narrow.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| L1 | BASE | M8 | path-based create_dir_all for `-D` (intermediate, final-parent, relative, below-existing shapes); install.rs standard() | reported site | none (landing) | the example |
| L2 | INJ | M2 | `-t DIR` creation moved into a helper calling uucore `create_dir_all_absolute` (route fixed upstream as A; the helper split was injected per the notes); install.rs + uucore fs.rs | second directory-creation implementation in the shared crate | -t names the directory explicitly; helper lives in another crate | "every way install can be asked to create a directory" |
| L3 | B-ROUTE | M1 | `install -d` still calls fs::create_dir_all on operands; install.rs directory() | another mode, real upstream code | advisory says -D; comment calls it safe | "every way ... create a directory" |
| L4 | INJ | M8 | perform_backup canonicalizes the destination before rename, so `-b` moves the link's target; install.rs | different operation (rename) at the same symlink decision | backup is a separate feature; the link is replaced anyway | "nothing may be ... renamed ... at a link's target" |

**Outcome:** gate UNSOUND (pipeline ledger: "nop/oracle/patches not all ok", confirmed on re-gate twice, although the builder notes record all stages PASS). Not trialled: no DS or MiMo rewards.
**Read:** L1-L3 are routes to one concept: "create directories fd-anchored without following links". A solver who fixes the shared creation primitive covers all three. L4 (canonicalize before rename) is the genuinely different concept, but the must-keep-working text makes its boundary subtle. The task is untested because the gate never went SOUND.

### django-cms-ds
**Host / advisory:** django-cms/django-cms, GHSA-6X92-6VX4-5FWR / CVE-2026-63003, CWE-639 (+CWE-862), Python · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18 · **Pattern label:** A+B, injected · **Traps:** 9
**Base bug:** The admin page-duplicate form takes the copy source as a hidden field in the POST body and never checks that the user may view that page, so a section editor copies a restricted page's plugins into their own section (`cms/admin/forms.py:514-519`).
**Symptom as reported:** "A new page appeared in their section carrying all of the restricted page's plugins, readable and editable by them." Invariants: content may not reach "a user who is not allowed to view that page ... judged on the site where the page lives: rights on one site give none on another"; no translation add/change without change rights; no create/place/copy "for a user who is not allowed to add pages at the place and on the site where the page ends up"; "Importing or transferring content between pages must respect both the page the content comes from and the page or site it goes to." Every trap is covered. The preservation clause ("the page administration's other page-creation and content-transfer features") hints that other routes exist.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M10 | Hidden copy source on the duplicate form; the URL object differs from the source; source plus a translation target (`cms/admin/forms.py`) | The reported site | none (report example) | The example request |
| T2 | A-FAR | M1 | Add-translation target page has no change check; site narrowing skipped when the source widget is hidden (`cms/admin/forms.py:279-287,334-338`) | Same form family, other feature (translation target) | Belongs to add-translation, not duplication | "No request may add or change a translation ... not allowed to change that page" |
| T3 | A-FAR | M3 | The view helper's "may change ⇒ may view" shortcut is judged on the current site, not the page's site (`cms/utils/page_permissions.py:284-289`) | The shared permission helper the fix relies on is site-blind | The project's own view helper is treated as authoritative | "judged on the site where the page lives: rights on one site give none on another" |
| T4 | B-ROUTE | M6 | Page-type source queryset spans every page type; only the rendered choices are narrowed; also into a translation and via the wizard (`cms/admin/forms.py:248-257,397-424`) | Same view check, but the source comes from a field whose validation is separate from the rendered list | Page types are shared templates; the dropdown lists only this site's | "every page a request refers to" |
| T5 | B-ROUTE | M10 | The add view checks add rights on the GET `parent_page`; the form creates under the POST value (`cms/admin/pageadmin.py:1015-1040`) | Add-rights check made on a different object than the one used | "the add view already checks add permission on the parent" | "not allowed to add pages at the place ... where the page ends up" |
| T6 | B-ROUTE | M10 | Tree copy checks only the URL page, trusts a client-supplied source-site id; copies restricted descendants and other-site pages (`cms/admin/pageadmin.py:650-700`) | Composed resource: the check covers the root only | The URL page is checked; multi-site copy is a separate admin concern | "every page a request refers to"; "rights on one site give none on another" |
| T7 | INJ | M6 | Wizard "start from page" selector: choices view-filtered, queryset is every page, save copies placeholders (`cms/forms/wizards.py`) | Same view check, bypassed by the field queryset | Selector lists only viewable pages; the wizard checks add rights | "every page a request refers to" |
| T8 | INJ | M10 | "Import content" route checks change on the target page only; client-chosen source unchecked (`cms/admin/pageadmin.py`) | Second implementation of copy, checks the wrong side | It checks change on the page it writes to | "Importing or transferring content ... must respect both the page the content comes from and ..." |
| T9 | INJ | M10 | "Copy to site" route checks view on the source, not add rights on the client-chosen target site (`cms/admin/pageadmin.py`) | Same decision, target-side half missing | Source is checked; multi-site placement is an admin convenience | "...and the page or site it goes to"; "on the site where the page ends up" |

**Outcome:** gate SOUND (fairness not recorded). DS 1.0 (1 run), MiMo 1.0 (1 run); per-trial rows show 226 tests, 0 failing for both. No trap missed.
**Read:** All nine traps are one trust decision (view the source and add/change at the target, on the right site), applied at more routes. The instruction states both halves and the cross-site rule outright, so a model that sweeps every copy/transfer path fixes them together. T3 (site-blind helper) and T5 (GET/POST split) are the only conceptually distinct traps, and both were still caught. Realism is fine: the injected routes are plain feature code.

### django-cms-object-level
**Host / advisory:** django-cms/django-cms, GHSA-6X92-6VX4-5FWR / CVE-2026-63003, CWE-639 (+CWE-862), Python · **Built by:** Opus, build-v1 template, batch 1 (mined), 10-17 · **Pattern label:** A+B (mined) · **Traps:** 4
**Base bug:** Same as django-cms-ds. The duplicate form's hidden copy source is chosen in the POST body with no view check (`cms/admin/forms.py:514`).
**Symptom as reported:** "A new page appeared in their section carrying all of the restricted page's plugins, readable and editable by them." Invariants: "No request that creates a page or a translation may copy content ... from a page the requesting user is not allowed to view" (T1, T3, T4); "No request may add a translation to an existing page that the requesting user may not change" (T2). Every trap is covered. A cross-site source trap (the site-blind helper) was built and then dropped as unfair, because no sentence pointed to it.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M10 | Hidden copy source in the POST body vs the URL object; source + own translation (`cms/admin/forms.py:514`) | The reported site | none | The example request |
| T2 | A-FAR | M1 | Add-translation target lacks a change check; site narrowing skipped for hidden-source forms, incl. the cross-site shape (`cms/admin/forms.py:253-257,279-287,334`) | Same form family, other feature | Belongs to "Add translation", not Duplicate | Bullet 2 (translation to a page the user may not change) |
| T3 | B-ROUTE | M6 | Visible page-type source validates against all page types, no view check, also with a translation target (`cms/admin/forms.py:248-252`) | Same view check, other source field | Page types are shared templates; the dropdown lists only this site's | Bullet 1 ("creates a page or a translation") |
| T4 | B-ROUTE | M2 | Page wizard inherits the source field; its `clean()` overrides the base without `super()` (`cms/forms/wizards.py:22`) | Second implementation skips the shared check | Separate frontend feature in another package that re-checks add rights | Bullet 1 |

**Outcome:** gate passed; fairness NOT READY. DS 1.0 (header; per-trial rows show 2 runs at 1.0, 214 tests). MiMo 1.0 (header; per-trial rows show 2 runs at 1.0). No trap missed.
**Read:** This is a small, form-layer variant of one concept (check view on every copy source). The published fix alone fails only T3+T4, and models closed both. Compared with django-cms-ds: this earlier mined set (published T1/T2, page-type queryset, wizard) is a subset of the -ds set, which folds the wizard shape into its T4 and adds the site-blind helper (T3, dropped here as unfair, made fair there by an explicit cross-site sentence), the GET/POST parent split, tree copy and three injected routes. Both variants scored 1.0/1.0.

### docling-file-disclosure
**Host / advisory:** docling-project/docling, GHSA-P944-4XH2-X776 / CVE-2026-105748, CWE unclear (file disclosure; not in bundle), Python · **Built by:** Opus, build-v1 template, batch 1, 10-17 · **Pattern label:** B · **Traps:** 5
**Base bug:** The Docling JSON backend validates an incoming serialized document and keeps local `ImageRef` URIs. Later embedded/referenced exports read the host file into the output (`docling/backend/json/docling_json_backend.py:57`). The base site has no row of its own; it is covered through S1-S3.
**Symptom as reported:** "`report.md` contains that file's content, base64-encoded." Invariants: "No image reference inside serialized document data ..., in any form and anywhere in the document, may cause docling to read, embed or copy a file"; "This holds wherever docling reads such serialized document data from". Every trap is covered. "Wherever ... reads from" points straight at the loader routes.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | B-ROUTE | M1 | `ConversionAssets.load` validates the archive's `document.json` with no ImageRef filtering (`docling/datamodel/document.py:572-576`) | Other loader of the same serialized data, same sink | Loading your own saved output, not a converter input format | "wherever docling reads such serialized document data from" |
| T2 | B-ROUTE | M1 | Service-client result (in-body JSON) loaded with local image refs (`docling/service_client/client.py:428`, also :1784, :1797-1799) | Other loader, same sink | Your own docling-serve; the bundle path already has a containment guard | Same sentence |
| S1 | SHAPE TRAP | M12 | Picture image as a relative path (landing site) | Spelling variant of the base input | The report's example is absolute | "in any form" |
| S2 | SHAPE TRAP | M12 | Picture image as a `file:` URI (landing site) | Encoding variant | A URI, not a path; docling-core refuses `file:` in some paths | "in any form" |
| S3 | SHAPE TRAP | M12 | Page image (not a picture item) copied by a REFERENCED save (landing site) | Same reference type at another document location | Page images are not document items; the report shows a picture | "anywhere in the document" |

**Outcome:** gate passed; fairness READY. DS 1.0, MiMo 1.0 (1 run each, 265 tests, 0 failing). No trap missed.
**Read:** This is one concept (strip local image refs on every load of serialized docs). The instruction names "wherever ... reads from" and "in any form ... anywhere", so the B routes and shapes are a checklist. Shapes are the M12 class that models always catch. Low bite.

### ec2-fleet-plugin-ds
**Host / advisory:** jenkinsci/ec2-fleet-plugin, GHSA-2X9C-VP3G-HVV2 / CVE-2026-57295, CWE-352 (also filed as CWE-862), Java · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18; a rebuild of jenkins-ec2fleet-authz-inj · **Pattern label:** A (injected) · **Traps:** 6
**Base bug:** The main cloud descriptor's Stapler form helpers (region/fleet listing, connection test) use a stored AWS credential against a caller-chosen region/endpoint with no ADMINISTER check, no `@RequirePOST` and no region/endpoint validation (`EC2FleetCloud.java:978-1072`).
**Symptom as reported:** "the server will go ahead and use the stored credential to talk to the cloud provider for them ... the caller can also steer which host the server contacts." Invariants: no credential use unless the requester "has the right to administer the server **and** the request is a genuine state-changing submission ... for every such operation the plugin exposes, whatever it returns"; "No value of the caller-supplied region or endpoint may cause a credential-bearing call to be directed at a host that is not one of the cloud provider's own endpoints." Every trap is covered. The preservation clause adds that non-admins holding the per-agent delete right must still retire agents (a coupled functional test only, not a manifest trap).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base_authz_and_post | BASE | M12 | Main-cloud form helpers: non-admin GET/POST and admin GET must be refused (`EC2FleetCloud.java`) | The reported sink (role and verb variants) | none | Example + property 1 |
| label_cloud_second_implementation | A-FAR | M2 | Label-based cloud duplicates region/key-pair listing and connection test (`EC2FleetLabelCloud.java:811-886`) | Second implementation of the same helpers | Separate, less-used cloud type | "every such operation the plugin exposes" |
| ec2api_region_lower_level | A-FAR | M8 | Region concatenated into `https://ec2.<region>.<domain>` unvalidated; `evil.com/`, `#`, `@` tricks (`aws/EC2Api.java:181-223` or handlers) | Host-steering half of the bug, lower layer | Indirect helper; a `/`+`:` blocklist looks sufficient | Property 2 ("No value of the caller-supplied region ...") |
| endpoint_lookalike | SHAPE TRAP | M8 | Raw suffix/contains endpoint check accepts `evilamazonaws.com`, `amazonaws.com.evil.example`, userinfo, AWS-looking path (both cloud classes) | Canonicalisation variant of the endpoint input | "ends with amazonaws.com" reads as complete | Property 2 |
| node_hardware_preview_injected | INJ | M1 | Nested `NodeHardwareScaler` `doFillInstanceTypeItems` builds a client from request creds/region/endpoint (`EC2FleetCloud.java`, inject-siblings.patch) | Another web method to the same sink | Nested scaler preview, easy to miss | "every such operation ... whatever it returns" |
| stats_refresh_injected | INJ | M1 | Root-action `doRefresh` forces every cloud `update()` with stored creds (`EC2FleetStatsApi.java`) | Another web method to the same sink | Sits beside the existing no-check stats endpoint | Same |

**Outcome:** gate SOUND (fairness not recorded). DS 1.0, MiMo 1.0 (1 run each, 39 tests, 0 failing). No trap missed.
**Read:** This rebuild reuses the predecessor's six traps unchanged (minus the non-reproducing retirement lever), and the predecessor was already solved 3/3 by both models, so the result was predictable. Permission/POST siblings are one grep-able concept (every `doFill*`/`doTest*`/`do*` web method); the region/endpoint traps are M8 parser checks stated explicitly in property 2.

### jenkins-ec2fleet-authz-inj
**Host / advisory:** jenkinsci/ec2-fleet-plugin, GHSA-2X9C-VP3G-HVV2 / CVE-2026-57295, CWE-862, Java · **Built by:** Opus, build-v1 template, injected track, 10-18 · **Pattern label:** A+B (no B route actually built; both B leads dismissed as unreachable) · **Traps:** 6
**Base bug:** Same as ec2-fleet-plugin-ds. Main-cloud form helpers use a stored credential with no ADMINISTER, no `@RequirePOST`, no region/endpoint validation (`EC2FleetCloud.java:978-1072`).
**Symptom as reported:** Same text as ec2-fleet-plugin-ds without the agent-retirement preservation sentence: "for every such operation the plugin exposes, whatever it returns"; "No value of the caller-supplied region or endpoint may cause a credential-bearing call to be directed at a host that is not one of the cloud provider's own endpoints." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base_authz_and_post | BASE | M12 | Main-cloud helpers: non-admin GET/POST, admin GET refused (`EC2FleetCloud.java`) | The reported sink | none | Example + property 1 |
| label_cloud_second_implementation | A-FAR | M2 | Label cloud duplicates the helpers (`EC2FleetLabelCloud.java:813-860`) | Second implementation | Separate, less-used cloud type | "every such operation" |
| ec2api_region_lower_level | A-FAR | M8 | Unvalidated region builds the service host (`aws/EC2Api.java:181-223`) | Host-steering half, lower layer | Indirect; partial blocklist looks enough | Property 2 |
| endpoint_lookalike | SHAPE TRAP | M8 | Suffix-check lookalike endpoints (both cloud classes) | Canonicalisation variant | "ends with amazonaws.com" looks complete | Property 2 |
| node_hardware_preview_injected | INJ | M1 | Nested scaler instance-type preview helper (`EC2FleetCloud.java`, injected) | Another web method, same sink | Nested optional preview | "every such operation ... whatever it returns" |
| stats_refresh_injected | INJ | M1 | Root-action refresh with stored creds (`EC2FleetStatsApi.java`, injected) | Another web method, same sink | Looks like a companion of the no-check stats endpoint | Same |

**Outcome:** fairness NOT READY (gate passed at build). Post-fairfix: DS 1.0 ×3, MiMo 1.0 ×3 (38-39 tests, 0 failing). Six earlier pre-fairfix runs (16 tests) scored 0.0 for both models: every one failed `adminCanListRegions` and `adminCanTriggerRefresh` (functional tests that used GET while the instruction demanded POST, the contradiction the fairness revision fixed), and 5 of 6 also failed the old direct `EC2Api.getEndpoint` region test (an earlier form of ec2api_region_lower_level, later replaced). Those runs are void, and no trap is missed on the current task.
**Read:** It is one concept swept across web methods plus a stated host allow-list, so models fix everything together. Compared with ec2-fleet-plugin-ds: the trap set is identical (same six ids and tests). The -ds rebuild only removed the unscored retirement hardening from the narrative and added a coupled non-admin retirement functional test, so it could not have bitten harder.

### electron-builder-credential-leakage
**Host / advisory:** electron-userland/electron-builder, GHSA-P2F4-R6V6-J797 / CVE-2026-54673, CWE-200, TypeScript · **Built by:** Opus, build-v1 template, batch 1 (mined), 10-17 · **Pattern label:** A+B · **Traps:** 3
**Base bug:** The shared redirect helper drops only the exact lower-case `authorization` key, so other credential headers (PRIVATE-TOKEN, capitalised Authorization, API keys, cookies, proxy creds) follow a redirect to another origin (`packages/builder-util-runtime/src/httpExecutor.ts:323`).
**Symptom as reported:** "The object-storage host's access logs contain the project access token." Invariants: "No credential attached to a request may reach an origin ... other than the one it was attached for ... for every request the updater and the build and publish tooling make, at every redirect"; "No secret the tooling is given may appear in clear text in an error message or in debug output (`DEBUG=electron-builder`)." Every trap is covered. The redaction invariant is a second, separately stated concept.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Header spellings/kinds (capitalised Authorization, PRIVATE-TOKEN, X-Api-Key+Cookie+Proxy-Authorization) via the Electron updater and Node client (`httpExecutor.ts:323`) | The reported helper, input variants | Adding PRIVATE-TOKEN + case-insensitive Authorization looks enough | "any request header that authenticates the client" |
| T2 | B-ROUTE | M2 | Differential download re-issues redirects with `followRedirect()` and all headers; multi-range path has no listener (`electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264`, `multipleRangeDownloader.ts`) | Own redirect handling that never calls the shared helper | Another package; comments say Electron net handles redirects | "every request the updater ... make, at every redirect" |
| T3 | A-FAR | M4 | Publisher invalid-token errors echo the token; debug log prints JSON request bodies raw (`electron-publish/src/gitHubPublisher.ts:61`, `gitlabPublisher.ts:49`, `httpExecutor.ts:90`) | Second published concept (redaction), other packages | Report is about redirects; logging looks separate | Bullet 2 (errors / debug output) |

**Outcome:** gate_report passed=False; fairness NOT READY. DS 1.0 (1 run). MiMo 0.8, 0.9, 0.8: r1 and r3 missed T2 (both differential tests), r2 missed T3 (debug JSON body). DS missed nothing.
**Read:** T2 is a real second implementation in another package with a misleading comment, and it is the one trap that bit (MiMo 2/3). T3 is a separately stated concept. Partial misses only, no 0.0. The gate_report fail and fairness status mean these runs predate a sound version.

### electron-builder-ds
**Host / advisory:** electron-userland/electron-builder, GHSA-P2F4-R6V6-J797 / CVE-2026-54673, CWE-200, TypeScript · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18/19 · **Pattern label:** A+B, injected · **Traps:** 7
**Base bug:** Same as electron-builder-credential-leakage. The shared redirect helper strips only the lower-case `authorization` key (`httpExecutor.ts:323`).
**Symptom as reported:** "The object-storage host's access logs contain the project access token." Invariants: no credential at another origin, "standard or application-specific, whatever its spelling ... every request the updater and the build and publish tooling make, at every redirect"; "No secret ... may appear in clear text in an error message or in debug output ... whatever the field, option or variable holding it is called." Every trap is covered. Child-process output (T4) is covered only through the general "error message" wording.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_core_redirect_shapes | BASE | M12 | Case/separator variants, X-Amz-Security-Token, cookies, proxy creds, Basic `options.auth`, port change (`httpExecutor.ts:323`) | Reported helper, input variants | Adding the GitLab header + case-insensitive check looks enough | "whatever its spelling"; origin = scheme, host and port |
| T2_block_based_download_redirects | B-ROUTE | M2 | Single-range `followRedirect()` and multi-range no-listener paths (`DifferentialDownloader.ts:260-264`, `multipleRangeDownloader.ts:73,96`) | Own redirect handling bypassing the helper | Blockmap optimisation in another package; comments say Electron handles redirects | "every request the updater ... at every redirect" |
| T3_runtime_redaction | A-FAR | M4 | Request-body debug log, JSON error text, `safeStringifyJson` name detection (apiKey/clientSecret/passphrase/credential) (`httpExecutor.ts:90,209,586`) | Second concept, same library | Existing redactor "already covers token/password" | "whatever the field ... is called" |
| T4_build_config_redaction | A-FAR | M4 | Failed child command's stdout/stderr appended raw; `removePassword` stems; GitHub/GitLab token echoed (`builder-util/src/util.ts:51,186,192`, publishers) | Second concept, other packages | Build-time command output looks unrelated to a redirect | "in an error message" |
| T5_injected_upload_redirect | INJ | M2 | Gitea publisher re-issues a 307 upload to Location with the same headers (`electron-publish/src/giteaPublisher.ts:78`) | Own redirect handling outside the helper | Upload/publisher concern; fix never enters this file | "build and publish tooling ... at every redirect" |
| T6_injected_token_error | INJ | M2 | Gitea publisher echoes a malformed token in its config error (`giteaPublisher.ts:39`) | Copy of the pre-fix GitHub/GitLab pattern | Published fix only edited GitHub/GitLab | "in an error message" |
| T7_injected_debug_config | INJ | M4 | Gitea publisher logs its resolved config, token included, under DEBUG (`giteaPublisher.ts:46`) | Same output decision, new site | Debug-only constructor line looks harmless | "in debug output" |

**Outcome:** gate SOUND; fairness READY. DS raw: 0.875, 0.6875, 0.875, 0.875, 0.75, 0.9375 (plus three earlier per-trial rows at 0.8/0.8667/0.7333). MiMo raw: 0.625, 1.0 (plus earlier 0.6667/0.8667/0.6). From per-test rows: T4 exec-output redaction missed by DS 9/9 and MiMo 4/5. T3 runtime redaction (JSON error text, debug body) missed by DS 4/9 and MiMo 3/5. T2 differential redirect missed by DS 2/9 and MiMo 3/5. T1, T5, T6, T7 and T4's publisher-token part were never missed.
**Read:** The redirect concept, including all three injected Gitea siblings, is solved. What bites is redaction of free-form text (child stdout/stderr, JSON error bodies), a less obvious sink than named fields. It produces partial scores, not 0.0. Compared with electron-builder-credential-leakage: -ds keeps the same T1/T2, splits redaction into runtime (T3) and build (T4) and widens it to exec output and JSON error text, and adds three injected Gitea siblings. The injected traps never bit; the newly scored real exec-output redaction became the most-missed trap.

### fission-ds
**Host / advisory:** fission/fission, GHSA-GX55-F84R-V3R7 / CVE-2026-50564 / GO-2026-5855, CWE-269/284/693, Go · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18 · **Pattern label:** A+B, injected · **Traps:** 6
**Base bug:** Environment admission (`pkg/apis/core/v1/validation.go:655`) accepts a tenant runtime pod spec with `hostPID`/host namespaces/privileged/hostPath/SA, and the controllers put it on platform-created pods. The base site has no row of its own.
**Symptom as reported:** "The object is accepted. The platform then schedules the environment's pods in the node's PID namespace ... including through extra containers, through a serialized pod override, and on later updates and patches." Invariants list the five forbidden settings and cover "every part of these objects that shapes the resulting pods, including structured fields, serialized configuration such as a YAML or JSON fragment, and every container they add ... no metadata may exempt an object"; stored objects "must never yield such pods either". Every trap is covered; the injected ones are named almost verbatim.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M1 | Container-executor Function pod spec at admission (`validation.go:296`) | Second CRD, same pods | Report leads with Environments | "No Environment or Function object" |
| T2 | A-FAR | M5 | Controllers build pods from stored objects via the shared `MergePodSpec` (`pkg/executor/util/merge.go:58-199`) | Stored-object/merge route to the same pods | Admission refuses now; helper carries the trusted operator patch | "Objects that are already stored ... must never yield such pods" |
| T3 | B-ROUTE | M1 | Runtime/builder single-container override fields, unchecked at admission and in `MergeContainer` (`merge.go:35-55`) | Other field reaching the same pods | A convenience container field, not a pod spec | "every container they add" / "every part ... that shapes the resulting pods" |
| S1 | INJ | M1+M7 | `FunctionSpec.Sidecars` appended after the pod-spec merge (`types.go`, `container/deployment.go`) | New field added after sanitisation | Extra containers aren't pod-level; platform adds its own fetcher | "including through extra containers"; "every container they add" |
| S2 | INJ | M8 | `Runtime.PodSpecPatch` strategic-merge string applied after the typed pod spec (`util/podspec_patch.go`) | Serialized nested input not inspected by typed checks | Mirrors the operator's patch; a string, not a typed field | "serialized configuration such as a YAML or JSON fragment" |
| S3 | INJ | M9 | Annotation-keyed admission exemption (`pkg/webhook/legacy.go` + early return) | Bypass switch in front of the check | Reads as operator-set compatibility metadata | "no metadata may exempt an object" |

**Outcome:** gate SOUND (fairness not recorded). DS 1.0, MiMo 1.0 (1 run each, 283 tests, 0 failing). No trap missed.
**Read:** The injected siblings are distinct mechanisms (post-merge append, serialized patch, metadata bypass), but the instruction names each one ("extra containers", "serialized pod override", "no metadata may exempt"), so they read as a checklist. The published fix already touched T1/T2. The likely cause of 1.0/1.0 is over-specification, not weak traps.

### fission-podspec-passthrough
**Host / advisory:** fission/fission, GHSA-GX55-F84R-V3R7 / CVE-2026-50564 / GO-2026-5855, CWE-269/284/693, Go · **Built by:** Opus, build-v1 template, batch 1 (mined), 10-17 · **Pattern label:** A+B · **Traps:** 3
**Base bug:** Same as fission-ds. Environment admission accepts dangerous runtime pod-spec fields, and controllers apply them (`validation.go:655`). The base site has no row of its own (builder pod spec, UPDATE registration and the SA alias are tested but not counted as levers).
**Symptom as reported:** "The object is accepted. The platform then schedules the environment's pods in the node's PID namespace". Invariants: the five forbidden settings; "This covers every part of these objects that shapes the resulting pods ... both when an object is created and on any later update or patch"; stored objects "must never yield such pods either". Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M1 | Function (container executor) pod spec at admission (`validation.go:296`) | Second CRD, same pods | Report is about Environments | "No Environment or Function object" |
| T2 | A-FAR | M5 | Stored objects reach pods through `MergePodSpec` in poolmgr/newdeploy/container/buildermgr (`pkg/executor/util/merge.go`) | Stored-object/merge route | Admission refuses already; operator patches share the helper | "Objects that are already stored ... must never yield such pods" |
| T3 | B-ROUTE | M1 | Runtime and builder single-container overrides unchecked at admission and in `MergeContainer` (`merge.go:35-55`) | Other field to the same pods; the published fix misses it | Convenience container field, not a pod spec | "every part of these objects that shapes the resulting pods" |

**Outcome:** gate passed; fairness NOT READY. DS 1.0, MiMo 1.0 (header). Per-trial rows show 2 runs each at 1.0 (181 and 231 tests). No trap missed.
**Read:** This is one concept (validate every pod-shaping field at admission and sanitise at merge), stated explicitly with the stored-object rule, and models do both. Compared with fission-ds: -ds keeps these three traps and adds three injected ones (sidecars, serialized patch, annotation exemption) while also naming them in its instruction, so the larger set did not bite either.

### flowise-cross-tenant-inj
**Host / advisory:** flowiseai/flowise, GHSA-CHM3-VQCF-52RX / CVE-2026-70472, CWE-285, TypeScript · **Built by:** Opus, build-v1 template, injected track, 10-18 · **Pattern label:** A+B, injected · **Traps:** 4
**Base bug:** The OpenAI vector-store module resolves a caller-supplied `?credential=` id by id alone (`findOneBy({id})`), then decrypts and uses another workspace's secret (`packages/server/src/services/openai-assistants-vector-store/index.ts:13`).
**Symptom as reported:** "the caller gets the external provider to act under another tenant's account". Invariant: "A credential reference ... must never cause the server to decrypt or use a stored secret that does not belong to the caller's active workspace ... for **every** operation that accepts a credential reference — ... query, the path, or the request body, and no matter what the operation returns (data, a status, or nothing)." Every trap is covered, and the "status, or nothing" wording points straight at the injected siblings. Coupled: explicitly shared credentials must still resolve.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base | BASE | M10 | Vector-store routes look up the credential by id alone (`services/` + `controllers/openai-assistants-vector-store/index.ts`) | The reported sink | none | Example + invariant |
| uncovered_assistants | B-ROUTE | M1 | Assistants list/single via `?credential=`, same unscoped lookup (`services/openai-assistants/index.ts:15,43`) | Neighbouring module, same sink | Different feature from the advisory's module | "every operation that accepts a credential reference" |
| sibling_models | INJ | M1 | Added model-listing helper decrypts the key though it returns only model ids (`services/openai-assistants/index.ts:118`) | Another entry, same sink | Read-only output carries no secret | "no matter what the operation returns" |
| sibling_verify | INJ | M1 | Added credential-verification helper, id in the request body, returns only a status (`services/openai-assistants/index.ts:146`) | Another entry, body shape | Diagnostic endpoint for trusted admins | "request body", "a status, or nothing" |

**Outcome:** gate_report passed=False; fairness NOT READY. DS 0.0, 1.0; MiMo 0.0, 0.0, 0.0. Every 0.0 run reports tests=0 (the verifier produced no results: harness/build failure, not a missed sibling). The only run that executed, DS r2, passed 13/13. No trap missed where data exists.
**Read:** This is one concept (scope a credential id to the workspace, honouring shares) at four call sites of the same `findOneBy({id})` pattern, all in two neighbouring modules, and grep finds them all. The 0.0 rewards are infrastructure and must not be read as model failures.

### flowise-ds
**Host / advisory:** flowiseai/flowise, GHSA-CHM3-VQCF-52RX / CVE-2026-70472, CWE-285 (/863), TypeScript · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track per notes), 10-18 · **Pattern label:** A+B, injected · **Traps:** 5
**Base bug:** Same as flowise-cross-tenant-inj. All 7 vector-store routes resolve `?credential=` by id alone and decrypt/use a foreign secret (`services/openai-assistants-vector-store/index.ts:13`).
**Symptom as reported:** "a member of one workspace can ask the server to list the AI provider's resources while naming a credential id from an unrelated workspace". Invariants: never decrypt/use a secret outside the caller's active workspace unless explicitly shared; "every operation ... query, the path, or the request body ... no matter what the operation returns"; "If the request's caller is authenticated but has no active workspace, no credential may be loaded"; "a share recorded for a different kind of resource is not a credential share". Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base | BASE | M10 | 7 vector-store routes; also wrong-item-type share and no-active-workspace shapes (`openai-assistants-vector-store`) | The reported sink (+M9 fail-open shape) | none | Example + all four invariant sentences |
| far_site_oauth | A-FAR | M1 | OAuth2 router, credential id in the path, inline DB access (`routes/oauth2/index.ts:80`) | Published far site, other router | Separate OAuth feature; path not query | "the path" |
| uncovered_assistants | B-ROUTE | M1 | Assistants list/single and `openai-assistants-file` upload, same unscoped lookup (`services/openai-assistants/index.ts:18,46,87`, `routes/openai-assistants-files/index.ts:8`) | Neighbouring module + third router | Never named; file router looks like a storage helper | "every operation that accepts a credential reference" |
| sibling_credential_test | INJ | M1 | `POST /credentials/:id/test` decrypts and calls the provider, returns a boolean (`services/credentials/index.ts:196`) | Another entry, path shape | Diagnostic config validation | "path"; "no matter what the operation returns" |
| sibling_thread | INJ | M1 | `POST /openai-assistants/thread` with credential in the body, returns an opaque id (`services/openai-assistants/index.ts:118`) | Another entry, body shape | Ephemeral object, no tenant data | "request body" |

**Outcome:** gate SOUND (fairness not recorded). DS 0.0, 0.0, 1.0; MiMo 0.0, 1.0. DS r1 and MiMo r1 report only 16 of 32 tests with 0 failing (a partial/aborted verifier; cause unclear, no security failure recorded). DS r2 failed only the functional "a workspace can start OAuth with its own credential" (an over-broad OAuth fix, coupled to far_site_oauth). No security trap was missed in any complete run.
**Read:** Still one grep-able concept (`findOneBy({id})` on credentials); the extra shapes (item-type share, no workspace) are stated outright. The zeros are verifier/over-broad issues, not sibling misses. Compared with flowise-cross-tenant-inj: -ds keeps its base and assistants route, adds the published OAuth2 far site (which -inj left untested), the assistants-file router, two different injected siblings (credential test, thread) and two security sub-shapes. On complete runs, both variants solve every security test.

### ghost-ds
**Host / advisory:** tryghost/ghost, GHSA-HQQ2-XQR2-FMX2 / CVE-2026-105644, CWE unclear (stored XSS via SVG; not in bundle), JavaScript/TypeScript · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18/19 · **Pattern label:** A (injected) · **Traps:** 5
**Base bug:** The content-import image handler picks files by extension and stores SVG (and non-image bytes behind image names) unsanitised into image storage served from the site origin (`ghost/core/core/server/data/importer/handlers/image.js:13`).
**Symptom as reported:** "requesting it from the site's own domain executes the script in the browser of anyone who opens it." Invariants: "A file may be stored as an image only when its contents are an image in one of the site's configured image formats"; SVG-named files sanitised, SVG bytes under other names refused/skipped; "This holds for every path that writes image storage, whatever the asset kind or source." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | Import image handler: unsafe `.svg`, `.svgz`, `.SVG`, SVG/non-image bytes behind raster names, unaccepted format (`importer/handlers/image.js`) | The reported site (name vs content) | none | Example + "depends on its contents" |
| T2 | A-FAR | M1 | Remote media inliner stores fetched bytes under content-type/URL extension, no check (`media-inliner/external-media-inliner.js:185`, `service.js:22`) | Other writer of image storage | Background remote fetcher, not archive files | "every path that writes image storage ... or source"; "remote fetch skips it" |
| T3 | A-FAR | M8 | Direct upload validation trusts client extension + mimetype, no content check (`web/api/middleware/upload.js:347`) | Same name-vs-content gap at the endpoint that already sanitises SVG | Upload already sanitises SVG, so it looks safe | "an upload is refused"; "depends on its contents" |
| T4 | INJ | M2 | CSV import `avatars` asset kind routed through the generic content-file handler into image storage (`importer/content-files.ts:56`) | Bypasses the image handler | Another asset type via the generic file handler | "whatever the asset kind" |
| T5 | INJ | M1 | Bookmark mention-icon cache stores icon bytes under the response extension (`oembed/mention-icon-cache.js`) | Other writer of image storage | Link-preview furniture, not post media | "every path that writes image storage ... or source"; "a link preview still receives its icon" |

**Outcome:** gate SOUND; fairness NOT READY (header). DS: three pre-revision runs at 0.9444 (33 tests) each missed T3 ("upload: refuses SVG bytes named as a raster image"), then 1.0 post-revision. MiMo 0.8636, 0.8636, 1.0: r1 missed T2 (SVG served as raster; skipped file must not stop the next) and T3 (SVG-as-raster upload); r2 missed T3 (all three upload tests). T1, T4, T5 never missed.
**Read:** The siblings that bite are the real A-FAR sites that already look protected or remote (T3's upload sanitises SVG; T2's content-type routing). The injected siblings were caught. It is one concept (content-sniff every image write), but T3 needs a content check added where a partial guard already exists, which is a genuine M8 trap. Partial scores only.

### gogs-ds
**Host / advisory:** gogs/gogs, GHSA-5C3F-6486-3G7G / CVE-2026-52809 / GO-2026-5140, CWE unclear (insufficient token expiration; not in bundle), Go · **Built by:** DeepSeek-driven pilot (build-v1 template, injected track), 10-18 · **Pattern label:** B, injected · **Traps:** 5
**Base bug:** The reset-password mail mints its code with the account-activation generator, so the code carries the activation lifetime; the verifier trusts the embedded minutes and is purpose-blind (`internal/email/email.go:228`).
**Symptom as reported:** "a password-reset link mailed in response to a reset request still sets a new password when it is used two minutes later." Invariants: "A password-reset code may be accepted only while the configured password-reset lifetime is running, wherever a password reset is started or completed"; "A code issued to activate an account must never be accepted as a password-reset code, and the reset-code validity check must not report it as usable." Every trap is covered. The System paragraph also lists the web API, "the compatibility reset form" and the admin reset link.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| t1_reset_lifetime | BASE | M6 | Reset mail mints with the activation generator; verifier trusts the producer's lifetime (`internal/email/email.go:228`) | The reported site | Changing the mail generator looks complete | Example + property 1 |
| t2_activation_purpose | B-ROUTE | M4 | Reset completion uses the purpose-blind shared verifier; an activation code resets a password (`cmd/gogs/internal/web/webapi_user.go:246`) | Second half of the advisory (purpose binding never existed) | Codes always shared one format/verifier; binding looks like a redesign | Property 2 |
| t3_validity_probe_purpose | B-ROUTE | M1 | Reset-code validity probe reports an activation code as valid (`webapi_user.go:188`) | Read-only route through the same verifier | Read-only, UI-only | "the reset-code validity check must not report it as usable" |
| t4_admin_reset_lifetime | INJ | M2 | Admin `SendPasswordResetLink` mints with the activation generator directly (`internal/route/admin/users.go:223`) | Second producer not routed through the fixed sender | Admin-only operator action | "wherever a password reset is started"; System names the admin link |
| t5_legacy_purpose | INJ | M2 | Compatibility reset form carries its own copy of the purpose-blind verifier (`internal/route/user/setting.go:295`) | Duplicate verifier outside the shared helper | Legacy endpoint, not the web API | Property 2; System names "the compatibility reset form" |

**Outcome:** gate SOUND (fairness not recorded). DS 1.0, MiMo 1.0 (1 run each, 37 tests, 0 failing). No trap missed.
**Read:** t2 is a genuinely different concept (purpose binding) from the reported lifetime bug, but property 2 states it outright. The System paragraph enumerates every entry point, including both injected ones, which turns the task into a checklist. Fair, but over-specified.

### flyto-core-path-traversal
**Host / advisory:** flytohub/flyto-core, GHSA-2956-977X-2W3R / CVE-2026-67429, CWE-22/CWE-73, Python · **Built by:** Opus build-v1 template, batch 1 (10-17), mined (no injection) · **Pattern label:** A+B · **Traps:** 10
**Base bug:** Workflow modules write caller-chosen output paths outside `FLYTO_SANDBOX_DIR`. The report leads to `image/download.py:139-143`. Its commonpath check compares `output_path` with the caller's own `output_dir`, so it does nothing, and the parent mkdir runs before the check.
**Symptom as reported:** `image.download` with `output_path: /var/www/html/logo.png` succeeds, so "any API client can write files anywhere". Invariants: "No caller-supplied parameter of any module run may cause a file or directory outside the sandbox to be created, overwritten, appended to or removed. This covers every file a module writes, for any purpose ... locations the module derives itself"; "however the location is spelled: absolute, relative, with `..` ... symbolic link"; "That includes directories the run would otherwise have created". Every trap has a covering invariant.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M4 | paginator checkpoint state file: browser/pagination.py -> core/browser/checkpoint.py | published site; a save/reload state file, written each page and removed at the end | "internal resume state, not an output file" | "every file a module writes, for any purpose"; "removed" |
| T2 | A-FAR | M1 | document/{excel_write,pdf_fill_form,pdf_to_word,word_to_pdf}.py | published sites in another package | the example is an image module | "any module run"; "not the full set of affected modules" |
| T3 | B-ROUTE | M8 | data/csv_write.py, data/json_to_csv.py: `'..'` substring check only | real gap; absolute paths pass | already has a traversal check | "however the location is spelled: absolute" |
| T4 | B-ROUTE | M1 | file/copy.py, file/move.py: no check; move removes an outside source | real gap beside the guarded file.write | generic file operations, not named | "created, overwritten ... or removed" |
| T5 | B-ROUTE | M1 | document/word_parse.py images_output_dir: same no-op check as the landing site | real gap in a reader module | a parser; the file names are generated | "every file a module writes, for any purpose" |
| T6 | B-ROUTE | M1 | document/pdf_generate.py: no check | real gap in a content generator | generates content; not in the report | "any module run" |
| T7 | SHAPE TRAP | M8 | symlink inside the sandbox resolving outside (via image/rotate.py) | spelling variant | a lexical prefix check looks enough | "through a symbolic link inside the sandbox" |
| T8 | SHAPE TRAP | M8 | absolute path outside vs `..`-only rejection; includes the qrcode .png->.svg rewrite | spelling variant | rejecting `..` looks like the traversal fix | "absolute, relative, with `..`" |
| T9 | SHAPE TRAP | M5 | derived default output (resize, download, word_to_pdf) | default-location route | only explicit paths look attacker-controlled | "locations the module derives itself" |
| T10 | SHAPE TRAP | M7 | mkdir before the check (download, convert, excel_write) | side effect before validation | the run is refused, so it looks blocked | "includes directories the run would otherwise have created" |

**Outcome:** gate_report passed=True; fairness NOT READY. Raw DS 0.96, 1.0; MiMo 0.96, 1.0. Both first post-fairfix runs (69 tests) failed only `test_qrcode_svg_outside` (T8; this is the check-before-.svg-rewrite case). Both second runs scored 1.0. Before the fairfix (10-17, 67 tests), DS scored 0.0 three times on functional failures only: the project checkpoint tests (a sink guard broken by the TMPDIR test artefact, later repaired) and once `test_excel_write_inside`. These were not missed siblings.
**Read:** Every sibling is one concept: "validate every write location against the sandbox". Once the invariant says "every file ... any purpose", a model that sweeps writers fixes them together. That is why this build missed the bar. The only miss was a check placed before the path rewrite (M7 flavour), seen in one run per model.

### flyto-core-ds
**Host / advisory:** flytohub/flyto-core, GHSA-2956-977X-2W3R / CVE-2026-67429, CWE-22/CWE-73, Python · **Built by:** DeepSeek-built pilot (10-18), injected track · **Pattern label:** A+B · **Traps:** 13
**Base bug:** Same as flyto-core-path-traversal. The landing site `image/download.py:140-141` has a caller-relative commonpath no-op, plus a derived name and mkdir before the check at `:34-36`.
**Symptom as reported:** The same `image.download` example. Invariants: "No caller-supplied value may cause a file or directory outside the sandbox to be created, overwritten, appended to or removed ... the module's main output, extra files it keeps beside it, and locations it derives itself"; "applies to every value that becomes part of a location ... A name, label or file name that a module joins into a location"; "files it would otherwise have removed". Every trap is covered. The name clause points almost directly at T10, T11 and T13.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M10 | image/download.py: check against the caller's own output_dir; derived name; mkdir first | reported site | it already has a realpath/commonpath check | the example itself |
| T2 | A-FAR | M1 | image/{compress,convert,crop,resize,rotate,watermark,qrcode_generate}.py incl. symlink and .svg rewrite | published sites in the same package | the report names one image module | "not the full set of affected modules" |
| T3 | A-FAR | M1 | document/{excel_write,pdf_fill_form,pdf_to_word,word_to_pdf}.py incl. derived defaults | published sites in another package | the example is an image module | "any ... value"; "locations it derives itself" |
| T4 | A-FAR | M4 | browser/pagination.py -> core/browser/checkpoint.py; .jsonl sibling; removal at the end | published save/reload state file | internal resume state, not an output | "extra files it keeps beside it"; "removed" |
| T5 | B-ROUTE | M8 | data/csv_write.py, data/json_to_csv.py: `..`-only check | real gap; absolute paths pass | already has a traversal check | "absolute, relative, with `..`" |
| T6 | B-ROUTE | M1 | file/copy.py, file/move.py: destination, plus a move source outside (removal) | real gap beside the guarded file.write | generic file operations | "created ... or removed" |
| T7 | B-ROUTE | M1 | document/word_parse.py: image extraction directory with the same no-op check | real gap in a reader | a parser; the names are generated | "every file a run writes" |
| T8 | B-ROUTE | M1 | document/pdf_generate.py, verify/report.py, warroom/report.py | real gaps in generators and reporting | reporting side feature, not a transform | "for any purpose" |
| T9 | B-ROUTE | M4 | data/dedup.py hash_file, plus a .tmp sibling and a rename | real gap in a cache file | bookkeeping, not an output | "extra files it keeps beside it" |
| T10 | B-ROUTE | M10 | verify/report.py: report `name` joined onto a validated output_dir | real gap; the check covers the directory, not the final file | the name is a label; output_dir is the path | "A name, label or file name that a module joins" |
| T11 | INJ | M10 | image/thumbnail.py: validated output_dir plus an unvalidated caller name | planted name-joined-after-check | the directory is already guarded | the name/label clause |
| T12 | INJ | M1 | document/pdf_metadata.py: guarded output, but the original is copied to a caller backup_path first | planted second destination option | a backup copy is not an output | "every file a run writes ... for any purpose" |
| T13 | INJ | M7 | image/gallery_export.py: clears the caller dir before validating it; caller prefix joined into names | planted destructive side effect before the check | clearing is housekeeping | "files it would otherwise have removed"; name clause |

(Note: notes.md swaps the T9/T10 labels. This table follows manifest.traps.)
**Outcome:** gate UNSOUND, although notes.md reports static/nop/oracle passing and patches passing only through a manual per-check rerun after the Docker network race; the bundle does not give the UNSOUND reason. No trials (no DS or MiMo rewards); no per-test data.
**Read:** Compared with flyto-core-path-traversal, this build keeps all 10 of its levers (renumbered). It adds real B routes (verify/warroom reports, the dedup cache, a report name joined into the path) and three injected siblings: a name joined after a validated directory, a backup copy, and clear-before-check. The new M10/M7 siblings are a different concept from "validate the path parameter", but the instruction's name clause and "removed" clause name them almost directly. About 20 files must be changed, so breadth adds as much difficulty as concept does.

### flyto-core-mm
**Host / advisory:** flytohub/flyto-core, GHSA-2956-977X-2W3R / CVE-2026-67429, CWE-22/CWE-73, Python · **Built by:** MiMo-built pilot (10-18), injected track (the header says track None, but notes.md says INJECTED) · **Pattern label:** A+B · **Traps:** 16
**Base bug:** Same as flyto-core-path-traversal. The landing site `image/download.py` checks against the caller-supplied base and runs mkdir first.
**Symptom as reported:** The same example. Invariants: "covers every file a module writes, for any purpose — primary outputs, copies of earlier contents, side outputs a caller opts into, state a run keeps across pages or calls, extracted media, anything"; "file names or sub-paths taken from the data a module is processing rather than from a path parameter"; "A spelling that is only checked for `..` while still accepting absolute destinations is not enough"; "Optional extra destinations a caller names inside the sandbox keep working". Every trap is covered. The instruction comes close to listing the siblings (backup, opt-in side output, state, data-derived names).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M4 | browser/pagination.py -> core/browser/checkpoint.py save/clear | published state file | internal resume state | "state a run keeps across pages or calls" |
| T2 | A-FAR | M1 | document/{excel_write,pdf_fill_form,pdf_to_word,word_to_pdf}.py incl. derived defaults | published sites in another package | the example is an image module | "any module run"; derived locations |
| T3 | A-FAR | M1 | image/{compress,convert,crop,resize,rotate,watermark,qrcode_generate}.py incl. symlink and .svg | published sites in the same package | "same package, I got them all" | "not the full set of affected modules" |
| T4 | B-ROUTE | M8 | data/csv_write.py, json_to_csv.py: `..`-only check plus mkdir first | real gap | already has a path check | "only checked for `..` ... is not enough" |
| T5 | B-ROUTE | M1 | file/copy.py, file/move.py: destination unchecked; move removes an outside source | real gap | file.write next door is guarded | "created ... or removed" |
| T6 | B-ROUTE | M1 | document/word_parse.py images_output_dir | real gap in a reader | the module reads; the report is about writes | "extracted media" |
| T7 | B-ROUTE | M1 | document/pdf_generate.py: no check | real gap in a generator | not a converter of an existing file | "primary outputs" |
| T8 | B-ROUTE | M4 | data/dedup.py hash_file (mkdir before check) | real gap in a cache file | a state file, not an output | "state a run keeps across ... calls" |
| T9 | INJ | M1 | file/write.py: optional backup_path copy beside the guarded primary path | planted second destination (manifest labels it "B") | the module already validates its path | "copies of earlier contents" |
| T10 | INJ | M1 | storage/kv.py: optional file_path extra file on a KV store | planted option on a module with no other path parameter (manifest "B") | a KV store, not a file-output module | "side outputs a caller opts into" |
| T11 | INJ | M10 | data/export_records.py: output_dir checked; per-record name from the data not checked | planted data-derived names (manifest "B") | names come from records, not a path parameter | "file names ... taken from the data" |
| T12 | SHAPE TRAP | M5 | guard only explicit path parameters (derived defaults, data names left open) | shape across sites | the example passes an explicit path | "locations the module derives itself" |
| T13 | SHAPE TRAP | M7 | parent mkdir before the guard (download, convert, json_to_csv, dedup, backup, kv) | side effect before validation | the file is refused, so nothing seems to happen | "includes directories ... created" |
| T14 | SHAPE TRAP | M8 | `..`-substring rejection only | spelling variant | house style of the csv writers | "only checked for `..` ... not enough" |
| T15 | SHAPE TRAP | M8 | normpath instead of realpath | symlink variant | normpath looks standard | "symbolic link inside the sandbox" |
| T16 | BASE | M10 | image/download.py: compares against the caller base instead of the sandbox | the landing bug (manifest labels it "shape") | there is already a check there | the example itself |

**Outcome:** no gate marker; no trials; no per-test data.
**Read:** Compared with path-traversal, this build has the same published and B base plus dedup. Compared with flyto-core-ds, it plants three different siblings on the same two ideas: a second destination option (backup_path, kv file_path) and a name joined after a checked directory (export_records). The instruction spells out each sibling class ("copies of earlier contents", "side outputs a caller opts into", "names ... from the data"). That makes the task fair, but it removes most of the "different concept" bite. Expect models to sweep them together.

### grav-info-exposure-inj
**Host / advisory:** getgrav/grav, GHSA-MC5Q-6HPJ-RP7J / CVE-2026-61450 / CVE-2026-61842, CWE-200, PHP (Twig) · **Built by:** Opus build-v1, injected track (10-18) · **Pattern label:** A+B · **Traps:** 3
**Base bug:** Sandboxed page-body Twig reaches the raw Config through the container accessor (`grav.offsetGet('config')`) and prints it with serialize/reflect helpers (`print_r`, `json_encode`, `yaml_encode`, `vardump`), or reflects the redacting facade's private state. On the real `processPage`/`processString` path, `isSandboxed()` is false. The landing site is the helper registrations in GravExtension.php and the security.yaml allowlist.
**Symptom as reported:** "the rendered output discloses private configuration values ... for example a configured plugin credential". Invariant: "No templating expression in page-body content may cause any configuration value that is hidden ... to appear ... regardless of which template construct is used to reach it, and whether the value is read singly, in bulk, or by any indirect route"; operator templates "must keep full, unredacted access". Both siblings are covered by "any construct ... singly ... indirect".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base | BASE | M8 | GravExtension.php dump/serialize registrations + security.yaml allowlist + Twig render scope; nested lists; object carrying config (grav.theme) | published sink; the helpers see raw state the member gate hides | allowlist looks like config; `isSandboxed()` looks sufficient but is false on the real path | "any configuration value ... in bulk, or by any indirect route" |
| sibling_export | INJ | M2 | GravExtension.php: added `export` filter (var_export) beside print_r | another reflective dumper outside the named family | reads as a value-formatting helper | "regardless of which template construct" |
| sibling_accessor | INJ | M2 | GravExtension.php: added `theme_config()` reading raw config from the container, past the facade | another config read path that skips the redacting facade | a targeted convenience reader, not a bulk dump | "read singly" |

**Outcome:** gate_report passed=False; fairness NOT READY. Raw DS 1.0 x3; MiMo 1.0 x3 (all after the fairness revision, 24 tests). Before the revision (19 tests), DS twice missed sibling_accessor (`testConfigAccessorScalar/Subtree`) and also broke the trusted `export` functional test. MiMo missed base (serialize/reflect/yaml/list), sibling_export and sibling_accessor in various runs. On 10-18 13:45 DS scored 0.0 on functional failures only (an over-broad guard on legitimate dumps). After the revision, nothing was missed.
**Read:** The siblings are more helpers of the same "printer leaks object state" concept, and a broad per-helper guard with recursive normalisation covers them all, which is what both models did. The accessor was the only distinct idea (a targeted read that skips the facade), and it bit only before the revision. Fairness was flagged (test artefacts; NOT READY).

### grav-ds
**Host / advisory:** getgrav/grav, GHSA-MC5Q-6HPJ-RP7J, CWE-200, PHP (Twig) · **Built by:** DeepSeek-built pilot (10-18), injected track · **Pattern label:** A+B · **Traps:** 6
**Base bug:** Same as grav-info-exposure-inj: the container accessor returns the raw Config, and dump/serialize helpers print it or reflect the facade. The landing site is GravExtension.php:148-165,190-219 plus security.yaml:340, and `isSandboxed()` is false on processPage/processString.
**Symptom as reported:** Same impact text, a standard page view. The invariant is broadened: "regardless of which template construct or which formatting, conversion, serialization, dump or display helper is used ... singly, in bulk, or by any indirect route; and whether it is reached directly or through another object that carries it". Every trap is covered. The "conversion" and "object that carries it" wording points at the B routes.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base | BASE | M8 | GravExtension.php registrations, security.yaml allowlist, Twig.php render scope; lists/hashes holding config | published sink | allowlist is config; encoder is vendor code; `isSandboxed()` looks sufficient | "any configuration value ... in bulk ... indirect route" |
| string_function | B-ROUTE | M1 | GravExtension.php:216 `string()` function form -> stringFilter raw encoder (the filter form is guarded upstream) | same helper, other registration list | the report talks about filters; looks like a scalar cast | "which ... conversion ... helper" |
| array_cast_yaml | B-ROUTE | M6 | GravExtension.php arrayFilter/yamlFilter: a cast flattens an object carrying config; the second YAML printer prints it | the producer (cast) feeds a printer whose own object check never sees the object | a cast is not a dump; YAML alone refuses objects | "through another object that carries it"; "conversion" |
| sibling_to_json | INJ | M2 | GravExtension.php: added pretty-print `to_json` filter and function calling the raw encoder | another serializer | a formatting helper next to a decoder | "formatting ... serialization ... helper" |
| sibling_inspect | INJ | M2 | GravExtension.php: added always-on `inspect()` that flattens via toArray()/cast and returns text | another reflective dumper | a page-display helper, not a debug dump | "dump or display helper" |
| sibling_accessor | INJ | M2 | GravExtension.php: `theme_config()` reading raw config past the facade (scalar and subtree) | another config read path skipping the facade | a targeted convenience reader | "read singly" |

**Outcome:** gate SOUND. Raw DS 1.0 (1 run); MiMo 1.0 (1 run); 50 tests, 0 failing. Nothing missed.
**Read:** Compared with grav-info-exposure-inj, this build keeps base and theme_config, drops `export`, and adds two real B routes (the `string()` function form and array/yaml cast) plus two new injected printers (to_json, inspect). The broadened invariant lists helper families, so a broad "guard every printer and normalise recursively" fix still covers everything. Only array_cast_yaml (M6) is a somewhat different concept, and it did not bite.

### grav-mm
**Host / advisory:** getgrav/grav, GHSA-MC5Q-6HPJ-RP7J, CWE-200, PHP (Twig) · **Built by:** MiMo-built pilot (10-18; built about 3 h before grav-ds), injected track · **Pattern label:** A+B · **Traps:** 5
**Base bug:** Same as the other grav tasks (container accessor plus dump/serialize helpers; `isSandboxed()` false on the real content path).
**Symptom as reported:** The impact text matches grav-info-exposure-inj; the properties match grav-ds word for word ("which formatting, conversion, serialization, dump or display helper ... through another object that carries it"). Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base | BASE | M8 | GravExtension.php registrations + security.yaml allowlist + Twig render scope; lists/hashes holding config | published sink | allowlist is config; `isSandboxed()` looks sufficient | "any configuration value ... in bulk" |
| string_function | B-ROUTE | M1 | GravExtension.php `string()` function: the array branch calls the raw encoder (function-form tests only) | same helper, other registration | looks like a scalar cast; private encoder call | "conversion ... helper" |
| array_cast_yaml | B-ROUTE | M6 | GravExtension.php array filter/function + yaml filter: the cast exposes protected state that a printer outputs | the producer (cast) feeds the printer | a cast is not a dump; Symfony YAML refuses objects | "through another object that carries it" |
| sibling_to_json | INJ | M2 | GravExtension.php: added `to_json` filter and function beside json_decode | another serializer | pretty-print helper | "formatting ... serialization" |
| sibling_inspect | INJ | M2 | GravExtension.php: added `inspect()` readable dump beside vardump/dump | another reflective dumper | returns a string; not the dump family | "dump or display helper" |

**Outcome:** no gate marker; no trials; no per-test data.
**Read:** This build is grav-ds without the theme_config accessor (same base, the same two B routes, the same two injected printers). Its design leaned on DeepSeek's observed gap, the unguarded `string()`, in grav-info-exposure-inj. Since grav-ds, a superset, was solved 1/1 by both models, this set is very likely solved too. Plan dropped L5 (raw system/site/theme template variables) because they carry no withheld paths.

### handlebars-path-read-inj
**Host / advisory:** jknack/handlebars.java, GHSA-G29J-RWFV-H99W / CVE-2026-63490, CWE-22, Java · **Built by:** Opus build-v1, injected track (10-17/18) · **Pattern label:** A+B · **Traps:** 5
**Base bug:** `SpringTemplateLoader.getResource/resolve` (handlebars-springmvc) builds a URL location from prefix + name + suffix. A `#` or `?` in the name truncates the suffix, a caller-supplied protocol is kept, and there is no prefix boundary. The far site `HandlebarsViewResolver.configure` passes unsafe view names straight through.
**Symptom as reported:** "a single request that carries a crafted template name causes the server to read and render a file that is not a template in the configured area". Invariants: no name may read "outside the configured template location" (traversal, embedded scheme, absolute), no file of a different "extension" ("fragment or query delimiter"), and "for every way a name enters the engine ... and for every configured backing location (filesystem, classpath, servlet context, and framework resources)". Every trap is covered. The backing-location list points at both injected loaders.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| spring_suffix_bypass | BASE | M8 | SpringTemplateLoader.java:57-77: `#`/`?` in the name truncates the suffix under URL parsing | reported sink | none (obvious lever) | "fragment or query delimiter that truncates" |
| spring_traversal_boundary | SHAPE TRAP | M8 | SpringTemplateLoader.java:57-63: `..` climbs out of the prefix | same sink, traversal shape | assumes the resource layer normalises `..` | "relative traversal to climb out" |
| view_resolver_name | A-FAR | M1 | HandlebarsViewResolver.java:163-178 configure: reject protocol/fragment/traversal view names | published far site in the web layer | looks redundant once the loader is hardened | "every way a name enters (view names ...)" |
| file_loader_protocol_passthrough_injected | INJ | M2 | io/FileTemplateLoader.java: `file:` name treated as an absolute URL, skipping base dir and suffix | second loader implementation with the same flaw | URI-style names look like a neighbouring feature | "filesystem" backing; "names that embed their own location or scheme" |
| servlet_loader_absolute_fastpath_injected | INJ | M2 | io/ServletContextTemplateLoader.java: leading-slash fast path skips normalise + boundary | second loader implementation | a legacy path; the container is trusted | "servlet context" backing; traversal |

**Outcome:** no gate marker; no trials; no per-test data.
**Read:** All siblings are the same concept: bound every loader's resolved location to its prefix and suffix. The instruction lists each backing location explicitly, so a model that writes a shared name validator in the abstract loader fixes them together. It is unclear whether a loader-only fix also satisfies the view-resolver tests (the stub collaborators may hide this).

### hazelcast-ds
**Host / advisory:** hazelcast/hazelcast, GHSA-6V25-8WQ6-XQ4J / CVE-2026-107726, CWE-470, Java · **Built by:** DeepSeek-built pilot (10-18/19), injected track · **Pattern label:** A+B · **Traps:** 9
**Base bug:** Compact zero-config deserialization constructs the class named by a client-supplied schema type name. `CompactUtil.verifyClassIsCompactSerializable` runs only after `createObject`, at CompactStreamSerializer.java:246-263 and ReflectiveCompactSerializer.java:144-158.
**Symptom as reported:** "a Compact value whose type name denotes a platform-internal or JDK class comes back from the member as an instance of that class". Invariants: "No class may be constructed, even transiently, before it is found eligible"; "not eligible when ... belongs to the platform's own implementation ... every package the platform ships, not only packages named 'internal'"; "at any depth and any position within a value, and whether the schema travels in the schema service or inside the binary"; nested ineligible values must be read as generic records. Every trap is covered after the fairness revision.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base_instantiation_order | BASE | M7 | CompactStreamSerializer / ReflectiveCompactSerializer: construct before the eligibility check | reported site | verifyClassIsCompactSerializable looks like the guard | "No class may be constructed, even transiently" |
| default_block_list | A-FAR | M9 | DefaultSerializationServiceBuilder.java:310-335 default block list (HeapData, Packet, UnsafeObjectDataInput; schema in binary) | published defaults site | a client never sends internal transfer types | "platform's own implementation"; "inside the binary" |
| nested_positions | A-FAR | M1 | ValueReaderWriters.java + ReflectiveCompactSerializer nested readers (field, list, map value/key) | nested read paths reach the same construction | the top-level decision looks like it covers nested values | "at any depth and any position"; generic-record fallback |
| record_implementation | A-FAR | M2 | record/JavaRecordSerializer.java, JavaRecordReader.java components | second serializer implementation | records use the canonical constructor | "any position"; "including ... records" |
| uncovered_member_internal | B-ROUTE | M9 | com.hazelcast.instance.impl.HazelcastInstanceProxy not blocked | real gap in the default list | member internals are never sent | "every package the platform ships" |
| uncovered_discovery_reader | B-ROUTE | M9 | KubernetesConfig$DefaultFileContentsReader not blocked | real gap in the default list | a discovery helper in another subsystem | same |
| uncovered_connector | B-ROUTE | M9 | jet.impl.connector.DataSourceFromJdbcUrl not blocked | real gap in the default list | a connector, no no-arg constructor | same |
| sibling_serialization_machinery_class | INJ | M9 | internal/serialization/impl/SerializationServiceStatistics (new eligible class) | planted product class the list misses | serializer machinery reads as trusted | same |
| sibling_array_element_accessor | INJ | M2 | CompactInternalGenericRecord.getArrayOfObject -> new readArrayElement building a registration directly | planted duplicate read path that skips eligibility | an accessor looks read-only | "any position"; array/map elements |

**Outcome:** gate SOUND; fairness NOT READY. Raw DS 1.0, 1.0 (final 32-test runs). The earlier pre-revision 30-test DS runs scored 0.1765, 0.7647 and 0.1765, missing the B routes, the injected class, nested, record and default-list cases. Raw MiMo 0.8421, 0.7895 (the per-trial rows also show an earlier 0.8421). Every MiMo run missed nested_positions (`nestedConcreteFieldIsReadAsGenericRecord`, `nestedCounterFieldIsNotConstructed`) and record_implementation (`recordConcreteComponentIsReadAsGenericRecord`; r3 also `recordComponentIsNotInstantiated`).
**Read:** The concepts differ in a useful way: construction ordering versus "the platform's own packages" (a denylist breadth gap) versus nested and record readers. MiMo's misses cluster on the nested generic-record fallback contract that the fairness revision tightened. That looks partly like contract strictness rather than a missed sibling, so it needs an audit before it counts.

### hermes-agent-ds
**Host / advisory:** nousresearch/hermes-agent, GHSA-33QV-C5QM-799V / CVE-2026-10223, prompt injection (CWE not given in the bundle), Python · **Built by:** DeepSeek-built pilot (10-18/19), injected track · **Pattern label:** A+B · **Traps:** 9
**Base bug:** Project instruction files are loaded into the system prompt through `_scan_context_content` (agent/prompt_builder.py:55). That scanner blocks only classic injection phrases, not C2/"promptware" text. The published fix also scans memory writes and loads, and wraps external tool results in an envelope.
**Symptom as reported:** A checked-in instruction file with a "housekeeping" paragraph (register in a mesh, adopt a new name) is followed; "the same paragraph placed in a memory file, supplied by a configured memory source, or returned by an external-content tool has the same effect". Invariants: block workspace guidance "for every instruction-file convention and every discovery path"; memory must not reach the prompt "however it was written and whichever memory source supplied it"; external tool results wrapped `<untrusted_tool_result ...>` "wherever such a result becomes a model message, not only on the primary execution path". Every trap is covered, with near-explicit pointers.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_context_scanner | BASE | M12 | agent/prompt_builder.py:55 (+ subdirectory_hints.py:188): promptware, filler-word and invisible-unicode variants | reported site | a scanner already blocks classic phrases | the example; "every discovery path" |
| T2_memory_write_scan | A-FAR | M2 | tools/memory_tool.py:137 separate memory scanner misses promptware | second scanner implementation | memory writes are already scanned | "however it was written"; refused write -> `success: false` |
| T3_memory_snapshot | A-FAR | M5 | tools/memory_tool.py:201-217 load_from_disk -> frozen snapshot, no scan | stored-object (save/reload) route | writes are scanned, so a load scan looks redundant | "Persistent memory content must not reach the system prompt" |
| T4_tool_envelope | A-FAR | M4 | agent/tool_dispatch_helpers.py:320: no untrusted envelope (web/search/browser/mcp, plus x_search missing from the set) | a new defence class (envelope), not a scanner | a message builder is not a context loader | the explicit envelope contract |
| T5_provider_block | B-ROUTE | M1 | agent/memory_manager.py:318-335 provider system_prompt_block() joined unscanned | another source into the prompt | plugin code is trusted | "whichever memory source supplied it" |
| T6_recall_fence | B-ROUTE | M1 | agent/memory_manager.py:227-241 recalled context fenced as authoritative, tags stripped only | another source; a fence that looks like a defence | already inside a fence | "recalled memory"; "whichever memory source" |
| T7_codex_mcp | B-ROUTE | M2 | agent/transports/codex_event_projector.py:217-253 builds role=tool messages directly | alternate transport bypassing the builder | a separate runtime with its own loop | "not only on the primary execution path" |
| T8_clinerules_loader | INJ | M2 | agent/prompt_builder.py:1426 `.clinerules` loader without the scan call | a copied loader that skips the shared scanner | five other loaders do scan | "every instruction-file convention" |
| T9_memory_import | INJ | M1 | tools/memory_tool.py:454 bulk `import` action merges into live state and snapshot unscanned | another write action | add/replace and load are fixed | "however it was written" |

**Outcome:** gate SOUND. Raw DS 0.5417, 0.625, 1.0; MiMo 0.9167, 0.0, 0.625. DS r1 missed T1 (filler/invisible), T4 (all 7 tools incl. x_search) and T7; DS r2 missed T4 and T7. MiMo r1 missed the T1 shapes; MiMo r3 missed T4 and T7. In MiMo r2 all 24 security tests failed (no effective fix; a null run, not a sibling signal).
**Read:** The siblings that bit are T4 (a new envelope defence; M4) and T7 (an alternate transport; M2). They are a different concept from "upgrade the scanner", and they bit in 3 of 6 runs even though the instruction states the envelope contract and "not only on the primary execution path". Scanner, memory and loader siblings were fixed together, as expected. The T1 vocabulary misses depend on regex coverage of "filler-word and invisible-unicode" spellings; this is a judgement call for fairness.

### hubuum-client-rust-ds
**Host / advisory:** hubuum/hubuum-client-rust, GHSA-2625-RW7M-5Q5X, CWE-532, Rust · **Built by:** DeepSeek-built pilot (10-18/19), injected track · **Pattern label:** A+B · **Traps:** 9
**Base bug:** `ApiError::HttpWithBody` `Display`/`Debug` (src/errors.rs:58,151) prints the server's message and response body. The published fix also redacts other error arms, runner errors and many result-type `Debug` impls.
**Symptom as reported:** "An application that logs a failed call with `{}` or `{:?}` writes the server's error message and response body into its log". Invariants: "No server-supplied content and no caller-supplied secret may appear in the default `Display` or `Debug` representation of any error or result value ... nested values ... source chain"; "both the asynchronous and the blocking interface, and for every shape of result"; ids, names, statuses and counts must stay visible. Every trap is covered. "result value" covers B1-B3 and S3.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_http_envelope | BASE | M12 | src/errors.rs:58,151 HttpWithBody Display/Debug (JSON message and plain-text body) | reported site | none | the example |
| T2_decode_retry | A-FAR | M1 | src/errors.rs Json/Deserialization/RetryExhausted arms + source; client send_with_retry | other error arms in the same enum and its source chain | codec/retry detail, not HTTP text | "any error ... source chain" |
| T3_high_level_runners | A-FAR | M2 | src/client/async.rs + sync.rs export/backup run operations embed the task summary | async and blocking duplicates | a summary reads as status; blocking is a non-default feature | "both the asynchronous and the blocking interface" |
| T4_result_models | A-FAR | M4 | src/types/{task,event,export,import,remote}.rs, client/shared.rs derived Debug | result structs never redacted | plain data the caller already holds | "any ... result value"; "nested values" |
| B1_audit_event | B-ROUTE | M4 | src/types/event.rs:7-35 audit event snapshots/metadata | real unredacted result type | audit content is meant to be read | "every shape of result" |
| B2_restore_stage | B-ROUTE | M4 | src/types/backup.rs:233 RestoreStageResponse.error hand-written Debug | real unredacted result type | the hand-written Debug looks reviewed | "any ... result value" |
| B3_history_payloads | B-ROUTE | M4 | src/types/history.rs:33-54 object/class history data and schema | real unredacted result type | history rows are requested data | "every shape of result" |
| S1_restore_run | INJ | M2 | async + blocking RestoreRunOp::send formats the server restore error into ApiError::Api | planted runner duplicate (manifest "B (injected)") | new backup/restore code; not a task summary | "any error"; both interfaces |
| S3_sink_health | INJ | M4 | src/types/event.rs EventSinkDeliveryHealth.last_error derived Debug | planted nested result field | a health view is diagnostics by definition | "nested values ... optional and required fields" |

**Outcome:** gate SOUND. Raw DS 1.0 (1 run); MiMo 1.0 (1 run); 34 tests, 0 failing. Nothing missed.
**Read:** Every sibling is one concept: "redact server content in every Debug/Display". A grep for `derive(Debug)` and `format!` over error paths finds them all, so models fix them together, which the 1/1 solves confirm. The sensitive/non-sensitive split (keep ids, names and statuses) is a judgement call, but it did not hurt either model.

### jetty.project-ds
**Host / advisory:** jetty/jetty.project, GHSA-2FVJ-HGJ9-J2GR / CVE-2026-10050, CWE-173, Java · **Built by:** DeepSeek-built pilot (10-18/19), injected track (header says track None; notes and manifest describe injected siblings) · **Pattern label:** A+B · **Traps:** 5
**Base bug:** Core `DigestAuthenticator.Digest.check` builds H(A1) with `getBytes(ISO_8859_1)` (DigestAuthenticator.java:369-373), so a password differing only in a non-Latin-1 character (it maps to `?`) gives the same digest.
**Symptom as reported:** "distinct passwords are treated as the same, so a wrong password is enough to log in as the user". Invariant: no credential may establish identity "unless it corresponds exactly to that account's stored secret. This applies to every authentication scheme, every deployment environment, every supported digest algorithm, and every way a stored credential can be represented". Every trap is covered. "environment", "algorithm" and "representation" each name one sibling family.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| reported_digest | BASE | M8 | jetty-core/jetty-security DigestAuthenticator.java:369-373 ISO-8859-1 H(A1) | reported site | none | the example |
| servlet_second_implementation | A-FAR | M2 | jetty-ee9-security DigestAuthenticator.java:351-355 copy | second implementation in another module | legacy servlet module, out of scope | "every deployment environment" |
| stored_digest_credential_route | B-ROUTE | M2 | jetty-util Credential.java:215 MD5.check hashes the submitted password with ISO-8859-1 (via Basic) | the same lossy hash in the credential class | legacy format; a fix might break stored hashes | "every way a stored credential can be represented"; "every scheme" |
| stronger_digest_algorithm_injected | INJ | M2 | DigestAuthenticator.java:330-334 added SHA-256 branch + setAlgorithm with ISO-8859-1 A1 | planted duplicate hash branch | a non-default algorithm | "every supported digest algorithm" |
| stored_strong_digest_injected | INJ | M2 | Credential.java:327 added SHA256: credential type with ISO-8859-1 | planted duplicate stored format | a newer format, looks unrelated | "every way a stored credential can be represented" |

**Outcome:** gate SOUND. Raw DS 1.0 (1 run); MiMo 1.0 (1 run); 17 tests, 0 failing. Nothing missed.
**Read:** Every sibling is the same one-token concept (`ISO_8859_1` -> `UTF_8`). A grep for the charset finds every site, and the instruction names each family, so models fix them together. Fair, but with no bite.

### keras-ds
**Host / advisory:** keras-team/keras, GHSA-26C4-7VV6-867J / CVE-2026-12480, CWE-73, Python · **Built by:** DeepSeek-built pilot (10-18/19), injected track · **Pattern label:** A+B · **Traps:** 8
**Base bug:** HDF5 artifact entries can point outside the artifact through a virtual dataset, ExternalLink or SoftLink. `H5IOStore.__getitem__` (saving_lib.py:1162) rejects only external-storage values, so loaders fill weights with bytes from other host files.
**Symptom as reported:** "A crafted artifact using such an entry makes the loader open that other file and fill model weights ... with its contents". Invariants: no artifact content may make "any API that loads or inspects it" read outside the artifact's files, "for every artifact form named above, for every position an entry can occupy, and for every way the format lets an artifact express indirection, including a link ... and a value whose bytes are kept in an external file"; "at every loading and inspection entry point ... for a link or indirection at any level ... not only at the deepest one". Every trap is covered. "Any level" points at T6; "sharded set" and "inspection utility" point at T3/S1/S2 and T5.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | saving_lib.py:1162 H5IOStore.__getitem__: virtual dataset at a value (weights.h5, Model.load_weights, unzipped .keras) | reported site; only external storage checked | a one-line is_virtual check looks complete | "a value whose bytes are kept in an external file" |
| T2 | SHAPE TRAP | M8 | saving_lib.py:1103 H5IOStore.get: ExternalLink at a group, SoftLink at a value / in a zipped .keras / in the older-layout fallback | link variant in the base store | links resolve like ordinary entries | "a link to another location" |
| T3 | A-FAR | M2 | saving_lib.py:1390 ShardedH5IOStore._get_h5_group (later shard) | second store implementation | a subclass only for .weights.json | "a sharded weights set" |
| T4 | A-FAR | M2 | legacy/saving/legacy_h5_format.py:361,374,504,582 loaders | separate loader with no validation | keras/src/legacy reads as out of scope | "the older single-file model format" |
| T5 | B-ROUTE | M2 | saving/file_editor.py:455 _extract_weights_from_store (only an external-storage check) | the inspector's own extractor | an inspector, not a loader; already has a check | "the inspection/editing utility" |
| T6 | B-ROUTE | M1 | saving/saving_api.py:302 raw `f["model_weights"]` top-level fetch | call site before the validating loader | a dispatch step; the loader below validates | "at any level ... not only at the deepest one" |
| S1 | INJ | M2 | saving_lib.py:1428-1445 ShardedH5IOStore.__getitem__ cross-shard in-place read | inline copy of the base conversion that skips the verified reader | the base reader is fixed, so reads look covered | "sharded weights set"; "every position" |
| S2 | INJ | M9 | saving_lib.py:1289-1323 ShardedH5IOStore.get fallback when the weight map has no entry | fallback lookup when the index data is missing | the weight map is bookkeeping | "sharded set"; "at any level" |

**Outcome:** gate UNSOUND, although notes.md reports static (expected gaps only), nop, oracle and patches all passing after Docker-race retries; the bundle does not give the UNSOUND reason. No trials; no per-test data.
**Read:** Most siblings are routes of one concept (check every HDF5 lookup for links and virtual or external data). A shared `safe_get` helper used everywhere covers T1-T6. S1 (an inline duplicate reader) and S2 (a fail-open fallback) are the parts most likely to bite, because they bypass a helper the model has already hardened. Realism of S1/S2 depends on how plausible those small saving_lib edits are; the instruction names every form and level, so fairness looks sound.

### knowns-ds
**Host / advisory:** knowns-dev/knowns, GHSA-9GFJ-28HW-JCHP / CVE-2026-86439, CWE-22, Go · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18) · **Pattern label:** A (track injected) · **Traps:** 8
**Base bug:** Document paths, memory ids and template names are joined onto `.knowns/{docs,memory,templates}` with `filepath.Join` and nothing checks that the result stays inside. The report leads to the document read (`doc_store.go:124` Get) through MCP `docs get` / HTTP `GET /docs/*`.
**Symptom as reported:** "A local web API request for the document named `../notes` returns the contents of `notes.md` from outside the project's document library", plus "write, rename or delete … read or remove memory notes … reach files outside the template library". Invariants: "No value that names a document, a memory note, a template, a template file, or a generated destination may cause the product to read or write a file outside the folder … whatever the operation is called"; "An identifier read back from stored data … is as untrusted as one supplied by a client"; spelling and symlink forms must be "refused, not silently reinterpreted". Every trap has a covering invariant. The instruction names "a generated destination" (S2) and stored identifiers (T5) outright.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M2 | none planted: the template store's own name-to-file mapping (create, import-qualified get) and the preview `templateFile` read, in `template_store.go` and `routes/templates.go` | same join without containment, in a separate store and package | "the report is about documents and memory notes; templates are a separate feature" | "a template, a template file"; "reach files outside the template library" |
| T2 | A-FAR | M1 | none planted: doc create/update/rename/delete, each with its own join, in `doc_store.go` | other verbs on the landing store | "observed impact is a read; writes look covered by the read guard" | "write, rename or delete files outside the library" |
| T3 | BASE | M8 | none planted: the landing read plus imported-doc lookup, symlink target, encoded wildcard, absolute/volume/UNC/device spellings, in `doc_store.go:124/146/158` | landing site; a plain `..` check misses these spellings | "a `..` string check fixes the example" | "however the value is spelled … a symbolic link inside a managed folder" |
| T4 | A-FAR | M2 | none planted: client memory ids on get/delete/review-create, plus trailing-dot, backslash and colon spellings, in `memory_store.go` | the memory store's own id-to-file mapping | "memory ids are generated tokens, so they look trusted" | "read or remove memory notes outside the memory folders" |
| T5 | A-FAR | M5 | none planted: promote/demote re-uses the id read from the record's own frontmatter (`memory_store.go` moveLayer) | the same sink, reached through a stored value | "the id came from our own file and was already used to fetch the record" | "An identifier read back from stored data … is as untrusted" |
| S1 | INJ | M1 | memory snapshot recovery view (`ReadSnapshot`/`writeSnapshot` in `memory_store.go` + `snapshot` action in `handlers/memory.go`) maps the id under `.snapshots` | new action reaching the sink without the id check | "read-only recovery view of our own backup" | "every operation that resolves such a value, whatever the operation is called" |
| S2 | INJ | M5 | template preview returns the destination's current contents; destination = template actions + request variables, joined to the project root (`routes/templates.go`) | a config-derived value reaches a file read | "destination looks like template-author config; the guard above covers templateFile" | "a generated destination" |
| S3 | INJ | M2 | raw document source view (`GET /docs/*/source`, `routes/docs.go`) rejoins the path to the docs root instead of going through the store | an inline copy of the mapping that bypasses the fixed store | "an export view assumed to use the same document store" | "every operation … whatever it returns" |

**Outcome:** gate UNSOUND (the bundle's marker; the notes record nop/oracle/patches eventually green, so the reason is unclear). No DS or MiMo trials. Missed siblings: unknown.
**Read:** Five of the eight levers are published-fix sites of one concept: confine every name-to-file mapping. S1 and S3 are more routes of that same concept. S2 (config-derived destination) and T5 (stored id) are the only ones with a different trust source, and the instruction names both outright, so they are unlikely to bite. Fairness: the Windows spellings do not escape on Linux and are tested only as "must refuse". The doc-delete patch does not isolate its own lever.

### knowns-mm
**Host / advisory:** knowns-dev/knowns, GHSA-9GFJ-28HW-JCHP / CVE-2026-86439, CWE-22, Go · **Built by:** MiMo-built pilot (build-v1 template, injected track, 10-18) · **Pattern label:** A (track injected) · **Traps:** 6
**Base bug:** The same flaw as knowns-ds: the storage layer joins caller names onto the record-kind subdirectory with no containment. The report leads to document create with a parent-segment folder (`doc_store.go`).
**Symptom as reported:** "A document whose folder contains parent-segment spelling (for example `../../outside`) is accepted and written outside the documentation directory … the same class of name can also cause files … to be read, overwritten or removed." Invariant: "No name used to locate a record's file may cause the system to create, read, write, move or delete any file … outside that record kind's own subdirectory … for every operation that turns a name into a file location." There is no explicit stored-identifier clause, but T3 is covered by "however the name arrives". All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | none planted: doc create/get/delete with `../`, and an in-docs symlink pointing outside (`doc_store.go`) | landing site; a lexical fix misses the symlink and the other verbs | none (the reported site) | "read, overwritten or removed"; "every operation" |
| T2 | A-FAR | M2 | none planted: memory id to `memory-<id>.md` on get/delete (`memory_store.go`) | the second record kind's own mapping | "another tool and directory; the prefix absorbs one `..`" | "for every operation that turns a name into a file location" |
| T3 | A-FAR | M5 | none planted: the move between layers rebuilds the filename from the id in the stored frontmatter (`memory_store.go` move path) | a stored value reaches the same sink | "the id came from our own file and was accepted when read" | "however the name arrives" |
| T4 | A-FAR | M2 | none planted: template create/get (including import-qualified names) and the preview `templateFile` (`template_store.go`, `routes/templates.go`) | a neighbouring store's own mapping | "templates are a feature the report does not name; the preview is the web UI" | "templates … a file inside a template" in the system description |
| S1 | INJ | M1 | new doc-archive action copies a document into the archive area keyed by its path (`doc_archive.go`) | new operation reaching the file sink | "a derived copy, not the live document" | "every operation that turns a name into a file location" |
| S2 | INJ | M1 | new memory history/checkpoint side record keyed by id in the versions area (`memory_history.go`) | new operation reaching the file sink | "a system side record in a different area" | same |

**Outcome:** no gate marker in the bundle (the notes report nop PASS, oracle PASS and patches PASS on the 4th attempt). No DS or MiMo trials. Missed siblings: unknown.
**Read:** This is one concept with more routes. Both injected siblings are new operations keyed by the same identifier, so a confinement helper at the mapping layer covers them. A coupled in-project-symlink test guards against an over-broad "reject all symlinks" fix. Compared with knowns-ds: both builders kept the same five published-fix levers. mm dropped the non-Linux spellings, while ds tested them as must-refuse values. ds's injected set (snapshot view, config-derived preview destination, store-bypassing raw view) has more variety than mm's two keyed side records (archive copy, history record).

### langchain-path-escape-inj
**Host / advisory:** langchain-ai/langchain, GHSA-GR75-JV2W-4656 / CVE-2026-55443, CWE-22/CWE-59, Python · **Built by:** Opus, build-v1 template, injected track (10-18) · **Pattern label:** A+B (track injected; pattern B: none built) · **Traps:** 6
**Base bug:** `glob_search` in the file-search middleware expands an agent-chosen pattern and follows per-match symlinks with no workspace containment (`file_search.py:162`).
**Symptom as reported:** "A single tool call the model emits — a search pattern, or a path handed to a file operation — comes back having reached a file the application never meant to expose: content from elsewhere on the host, or an entry that belongs to a neighbouring directory outside the one the tool was limited to." Invariants: no operation may "read, list, enumerate, copy or write a file outside the workspace … however the input is spelled — … a name that merely shares leading characters with an allowed directory, or a symbolic link …", and "a sibling whose name merely begins with the same characters is outside the restriction." All traps are covered. The report explicitly mentions the memory tool and the prefix sibling.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | none planted: upward glob pattern and in-workspace symlink match (`file_search.py:162`) | landing site; a base-path-only fix misses the pattern and symlink shapes | none | "a relative pattern … that walks upward … a symbolic link" |
| T2 | A-FAR | M2 | none planted: the Python grep fallback reads through a symlink (`file_search.py:329`) | second implementation in the same file | "a fallback that runs only without ripgrep" | "for every one of these operations" |
| T3 | A-FAR | M8 | none planted: raw `startswith` allowed-prefix check in the filesystem file tool (`anthropic_tools.py:881`) | the same boundary in another package, string prefix vs path segment | "partner package; path already root-resolved, so the prefix looks cosmetic" | "a sibling whose name merely begins with the same characters" |
| T4 | A-FAR | M8 | none planted: the same raw prefix check in the state-backed file tool (`anthropic_tools.py:126`) | state-backed variant of T3 | "in-memory store cannot reach disk" | same; "neighbouring directory" in the report |
| S1 | INJ | M8 | new `copy` command reads its source by join without a resolved-path containment check (`anthropic_tools.py:1092`) | new command; symlinked source leaks into an in-bounds destination | "destination is validated; source read looks like plumbing" | "copy" listed in the invariant verbs |
| S2 | INJ | M8 | new state glob/list command filters with raw `startswith` (`anthropic_tools.py:575`) | new command with the T3/T4 prefix flaw | "listing convenience over own state, not a boundary" | "list, enumerate"; prefix-sibling clause |

**Outcome:** gate_report passed=False; fairness NOT READY. DS 1.0 (1 run), MiMo 1.0 (1 run), 73 tests, 0 failing. No siblings missed.
**Read:** Every lever is one concept: resolve the path and compare it by whole segments. The injected commands just add routes that reuse the T3/T4 flaw. The invariant spells out both shapes (prefix sibling, symlink), so models fix them together, as the 1.0s show.

### langchain-ds
**Host / advisory:** langchain-ai/langchain, GHSA-GR75-JV2W-4656 / CVE-2026-55443, CWE-22/CWE-59, Python · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18/19) · **Pattern label:** A (track injected) · **Traps:** 8
**Base bug:** The same as langchain-path-escape-inj: `glob_search` (`file_search.py:162`) expands agent patterns with no per-match containment.
**Symptom as reported:** "a single search request the model emitted came back naming a file that lives outside the configured workspace; the agent then read that file and repeated its contents". Invariants: nothing outside the workspace or allowed directories may be "read, enumerate[d], take content from, cop[ied], mov[ed], create[d], modif[ied]"; "a permitted location is one of those directories itself, or a location beneath it by whole path segments". Unlike the -inj report, the symptom shows only the search case and does not name the symlink or prefix shapes, but the "whole path segments" invariant covers the prefix traps and "every operation the component offers" covers the injected commands. Symlinks appear only in the keep-working list ("a link inside the workspace that resolves to a target also inside it").

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| A1 | BASE | M8 | none planted: upward pattern (leading and mid-pattern), symlinked file match, symlinked-dir component (`file_search.py:162`) | landing site | "a base-path or leading-`..` fix looks complete" | the observed search case |
| A2 | A-FAR | M2 | none planted: Python grep backend reads through a symlink, with and without an include filter (`file_search.py:329`) | second implementation in the same file | "fallback only when ripgrep is missing" | "on either search implementation" (keep-working) and "every operation" |
| A3 | A-FAR | M8 | none planted: raw-prefix allowed-dir check, read and write, filesystem file tool (`anthropic_tools.py:885`) | segment-boundary flaw in another package | "path is root-resolved; prefix looks cosmetic" | "beneath it by whole path segments" |
| A4 | A-FAR | M8 | none planted: the same raw-prefix check in the state file tool, read and write (`anthropic_tools.py:126`) | state variant | "in-memory store cannot reach disk" | same |
| S1 | INJ | M8 | `copy` resolves the source and reads it without a containment check (`anthropic_tools.py:1096`) | new command; symlinked source | "destination is validated" | "copy … take content from" |
| S2 | INJ | M8 | `list` checks containment on the unresolved join, then enumerates (`anthropic_tools.py:1131`) | new command; symlinked dir | "listing only reads names; the path is textually inside" | "enumerate" |
| S3 | INJ | M8 | `append` validates only the parent dir, then opens the joined path (`anthropic_tools.py:1168`) | new command; write through a symlink | "parent dir is validated" | "modify … no out-of-bounds file may be … changed" |
| S4 | INJ | M8 | state `glob` listing filters entries with a raw prefix (`anthropic_tools.py:575`) | new command; prefix sibling | "listing convenience over own state" | "whole path segments" |

**Outcome:** gate SOUND. DS 1.0 (1 run), MiMo 1.0 (1 run), 88 tests, 0 failing. No siblings missed.
**Read:** This is still one concept (resolve, then compare by segment) with more routes. The four injected commands are three symlink shapes and one prefix shape of A3/A4, and models fix them together. Compared with langchain-path-escape-inj: the same four published-fix sites, plus two more injected commands (`list` via an unresolved join, `append` via a parent-only check) and more shapes (mid-pattern `..`, symlinked-dir component, include filter, read+write prefix). The earlier report names the symlink and prefix shapes in the invariant, while this one names only the whole-segment rule. That is a little harder in principle, but it made no difference (both 1.0).

### limesurvey-ds
**Host / advisory:** limesurvey/limesurvey, GHSA-5C37-5J7W-8MH8 / CVE-2026-50635, CWE-640 (Host-header poisoning), PHP · **Built by:** DeepSeek-built pilot (build-v1 template; notes say track injected, bundle says track None) · **Pattern label:** A (+ one pattern-B row, T3b) · **Traps:** 7
**Base bug:** `sendForgotPasswordEmailLink` (`PasswordManagement.php:168`) builds the reset link with `createAbsoluteUrl`, which takes the host from the request `Host` header even when a public URL is configured.
**Symptom as reported:** "A password-reminder request that carried a forged HTTP Host header produced an email whose link pointed at the attacker's domain instead of the public URL." Invariants: "Every link the application writes into an outgoing email, including links to images, must use the host of the configured public URL"; "This holds for every email the application sends … anonymous forms, authenticated staff actions and survey-participant flows alike." All traps are covered, and the invariant enumerates the trap classes (images → T3b, staff → T2/T3, participant → T4/T5).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_reported_reminder | BASE | M12 | none planted: forgot-password link, plain / mixed-case+port / bracketed IPv6 Host (`PasswordManagement.php:168`) | landing site | none | the example request |
| T2_staff_new_account | A-FAR | M1 | none planted: new-account email from an authenticated admin (`PasswordManagement.php:44`) | another entry to the same URL builder | "behind admin login, not the anonymous form" | "authenticated staff actions" |
| T3_bulk_reset_template | A-FAR | M1 | none planted: bulk reset renders another template (`PasswordManagement.php:260-261`) | another action and template, same host source | "bulk action, different template" | "every email the application sends" |
| T3b_logo_asset | B-ROUTE | M1 | none planted: logo image URL in the same template, left by the published fix (`PasswordManagement.php:279`) | another link in the same mail, never fixed upstream | "only a cosmetic image" | "including links to images" |
| T4_registration_confirmation | INJ | M1 | direct survey link added to the public registration confirmation (`RegisterController.php:324`) | new link built from the request host | "the shared mailer covers registration mail" | "survey-participant flows" |
| T5_withdrawal_message | INJ | M1 | new public action that emails a withdrawal link (`OptoutController.php:88-124`) | new link built from the request host | "opt-out is a privacy flow, not account security" | "a link that withdraws a participant" (system text); "survey-participant flows" |
| T6_host_spelling | SHAPE TRAP | M12 | none planted: case/port/IPv6 variants on the landing site (shares tests with T1) | input variants | "special-casing the reported spelling" | "any requester-supplied host must be treated the same way" |

**Outcome:** gate SOUND. DS 1.0 (1 run), MiMo 1.0 (1 run), 22 tests, 0 failing. No siblings missed.
**Read:** Every trap is a further route to one accepted concept (do not derive email-link hosts from the request), and the invariant enumerates the classes, including images and participant flows. Models fix this at the URL-helper layer, which covers all of them. T1 and T6 share security tests, so they are not independent levers.

### litellm-ds
**Host / advisory:** berriai/litellm, GHSA-3CV6-JPF6-8222 / CVE-2026-84377, SSRF / credential forwarding (CWE-918-like), Python · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18/19) · **Pattern label:** A+B (track injected) · **Traps:** 7
**Base bug:** In the deployment-scoped routes, the path `{model}` overrides the body model after the request-body URL-destination guard has already run, so a URL-valued model routes the request (and the configured credential) to a caller-chosen host (`common_request_processing.py:891`).
**Symptom as reported:** "A client holding an ordinary proxy key can make the gateway send a provider request to a host of the client's choosing, carrying the deployment's configured credential, by placing a URL where the model identifier belongs in a deployment-scoped route." Invariants: no model/file identifier may become an outbound destination "however the request delivers it: request body, query parameter, URL path, or form field"; destination params "inside nested settings, or as a bracket-notation form field"; "Credentials configured for a deployment must never be sent to a destination the request chose"; "Every route that accepts a model identifier … including management routes that test a deployment's connectivity." The "Names the tests use" contract names `extra_body` and `litellm_credential_name`. All traps are covered. Fairness tension: the contract keeps "the explicit admin opt-in that lets callers supply their own connection parameters", and a T4 coupled test expects that opt-in to restore credential inheritance for a caller endpoint. That contradicts the "never" invariant above.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_path_model_shared_processor | BASE | M7 | none planted: path model assigned after the guard; chat/completions, embeddings, `/engines` (`common_request_processing.py:891`) | landing site | "the guard already ran; the path is just the deployment name" | the example request |
| T2_image_second_implementation | A-FAR | M2 | none planted: image generation's own model-selection block (`image_endpoints/endpoints.py:99`) | second implementation of the path override | "fixing the shared processor covers the proxy" | "Every route that accepts a model identifier" |
| T3_bracket_form_metadata | A-FAR | M6+M8 | none planted: multipart `litellm_metadata[langfuse_host]`, `metadata[api_base]` flattened before the auth check (`auth_utils.py:439`, `files_endpoints.py:376`) | form producer the check never sees nested | "dict/JSON shapes are already checked" | "as a bracket-notation form field" |
| T4_health_connection_credentials | A-FAR | M5 | none planted: `/health/test_connection` merges config credentials and the credential-name reference under a caller `api_base` (`_health_endpoints.py:1830`) | configured defaults merged under a caller destination | "admin utility documented to load config and allow overrides" | "management routes that test … connectivity"; "must not accompany it" |
| T5_queue_route | B-ROUTE | M1 | none planted: `/queue/chat/completions` never calls the guard (`proxy_server.py:13096`) | uncovered route, still in upstream main | "experimental, hidden from schema" | "query parameter"; "Every route" |
| T6_extra_body_bracket_form | INJ | M6+M8 | files handler extended to rebuild `extra_body[...]` bracket fields; the check handles only metadata prefixes (`files_endpoints.py:390`, `auth_utils.py:436`) | new nested container the check never inspects | "fixing the reported metadata prefix is enough" | "inside nested settings"; `extra_body` named |
| T7_moderation_path_model | INJ | M2 | Azure-style path model copied into the moderations handler after the guard (`proxy_server.py:8966,9010`) | copy-paste of the T1/T2 override | "moderations is a different endpoint" | "Every route that accepts a model identifier" |

**Outcome:** gate SOUND. Raw rewards: DS 0.0, 0.0, 0.0. MiMo 0.0, 0.0, then r3 NA (no result). DS r1–r3 each failed only `functional.test_legit_health::test_operator_opt_in_restores_inheritance_for_a_caller_endpoint` (a T4 coupled test), so DS fixed every sibling. MiMo r1 missed T2 (image), T7 (moderations) and T5 (queue), plus the same functional test. MiMo r2 failed only that functional test.
**Read:** The siblings are mostly more routes of one concept (check the model/destination after the final value is chosen, on every route). DS closed them all 3/3. The 0.0s come from one coupled opt-in test whose expected behaviour conflicts with the stated "never" invariant. That makes the failure a likely fairness defect or false breaker, not sibling difficulty, so it needs a fairfix before it counts. MiMo's single real sibling miss (T2/T5/T7) happened once in three runs.

### mcp-atlassian-path-inj
**Host / advisory:** sooperset/mcp-atlassian, GHSA-2XJ6-XX86-CWWC / CVE-2026-77255, CWE-22 + CWE-441, Python · **Built by:** Opus, build-v1 template, injected track (10-18) · **Pattern label:** A+B (track injected; no B route found) · **Traps:** 6
**Base bug:** Jira attachment upload (`jira/attachments.py:381`) reads a caller-supplied local path with no workspace confinement and sends the bytes to Atlassian.
**Symptom as reported:** "passes a path that points *outside* the workspace … The server reads that file and transmits its contents to the remote Atlassian site." Invariant: no path "whether the path names a file to be uploaded as an attachment, or a file whose contents are read to become the body of a created or edited item … however the path is spelled … one entry among several … for every tool that accepts such a path". The system text names wiki page, tracker issue and comment bodies, which point at T3/S2/S3. All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8+M12 | none planted: absolute, `../`, symlink, list entry, update_issue attachments (`jira/attachments.py:381`) | landing site | none | "absolute … walks upward … symbolic link … one entry among several" |
| T2 | A-FAR | M2 | none planted: Confluence attachment upload (`confluence/attachments.py:151`) | second implementation in another product package | "different product from the Jira report" | "every tool that accepts such a path" |
| T3 | A-FAR | M4 | none planted: page body from `content_file` (`servers/confluence.py:149`) | other feature, same read-and-send sink | "documented as accepting an absolute or relative path, so it looks intended" | "a file whose contents are read to become the body" |
| S1 | INJ | M2 | create_issue `attachments` via an inline `add_attachment` loop, exists-check only (`jira/issues.py:773`) | bypasses the shared upload helper | "fixed the shared helper; create goes through it" | "attach a file"; "every tool" |
| S2 | INJ | M2 | create_issue `description_file` reader (`servers/jira.py:170`) | cross-package twin of the T3 helper | "fixing the Confluence helper is enough" | "a tracker issue … body … as a path" |
| S3 | INJ | M2 | add_comment `body_file` inline read (`servers/confluence.py:1270`) | inline copy of the T3 read | "the shared page helper covers it" | "a comment … body … as a path" |

**Outcome:** no gate marker in the bundle. DS 1.0, 1.0, 0.0; MiMo 0.0, 1.0, 1.0. Every 0.0 failed only the project test `tests.unit.servers.test_confluence_server::test_upload_attachment[asyncio]`, which is not a trap test. No security test failed in any run, so no siblings were missed. Why that project test fails is unclear: it may encode pre-fix behaviour that was not deselected, or it may catch an over-tight fix.
**Read:** Two concepts (attachment upload, body-from-file), each with duplicated implementations. The system text names both and every body type, so a model that confines at a shared helper and greps for the readers finds them all. The intermittent 0.0s come from one project test, so check that test's fairness before reading any failure as difficulty.

### mcp-atlassian-ds
**Host / advisory:** sooperset/mcp-atlassian, GHSA-2XJ6-XX86-CWWC / CVE-2026-77255, CWE-22 + CWE-441, Python · **Built by:** DeepSeek-built pilot slug, but the notes say it re-used the MiMo build's (mcp-atlassian-mm) design and artifacts verbatim, renamed, and re-ran the gate · **Pattern label:** A (track injected) · **Traps:** 6
**Base bug:** The same as mcp-atlassian-path-inj: Jira attachment upload (`jira/attachments.py:353-415`, reached via update_issue) reads an unconfined caller path.
**Symptom as reported:** Same text as -path-inj, with the invariant widened to "a path the platform expands on the caller's behalf before it is used; wherever in the request the path appears", plus a keep-working line for the existing download-side protection. All traps are covered, and the smuggled-in-JSON and `~` shapes are covered by those new clauses.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | none planted: absolute, `../`, symlink, list, update_issue, JSON-array string, comma string, list smuggled in `fields`/`additional_fields` JSON (`jira/attachments.py:353-415`) | landing site plus delivery variants | "validating the named argument is enough" | "wherever in the request the path appears" |
| T2 | A-FAR | M2 | none planted: Confluence upload, absolute/`../`/symlink/list (`confluence/attachments.py:124-197`) | second implementation | "different product package" | "every tool" |
| T3 | A-FAR | M4 | none planted: `content_file` page body, absolute/`../`/`~` (`servers/confluence.py:117-153`) | other feature, same sink | "documented path parameter, looks intended" | "body … read from a file"; "a path the platform expands" |
| S1 | INJ | M2 | create_issue attachments inline loop (`jira/issues.py:647,777-791`) | bypasses the shared helper | "create routes through the fixed helper" | "attach a file" |
| S2 | INJ | M2 | `_resolve_issue_description` (`servers/jira.py:172-209`) | cross-package twin of T3 | "fixing the Confluence helper is enough" | "a tracker issue" body |
| S3 | INJ | M2 | add_comment `body_file` inline read (`servers/confluence.py:1237-1283`) | inline copy | "the shared helper covers it" | "a comment" body |

**Outcome:** gate SOUND. DS 1.0 (1 run). MiMo 0.0, 0.0, 1.0: both 0.0s failed only the project test `test_confluence_server::test_upload_attachment[asyncio]`, with no security failures. No siblings missed.
**Read:** The same one-concept-many-routes design as -path-inj, and models fix it at the read sites. Compared with mcp-atlassian-path-inj: the same six levers. This variant adds the delivery-shape variants (JSON-string and comma lists, list smuggled inside the fields JSON) and `~` expansion, plus matching invariant clauses. These are M12 shapes, which do not raise difficulty. The only 0.0s again come from the same non-trap project test, which needs a fairness check.

### mcp-atlassian-mm
**Host / advisory:** sooperset/mcp-atlassian, GHSA-2XJ6-XX86-CWWC / CVE-2026-77255, CWE-22 + CWE-441, Python · **Built by:** MiMo-built pilot (build-v1 template, injected track, 10-18) · **Pattern label:** A (track injected) · **Traps:** 6
**Base bug:** The same as mcp-atlassian-ds: unconfined Jira attachment upload path (`jira/attachments.py:353-415`).
**Symptom as reported:** Text identical to mcp-atlassian-ds, including "a path the platform expands on the caller's behalf" and "wherever in the request the path appears". All traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | none planted: absolute, `../`, symlink, list, update_issue, JSON/comma strings, smuggled `fields`/`additional_fields` (`jira/attachments.py:353-415`) | landing site | none | "wherever in the request the path appears" |
| T2 | A-FAR | M2 | none planted: Confluence upload (`confluence/attachments.py:124-197`) | second implementation | "different product package" | "every tool" |
| T3 | A-FAR | M4 | none planted: `content_file` page body incl. `~` (`servers/confluence.py:117-153`) | other feature, same sink | "documented path parameter" | "a path the platform expands" |
| S1 | INJ | M2 | create_issue attachments inline loop (`jira/issues.py:647,777-791`) | bypasses the shared helper | "create routes through the helper" | "attach a file" |
| S2 | INJ | M2 | `_resolve_issue_description` (`servers/jira.py:172-209`) | cross-package twin | "Confluence fix is enough" | tracker-issue body |
| S3 | INJ | M2 | add_comment `body_file` inline read (`servers/confluence.py:1237-1283`) | inline copy | "shared helper covers it" | comment body |

**Outcome:** gate UNSOUND (the bundle's marker; the notes record patches PASS on the 4th attempt after network-prune flakes, so the reason is unclear). No DS or MiMo trials. Missed siblings: unknown.
**Read:** One concept with duplicated readers. Expect the same result as mcp-atlassian-ds (models fix all six). Compared with the other variants: this is the source design that mcp-atlassian-ds copied byte for byte, and it differs from -path-inj only in the extra delivery shapes and `~` expansion. The only difference from -ds is the gate status (UNSOUND here, SOUND there).

### mockoon-ds
**Host / advisory:** mockoon/mockoon, GHSA-RQX4-3F6Q-3X2V / CVE-2026-59148, CWE-306 / CWE-942 / CWE-532, TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18/19) · **Pattern label:** A (track injected) · **Traps:** 7
**Base bug:** The management API (`/mockoon-admin*`, middleware `admin-api.ts:63-74`) has no authentication and grants CORS to every origin, so any caller or web page can read recorded transactions (with credential headers) and change runtime state.
**Symptom as reported:** "a page served from `https://evil.example` can issue a cross-origin request for the recorded requests and read the `Authorization` and `Cookie` headers … can write process environment variables". Invariants: a bearer token is required "for every management operation and whichever way the server is started", including "subscribe to live management updates"; "No management output — stored or live — and no transaction log the runtime writes may contain" the listed sensitive headers; env writes "stay inside the configured prefix"; the token is configured through `adminApiAuthToken`/`MOCKOON_ADMIN_API_TOKEN`, and live streams take `?token=`. All traps are covered. The invariant text names transaction logs (T2), live streams (T3/T6) and the env prefix (T4/T7).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M1 | none planted: middleware plus every route/verb, SSE, wrong/non-bearer/query token, no-token-configured fail-closed (`admin-api.ts:63-74`) | landing site; coverage of all routes and verbs | none | "every management operation" |
| T2 | A-FAR | M2 | none planted: the second redaction implementation in runtime transaction logging (`events-listeners.ts:15-25`) | separate redaction copy (masked authorization only) | "operator's own local log; auth is already masked" | "no transaction log the runtime writes" |
| T3 | A-FAR | M1 | none planted: SSE replay and live emitter carry raw headers (`admin-api.ts:41-61, 88-92`) | another output path for the same data | "redacting the logs endpoint looks sufficient" | "stored or live" |
| T4 | A-FAR | M4 | none planted: env-var write sets the bare key (`admin-api.ts:151-166`) | separate property; prefix never enforced on write | "report headline is auth/CORS; prefix is an operator setting" | "Environment-variable writes stay inside the configured prefix" |
| T5 | A-FAR | M11 | none planted: the serverless wrapper does not convey the token/origins (`serverless.ts:36-59`) | host wiring of the fix (its check patch is functional_fail) | "the library fix covers every host" | "whichever way the server is started" |
| T6 | INJ | M1 | management WebSocket log stream on the upgrade path, outside Express middleware, unauthenticated and unredacted (`server.ts`) | new transport that bypasses the auth middleware | "the router middleware covers every management path" | "subscribe to live management updates"; "live update streams" take `token` |
| T7 | INJ | M2 | bulk env-var import route with its own write loop (`admin-api.ts`) | duplicate of the T4 write | "fixing the single write handler is complete" | prefix invariant |

**Outcome:** gate SOUND. DS 1.0 (1 run). MiMo 0.9615, 1.0. MiMo r1 missed T6 (`an unauthenticated management stream delivers no recorded transactions`; the WS redaction test passed). No other misses.
**Read:** Three concepts (auth, redaction, env prefix), but the instruction states each one, so each is an accepted requirement. The only real bite is T6, a transport that bypasses Express middleware. That is a genuine M1 route away from where the fix sits, and it caught MiMo once. Every other sibling is a further route to a stated rule.

### n8n-ds
**Host / advisory:** n8n-io/n8n, GHSA-2X35-3FW4-9JR4 / CVE-2026-72766, CWE-73 / CWE-918-like (file read / URL fetch into email), TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18) · **Pattern label:** A+B (track injected) · **Traps:** 6
**Base bug:** Send Email v2 `send` copies workflow values into nodemailer options. An object value `{path}`/`{href}` makes the mail library read a host file or fetch a URL into the message (`EmailSend/v2/send.operation.ts:206-228`).
**Symptom as reported:** "can be made to send a message containing the contents of a file from the n8n host … pointed at a remote address, the product fetches that address". Invariants: no workflow value may cause a file read or URL fetch into an outgoing email "in any part of that email"; non-text values "must be delivered as text"; "These properties hold for every email-sending capability of the product … and for every way a message part or attachment can be supplied." All traps are covered. The invariant names attachments (T5) and "every email-sending capability" (T3 Gmail, T2 legacy).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_current_send | BASE | M8 | none planted: text/HTML `{path}`/`{href}` objects (`v2/send.operation.ts:206-228`) | landing site; object value interpreted as a reference | none | the observed impact |
| T2_legacy_send | A-FAR | M2 | none planted: v1 node with its own transport and mail options (`v1/EmailSendV1.node.ts:153-196`) | second implementation | "superseded node version, not the reported node" | "every email-sending capability" |
| T3_gmail_encoder | B-ROUTE | M2 | none planted: Gmail v1 send/draft through the MailComposer encoder (`Gmail/GenericFunctions.ts:209-250`) | uncovered route to the same library sink | "different node and transport; current version already coerces" | "every email-sending capability" |
| T4_input_shapes | SHAPE TRAP | M12 | none planted: array/number/boolean values must render as text, not fail (`send.operation.ts:224-228`, v1) | correctness contract on the fix | "cosmetic robustness detail" | "A value that is not text must be delivered as text" |
| T5_injected_attachment_path | INJ | M1 | "Attachments (Path)" send option forwarding `{path}`/`{href}` to the mail library (`v2/send.operation.ts:141-148, 253-269`) | new attachment route to the sink | "an attachment option, not a message field; attachments are binary" | "every way a message part or attachment can be supplied" |
| T6_injected_send_and_wait_text | INJ | M1 | "Plain Text Alternative" on send-and-wait, copied raw (`v2/sendAndWait.operation.ts:22-38, 60-73`) | new message-part route | "HTML is templated; the raw text looks benign" | "every way a message part … can be supplied" |

**Outcome:** gate SOUND (patches stage verified piecewise because of network flakes). DS 1.0, 1.0, 1.0. MiMo 0.875, 1.0, 1.0. MiMo r1 missed T5 (both attachment-path tests). No other misses.
**Read:** One concept (string-coerce, or disable file/URL access, at every mail build) with more routes. A transport-level `disableFileAccess`/`disableUrlAccess` fix covers most of them. T5 differs because a path attachment is the feature itself, so it bit MiMo once. Every route is stated in the invariant.

### new-api-ds
**Host / advisory:** quantumnous/new-api, GHSA-6X2C-PHFF-WX57 / CVE-2026-64859, CWE-200 / CWE-285, Go · **Built by:** DeepSeek-built pilot (build-v1 template, injected track, 10-18) · **Pattern label:** B (track injected) · **Traps:** 7
**Base bug:** The shared user model serializes `access_token` (`model/user.go:39`), so the admin listing (`controller/user.go:236`) returns root's management token to non-root admins. The passkey-reset admin action also lacks the role-hierarchy guard.
**Symptom as reported:** "An administrator who is not the root account can read the root account's management token from the account listing." Invariants: the management token and "the notification credentials an account stores in its profile belong to that account alone … in every response that describes accounts to an administrator"; "An administrator may change or revoke another account's sign-in credentials or sign-in protections only when the administrator outranks that account." All traps are covered. The system text lists webhook secret, push token and push URL (T3), and the rank invariant covers T4/T7.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_landing_token_listing | BASE | M3 | none planted: token via the model JSON tag in the admin listing (`model/user.go:39`, `controller/user.go:236`) | landing site; fix at the shared serializer | none | the example request |
| T2_far_token_routes | A-FAR | M1 | none planted: admin search and detail use the same serializer (`controller/user.go:251, 350`) | other handlers | "a handler-level fix covers the report" | "in every response that describes accounts" |
| T3_uncovered_notification_secrets | B-ROUTE | M4 | none planted: settings blob with webhook secret, push token, push URL in list/search/detail/export (`model/user.go:51`, `dto/user_settings.go`) | a second secret class, never protected; still in upstream main | "notification config, not a login credential" | "notification credentials … belong to that account alone" |
| T4_published_passkey_hierarchy | A-FAR | M1 | none planted: passkey reset with no rank check (`controller/passkey.go:341`) | a separate admin action that lacks the neighbour's guard | "report is a listing leak, not passkey management" | "change or revoke … sign-in protections only when the administrator outranks" |
| T5_injected_export | INJ | M2 | admin export with its own row type copying token and settings (`controller/user.go:281`) | duplicate serialization path | "separate admin-only feature" | "every response that describes accounts" |
| T6_injected_token_view | INJ | M1 | admin route returning a target's token (`controller/user.go:313`) | new route exposing the token | "intentional support tooling" | "may be returned to that account and to no one else" |
| T7_injected_force_logout | INJ | M1 | admin force-logout revokes a target's token, no rank check (`controller/user.go:334`) | new action that lacks the rank guard | "revoking looks harmless" | "change or revoke … credentials … only when … outranks" |

**Outcome:** gate SOUND. DS 1.0 (1 run), MiMo 1.0 (1 run), 78 tests, 0 failing. No siblings missed.
**Read:** Two stated concepts (credential disclosure, rank guard) with more routes to each. T3 is the most "different concept" lever (a non-login secret class), but the instruction names it explicitly, so it no longer bites. The injected routes are easy to find by grepping the admin handlers.

### nhost-cors-auth
**Host / advisory:** nhost/nhost, GHSA-64CJ-QVX5-M4F3 / CVE-2026-47671, CWE-306 / CWE-942, Go · **Built by:** Opus, build-v1 template, batch 1 (10-17; mined track, no injected siblings) · **Pattern label:** A (track None/mined) · **Traps:** 5
**Base bug:** The local configserver uses `cors.Default()` (allow-all) as its only origin control (`cli/cmd/configserver/configserver.go:170`), and the loader puts real secret values into the store that every GraphQL resolver reads.
**Symptom as reported:** "a page on `https://evil.example` can `fetch()` a GraphQL query for the project's secrets … read the admin secret, JWT key and every other stored secret". Invariants: browser access only from `<single-label>.dashboard.local.nhost.run` or `local.dashboard.nhost.run` ("No other origin may, however closely it resembles one of these … local development servers"); "No response from the service may contain a secret value it read from the project's secrets file … for the dashboard and every other client." Must-keep: secret edits leave other secrets intact, and resolved config still works. All traps are covered. The secret rule is scoped to values read from the file (fairness revision of 10-17).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M6 | none planted: secret values must be withheld at the `GetApps` loader that feeds all resolvers, including resolved config (`local.go:94-105`) | producer off the CORS check's path | "the report is cross-origin; fixing CORS (or the listing resolver) looks complete" | "Secret values never leave the service … every other client" |
| T2 | COUPLED TRAP | M11 | none planted: once values are redacted, `UpdateSecrets` must merge placeholders with stored values (`local.go:164-180`); functional tests only | save path coupled to T1 | "plain persistence code unrelated to CORS" | "Adding, changing or deleting one secret … leaves the other secrets as they are" |
| T3 | SHAPE TRAP | M8 | none planted: lookalike ending, other `*.local.nhost.run`, multi-label, localhost, `null`, bare dashboard domain; preflight and response (`configserver.go:170`) | origin-matching variants | "copy the looser logs-websocket checker" | "single DNS label … however closely it resembles … local development servers" |
| T4 | A-FAR | M1 | none planted: logs GraphQL on the same gin engine (`configserver.go:174`) | second API under the same middleware | "the example names the configuration API" | "`/v1/logs/graphql`" and "look at service logs" |
| T5 | COUPLED TRAP | M11 | none planted: dashboard origins keep credentialed CORS; the shared `oapi` CORS helper keeps its defaults for auth/storage (`configserver.go:170`, `internal/lib/oapi/middleware/cors.go`) | over-hardening guard | n/a (must keep working) | "The dashboard on its origins works exactly as today" |

**Outcome:** gate_report passed=False; fairness NOT READY. DS 1.0 (1 run), MiMo 1.0 (1 run), 49 tests, 0 failing. No siblings missed.
**Read:** T1+T2 (redact at the loader and merge on save) is the only genuinely different concept from "fix CORS", and the instruction states it as its own required behaviour, so models do it. T3 is origin-regex shapes that models always get. There are no injected siblings. The uncovered logs-websocket origin checker was left out, and its project test was excluded.

### olivetin-allowlist-inj
**Host / advisory:** OliveTin/OliveTin, GHSA-PRJ9-97MP-MWH2 / CVE-2026-53541, CWE-20 (command injection / allowlist bypass), Go · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B (manifest; the two published sites are A, the two others are injected) · **Traps:** 4
**Base bug:** The caller's login name, which comes from the identity layer, is put into the shell command the action runs without a type check, so shell metacharacters in the name execute. The report leads to `injectSystemArgs`/`parseActionArguments` in the executor.
**Symptom as reported:** "the caller's identity ... carries shell metacharacters in a field the action includes in its command (for example the caller's login name)". Invariants: "No value that describes *who the caller is* — their login name, their group membership, or any other attribute ..."; "No request-supplied input that the action has not declared may reach the command or its environment ... whatever name they give it"; "whether that command is run through a shell or launched directly, and for a command's environment as much as for the command text itself". Every trap is covered. The wording names group membership and the direct-exec environment, so it almost points straight at both injected siblings.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| username_into_command | BASE | M12 | Upstream: login name templated into the shell command (executor.go injectSystemArgs, arguments.go) | The reported site | none (the lead) | "for example the caller's login name" |
| client_reserved_arg_into_env | A-FAR | M7 | Upstream: an undeclared client argument with the reserved system prefix survives the filter; system args are injected before filtering (executor.go keepArgument + ordering) | Same published fix, a second gap (allowlist bypass into the environment) | A fix that validates the name keeps the prefix pass-through and the inject-before-filter order | "No request-supplied input that the action has not declared ... whatever name they give it" |
| group_into_shell | INJ | M1 | The caller's group line is exposed to the shell command template (arguments.go parseActionArguments) | A neighbouring identity field reaching the same shell sink | It is not the login name the report flags | "their group membership, or any other attribute" |
| group_into_exec_env | INJ | M2 | The same group value is written into the environment of a direct-exec action (executor.go handleExecBranch) | A second execution branch, maintained separately, sink = environment | Direct exec uses argv, so it looks injection-proof | "run through a shell or launched directly ... environment as much as ... command text" |

**Outcome:** no gate marker; no DS or MiMo trials.
**Read:** The injected siblings are "another identity field" and "the other branch". Both are the same accepted concept, and the invariant names both outright, so models will likely fix all four together. Low distance. The only real lever is the reserved-prefix and ordering gap, which is an A site.

### openbao-ds
**Host / advisory:** openbao/openbao, GHSA-59W7-V8RR-PR4P / CVE-2026-71543, CWE-863, Go · **Built by:** DeepSeek-built (10-19) · **Pattern label:** A (track: injected per notes) · **Traps:** 8
**Base bug:** Identity-template substitutions (entity, alias and group names and metadata) are pasted unescaped into ACL policy path patterns. A metadata value of `+` or `*` widens a written rule. The report leads to `vault/policy/policy.go` parsePaths.
**Symptom as reported:** "Setting that key to a path wildcard and then requesting a path the written rule was never meant to cover returns the secret." Invariants: "wherever a substituted value is matched against ... a request path, or a name, identifier or host in a certificate request"; metacharacters "include the wildcards ..., the star ..., the separator that splits an allow-list ..., and the path separator". The system section also says the same placeholders "fill the allow-lists on certificate-issuing roles". Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| acl_plus | BASE | M12 | Upstream: `+` substituted into an ACL path (policy.go parsePaths, policy_store.go) | The reported site | none (the documented wildcard) | "a path wildcard" |
| acl_star | SHAPE TRAP | M12 | Upstream: `*` as the final path segment (policy.go) | Another metacharacter at the same site | `*` placed mid-path does nothing, so the shape gets dropped | "the wildcards used when a path pattern is matched" |
| acl_slash | SHAPE TRAP | M12 | Upstream: `/` in the value spans segments, alone or next to a literal `*` (policy.go) | A non-wildcard metacharacter at the same site | "a path separator is not a wildcard" | "and the path separator" |
| pki_uri | A-FAR | M2 | Upstream: templated allowed-URI list matched with glob (pki/cert_util.go validateURISAN) | The same templating feeds a different engine's glob matcher | A role allow-list does not read as a "policy" | "allow-lists on certificate-issuing roles"; "a name, identifier" |
| pki_dom | A-FAR | M2 | Upstream: templated allowed-domains with allow_glob_domains (cert_util.go validateNames) | Same engine, second matcher | Only matters when the admin enabled globs | "the star used when a name ... pattern is matched" |
| ssh_comma | A-FAR | M2 | Upstream: templated SSH allowed_users / allowed_domains split on `,` (ssh/path_issue_sign.go renderPrincipal) | A different engine with a different metacharacter (list separator) | `*` is not a wildcard in SSH, so a wildcard fix looks complete | "the separator that splits an allow-list into entries" |
| ssh_host_glob | INJ | M2 | New SSH role flag allow_glob_domains with a glob branch in the host-principal check (ssh/path_issue_sign.go, path_roles.go) | A glob matcher added to the engine where only `,` is blocked | An optional host-cert feature; `*` is not an SSH metacharacter | "or host in a certificate request"; "the star" |
| pki_userid | INJ | M1 | New PKI role flag allowed_user_ids_template rendered into the glob-matched user-id list (cert_util.go validateUserId, path_roles.go) | A third template flag on the same role reaching an existing glob matcher | A niche subject field; reads as copy-paste | "a name, identifier ... in a certificate request" |

**Outcome:** no gate marker; no DS or MiMo trials.
**Read:** This is one concept (escape substituted values per matcher syntax) spread across three consumers and three metacharacter syntaxes. The real lever is that each matcher needs its own blocked set. Both injected siblings are more consumers of the same concept, and the invariant lists every metacharacter, so it is likely fixed in one shared helper. Distance comes only from the PKI and SSH engines.

### openbao-mm
**Host / advisory:** openbao/openbao, GHSA-59W7-V8RR-PR4P / CVE-2026-71543, CWE-863, Go · **Built by:** MiMo-built (10-18) · **Pattern label:** A (track: injected per notes) · **Traps:** 8
**Base bug:** Same as openbao-ds: identity-template values are pasted unescaped into ACL path patterns (`vault/policy/policy.go` parsePaths, fed by `Store.ACL`).
**Symptom as reported:** Same impact sentence as openbao-ds. Invariants: "matched against something the caller supplies — a request path, or a name in a certificate request"; metacharacters "include the wildcards ..., the star ..., and the separator that splits an allow-list". **Fairness gaps:** unlike openbao-ds, this list does **not** name the path separator, so `acl_slash` (a slash is "not a wildcard") has no explicit covering invariant. It also says only "a name in a certificate request", which covers a serial number (`pki_serial_glob`) only weakly.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| acl_plus | BASE | M12 | Upstream: `+` substituted into an ACL path (policy.go parsePaths) | The reported site | none | "a path wildcard" |
| acl_star | SHAPE TRAP | M12 | Upstream: `*` as the final segment (policy.go) | Another metacharacter at the same site | Mid-path `*` shows no widening | "the wildcards used when a path pattern is matched" |
| acl_slash | SHAPE TRAP | M12 | Upstream: `/` (and `alice/+`) spans segments (policy.go) | A non-wildcard metacharacter at the same site | "a slash is not a wildcard" | weak: not in the metacharacter list (gap) |
| pki_uri | A-FAR | M2 | Upstream: templated allowed-URI glob (pki/cert_util.go validateURISAN) | Another engine's glob matcher | Not a "policy" | "allow-lists on certificate-issuing roles" |
| pki_dom | A-FAR | M2 | Upstream: templated allowed-domains with globs (cert_util.go validateNames) | Same engine, second matcher | Looks like administrator error | "the star used when a name pattern is matched" |
| ssh_comma | A-FAR | M2 | Upstream: SSH allowed_users/domains comma split (ssh/path_issue_sign.go renderPrincipal) | A different engine and metacharacter | `*` is not an SSH wildcard | "the separator that splits an allow-list" |
| ssh_host_glob | INJ | M2 | New SSH allow_glob_domains with a glob branch in the host-principal check (path_issue_sign.go, path_roles.go) | A glob matcher added to SSH | Optional host-cert feature | "the star used when a name pattern is matched" |
| pki_serial_glob | INJ | M1 | New PKI allowed_serial_numbers_template rendered into the glob-matched serial list (cert_util.go validateSerialNumber, path_roles.go) | A third template flag on the same role | Serial numbers are a niche field | weak: "a name in a certificate request" (a serial is not a name) |

**Outcome:** no gate marker; no DS or MiMo trials. (Manifest oddity: the coupled functional test listed for ssh_host_glob is a PKI test.)
**Read:** Same single concept as openbao-ds, so the same judgement applies. The narrower metacharacter wording makes `acl_slash` and the serial sibling fairness risks rather than levers. Compared with openbao-ds (built a day later), the sibling set is identical except that the injected PKI sibling uses the serial-number allow-list instead of the user-id allow-list. openbao-ds also widened the invariant to "identifier or host" and "the path separator", which closed this variant's two gaps.

### orval-ds
**Host / advisory:** orval-labs/orval, GHSA-2H9G-J24R-H63G / CVE-2026-71869 (code injection into generated source; CWE number not stated in the bundle), TypeScript · **Built by:** DeepSeek-built (10-18) · **Pattern label:** A+B, track injected · **Traps:** 15
**Base bug:** A zod schema default value is emitted as a module const after swapping single quotes for backticks, so a backtick or `${...}` in an OpenAPI default becomes live code when the generated module is imported (packages/zod/src/index.ts:842-846).
**Symptom as reported:** "A description whose schema default value contains a backtick or a `${...}` sequence produces a generated module in which that text is no longer data". Invariant: any description string — "default values, property and parameter and form-field names, path text, base-URL text and its variable defaults, and media-type metadata — must remain data in every generated file", "in every generated artifact (HTTP clients, validation schemas, mock and factory code, server scaffolding) and in every supported mode". Every trap is covered, and the invariant enumerates almost every input class.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Upstream: zod default quote swap to backtick; string, array and enum shapes (zod/src/index.ts) | The reported site | none; must generalise across default shapes | "schema default value contains a backtick or `${...}`" |
| T2 | A-FAR | M2 | Upstream: zod property and object-default keys emitted in `"..."` without escaping (zod/src/index.ts) | The same output package, a different literal kind | Double-quoted keys look safe | "property ... names" |
| T3 | A-FAR | M3 | Upstream: shared getKey wraps non-identifier keys in `'...'` (core/getters/keys.ts) | A shared core helper feeding mocks and types | Shared helper; output looks like scaffolding | "property ... names"; "mock and factory code" |
| T4 | A-FAR | M2 | Upstream: static path text into backtick URL literals (core/getters/route.ts getRoute) | Same escaping class, route emitter | "paths are URLs, not code" | "path text" |
| T5 | A-FAR | M5 | Upstream: servers[].url and variable defaults into URL literals (core/getters/route.ts getFullRoute) | A defaults/config route into the same sink | Needs the base-URL-from-spec option | "base-URL text and its variable defaults" |
| T6 | A-FAR | M2 | Upstream: getRouteAsArray single-quoted segments (core/getters/route.ts) | Third route emitter, different quoting | Cache-key bookkeeping | "path text"; "same cache keys" |
| T7 | A-FAR | M2 | Upstream: mutation invalidation prefix, raw path bypass plus a `'...'` literal (query/mutation-generator.ts) | A caller that bypasses the fixed core helper | "core helper is fixed, so callers are safe" | "path text"; "every supported mode" |
| T8 | B-ROUTE | M2 | Upstream: effect output string default quote swap (effect/src/index.ts) | Alternate schema-output package, same bug | Different package from zod | "in every generated artifact" |
| T9 | INJ | M2 | Effect object-default keys emitted bare (effect/src/index.ts:271-286) | Copies zod's pre-fix key omission into the alternate output | The main output's branch was fixed | "property ... names"; "every artifact" |
| T10 | B-ROUTE | M2 | Upstream: hono's own route copy in single-quoted registration (hono/src/route.ts, index.ts) | Second route implementation | Server generator, not client | "server scaffolding"; "path text" |
| T11 | B-ROUTE | M2 | Upstream: MSW route copy in a single-quoted handler URL (mock/src/msw, faker/getters/route.ts) | Third route implementation | Mock/test scaffolding | "mock ... code"; "path text" |
| T12 | B-ROUTE | M1 | Upstream: media-type key emitted as a Content-Type literal (fetch/src/index.ts, core/generators/options.ts) | A different description string into the generated source | "protocol metadata, not code" | "media-type metadata" |
| T13 | B-ROUTE | M1 | Upstream: form-data field names inside literals (core/getters/res-req-types.ts) | A different description string into the generated source | Body field names, buried in a helper | "form-field names" |
| T14 | B-ROUTE | M2 | Upstream: factory date default raw inside `new Date('...')` (core/generators/factory.ts) | Second default emitter (factory) | "a date, already constrained" | "default values"; "factory code" |
| T15 | INJ | M2 | zod $ref-sibling default reuses the quote swap (zod/src/index.ts:450-456) | A copy of the base swap on a rarer path in the same file | Rarely used second default path | "default values"; "every supported mode" |

**Outcome:** gate UNSOUND per the bundle (notes: static missing only the blind patch and FAIRNESS.md; nop and oracle PASS; the patches stage never completed under Harbor because of the shared-host network-prune race, though all 18 checks were run by hand in the image). No DS or MiMo trials.
**Read:** This is breadth, not a new concept. It is 15 emission sites of one rule (escape description strings for their literal kind), and the invariant enumerates every input class and artifact. A model that writes a shared escape helper and greps every emitter will collect most of them. The bite is purely volume: many separate emitters with different quoting (`'`, `"`, backtick). The two injected siblings are copies of known gaps, so they add little.

### pimcore-ds
**Host / advisory:** pimcore/pimcore, GHSA-9X44-4GXF-8C25 / CVE-2026-55634 (code injection plus SQL DDL injection from class definitions; CWE number not stated), PHP · **Built by:** DeepSeek-built (10-19) · **Pattern label:** A+B, track injected · **Traps:** 6
**Base bug:** A DataObject class-definition field name is not validated as an identifier, so an imported definition puts executable PHP into the generated model class and alters definition-save DDL. The report leads to `models/DataObject/ClassDefinition/Data.php` setName.
**Symptom as reported:** "Importing a document whose field name contains characters that are not allowed in an identifier produces a generated model class file that contains executable PHP ... can change the structure of the statements the definition save runs". Invariants: every identifier-used value (field, column, index, constant, property or method name) must be a plain identifier; "a value placed inside a generated comment or string must never be able to end that comment"; DDL identifiers "must be quoted as one identifier"; "Values that configure storage (a column type or a column default) must be a recognised form". Every trap is covered, and the comment and column-default sentences point almost directly at T4 and T6.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_field_name | BASE | M12 | Upstream: field-name validation missing; shapes include metacharacters, backtick, leading digit, >63 chars, trailing newline (ClassDefinition/Data.php) | The reported site | none | "field name contains characters that are not allowed in an identifier" |
| T2_ddl_identifiers | A-FAR | M3 | Upstream: shared DDL trait backtick-wraps raw labels and DB-returned column names; separate objectbrick removeIndices override (ClassDefinition/Helper/Dao.php, Objectbrick/Definition/Dao.php) | Lower layer the published fix also quotes | "setter validation leaves only valid identifiers" | "must be quoted as one identifier, so a label containing a quote..." |
| T3_classificationstore_override | B-ROUTE | M2 | Upstream: Classificationstore::setName overrides the base setter without calling it (Data/Classificationstore.php) | A subclass bypassing the shared guard | "a separate key/group feature" | "every value ... used as an identifier" |
| T4_display_title_comment | INJ | M1 | Field display title written into the generated class docblock (ClassBuilder/FieldDefinitionDocBlockBuilder.php) | A different definition value into generated PHP, comment context | "a title is display text" | "inside a generated comment ... never ... end that comment" |
| T5_legacy_accessor_alias | INJ | M1 | New legacyName field emitted as an extra accessor method (Data.php, ClassBuilder.php) | A second name-carrying field into a generated method name | "an alias, not the field's own name" | "property or method name — must be a plain identifier" |
| T6_storage_default_clause | INJ | M4 | New defaultValueSql passed raw by the Dao save loops into the column DDL (Data.php, four Dao loops) | A storage-config value into DDL, not an identifier | "a DEFAULT clause is SQL by definition" | "a column default ... must be a recognised form" |

**Outcome:** gate UNSOUND per the bundle (notes: static missing only blind/FAIRNESS; nop, oracle and patches 12/12 PASS after re-runs for the network race). No DS or MiMo trials. Notes: the published fix alone leaves 7 security tests failing.
**Read:** T2, T3 and T6 are genuinely different from "validate the field name": quoting in a lower DDL layer, a subclass override that bypasses the setter, and a free-form SQL default. T6 is the most "feature-absent" shaped. But the invariant spells out comment, quoting and column-default rules, which turns them into a checklist. Realistic and fair; the main risk is over-specification.

### portainer-ds
**Host / advisory:** portainer/portainer, GHSA-X626-FCWX-F5PC / CVE-2026-55761, CWE-287, Go · **Built by:** DeepSeek-built (10-18) · **Pattern label:** A, track injected · **Traps:** 5
**Base bug:** On a fresh instance with no administrator, the public `/api/restore` accepts an unauthenticated backup upload, which installs an attacker database and admin account (api/http/handler/backup/restore.go).
**Symptom as reported:** "The client uploaded a backup archive of its own choosing to the instance's restore API ... then signed in with the administrator account contained in the archive." Invariants: "creating the first administrator account and replacing the instance's database from a backup are operator actions ... only for a request that proves knowledge of the instance's current setup token"; "With no token pinned ... the requirement must not be disabled just because no value was configured". Every trap is covered. The invariant names both sink classes (first-admin creation, database replacement), not routes.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T0_restore_upload | BASE | M9 | Upstream: public multipart restore with no setup token (backup/restore.go) | The reported site | none | the restore-API impact sentence |
| T1_admin_init_far_site | A-FAR | M1 | Upstream: public first-admin init (users/admin_init.go) | Another public entry to the same "no admin yet" takeover | The documented first-run wizard, not restore | "creating the first administrator account ... operator actions" |
| T2_restore_local_sibling | INJ | M1 | New public POST /api/restore/local restoring a server-side archive (backup/restore_local.go) | Parallel restore route copying the handler's access policy | Recovery convenience, not the upload | "replacing the instance's database from a backup" |
| T3_legacy_admin_init_sibling | INJ | M1+M2 | New deprecated POST /api/admin/init with its own copy of the creation logic (users/admin_init_legacy.go) | Parallel admin-creation route plus duplicated logic | Legacy code a route-focused fix never visits | "No value of any request ... may let a request create the first administrator" |
| T4_startup_token_producer | A-FAR | M6+M9 | Upstream fix site: token resolved at startup from env/datastore/generated and passed to handlers (cmd/portainer/main.go, http/server.go) | The producer the checks rely on; a fail-open if no token is configured | Wiring looks like plumbing | "must still require a token that it generates itself" |

**Outcome:** gate SOUND. DS 1.0, 0.0, 1.0; MiMo 0.0, 0.0, 1.0 (plus one MiMo NA run with 0 tests). Every 0.0 run fails only the 3 functional cases of the project test `Test_restoreArchive_usingCombinationOfPasswords`, with no security failures. That points to breaking the restore handler's legitimate path (over-broad or signature change), not to a missed sibling. No trap was missed in any counted run.
**Read:** This is one concept (gate every bootstrap-state operation on a token) with more routes. The models closed all five, including the injected ones, every time. The failures are a functional contract issue around the restore project test and are worth checking for test fairness.

### prompty-path-read-inj
**Host / advisory:** microsoft/prompty (Python runtime), GHSA-wxhm-2mq7-7697 / CVE-2026-53598, CWE-22 / CWE-200, Python · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B, track injected · **Traps:** 4
**Base bug:** A frontmatter `${file:}` reference is resolved relative to the prompt's directory and read with no containment, so a hostile `.prompty` pulls in host files (core/loader.py file branch).
**Symptom as reported:** "the loader follows the path the author wrote and reads whatever it lands on — including locations well outside the folder". Invariant: "for every way a document can name an external target — injected file contents, an included text fragment, an inherited base document, and a referenced child prompt — ... regardless of how the path is spelled". This enumerates all four sinks (fairness review: hint and count give-away). **Fairness gap:** the invariant is scoped to "loading that document", while T2 reads during wire projection, not load. The review also flagged T2's test for calling `load()` outside the refusal block, which mis-scores a load-time refusal (HIGH, not yet fixed).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | Upstream: `${file:}` read with no containment; relative, absolute and symlink shapes (core/loader.py) | The reported site | none; a one-shape fix misses absolute paths and symlinks | "relative path that walks upward, an absolute path, or a link" |
| T2 | B-ROUTE | M1 | Upstream: child-prompt tool path joined and loaded during OpenAI wire projection (providers/openai/executor.py _project_prompty_tool) | Another consumer reaching the same file-read sink, outside load() | Provider wire adapter for a tool feature, different package | "a referenced child prompt" (but scoped to "loading") |
| T3 | INJ | M1 | New `${prompt:}` fragment protocol, read in utils.load_fragment (core/loader.py, core/utils.py) | Second reference protocol, read delegated to another file | Trusted composition plumbing | "an included text fragment" |
| T4 | INJ | M5 | New `base:` document loaded and merged for defaults (core/loader.py _build_agent) | Inheritance/defaults route to the same read | A separate inheritance feature | "an inherited base document" |

**Outcome:** gate_report passed=False; fairness NOT READY (fairfix not applied). DS 0.8333, 1.0; MiMo 0.8333 x3. Every failed run misses only T2 (`test_prompty_tool_child_path_traversal`): DS r1 and MiMo r1-r3. DS closed it on r2. This is a MiMo-only lead per the report, provisional until the T2 test is fixed.
**Read:** The injected siblings are different features but are named in the invariant, so both models collected them every time. Only the real upstream B route that reads outside `load()` bit. The miss is partly a wording gap ("loading") plus a test-construction fault, so the MiMo signal is not trustworthy yet.

### prompty-ds
**Host / advisory:** microsoft/prompty (Python runtime), GHSA-wxhm-2mq7-7697 / CVE-2026-53598, CWE-22 / CWE-200, Python · **Built by:** DeepSeek-built (10-18) · **Pattern label:** A+B, track injected · **Traps:** 6
**Base bug:** The same `${file:}` frontmatter reference read with no containment (core/loader.py:170).
**Symptom as reported:** "Calling the public load call on a document taken from a template gallery is enough to return a description built from a file that lives outside the gallery directory." Invariant: "No path written anywhere in a prompt document may cause loading or using that document to read a file outside ... whichever part of the document or composition feature names the path, whether the path is named in the document itself or in a file the document pulls in, and regardless of how the path is spelled or what it resolves to on disk." Every trap is covered without listing sinks. The keep-working list ("inherited defaults, inlined body text, and a child prompt declared as a tool") hints at T2, T4 and T6.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | Upstream: `${file:}` sink; 8 shapes (relative, absolute, symlink file and dir, prefix-sharing sibling, nested in pulled file, array element, async) (core/loader.py) | The reported site | none; lexical or one-spelling containment misses links and prefix siblings | "regardless of how the path is spelled or what it resolves to on disk" |
| T2 | B-ROUTE | M1 | Upstream: child-prompt tool path at provider request build and public dispatch (providers/openai/executor.py, core/tool_dispatch.py) | Two consumers reaching the same read outside load() | Tool wiring in a provider adapter | "loading or using that document"; keep-working "child prompt declared as a tool" |
| T3 | INJ | M1 | `${prompt:}` fragment protocol, read in utils.load_fragment (core/loader.py, core/utils.py) | Second reference protocol | Composition plumbing in another file | "whichever part ... or composition feature" |
| T4 | INJ | M5 | `base:` inheritance, key popped before the resolver (core/loader.py) | Defaults-merge route to the same read | Looks unrelated to reference expansion | "composition feature"; keep-working "inherited defaults" |
| T5 | INJ | M6 | YAML `!include` constructor in the parser, including nested in a pulled file (core/utils.py:30) | The parser reads the file before the loader's resolver ever sees it | "ordinary YAML config composition" | "named ... in a file the document pulls in" |
| T6 | INJ | M1 | Body `@include` partial expansion (core/loader.py:109, core/partials.py) | Body-side directive to the same read | Body composition, not frontmatter | "written anywhere in a prompt document"; "inlined body text" |

**Outcome:** gate SOUND. DS 0.8667, 1.0; MiMo 0.8667, 0.8667, 1.0. Every failed run misses only T2 (`test_prompty_tool_projection_relative` and `test_prompty_tool_dispatch_absolute`): DS r1, MiMo r1 and r2. Both models solved by a later run.
**Read:** Again the only biting sibling is the real tool-child route that reads outside the load path. All four injected siblings, including the parser-level `!include`, were closed every time, so injected composition features read as one concept. Compared with prompty-path-read-inj, this variant drives T2 through both projection and dispatch, widens the invariant to "loading or using", adds more T1 shapes, and adds two more injected composition siblings (YAML include, body partial). T2 still bit only on first runs.

### prompty-mm
**Host / advisory:** microsoft/prompty (Python and TypeScript runtimes), GHSA-wxhm-2mq7-7697 / CVE-2026-53598, CWE-22 / CWE-200, Python + TypeScript · **Built by:** MiMo-built (10-18) · **Pattern label:** A+B, track injected · **Traps:** 7
**Base bug:** The same `${file:}` reference read with no containment (Python core/loader.py:155).
**Symptom as reported:** "the runtime follows the path the author wrote and reads whatever it lands on". Invariant: "for every part of a document that can name a file, and at every point in the document's life — loading it, rendering its body, and anything the runtime does on the loaded prompt's behalf ... whether the path is given on its own or as one entry among several". The system section names "a companion prompt it later invokes" and body snippets. **Fairness gap:** nothing says the repository ships a second language runtime. "the runtime" and "the library's public load call" read as the Python package, so T2 (TypeScript loader) is covered only by an implicit "every runtime" reading.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M8 | Upstream: `${file:}` sink; relative, absolute, symlink and list-entry shapes (python core/loader.py) | The reported site | none; a `..`-only fix misses the other shapes | "regardless of how the path is spelled ... one entry among several" |
| T2 | A-FAR | M2 | Upstream (published-fix far site): same reference expansion in the TypeScript package (runtime/typescript/packages/core/src/core/loader.ts) | Second-language implementation of the same sink | The advisory is Python-scoped; looks like a parallel port | weak: only "every part ... the runtime" (gap) |
| T3a | B-ROUTE | M1 | Upstream: companion-prompt tool loaded at request build (providers/openai/executor.py) | Consumer outside load() | Tool-kind feature, spec resolves relative to parent | "anything the runtime does on the loaded prompt's behalf" |
| T3b | B-ROUTE | M1 | Upstream: companion prompt loaded at tool dispatch (core/tool_dispatch.py) | Second consumer route to the same read | Host-side dispatcher concern | same as T3a |
| S1 | INJ | M1 | `${prompt:}` fragment protocol read in utils.load_fragment (core/loader.py, core/utils.py) | Second reference protocol | Trusted plumbing in another file | "a reusable block of text"; "every part of a document" |
| S2 | INJ | M5 | `base:` inherited-document include (core/loader.py _build_agent) | Inheritance route | Separate defaults-merge feature | "defaults inherited from a related document" |
| S3 | INJ | M1 | Jinja2 renderer given a filesystem loader for `{% include %}` (renderers/jinja2.py _PromptDirLoader) | Render-time read in another package | The template is "already sandboxed"; an authoring convenience | "rendering its body"; "a shared snippet can be pulled into it" |

**Outcome:** no gate marker in the status (notes: static missing only blind/FAIRNESS; nop, oracle x3 and patches 8/8 PASS). No DS or MiMo trials.
**Read:** This variant adds the one genuinely different-distance sibling of the family: the TypeScript implementation. It is also the least supported by the text, so it is a likely-to-bite lever with a fairness question. The rest is the same composition-feature set models already close. Compared with prompty-path-read-inj and prompty-ds, it keeps the biting tool-child route (split into two traps), replaces the YAML and body-partial siblings with a renderer-package include, and adds the TS far site. It widens the lifecycle wording, as prompty-ds does.

### protobuf.js-ds
**Host / advisory:** protobufjs/protobuf.js, GHSA-JFJ6-75FJ-8934 / CVE-2026-59876, CWE-1321, JavaScript · **Built by:** DeepSeek-built (10-18) · **Pattern label:** A, track injected · **Traps:** 11
**Base bug:** A text-format map entry keyed `__proto__` replaces the returned map's prototype instead of being stored as an own key (ext/textformat.js addMapEntry).
**Symptom as reported:** "the map that comes back has been altered: the entry is not present as data, `admin` appears to be a property of the map itself". The text continues: "The same class of confusion appears wherever a name ... becomes a key in an object the library builds or stores — a message field, a map entry, an enum identifier, an option or setting name, a descriptor entry, an emitted table." Invariants also cover reading unset settings, dotted setting paths, and generated code. **Fairness concerns:** R2 reads the prototype of the *input* plain object, which is neither "returned or stored", so coverage is only via "never resolved to a property the object inherits". The coupled functional test for S2 ("an unsafe option name is ignored and leaves the options object shape alone") is not stated in the instruction, which instead says a declared name "must ... be stored ... like any other name".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Upstream: `__proto__` map key; brace, angle, list and scalar forms (ext/textformat.js) | The reported site | none | the example |
| T2 | A-FAR | M1 | Upstream: field containers read/written by schema field name (toString, hasOwnProperty) (ext/textformat.js addField/parseMapField) | Same parser, a different name source | Field names look trusted (schema) | "a message field" |
| T3 | A-FAR | M6 | Upstream: enum values table inherits Object.prototype; producer for text and JSON parsing (src/enum.js) | Producer two layers below both parsers | Schema metadata, not the parser | "an enum identifier"; "never resolved to a property the object inherits" |
| T4 | A-FAR | M5 | Upstream: getOption/setOption ifNotSet and util.merge ifNotSet treat inherited as set (src/object.js, src/util/minimal.js) | Defaults/merge route | Metadata plumbing | "Reading a setting that was never set reports it as absent" |
| T5 | A-FAR | M2 | Upstream: .proto aggregate option member read without an own check (src/parse.js) | Second parser | Build-time developer input | "an option or setting name" |
| T6 | A-FAR | M2 | Upstream: descriptor import enum value `__proto__` reparents valuesOptions (ext/descriptor.js) | Second implementation | Optional extension | "a descriptor entry" |
| T7 | A-FAR | M2 | Upstream: static generator emits an enum table that inherits Object.prototype (cli/targets/static.js) | Generated copy of the runtime table | Build-time tool | "an emitted table"; "Anything the library generates" |
| R1 | B-ROUTE | M5 | Upstream: dotted setProperty reads inherited segments; reaches shared built-ins (src/util.js) | Settings-write route | The unsafe-name guard already exists | "Writing a setting by a dotted path stores the given value at every segment" |
| R2 | B-ROUTE | M1 | Upstream: converter fromObject reads absent fields from the input object's prototype, also in emitted code (src/converter.js) | Conversion entry point, read-side | Converts the application's own object | weak: "never resolved to a property the object inherits" (input object) |
| S1 | INJ | M2 | Single-segment fast path in setParsedOption skipping the path logic (src/object.js) | Duplicate path logic without checks | Parsed options look like diagnostics | "an option or setting name" |
| S2 | INJ | M8 | setProperty's unsafe-name guard applied only while recursing, not to the final segment (src/util.js) | A partial guard on the same helper | The guard is visibly present | "no shared built-in object is modified" |

**Outcome:** gate SOUND. DS 0.8889, 0.0, 0.0; MiMo 0.0, 0.0, 0.0.
- DS r1 missed T3 (values table), T4 (merge) and T7.
- DS r2 missed T3 and T7, plus functional failures.
- DS r3 failed functional only.
- MiMo r1 missed T3 (text, JSON and table), T4, T7 and R2 (both), plus functional failures.
- MiMo r2 failed functional only.
- MiMo r3 missed T4 and R2, plus functional failures.

Missed: T3 both, T4 both, T7 both, R2 MiMo only. In 5 of 6 runs the S2-coupled functional test and the project area tests fail. That is the main cause of the 0.0 scores (an over-broad or contract-conflicting fix).
**Read:** The biting siblings are the lower-layer producer (enum table), the merge/defaults helper and the generated table. These are genuinely different from "fix the parser's map write" (M6, M5, M2 at distance), and they bit both models. The injected siblings were never missed. The 0.0 scores rest heavily on an unstated "ignore unsafe option names" contract, which needs a fairness check before this counts as a breaker.

### protobuf.js-mm
**Host / advisory:** protobufjs/protobuf.js, GHSA-JFJ6-75FJ-8934 / CVE-2026-59876, CWE-1321, JavaScript · **Built by:** MiMo-built (10-18) · **Pattern label:** A, track injected · **Traps:** 10
**Base bug:** The same `__proto__` text-format map key replacing the map's prototype (ext/textformat.js addMapEntry).
**Symptom as reported:** The same example. Invariants: "No name the library takes from input may reach or read the inherited shape of any object", "Reading a setting that was never set reports it as absent", "Rules the library applies at runtime apply equally to anything it emits as code", and "for every operation the library offers — compiling a schema, parsing a message in either wire format, building or importing schema objects, reading and writing settings, merging input into an existing object, and generating code". Every trap is covered; the list names the injected merge entry points outright.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Upstream: `__proto__` map key; brace, angle, list, scalar and omitted-key shapes (ext/textformat.js) | The reported site | none; a one-delimiter fix misses forms | the example |
| T2 | A-FAR | M1 | Upstream: camelCased field names (to_string, has_own_property ...) written with plain property writes (ext/textformat.js) | Same parser, a different name source | The schema looks trusted | "a message field" |
| T3 | A-FAR | M6 | Upstream: Enum valuesById inherits Object.prototype; Enum#add false duplicate (src/enum.js) | Producer table read by the parsers | Enum never parses text | "an enum identifier"; "never resolved to a value the container happens to inherit" |
| T4 | A-FAR | M5 | Upstream: getOption returns inherited values; setOption ifNotSet skips (src/object.js) | Settings route | Reflection API, not the parser | "Reading a setting that was never set reports it as absent" |
| T5 | A-FAR | M2 | Upstream: .proto aggregate option member read without an own check (src/parse.js) | Second input language | Developer action | "compiling a schema" |
| T6 | A-FAR | M3 | Upstream: util.merge ifNotSet treats inherited keys as set (src/util/minimal.js) | Shared internal helper | Internal helper, not an entry point | "merging input into an existing object" |
| T7 | A-FAR | M2 | Upstream: descriptor import lookup tables (mapEntries, valuesOptions, groupTypeNames) are plain `{}` (ext/descriptor.js) | Second implementation | Someone else's module | "a descriptor entry"; "importing schema objects" |
| T8 | A-FAR | M2 | Upstream: pbjs static emits `valuesById = {}` (cli/targets/static.js, proto.js) | Generated copy | A generator's threat model differs | "anything it emits as code" |
| S1 | INJ | M1 | New Type#mergeFromText writing fields and map entries by direct assignment into the caller's target (ext/textformat.js) | Merge entry point to the same write | A caller-owned target, not the returned map | "merging input into an existing object" |
| S2 | INJ | M2 | New Type#mergeFromJson bypassing the module's safe-write helper (ext/protojson.js) | Merge path duplicating writes without the helper | The module looks covered by its helper | "parsing a message in either wire format ... merging input" |

**Outcome:** no gate marker in the status (notes: nop and oracle x3 PASS; patches still in progress with network flakes). No DS or MiMo trials.
**Read:** Like protobuf.js-ds, the distance lies in the enum producer, the merge helper, descriptors and the generator. These are the A far sites that bit the DS-built variant. The injected merge APIs are named in the invariant's operation list, so they are unlikely to bite. Compared with protobuf.js-ds, this set drops both real B routes (dotted setProperty, converter fromObject) and the setParsedOption/setProperty injected gaps. It splits util.merge into its own trap and injects merge-into-existing-object entry points instead. It has no unstated "ignore unsafe option names" coupled contract.

### rsdoctor-ds
**Host / advisory:** web-infra-dev/rsdoctor, GHSA-JMG2-RCXH-W8Q3 / CVE-2026-61782, CWE-200 (local dev-server exposure), TypeScript · **Built by:** DeepSeek-built (10-19) · **Pattern label:** A, track injected · **Traps:** 8 (T6 is a functional-only producer)
**Base bug:** The report server sends `cors()` plus `Access-Control-Allow-Origin: *` on every response, so any web origin can read the build analysis (packages/sdk/src/sdk/server/index.ts).
**Symptom as reported:** "a web page on any origin can read the analysis, and a client on another machine can reach it". Six numbered rules state the fix almost literally: bind to `127.0.0.1`, require a local Host, refuse a non-local Origin "on every route and every method", a per-instance `token` credential for the realtime channel, "When the client server is disabled (`noServer`), nothing may listen", "Every other HTTP surface ... follows rules 1–3", and "every route ... including routes an integrator registers later". Every trap is covered, and most are named outright (heavy over-specification).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Upstream: wildcard CORS on GET, POST, OPTIONS and the static report (sdk/server/index.ts) | The reported site | none | "a web page on any origin can read the analysis"; rule 3 |
| T2 | A-FAR | M8 | Upstream fix: foreign or missing Host, mismatched `*.localhost` origin (sdk/server/index.ts, security.ts) | DNS rebinding, a distinct check | "the report is about CORS" | rule 2 (names the allowed host spellings) |
| T3 | A-FAR | M3 | Upstream: shared createServer listens on all interfaces (packages/utils/src/build/server.ts) | Lower shared helper in another package | Generic util | rule 1 ("bound to ... `127.0.0.1`") |
| T4 | A-FAR | M1+M4 | Upstream: WebSocket accepts any handshake, no per-server credential (sdk/server/socket/index.ts) | Second protocol on the same port, protection never existed | "a browser cannot read WS cross-origin anyway" | rule 4 (names `token`, `socketUrl`) |
| T5 | A-FAR | M2 | Upstream: noServer fake server still bootstraps a listener (sdk/server/fakeServer.ts) | Subclass inherits the listening bootstrap | "not a server at all" | rule 5 (names `noServer`) |
| T6 | COUPLED TRAP | M11 | Upstream fix: server.port / server.cors produced by the config loader and threaded through the plugin and SDK (core/.../config.ts, rspack-plugin) | Must-keep-working config producer; no security test | n/a (functional only) | rule 6 |
| S1 | INJ | M2 | New assistant HTTP bridge with wildcard CORS, any Host, all interfaces (packages/ai/src/server/http.ts) | Second data-serving implementation | "the assistant helper, not the report server" | rule 5 "Every other HTTP surface ..." |
| S2 | INJ | M7 | New addRoute helper inserting integrator routes ahead of the request checks (sdk/server/index.ts) | Ordering: route runs before the guard | "integrator routes are trusted" | rule 5 "including routes an integrator registers later" |

**Outcome:** no gate marker in the status, but the manifest records static PASS (except downstream blind/FAIRNESS), nop PASS, oracle PASS x3 and patches PASS 18/18 (10-19). No DS or MiMo trials.
**Read:** Several siblings are genuinely different mechanisms: bind address, Host check, WebSocket auth and route ordering. But the instruction enumerates each one, including the injected bridge and the addRoute ordering, so the task reads as a documented checklist (documented checklists have not bitten in earlier rounds). Low expected difficulty unless volume alone bites.

### seaweedfs-s3tables-authz
**Host / advisory:** seaweedfs/seaweedfs, GHSA-HGPF-8634-G44C / CVE-2026-55873, CWE-863, Go · **Built by:** Opus build-v1 template, batch 1 (10-17) · **Pattern label:** A+B · **Traps:** 6
**Base bug:** In the S3 Tables API, the open-by-default fallback applies to authenticated callers, and principals are mis-derived (any admin-account member counts as admin). A signed `ListTableBuckets` from another account's user therefore returns other accounts' buckets (landing: handler_bucket_get_list_delete.go).
**Symptom as reported:** "a user in their own account holding only ordinary S3 permissions sends a signed `ListTableBuckets` request and gets back other accounts' table buckets". Invariants: "every operation and every front end that serves remote callers"; "Only an identity granted administrative permissions is an administrator; no other attribute ... makes it one"; "An authenticated caller never gets access just because nothing denied it"; "Only authentication decides who a request acts as ... whatever else it carries". Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M10 | Upstream: admin-account member, or identity with an unknown account, treated as admin (s3tables/handler.go; producer auth_credentials.go) | Principal mis-derivation in the shared helper (notes label it "landing + shared principal helper") | Admin-account membership looks like intent | "Only an identity granted administrative permissions is an administrator" |
| T2 | BASE | M9 | Upstream: open default applied to authenticated callers on 28 policy contexts (s3tables/permissions.go, handler_*.go, s3api_tables.go) | The reported trigger (other-account user lists, reads and deletes) | Default-allow is documented zero-config; fixing the listing looks enough | "An authenticated caller never gets access just because nothing denied it" |
| T3 | A-FAR | M2+M9 | Upstream: Iceberg catalog manager forced open; name-only callers treated as unauthenticated (s3tables/manager.go, iceberg/server.go) | Second front end with the same fail-open | Manager is a tooling helper; catalog is another package | "every front end that serves remote callers"; "embedded with its own authenticator" |
| T4 | B-ROUTE | M10 | Upstream: client `s3-account-id` header becomes the principal for credential-less requests (handler.go, s3api_tables.go) | Attacker-chosen principal field | Only reachable on an already open gateway | "Only authentication decides ... whatever else it carries ... explicit Deny always applies" |
| T5 | B-ROUTE | M10 | Upstream: IdP `sub` or `preferred_username` = admin becomes admin (handler.go:190-205) | Identity confusion by attribute | Claims come from the trusted IdP | "no other attribute of an identity makes it one" |
| T6 | B-ROUTE | M10 | Upstream: embedding-authenticator caller named "admin" becomes admin via the manager (handler.go, permissions.go, manager.go) | Name-only principal | The admin console relies on acting as admin by name | "no other attribute ..."; "trusted local tools" carve-out |

**Outcome:** gate_report passed=False; fairness NOT READY (notes record a fairness revision on 10-17 that added T6 and reworded P2). DS 1.0 (1 run), MiMo 1.0 (1 run): no trap missed.
**Read:** Two concepts (fail-open for authenticated callers, principal mis-derivation) with B routes that are variants of the second. The invariant states both crisply, and both models solved it on run 1. The siblings are routes of accepted concepts, not new ones.

### seaweedfs-ds
**Host / advisory:** seaweedfs/seaweedfs, GHSA-HGPF-8634-G44C / CVE-2026-55873, CWE-863, Go · **Built by:** DeepSeek-built (10-19) · **Pattern label:** A+B (three injected siblings, labelled "B" in the manifest) · **Traps:** 10
**Base bug:** The same as seaweedfs-s3tables-authz: the open default applies to authenticated callers, and admin principals are mis-derived. An other-account `ListTableBuckets` returns foreign buckets.
**Symptom as reported:** Same impact sentence. The invariants add "to every object in a multi-object request", "The owner of a resource, and the resource a request acts on, come from what the server has recorded, never from an identifier the request supplies", "nor ... of a request", and "a create that is refused leaves no file, directory or registration behind". Each added sentence maps to one new trap (T9, T8, T4, T7). Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M10 | Upstream: admin-account member or unknown-account identity treated as admin (s3tables/handler.go; auth_credentials.go) | Principal mis-derivation | Membership looks like intent | "Only an identity granted administrative permissions is an administrator" |
| T2 | BASE | M9 | Upstream: open default for authenticated callers, 28 contexts (permissions.go, iam.go, handler_*.go) | The reported trigger | Default-allow is documented; listing fix looks enough | "An authenticated caller never gets access just because nothing denied it" |
| T3 | A-FAR | M2+M9 | Upstream: catalog name-only caller treated as unauthenticated and falls open (iam.go, iceberg/server.go, manager.go) | Second front end | Separate REST protocol and package | "every front end"; "whatever caller that authenticator reports" |
| T4 | B-ROUTE | M10 | Upstream: client account header becomes the principal (handler.go, s3api_tables.go) | Attacker-chosen principal | Gateway already open | "never from an identifier the request supplies"; "whatever else it carries" |
| T5 | B-ROUTE | M10 | Upstream: IdP claim = admin becomes admin (handler.go) | Attribute-based identity confusion | Trusted IdP | "no other attribute of an identity" |
| T6 | B-ROUTE | M10 | Upstream: name-only "admin" via the catalog Manager (handler.go, permissions.go, manager.go) | Name-only principal | Console relies on admin-by-name | "no other attribute ... or of a request" |
| T7 | B-ROUTE | M7 | Upstream: Iceberg CreateTable writes metadata and the table dir before authorization (iceberg/handlers_table.go) | Side effect before the check | Storage plumbing; the refusal still looks clean | "a create that is refused leaves no file, directory or registration behind" |
| T8 | INJ | M10 | New GetTableBucketUsage authorizes with the account in the caller-supplied ARN plus the raw open flag (s3tables/handler_bucket_usage.go) | Owner taken from the request | "the ARN already carries the owning account" | "owner ... never from an identifier the request supplies" |
| T9 | INJ | M10 | New BatchDeleteTables authorizes the first table once, deletes all (s3tables/handler_table_batch.go) | Authorizes a different object than the ones touched | "a batch targets one bucket" | "to every object in a multi-object request" |
| T10 | INJ | M1 | New catalog table index reads the filer directly with no per-table decision (iceberg/handlers_index.go, server.go route) | Parallel read endpoint bypassing the manager | "an index only returns identifiers" | "Listings leave out resources the caller may not see" |

**Outcome:** no gate marker in the status (notes: static missing only blind/FAIRNESS; nop, oracle and patches 18/18 PASS, run one check at a time). No DS or MiMo trials.
**Read:** T7 (ordering) and T9 (per-object authorization in a batch) are genuinely different mechanisms from the base. But each has its own invariant sentence that names it, so they become checklist items rather than hidden depth. Compared with seaweedfs-s3tables-authz (solved 1.0 by both), this keeps the same T1-T6 and adds a real ordering route (T7) plus three injected siblings (forged ARN owner, batch first-item check, catalog index). The added invariant sentences point at each new trap.

### siyuan-ds
**Host / advisory:** siyuan-note/siyuan, GHSA-FGMR-7W36-9QFQ / CVE-2026-72796, CWE-862, Go · **Built by:** DeepSeek-built pilot (build-v1 template, 10-18) · **Pattern label:** A+B, track injected · **Traps:** 9
**Base bug:** In publish mode a reader reaches the kernel's static routes (`/templates/`, `/export/`, `/widgets/`, `/plugins/`, `/emojis/`, `/snippets/`), which run only the authentication check and not the publish access rules, so excluded resources are served. The report leads to those static handlers in `kernel/server/serve.go`.
**Symptom as reported:** "A visitor with reader access to one published document was able to download a document template, a generated export of a note, and a code snippet that the owner had explicitly excluded ... could enumerate installed packages that were excluded from publishing, and saw custom emoji that no published document used." Invariants: no unpublished template/export/snippet "under any request method"; plugins only when "installed, enabled ... and not marked as excluded"; widget/emoji only when "a document the visitor can read uses it"; "listings and catalogs of these resources must expose only entries the visitor may receive"; "Apply the rules to every route that can return these resources and to every listing". Every trap has a covering invariant. The template-listing case needs two invariants combined (templates are never receivable, and listings show only what is receivable).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_widgets_emojis_producer | BASE | M6 | serve.go widgets/emojis + new publish_resource_access.go reference mapper (published fix) | reported site; needs a document-reference producer | per-document relationship easy to overlook; no publish flag on emoji; blanket deny breaks pages | "saw custom emoji that no published document used"; "a document the visitor can read uses it" |
| T2_snippets_fallback | A-FAR | M9 | serve.go serveSnippets: disk-only snippet fallback + publish switch | same static channel, second code path | a file on disk has no flag to check | "a file that merely exists on disk is not published" |
| T3_templates_export | A-FAR | M1+M4 | serve.go serveTemplates/serveExport (incl. /export/temp/, HEAD) need an admin gate | neighbouring static routes | no publish flag exists for these classes; export handler looks unrelated | "download a document template, a generated export"; "under any request method" |
| T4_plugins | A-FAR | M1 | serve.go servePlugins + loaded-petal state | neighbouring resource class | "published pages need plugin JS"; depends on loaded state | "installed, enabled in this workspace, and not marked as excluded" |
| T5_path_shapes | SHAPE TRAP | M8 | serve.go static file helper: traversal, nested symlink, top-level symlink, dir->index | input shapes of the same routes | top-level symlink must keep working while nested one is refused | "Path spellings that climb out ... symbolic links inside a package" |
| T6_marketplace_listings | B-ROUTE | M1 | kernel/api/bazaar.go installed plugin/widget/template listings (real, unfixed upstream) | metadata API, other package | "marketplace metadata API, not a static-file route" | "could enumerate installed packages"; "listings and catalogs ... must expose only entries" |
| T7_emoji_catalog | B-ROUTE | M1 | kernel/api/system.go getEmojiConf (still in upstream) | catalog API, other package | "the picker needs it; names only" | "listings and catalogs"; emoji rule |
| T8_injected_preview_resolver | INJ | M1 | serve.go GET /publish-preview/*filepath serves data-relative files, CheckAuth only | parallel entry to the same files | name looks publish-aware, so assumed guarded | "every route that can return these resources" |
| T9_injected_snippet_preview | INJ | M1 | serve.go GET /snippet-preview?name=&type= ignores the publish switch | parallel entry to snippet content | query-param preview helper, not a static path | snippet rule + "every route" |

**Outcome:** gate SOUND; fairness not stated. DS raw 0.0, 0.0, 0.9375; MiMo raw 1.0 (one run). DS missed T6 in all 3 runs (`TestPubAccessReaderTemplateListingFiltered`: it still showed the template listing to readers) and T3 in r1 (`TestPubAccessTemplateRefusedToReader`). In r1 and r2 DS also failed the coupled functional `TestPubUsePreviewResolverServesPublishedResources` (an over-broad fix on the T8 resolver, not a missed sibling). MiMo missed nothing.
**Read:** The template listing is the sibling that held. It is a different concept (it describes metadata rather than serving file bytes), and it only follows by combining two invariants. Most of the other siblings are more routes under one "check publish access everywhere" concept, and both models swept them. One model solved it in one run, so the task is not a breaker.

### summarize-ds
**Host / advisory:** steipete/summarize, GHSA-3VX2-VQX8-JXFG / CVE-2026-53782, CWE-918 SSRF, TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, 10-19) · **Pattern label:** A+B (injected siblings) · **Traps:** 6
**Base bug:** A podcast feed's declared `<podcast:transcript url>` is fetched with redirect follow and no scheme, address or DNS check (`podcast/rss-transcript.ts:53`), and the internal response comes back as the transcript.
**Symptom as reported:** "Summarizing a podcast feed that declares its transcript at an internal address makes the process connect to that address ... The same connection is made when a page's own markup names an internal address, and when the background service is asked to summarize a URL presented in an accepted address form that maps to an internal one." Invariants: "No URL that arrives inside content being summarized may cause a network connection to a ... non-public address ... (including forms whose value embeds an IPv4 address), to names that resolve to such an address, and to every hop of a redirect chain"; "The background service must apply the same rule"; "including URLs that content declares for data other than the transcript." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_base_transcript | BASE | M8 | podcast/rss-transcript.ts: literal IPv4/IPv6, DNS-private name, public->private redirect | reported sink | none | the feed-transcript example; "after name resolution and after any redirect" |
| T2_daemon_blocklist | A-FAR | M2+M8 | src/daemon/url-fetch-guard.ts: second blocklist misses NAT64/6to4 and reserved v6 ranges | duplicate guard in another package | "the daemon already has an SSRF guard" | "accepted address form that maps to an internal one"; "forms whose value embeds an IPv4 address" |
| T3_caption_route | B-ROUTE | M1 | generic-embedded.ts page `<track src>` fetched unguarded (real upstream) | another content-declared fetch | "generic HTML provider, not the podcast feature" | "when a page's own markup names an internal address" |
| T4_enclosure_route | B-ROUTE | M1 | podcast provider-flow.ts + media.ts enclosure HEAD/GET (real upstream) | another feed-declared fetch | "it is the episode audio the user asked to transcribe" | "data other than the transcript" |
| T5_injected_chapters | INJ | M1 | new podcast/chapters.ts fetches `<podcast:chapters url>` copied from the transcript fetch | sibling fetch in the same item parser | "chapter titles are optional enrichment" | "data other than the transcript" |
| T6_injected_spotify_transcript | INJ | M1 | podcast/spotify.ts + spotify-flow.ts fetch an embed-declared transcriptUrl | parallel provider flow | "the Spotify flow already fetches third-party feed data" | "every URL obtained from content under summarization" |

**Outcome:** gate SOUND (all 13 checks as declared); fairness not stated. No DS or MiMo trials recorded; no per-test data.
**Read:** Except for T2, the siblings are more sinks of one concept ("guard every content-derived fetch"), and the instruction says outright that the rule covers non-transcript URLs. A central guarded transport (the shape of pass_alt_fix) closes them all at once, so a model that sweeps fetches will close them together. T2 (a duplicate guard that misses IPv4-embedding IPv6 forms) is the only distinct concept, and the report names it ("accepted address form").

### suneditor-xss-inj
**Host / advisory:** jihong88/suneditor, GHSA-W93Q-CQ9W-58P7 / CVE-2026-54606, CWE-79 DOM XSS, JavaScript · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B, track injected · **Traps:** 6
**Base bug:** The embed plugin turns pasted embed HTML into live DOM. In `#create` in `src/plugins/modal/embed.js`, a top-level `<script src>` is re-created as a live script, and iframe sources are never validated.
**Symptom as reported:** "the pasted markup causes author-controlled script to run in the editor's own page ... submit embed code that ... would load a script from, or frame, an author-chosen address." Invariants: no script "unless its source has been explicitly opted in ... including nested inside another pasted element"; frames only from a recognised provider and "no placed frame may carry inline document content of its own"; "No pasted markup may keep inline event-handler attributes"; "whether the submission inserts a new embed or replaces/edits an embed". The invariants map almost one-to-one onto the traps. Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | embed.js #create: top-level `<script src>` recreated live | reported site; must gate sources, not drop one literal | none | "load a script from ... an author-chosen address" |
| T2 | A-FAR | M4 | embed.js submitSRC: off-provider iframe src (top level or in a blockquote) placed unvalidated | same input, other element type | "iframe-src validation looks like separate URL filtering" | "or frame, an author-chosen address"; "frame ... recognised as an embeddable provider" |
| R1 | B-ROUTE | M8 | embed.js: provider-src iframe carrying `srcdoc` (real upstream, open after the published fix) | allow-listed src passes, other attribute not inspected | "src is on the provider list; srcdoc is an attribute detail" | "no placed frame may carry inline document content" |
| R2 | B-ROUTE | M4 | embed.js #create child-append: non-script sibling keeps `on*` handler (real upstream) | same append loop, no attribute sanitising | "general HTML sanitisation, a neighbouring feature" | "No pasted markup may keep inline event-handler attributes" |
| S1 | INJ | M8 | embed.js #create: `<script>` nested in a provider blockquote re-created without the opt-in gate | nested copy of the base sink | "top-level gate assumed sufficient" | "including nested inside another pasted element" |
| S2 | INJ | M2 | embed.js #create update/edit branch duplicates create logic without the guards | second implementation for the edit path | "edit acts on an already-validated embed" | "replaces/edits an embed that is already in the document" |

**Outcome:** no gate marker (notes say nop, oracle and patches passed); fairness not stated. DS raw 1.0, 1.0, 1.0; MiMo raw 1.0, 0.0, 1.0. MiMo r2 failed only one project functional case ("submitSRC should call handler with result when event returns an object"), which points to an over-broad fix or a broken callback, not a missed sibling. No sibling was missed by either model.
**Read:** All six traps sit in one file, and each is spelled out as its own invariant clause, so the task works as a checklist and both models fixed them together. The siblings are variants of one sanitiser concept. Nothing realistic or unfair stands out, but the task gives no difficulty lever.

### surrealdb-ds
**Host / advisory:** surrealdb/surrealdb, GHSA-66R2-5GWJ-GXM2 / CVE-2026-63733, CWE-863, Rust · **Built by:** DeepSeek-built pilot (build-v1 template, 10-19) · **Pattern label:** A+B, injected siblings · **Traps:** 6
**Base bug:** Definer-authored permission predicates are computed with permission enforcement disabled, and nothing stops a data-modifying statement inside them. The report leads to the table permission predicate (`doc/check.rs:461`), where a helper function writes during a record user's UPDATE. The base has no trap row of its own.
**Symptom as reported:** "The table's `update` permission expression calls a helper function, and that helper creates a row in a different table." Invariants: "Evaluating any expression a definition stores must never create, update or delete data ... inline, in a nested block, through a helper function body, or through a subquery"; a stored permission clause containing a write must be refused at definition time, "both when a definition is created and when an existing definition is replaced"; "They apply to every definition kind that stores an expression". Every trap is covered. Events, views and ASSERT/VALUE fall under "every definition kind that stores an expression", not under the word "permission".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| far_permission_sites | A-FAR | M1 | doc/field.rs, doc/output.rs, doc/reduce.rs, expr/function.rs, expr/param.rs permission predicates | same predicate evaluation at other definition kinds | "report is about a table's PERMISSIONS" | "every definition kind that stores an expression" |
| api_endpoint_permission | A-FAR | M1 | api/invocation.rs endpoint permission predicate | far module, same evaluation | "API handler bodies write by design" | "every definition kind"; "writes a definition is itself meant to perform ... must still happen" |
| trigger_and_view_conditions | B-ROUTE | M11 | doc/event.rs WHEN condition, doc/table.rs view condition (real, unfixed upstream) | condition shares Options with the action that must write | "not PERMISSIONS; the action must keep writing" | "any expression a definition stores"; coupled "writes a definition is itself meant to perform" |
| alter_definition_time | B-ROUTE | M5 | expr/statements/alter/{table,field,function,param,bucket}.rs store clauses without the DEFINE-time check | patch route to the same stored definition | "ALTER is not DEFINE; the runtime guard blocks the write" | "when an existing definition is replaced" |
| definition_time_nested_shapes | SHAPE TRAP | M8 | expression.rs/block.rs/ifelse.rs/foreach.rs: writes nested in IF/FOR/LET/RETURN or call args | shallow inspection of the stored expression | "top-level check looks sufficient; nested is runtime's job" | "directly contains a data-modifying statement"; "in a nested block" |
| schema_expression_siblings | INJ | M4 | doc/field.rs process_assert_clause / process_value_clause run with enforcement disabled | same disabled-enforcement evaluation in schema logic | "schema validation and derived values are not authorization" | "every definition kind that stores an expression" |

**Outcome:** gate SOUND (nop 18/18 security fail, oracle 3x 1.0, patches 12/12); fairness not stated. No DS or MiMo trials recorded; no per-test data. A dropped streaming-executor lever had no black-box observable and was removed.
**Read:** The best candidates for a different concept are trigger_and_view_conditions (the coupled Options object means a blanket guard breaks event actions) and the ASSERT/VALUE injection ("not authorization"). A central runtime guard on expression compute, which the published fix has, may still sweep the far permission sites together. The instruction's broad wording ("every definition kind") is fair, and the siblings are realistic.

### theia-ds
**Host / advisory:** eclipse-theia/theia, GHSA-3JWW-HXQJ-WFQ2 / CVE-2026-44688, workspace trust (CWE not given in the bundle; the host ledger says untrusted workspace config/content reaching AI), TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, 10-18) · **Pattern label:** A+B, track injected · **Traps:** 11
**Base bug:** The AI features ignore Restricted Mode: the activation service gates on the preference only, and workspace-scope AI settings and content are honoured in an untrusted workspace. The manifest's landing point is `ai-ide-activation-service.ts:41` plus the command wrapper. The observed example (auto-run tools) actually surfaces at T3, the tool-approval merge.
**Symptom as reported:** "The assistant executed a tool without showing the confirmation we expected, because the repository's own workspace settings said that every tool may run automatically ... the same workspace was also able to influence other AI behaviour." Invariants: no AI execution, and LM requests refused "an error, no call to a provider, and no recorded session"; workspace/folder values of "any AI setting" must not count, an enumerated list (tool approval, agent settings, model-alias, request/thinking, shell allow/deny lists, provider model/endpoint/key/proxy); no workspace skills or templates; fail closed until trust resolves; runtime trust changes take effect. The Contracts even name `WorkspaceTrustService`, `canRun` and `onDidChangeCanRun`. Every trap has an explicit clause.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1_activation_and_command_wrapper | BASE | M11 | ai-ide-activation-service.ts + ai-core-frontend-module.ts wrapper: isActive vs canRun | landing; visibility vs execution split | "chat input already checks activation"; visible = executable | "Commands must remain visible ... but must not be enabled"; canRun contract |
| T2_language_model_request_gate | A-FAR | M3 | ai-core frontend-language-model-service.ts sendRequest gate | lower-level public API under the UI | "UI is disabled, so the service is unreachable" | "Language-model requests must be refused by the public request APIs" |
| T3_tool_approval_merge | A-FAR | M5 | ai-chat chat-tool-preference-bindings.ts: workspace/folder scopes in the preference merge | the reported example's mechanism | "ordinary preference merging; chat is off anyway" | "every tool may run automatically"; "wildcard entry, per-tool entries" |
| T4_agent_settings_loader | A-FAR | M5 | ai-core ai-settings-service.ts workspace agent settings | config loader | "read-only config, low impact" | "agent settings" |
| T5_alias_registry_loader | A-FAR | M5 | ai-core frontend-language-model-alias-registry.ts | second loader next to T4 | "easy to overlook next to the settings service" | "model-alias selections" |
| T6_workspace_templates | A-FAR | M5 | ai-ide template-preference-contribution.ts (async loader) | workspace content via config | "prompt augmentation is not execution"; async placement | "template directories, individual template files and additional template extensions" |
| T7_workspace_skills | B-ROUTE | M4 | ai-core skill-service.ts: hard-coded `.prompts/skills` dir + workspace skill dirs (real upstream) | uncovered content route | "docs say the workspace directory is always included" | "This covers skills" |
| T8_shell_permission_lists | B-ROUTE | M5 | ai-terminal shell-command-permission-service.ts allow/deny via PreferenceService.get (real upstream) | uncovered settings route | "confirmation UX; the user still confirms" | "shell-command allow and deny lists" |
| T9_provider_configuration | B-ROUTE | M5 | ai-anthropic anthropic-frontend-application-contribution.ts endpoints/models/key/proxy (real upstream) | uncovered settings route | "provider config looks user-level" | "provider model, endpoint, key and proxy configuration" |
| T10_injected_command_gate | INJ | M1 | ai-core ai-core-command-contribution.ts command enabled from preference-only flag | command outside the wrapper | "the wrapper covers every AI command" | "Commands ... must not be enabled" |
| T11_injected_provider_init | INJ | M1 | ai-copilot copilot-frontend-application-contribution.ts model init on isActive | provider start-up gated by the wrong flag | "registration is metadata; request path gated" | "agent and provider integrations must not start" |

**Outcome:** gate UNSOUND per the bundle's marker. The builder's notes say nop, oracle (3x) and patches (18/18) passed after a dind rerun; the reason for UNSOUND is not in the bundle. No DS or MiMo trials recorded; no per-test data.
**Read:** The sibling set is broad (11 sites in 6 packages), but it rests on one concept, "honour workspace trust", and the instruction enumerates every setting family, so a careful sweep closes the traps together. The instruction is heavily over-specified: it names the trust service and the canRun API. The UNSOUND status should be resolved before this task counts.

### tinacms-ds
**Host / advisory:** tinacms/tinacms, GHSA-8MQ9-5FW2-5RM4 / CVE-2026-59992, CWE-639 (object-key path traversal), TypeScript · **Built by:** DeepSeek-built pilot (build-v1 template, 10-18) · **Pattern label:** A, track injected · **Traps:** 6
**Base bug:** Each media adapter passes a caller-supplied object key or directory to the storage SDK without confining it to the media root. The report leads to the S3 adapter's presigned-upload `?key=` in `packages/next-tinacms-s3/src/handlers.ts:68`.
**Symptom as reported:** "The API returns a working upload URL for that key ... The same unchecked value is used by the delete and listing operations, and by the other storage backends the project ships." Invariants: "No caller-supplied object key, directory, file name, list of keys, or pair of keys used together may cause a read, write, copy, move, delete, presigned write URL or listing outside the media area"; "every storage backend ... including backends that have no configured root"; every input shape (single, list, split route segments, multipart). The invariant names every sibling class (list, pair, copy, no-root backends).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M1 | next-tinacms-s3 handlers.ts upload ?key= plus same handler's delete and list branches | reported site + sibling branches | delete/list branches look unrelated to the upload symptom | "upload URL for a key"; "used by the delete and listing operations" |
| T2 | A-FAR | M2 | next-tinacms-dos handlers.ts upload/delete/list | S3-compatible second adapter | "reads like a copy, not the reported handler" | "the other storage backends the project ships" |
| T3 | A-FAR | M2+M4 | next-tinacms-azure and next-tinacms-cloudinary handlers.ts (no media-root option) | adapters without a root | "no root, so no boundary to escape" | "including backends that have no configured root" |
| I1 | INJ | M1 | next-tinacms-s3 batch-delete.ts DELETE ?keys= (array) | separate multi-select route | fix on single delete never reaches it | "list of keys" |
| I2 | INJ | M2 | next-tinacms-s3 app-handlers.ts app-router GET/POST/DELETE | parallel router module duplicating handlers | "pages-router handler is the reported one" | "every operation the media API exposes" |
| I3 | INJ | M1 | next-tinacms-dos copy-handler.ts POST ?from=&to= | different operation (copy/move) | "copy is neither upload nor delete" | "pair of keys used together"; "copy, move" |

**Outcome:** gate UNSOUND per the bundle's marker. The builder's notes say nop (0/73 security), oracle 3x and patches 12/12 passed; the reason for UNSOUND is not in the bundle. No DS or MiMo trials recorded; no per-test data.
**Read:** All six traps are routes or implementations of one "confine key to root" concept, and the invariant names each class (list, pair, copy, no-root backend). One shared resolveKey helper applied everywhere closes them together, so the traps are unlikely to bite. The injected siblings are realistic parity features.

### traefik-header-name
**Host / advisory:** traefik/traefik, GHSA-X677-9FXG-V5C5 / CVE-2026-54763 / GO-2026-6211, CWE-178/290/345, Go · **Built by:** Opus build-v1 template, batch 1 (10-17) · **Pattern label:** B (mined, no injection) · **Traps:** 6
**Base bug:** Middlewares that set or delete a managed request header remove only its canonical spelling, so a client's `X_Auth_User` reaches a backend that folds case and `_`/`-`. The report leads to basic auth's `headerField` (`pkg/middlewares/auth/basic_auth.go:106-110`). The published fix only adds an opt-in entry-point `underscoreHeadersStrategy` and leaves the middlewares untouched.
**Symptom as reported:** Basic auth sets `X-Auth-User: alice`, but the client's `X_Auth_User: admin` is forwarded and PHP reads it as the user. Invariants: "Whenever Traefik sets, replaces or removes a request header ... no header sent by the client may reach the backend under a name that differs ... only in letter case or in `_` versus `-`. This applies whichever feature or configuration manages the header, and with every entry-point setting, including the default"; plus the full keep/delete/reject option contract. Every trap is covered; T5 (client-certificate headers) was added after FAIRNESS review R1.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | B-ROUTE | M2 | auth/digest_auth.go headerField deletes only the canonical name (real upstream) | same logic in a sibling auth scheme | "report shows basic auth; digest is rare" | "whichever feature ... manages the header" |
| T2 | B-ROUTE | M1 | auth/forward.go authResponseHeaders list + regex (real upstream) | copied auth-service headers | upstream comment leaves spellings to the entry-point option | "whichever feature or configuration manages the header" |
| T3 | B-ROUTE | M1 | headers/header.go customRequestHeaders set/remove (real upstream) | generic header rewrite, other package | "not an authentication feature" | "sets, replaces or removes a request header" |
| T4 | A-FAR | M11 | config/static/entrypoints.go + server/server_entrypoint_tcp.go option (published fix, named in instruction) | published fix; default must stay keep | none (named); coupling with T1-T3 under default | option contract; "including the default" |
| T5 | B-ROUTE | M1 | passtlsclientcert/pass_tls_client_cert.go cert headers (real upstream) | header set from TLS layer | "value comes from TLS, other package" | "sets ... a request header ... whichever feature" |
| S1 | SHAPE TRAP | M12 | mixed spellings X_Auth-User / X-Auth_User, lower-case configured name, across all routes | input variants | example is the all-underscore spelling | "differs ... only in letter case or in `_` versus `-`" |

**Outcome:** gate_report passed=True; fairness NOT READY. Raw DS 1.0, MiMo 1.0. The per-trial data shows two runs per model (295 tests on 10-17, 329 tests after the T5 revision on 10-18), all 1.0 with 0 failing. Neither model missed a sibling. Per traefik-ds notes, DS solved run 1 in 24 min and MiMo in 106 min.
**Read:** Every sibling is another `Header.Del`/`Set` site under one stated rule. The instruction gives the general rule plainly, so both models swept all the sites with one normaliser. The upstream design choice (opt-in only) differs from the task's invariant, but the instruction states the stronger rule explicitly.

### traefik-ds
**Host / advisory:** traefik/traefik, GHSA-X677-9FXG-V5C5 / CVE-2026-54763 / GO-2026-6211, CWE-178/290/345, Go · **Built by:** DeepSeek-built pilot (build-v1 template, 10-19) · **Pattern label:** B, with injected siblings · **Traps:** 10
**Base bug:** Same as traefik-header-name: middlewares that set or strip a managed header remove only the canonical spelling. The landing is basic auth `headerField` (`pkg/middlewares/auth/basic_auth.go:106-111`).
**Symptom as reported:** The same `X_Auth_User: admin` example and the same general rule ("whichever feature does it, and with every entry-point setting, including the default"). This build adds a new invariant: "When the headers to manage are selected by an operator-configured pattern ... a pattern written with dashes and a pattern written with underscores select the same names." Must-keep-working now includes "request-header filtering". Every trap is covered. S1 (the trusted-headers filter) falls under "whichever feature does it".

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| P | A-FAR | M11 | config/static/entrypoints.go + server_entrypoint_tcp.go option (published fix, named in instruction) | default keep must coexist with closed routes | none (named) | option contract |
| U1 | BASE | M8 | auth/basic_auth.go headerField deletes only the canonical spelling | landing/trigger | none | the X_Auth_User example |
| U2 | B-ROUTE | M2 | auth/digest_auth.go headerField (real upstream) | same logic, sibling scheme | "digest is rare" | "whichever feature does it" |
| U3 | B-ROUTE | M1 | auth/forward.go authResponseHeaders list, incl. underscore-configured name (real route + injected helper) | copied auth-service headers | "a case-only alias filter is already here" | "whichever feature does it" |
| U4 | B-ROUTE | M8 | auth/forward.go authResponseHeadersRegex: pattern with dashes vs underscores | regex selection by canonical key only | "the operator chose the pattern" | the new pattern invariant |
| U5 | B-ROUTE | M1 | headers/header.go customRequestHeaders set/remove incl. underscore-configured name, XFF nil-slice branch | other package | "not an authentication feature" | "sets, replaces or removes a request header" |
| U6 | B-ROUTE | M1 | passtlsclientcert/pass_tls_client_cert.go cert headers | TLS-derived headers | "value comes from TLS" | "whichever feature does it" |
| S1 | INJ | M2 | new pkg/middlewares/trustedheaders (filter loop over a canonical set, case-only) + factory branch | second strip implementation, different idiom | "a trusted-proxy passthrough that already filters the names" | "removes a request header ... whichever feature" |
| S2 | INJ | M8 | auth/forward.go removeHeaderVariants: case-only (EqualFold) partial defence | half-right helper on U3's route | "an alias-aware helper is already present" | "`_` versus `-`" |
| S3 | SHAPE TRAP | M12 | configured names with underscores/lower case, mixed client spellings, underscore pattern | input variants across routes | "one-way normalisation looks enough" | "differs ... only in letter case or `_` versus `-`"; pattern clause |

This build keeps traefik-header-name's routes (digest, forward list/regex, custom headers, client-certificate, entry-point option). It adds a basic-auth row, an injected trusted-headers middleware with a different idiom, an injected case-only partial defence, and configured-spelling and pattern shapes, because both models solved the earlier variant in run 1.
**Outcome:** no gate marker. Notes say nop (82 security fail, 280 functional pass), oracle 3x 1.0 and patches 21/21 passed. The notes give oracle security as 92/92 but nop as 82, which is a count discrepancy. No DS or MiMo trials recorded; no per-test data.
**Read:** S1 (a different filter idiom) and S2 (a defence that looks finished) are the only genuinely new mechanisms. A full normaliser sweep that also inspects existing helpers would still close everything. The pattern rule is now stated outright, so U4 is fair but signposted. The new difficulty is modest compared with a variant that both models already solved.

### trivy-path-traversal-inj
**Host / advisory:** aquasecurity/trivy, GHSA-8RC5-4FR6-64PW / CVE-2026-63328 / GO-2026-6250, CWE-22, Go · **Built by:** Opus build-v1 template, injected track (10-18) · **Pattern label:** A+B (manifest), track injected · **Traps:** 4
**Base bug:** A plugin name from packaged metadata is joined onto the plugin root to form the install destination, which is cleared and written with no confinement (`pkg/plugin/manager.go:129-139`, `Manager.install`).
**Symptom as reported:** "Installing a plugin whose packaged metadata declares a hostile name causes Trivy to create and overwrite files ... outside the plugins directory ... the same class of crafted name can also cause files or directories outside the plugins directory to be removed or newly created." Invariants: no plugin name may escape "for every source a name can come from — a plugin's packaged metadata, a value supplied on the command line, metadata already stored on disk from an earlier install, or an entry in the plugin index — and for every plugin management operation, whether it installs, removes, reads, re-reads or prepares a cache". The system description even lists the injected operations ("re-read an already-installed plugin, or prepare a cache for one listed in the plugin index"). Every trap is covered, explicitly.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base_install | BASE | M8 | manager.go loadMetadata/install: '..' name joined onto the plugin root | reported write/clear sink | none | the `trivy plugin install` example |
| far_uninstall | A-FAR | M1 | manager.go Uninstall joins the CLI name and RemoveAll's it | other command, same join | "CLI arg is the user's own input" | "a value supplied on the command line"; "removed" |
| sibling_reload | INJ | M5 | injected Manager.Refresh writes via the stored-name-derived dir (derivation is real pinned code) | stored-object route to the same join | "metadata written by Trivy itself is trusted" | "metadata already stored on disk"; "re-reads" |
| sibling_prefetch | INJ | M1 | injected Manager.Prefetch creates a cache dir from an index-entry name | another operation, same join | "curated index is trusted; only a cache dir" | "an entry in the plugin index"; "prepares a cache" |

**Outcome:** gate_report passed=False; fairness NOT READY. The builder's notes say nop, oracle and patches passed after a test-filter fix; the reason for the False is not in the bundle. Raw DS 1.0, MiMo 1.0, 0 failing tests each. No sibling missed.
**Read:** All four traps are one concept (confine every name join), and the instruction enumerates every name source and operation, including the injected ones, so one IsLocal helper closes all of them. It is a checklist with no lever.

### trivy-ds
**Host / advisory:** aquasecurity/trivy, GHSA-8RC5-4FR6-64PW / CVE-2026-63328 / GO-2026-6250, CWE-22, Go · **Built by:** DeepSeek-built pilot (build-v1 template, 10-19) · **Pattern label:** A, injected siblings · **Traps:** 5
**Base bug:** Same as trivy-path-traversal-inj: a packaged-metadata plugin name (`../escaped_plugin`) joined onto the plugin directory forms the install destination, which is cleared and written (`pkg/plugin/manager.go:137,142`).
**Symptom as reported:** "Installing a plugin whose packaged metadata declares the name `../escaped_plugin` creates a plugin directory above the plugin directory and deletes whatever was already stored there." Invariants: no name "however Trivy obtained it, and whichever plugin management operation uses it" may cause anything outside "to be created, written, removed, read or executed"; "A name that leaves the plugin directory only after its path is interpreted, including one that goes through a link that already exists inside the plugin directory, is covered as well." Every trap is covered. Unlike the earlier variant, the injected operations are not named.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| base_install | BASE | M8 | manager.go install destination + metadata write; shapes `../x`, `missing/../../x`, `../plugins_evil` (prefix sibling) | reported sink | none | the `../escaped_plugin` example |
| symlink_install | SHAPE TRAP | M8 | name `link/sub` through an existing symlink in the plugin dir (manager.go + downloader RemoveAll) | lexical check passes, resolved path escapes | "a link in the user's own dir is local tampering"; IsLocal passes | "goes through a link that already exists inside the plugin directory" |
| far_cli_name | A-FAR | M1 | manager.go Uninstall and load (Information), incl. bare `..` | other commands, same join | "CLI arg is the user's own input; reading is intended" | "however Trivy obtained it"; "removed, read" |
| stored_name_dir | A-FAR | M5 | manager.go loadMetadata derives dir from the stored name -> Start exec (plugin.go:69) + injected Repair | stored-object route; exec sink | "stored metadata written by Trivy is trusted" | "read or executed"; "however Trivy obtained it" |
| sibling_index_cache | INJ | M1 | injected index.go Update loop creates per-plugin cache dirs from index entry names | another operation, same join | "curated feed; only primes a cache" | "whichever plugin management operation uses it" |

Compared with trivy-path-traversal-inj, this variant keeps the base, uninstall and stored-name siblings. It adds a symlink shape, the Information read and Start-exec sinks, and prefix/bare-`..` shapes, swaps the injected Refresh/Prefetch for Repair and an index cache, and removes the instruction text that named the injected operations.
**Outcome:** gate UNSOUND per the bundle's marker. The notes say nop, oracle 3x and patches 12/12 passed; the reason for UNSOUND is not in the bundle. No DS or MiMo trials recorded; no per-test data.
**Read:** symlink_install (resolved versus lexical containment) and the exec sink through the stored name are the only parts that go beyond "IsLocal every join". The symlink case is the likeliest to bite, because a plain IsLocal fix passes it. The rest is the same concept the models already solved in the earlier variant.

### typo3-ds
**Host / advisory:** typo3/typo3 (TYPO3 CMS form framework), GHSA-JH32-V29G-68PQ / CVE-2026-49741, CWE-862 leading to CWE-89 (save-to-database finisher), PHP 8.2 · **Built by:** DeepSeek-built (model-driven pilot, build-v1 template), 10-19 · **Pattern label:** A (track none in bundle; notes describe A + B + injected) · **Traps:** 5
**Base bug:** stored form definitions (DB table) can be written by any backend user with table-modify permission through the generic core record API (DataHandler), bypassing the form editor's validation and permission checks, so arbitrary finisher options (e.g. save-to-database into any table) execute on submit. The report leads to "ordinary record editing" of the forms table.
**Symptom as reported:** "can save a form definition straight through the ordinary record editing interface. Nothing validates or authorises that definition". Invariants: "No other operation may create, change, remove or re-activate a definition — whatever the operation is called, whichever fields it carries, and whoever invokes it"; "a command exits non-zero"; "including operations that carry no configuration field at all and paths that were not mentioned here". Every trap is covered, most of them almost by name (re-activate, no configuration field, command).

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M1 | Nothing planted; record API create (NEW id, full field set), core DataHandler.php:708 vs form FormDefinitionRepository.php:180 | The reported route itself, but the guard must sit on core code in another package | Table looks UI-protected (read-only fields, no New Record wizard); generic core code, so harden only the editor | "straight through the ordinary record editing interface"; "No other operation may create" |
| T2 | A-FAR | M12 | Nothing planted; record command soft delete, DataHandler.php:3233-3241 | Another verb on the same record API | "Removal writes no configuration, so the injection impact does not apply" | "create, change, remove or re-activate"; "whatever the operation is called" |
| T3 | SHAPE TRAP | M12 | Nothing planted; partial update (integer uid, label only), DataHandler.php:708 | Input-shape variant of the update route | A fix that inspects only the configuration field misses ordinary partial saves | "including operations that carry no configuration field at all"; "whichever fields it carries" |
| T4 | B-ROUTE | M12+M11 | Upstream undelete command (DataHandler.php:3303-3305), which the published hook ignores; INJECTED `form:definition:restore` command as its legitimate user | Re-activation verb on the record API, coupled to a legitimate restore that uses the same command | "Restoring writes no configuration"; blocking the command outright breaks the product's restore tool | "or made active again"; "restoring a definition that this path itself removed" must keep working |
| T5 | INJ | M2 | Administrative import (FormTransferService.php:171 + new ImportFormDefinitionsCommand.php:67) inserting definitions through a raw DB connection, nested and serialized configuration | A second persistence implementation that bypasses the form framework and the record API | CLI runs as an administrator and is outside the advisory | "whoever invokes it"; "a command exits non-zero"; "paths that were not mentioned here" |

**Outcome:** gate SOUND (nop 7/7 sec fail, oracle 3/3 at 1.0, patches 14/14; static fails only on blind/FAIRNESS). No fairness review. No DS or MiMo trials. Missed traps: no data.
**Read:** T1-T4 are one concept (guard every DataHandler write and command on the table). A generic DataHandler hook catches them together, except that T4 needs the restore exemption. T5 is a genuinely different second implementation (raw connection), but the instruction signposts all five almost explicitly ("re-activate", "no configuration field", "command exits non-zero"), so it is unlikely to bite. Coupling the injected restore command to the real undelete route is the most interesting part.

### vibe-trading-path-read
**Host / advisory:** hkuds/vibe-trading, GHSA-5RMQ-CHC7-M22F, CWE-22, Python · **Built by:** Opus build-v1 template, batch 1 (10-17) · **Pattern label:** A+B · **Traps:** 7
**Base bug:** agent tools take file and directory paths from the model's tool call with no confinement. The report leads to the document reader (`doc_reader_tool.py:270`), which reads any path, e.g. /root/.ssh/id_rsa.
**Symptom as reported:** "A user who sends a chat message such as 'Read the document /root/.ssh/id_rsa…' gets the server's private key back." Invariants: "No argument of any agent tool that names a file or a directory … may make the tool read, list, run, create or change anything outside the areas above, whatever the path's spelling or wherever it ultimately resolves"; "A directory a tool is told to work in or write into must be inside run storage." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Nothing planted; document reader with no check (doc_reader_tool.py:270); absolute, cwd-relative and `..` spellings | Landing site | n/a | The example itself; "whatever the path's spelling" |
| T2 | A-FAR | M2 | Nothing planted; shared broker-file validator with a HOME∪CWD envelope (path_utils.py:52-81) used by the trade-journal and shadow-account tools | Second implementation of the path check, too wide | Already calls a dedicated validator whose docstring says broker exports live anywhere in HOME | "No argument of any agent tool"; operator-configured areas only |
| T3 | A-FAR | M6 | Nothing planted; read/write/edit_file trust the model's run_dir; producer loop.py:240-262 passes absolute values through and resolves relative ones | Confinement relative to a root the attacker supplies; the check must sit after the mapper | Paths are already confined to the workspace root, and the root looks system-supplied | "A directory a tool is told to work in … must be inside run storage" |
| T4 | A-FAR | M1 | Nothing planted; pattern_tool.py:316 and backtest_tool.py:21 take run_dir unchecked | Other tools reaching file sinks | "Chart analysis and engine runner, not file readers" | "read, list, run, create or change"; "work in" |
| T5 | B-ROUTE | M1 | Nothing planted; factor_analysis_tool.py:113-118 reads caller CSVs and creates the caller's output_dir (unchanged upstream) | Uncovered tool route to the same sink | Returns only aggregate statistics, so it does not look like a file reader | "any agent tool"; "a place to write output" |
| T6 | SHAPE TRAP | M8 | path_utils: symlink inside the upload area pointing out | Resolved vs lexical containment | A normalised-string prefix check looks sufficient | "wherever it ultimately resolves" |
| T7 | SHAPE TRAP | M8 | path_utils: a directory whose name starts with a configured root's or run storage's name | String prefix vs path component | Prefix match looks equivalent | "whatever the path's spelling" |

**Outcome:** gate passed; fairness NOT READY (a fairfix revision was applied afterwards; not re-reviewed). DS 0.0 then 1.0; MiMo 1.0. DS r1 failed only the functional test `test_read_file_bundled_skill_docs` (T3's coupled check), so its fix was over-broad (it blocked reading the skill docs) and missed no sibling. No trap was missed.
**Read:** T1-T5 are routes and variants of one accepted concept ("confine every tool path argument"). The instruction makes models enumerate the tools, and both solved it. T6/T7 are standard path-confinement expertise. Nothing here is a different concept.

### vibe-trading-ds
**Host / advisory:** hkuds/vibe-trading, GHSA-5RMQ-CHC7-M22F, CWE-22/23/552, Python · **Built by:** DeepSeek-built (model-driven pilot, build-v1 template; a rebuild of vibe-trading-path-read), 10-18/19 · **Pattern label:** A+B (+ injected) · **Traps:** 10
**Base bug:** same as vibe-trading-path-read. Tool and API path values are not confined; the landing site is the document reader (`doc_reader_tool.py:270`).
**Symptom as reported:** same key example, plus "the same location can be asked for as a document to display in the browser". Invariant: "No caller-supplied value that names a file or a directory may make the service read, list, serve, run, create or change anything outside the areas … whether the value arrives as a tool argument, as a request parameter, or as a location recorded in a run's own data"; must-keep-working lines name "a run's configuration pointing at a data file" and "a skill's supporting files by the names they have inside that skill's own directory". Every injected sibling has a covering clause, and each is close to named.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M12 | Nothing planted; doc_reader_tool.py:270; absolute, cwd-relative, `..`, symlink and configured-root-sibling spellings | Landing site | n/a | The example; "whatever the path's spelling" |
| T2 | A-FAR | M2 | Nothing planted; shared broker-file validator with a HOME+CWD envelope (path_utils.py:52) via the trade-journal and shadow tools | Second, too-wide validator | Docstring says broker exports live anywhere in HOME | "No caller-supplied value" |
| T3 | A-FAR | M6 | Nothing planted; read/write/edit_file trust run_dir; producer loop.py:240-262 | Root supplied by the caller through the mapper | Workspace root looks system-supplied | "A directory a tool is told to work in … must be inside run storage" |
| T4 | A-FAR | M1 | Nothing planted; pattern_tool.py:316 and backtest_tool.py:23 take run_dir | Other tools | "Analysis and engine tools, not file readers" | "read, list, serve, run" |
| T5 | B-ROUTE | M1 | Nothing planted; factor_analysis_tool.py:113-118 CSV inputs and output_dir | Uncovered upstream tool route | Returns only aggregates | "any caller-supplied value"; "write into" |
| T6 | SHAPE TRAP | M8 | path_utils: symlink in the upload area | Resolved vs lexical | Prefix check looks sufficient | "wherever it ultimately resolves" |
| T7 | SHAPE TRAP | M8 | path_utils: name-prefix sibling of a configured root or run storage | Component-wise containment | Prefix match looks equivalent | "whatever the path's spelling" |
| T8 | INJ | M1 | New HTTP stored-document preview route serving a caller path (api_server.py:1402) | Same sink through an HTTP route instead of an agent tool | "It is an HTTP read route, not an agent tool" | "as a request parameter"; "a refused HTTP request is a client error"; "display in the browser" |
| T9 | INJ | M5 | Backtest reads and previews a local data file named inside the run's config.json (backtest_tool.py:49-63) | Path arrives as stored data inside a confined workspace | "The workspace is already confined, so data inside it is trusted" | "as a location recorded in a run's own data"; "a run's configuration pointing at a data file" |
| T10 | INJ | M10 | load_skill gains a supporting-file name joined onto the skill directory without containment (skills.py:47 + load_skill_tool.py) | The skill name is validated, but the file joined to it is not | "Skill loading is legitimate and the skill list is validated" | "a skill's supporting files by the names they have inside that skill's own directory" |

**Outcome:** no gate marker (notes: nop 25/25 sec fail, oracle 3/3 at 1.0, patches 20/20; static fails only on blind/FAIRNESS). No fairness review. No DS or MiMo trials. Missed traps: no data.
**Read:** T1-T7 are the same set that both models solved in vibe-trading-path-read. T8-T10 move the sink onto non-tool surfaces (HTTP route, run data, a validated-parent join), which is a real step toward different concepts (M5, M10). However, the instruction names each surface ("request parameter", "location recorded in a run's own data", "skill's supporting files"), so they are signposted rather than hidden. **Compared with vibe-trading-path-read:** it keeps T1-T7 unchanged and adds three injected siblings on other surfaces, but the broadened instruction points to each one, so the extra difficulty is probably small.

### vitest-api-fs-authz-inj
**Host / advisory:** vitest-dev/vitest, GHSA-5XRQ-8626-4RWP / CVE-2026-47429, CWE-862 / CWE-22, TypeScript · **Built by:** Opus build-v1 template, injected track, 10-18 · **Pattern label:** A+B (realized: A + 2 injected) · **Traps:** 4
**Base bug:** the test-runner control server (UI API WebSocket RPC) accepts write and exec operations (saveTestFile, rerun/rerunTask, updateSnapshot) from any token holder when it is bound to a network address. The token is embedded in the served page. The report leads to the UI API's file save.
**Symptom as reported:** "a client that holds the token sends a single request naming one of the project's test files and new contents, and the file on disk is overwritten … can also make the runner execute test code. This is one example". Invariant: "no request from a client may create, modify, or delete any file on disk, and no request may cause test code to run — whichever of the server's operations is used, through whichever interface, and whichever target". The browser-mode driver is named as a client of "the control server". Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| BASE | BASE | M4 | Nothing planted; packages/vitest/src/api/setup.ts saveTestFile (write), rerun/rerunTask/updateSnapshot (exec) | Reported site; write and exec halves | n/a | The example (overwrite + execute) |
| A-FAR | A-FAR | M2 | Nothing planted; packages/browser/src/node/commands/fs.ts writeFile/removeFile (@vitest/browser) | Same missing write gate in a second implementation in another package | "Browser-test server; writes are the user's own test code; gating looks like breaking browser tests" | "through whichever interface"; "the browser-mode test driver use[s] it" |
| S-CMD | INJ | M1 | Added `appendFile` browser command (fs.ts:51 + commands/index.ts registration) with the pre-fix pattern | Extra command next to A-FAR | "Convenience append helper, not the create/delete pair" | "create, modify, or delete any file"; "whichever of the server's operations" |
| S-UI | INJ | M1 | Added UI handler `saveSnapshotFile` (setup.ts + api/types.ts), gated only by registered-file membership | Extra write handler next to BASE | "Writes only the snapshot of an already-registered test file" | "whichever of the server's operations"; "write snapshots" (local-only) |

**Outcome:** gate_report passed=False (blind patch missing); fairness NOT READY, fairfixed 10-18 and not re-reviewed. The six pre-fairfix runs (DS ×3, MiMo ×3) all scored 0.5714, failing exactly the 3 browser_commands security tests. FAIRNESS.md attributes this to a harness artifact (a synthetic project with no host). Post-fairfix: DS 0.625 ×3 and MiMo 1.0, 1.0, 0.625. **Per-test map (DS, all 3 post-fairfix runs, identical):** DS failed `creating a file does not take effect` and `removing a file does not delete it` (A-FAR) and `appending to a file does not change it` (S-CMD). It passed all 4 BASE tests and the S-UI test, so its score was 5/8 security with functional green. MiMo r3 failed the same 3 tests. **Caution:** this 3-test signature matches the pre-fairfix artifact exactly. The post-fairfix harness still calls the exported command functions directly (aliased source) rather than the browser RPC dispatcher. vitest-ds/notes.md records that "reviewing the earlier trial patches showed a model gating the real browser RPC dispatcher (`triggerCommand`) — a legitimate fix — which those tests rejected". DS then scored 1.0 on vitest-ds, whose harness drives `triggerCommand`. No trial diffs were available here to say which model's patch that was.
**Read:** DS's misses form one unit: the whole browser-mode package (A-FAR + S-CMD). That is a second-implementation miss, not a miss of the injected sibling as such; DS caught the injected UI sibling. The evidence points strongly to a test-layer artifact (a gate at `triggerCommand` is rejected), so this DS-only breaker lead is probably false until DS's patches are checked.

### vitest-ds
**Host / advisory:** vitest-dev/vitest, GHSA-5XRQ-8626-4RWP / CVE-2026-47429, CWE-862 / CWE-22, TypeScript · **Built by:** DeepSeek-built (model-driven pilot, build-v1 template; started from the vitest-api-fs-authz-inj artifact), 10-18 · **Pattern label:** A+B · **Traps:** 6
**Base bug:** same as vitest-api-fs-authz-inj, plus the advisory's CWE-22 half: browser write commands escape the project root when Vite's `server.fs.strict` is off.
**Symptom as reported:** the same example and authorization invariant, plus: "No request may create, modify, or delete a file outside the project's root directory. This holds even when the project is configured to serve files from outside its root, and even when the server is reachable only from the local machine." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| BASE | BASE | M4 | Nothing planted; api/setup.ts saveTestFile, rerun/rerunTask, updateSnapshot | Reported site | n/a | The example |
| A-FAR | A-FAR | M2 | Nothing planted; browser commands/fs.ts writeFile/removeFile, now reached via the real browser-API WebSocket `triggerCommand` | Second implementation in another package | "Browser tests' own writes" | "through whichever interface" |
| S-CMD | INJ | M1 | Added `appendFile` command (fs.ts + commands/index.ts) | Extra command next to A-FAR | "Convenience helper" | "whichever of the server's operations" |
| S-UI | INJ | M1 | Added UI `saveSnapshotFile` (setup.ts + types.ts), registered-file gate only | Extra handler next to BASE | "Scoped to registered files" | "whichever of the server's operations" |
| A-SNAP | A-FAR | M1 | Nothing planted; browser rpc.ts saveSnapshotFile (:194) / removeSnapshotFile (:200) | Other write handlers on the browser API | "Snapshot files are run artifacts, part of the trusted test protocol" | "create, modify, or delete any file"; "whichever interface" |
| PATH | B-ROUTE | M9 | Nothing planted; fs.ts `assertFileAccess` serving check returns true when `fs.strict` is false (both Vite helpers do), so writes and removes reach outside the root | The CWE-22 half; the published change (helper swap) does not close it in vite 7.1.5 | "The code already runs Vite's serving check before every write" | "even when the project is configured to serve files from outside its root, and even when … local" |

**Outcome:** gate SOUND (nop 0/13 sec, oracle 3/3 at 1.0; patches stage partly cut by infrastructure, with all 16 checks verified locally). No fairness review. DS 1.0 (24 tests, 0 failing). MiMo run produced no result (reward NA, 0 tests). Missed traps: none for DS; MiMo no data.
**Read:** A-SNAP is one more route of the accepted "gate every browser-API write" concept. PATH is a genuinely different concept (fail-open confinement), but the instruction spells out its exact trigger ("even when … serve files from outside its root"). DS solved it. **Compared with vitest-api-fs-authz-inj:** it keeps all four traps, adds A-SNAP and PATH, and drives the browser API through the real `triggerCommand`, which fixes the layer artifact. DS's 1.0 here supports the view that its 0.625 on the earlier variant was a test artifact.

### vitest-mm
**Host / advisory:** vitest-dev/vitest, GHSA-5XRQ-8626-4RWP / CVE-2026-47429, CWE-862 / CWE-22, TypeScript · **Built by:** MiMo-built (model-driven pilot, build-v1 template), 10-18 · **Pattern label:** A+B · **Traps:** 7
**Base bug:** same UI control-server write/exec authorization gap (setup.ts), plus the confinement half: reads and writes outside the project when `server.fs.strict` is false.
**Symptom as reported:** the overwrite and execute example, plus "Separately, a request named a path outside the project and the runner read or wrote that path … even when the project had relaxed the usual file-serving restriction". It also says "The same server also exchanges test evidence with the UI over HTTP". Invariants: Authorization ("whichever of the server's operations … through whichever interface") and Confinement ("No request from a client may read or write a file outside the project's files — whichever operation, whichever interface, and whatever file-serving settings"). Every trap is covered; A3 only through must-keep-working (it is unnamed: "reachable only from the local machine").

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| A1 | BASE | M4 | Nothing planted; api/setup.ts saveTestFile, rerun/rerunTask, updateSnapshot | Reported site | n/a | The example |
| A2 | A-FAR | M2 | Nothing planted; browser commands/fs.ts writeFile/removeFile | Second implementation | "Browser tests' own writes" | "through whichever interface" |
| A3 | A-FAR | M5 | resolveConfig.ts resolveApiServerConfig: the local-vs-exposed decision across host spellings, `api` as number vs object, and browser.api inherit vs own (no standalone test; enforced through shape variants inside A1/A2 tests) | Producer of the exposure decision | "Config plumbing, not a request handler" | "reachable only from the local machine … keeps working"; variants unstated |
| B1 | B-ROUTE | M9 | Nothing planted; browser plugin.ts GET `/__vitest_attachment__` returns any path when fs.strict is false | Uncovered read route; the serving check fails open | "Read-only helper; the report is about write/exec" | "read or write a file outside the project's files … whatever file-serving settings" |
| B2 | B-ROUTE | M9 | Nothing planted; fs.ts writeFile path check fails open under fs.strict=false (the helper migration is a no-op) | Write form of the same confinement hole | "The serving check is the documented Vite API; migrating it is the fix" | Same Confinement clause; "Writing a file that is inside the project must keep working whatever file-serving settings" |
| S1 | INJ | M1 | New commands/artifacts.ts `exportArtifact` (+ index.ts registration) copying the pre-fix writeFile shape | Extra browser write command | "Test-evidence export, not the file API" | "whichever operation"; "test evidence" |
| S2 | INJ | M1 | New `POST /__vitest_attachment__` in packages/ui/node/index.ts (HTTP write beside the GET read-back) | Write over a different interface (HTTP middleware) | "Upload helper next to a read, not the control API" | "exchanges test evidence with the UI over HTTP"; "whichever interface" |

**Outcome:** no gate marker (notes: nop 12/12 sec fail, oracle 3/3; patches stage partial: base_only, miss_far and miss_conf matched, the rest cut by an infrastructure flake). No fairness review. No DS or MiMo trials. Missed traps: no data.
**Read:** B1/B2 (fail-open confinement) are a genuinely different concept from authorization, but the instruction states them as a separate, explicit invariant. S2 is the most hidden sibling, and even it is hinted at ("test evidence … over HTTP"). Fairness risk: as in vitest-api-fs-authz-inj, the browser-command tests call the exported command functions directly, so a correct gate at the RPC dispatcher would fail A2/S1/B2. **Compared with vitest-ds:** it drops S-CMD, S-UI and the browser-RPC snapshot handlers, and adds a read-form confinement route (B1), the config producer (A3) and two injected siblings on new surfaces. However, it keeps the direct-call harness that vitest-ds replaced with the real `triggerCommand` path.

### whistle-cwe-path
**Host / advisory:** avwo/whistle, GHSA-3VFR-4GWF-QXFP / CVE-2026-55629, CWE-22, Node.js · **Built by:** Opus build-v1 template, batch 1 (10-17), mined track · **Pattern label:** A+B (realized: A + coupled) · **Traps:** 2
**Base bug:** the forked internal service child serves any caller on its loopback port. `GET /cgi-bin/temp/get?filename=<abs path>` reads any host file, and no route checks the uid header the UI sends. The report leads to the file-read endpoint; the published fix is a credential gate over the whole service.
**Symptom as reported:** "a single HTTP GET … that asks for a file by its path comes back with that file's contents … Other data the component holds is exposed the same way". Invariants: "must act only on requests that prove they come from the tool itself … regardless of what the request asks for"; "honour that [existing identification] contract"; "including loading arbitrary files the operator selects, must keep working unchanged". Both traps are covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | A-FAR | M1+M4 | Nothing planted; a server-wide credential gate is needed in lib/service/service.js sessionsHandler (:308-312), covering temp/get, the list form, saved/list, history, temp/create and a wrong-valued header | The fix belongs above the reported endpoint; the other routes of the same unauthenticated server | "Loopback-only server fronted by the UI's guard needs no auth" | "Other data the component holds is exposed the same way"; "every operation the component exposes" |
| T2 | COUPLED TRAP | M11 | Nothing planted; service.js:458-467 authorized full-path read is a feature | Over-broad fix (confine to the temp dir) breaks it | The report is about reads outside storage, so "confine" is natural | "including loading arbitrary files the operator selects, must keep working" |

**Outcome:** gate passed; fairness NOT READY (fairfix revision applied 10-17). DS 1.0, 1.0; MiMo 1.0, 1.0 (11 then 13 tests, 0 failing). No trap was missed.
**Read:** one concept (authenticate the whole component) plus one coupled feature. Both models solved it. The pattern-B route (panel import-remote ahead of login) was not built here.

### whistle-ds
**Host / advisory:** avwo/whistle, GHSA-3VFR-4GWF-QXFP / CVE-2026-55629, CWE-22 (+ missing authentication), Node.js · **Built by:** DeepSeek-built (model-driven pilot, build-v1 template), 10-18 · **Pattern label:** A+B (+ injected) · **Traps:** 4
**Base bug:** the data component authenticates nothing (as in whistle-cwe-path). In addition, panel routes registered before the panel's login middleware forward caller-supplied paths to the component with the component's valid credential. The report leads to the panel's import feature with login configured.
**Symptom as reported:** "a single HTTP GET to the panel's import feature, asking it to load a file by a local path, returned that file's contents even though the request carried no login credentials." Invariants: "The background data component must act only on requests that prove they come from the tool itself"; "When panel login is configured, a request to the panel must not perform any operator action unless the caller has authenticated … whatever operation, parameter or value"; "A credential that is present but wrong must be treated exactly like one that is absent." Every trap is covered.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| T1 | BASE | M4 | Nothing planted; lib/service/service.js:303 sessionsHandler (all routes: temp/get single and list forms, create, saved/list, history, wrong credential); coupled full-path read for authorized callers | Published-fix site; the component never authenticated | "Loopback-only, fronted by the panel's guard" | First invariant; "present but wrong" |
| T2 | B-ROUTE | M1+M10 | Nothing planted; biz/webui/lib/index.js:414 `/cgi-bin/import-remote`, registered before the login middleware (:504), forwards to the component with its valid credential | The reported route; the panel acts as a proxy for an anonymous caller | "Looks like a remote-URL importer; the later login middleware looks global; the published fix is about the component" | The example itself; second invariant |
| S1 | INJ | M1+M10 | New panel download route (biz/webui/lib/index.js:440) forwarding a caller filename to the component's stored-item read, before login | Same proxy pattern on a new route | "A thin alias; a component fix looks like it covers it" | "whatever operation, parameter or value" |
| S2 | INJ | M10 | New composer local-body route (biz/webui/lib/index.js:447) behind a client-supplied Host (loopback) check, before login | Same proxy, with its own weak access check | "Already has its own access check" (which trusts the Host header) | "must not perform any operator action unless the caller has authenticated" |

**Outcome:** gate SOUND (nop 13/13 sec fail, oracle 3/3, patches 11/11). No fairness review. DS 1.0. MiMo 0.0 then 1.0. MiMo r1 failed all 6 `functional-component` tests and no security test. That fits a changed or over-broad credential contract (authorized component calls refused), not a missed sibling. No trap was missed.
**Read:** the panel-side traps (T2/S1/S2) are a genuinely different concept from the component gate: confused-deputy forwarding plus route ordering against login. However, the report leads straight to T2, and S1/S2 are the same pattern a few lines away, so models fix them together. **Compared with whistle-cwe-path:** it keeps that build's component gate (now BASE, with the full-path read as a functional check) and adds the panel layer: the real import-remote route the earlier build could not test, plus two injected panel routes. It is a broader task, but both models still solved it.

### yamcs-ds
**Host / advisory:** yamcs/yamcs, GHSA-FWWW-CP23-7F5G / CVE-2026-55545, CWE-862, Java 17 · **Built by:** DeepSeek-built (model-driven pilot, build-v1 template), 10-19 · **Pattern label:** B (+ injected) · **Traps:** 8
**Base bug:** WebSocket subscription handlers skip the privilege checks that the matching REST reads apply. The live packet subscription for a processor streams every packet regardless of ReadPacket. The report leads to the processor packet feed (`PacketsApi.java:499-527`).
**Symptom as reported:** "An account whose role grants read access to one family of telemetry packets … received every packet that processor produced … Other live feeds behave the same way." The invariants enumerate each sibling class: per-object filtering for multi-object subscriptions; "Raw stream or table data … must not be delivered to a caller that lacks the table-reading system privilege, including a caller that may access the stream as an object"; the override collection and algorithm override text rules; live algorithm status; and command history "for every entry the feed emits". Every trap is covered, most of them almost by name.

| Trap | Origin | Mechanism | What was planted / where (1 line, file-level) | Relation to the base bug | Reason to dismiss (why a model may skip it) | What in the symptom/invariant points to it |
|---|---|---|---|---|---|---|
| packets_processor_per_item | BASE | M4 | Nothing planted; PacketsApi.java:499-527 subscribePackets(processor) must filter each packet by ReadPacket | Reported site; filter per item, do not refuse | n/a | The example; "keep delivering the authorized objects" |
| packets_stream_readtables | A-FAR | M10 | Nothing planted; PacketsApi.java:524-526 stream branch must require the ReadTables system privilege | Second input shape of the same subscription; checks the wrong privilege | "Stream object privilege already gates it" | "including a caller that may access the stream as an object" |
| mdb_changes_subscription | A-FAR | M1 | Nothing planted; MdbOverrideApi.java:274-280 subscribeMdbChanges needs GetMissionDatabase | Another live feed in another file | "Override notifications are metadata" | "Override notifications require the mission-database system privilege" |
| algorithm_status_subscription | A-FAR | M1 | Nothing planted; ProcessingApi.java:473-481 subscribeAlgorithmStatus needs ReadAlgorithm | Another live feed | "Diagnostic metadata" | "Live algorithm status must not be delivered to a caller lacking read privilege" |
| table_stream_subscription | B-ROUTE | M1 | Nothing planted; TableApi.java:177-199 subscribeStream gated only by the stream object (still unfixed upstream) | Uncovered route to the same packet-bearing rows | "Matches its REST sibling's stream-object gate" | "Raw stream or table data … table-reading system privilege" |
| mdb_override_rest_readers | B-ROUTE | M1 | Nothing planted; MdbOverrideApi.java:55-82 listMdbOverrides and :118-136 getAlgorithmOverrides enforce nothing | Ordinary REST readers of the same protected data | "REST is assumed to be the guarded side; the report is about subscriptions" | "The collection of active mission-database overrides may only be read by …" |
| containers_subscription_injected | INJ | M1 | Removed the request-time ReadPacket check from PacketsApi.java:556-590 subscribeContainers | Another packet-bytes subscription | "Narrow subscription; fixing the packet feed looks like it covers it" | "No live subscription may deliver an item …"; "covering several objects" |
| command_updates_injected | INJ | M2 | CommandsApi.java:523-543: the updatedCommand callback emits without the CommandHistory check that the creation callback keeps | An inline second copy of the per-command filter, left unguarded | "Update callback carries only attribute changes" | "for every entry the feed emits"; "receives both its creation entry and its later update entries" |

**Outcome:** the status marker is gate UNSOUND, but the notes report nop (9/9 sec fail), oracle (3/3 at 1.0) and patches (14/14, run with the blind entry temporarily omitted) as passed, with static failing only on blind/FAIRNESS. The reason for the UNSOUND marker is unclear. No fairness review. No DS or MiMo trials. Missed traps: no data.
**Read:** the siblings are many routes of one concept ("each live feed must apply its REST read's privilege"), and the instruction lists nearly every feed and privilege rule explicitly. This is close to a checklist, so the traps are unlikely to bite. The only different-concept sibling is the per-entry update callback (M2), and the instruction names it too ("every entry the feed emits"). Settle the UNSOUND marker before any trial.


---

## 7. Appendices

### 7.1 Built tasks with no sibling (not covered above)

These tasks were trialled in round 1 or in the instruction experiment, but none has a sibling.
- **Mined only (Branch A, the real advisory as published):** async-http-client, hickory-dns,
  jackson-databind, py-shiny, rclone, russh, webob. Both models solved all of them.
- **Stacking (Branch C, several real co-present vulnerabilities):** actualbudget, argo-workflows,
  asyncssh, cloudreve, filament, ruby-saml, stigmem, trigger-dev. All were solved offline, except
  stigmem (raw, unaudited: MiMo 0/3, DeepSeek solved).
  - Round-1 defects in this branch match the mechanisms above: argo `templateDefaults` (M5) and
    the argo configmap precedent (M10); asyncssh pktsize after an adjustment (M7).
  - They were real co-present bugs, not siblings of one base.
- **Instruction experiment (`-inv`, 7 tasks):** the same tasks with a terser "system + invariant"
  report. Every finished run solved. Wording is not the lever (`research/instruction-experiment.md`).

### 7.2 Prompted but never built (no manifest on the VM, 2026-10-19)

- **Opus `-inj` builds that did not finish:**
  - parked after the safety classifier stopped the injection step twice: file-viewer-xss-inj,
    izpack-zip-path-inj, protobufjs-proto-pollution-inj, rsdoctor-access-control-inj,
    yamcs-missing-authz-inj and knowns-path-traversal;
  - ended with no manifest: ckan-mcp-ssrf-inj, i18next-ssrf-inj, jetty-encoding-inj,
    nginxui-origin-inj, nuxt-authz-casing-inj, openbao-authz-pattern-inj, praisonai-authn-inj,
    summarize-ssrf-inj, svgo-sanitize-inj, tilt-ws-origin-inj, tinacms-objkey-path-inj.
- **DeepSeek pilot:** composer-ds stopped during the build.
- **MiMo pilot:** 50 `-mm` prompts were written and 9 built. The other 41 are prompts only, paused
  for queue stage 4a; langchain-mm was stopped mid-build.

### 7.3 Method

1. On 2026-10-19, pulled every `build/*/manifest.json`, `notes.md`, `FAIRNESS.md`, gate marker and
   run log, and every `tasks/*/instruction.md`, from the VM. From each trial job's verifier
   (`~/.tb-graders/cwe/jobs/*/verifier/{security,functional}/*.xml`) extracted the failing tests:
   267 graded jobs over 53 tasks.
2. Built one bundle per task: instruction, traps, verified sites, notes, raw rewards and failing
   tests.
3. Eight Opus reader agents classified every trap against one fixed guide (the two axes in §1) and
   wrote the §6 blocks. Each agent took a group of hosts, so builds of the same host were compared
   side by side. Each mapped failing security tests to trap ids through the manifest's
   `security_tests`.
4. A script computed the counts in §1-§3 from the readers' per-trap rows.

### 7.4 Caveats (read before quoting a number)

- **Rewards are raw.** They are chronological from `runs_*.log` and include runs from before a test
  repair or fairfix, so a task's row can mix two test versions. Audited verdicts come only from
  `build/audit_results.py`. Here, only the round-1 jackson tasks and jackson-databind-sib2 use
  audited data.
- **"Missed" is per trap**: missed in at least one run with per-test data. It is not a miss rate
  per run. 249 trap rows have no trial data ("unknown") and are left out of the rates.
- **Gate markers disagree with notes** for astro-ds, coreutils-ds, knowns-ds, mcp-atlassian-mm,
  theia-ds, tinacms-ds, keras-ds, yamcs-ds and pimcore-ds. The pipeline marked these tasks UNSOUND
  while their builders' notes say every stage passed (often a Docker or network race during the
  patches stage). Settle each by re-gating before any trial.
- **Mechanism codes are judgement calls.** Readers flagged their choices in their blocks. The main
  ones:
  - jackson's any-setter gaps are coded B (real code), although round 1 called the track
    "injection";
  - seaweedfs T1/T2: which one counts as base;
  - files named after a validated directory are coded M10;
  - state and cache files are coded M4.
- **Small samples.** Most tasks have 1-3 runs per model, so read the miss rates per mechanism as
  directions, not estimates.
