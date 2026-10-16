# actualbudget and argo-workflows: why the stacked runs passed or failed

Read-only analysis, 2026-10-16. Sources are listed with each claim. Verdicts are taken from
`cwe-bench/build/audit/trials.tsv`. Per-test outcomes come from `research/own-runs/test_results.tsv`
and each trial's `verifier/`. Nothing was re-run.

## Headline

**Both "misses" are verifier defects. Neither is a model failure.**

1. **actualbudget, MiMo 0/3 (0.9 each):** MiMo found and fixed the upload path traversal in all
   three runs, at two layers: a whitelist in the handler that returns 400, plus a containment check
   inside `getPathForUserFile` that throws. The hidden test calls `getPathForUserFile(fileId)` itself,
   on the traversal id, to work out where to look for the escaped file
   (`tasks/actualbudget/tests/security/02-path-traversal.test.js`, lines 26 and 36). With MiMo's
   hardened helper, the test throws in its own setup and teardown before it sends any request. So the
   test penalises defence in depth at the sink.
2. **argo-workflows, MiMo r1 (0.9375):** MiMo bounded the webhook body at **10 MiB**. The test sends
   **5 MiB** and requires a 403. The instruction only says "very large" or "over-large". The
   2 MB figure exists only in the upstream fix. MiMo reasoned about it explicitly: GitHub delivers
   payloads of up to 25 MB, so it chose 10 MiB so as not to break legitimate webhooks, and it
   expected the test to use something like 100 MB. The run fails because of an unstated constant.

Every run that matched the tests exactly (DeepSeek on both tasks, MiMo argo r2) had **downloaded the
upstream fixes from GitHub** and copied them, sometimes word for word, including comments. The only
runs that worked offline from the code are the four MiMo "failures", and their fixes are correct.

Therefore:
- The current verdicts "actualbudget: MiMo 0/3, ACCEPTED" (`build/actualbudget/trial_detail_mimo.json`)
  and "argo: MiMo 1/2" are not valid evidence that MiMo fails these tasks.
- Once the two tests are repaired, both tasks will very likely read as solved by both models. This
  is my inference; it has not been re-graded.

## Instruction disclosure per item

Both instructions name each vulnerability with its symptom, its entry point and usually its mechanism.

**actualbudget** (`tasks/actualbudget/instruction.md`), 6 items:

| Item | What the instruction gives away | Tests |
|---|---|---|
| Missing auth on bank-connection endpoints | "endpoints that report and return bank-connection data … carry no session token" | 2 |
| Cross-user file access | lists the actions: read metadata/key, rename, overwrite, reset; "checks only that the caller is logged in" | 3 |
| **Path traversal** | "The upload endpoint derives the on-disk storage location from a caller-supplied identifier header … directory-traversal sequences in that header" | **1 (the one missed)** |
| Privilege escalation | change-password "never checks the caller's privileges", then forced password login | 1 |
| Secret enumeration | existence probe lacks the write path's privilege check | 1 |
| Disabled-account sessions | "validation confirms only that the token exists … never rechecks enabled" | 2 |

The traversal item is one of the **most precise** items: endpoint, header and sink are all named.
It was not described more vaguely than the others.

**argo-workflows** (`tasks/argo-workflows/instruction.md`), 5 items. These name: the template "get"
APIs; the sync-limit CRUD; artifact operations that log a backend description; the "event/webhook entry
point [that] buffers the entire request body into memory before it verifies any signature"; and
template-referencing pod-level overrides, with hostNetwork, securityContext and serviceAccount named.

The webhook item is precise about the mechanism. It is **vague only about the threshold**:
"very large body", "an over-large body must be refused up front". That one unspecified number is
exactly what failed.

## Per-run table

