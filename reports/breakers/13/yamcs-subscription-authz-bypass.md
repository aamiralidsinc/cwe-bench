# yamcs-subscription-authz-bypass — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness review, every counted attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- DeepSeek finished on its own in 25–32 minutes. MiMo took 56–59 minutes in two attempts and reached the 2-hour limit in the third, which was graded on the code it had left.
- Each attempt was audited independently and judged a genuine model failure with high confidence.
- Every attempt closed every leak (10/10 security tests), and every attempt then broke a legitimate live feed, which scores 0.
- Why both models fail: the task requires authorizing each packet under one name while leaving the name a client sees, and the authorization of a neighbouring feed, as they are today. Each model applied its new authorization key one step too far:
  - DeepSeek also filtered a second feed by that key.
  - MiMo also relabelled the packets it delivers.

## 1. The task

**Vulnerability (CWE-862, missing authorization).** Yamcs is a mission-control server (Java). Roles grant system-wide privileges and per-object privileges, such as read access to named telemetry packets. The ordinary request/response reads check these privileges. Several live websocket subscriptions do not, so a caller receives live data it would be refused through the ordinary read.

**Base advisory:** GHSA-FWWW-CP23-7F5G (CVE-2026-55545). Vulnerable commit b566bece (b566beceba98cc35514b0e1519be126b8c5a0438), upstream fix 0691731 (the same change exists on a maintenance branch as 12864af). The upstream fix adds no tests.

