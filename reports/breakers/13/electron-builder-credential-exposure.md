# electron-builder-credential-exposure — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness review and the human review, every counted run's transcript, final code and per-test results, and the independent audit of every counted run.

## Summary

- **Result: both target models failed all 3 counted runs.**
  - DeepSeek V4.1 Flash: 0.72, 0.61, 0.72.
  - MiMo-V2.6-Pro: 0.61, 0.61, 0.61.
- Every run finished on its own (no timeout): DeepSeek in 19–24 minutes, MiMo in 39–112 minutes of a 2-hour limit.
- No run broke legitimate behaviour: all 6 pass all 165 functional tests. The scores differ only in how many of the 18 attack tests each run blocked.
- Every counted run was audited independently and judged a genuine model failure with high confidence.
- Why both fail: the rule reaches further than the obvious redirect helper. All 6 runs left two block-based update download paths sending the credential to the redirect target. All 6 also left a failed command's output printing a secret in clear. DeepSeek found most of these places and ruled them out of scope. MiMo fixed only part of the download code and built a redaction design that cannot see the rest.

## 1. The task

**Vulnerability (CWE-200, exposure of sensitive information).** electron-builder (TypeScript/Node) is a suite of tools for desktop apps: a build tool, release publishers and an auto-updater. Their network requests can carry a credential the operator supplied, and they are given secrets for the services they use. At the vulnerable commit, a credential supplied for one origin reaches a different origin after a server redirect. A configured secret is also written in clear text into diagnostic output.

**Base advisory:** GHSA-P2F4-R6V6-J797 (CVE-2026-54673). Vulnerable commit 8a035f8, the direct parent of the upstream fix 22a7532. The upstream fix hardens the shared redirect helper and several redaction sites. It does not touch the block-based download code or the publisher added for this task.

**What the task contains.** Six routes to the same two rules:

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| 1. Shared redirect decision, reached through the Node HTTP client, its download helper and the updater's full download over Electron | credential headers in other spellings (capitalised, upper-case, underscore), application headers (`PRIVATE-TOKEN`, `X-Api-Key`, ...), cookies, proxy credentials, Basic authentication from connection options, and a redirect that only changes the port | same-origin redirects keep credentials; an http→https upgrade on the same host keeps them; a cross-origin redirect still completes; ordinary headers still travel | advisory's own route |
| 2. Block-based (differential) update download: single-range and default multi-range requests | the updater's credential header reaches the host the update file redirects to | a download without redirects still fetches only the changed blocks; a same-origin redirect keeps the credential; a cross-origin redirect still yields the right file | real upstream code the fix left open |
| 3. Trailing byte-range read of a block map embedded at the end of the package | the credential reaches the host that read redirects to | the update still downloads correctly | real upstream code the fix left open |
| 4. Runtime diagnostics of the HTTP client: request-body debug output and the text of an HTTP error built from a JSON error response | `apiKey`, `clientSecret`, `passphrase`, `private_token`, `credential` field values in clear | non-secret fields and options are still printed; the error keeps the non-secret message | advisory's own fix sites |
| 5. Build and configuration diagnostics: a failed command's captured output, and the GitHub/GitLab invalid-token errors | a credential printed by the child process; the raw token echoed in the error | non-secret arguments and output stay in the error, the error code is unchanged, valid tokens still work | advisory's own fix sites |
| 6. A Gitea release publisher | its upload re-sends the token after a 307 to a storage origin; a malformed token is echoed in the configuration error; debug output logs the resolved configuration with the token | an unredirected upload works; a same-origin redirect keeps the token; a cross-origin upload completes and its body arrives; an invalid token is still refused and the error names the variable; the instance URL still shows in debug | added for the task |

The Gitea publisher is a new module written in the style of the existing publishers. It is wired into the normal publish-provider dispatch and exported. The published fix never enters it.

**Report given to the agent.** It is written as a bug report: the system, the observed impact (a credential reached another origin after a redirect; a secret appeared in diagnostic output), the security property, and contracts. The key rules:

> "A credential is bound to the origin — the scheme, host and port — it was supplied for. No request the product makes may carry it to any other origin, at any hop and by any path, however that credential is expressed: as a request header (standard or application-specific, in any spelling or case), as connection-level authentication, or otherwise."

> "A secret the product is given must not appear in clear text in any diagnostic output the product emits, whether an error message or debug output, and whatever name the field, option, argument or variable holding it has."