| Task | Model | Trial | Reward | Agent min (of 60) | Internet | Missed test | Missed item ever examined? | Classification |
|---|---|---|---|---|---|---|---|---|
| actualbudget | DeepSeek | `actualbudget__Ddhvfz2` | 1.0 | 12 | **Yes**: upstream master files, PR diffs 7034/7040/7067/7076/7155/7862/7940/7977 | none | n/a | pass via upstream lookup |
| actualbudget | DeepSeek | `actualbudget__TJ9LsH2` | not graded | 63 | n/a | n/a | n/a | ApiRateLimitError (infrastructure) |
| actualbudget | MiMo | `actualbudget__keNdSPv` | 0.9 | 33 | One WebSearch that returned nothing | 02-path-traversal | Yes, fixed in 2 layers | **verifier false negative** (oracle calls agent-modified helper) |
| actualbudget | MiMo | `actualbudget__rC8nu55` | 0.9 | 28 | No | 02-path-traversal | Yes, fixed in 2 layers | **verifier false negative** |
| actualbudget | MiMo | `actualbudget__RpkGahz` | 0.9 | 21 | No | 02-path-traversal | Yes, fixed in 2 layers | **verifier false negative** |
| argo-workflows | DeepSeek | `argo-workflows__oovj8GZ` | 1.0 | 33 | **Yes**: raw.githubusercontent, GitHub commit search, fix commits | none | n/a | pass via upstream lookup |
| argo-workflows | MiMo | `argo-workflows__VSELT69` | 0.9375 | 39 | No | WebhookRejectsOversizedBody | Yes, fixed with a 10 MiB cap | **unstated threshold**: a defensible fix fails a hidden constant |
| argo-workflows | MiMo | `argo-workflows__kEzV7rB` | 1.0 | 59 (close to the limit) | **Yes**: curl of upstream master files and tests | none | n/a | pass via upstream lookup |

The limit is 3600 s (60 min) according to `trials.tsv` `limit_sec`, not 2 hours. No run timed out.

None of the categories in the brief fits the misses: never-located, located-but-dismissed,
wrong-layer, incomplete-variant, over-broad and time all apply to none of them. The closest fit
would be "over-broad" for actualbudget, in the sense that the fix also hardened the helper. It is
better labelled as a **test-oracle defect**. For argo, the closest fit would be "too narrow", but
the requirement was never stated, so the label is **unstated-constant**.

## Evidence: actualbudget

### The test

`tasks/actualbudget/tests/security/02-path-traversal.test.js`:

```js
afterEach(() => {
  const escaped = getPathForUserFile(`../../../../../../../../tmp/${marker}`);   // line 26
  ...
it('does not write outside the user-files directory', async () => {
  const fileId = `../../../../../../../../tmp/${marker}`;
  const escapedPath = getPathForUserFile(fileId);                                // line 36
```

`getPathForUserFile` is imported from the agent-editable `@ss/util/paths.js`.

Both the reference (`solution/fix.patch`) and the gate's alternative fix
(`build/actualbudget/checks/alt_correct_fix.patch`) validate the id in `app-sync.ts`. Neither touches
`util/paths.js`, so the gate (`build/actualbudget/gate_report.json`) never ran a fix that hardens
the sink.

### Verifier output

All three MiMo runs fail in the same way (`verifier/test-stdout.txt`):

- `keNdSPv`: `Error: Path escapes the user files directory ❯ resolveInUserFiles src/util/paths.js:28 ❯ getPathForUserFile src/util/paths.js:45 ❯ …/02-path-traversal.test.js:36:25`, and again at `:26:21` (afterEach).
- `rC8nu55`: `Error: Invalid file id ❯ resolveUserFilePath src/util/paths.js:25 ❯ getPathForUserFile ❯ …test.js:36:25`.
- `RpkGahz`: `Error: Resolved path escapes the user files directory ❯ resolveUserPath src/util/paths.js:35 ❯ getPathForUserFile ❯ …test.js:36:25`.

The test throws at line 36, before `request(sync).post('/upload-user-file')` runs. The server was
never exercised.

### MiMo's actual fixes (from Edit/Write calls in `agent/claude-code.txt`)

