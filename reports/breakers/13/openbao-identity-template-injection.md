# openbao-identity-template-injection — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: both-model breaker, delivered.** The counted attempts were run on 2026-10-21 (04:30–08:46 UTC). Sources: the delivered task, the build and validation records, the fairness review, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- Every counted attempt finished on its own (no timeout). Agent time was about 12–32 minutes for DeepSeek and 49–78 minutes for MiMo, against a 2-hour limit.
- Every counted attempt was audited independently: all 6 were judged trustworthy and a genuine model failure, with high confidence.
- The task is OpenBao, a real secrets-management server, at the commit before a published fix for identity-template injection. Two further allow-list routes that follow the same pattern were added for the task, and they are reachable through the real certificate API.
- Why both models fail: every attempt closed every attack route (21/21 security tests in all 6). They all failed on legitimate use. Each model put one global block-list of characters in the shared templating code, and this block-list also refused ordinary identity values in places where those characters have no special meaning: a certificate URI name containing `/` (5 of 6 attempts) and an SSH default user containing a comma (3 of 6).

## 1. The task

**Vulnerability (CWE-863, incorrect authorization).** OpenBao fills administrator-written authorization rules with the caller's identity data at use time: placeholders such as `{{identity.entity.metadata.<key>}}` appear in ACL policy paths and in the allow-lists of PKI and SSH certificate roles. The substituted value is pasted in verbatim. So a user who can edit their own identity data can plant a pattern metacharacter (a wildcard, a glob star, a list separator or a path separator) and widen what the rule grants.

- **Project and language:** OpenBao (Go).
- **Base advisory:** GHSA-59W7-V8RR-PR4P / CVE-2026-71543 / GO-2026-6556.
- **Vulnerable commit:** 681f6e2 (`681f6e2730f03f9cd2a5ce7d056fc957622cfe81`). **Upstream fix:** 2d4ebaf (the advisory record also lists a second commit, e516ce5). The upstream fix covers ACL paths, the PKI URI and domain allow-lists, and SSH principal rendering.

**What the task contains.** Nine routes. Each is a matcher fed by a substituted identity value.