The contracts say that a cross-origin redirect continues without the credential and the operation still completes "by its normal path or by an equivalent fallback". Same-origin redirects and same-host http→https upgrades keep their credentials, ordinary headers still travel, and every legitimate operation keeps working. No file, package, function, route, advisory or count is named.

**Hidden tests.** 18 security tests and 165 functional tests:

| Area | Security | Functional |
|---|---|---|
| Shared redirect decision (route 1) | 6 | 8 |
| Block-based downloads (routes 2 and 3) | 3 | 4 |
| Runtime and build diagnostics (routes 4 and 5) | 6 | 7 |
| Gitea publisher (route 6) | 3 | 6 |
| The project's own HTTP-client and utility tests (43 + 20 + 77) | | 140 |

The tests drive the real entry points:
- the updater (`NsisUpdater`) checking for and downloading updates, over an in-process stand-in for Electron 39's network module with virtual hosts;
- the shared HTTP client against loopback servers;
- the publisher constructors and the Gitea upload;
- the build tool's `exec()` with a failing child process;
- debug output with `DEBUG=electron-builder` captured.

A redirect test passes when the other origin did not receive the credential. A redaction test passes when the secret is absent from the captured error or debug text. Refusing or falling back is accepted wherever the operation still completes.

Reward = 1.0 when every test passes. Otherwise the share of security tests passing, capped below 1. It is 0 if any functional test fails.

## 2. How we know the task is fair

Before any model ran:

| Check | Result |
|---|---|
| Vulnerable code (with the added publisher) | fails all 18 security tests, passes all 165 functional tests |
| Reference fix | 1.0: three identical runs in the full gate of 2026-10-19, and again in the full gate of 2026-10-20 after the two newest tests were added |
| Blind fix (written from the report alone) | not run |
| Alternative correct fix with a different design (allowlist of ordinary headers on cross-origin, abort and full-download fallback on block-based redirects, tokens omitted rather than hashed) and a hardening fix | 1.0 each |
| The upstream advisory fix alone | not run as a separate check. A patch limited to the published fix's sites leaves the block-based downloads and the added publisher open: 6 security tests fail (0.67) |
| One wrong-fix patch per route (7 patches: shared redirect, block-based downloads, embedded block map, runtime redaction, build redaction, and the three Gitea sites) | each fails the matching security tests (rewards 0.50–0.94), with all functional tests passing |
| Common partial fixes: two named headers only; names matched without case or separator folding; one range path only; follow the redirect first, then strip | fail 4, 8, 2 and 3 security tests |
| Over-broad fixes: strip credentials on every redirect; refuse every cross-origin redirect; drop every header | fail 24, 20 and 29 functional tests, reward 0 |

All 18 check patches behaved as declared in the full gate after the last test change (2026-10-20), and again in a patch-stage re-run the same day.

After the runs:
- An independent fairness review of this version checked all 18 security and 165 functional tests against the report. Its verdict was READY: it found no test that a correct fix could fail. It rated 16 security tests low risk and 2 medium: the full update download over Electron and the embedded block-map read, both because they rely on the Electron stand-in.
- A human review on 2026-10-20 accepted the Electron stand-in and kept the task unchanged. It noted that no counted run failed the full-download test, and that every run fails tests that were in the suite before those two were added.

## 3. Results, attempt by attempt

| Model | Run | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.72 | 13/18 | 165/165 | block-based downloads (single-range, multi-range, embedded block map); failed command's stdout and stderr | nothing |
| DeepSeek | 2 | 0.61 | 11/18 | 165/165 | all three block-based paths; command stdout and stderr; request-body debug; JSON error text | nothing |
| DeepSeek | 3 | 0.72 | 13/18 | 165/165 | multi-range; embedded block map; command stdout and stderr; JSON error text | nothing |
| MiMo | 1 | 0.61 | 11/18 | 165/165 | multi-range; embedded block map; command stdout and stderr; request-body debug; JSON error text; case and separator spellings of credential headers | nothing |
| MiMo | 2 | 0.61 | 11/18 | 165/165 | all three block-based paths; command stdout and stderr; request-body debug; JSON error text | nothing |
| MiMo | 3 | 0.61 | 11/18 | 165/165 | all three block-based paths; command stdout and stderr; request-body debug; JSON error text | nothing |

