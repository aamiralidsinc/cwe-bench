# tinacms-storage-path-traversal — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness review, every counted run's transcript, final code and per-test results, and the independent audit of every counted run.

## Summary

- **Result: both target models failed all 3 counted runs.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.97, 0.0, 0.0.
- Every run finished on its own (no timeout): DeepSeek in 10–12 minutes, MiMo in 68–112 minutes of a 2-hour limit.
- Every counted run was audited independently and judged a genuine model failure with high confidence.
- Why both fail: every run found and guarded every route, but none applied the rule exactly at its edges. All 6 runs let an upload directory with a leading separator through on the Azure backend. 5 of 6 broke a legitimate listing request next to the rule.

## 1. The task

**Vulnerability (CWE-639, authorization bypass through a user-controlled key).** TinaCMS (TypeScript) is a content platform with a media manager. Its server-side media API takes an object key or directory from the signed-in editor and hands it to the configured cloud storage backend. The operator can set a media root, the prefix where the site's media lives. At the vulnerable commit, the first-party storage adapters pass the caller's key to the storage SDK without confining it. An editor can therefore get a presigned upload URL for, delete, or list objects anywhere the storage credential can reach.

**Base advisory:** GHSA-8MQ9-5FW2-5RM4 (CVE-2026-59992). Vulnerable commit d08ffb4, upstream fix d44558e ("Fix media mediaroot key scoping (#7088)"). The upstream fix resolves every key and directory against the root in the four adapter handler files. It returns 400 for absolute, traversal, NUL/backslash, empty or escaping values.