**What the task contains.** Eight routes to the same rule:

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| 1. Live packet feed of a processor | every packet, including families the role excludes | a caller authorized for a subset still receives those packets, labelled as today | advisory's own route |
| 2. Packet feed read from a raw stream | raw packet bytes to a caller with stream access but no table-read privilege | a caller with both still receives rows | advisory's own route |
| 3. Mission-database override notifications | override changes to a caller without the mission-database privilege | a holder of that privilege still receives them | advisory's own route |
| 4. Live algorithm status | status of an algorithm the caller may not read | a reader of that algorithm still follows it | advisory's own route |
| 5. Generic stream subscription | the same packet-bearing rows, gated only by stream access | a caller with stream access and table-read privilege still receives rows; a stream-only caller can still describe the stream | real upstream code the fix left open |
| 6. REST override readers (list all, read one algorithm's text) | active overrides to a caller with no privilege | the mission-database holder lists them; an algorithm reader reads that algorithm's text | real upstream code the fix left open (upstream changed these readers later) |
| 7. Container subscription | any named container's bytes, with no request-time check | a caller authorized for the named container still receives it | code added for the task (an existing check removed) |
| 8. Command-history update entries | update entries for commands the caller may not read (creation entries are already filtered) | a caller authorized for a command receives both its creation and its update entries | code added for the task (an existing check removed) |

The two added routes (7 and 8) are applied as a small patch to the task's copy of the repository. In both, a check that exists upstream is removed, on a real websocket topic.

**The coupled value on route 1.** Packets on the processor feed are labelled with the root container name (`/REFMDB/ccsds-default`). The ordinary packet reads authorize a packet under the name it is archived under. For example, PKT1_1 is archived under its own name, while PKT1_3 is archived under the root name. A correct fix:
- authorizes each packet under its archived name;
- keeps today's label on what it delivers;
- keeps the container subscription authorized on the container names the caller requests.

**Report given to the agent.** It is written as a bug report:
- the system;
- one observation: a role limited to one packet family received every packet on the live packet feed, and "other live feeds behave the same way";
- the rules:
  - the first is "No live subscription may deliver an item that the same caller would be refused when requesting it through the corresponding ordinary read";
  - further rules cover per-object filtering, whole-subscription refusal, raw stream data, mission-database overrides, algorithm status and command history.
- the contracts, including "Legitimate use must keep working exactly as it does today" and "A caller authorized for a subset of packets still receives those packets".

It also says "These examples describe the rule; they are not the complete set of places where it applies." No file, function, or count is named.

**Hidden tests.**
- 10 security tests and 9 functional tests:

  | Route | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|
  | Security tests | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
  | Functional tests | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |

- They start the real Yamcs server in-process with the project's own integration harness. They drive it with the real `yamcs-client` over a real websocket, and with the generated REST clients.
- Each test signs in as its own role-scoped user.
- Security tests assert that no protected item arrives. Where refusal is required, any client error is accepted.
- Reward:
  - 1.0 when all 19 tests pass;
  - otherwise the share of security tests passing, capped below 1;
  - 0 if any functional test fails.

## 2. How we know the task is fair

Final gate run, 2026-10-21, on the delivered tests:

| Check | Result |
|---|---|
| Vulnerable code | fails all 10 security tests, passes all 9 functional tests |
| Reference fix | 1.0, three times |
| Control fix written by a separate model (Opus 5.5) from the report, the code and the list of routes, without the tests | 1.0 |
| Fully blind fix (report and code only) graded on this test suite | not run |
| Alternative correct fix (different guard style and placement) and hardened fix | 1.0 each |
| A patch limited to the published fix's sites | 0.4: fails 6 of 10 security tests (generic stream, both override readers, override notifications, container subscription, command updates) |
| The upstream approach on route 1 (authorize each packet under the subscribed root container's name) | 0.0: leaks PKT1_1 to a root-name holder and drops authorized packets for a subset holder |
| One wrong-fix patch per route (reference minus that route), plus one that checks stream access instead of table-read privilege | each fails the matching security tests |
| Over-broad fixes: refuse the whole packet feed; tighten the shared stream lookup | fail the functional tests (authorized packet feed; stream description) |
| Fairness review of every test against the report | verdict READY; every test rated low or medium risk; no instruction/test contradiction found |

In total, 16 check patches behaved as declared, and the scripted gate passed.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 10/10 | 8/9 | nothing | container feed for a caller authorized on the requested container |
| DeepSeek | 2 | 0.0 | 10/10 | 8/9 | nothing | container feed (same) |
| DeepSeek | 3 | 0.0 | 10/10 | 7/9 | nothing | container feed; packet label on the processor feed |
| MiMo | 1 | 0.0 | 10/10 | 8/9 | nothing | packet label on the processor feed (reached the 2-hour limit) |
| MiMo | 2 | 0.0 | 10/10 | 8/9 | nothing | packet label |
| MiMo | 3 | 0.0 | 10/10 | 8/9 | nothing | packet label |

- All 6 closed all 8 routes, including the two added ones and the two real routes the upstream fix left open.
- All 6 broke a legitimate live feed.
- 4 of 6 (all three MiMo, DeepSeek attempt 3) changed the label on delivered packets.
- All 3 DeepSeek attempts over-restricted the container feed. No MiMo attempt did.
- No attempt was excluded: these 6 are all the attempts run on this task version.

## 4. Why both models failed

Nothing was left open, so every failure is broken legitimate behaviour. Both errors come from the same step. Each model correctly found that the ordinary packet reads key on the archived packet name (`deriveArchivePartition` in product code). It then applied that name beyond the authorization decision it was needed for.

### 4.1 Relabelling the delivered packets (MiMo 3 of 3, DeepSeek 1 of 3)

The live feed labels each packet with the root container name, and clients see that label today. The reference authorizes on the archived name and keeps the label. The failing attempts used one variable for both purposes.
- MiMo, attempt 3, in its final summary: "`TmPacketData.id` now carries that pname, matching `GPBHelper.tupleToTmPacketData` on the archive path." It had first checked "who consumes the live packet feed's ID field to assess changing it". It found the packet viewer as a consumer, and changed the field anyway.
- MiMo, attempts 1 and 2: the audit found the same code: "`.setId(setName(pname))`, wrong label". The authorized packet is delivered, but under a different name.
- DeepSeek, attempt 3: "The packet `id` now carries that derived packet name."

The report says that legitimate use must keep working "exactly as it does today". The audit notes that the repository's own public test (`XtceTmExtractorTest`) shows the same label convention.

### 4.2 Over-filtering the container feed (DeepSeek 3 of 3)

The container subscription asks for named containers. The reference checks, once and at request time, that the caller may read the names it requested. DeepSeek instead filtered every delivered container by the archived name of the packet it came from. A caller authorized on the requested root container therefore received nothing.
- DeepSeek, attempt 1: "each emitted container is filtered by `ReadPacket` using its packet's archived name; authorized containers keep flowing."
- DeepSeek, attempt 2: "`subscribeContainers`: per-item `ReadPacket` filtering using the derived packet name." This version also changed a shared extraction result class to carry the name.
- DeepSeek, attempt 3: "`subscribeContainers` applies the same per-item `ReadPacket` check on the derived archive partition".

All three MiMo attempts kept this feed working. In attempt 3, MiMo filtered it "by `ReadPacket` on its qualified name", which is the name the caller requests.

### 4.3 What they got right

Every attempt:
- closed the reported feed;
- closed both raw-stream routes with a table-read privilege, while keeping the stream description available;
- added the mission-database and algorithm checks to the override readers, notifications and status;
- filtered command-history updates per command.

Several attempts also audited unrelated APIs for the same pattern. The failures are not about finding the leaks: they come from changing behaviour next to a correct check.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (25–32 minutes). It reused one authorization key everywhere it could, including a feed whose existing authorization model is the requested name.
- **MiMo-V2.6-Pro:** slower (56–59 minutes, and one attempt reached the 2-hour limit). It kept the container feed on the requested names. It treated the packet label as something to make "consistent" with the archive, rather than as existing behaviour to preserve.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models:
  - DeepSeek V4.1 Flash, reasoning effort max;
  - MiMo-V2.6-Pro;
  - 3 counted attempts each, 2 hours per attempt.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history, and the hidden tests are not in the agent's environment.
- Every counted attempt was audited (Claude Opus 5.5, high effort) before it counted:
  - no access to the hidden tests and no lookups;
  - the graded code is the model's own work;
  - the score reflects real defects in that code.
- What counts:
  - An attempt that reaches the time limit is graded on the code it left and counts as a failure (MiMo, attempt 1). Its audit found no provider or infrastructure error.
  - An attempt cut off by a provider or network outage would not count. None occurred.
- The delivered package grades in a fresh container from the agent's collected patch. Its hidden tests and scoring are identical to those used in the counted attempts.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?**
- The reference, an alternative fix, a hardened fix and a control fix written by a separate model all score 1.0.
- The report states the contract the failing attempts broke: legitimate use must keep working "exactly as it does today".
- A separate audit read the transcript and code of each attempt and judged all 6 genuine model failures with high confidence.

**Does it hinge on one test?** Every attempt passed all 10 security tests, so every score of 0 comes from functional tests. Per model, the result rests on one legitimate behaviour:
- DeepSeek: the container feed in all 3 attempts, and the packet label as well in attempt 3;
- MiMo: the packet label in all 3 attempts.

Each failure is a real regression for an authorized caller.

**Could the model have seen the answer?** No.
- The upstream fix does not pass this task: its approach to the reported feed scores 0.0.
- It leaves the generic stream and the REST override readers open.
- The agent could not reach the internet or the hidden tests, and the audit checked every transcript for this.

**What does a 0.0 mean here?** All 10 attack routes were closed, but at least one authorized caller lost data it receives today (or received it under a different name). Any functional failure scores 0. A fix that closes every route and keeps every legitimate feed scores 1.0.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | report (`instruction.md`), `task.toml`, environment (Dockerfile and the patch that adds routes 7 and 8), reference fix (`solution/fix.patch`, `solve.sh`), hidden tests (`tests/`: 10 security and 9 functional tests, integration harness and role configuration, `test.sh`, `score.py`) |
| Validation | gate report, the 16 check patches (one wrong-fix patch per route, over-broad fixes, alternative, hardened and control fixes), the fairness review |
| Attempts | per attempt: score, per-test results, final code and the audit's findings |

Internal slug: `yamcs-ds`.

Sources used:
- the delivered task `tasks/yamcs-subscription-authz-bypass/`;
- its sections in `RESULTS.md` and `README.md`;
- the build record `build/yamcs-ds/` (`manifest.json`, `notes.md`, `FAIRNESS.md`, `gate_report.partial.json`, `recover.log`, `runs_*.log`);
- the final gate jobs (2026-10-21, 03:17–03:41 UTC);
- the six trial folders:
  - `yamcs-ds-deepseek-r1-20261021-043051-n001`, `-r2-20261021-050437-n002`, `-r3-20261021-053106-n003`;
  - `yamcs-ds-mimo-r1-20261021-060031-n004`, `-r2-20261021-080139-n005`, `-r3-20261021-090125-n006`;
  - for each: `result.json`, `verifier/results.json`, `POSTMORTEM.json` and `evidence/transcript.md`.