- All 6 left the multi-range download and the embedded block-map read open, and all 6 printed a secret from a failed command's output.
- 4 of 6 also left the single-range download open. 5 of 6 left the JSON error text open, and 4 of 6 the request-body debug output.
- All 6 closed the advisory's main redirect route (5 of 6 completely), the updater's full download, the GitHub and GitLab token errors, and all three Gitea sites.
- No run broke a legitimate behaviour.
- No single test, and no single area, decides any run. Every run fails at least 5 tests in at least two independent areas: block-based downloads and command output. Remove either area entirely and all 6 runs still score below 1.0.

## 4. Why both models failed

### 4.1 Left open: block-based update downloads (multi-range 6 of 6, embedded block map 6 of 6, single-range 4 of 6)

The block-based downloader issues its own range requests and follows redirects with the original headers. No run changed the multi-range path or the embedded block-map read.
- DeepSeek, run 1, decided the runtime would handle it: "Differential/multiple range rely on Electron's auto (or tests not redirects)". Later: "`multipleRangeDownloader` doesn't handle redirect events at all; under Electron, auto-follow handles them (and strips auth)". In this file it changed only log lines.
- DeepSeek, run 3, found all three paths and fixed only the single-range one, by refusing and falling back to a full download. On the multi-range path: "auto-follow likely handled by Chromium's own auth stripping; and even if not, hidden tests can't run Electron. I'll leave it." It also noted the gap in that reasoning: "Application-specific tokens (PRIVATE-TOKEN) wouldn't be stripped, though." It drafted redirect handling for the embedded block-map read, but did not apply it.
- MiMo, run 1, read the multi-range downloader ("Let me read its request-option construction and the multi-range downloader"). It fixed the single-range path correctly, by aborting and re-issuing the request without the credential, but left the multi-range path unchanged.
- MiMo, run 2, stripped the credential from the shared options and then called `request.followRedirect()`. The request already in flight still carried the header, so even the single-range path leaked. This is the "follow first, then strip" trap that one of the gate patches tests.
- DeepSeek, run 2, assumed the downloader used the shared path ("all go through `download`/`doDownload`, which uses prepareRedirect") and never opened it. MiMo, run 3, never looked at its redirect handling.

The audit, for every run: the model "hardened the main HttpExecutor redirect path but the DifferentialDownloader (and its multi-range / trailing-range variants) still forwarded the auth/credential header to the redirect target."

### 4.2 Left open: a secret in a failed command's output (6 of 6)

When a build command fails, `exec()` appends the child's raw stdout and stderr to the error. The published fix routes that output through the existing argument redactor. No run did.
- DeepSeek, run 1, weighed it and declined: "I'll skip child-output redaction to avoid scope creep and potential behavioral regressions". Later: "OK, skip child-output redaction. Final decision."
- DeepSeek, run 2, found the exact lines ("stdout/stderr are appended unsanitized") and then judged them "probably overkill and hidden tests unlikely".
- All three MiMo runs built a value-based secret registry: secrets are recorded where the product receives them, and every diagnostic is scrubbed of those values. MiMo, run 3: "Names are irrelevant by construction". A credential that first appears inside a child process's output was never registered, so it passes through.

The audit: the model "did not route the failed child command's captured stdout/stderr through secret redaction in the exec() error path".

### 4.3 Left open: credential fields in HTTP diagnostics (JSON error text 5 of 6, request-body debug 4 of 6)

The two runtime sites print JSON that the product sends or receives, and the secret sits in a field.
- MiMo, runs 1 and 3, wrapped both sites in their registry scrubber (`debug(redactSensitiveValues(json!))`, `redactSecrets(...)`). The field values in a request or response body were never registered, so they still printed.
- DeepSeek, run 3, passed the request body through the existing name-based redactor (`safeStringifyJson(data)`), which closed the debug output. For the error it did the same with the error description. That description is a string with the server's JSON body inside it, so a name-based redactor never sees the fields. DeepSeek run 1 noticed exactly this ("Because description is a *string*, the replacer sees root name \"\" …") and added value redaction. It is the only run that closed both sites.
- DeepSeek, run 2, judged the request body out of scope: "Could a configured secret be in the body? … no token. Fine."

### 4.4 Left open: header spellings (1 of 6)

MiMo, run 1, matched credential header names by whole segments. Some of the tested case and separator spellings still reached the other origin. All other runs closed this test.

### 4.5 What they got right

Every run fixed the advisory's main example and the updater's full download, removed the token from all three publishers' errors, and fixed all three sites in the added Gitea publisher. No run broke a same-origin redirect, the http→https upgrade, ordinary headers or any of the project's own tests. The failures are not about understanding the bug. They come from how far the rule reaches: request paths outside the shared helper, and output the product did not write itself.

