# Diversity of breakers: how to measure it, what we have, what else is available (2026-10-27)

## Executive summary

Our breakers are concentrated in one category and one trap shape. The concentration comes from what we choose to
build, not from what is possible, so there is room to diversify at little cost in yield.

### 1. How diversity is defined and measured

- **Axes:** OWASP 2025 category; CWE; mechanism; what the check guards; language; repo domain; and the decisive trap
  shape (nine named shapes, S1–S9) and its origin.
- **Numbers per axis:** count per class, share of the largest class, effective number of classes (e to the power of
  Shannon entropy; 10 means evenly spread over 10 classes), and the size of the largest family × trap-shape cluster.
- **Targets for about 150 tasks:**

  | Measure | Target |
  |---|---|
  | OWASP categories with 3 or more breakers | at least 8 of 10 |
  | Effective number of OWASP categories | at least 6 |
  | A01 (Broken Access Control) share | at most 30% |
  | Distinct CWEs | at least 40 |
  | Java share | at most 30% |
  | "Missed another place" traps | at most 50% |
  | Re-skins | none |

### 2. What our 18 breakers rely on

- **One category:** 11 of 18 (61%) are A01, Broken Access Control. Our effective number of categories is 2.8;
  CWE-bench's own set scores 10. There are no breakers yet in A02 (misconfiguration), A03 (supply chain) or A04
  (cryptographic failures).
- **One trap shape:** "missed another place" (a second copy of the check, a route around it, another input) decides
  11 of 18. Real code that the published upstream fix also misses decides 14 of 18. A protection declared in
  configuration that one consumer ignores is behind 4 (tomcat servlet, camel, fastify, dbhub).
- **Near-duplicates:** ip-address and bifrost-s2 (another SSRF of this kind would be a re-skin); fastify and camel;
  froxlor and passenger.
- **Java** is our best language (43% of trialled Java tasks are both-model breakers, against 11–21% for others) and
  also a concentration (8 of the 18).

### 3. What else is available

- **The concentration is our choice:** A01 is 51% of what we built but only 31% of the candidate pool, and the yield
  per trialled task looks similar across categories (the non-A01 samples are small). Moving away from A01 should cost
  little yield.
- **Families with supply but no breaker yet** (main candidate pool):

  | Family | Candidates | Note |
  |---|---|---|
  | Signature and certificate verification | 80 | |
  | SQL/NoSQL injection | 54 | plain sinks are easy; only dialect or grammar quirks look promising |
  | ReDoS | 51 | |
  | Request smuggling and parser differentials | 43 | h2-s2 is a both-fail candidate here (in repair) |
  | Cryptographic failures (A04) | 43 | 4 built, none ever trialled |
  | Deserialization | 36 | 374 more among older advisories |
  | Race conditions and TOCTOU | 30 | |
  | Template injection | 15 | |
  | XXE | 9 | 215 more among older advisories; the only route into A02 |

- **Supply beyond A01:** 1,749 non-A01 candidates in the main index, 9,829 unscored entries in the newer source index,
  and 15,217 older advisories set aside. Half of our breakers already come from older advisories, so that pool is usable.
- **Gaps that need another source:** supply chain (A03) has 2 candidates in OSV advisories; memory safety is mostly
  C/C++ (parked), with only about 44 Rust/Go candidates.
- **Most promising directions:** A04 crypto (untried), deserialization and XXE from the older pool, ReDoS, and parser
  differentials / request smuggling. They are outside A01, have real supply, and fail models the way breakers need
  (several sites, a distant sink, a parser mismatch).
- **Caveats:** pool counts are advisories, not confirmed buildable tasks; advisory CWE labels are sometimes wrong;
  repo domain is not in the index, so domain counts exist only for the breakers.

---

**Scope.** The 18 scale-run both-model breakers (17 delivered, plus bifrost-s2, which is in repair). Earlier breakers are
used for comparison. Everything here was read only.

**Sources** (every number below comes from one of these):
- **[L] ledger:** VM `build/audit/ledger.md`, generated 2026-10-27 15:04 from 1,038 raw trials. It lists 44 "BREAKER
  candidate" rows: the 18, the 25 from the 2026-10-25 audit, and h2-s2.
- **[M] manifests:** VM `build/<slug>/manifest.json` (trap design), `trial_detail_*.json`, and the newest
  `POSTMORTEM.json` of each graded run (the Opus audit). It names the failing tests and what the model did.
- **[H] decisions:** VM `build/<slug>/HUMAN-DECISION.md`. All 17 delivered breakers say KEEP; bifrost-s2 has none yet.
- **[T] task metadata:** client repo `cwe-client/repo/tasks/*/task.toml` (`cwe_id`, language, advisory).
- **[I] main index:** `sourcer/index/candidates.sqlite`, 37,416 OSV entries.
- **[R] reserve index:** `sourcer/reserve/index/candidates.sqlite`, the sources2 copy with 128,864 entries.
- **[B] builds:** VM `build/` folder names plus `tasks/<slug>/task.toml`. There are 366 built tasks with a CWE,
  excluding stacking controls; 212 of them are trialled in [L].