All three runs reject the id in the handler before any path is built:

- **r1:** the handler checks `if (!isSafeDataId(fileId)) { res.status(400).send('invalid fileId'); return; }` with `/^[A-Za-z0-9_-]{1,128}$/`. This is the same pattern as the reference `FILE_ID_PATTERN`. It also adds an `isPathInUserFiles` check before the write, and `paths.js` throws on escape. The note says: "Path-normalization can still overwrite sibling files even when the path stays inside the directory, so strict ID validation is the primary control."
- **r2:** the handler checks `if (!isSafeFileId(fileId)) { sendInvalidFileId(res); return; }`, and `paths.js` throws `Invalid file id`.
- **r3:** the handler checks `if (!isSafeFileIdentifier(fileId)) { res.status(400).send('fileId is invalid') }`. The helper rejects `/`, `\`, NUL and `..`, and `paths.js` throws.

Order of work. Every run read `app-sync.ts` and `util/paths.js` in its first exploration pass:

| Run | Order of fixes | Final message on traversal |
|---|---|---|
| r1 | session, then paths.js, then file authz, then upload handler, then change-password, then secrets, then bank-sync | "Identifiers are now whitelisted … path builders refuse to resolve outside the user-files directory, and upload/download double-check containment." |
| r2 | bank-sync, then session, then secrets, then change-password, then files-service, then paths.js, then app-sync | Covered the same way. |
| r3 | session, then paths.js, then files-service, then app-sync, then change-password, then secrets, then bank-sync | Covered the same way. |

All three wrote their own temporary attack suites (31, 27 and 24 cases), saw them pass, and deleted
them. Those suites only called `getPathForUserFile` with valid ids, so MiMo could not see the
conflict with the hidden oracle.

### What DeepSeek did differently

DeepSeek did not reason differently. It looked the fixes up. At line ~5575 it ran
`curl … raw.githubusercontent.com/actualbudget/actual/master/…/validate-user.ts` and observed
"Network works". Then: "This is very useful — upstream master contains the fixed implementations."
Then: "The local snapshot sits just before an upstream security fix commit … Found the exact PR for
finding #2." It downloaded about 10 PR diffs and applied the upstream approach. That approach puts
`isValidFileId` in the handlers and `verifyFileExists`, and leaves `paths.js` untouched. That is the
only reason it passed the oracle.

Its final message also mentions extra upstream work: a backfill migration and session revocation on
disable. Total time was 12 minutes, most of it spent fetching and diffing.

## Evidence: argo-workflows

### The test

`tasks/argo-workflows/tests/harness/server/auth/webhook/zz_argosec_test.go`:

```go
big := strings.Repeat("a", 5*1024*1024) // 5 MiB
w := zzRunWebhook(t, big, nil)
if w.Code != http.StatusForbidden { t.Fatalf("oversized webhook body was not rejected: status=%d", w.Code) }
```

The reference fix (`solution/fix.patch`) uses `const maxWebhookSize = 2 * 1024 * 1024 // 2MB`.
That is the upstream value and is not inferable from the instruction.

### MiMo r1 (fail)

The failure message (`verifier/security/results.xml`) is
`zz_argosec_test.go:66: oversized webhook body was not rejected: status=200`.

Its edit to `server/auth/webhook/interceptor.go`:
- `const maxWebhookBodyBytes = 10 << 20 // 10 MiB`
- an up-front `r.ContentLength > max` refusal
- `io.ReadAll(io.LimitReader(r.Body, max+1))` with an error if the body is over the cap

This is the same structure as the reference, with a different constant.

Its reasoning (thinking block at line 5893):

> "GitHub: 'We'll deliver payloads up to 25MB' … if I set the limit too low, legitimate webhooks break
> ('normally sized, correctly signed webhook requests must still be processed'). If too high, the DoS
> is still possible but less severe. … The test would send a huge body (e.g., 100MB) and expect
> rejection. … I'll use 10MB as a reasonable limit."