### 4.6 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (19–24 minutes, 139–173 turns). It audits widely and names the remaining paths. It then rules them out on assumptions it does not test: that the Electron runtime strips credentials, that the hidden tests cannot reach Electron, or that a fix is scope creep.
- **MiMo-V2.6-Pro:** slower (39–112 minutes, 88–195 turns). It looks for one general mechanism and builds a secret registry. The registry is general in name but only covers values the product registered at intake. In run 3 it converted error construction across the whole product to its redacting factory, and still missed the command output and the JSON fields.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro. 3 counted runs each, 2 hours per run.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has one local commit and no upstream history. The hidden tests are copied in only after the agent stops.
- The counted runs used the build version of the task. The delivered package has the same report and the same tests. It grades in a separate container that applies only the agent's source diff.
- Every counted run was audited before it counted:
  - no access to the hidden tests and no lookups (none of the hidden suite's markers or helper names appear in any transcript);
  - no tool calls during grading;
  - the same task checksum across all six runs;
  - the score reflects real defects in the model's code.
- What counts: a timeout counts as a failure (none occurred). A run cut off by a provider or network outage is not counted (none occurred).

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, an alternative design and a hardened fix score 1.0. Before the runs, one wrong-fix patch per route showed that each route's tests catch exactly that route, and three over-broad fixes showed that the functional tests catch over-hardening. After the runs, a fairness review and a human review checked the tests against the report, and a separate audit attributed every run to model failure with high confidence. In several runs the model found the path it left open and gave a reason for leaving it (section 4).

**Doesn't Electron strip the credential itself?** The tests use an in-process stand-in modelled on Electron 39's request redirect behaviour, and the human review accepted it. The verdict does not depend on that question. The multi-range test, failed by all 6 runs, uses an application-specific header (`X-Api-Key`), and DeepSeek itself noted that application-specific tokens "wouldn't be stripped" by the runtime. Every run also fails the command-output tests, which involve no Electron code.

**Does it hinge on one test?** No. Every run failed at least 5 tests in at least two independent areas. Remove all the block-based download tests, or both command-output tests, and all 6 runs still score below 1.0.

**Could the model have seen the answer?** The block-based download paths and the Gitea publisher are not in the published fix. The agent had no internet access beyond the model API, no web tools, and no access to the hidden tests. The audit checked every transcript for this.

**Was this always a two-model failure?** No. An earlier version had a more specific report that named the scenarios, and 16 security tests. DeepSeek failed it in 3 of 3 runs, but MiMo solved it on its second attempt. The delivered version states the rule in general terms and adds two real routes (the embedded block map and the updater's full download). Every counted run fails tests that were already in the earlier version.

**What does a 0.72 or a 0.61 mean?** 0.72 means 13 of 18 attack tests were blocked, and 0.61 means 11 of 18, with nothing broken in either case. No run scored 0.0, so no run broke a legitimate behaviour.

## Appendix

**Task package** (`tasks/electron-builder-credential-exposure/`):

| What | Contents |
|---|---|
| `instruction.md` | the report given to the agent |
| `environment/` | Dockerfile (electron-builder at 8a035f8, historyless) and `injection.patch` (the Gitea publisher and its dispatch wiring) |
| `solution/` | `fix.patch` (reference fix) and `solve.sh` |
| `tests/` | 5 security and 4 functional vitest files, 3 project test files with a snapshot, the loopback server harness and the Electron stand-in, `score.py`, `test.sh`, and the grader's Dockerfile |
| `task.toml` | metadata (CWE-200, advisory, commits), 2-hour agent limit, offline agent, separate verifier |

**Internal slug:** `electron-builder-ds`.

**Sources used:**
- the delivered task and its RESULTS.md and README.md entries;
- the build record (manifest, notes, both fairness reviews, human review, gate logs and the patch-stage gate report of 2026-10-20, the 18 check patches, trial logs);
- the six counted runs, each with its result, per-test results, transcript and audit:
  - `electron-builder-ds-deepseek-r1-20261020-074655-n001`
  - `electron-builder-ds-deepseek-r2-20261020-081533-n002`
  - `electron-builder-ds-deepseek-r3-20261020-083617-n003`
  - `electron-builder-ds-mimo-r1-20261020-085635-n004`
  - `electron-builder-ds-mimo-r2-20261020-094957-n005`
  - `electron-builder-ds-mimo-r3-20261020-103026-n006`