| Route | Origin | What leaks | What must keep working next to it |
|---|---|---|---|
| 1. ACL policy path, one-segment wildcard `+` | advisory (the report's example) | a secret on a sibling path | a clean substituted value still reads its own path |
| 2. ACL policy path, trailing glob `*` as the last segment | advisory | every path under the prefix | an administrator's literal trailing `*` next to a placeholder |
| 3. ACL policy path, `/` inside the value (alone or next to a literal `*`) | advisory | deeper paths the rule never named | a clean value in a multi-segment rule |
| 4. PKI `allowed_uri_sans`, glob star | advisory, fixed upstream | a certificate for any URI under the prefix | a clean templated URI name such as `spiffe://d/users/alice` still issues |
| 5. PKI `allowed_domains` with globs enabled, glob star | advisory, fixed upstream | a certificate for any matching host | an administrator's literal `*.example.com` |
| 6. SSH `allowed_users` / `allowed_domains`, list separator `,` | advisory, fixed upstream | a signed certificate for an extra principal or host | clean templated users; a literal `*` still means "any"; a default user rendered from identity data is still used and re-checked |
| 7. SSH host certificates with domain globs enabled, glob star | code added for the task | a host certificate for any matching host | an administrator's literal glob domain |
| 8. PKI templated user-id allow-list, glob star | code added for the task | a certificate for any user id | an administrator's literal `dev*`; a clean templated user id |
| 9. The same values arriving through other identity sources (entity name, alias name and metadata, group name and metadata) | advisory, fixed upstream in the shared templating code | the same widenings on routes 1–8 | clean values from each source |

Routes 7 and 8 add one role option to each engine. Each copies a neighbouring option of the same engine and is registered on the real role API. The upstream fix never touches them.

**Report given to the agent.** It is written as a real bug report:
- the system (identity placeholders fill policy paths and certificate-role allow-lists);
- one example (route 1 in prose: a metadata key set to a path wildcard returns a secret);
- the rule: "No value substituted from identity data may introduce a pattern metacharacter into an authorization pattern. This holds wherever a substituted value is matched against something the caller supplies — a request path, or a name, identifier or host in a certificate request — and for every identity source";
- the metacharacters it names in general terms: path wildcards, the name/identifier/host star, the allow-list separator, and the path separator;
- refusal: a client error with no side effect;
- keep working: literal metacharacters written by an administrator keep their meaning; "Legitimate substitutions keep working exactly as today"; a placeholder next to a literal `*`; literal globs; a literal single star; and "A default user or similar principal filled from identity data is still used when a role names one, and its rendered value is still re-checked against the allow-list afterwards";
- constraints: fix the close variants, keep legitimate use, do not modify tests, do not special-case the example, do not look up the upstream fix.

No file, function, engine-specific field or route count is named.

**Hidden tests.** 21 security tests (9 ACL, 6 PKI, 6 SSH) and 57 functional tests. The functional tests are 20 task tests (6 ACL, 7 PKI, 7 SSH) plus 37 of the project's own tests for the templating helper and the policy package. The ACL tests start a real in-process OpenBao cluster: they write the policy and identity data and read secrets over the HTTP API. The PKI and SSH tests drive the backends' request handler (`HandleRequest`) with an entity attached, the same path an issue or sign request takes. The tests assert behaviour only: an attack yields no secret, certificate or signature, and legitimate requests succeed. **Reward** = 1.0 only if every test passes; otherwise the share of security tests passed, forced to 0 if any functional test fails.

## 2. How we know the task is fair

The scripted gate passed on 2026-10-21 (00:45 UTC), before the counted attempts.

| Check | Result |
|---|---|
| Vulnerable code (with the added routes) | fails all 21 security tests, passes all 20 task functional tests |
| Reference fix | 1.0, on every recorded gate attempt |
| Independent fix (a separate model, given the report, the code and the list of sites; never the tests or the reference) | 1.0 |
| Alternative correct fix with no opt-in role flags | 1.0 |
| Hardening fix (reference plus default-deny in the shared helper) | 1.0 |
| The upstream advisory fix alone | not run as a separate patch; the reference minus each added route (7 or 8) fails 2 security tests each |
| One wrong-fix patch per route (leave out `+`, `*`, `/`, the URI list, the domain list, the SSH comma, route 7, route 8) | each fails the matching security tests (rewards 0.81–0.90) |
| Fix only the reported ACL site | fails 12 security tests |
| Check only entity metadata, not the other identity sources | fails 11 security tests |
| Reject only a value that is exactly a metacharacter | fails 13 security tests |
| Crash instead of refusing | fails security tests (counted as an error, not a refusal) |
| Over-broad fix (refuse every templated rule) | fails 6 ACL functional tests (reward 0.0) |
| Fairness review (a separate model checked every hidden test against the report) | READY: every security test traces to the stated rule, and every functional test to a keep-working clause or the project's own tests |

In total, 16 patches behaved as declared.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 21/21 | 56/57 | nothing | SSH default user containing a comma |
| DeepSeek | 2 | 0.0 | 21/21 | 54/57 | nothing | templated URI names containing `/` (2 tests); SSH default user |
| DeepSeek | 3 | 0.0 | 21/21 | 55/57 | nothing | templated URI names containing `/` (2 tests) |
| MiMo | 1 | 0.0 | 21/21 | 55/57 | nothing | templated URI names containing `/` (2 tests) |
| MiMo | 2 | 0.0 | 21/21 | 54/57 | nothing | templated URI names containing `/` (2 tests); SSH default user |
| MiMo | 3 | 0.0 | 21/21 | 55/57 | nothing | templated URI names containing `/` (2 tests) |

- All 6 closed every attack route, including the two added routes and every identity source.
- All 6 broke legitimate use; no project test failed in any attempt.
- 5 of 6 refused a templated certificate URI name because it contains `/` (`TestFunc_PKIUriTemplateLegit`, `TestFunc_PKIAliasMetadataUriLegit`).
- 3 of 6 refused an SSH default user rendered from identity data because it contains a comma (`TestFunc_SSHDefaultUserCommaPreserved`).
- 2 attempts broke both; 4 broke one.

## 4. Why both models failed

All six attempts took the same approach. They placed one character block-list in the shared templating helper (`sdk/helper/identitytpl`), so that every caller inherits it. The block-list was always `*`, `+`, `,` and `/` (DeepSeek attempt 1 later narrowed it per engine). Both failures come from where the list was applied, not from what it contained. The models never left an attack route open: both failures are broken legitimate behaviour.

### 4.1 Broken: certificate URI names containing `/` (5 of 6)

PKI's URI allow-list is matched with a simple glob in which only `*` is special. A `/` in `spiffe://d/users/alice` is ordinary text there. The reference therefore blocks only `*` for certificate allow-lists, and blocks `/` only where a path pattern is matched.
- DeepSeek, attempt 3: "Values containing `*`, `+`, `/`, or `,` are rejected … These cover path wildcards, glob stars, path separators, and allow-list separators." This applied to every pattern use, PKI included.
- DeepSeek, attempt 2: `const aclTemplateValueMetaChars = "*+,/"`, applied to every ACL-mode substitution; it never edited the PKI code (audit).
- MiMo, attempt 1: each substituted value "is now checked against `patternMetacharacters = "*+,/"`". Its own probe of the existing PKI template tests passed, but those tests use values without `/`.
- MiMo, attempt 3 marked "PKI `allowed_uri_sans`, `allowed_domains`, `allowed_user_ids`" as patterns under `const patternMetaChars = "*+,/"`.
- The one attempt that passed both URI tests scoped the list per matcher. DeepSeek, attempt 1: "`/` and `+` remain allowed because they are legitimate in URI/user-ID patterns."

### 4.2 Broken: an SSH default user containing a comma (3 of 6)

A role's `default_user` may be rendered from identity data. The result is the principal itself, not an allow-list entry, and the existing code re-checks it against `allowed_users` afterwards. The test renders `alice,bob` against an allow-list of `alice,bob` and expects a signature. The reference renders the default user with commas allowed and relies on that re-check.
- DeepSeek, attempt 1: "Templated `allowed_users`, `allowed_domains`, and `default_user` reject `,` and `*` introduced by substitution". It used one rendering function for both the allow-list and the default user (audit).
- MiMo, attempt 2 listed `default_user` among the "certificate-issuing allow-lists", turning "a single-name pattern into … a multi-principal request". It rendered the default user through the restricted path.
- DeepSeek, attempt 2 applied the global list with no carve-out for the default user (audit).
- The three attempts that passed drew the line the reference draws. DeepSeek, attempt 3: "It is a principal value, not an authorization pattern." MiMo, attempt 3 left "SSH `default_user` (a subject, re-checked against the allow-list afterwards)" unrestricted.

### 4.3 What they got right

Every attempt closed all nine routes, including the two added routes and every identity source. Several also turned a refused default-user render from a server error into a client error. Both MiMo attempts 1 and 2 noticed that an existing upstream SSH test relies on comma expansion in `allowed_users`, and they reported it rather than editing it. The failures are not about finding the flaw. They come from applying a correct block-list in places where the same character is legitimate.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (12–32 minutes). It centralised the fix early. Attempt 1 was the only attempt to scope characters per engine, and it then over-blocked the default user instead.
- **MiMo-V2.6-Pro:** slower (49–78 minutes). It built large out-of-repo probe suites (attempt 1: "All 33 checks pass"). It added a pattern/value split in two of three attempts, but in every attempt it treated URI allow-lists as path-like.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro. 3 counted attempts each, 2 hours per attempt.
- Offline: network access was limited to the two model APIs, and web tools were disabled. The image has no git history. The hidden tests are copied in only after the agent stops. The trialled package and the delivered package have identical instruction, tests, added code and reference; only the grading packaging differs.
- Every counted attempt was audited before it counted, by a separate model reading the transcript, final code and per-test results:
  - no access to the hidden tests and no lookups;
  - grading started after the agent stopped, and no agent activity happened during grading;
  - the score reflects real defects in the model's code.
- What counts: a run that uses the full 2-hour budget without solving counts as a failure. An attempt cut off by a provider or network outage is not counted. No attempt here timed out or was cut off.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, an alternative fix, a hardening fix and an independently written fix all score 1.0. The fairness review traced every test to the report. After each attempt, an audit found that each failing test is protected by the report's keep-working text and that a correct fix passes it. Three attempts passed the URI tests or the default-user test by drawing the same line as the reference.

**Does it hinge on one test?** The scores do not come from attack tests: all 21 pass in every attempt. Each 0.0 comes from two separate legitimate uses (three tests). Two attempts break both. DeepSeek attempt 1 breaks only the default user. The other three break only the URI names.

**Could the model have seen the answer?** The two added routes have no upstream fix. The agent could not reach the internet or the hidden tests, and the audit checked every transcript for this.

**What does a 0.0 mean here?** In this task, every 0.0 means that all attacks were blocked but a legitimate request was refused. Any functional failure scores 0.

## Appendix

| What | Contents |
|---|---|
| Task package | `instruction.md`, `task.toml`, `environment/` (Dockerfile pinning 681f6e2, `injection.patch` adding routes 7–8), `solution/` (`fix.patch`, `solve.sh`), `tests/` (security and functional Go suites, `test.sh`, `score.py`, grader Dockerfile) |
| Validation | gate report; 16 check patches (12 wrong-fix, 1 over-broad, alternative, hardening, independent fix); fairness review |
| Attempts | per attempt: score, per-test results, final code and the audit's findings |

- **Internal slug:** `openbao-ds`.
- **Counted runs (job folders):** `openbao-ds-deepseek-r1-20261021-043026-n001`, `openbao-ds-deepseek-r2-20261021-045134-n002`, `openbao-ds-deepseek-r3-20261021-050621-n003`, `openbao-ds-mimo-r1-20261021-054054-n004`, `openbao-ds-mimo-r2-20261021-070110-n005`, `openbao-ds-mimo-r3-20261021-075219-n006`.
- **Sources used:** the delivered task `tasks/openbao-identity-template-injection/` and `RESULTS.md`; the build record `build/openbao-ds/` (notes, manifest, gate report, check patches, fairness review, trial detail); per-attempt `result.json`, `verifier/results.json`, final code, transcript and `POSTMORTEM.json`.