- **[O] OWASP map:** `docs/research/owasp2025_cwe_map.json`, the official OWASP Top 10:2025 lists (249 CWEs), plus
  CWE-bench's 9 extra placements and the ancestor fallback, exactly as `sourcer/weights.json` uses them.
- **[CB] CWE-bench:** `docs/research/cwe_bench_v1_category.tsv` and `cwe_bench_v1_cwe.tsv`, DeepSeek V4.1 Flash pass@1.
- **[QA] the 2026-10-25 audit:** `reports/QUALITY-AUDIT-20261025.md`.

The scripts I used are in my scratchpad; they only read the files above.

---

## Most important findings

1. **We are concentrated on one category.** 11 of the 18 breakers (61%) are OWASP A01, Broken Access Control.
   - The effective number of categories is **2.8**. CWE-bench's own set scores **10.0** (12 tasks in each of 10 categories).
   - Over all 44 breaker candidates in [L]: A01 is 25 (57%) and the effective number is 4.2.
   - **Never covered by any breaker:** A02 Misconfiguration, A03 Supply Chain, A04 Cryptographic Failures.
   - The 18 also miss A07, A08, A09 and A10.
2. **The shared pattern is mainly the trap, not only the category.**
   - **Trap:** 11 of 18 (61%) were decided by "missed another place": a second copy of the check, an indirect route
     around it, or another input on the same surface.
   - **Origin:** 14 of 18 (78%) were decided by real code that the published upstream fix does not cover.
   - **What the guard protects:** 11 of 18 (61%) decide who may reach which data or which destination. This matches
     the comparison the owner cited.
