# Validity concerns found while writing the 13 breaker reports (internal, 2026-10-21)

The reports in `breakers/13/` describe the 13 tasks delivered to the client in `cwe-client/repo`
(commits d3e00f6 and ea4ce53). By design they contain no caveats. Everything the 13 report agents
found that could affect a verdict is listed here instead. This file stays internal and is not part
of `breakers/13/`.

## Verdict status per task

| Task | Status | Why |
|---|---|---|
| jackson-databind-jsonview-bypass | **holds** | instruction, tests and reference byte-identical to what was run; 6/6 audited trustworthy |
| electron-builder-credential-exposure | **holds** | real leaks left open in every run (multi-range download, failed-command output); no functional failure |
| hubuum-error-log-secret-exposure | **holds** | one coupled functional test decides all runs, but it checks a stated contract (task id and status stay visible) |
| mockoon-admin-api-missing-auth | **holds** | each model's 0/3 rests on the copied-credential test, which fits the stated rule; no functional failure |
| seaweedfs-table-storage-authz | **holds** | the listing rule is ambiguous (an empty list is allowed by the instruction, rejected by 2 tests), but MiMo r2 still has 2 real leaks without them |
| theia-workspace-trust-bypass | **holds, with a shaky harness** | genuine misses in every run. But: one test needs `onDidChangeCanRun`, a name the instruction dropped; functional/02 skips the flush; the AI-enable setting is unscoped; PreferenceService is stubbed. Some runs lost points to these as well. |
| siyuan-unpublished-resource-exposure | **at risk (DeepSeek)** | the fixture snippets leave `Enabled` false, which contradicts the instruction (every run fails 3-4 functional tests on it; other real failures remain). DeepSeek r3 grading crashed (server panic; only 6/20 security tests ran), so DeepSeek's 0/3 rests on 2 proven runs plus 1 undetermined. The Dockerfile timestamp reveals the injected file. |
| protobufjs-prototype-pollution | **at risk (DeepSeek)** | DeepSeek r3 (0.91) fails only the two points sent to human review; HUMAN-REVIEW.md says the instruction contradicts itself on one. Read the other way, DeepSeek is 1/3. |
| knowns-memory-id-path-injection | **at risk (both)** | the trailing-dot memory id `zzbad.` alone decides DeepSeek's 0/3, and MiMo's with r3. The id fits the report's own keep-working character set and is written inside the folder; NEEDS_HUMAN_REVIEW was not resolved. Also a test-isolation bug: a leftover file makes the backslash and colon cases look missed (the runs still fail at 26/28 when fixed). |
| tinacms-storage-path-traversal | **at risk (DeepSeek)** | DeepSeek r1 fails only two tests that contradict the instruction: an empty key must be refused with a 4xx, yet a functional test requires root listing; a leading slash is accepted for DigitalOcean and Cloudinary but must be refused for Azure. Without them, DeepSeek is 1/3. |
| yamcs-subscription-authz-bypass | **at risk (DeepSeek)** | `authorizedContainerSubscriptionStillDelivers` seems to contradict the report's first rule (no feed may deliver an item the caller would be refused through the ordinary read). Without it, DeepSeek r1 and r2 score 1.0. |
| openbao-identity-template-injection | **at risk (MiMo)** | the instruction lists "the path separator" as a metacharacter with no qualifier, yet two keep-working tests require a substituted `/` in certificate URI names; the fairness review asked for a rewording, which was never made, and models quoted the instruction. Without those tests, MiMo is 2/3. The default-user comma test is also unstated. |
| litellm-outbound-destination-ssrf | **not a breaker on this evidence** | the instruction says configured credentials "must never be sent to a destination the request chose"; `test_operator_opt_in_restores_inheritance_for_a_caller_endpoint` requires the opposite under the opt-in. Every run fails it, and 5 of 6 fail only it. Without it, DeepSeek scores 1.0 ×3 and MiMo solves 2/3. The audits misread the clause. |

## Cross-cutting issues

1. **No delivered package was re-run.** All counted runs were graded in shared mode with a model
   allowlist. The delivered tasks use a separate verifier, `no-network`, and in places different
   verifier timeouts. No gate or reference-fix run in the delivered format is recorded for any of
   the 13.
2. **Time limit misstated.** The counted runs had a 3 h agent limit (multiplier 1.5). The delivered
   `task.toml` says 7200 s, and RESULTS.md says runs finished "within the 2-hour budget". Runs
   longer than 2 h: protobufjs MiMo r1 (178 min) and seaweedfs MiMo r3 (156 min). litellm's MiMo
   runs and yamcs MiMo r1 also ran at the limit.
3. **"Independently-written correct fix" is claimed for every task, but none was run** for mockoon,
   protobufjs, litellm or theia. Where one was run, some were written with the private trap list.
   That is acceptable as a control under our fairness rule, but it does not match the word
   "independent" in RESULTS.md and the README.
4. **Human reviews flagged but not recorded as done** (fairness `NEEDS_HUMAN_REVIEW: YES`): yamcs,
   tinacms, knowns, openbao, hubuum, theia, protobufjs. Several fairness reviews were run by
   DeepSeek, not an independent model.
5. **Audit quality.** Templated or partly wrong audit text in hubuum, electron-builder and theia
   (MiMo r1). Wrong causes in siyuan (r3) and litellm (the misread clause). The verdict columns
   mostly match the per-test results; the explanations often do not.
6. **RESULTS.md wording** to correct:
   - litellm: "missing routes" (DeepSeek passed 21/21 security);
   - seaweedfs: MiMo "always" left the name-only route open;
   - tinacms: "every failing check passes in at least one sibling run" (Azure `/etc` fails 6/6);
   - knowns: spellings reported missed that were refused.

## Suggested next steps (not done; need a decision)

1. **litellm:** withdraw it, or fix the test so it follows the instruction and re-trial.
2. **The five at-risk tasks** (yamcs, tinacms, knowns, openbao, protobufjs; siyuan's DeepSeek side):
   - resolve each contradiction the way we settled it on 2026-10-20: keep the instruction, change the
     test and the reference;
   - finish the open human reviews;
   - re-trial the affected model.
3. **Re-gate all 13 in the delivered format:** nop, oracle and patch checks under the separate
   verifier.
4. **Correct RESULTS.md and the README in `cwe-client/repo`:** the time limit, the
   independent-fix claim, and the wording in issue 6.
