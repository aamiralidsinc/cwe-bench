# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-social-core-5847`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 5847; Session fixation (CWE-384): login CSRF via cross-session resume of a s
- Pinned (vulnerable) commit: 6fcde2c2bf16b6fefb15316e4c9f7a9d9ddfd95b. Published fix: 0418782454ac7bbc6a9230ea21f7f5066fe89686.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-5847",
 "pattern": "H4",
 "repo": "python-social-auth/social-core",
 "pinned_commit": "6fcde2c2bf16b6fefb15316e4c9f7a9d9ddfd95b",
 "protections": [
  "A stored partial pipeline may be resumed only by the client session that created it: the resume token presented in the request must be bound to the token recorded in that session, not merely be a valid token for the same backend (social_core/utils.py:185-216).",
  "An intentional out-of-band resume (the emailed email-validation link opened in a fresh session) must keep working, and the allowance is recorded on that step's stored partial only rather than granted blanket (social_core/pipeline/mail.py:13-37, social_core/pipeline/partial.py:8-59).",
  "The ownership decision is applied at every resume sink (public utility, both framework actions, and backend continue_pipeline overrides), not only in the login action (social_core/actions.py:96-100, social_core/actions.py:176-182, social_core/backends/base.py:269-275, social_core/backends/open_id.py:189-200)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "social_core/utils.py:185-189",
    "social_core/utils.py:191-216",
    "social_core/utils.py:195-207"
   ],
   "reason_to_dismiss": "The partial_token is an unguessable uuid4 capability (social_core/storage.py:421-422) and resuming a pipeline from a token is the documented public contract of this utility, so a request-supplied token looks like an already-authenticated capability rather than user-controlled input.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "social_core/utils.py:180",
    "social_core/utils.py:185",
    "social_core/utils.py:186",
    "social_core/utils.py:187",
    "social_core/utils.py:188",
    "social_core/utils.py:192",
    "social_core/utils.py:195",
    "social_core/utils.py:202",
    "social_core/utils.py:209",
    "social_core/utils.py:215"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "locations": [
    "social_core/actions.py:176-182",
    "social_core/actions.py:96-100"
   ],
   "reason_to_dismiss": "do_disconnect is reached only with an already-authenticated user and the advisory describes the login/complete flow, so the disconnect caller looks out of scope and a fix written inside do_complete alone appears sufficient.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "easy",
   "type": "deepseek",
   "evidence": [
    "social_core/actions.py:96",
    "social_core/actions.py:98",
    "social_core/actions.py:100",
    "social_core/actions.py:176",
    "social_core/actions.py:180",
    "social_core/actions.py:182"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "social_core/utils.py:182-189"
   ],
   "reason_to_dismiss": "Framework views are expected to pass the token in request data, so the explicit partial_token argument and the configurable PARTIAL_PIPELINE_TOKEN_NAME name look like internal/rare shapes that a check on request_data['partial_token'] need not cover.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "social_core/utils.py:182",
    "social_core/utils.py:183",
    "social_core/utils.py:185",
    "social_core/utils.py:186"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "social_core/pipeline/mail.py:13-37",
    "social_core/pipeline/mail.py:30-33",
    "social_core/pipeline/partial.py:8-59",
    "social_core/strategy.py:130-134"
   ],
   "reason_to_dismiss": "mail_validation is applied with the plain @partial alias and already checks the verification_code (mail.py:23-29), so the emailed token looks like a self-authenticating exception and the step's cross-session resume policy looks like an internal decorator detail.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "social_core/pipeline/mail.py:13",
    "social_core/pipeline/mail.py:23",
    "social_core/pipeline/mail.py:25",
    "social_core/pipeline/mail.py:30",
    "social_core/pipeline/mail.py:31",
    "social_core/pipeline/mail.py:32",
    "social_core/pipeline/partial.py:8",
    "social_core/pipeline/partial.py:47",
    "social_core/pipeline/partial.py:48",
    "social_core/pipeline/partial.py:59",
    "social_core/strategy.py:130",
    "social_core/strategy.py:132"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "social_core/pipeline/partial.py:45-50",
    "social_core/pipeline/utils.py:60-71",
    "social_core/storage.py:392-396"
   ],
   "reason_to_dismiss": "The store path is an internal decorator/serializer concern (the decorator already calls partial_prepare), so where the resume-policy flag is written looks like an implementation detail and a flag placed in the ordinary kwargs appears to be persisted and restored like every other value.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "social_core/pipeline/partial.py:29",
    "social_core/pipeline/partial.py:46",
    "social_core/pipeline/partial.py:48",
    "social_core/pipeline/utils.py:14",
    "social_core/pipeline/utils.py:60",
    "social_core/pipeline/utils.py:65",
    "social_core/pipeline/utils.py:66",
    "social_core/pipeline/utils.py:67",
    "social_core/pipeline/utils.py:69",
    "social_core/pipeline/utils.py:100",
    "social_core/storage.py:392",
    "social_core/storage.py:394",
    "social_core/storage.py:396",
    "social_core/backends/base.py:273",
    "social_core/backends/base.py:274",
    "social_core/backends/base.py:152"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M5",
   "origin": "injection_room",
   "locations": [
    "social_core/strategy.py:130-134"
   ],
   "reason_to_dismiss": "BaseStrategy hosts framework extension points whose base behaviour is commonly a permissive no-op (as openid_session_dict or partial_load are), so the default of a new external-resume confirmation hook looks like it cannot itself be the security decision.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "social_core/strategy.py:127",
    "social_core/strategy.py:128",
    "social_core/strategy.py:130",
    "social_core/strategy.py:132",
    "social_core/strategy.py:133",
    "social_core/strategy.py:88",
    "social_core/strategy.py:119"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "social_core/pipeline/utils.py:83-104",
    "social_core/strategy.py:127-128",
    "social_core/backends/base.py:269-275"
   ],
   "reason_to_dismiss": "partial_load(token) plus continue_pipeline(partial) is a lower-level library API used by framework integrations and by the project's own test harness, not a user-facing web route, so the advisory's complete/disconnect handlers can be argued to be the whole scope.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "xhard",
   "type": "deepseek",
   "evidence": [
    "social_core/pipeline/utils.py:83",
    "social_core/pipeline/utils.py:86",
    "social_core/pipeline/utils.py:100",
    "social_core/strategy.py:127",
    "social_core/strategy.py:128",
    "social_core/backends/base.py:269",
    "social_core/backends/base.py:273",
    "social_core/backends/base.py:274"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "social_core/backends/open_id.py:189-200"
   ],
   "reason_to_dismiss": "BaseOpenID is a legacy OpenID 2.0 backend with its own continue_pipeline override, and the HTTP path still passes through the guard upstream in partial_pipeline_data, so the override looks like a neighbouring/legacy path rather than a second resume implementation.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "xhard",
   "type": "deepseek",
   "evidence": [
    "social_core/backends/open_id.py:189",
    "social_core/backends/open_id.py:191",
    "social_core/backends/open_id.py:194",
    "social_core/backends/open_id.py:196",
    "social_core/backends/open_id.py:198",
    "social_core/backends/base.py:269"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3"
  ],
  [
   "T4",
   "T5",
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": null,
  "masking": [
   "The email-validation resume currently works only because T1's hole exists; adding the session-ownership check without T4/T5's recorded allowance turns that flow into a regression rather than keeping it alive.",
   "T2 and T3 only become visible once the guard is written at the shared utility; a guard placed in do_complete alone hides them until the disconnect path or an explicit partial_token argument is exercised."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T4",
   "what": "Requiring the resume token to equal the session token (T1) refuses the emailed validation link opened in a fresh session, which mail_validation depends on because it puts the same token in the email (mail.py:30-33); the flow survives only if the allowance is recorded per stored partial and confirmed before the check denies."
  },
  {
   "a": "T1",
   "b": "T3",
   "what": "A check written only against request_data['partial_token'] passes the common case but leaves the explicit partial_token argument and a renamed PARTIAL_PIPELINE_TOKEN_NAME resolving to the stored partial unchecked, so the natural fix for T1 does not close T3 unless the check applies to the resolved token."
  }
 ],
 "fairness_risks": [
  "Email-validation links are a legitimate cross-session resume: mail_validation sends current_partial.token to the user's address (pipeline/mail.py:30-33) and the link is expected to work in a different browser or after the session expired; any rule that refuses a request token not present in the session contradicts this supported flow (strategy.py:163-174, 176-185).",
  "partial_step(save_to_session=False) deliberately records no session token (pipeline/partial.py:8, 45-50; exercised at tests/test_partial.py:58), so a rule of 'no session token means refuse' rejects a supported decorator shape.",
  "Framework views may pass partial_token as an explicit argument (utils.py:185-186) or configure PARTIAL_PIPELINE_TOKEN_NAME (utils.py:182-184); refusing all request-supplied tokens breaks stateless/mobile integrations that legitimately resume from a token.",
  "The repository's own partial-pipeline tests pop PARTIAL_TOKEN_SESSION_NAME before resuming: tests/backends/base.py:155-159 and 166-170, tests/test_pipeline.py:221-224 and 245-248. A guard placed in strategy.partial_load or BaseAuth.continue_pipeline (T7) or in the OpenID override (T8) makes those tests fail, so those two traps can only be graded if the hidden suite drops or rewrites them.",
  "The session holds only the most recent token (pipeline/partial.py:48-50 overwrites it each time a step halts), so an exact-equality rule can refuse a legitimate resume of an older in-flight partial in a second tab.",
  "partial_pipeline_data is a public utility used by third-party framework strategies; changing its contract to require a session match is a breaking change for callers that legitimately resume from a token (utils.py:173-179)."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T4",
   "T7",
   "T8"
  ],
  "why": "Four independent groups with genuinely different reasons to dismiss, mixing deepseek- and mimo-type mechanisms: T1 is the absent check at the landing point with a capability-token argument for leaving it alone; T4 is the coupled must-keep-working email link that a blanket fix breaks (mimo); T7 is the unguarded loader/continue_pipeline sink argued away as a library API; T8 is the BaseOpenID override argued away as legacy. T2 and T3 add the parallel caller and the resolved-token shape inside T1's group without adding a new dismissal reason, and T5/T6 add the producer and default-value failure modes inside T4's group. This beats a T1-only or T1+T4 design because it forces three separate ownership-boundary judgements (where the check lives, what may still resume out of band, whether the lower-level sink needs its own guard) instead of one edit to partial_pipeline_data. Caveat: T7 and T8 are only gradeable if the hidden suite does not retain the repo's existing resume-after-session_pop tests (tests/backends/base.py:155-170, tests/test_pipeline.py:221-248); if it does, the fair stack reduces to T1+T4 and this candidate falls below the 3-trap bar."
 },
 "unverified": [
  "The published fix diff was not available in the pinned worktree (HEAD is the pre-fix commit 6fcde2c2); the screener's fix-site line ranges and the claim that the fix stamped an allow flag on the mail step could not be checked against actual changes.",
  "The screener's 'confirmation round trip (partial_pipeline_confirm parameter)' does not exist anywhere in the pinned code; no such parameter or session key is present, so no trap was built on it.",
  "Whether the reference fix modified tests/backends/base.py or tests/test_pipeline.py (both pop the session token before resuming) could not be determined; this decides whether T7/T8 are fairly gradeable.",
  "Git history was not inspectable (Bash disabled in this session); 'a_fix_leaves_b_open' is inferred from code shape (the existing guards at utils.py:195-207 and strategy.py:130-134 still never bind the request token to the session) and from CHANGELOG.md:102, 445 rather than from a diff, and b_in_code_a_wrote is left null for that reason.",
  "No latest release code was provided, so present_in_latest for T7 and T8 is unknown.",
  "Out of scope for this candidate's advisory but observed in the same repository: open_id.py:212-213 restores a request-supplied session id (SESSION_SAVE_KEY) via strategy.restore_session with no prior validation, while the sibling SAML path validates the response first (saml.py:356-378); it is not counted as a trap here because it is a session-restore mechanism, not partial-pipeline resume.",
  "The project test test_login_with_invalid_partial_pipeline (tests/actions/test_login.py:82-93) mutates partial.data['backend'], but the guard at utils.py:195 reads PartialMixin.backend (storage.py:396), so that test does not actually reach the backend-mismatch branch; its value as a regression guard is uncertain.",
  "No test anywhere in the repository supplies partial_token through request data (the only occurrence of the default name is utils.py:183), so every T1/T3 input shape would be exercised by new tests only."
 ]
}
  ```
- Published fix sites:   - social_core/utils.py:185-189 — T1 M4 (reason to dismiss: The partial_token is an unguessable uuid4 capability (social_core/storage.py:421-422) and resuming a pipeline from a token is the documented public contract of this utility, so a request-supplied token looks like an already-authenticated capability rather than user-controlled input.)
  - social_core/utils.py:191-216 — T1 M4 (reason to dismiss: The partial_token is an unguessable uuid4 capability (social_core/storage.py:421-422) and resuming a pipeline from a token is the documented public contract of this utility, so a request-supplied token looks like an already-authenticated capability rather than user-controlled input.)
  - social_core/utils.py:195-207 — T1 M4 (reason to dismiss: The partial_token is an unguessable uuid4 capability (social_core/storage.py:421-422) and resuming a pipeline from a token is the documented public contract of this utility, so a request-supplied token looks like an already-authenticated capability rather than user-controlled input.)
  - social_core/actions.py:176-182 — T2 M1 (reason to dismiss: do_disconnect is reached only with an already-authenticated user and the advisory describes the login/complete flow, so the disconnect caller looks out of scope and a fix written inside do_complete alone appears sufficient.)
  - social_core/actions.py:96-100 — T2 M1 (reason to dismiss: do_disconnect is reached only with an already-authenticated user and the advisory describes the login/complete flow, so the disconnect caller looks out of scope and a fix written inside do_complete alone appears sufficient.)
  - social_core/utils.py:182-189 — T3 M5 (reason to dismiss: Framework views are expected to pass the token in request data, so the explicit partial_token argument and the configurable PARTIAL_PIPELINE_TOKEN_NAME name look like internal/rare shapes that a check on request_data['partial_token'] need not cover.)
  - social_core/pipeline/mail.py:13-37 — T4 M11 (reason to dismiss: mail_validation is applied with the plain @partial alias and already checks the verification_code (mail.py:23-29), so the emailed token looks like a self-authenticating exception and the step's cross-session resume policy looks like an internal decorator detail.)
  - social_core/pipeline/mail.py:30-33 — T4 M11 (reason to dismiss: mail_validation is applied with the plain @partial alias and already checks the verification_code (mail.py:23-29), so the emailed token looks like a self-authenticating exception and the step's cross-session resume policy looks like an internal decorator detail.)
  - social_core/pipeline/partial.py:8-59 — T4 M11 (reason to dismiss: mail_validation is applied with the plain @partial alias and already checks the verification_code (mail.py:23-29), so the emailed token looks like a self-authenticating exception and the step's cross-session resume policy looks like an internal decorator detail.)
  - social_core/strategy.py:130-134 — T4 M11 (reason to dismiss: mail_validation is applied with the plain @partial alias and already checks the verification_code (mail.py:23-29), so the emailed token looks like a self-authenticating exception and the step's cross-session resume policy looks like an internal decorator detail.)
  - social_core/pipeline/partial.py:45-50 — T5 M6 (reason to dismiss: The store path is an internal decorator/serializer concern (the decorator already calls partial_prepare), so where the resume-policy flag is written looks like an implementation detail and a flag placed in the ordinary kwargs appears to be persisted and restored like every other value.)
  - social_core/pipeline/utils.py:60-71 — T5 M6 (reason to dismiss: The store path is an internal decorator/serializer concern (the decorator already calls partial_prepare), so where the resume-policy flag is written looks like an implementation detail and a flag placed in the ordinary kwargs appears to be persisted and restored like every other value.)
  - social_core/storage.py:392-396 — T5 M6 (reason to dismiss: The store path is an internal decorator/serializer concern (the decorator already calls partial_prepare), so where the resume-policy flag is written looks like an implementation detail and a flag placed in the ordinary kwargs appears to be persisted and restored like every other value.)
- Uncovered routes to confirm (pattern B):   - social_core/pipeline/utils.py:83-104 — T7 M4 (reason to dismiss: partial_load(token) plus continue_pipeline(partial) is a lower-level library API used by framework integrations and by the project's own test harness, not a user-facing web route, so the advisory's complete/disconnect handlers can be argued to be the whole scope.)
  - social_core/strategy.py:127-128 — T7 M4 (reason to dismiss: partial_load(token) plus continue_pipeline(partial) is a lower-level library API used by framework integrations and by the project's own test harness, not a user-facing web route, so the advisory's complete/disconnect handlers can be argued to be the whole scope.)
  - social_core/backends/base.py:269-275 — T7 M4 (reason to dismiss: partial_load(token) plus continue_pipeline(partial) is a lower-level library API used by framework integrations and by the project's own test harness, not a user-facing web route, so the advisory's complete/disconnect handlers can be argued to be the whole scope.)
  - social_core/backends/open_id.py:189-200 — T8 M2 (reason to dismiss: BaseOpenID is a legacy OpenID 2.0 backend with its own continue_pipeline override, and the HTTP path still passes through the guard upstream in partial_pipeline_data, so the override looks like a neighbouring/legacy path rather than a second resume implementation.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T4, T7, T8. Why: Four independent groups with genuinely different reasons to dismiss, mixing deepseek- and mimo-type mechanisms: T1 is the absent check at the landing point with a capability-token argument for leaving it alone; T4 is the coupled must-keep-working email link that a blanket fix breaks (mimo); T7 is the unguarded loader/continue_pipeline sink argued away as a library API; T8 is the BaseOpenID override argued away as legacy. T2 and T3 add the parallel caller and the resolved-token shape inside T1's group without adding a new dismissal reason, and T5/T6 add the producer and default-value failure modes inside T4's group. This beats a T1-only or T1+T4 design because it forces three separate ownership-boundary judgements (where the check lives, what may still resume out of band, whether the lower-level sink needs its own guard) instead of one edit to partial_pipeline_data. Caveat: T7 and T8 are only gradeable if the hidden suite does not retain the repo's existing resume-after-session_pop tests (tests/backends/base.py:155-170, tests/test_pipeline.py:221-248); if it does, the fair stack reduces to T1+T4 and this candidate falls below the 3-trap bar. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Email-validation links are a legitimate cross-session resume: mail_validation sends current_partial.token to the user's address (pipeline/mail.py:30-33) and the link is expected to work in a different browser or after the session expired; any rule that refuses a request token not present in the session contradicts this supported flow (strategy.py:163-174, 176-185). | partial_step(save_to_session=False) deliberately records no session token (pipeline/partial.py:8, 45-50; exercised at tests/test_partial.py:58), so a rule of 'no session token means refuse' rejects a supported decorator shape. | Framework views may pass partial_token as an explicit argument (utils.py:185-186) or configure PARTIAL_PIPELINE_TOKEN_NAME (utils.py:182-184); refusing all request-supplied tokens breaks stateless/mobile integrations that legitimately resume from a token. | The repository's own partial-pipeline tests pop PARTIAL_TOKEN_SESSION_NAME before resuming: tests/backends/base.py:155-159 and 166-170, tests/test_pipeline.py:221-224 and 245-248. A guard placed in strategy.partial_load or BaseAuth.continue_pipeline (T7) or in the OpenID override (T8) makes those tests fail, so those two traps can only be graded if the hidden suite drops or rewrites them. | The session holds only the most recent token (pipeline/partial.py:48-50 overwrites it each time a step halts), so an exact-equality rule can refuse a legitimate resume of an older in-flight partial in a second tab. | partial_pipeline_data is a public utility used by third-party framework strategies; changing its contract to require a session match is a breaking change for callers that legitimately resume from a token (utils.py:173-179).. Conflicts the reader found: Requiring the resume token to equal the session token (T1) refuses the emailed validation link opened in a fresh session, which mail_validation depends on because it puts the same token in the email (mail.py:30-33); the flow survives only if the allowance is recorded per stored partial and confirmed before the check denies. | A check written only against request_data['partial_token'] passes the common case but leaves the explicit partial_token argument and a renamed PARTIAL_PIPELINE_TOKEN_NAME resolving to the stored partial unchecked, so the natural fix for T1 does not close T3 unless the check applies to the resolved token.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-social-core-5847/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-social-core-5847/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-social-core-5847/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-social-core-5847/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-social-core-5847/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-social-core-5847/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-social-core-5847/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-social-core-5847 --only static
python3 -I common/gate/gate.py stk-social-core-5847 --only nop
python3 -I common/gate/gate.py stk-social-core-5847 --only oracle
python3 -I common/gate/gate.py stk-social-core-5847 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-social-core-5847/`;
  - edit only `tasks/stk-social-core-5847/`, `build/stk-social-core-5847/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-5847.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `pipelines/stacking/1-select/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-social-core-5847`. Control task slug: `stk-social-core-5847-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-5847.json`.