3. **The concentration comes from what we build, not from what breaks.**
   - A01 is 51% of our 366 builds [B], but only 31% of the 2,531 indexed candidates [I] (the sourcer's own `c_class`).
   - Yield per trialled task is similar across categories: A01 25 of 112 (22%), A05 7 of 38 (18%), A07 3 of 14,
     A06 2 of 15, A08 2 of 8, unmapped 3 of 19.
   - So steering selection away from A01 should cost little yield. The non-A01 samples are small.
4. **Supply outside A01 exists.**
   - **Main index:** 1,749 of the 2,531 candidates are not A01.
   - **Reserve:** 9,829 sources2 entries are pending, and 15,217 older advisories are deferred.
   - **Families with candidates but no breaker yet:** deserialization (36 candidates in the main pool), SQL/NoSQL
     injection (54), ReDoS (51), XXE (9; 215 in the deferred pool), race/TOCTOU (30), signature and certificate
     checks (80), template injection (15), request smuggling/parser differentials (43; h2-s2 is a both-fail candidate
     in repair).
5. **Older advisories already work.** 9 of the 18 breakers rest on an advisory published before the main index's
   window (2026-06-01). The deferred pool is therefore a proven source for stacking, not only a backup.
6. **Java is our strongest language** (10 of 23 trialled Java tasks are both-model breakers, 43%; the other languages
   range from 11% to 21%). It is also 8 of the 18 (44%), which is itself a concentration to watch.

---

## 1. How to define and measure diversity

**Unit.** Measure the delivered breakers. Measure the build queue too, because that is where concentration starts
(finding 3). Give each task one value per axis below, recorded at build time.

### The axes and their taxonomies

| Axis (metric) | Taxonomy | How to assign |
|---|---|---|
| OWASP category (C1) | OWASP Top 10:2025, 10 categories, plus "unmapped" [O] | Map the task's primary CWE: the official 249 CWEs first, then CWE-bench's 9 extra placements (310, 208, 1336, 770, 913, 1284, 354, 1321, 674), then the nearest mapped CWE ancestor. Anything left is "unmapped" (DoS 400/407/1333, memory safety, 178). This is the rule `weights.json` already uses. |
| CWE (C1) | MITRE CWE ids | `cwe_id` in task.toml |
| Mechanism family (C1) | Our 24 families (list in section 3.3) | By CWE, overridden by hand when the CWE label is misleading |
| Guard object (C1, coarse) | 5 values: data access, outbound destination, input/output filter, crypto/integrity, availability | What the missing protection decides |
| Language / ecosystem (C1) | Language of the changed source; OSV ecosystem | `language` in task.toml |
| Repo domain (C1) | 6 values: end-user web app, server/container, framework, library, infra/gateway service, AI/agent tooling | By hand from the repo |
| Decisive trap shape (C2) | S1–S9 (below) | From the post-run audits: the trap that failed in most failing runs |
| Decisive trap origin (C2) | uncovered upstream, published-fix far site, advisory route, injected | From the manifest trap `origin` field |

**Trap shapes (C2):**

| Shape | What the model got wrong |
|---|---|
| S1 second copy | the same defect in another implementation or another feature |
| S2 indirect route | a path that bypasses the shared check: an exemption, a sink after the check, a construction path that drops the configured protection, a component below the protection point |
| S3 conditional check | the check exists but only runs under a condition |
| S4 representation variant | the same value written another way: encoding, prefix length, numeric spelling, carried address form |
| S5 parser differential | the checker and the real consumer (browser, database) read the input differently |
| S6 adversarial object semantics | the value changes between reads, or an operation lies about succeeding |
| S7 other inputs on the same surface | the reported parameter is fixed, its neighbours are not |
| S8 kept a plausible special case | a branch that looks supported is the hole |
| S9 over-blocked legitimate use | a keep-working regression decides the run |

### The numbers to compute

Here n_i is the number of breakers in class i, N is the total, and p_i = n_i / N.

| Number | Formula | Why |
|---|---|---|
| Coverage | number of classes with n_i ≥ 1, and with n_i ≥ 3 | breadth |
| Largest share | max p_i | concentration (C4) |
| Shannon entropy | H = −Σ p_i ln p_i | spread |
| Effective number of classes | N_eff = e^H | spread in plain units: "as diverse as N_eff equal classes" |
| Largest cluster (C4) | the biggest group sharing (mechanism family × trap shape), as a share of N | catches re-skins that the category alone hides |
| Repo reuse (C4) | tasks per repo | |
| Near-duplicate pairs (C3) | count of pairs flagged by the rule below | |

**Near-duplicate rule (C3).** Flag a pair when the two tasks share the mechanism family **and** the trap shape, **and**
either the same repo or the same invariant (for example, "classify the address the value reaches"). A flagged pair
with the same invariant and the same shape is a re-skin. Reject it, because the client's agent makes variants itself.

### Targets for 100–200 breakers (per 150)

| Axis | Today: the 18 | Today: all 44 [L] | Target | Basis for the target |
|---|---|---|---|---|
| OWASP coverage (n ≥ 3) | 2 of 10 | 2 of 10 | ≥ 8 of 10 | A03 has 2 candidates in the main index, so all 10 is not realistic from OSV |
| OWASP largest share | 61% (A01) | 57% (A01) | ≤ 30% | the candidate pool itself is 31% A01 |
| OWASP N_eff | 2.8 | 4.2 | ≥ 6 | the pool is 6.6; CWE-bench is 10.0 |
| Distinct CWEs | 14 | 25 | ≥ 40 | CWE-bench has 73 CWEs in 120 tasks |
| Largest single CWE | 11% | 14% (CWE-863) | ≤ 8% | |
| Mechanism family N_eff | 6.6 (8 families) | — | ≥ 10, with ≥ 15 families present | |
| Language largest share | 44% (Java) | — | ≤ 30%, ≥ 7 languages | |
| Domain largest share | 28% (library) | — | ≤ 30% | |
| Trap shape largest share | 33% (S2) | — | ≤ 30% | |
| "Missed another place" (S1+S2+S7) | 61% | 44% of the 25 [QA] | ≤ 50% | |
| Largest family × shape cluster | 2 of 18 (11%) | — | ≤ 8% | |
| Repo reuse | 1 repo twice (apache/tomcat, different mechanisms) | 1 [L] | ≤ 2 tasks per repo, in different families | |
| Re-skins | 0 | — | 0 | |

---

## 2. What our current breakers rely on

### The 18, one per row

In the decisive-trap column, "6/6" means the trap failed in all six failing runs: three per model.

| # | Task (client name; VM slug if different) | CWE | OWASP | Mechanism | Decisive trap (failing runs) | Shape | Origin | Lang | Domain |
|---|---|---|---|---|---|---|---|---|---|
| 1 | froxlor-data-export-symlink-escape | 59 | A01 | Privileged cron follows links the customer planted | T10: a second privileged routine (traffic-statistics chown) follows the link, 6/6; T7 working directories, 3/6 | S1 | uncovered | PHP | web app (hosting panel) |
| 2 | silverpeas-file-download-path-traversal | 36 | A01 | File download traversal and missing entitlement | T1: a request naming no space is still served (the "personal space" branch is kept), 6/6. DeepSeek also left the sibling endpoint (T3) open and broke temp downloads. | S8 | advisory route (upstream fix covers it) | Java | web app (portal) |
| 3 | tomcat-servlet-constraint-bypass | 863 | A01 | Servlet security constraints not applied | T6: a login-action suffix match exempts any servlet mapped under that name, 6/6 | S2 | uncovered | Java | server/container |
| 4 | convoy-cross-project-source-access | 639 | A01 | Cross-project IDOR | T5: ownership is checked only for "incoming" projects, 6/6; T4: the check is nested under endpoint_id, 4/6 | S3 | uncovered | Go | infra service |
| 5 | dbhub-readonly-mode-write-bypass | 863 (+184) | A01 | Read-only SQL mode bypass | T9: MySQL's "--" comment grammar hides a write; a narrowed comment rule breaks legitimate parsing. Per-test detail exists for 4 of 6 runs. | S5 | advisory route | TypeScript | AI tooling (database MCP) |
| 6 | passenger-temp-dir-symlink-reuse | 59 | A01 | Predictable temp directories; link following (TOCTOU) | T4: the executable-probe helper, a third implementation, 6/6 | S1 | uncovered | C++/Ruby | server/container |
| 7 | payara-rest-credential-forwarding | 352 | A01 | Admin credential sent to a caller-chosen host | T6 + T7: other request values on the same download surface (Content-type; app name used in a REST path and a staging file), 6/6 | S7 | uncovered | Java | server/container |
| 8 | tomcat-cluster-encryption-bypass | 311 | A06 | Cluster encryption without integrity | T4: a component that sends from below the encryption interceptor sends plaintext, 6/6. DeepSeek also disabled the documented OFB/CFB modes. | S2 | uncovered | Java | server/container |
| 9 | liferay-unsanctioned-redirect | 601 | A01 | Open redirect | T2 + T3: the portlet-action response and the auto-login filter redirect without the shared check, 6/6 | S2 | uncovered | Java | web app (portal) |
| 10 | antisamy-sanitizer-xss-bypass | 79 | A05 | Sanitiser output that a browser re-parses differently | T4: backslash protocol-relative URL; T5: self-closed non-void elements; 6/6 | S5 | uncovered | Java | library |
| 11 | ip-address-private-range-ssrf | 918 | A01 | Address classification for SSRF guards | T2 link-local /10, T3 short-prefix host bits, T1/T4 NAT64 forms. Every run misses at least one. | S4 | uncovered (T2, T3) | TypeScript | library |
| 12 | commonmark-quadratic-parsing-dos | 407 | unmapped | Algorithmic-complexity DoS | T3–T5: the same quadratic merge in four places of the Attributes extension; all 6 runs score 0.25 | S1 | published fix, far site | PHP | library |
| 13 | fastify-false-schema-validation-bypass | 20 | A05 | A `false` schema treated as absent | T3: not-found handler schemas are never compiled, 6/6 | S2 | uncovered | JavaScript | framework |
| 14 | spring-framework-binding-exclusion-bypass | 178 | unmapped | Data-binding exclusion bypass | DeepSeek: T5, index spellings 00 / +0, 3/3. MiMo: over-normalised map keys, a functional failure, 3/3. | S4 (+S9) | uncovered | Java | framework |
| 15 | urllib3-redirect-credential-leak | 200 | A01 | Credentials replayed on a cross-origin redirect | T7: the URLFetch-backed manager, where the platform follows redirects, 6/6 | S1 | uncovered | Python | library |
| 16 | camel-undertow-header-filter-bypass | 20 | A05 | Header filter bypass | T1–T3: the configured filter is dropped by a supplied binding, the REST consumer and the REST producer; T4 also fails; 6/6 | S2 | uncovered | Java | framework |
| 17 | serialize-javascript-code-injection | 96 | A05 | Code injection in serialised output | T6: a second read of a property (getter); T7: a delete that does not delete; 6/6 | S6 | uncovered | JavaScript | library |
| 18 | bifrost-s2 (in repair) | 918 | A01 | SSRF in an LLM gateway | DeepSeek: the injected loader and probe (T4, T5) and the real raw fetcher and dial guard (T2, T3). MiMo: allowed CGNAT and 6to4-carried private addresses as "private OK". | S2 (+S4) | uncovered + injected | Go | AI tooling (LLM gateway) |

Sources: traps and origins from [M]; failing tests and model behaviour from the POSTMORTEM files [M]; CWE from [T];
OWASP from [O]; spring, silverpeas and dbhub notes from [H].

### Concentration of the 18

| Axis | Distinct | Largest class | N_eff = e^H | Counts |
|---|---|---|---|---|
| OWASP | 4 | A01, 11 (61%) | 2.8 | A01 11 · A05 4 · unmapped 2 · A06 1 |
| CWE | 14 | 59 / 863 / 918 / 20, 2 each (11%) | 13.2 | the rest 1 each |
| Mechanism family | 8 | SSRF / redirect / outbound, 5 (28%) | 6.6 | outbound 5 · path/links 3 · authz/IDOR 3 · input validation 3 · XSS 1 · code injection 1 · crypto 1 · DoS 1 |
| Guard object | 5 | data access, 6 (33%) | 4.1 | data access 6 · outbound destination 5 · input/output filter 5 · crypto 1 · availability 1 |
| Trap shape | 8 | S2 indirect route, 6 (33%) | 6.2 | S2 6 · S1 4 · S4 2 · S5 2 · S3 1 · S6 1 · S7 1 · S8 1 |
| Trap origin | 4 | uncovered upstream, 14 (78%) | 2.1 | uncovered 14 (one also injected) · advisory route 2 · published-fix far site 1 |
| Language | 7 | Java, 8 (44%) | 5.2 | Java 8 · PHP 2 · Go 2 · TypeScript 2 · JavaScript 2 · Python 1 · C++/Ruby 1 |
| Domain | 6 | library, 5 (28%) | 5.4 | library 5 · server/container 4 · framework 3 · web app 3 · AI tooling 2 · infra service 1 |
| Pipeline | 2 | stacking, 16 (89%) | — | stacking 16 · sibling step 2: 2 (fastify-s2, bifrost-s2) |

**What they all rely on, in one sentence.** A protection that exists and works where the report points, but is
missing, conditional or bypassed somewhere the report does not point. In 14 of 18, that place is real upstream code the
published fix also misses.

**A recurring sub-pattern** in 4 of 18 (tomcat-servlet, camel, fastify, dbhub): a protection is declared in
configuration or in a contract, and one consumer never honours it.

**Near-duplicates and reuse (C3, C4):**
- **fastify and camel:** they share 4 of 5 axes (input validation, S2, framework, A05). They differ in invariant
  ("a false schema admits nothing" vs "a configured header filter applies on every binding"), so they are not a re-skin.
- **ip-address and bifrost-s2:** both rest on "classify the address the value reaches", with the same carried forms
  (NAT64, 6to4, CGNAT). This is the closest pair. Another SSRF-classification task would be a re-skin.
- **froxlor and passenger:** both are CWE-59 link-following in privileged work, with the same shape (S1). The
  invariants differ: customer folder vs temp directory.
- **urllib3 and electron-builder-ds** (earlier batch): both are credentials replayed on a cross-origin redirect.
- **apache/tomcat appears twice**, with different mechanisms (constraints vs cluster crypto). Repo reuse among all 44: 1.

### Comparison with the 25 audited on 2026-10-25 [QA]

- **Same shape:** the top decisive pattern was again "missed indirect route / second copy": sibling 6 of 12,
  stacking 3 of 8, precision validation 2 of 5. That is 11 of 25 (44%).
- **Weaker breakers:** 5 of the 25 were decided only by a functionality regression (lemur, mistral-rs, hubuum,
  litellm, openbao).
- **Injection rarely decides:** in 10 of 12 sibling breakers, the injected sites did not decide the result. The 18
  agree: bifrost-s2 is the only one where an injected site decided runs.

**All 44 breaker candidates [L], by the OWASP category of the primary CWE:**

| Category | A01 | A05 | A07 | unmapped | A06 | A08 | A10 | A09 | A02 | A03 | A04 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Breakers | 25 | 7 | 3 | 3 | 2 | 2 | 1 | 1 | 0 | 0 | 0 |

The 25 distinct CWEs are 20, 22, 36, 59, 79, 88, 96, 173, 178, 200, 287, 306, 311, 352, 407, 444, 476, 532, 601, 639,
829, 862, 863, 918 and 1321.

---

## 3. What other patterns are available, and how many

### 3.1 The pools

| Pool | Entries | Repos | Published | State |
|---|---|---|---|---|
| **P1** main candidates [I] (status candidate or shortlisted) | 2,531 | 848 | 2026-06-01 to 2026-10-09 | passed the CWE, repo, fix-commit and diff filters; scored |
| **P2** sources2 pending [R] | 9,829 | 2,375 | 2026-06-01 to 2026-10-24 | parsed and diffs fetched (9,264 ok); **not classified or scored**. Language known for 5,186. |
| **P3** main deferred [I] | 15,217 | 4,887 | 2007 to 2026-05-29 | outside the recency window; all have a CWE, a GitHub repo and fix-commit references; not diff-checked |

Already used: 366 built tasks over 292 repos [B]. In P1, 1,169 of 2,531 candidates (in 265 repos) sit in a repo we
have already built. This matches by repo, not by advisory, so it is an upper bound on what has been used.

### 3.2 By OWASP category

| Category | P1 (`c_class`) | P2 (first CWE) | P3 (first CWE) | Built [B] | Trialled | Both-model breakers [L] | DeepSeek pass@1 in CWE-bench [CB] |
|---|---|---|---|---|---|---|---|
| A01 Broken Access Control | 782 | 3,104 | 4,227 | 188 | 112 | 25 | 65% |
| A02 Security Misconfiguration | 16 | 42 | 240 | 3 | 3 | 0 | 57% |
| A03 Software Supply Chain | 2 | 4 | 21 | 0 | 0 | 0 | 60% |
| A04 Cryptographic Failures | 43 | 181 | 411 | 4 | **0** | 0 | 65% |
| A05 Injection | 490 | 1,841 | 4,674 | 72 | 38 | 7 | 54% |
| A06 Insecure Design | 429 | 967 | 1,275 | 22 | 15 | 2 | 42% |
| A07 Authentication Failures | 186 | 769 | 991 | 30 | 14 | 3 | 58% |
| A08 Software/Data Integrity | 148 | 329 | 810 | 18 | 8 | 2 | **39%** (hardest) |
| A09 Logging & Alerting | 23 | 53 | 128 | 2 | 1 | 1 | 55% |
| A10 Exceptional Conditions | 112 | 369 | 443 | 5 | 2 | 1 | 52% |
| unmapped (DoS, memory safety, 178, …) | 300 | 2,170 | 1,997 | 22 | 19 | 3 | — |
| **Total** | 2,531 | 9,829 | 15,217 | 366 | 212 | 44 | |

**How the columns were made:**
- **P1** uses the sourcer's own `c_class`.
- **P2 and P3** use the first-listed CWE with the same mapping rules. Advisories with several CWEs can sit in more than one category.
- **Built and trialled** use each task's primary CWE.

**What the table says:**
- **Selection drives the A01 share.** Builds are 51% A01, against 31% of P1.
- **Under-built categories:** A06 is 17% of P1 but 6% of builds. Unmapped is 12% of P1 but 6% of builds. A04 has 43
  candidates and 4 builds, and none was ever trialled.
- **The largest unmapped CWEs in P1:** 400 (172), 407 (55), 1333 (51), 835 (29), 409 (19), 178 (19), 125 (18).

### 3.3 By mechanism family

- **How the counts work.** An advisory counts in every family its CWEs touch. Breakers [L] are counted the same way.
- **CWE-bench rates are DeepSeek pass@1 on 1 to 5 tasks per CWE**, so read them as hints only.

| Family (CWEs) | P1 | P1 repos | P2 | P3 | Built | Trialled | Breakers [L] | Main P1 languages | Why models might fail; what we know |
|---|---|---|---|---|---|---|---|---|---|
| Access control / IDOR (284, 285, 639, 862, 863, …) | 436 | 182 | 1,912 | 1,729 | 74 | 39 | 10 | Go 158, Py 71, TS 69 | covered; saturating the set |
| Path traversal / links (22, 36, 59, 73, …) | 267 | 170 | 667 | 1,198 | 75 | 42 | 5 | Py 78, Go 63 | covered; lowest yield of the big families (5 of 42 trialled) |
| SSRF (918, 441) | 151 | 102 | 416 | 399 | 27 | 18 | 5 | TS 41, Py 38 | covered; the next one risks a re-skin (ip-address / bifrost) |
| Open redirect (601) | 30 | 27 | 63 | 245 | 6 | 3 | 1 | TS 10 | CWE-bench DeepSeek 0% (1 task); liferay shows sinks after the check work |
| Authentication / session | 202 | 134 | 703 | 995 | 34 | 14 | 3 | Go 60 | covered |
| Information exposure (general) | 147 | 99 | 331 | 775 | 20 | 13 | 3 | Py 39 | covered |
| Input validation / canonicalisation / case (20, 178, 184, …) | 181 | 117 | 374 | 933 | 20 | 16 | 4 | Java 37 | fastify, camel, spring, jetty: "every spelling" invariants work |
| XSS / sanitiser (79, 116, …) | 191 | 127 | 684 | 2,490 | 23 | 11 | 3 | PHP 54, TS 52 | CWE-bench DeepSeek 25% on 79; parser differentials (antisamy, svgo) decide |
| **SQL / NoSQL / query injection** (89, 943, 90, 643) | 54 | 40 | 277 | 401 | 7 | 2 | **0** | PHP 19, TS 13 | textbook sinks are solved (CWE-bench 89: 100%). Only plausible angle: grammar or dialect differentials, or many query builders (dbhub's MySQL `--` trap decided runs) |
| **Template / expression injection** (1336, 917) | 15 | 14 | 39 | 61 | 0 | 0 | **0** | Py 5 | CWE-bench DeepSeek 0% on 1336 (2 tasks); a sandbox denylist is never complete |
| OS command / argument injection (77, 78, 88) | 64 | 47 | 376 | 516 | 8 | 5 | 1 | Py 23 | plain 78 is easy; option injection (gitpython: missed option alias) works |
| Code injection / eval (94, 95, 96, 470) | 95 | 72 | 312 | 566 | 18 | 12 | 1 | Py 34, TS 26 | low yield so far (1 of 12); serialize-js won through object semantics, not the sink |
| **Header / CRLF / log injection** (93, 113, 117) | 18 | 17 | 46 | 84 | 1 | 0 | **0** | mixed | CWE-bench DeepSeek 25% on 93; many emit points |
| **Deserialization** (502) | 36 | 24 | 120 | 374 | 3 | 0 | **0** | Java 15, Py 14 | CWE-bench DeepSeek 0% (2 tasks); A08 is the hardest category. An allow-list must cover every entry point (polymorphic types, alternate formats). Java is our best language. |
| Prototype pollution / mass assignment (1321, 915) | 52 | 40 | 58 | 304 | 11 | 6 | 1 | JS 24, TS 21 | protobuf.js; spring is mass-assignment in all but its label |
| **XXE / entity expansion** (611, 776) | 9 | 9 | 24 | 215 | 2 | 2 | **0** (both open) | Java 6 | the only real route into A02. Many parser factories make a natural second copy; well documented, so single-site fixes will be solved |
| **ReDoS** (1333) | 51 | 40 | 45 | 213 | 0 | 0 | **0** | Py 23, TS 12 | the same regex idiom recurs across a codebase; timing tests are feasible (commonmark: about 100 s pinned vs a 20 s bound) |
| DoS / algorithmic / uncontrolled resource (400, 407, 770, 835, 409, …) | 363 | 200 | 848 | 1,104 | 14 | 8 | 1 | Py 99, Go 64 | the largest unused family; commonmark proves the S1 shape works here |
| **Crypto misuse / weak randomness** (326, 327, 330, 338, 311, 319, …) | 45 | 36 | 116 | 346 | 3 | 1 | 1 | Go 11, Java 11 | A04 is easy in CWE-bench (Opus 90%). tomcat-cluster won by carrying one guarantee through every configuration. |
| **Signature / certificate / integrity checks** (295, 297, 345, 347, 354) | 80 | 62 | 298 | 427 | 11 | 4 | **0** | Py 21, TS 20, Go 15 | CWE-bench DeepSeek 0% on 345; verification must hold for every algorithm, key source and element |
| Timing side channel (208, 203) | 17 | 17 | 41 | 117 | 2 | 0 | 0 | Go 5 | hard to test deterministically |
| **Race / TOCTOU** (362, 367, …) | 30 | 25 | 124 | 169 | 1 | 1 | **0** (passenger is close) | Go 7, TS 6, Rust 6 | CWE-bench DeepSeek 0% on 362. Tests must be deterministic: hooks or link swaps, as passenger showed. |
| Secrets in logs / errors (532, 209, 215, …) | 46 | 38 | 90 | 277 | 4 | 1 | 1 (hubuum, functional-only) | Py 14, Go 12 | CWE-bench DeepSeek 35% on 532. Risk: over-redaction gives functional-only breakers (hubuum, airflow). |
| **Request smuggling / interpretation differential** (444, 436) | 43 | 23 | 64 | 123 | 1 | 1 | 1 (h2-s2, not in the 18) | JS 12, Go 10 | CWE-bench DeepSeek 0% on 444; two parsers must agree. The h2-s2 repair re-gate failed on 2026-10-27. |
| CSRF / CORS / origin (352, 346, 942) | 69 | 63 | 192 | 507 | 7 | 6 | 1 | TS 17 | payara |
| Supply chain / untrusted loading (426, 427, 494, 829, 1104, …) | 19 | 18 | 81 | 114 | 4 | 1 | 1 (theia) | TS 10 | A03 CWEs are almost absent from OSV advisories. Covering A03 needs a different source (for example, the 56 GitHub Actions records in NEW-SOURCES.md). |
| Memory safety (native: 119, 125, 416, 476, 787, …) | 78 | 52 | 1,377 | 708 | 5 | 3 | 1 (tensorflow, C++) | Go 22, C++ 14, C 10, Rust 8 | C/C++ is parked (build cost; OSS-Fuzz recall risk). P2 is mostly C and C++. |
| Integer overflow / numeric (190, 191, 369, …) | 25 | 21 | 267 | 204 | 1 | 1 | 0 | Go 14 | same constraint |
| Exceptional conditions (248, 252, 703, 754, 755) | 64 | 47 | 188 | 280 | 1 | 0 | 0 | JS 19 | CWE-bench DeepSeek 0% on 252 (1 task) |
| File upload (434) | 20 | 15 | 55 | 134 | 4 | 3 | 0 | PHP 9 | easy in CWE-bench (100%) |

**Memory safety outside C/C++.** Counting memory safety and integer overflow together:
- **P1:** Go 34, Rust 10, C/C++ 26.
- **P2:** C 666, C++ 173, Go 23, Rust 9.
- **The catch:** Rust and Go together give about 44 candidates in P1, mostly Go nil dereferences and integer
  conversions.

### 3.4 Languages and ecosystems

| Language | P1 | P2 (diffs) | Built | Trialled | Both-model breakers | Yield per trialled |
|---|---|---|---|---|---|---|
| Python | 542 | 746 | 88 | 51 | 8 | 16% |
| Go | 521 | 301 | 73 | 39 | 8 | 21% |
| TypeScript | 452 | 503 | 69 | 39 | 6 | 15% |
| JavaScript | 294 | 224 | 32 | 24 | 5 | 21% |
| PHP | 292 | 884 | 43 | 27 | 3 | 11% |
| Java | 233 | 270 | 40 | 23 | **10** | **43%** |
| Rust | 96 | 128 | 12 | 6 | 2 | — |
| Ruby | 36 | 100 | 6 | 2 | 1 | — |
| Scala / Kotlin | 25 | — | 1 | 0 | 0 | — |
| C / C++ | 33 | 1,330 | 1 | 1 | 1 | — |
| Elixir | 0 | 203 | 0 | 0 | 0 | — |
| C# | 0 | 125 | 0 | 0 | 0 | — |

**Notes:**
- **Ecosystems in P1:** npm 736, PyPI 589, Go 530, Packagist 302, Maven 265, crates.io 89, RubyGems 43.
- **Elixir and C# are new languages for us**, and only P2 has them. Beyond P2, NEW-SOURCES.md counts 366 Hex records
  with a fix commit (Elixir) and 533 NuGet records with a fix commit (.NET).
- **Why the language counts differ:** P1 uses the index `language`; built and trialled use task.toml `language`.

### 3.5 Families worth trying first

Ranked by: enough supply, no breaker yet, a reason for a multi-place trap, and no known blocker.

| Rank | Family | P1 / P3 supply | Category it adds | Why it might break both models | Known constraint |
|---|---|---|---|---|---|
| 1 | Deserialization (502) | 36 / 374 | A08 (hardest in CWE-bench) | entry points are spread out: polymorphic typing, nested types, YAML/XML front ends | single-site allow-lists are well known; we need repos with several deserialization entry points |
| 2 | Request smuggling / parser differentials (444, 436) | 43 / 123 | A06 | two parsers must agree; trailers, continuations and duplicate fields | h2-s2 is a live example; its repair re-gate failed |
| 3 | ReDoS and algorithmic DoS (1333, 407, 400) | up to 414 / 1,317 (the two families can overlap) | unmapped | the same idiom in many places (S1); commonmark worked | timing tests under load need generous bounds |
| 4 | Signature / certificate / integrity (345, 347, 295) | 80 / 427 | A04, A07, A08 | every algorithm, key source and signed element must be covered | none seen yet; 4 trialled, 0 breakers |
| 5 | XXE (611, 776) | 9 / 215 | A02 (never covered) | many parser factories (S1) | Java-heavy; documented protection; needs the deferred pool (P3) |
| 6 | Template / expression injection (1336, 917) | 15 / 61 | A05, a new sub-family | sandbox denylists are never complete | small supply; never built |
| 7 | SQL / NoSQL injection, only with dialect or grammar angles | 54 / 401 | A05 | parameterising one builder misses others; the comment and quoting grammar differs per dialect | the plain sink is solved |
| 8 | Race / TOCTOU (362, 367) | 30 / 169 | A06 | the check and the use are in different functions | test determinism |
| 9 | Crypto misuse (A04) | 45 / 346 | A04 (never trialled) | one guarantee across every mode and configuration (tomcat-cluster) | the easiest category in CWE-bench |
| 10 | Header / CRLF / log injection (93, 113, 117) | 18 / 84 | A05, A09 | many emit points | small supply |

**Lessons from earlier runs that apply to every row:**
- **Breakers come from real routes.** They are won by real code paths the upstream fix misses (14 of 18 here); the
  advisory site alone is not enough.
- **Some changes lose.** Wording changes, documented protections and single-site small libraries tend to be solved.
- **Stacking rescues small libraries.** It made four small libraries into breakers: ip-address, serialize-javascript,
  commonmark and antisamy. It worked because each stacked several advisories and had uncovered routes.
- **Functional-only breakers are weaker.** The client may not want them as security tasks.
- **Open internet.** A trap the upstream fix covers can be looked up (gitpython, pv-apostrophe, silverpeas T1).

---

## Unknowns

- **Pool counts are advisories, not buildable tasks.**
  - P2 has not been classified or scored; 3,582 of its entries have no linked fix commit.
  - P3 has not been diff-checked.
  - I did not read the screener records, so I do not know how many P1 candidates were screened and rejected.
- **The CWE labels are the advisories' own and are sometimes wrong.**
  - P2 and P3 categories use the first-listed CWE.
  - Built and trialled tasks use the task's primary CWE only, though stacked tasks hold several.
- **Repo domain is not in the index**, so domain counts exist only for the breakers.
- **Per-category yields rest on small samples:** A08 has 8 trialled tasks, A09 has 1, A10 has 2.
- **Some per-test detail is missing.** The audit records lack item-level failures for 2 of 6 dbhub runs and 3 of 6
  commonmark runs. Their rewards and human decisions are known.
- **bifrost-s2 is in repair.** Its audits flag two possible test issues: a "dial tcp" error match, and NAT64 local-use
  decoding.
- **h2-s2 (CWE-444) is a both-fail candidate in [L] but outside the agreed 18.** Its repair re-gate failed at
  2026-10-27 04:50Z, so it is not counted as a breaker here.