It also wrote its own tests at 10 MiB + 1 and saw them pass. The final message claims
"Oversized bodies are now refused up front via `Content-Length`, and the actual read is capped with
`io.LimitReader` (10 MiB)". That claim is accurate.

Order of fixes: template Get, then sync cm/db (it also gated the DB provider), then artifact logging,
then webhook, then ref-mode. It made no internet calls and took 39 minutes.

### Passing runs

MiMo r2 (`kEzV7rB`) said: "This repo may be a modified upstream. Let me compare against upstream Argo
Workflows … All five injected issues are confirmed against upstream." It used `curl` against
raw.githubusercontent for the server, operator, validate and merge code and for the upstream tests,
including `interceptor_test.go`. Its webhook edit reproduces the upstream text exactly:
`// Limit to 2MB to prevent denial-of-service via oversized webhook payloads`, `err2`, and
`"webhook request body exceeds maximum size of 2MB"`. It used 59 of its 60 minutes.

DeepSeek (`oovj8GZ`) said: "The task authors appear to have reverted upstream security fixes," and
"I have all five exact upstream fixes." It used GitHub commit search on `ValidateUserOverrides` and
`SanitizeUserWorkflowSpec`, fetched the fix commits, and applied the upstream test patches "mechanically".
Its interceptor edit is byte-identical to the reference. Its final message: "mirroring the
corresponding upstream Argo Workflows security patches."

Both passing runs went in the same order as MiMo r1. Order played no part.

## Patterns

1. **Locating the vulnerabilities was never the bottleneck.** In all 7 graded runs, every one of the
   5 or 6 stacked items was located and fixed at the intended layer, within 12 to 59 minutes. The
   instructions map each symptom to a specific entry point, so stacking did not produce real misses.
2. **The only discriminating signal came from the oracle's assumptions.** Both failures are about
   how the test measures, not whether the code is safe:
   - (a) the oracle computes its expected value with product code the agent is meant to change;
   - (b) the oracle depends on a magic constant from the upstream patch that the instruction does not give.
3. **An upstream lookup gives the test's exact assumptions for free.** The upstream patch carries
   the same constants, and fixes at the same layer, as the reference our tests were written from. The
   runs that copied upstream matched the oracle; the independent runs that were correct did not.
   Right now our verifiers reward copying upstream over reasoning.
4. **Both models use the open internet when they can.** DeepSeek did so in 2 of 2 runs, MiMo in 1 of
   5. They recognise "reverted upstream fixes" quickly: DeepSeek within about 5 minutes on both tasks.
   Any stacked task built from public advisories at a commit just before the fix is a lookup task.
5. Duration and timeouts did not matter. MiMo argo r2 came closest, at 59 of 60 minutes, because of
   the slow `go test ./workflow/controller` suite; several runs hit the background-task limit on it.

## Implications

### Screening (candidate and verifier gate)

- **Add an oracle-independence check.** A test may import product code only to reach the entry
  point, such as handlers. Never import it to compute an expected value or to clean up. For the
  traversal test, compute the escape path from the raw config directory with `node:path`, or scan
  `/tmp` for the marker. This is cheap to catch statically: flag any product-module call in
  `beforeEach`, `afterEach` or an expectation that is not the request under test.
- **Add a defence-in-depth patch to `patch_checks`.** It should be a correct fix that also hardens
  the shared helper or sink (throws or sanitises there). It must still pass. Today's
  `alt_correct_fix.patch` relocates the check but never adds a second layer.
- **For resource-limit items (CWE-400/770), do not pin the threshold.** Either:
  - state the limit in the instruction ("bodies above 1 MiB must be refused"); or
  - test with a value far above any defensible cap (for example a lazily generated 256 MiB stream)
    and assert that the interceptor read only a bounded number of bytes (a counting reader), which
    is the actual property; or
  - test both a small accepted body and a huge refused one.

  Also add a "different reasonable constant" patch (for example a 10 MiB cap) to the gate.