**What the task contains.** Six routes to the same rule:

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| 1. S3 adapter: presigned upload `?key=`, single delete, listing (the report's example) | upload URL, delete or listing outside the media root | deleting the identifier the listing returned (no second root prefix); literal `%` names; an inner `..` that stays inside; directories with leading/trailing slashes | advisory's own route |
| 2. DigitalOcean Spaces adapter: multipart upload (directory + file name), delete with the key split across route segments, listing | the same, through a second implementation | uploads with slashes around the directory; split-segment delete; deleting a listed identifier | real upstream code covered by the advisory fix |
| 3. Azure Blob and Cloudinary adapters (no media-root option) | absolute or climbing keys and directories reach the storage service | upload into a folder; delete by name; list the root and a folder | real upstream code covered by the advisory fix |
| 4. S3 batch delete (a list of keys) | any key in the list escapes; a partial batch runs | deleting several listed identifiers | added for the task |
| 5. S3 app-router handlers (upload URL, direct upload, delete, listing) | the same as route 1 through a second router module | nested-key upload and delete; listing | added for the task |
| 6. DigitalOcean copy/move (source and destination) | either end of the copy escapes | copying between two keys inside the area | added for the task |

Routes 4–6 are new modules written in the style of the surrounding adapters and exported from each package's index. The upstream fix does not touch them.

**Report given to the agent.** It is written as a bug report. It describes the system and one example (an upload URL for a key outside the media area). It says the same unchecked value is used by delete, listing and the other backends. Then come the invariants. The key rule:

> "A key that is absolute (a leading separator or a Windows drive letter), contains a NUL byte or a backslash, is empty, or uses `..` to climb above the area is refused with a client error (a 4xx response). No storage operation may be carried out for such a value."

The rule holds "for every operation the media API exposes and every storage backend the project ships, including backends that have no configured root". It also covers every input shape: single value, list, split route segments, and multipart or form body. A "Keep working" list protects ordinary use: listed identifiers are not prefixed twice; literal `%` is not decoded again; an inner `..` that stays inside is "collapsed, not refused"; split keys and "directories with leading or trailing slashes" work; the root of the area and any directory below it can be listed; copies inside the area work. No file, package, function, advisory or count is named.

**Hidden tests.** 73 security tests and 30 functional tests:

| Area | Security | Functional |
|---|---|---|
| S3 pages handler (upload / delete and listing) | 7 + 10 | 8 |
| DigitalOcean Spaces | 13 | 7 |
| Azure Blob | 11 | 4 |
| Cloudinary | 11 | 5 |
| S3 batch delete | 6 | 6 (all three added routes) |
| S3 app-router | 9 | |
| DigitalOcean copy | 6 | |

The tests import each adapter's exported handler factories and call them with plain request and response objects. The storage SDKs (AWS S3, Azure Blob, Cloudinary, multer) are replaced by in-memory stubs that record every operation. A security test passes when the request gets a 4xx and no storage operation runs. For an in-bucket key outside the root, the operation may instead be confined to the root. Any 4xx status is accepted.

Reward = 1.0 when every test passes. Otherwise the share of security tests passing, capped below 1. It is 0 if any functional test fails.

## 2. How we know the task is fair

Before any model ran:

| Check | Result |
|---|---|
| Vulnerable code (with the added routes) | fails all 73 security tests, passes all 30 functional tests |
| Reference fix (the upstream fix plus the same guard on the three added routes) | 1.0, three times, identically |
| Independent fix (a fresh agent given the report, the code and the locations of the added routes; completed by hand) | 1.0 |
| Hardening fix and an alternative correct fix, written differently from the reference | 1.0 each |
| The upstream advisory fix alone | not run as a separate check; each added route left unfixed fails, see below |
| One wrong-fix patch per route (7 patches: S3 upload, S3 delete/list, DigitalOcean, Azure + Cloudinary, app-router, batch delete, copy) | each fails the matching security tests (rewards 0.70–0.92) |
| Check made after joining with the root (the join collapses `..`) | fails 5 security tests |
| Only the first element of a repeated key checked | fails the list-input security test |
| Over-broad fix (refuses legitimate shapes) | fails 20 functional tests, reward 0 |

All 12 wrong-fix and alternative patches behaved as declared, in two separate gate runs (2026-10-18 and 2026-10-20).

After the runs, an independent fairness review checked every test against the report. Every security test maps to the invariants and every functional test to the "Keep working" list. Its verdict was READY. It rated four rows as alternative readings with low or medium risk:
- the Azure absolute upload directory;
- the Cloudinary leading-slash folder;
- the S3 empty `?key=`;
- the all-or-nothing batch refusal.

## 3. Results, attempt by attempt

| Model | Run | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 72/73 | 29/30 | Azure upload accepts an absolute directory | empty `?key=` no longer lists the root |
| DeepSeek | 2 | 0.0 | 72/73 | 26/30 | Azure absolute directory | empty-key listing; every DigitalOcean multipart upload (3 tests) |
| DeepSeek | 3 | 0.0 | 71/73 | 29/30 | Azure absolute directory; Cloudinary file name that climbs | empty-key listing |
| MiMo | 1 | 0.97 | 71/73 | 30/30 | Azure absolute directory; Cloudinary file name that climbs | nothing |
| MiMo | 2 | 0.0 | 71/73 | 26/30 | Azure absolute directory; Cloudinary file name | empty-key listing; every DigitalOcean multipart upload (3 tests) |
| MiMo | 3 | 0.0 | 69/73 | 29/30 | Azure absolute directory; Cloudinary file name; app-router listing (2 tests) | empty-key listing |

- All 6 runs closed the advisory's own route and both added S3 routes for upload and delete. All 6 also closed the DigitalOcean adapter, the batch delete and both ends of the copy.
- All 6 left the Azure absolute upload directory open. It is the only security test that fails in every run.
- 5 of 6 broke the empty-key listing on the S3 route. 2 of 6 broke ordinary DigitalOcean uploads.
- 4 of 6 accepted a Cloudinary file name that climbs (`../evil.png`).
- No single test decides any run. Removing any one test still leaves all 6 runs below 1.0.

## 4. Why both models failed

### 4.1 Left open: the Azure upload directory with a leading separator (6 of 6)

Every run built one shared helper that refuses absolute keys. Every run also let directories tolerate a leading slash, because the report says directories with leading slashes must keep working. On Azure, the upload directory `/etc` was stripped to `etc`, and the upload went ahead.
- DeepSeek, run 3, final summary: "Directories allow leading/trailing slashes and the root value; keys do not."
- MiMo, run 3, after its own harness expected a refusal: "`/etc/` as a *directory* is legitimate (leading slashes are tolerated)". It changed its expectations, not its code.
- The audit, for every run: the model's directory helper "tolerates a single leading slash … so `/etc` is stripped to `etc` and the blob upload proceeds". This violates "the stated absolute-refusal invariant" for backends with no root.

The reference, like the published upstream fix, joins the Azure directory and file name and validates the joined name. That name starts with a separator, so it is refused.

### 4.2 Broke: an empty key on the S3 route no longer lists the area root (5 of 6)

At the vulnerable commit, the S3 GET route sends a request with a key to presigning and everything else to listing. An empty `?key=` is therefore a listing request. Five runs rerouted it to the presign branch, where it is refused.
- DeepSeek, run 1, its own probe: "GET empty key 400 … GET list root 200".
- MiMo, run 2, listed it as a gap it closed: "an empty `?key=` on the GET route fell through to a listing instead of being refused".
- The audit: the model "changed the S3 GET routing from truthy `if (req.query.key)` to `if (key !== undefined)` … so an empty-string key now enters the presign branch and is rejected with 400, instead of falling through to list the media root".

MiMo run 1 kept the original routing and passes this test.

### 4.3 Left open: a climbing file name on Cloudinary (4 of 6)

DeepSeek run 3 and all three MiMo runs joined the folder and file name before validating, so `photos/../evil.png` collapsed to an in-area `evil.png`. The reference validates the file name on its own and refuses it. The audit rated this check an instruction ambiguity, against the "inner `..` is collapsed" rule. In every run it is not decisive: the same run also fails on other grounds.

### 4.4 Broke: ordinary DigitalOcean uploads (2 of 6)

DeepSeek run 2 and MiMo run 2 rewrote the multipart upload to take the file name from the form body instead of the uploaded file. Ordinary uploads supply no body file name, so every legitimate upload broke. The audit: the model took "the filename from `req.body.filename` instead of `path.basename(filePath)`". Sibling runs pass these exact tests.

### 4.5 Left open: one added route's listing (1 of 6)

MiMo run 3 guarded the S3 app-router listing with its directory helper but did not refuse an upward climb there, so `..%2F` and `..\outside` were still listed. Its pages-router listing in the same run is guarded.

### 4.6 What they got right

Every run found all six routes, including the three added ones. Every run hardened beyond the tests too: all six guarded the Azure read (delivery) handler, and most escaped quotes in the Cloudinary search expression. The failures are not about finding the bug. They come from applying the rule at its edges:
- refusing an absolute value where a "directories with slashes" rule pulls the other way;
- preserving a legitimate request shape that the new guard sits next to.

### 4.7 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (10–12 minutes, 139–173 turns). It builds one shared helper and wires it into every route. In all three runs it applied the helper's refusal of empty keys to the S3 listing route as well; run 1 asserted that result on purpose ("GET empty key 400").
- **MiMo-V2.6-Pro:** slower (68–112 minutes). It is thorough and writes large harnesses (86 checks in run 1, 232 in run 3). In run 3, when its harness expected `/etc` to be refused, it changed the expectation, not the code. In run 2 it treated the empty-key listing as a gap to close.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro. 3 counted runs each, 2 hours per run.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has one local commit and no upstream history. The hidden tests are copied in only after the agent stops.
- The counted runs used the build version of the task. The delivered package has the same report and the same tests. It grades in a separate container that applies only the agent's source diff.
- Every counted run was audited before it counted:
  - no access to the hidden tests and no lookups (none of the hidden suite's identifiers appear in any transcript);
  - no tool calls during grading, and the graded code equals the final code;
  - the same task checksum across all six runs;
  - the score reflects real defects in the model's code.
- What counts: the three runs per model on the latest task version. No run timed out and none was cut off by a provider or network outage, so all six count.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, an alternative and a hardened fix score 1.0. So does an independent fix, written from the report, the code and the locations of the added routes, and completed by hand. Before the runs, one wrong-fix patch per route showed that each route's tests catch exactly that route. After the runs, a separate audit read each transcript and final code, and attributed every run to model failure with high confidence.

**Does it hinge on one test?** No single test decides any run. Each of the 6 runs failed at least two tests, in at least two different backends. Removing any one test leaves all 6 runs below 1.0.

**Could the model have seen the answer?** Three of the routes are not in the published fix. The agent had no internet access beyond the model API, no web tools, and no access to the hidden tests. The audit checked every transcript for this.

**What does a 0.97 or a 0.0 mean?**
- 0.97 (MiMo, run 1) means 71 of 73 attack tests were refused, with nothing broken; two inputs still reached storage.
- 0.0 means a legitimate behaviour was broken, since any functional failure scores 0. Every 0.0 run also left at least one attack input open.

## Appendix

**Task package** (`tasks/tinacms-storage-path-traversal/`):

| What | Contents |
|---|---|
| `instruction.md` | the report given to the agent |
| `environment/` | Dockerfile (TinaCMS at d08ffb4, historyless) and `injection.patch` (the three added routes) |
| `solution/` | `fix.patch` (reference fix) and `solve.sh` |
| `tests/` | 8 security and 5 functional vitest files, SDK stubs, `score.py`, and the grader's Dockerfile |
| `task.toml` | metadata (CWE-639, advisory, commits), 2-hour agent limit, offline agent, separate verifier |

**Internal slug:** `tinacms-ds`.

**Sources used:**
- the delivered task and its RESULTS.md and README.md entries;
- the build record (manifest, notes, fairness review, gate reports of 2026-10-18 and 2026-10-20, wrong-fix patches, trial detail);
- the six counted runs, each with its result, per-test results, transcript and audit:
  - `tinacms-ds-deepseek-r1-20261021-043049-n001`
  - `tinacms-ds-deepseek-r2-20261021-044142-n002`
  - `tinacms-ds-deepseek-r3-20261021-045241-n003`
  - `tinacms-ds-mimo-r1-20261021-050531-n004`
  - `tinacms-ds-mimo-r2-20261021-061354-n005`
  - `tinacms-ds-mimo-r3-20261021-080649-n006`