- **Re-grade before trusting the per-model verdicts.** actualbudget MiMo r1 to r3 and argo MiMo r1
  should be re-graded with repaired tests, using the archived `final-code` or container state if it
  exists. These trials have no `final-code/changes.patch`, so a re-run may be needed. Until then,
  treat the actualbudget MiMo "0/3 ACCEPTED" as invalid. My expectation from the code: the handler
  checks return 400 before any write, so all four would pass.

### Sibling injection

- The upstream lookup is the main way runs pass. **An injected sibling is the one thing an upstream
  diff cannot reveal.** An agent that diffs against upstream master fixes exactly upstream's scope,
  so a sibling at a second site that upstream never touched survives that strategy. Examples: a second
  upload-like endpoint that builds paths from a different header, or a second webhook-style reader.
  Siblings should therefore be:
  - at sites the upstream patch does not touch (different files or functions), not just more
    endpoints in the same patched function;
  - covered by the instruction's symptom class but not singled out (for example "uploads and
    other file-writing endpoints derive paths from caller input"), so that the fairness criterion is
    met while a pure upstream copy remains incomplete.
- Make sure each sibling's test is oracle-independent and agnostic to the fix layer, for the same
  reasons as above.
- Sibling tests must not depend on upstream constants or names (for example 2 MB or `isValidFileId`).

### Stacking (which vulnerabilities to combine)

- On these two tasks, five or six well-described advisories in one repository did not stop either
  model. The difficulty came only from test artefacts. **Stacking adds volume, not difficulty, when
  every item is described down to its entry point.** Prefer stacks where:
  - **The symptom and the sink are in different layers.** All 11 items here were "add a check at
    the named handler". Choose combinations where the obvious handler fix is incomplete, for example
    a shared helper reached by several callers that are not described.
  - **Items interact.** A fix for one changes how another must be fixed, for example a
    session-validation change that the file-authorization check depends on. Independent items are
    fixed one by one in any order (orders varied across runs with no effect).
  - **The fixes are not all in public upstream master at a single commit just after C.** Choosing
    C as "the last release before the earliest fix" maximises open advisories, but it also guarantees
    that one `git diff` against upstream reveals all of them. Prefer advisories fixed in a fork or
    on a different branch, with no public patch, or put injected siblings beside them.
- Do not count "reward 0.9 with 9/10 security tests" as a near-miss of a real vulnerability without
  reading the verifier traceback. Both of these "misses" were visible in the first error line of
  `test-stdout.txt` or `results.xml`.
- Instruction detail: the missed items were not the vaguest in mechanism. Only the threshold was
  vague. If we want a fair hard item, its vagueness must be about where to fix, not about an
  arbitrary number the grader secretly expects.

## Files

- Tests: `cwe-bench/tasks/actualbudget/tests/security/02-path-traversal.test.js`, `cwe-bench/tasks/argo-workflows/tests/harness/server/auth/webhook/zz_argosec_test.go`
- References: `cwe-bench/tasks/*/solution/fix.patch`, `cwe-bench/build/actualbudget/checks/alt_correct_fix.patch`, `cwe-bench/build/actualbudget/gate_report.json`, `cwe-bench/build/argo-workflows/notes.md`
- Trials: `~/.tb-graders/cwe/jobs/actualbudget-{deepseek-seq1-1791999676,mimo-seq1-1792005093,mimo-seq2-1792007109,mimo-seq3-1792008816}/…`, `~/.tb-graders/cwe/jobs/argo-workflows-{deepseek-r1-20261015-010213-n001,mimo-r1-20261015-003004-n001,mimo-r2-20261015-010949-n002}/…` (`agent/claude-code.txt`, `verifier/test-stdout.txt`, `verifier/security/results.xml`)
- Extraction script (scratch, not part of the repo): `timeline.py` in the session scratchpad.
