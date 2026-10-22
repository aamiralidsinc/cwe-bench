# backstage-ds — a provisional single-model lead whose VM data does not match its "MiMo-only" label

**Status of 2026-10-20. PROVISIONAL — not a confirmed breaker, and the classification needs correcting.**
This report was commissioned as a *MiMo-only* result (DeepSeek V4.1 Flash solves, MiMo-V2.6-Pro
fails 3/3). The counted results on the VM do **not** support that shape. On the task's **current**
version (after the sibling-injection / §2 upgrade), the latest counted 3-run trial shows **both**
models failing all three attempts at reward 0.0. DeepSeek's one reward 1.0 was recorded on
2026-10-19, against a **pre-upgrade** version of the task that no longer exists. No post-run
transcript audit has been recorded (the authoritative reader still lists this task as
"awaiting audit"), and the task's full build gate was **not** re-run after the upgrade. Treat every
number here as provisional until the gate is re-run, the trial is confirmed, and per-attempt audits
are done.

Sources: `build/backstage-ds/manifest.json`, `tasks/backstage-ds/instruction.md`,
`build/backstage-ds/FAIRNESS.md`, `build/backstage-ds/notes.md`, the accumulated run logs
(`runs_deepseek.log`, `runs_mimo.log`), the pipeline trial record (`build/backstage-ds/auto_trial.out`),
the partial gate report, and the per-run graded results under each run's prepared post-run
evidence folder. (No transcript-level audit has been produced for this task yet.)

## Summary

- **The "MiMo-only / DeepSeek solves" label is not supported by the current task version.** It
  comes from reading the accumulated run log, which mixes two task versions. Isolated by version:
  - **Pre-upgrade (2026-10-19):** DeepSeek reached **1.0** once, plus 0.9149, 0.9149. MiMo ran
    this version **once** (0.9149) — it was never given a full 3-run trial here.
  - **Current version, post sibling-injection upgrade (2026-10-20):** the pipeline ran a clean
    3-run trial for each model. **DeepSeek 0.0 / 0.0 / 0.0 and MiMo 0.0 / 0.0 / 0.0** — both
    failed every counted attempt. `auto_trial.out` records the verdict as
    `deepseek: failed (0p/3f/0e); mimo: failed (0p/3f/0e)`.
- So on the version that was actually trialled 3×3, this is **not a MiMo-only lead** — it reads as
  a **both-model** failure. But it is **not** a confirmed breaker either (see below).
- **Every one of the 6 current-version runs failed on the same cluster** — the built-in fetch
  actions. Both models over-block legitimate reads (Bitbucket Server, plain HTTPS, and/or local
  relative template paths) once the setting is on; because any functional failure forces reward 0,
  each run scored 0.0 regardless of how much security it closed. Per-run detail in §3.
- Every attempt finished on its own (`finish=success`, rc=0). Wall times: DeepSeek ~30–39 min;
  MiMo ~75 min, ~75 min and ~130 min — the long MiMo runs match the "slow lane" note, but none was
  recorded as a timeout.
- **Why this is not yet trustworthy:** the full build gate (vulnerable-tree fail, oracle→1.0,
  check-patches) was **not re-run** after the upgrade — only the patch-checks stage ran, and the
  gate report is marked `passed: false, partial: true`. Because all six runs fail the *same*
  functional tests, we cannot yet separate "both models genuinely over-block the fetch actions"
  from "a functional test the current oracle can no longer pass." One data point argues for the
  former: DeepSeek run 1 passed **49/49 security and 83/85 functional**, losing only the two
  Bitbucket cases — so a non-over-blocking fix is plausibly within reach — but that is not a
  substitute for re-running the oracle.

## 1. The task

**Vulnerability — privileged-credential fallback in Backstage scaffolder SCM steps.**
backstage/backstage, advisory **GHSA-29GX-H2M3-XW44 / CVE-2026-106462**, TypeScript, at the pinned
vulnerable commit `29330a9` (verified parent of the published fix `6fb2a41`,
"fix: require user credentials for SCM actions"). Backstage software templates run scaffolder
steps; some act on source-control content on behalf of the person running the template. Each such
step takes a credential supplied by that person and, when it is absent, **falls back to the
privileged integration credential configured for the Backstage instance**. A user who supplies no
personal credential can therefore cause a source-control operation to run as the instance's
identity, which that user cannot use directly.

**The rule (as given to the agent).** Add an opt-in instance setting
`scaffolder.requireScmUserCredentials` (boolean, default false). While it is enabled, no supported
scaffolder step may perform any source-control operation using the instance's integration
credential, however the target is expressed or referenced. A step may proceed only with a non-empty
user-supplied credential (empty string counts as none); without one it must fail with a client
error (`InputError`) **before** making any SCM request and **without constructing a client** for
the target host. Operations that inherently need the instance identity must be refused even when a
user credential is present. Integrations with no per-user-credential concept (e.g. Bitbucket
Server) keep their existing behaviour; everything that is not an SCM operation keeps working.
Enabling the setting in config must be sufficient at startup. While the setting is off, behaviour
must be exactly as today. No file, function, action id, route count or trap id is named in the
instruction.

**The routes (none named in the instruction; from the manifest/notes).** Track INJECTED, Pattern A.
Seven real routes plus two injected siblings to the same rule:

| Route | Site | Why a solver might miss it |
|---|---|---|
| T1 — shared GitHub credential helper (report-led) | `github/.../util.ts` `getOctokitOptions` fallback | none; the obvious landing point |
| T2 — pull-request injectable client factory | `github/.../actions/githubPullRequest.ts` | built outside the shared helper; a helper-only fix leaves it on the fallback |
| T3 — the whole GitLab module (3 helpers + inline publisher + privileged ownership) | `gitlab/.../util.ts`, `actions/gitlab.ts` | "the report is about GitHub, another SCM module looks out of scope" |
| T4 — the four built-in fetch actions (separate package, URL-reader path) | `scaffolder-backend/.../fetch/{plain,plainFile,template,templateFile}.ts` | "read-only template fetchers, not publish actions" |
| T5 — config read + per-action module/plugin wiring | each module's `module.ts` / `ScaffolderPlugin.ts` | "guards added in the actions, wiring forgotten" |
| T6 — `gitlab:user:info` (published fix never wired it) | `gitlab/.../actions/gitlabUserInfo.ts` | looks informational; still builds an authenticated client |
| T7 — `gitlab:group:migrate` (credential field differs) | `gitlab/.../actions/gitlabProjectMigrate.ts` | guard keyed to the common credential field misses it |
| S1 — *injected* GitHub release action resolving its own credential | `github/.../actions/githubRelease.ts` | "every GitHub action goes through the shared helper" |
| S2 — *injected* GitLab project-member action with an inline client | `gitlab/.../actions/gitlabProjectMemberCreate.ts` | "all GitLab actions go through the shared helpers" |

**Scoring.** Reward = security pass fraction, **0 if any functional test fails**, 1.0 = solve. On
the current version the graded suites are **49 security tests** and **85 functional tests** (plus
the pristine upstream project tests). A critical consequence: a run can close every security route
and still score 0.0 if it breaks one legitimate behaviour — which is exactly what happened here.

## 2. Fairness status — pre-trial review PASSED, but the post-upgrade gate was NOT re-run

- **Pre-trial fairness review (`FAIRNESS.md`): clean.** A per-test table rates all security and
  functional tests **low risk** ("a competent literal implementation passes"), with an explicit
  "could a CORRECT fix fail it?" column answered *no* for every test. Fairness revisions F1–F7 were
  applied (no-client-construction wording, GitHub/GitLab scope with Bitbucket exempted, behavioural
  user-token assertions, empty-token cases, tokenless-integration cases, and removal of the
  credential-helper / out-of-scope-step hints). The review also lists the residual leniency gaps
  it could not close with a test (a GitLab guard gated on a configured integration token; a few
  setting-off actions with no functional case) and judges them low risk.
- **But the full build gate was not re-run after the sibling-injection upgrade.** The manifest
  status says plainly: *"sibling-injection upgrade applied … nop/oracle/patches gate not re-run
  after the upgrade."* The on-disk gate report is `gate_report.partial.json`, `passed: false`,
  `partial: true`, and contains only the **patches** stage — the vulnerable-tree-fails and
  **oracle→1.0** stages are absent. So we have no fresh confirmation that the reference fix still
  scores 1.0 against the current 49+85 tests, and in particular that it passes the Bitbucket /
  plain-HTTPS / local functional cases that every trial run failed.
- **Consequence for this result.** Because all six runs fail the same functional cluster, the
  honest reading is: either both models over-block the fetch actions (a genuine shared failure), or
  a functional test is unsatisfiable on the current oracle. The pre-trial review and DeepSeek run 1
  (49/49 security, 83/85 functional) both point toward the former, but the gate re-run is what
  settles it. Until then the "both fail 3/3" signal is provisional.

## 3. The current counted trial, run by run (provisional — no transcript audit yet)

Isolated from `auto_trial.out` and each run's graded `results.json` (the 2026-10-20 trial, current
task version). Security total 49, functional total 85.

| Model | Attempt | Reward | Security | Functional | What broke / stayed open |
|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 49/49 | 83/85 | over-blocked 2 fetch functional cases (Bitbucket Server, `fetch:plain` + `fetch:template`) |
| DeepSeek | 2 | 0.0 | 45/49 | 83/85 | 4 fetch **security** routes left open **and** the 2 Bitbucket functional cases over-blocked |
| DeepSeek | 3 | 0.0 | 45/49 | 83/85 | same as run 2 |
| MiMo | 1 | 0.0 | 49/49 | 75/85 | over-blocked 10 fetch functional cases (plain HTTPS, Bitbucket, local relative — across all four fetch actions) |
| MiMo | 2 | 0.0 | 45/49 | 83/85 | 4 fetch security routes open **and** the 2 Bitbucket functional cases over-blocked |
| MiMo | 3 | 0.0 | 49/49 | 75/85 | same shape as MiMo run 1 (10 fetch functional over-blocked) |

- **All six runs failed in the fetch actions** (T4) — never in GitHub (T1/T2/S1) or GitLab
  (T3/T6/T7/S2), which both models appear to have closed (security 45–49/49 every run).
- The dominant failure is **over-broad fetching**: once the guard was added to the fetch actions,
  legitimate non-SCM and Bitbucket reads were refused too, tripping the "fetch actions keep working"
  functional tests and forcing reward 0. In 2 of 6 runs the models *also* left 4 fetch security
  routes open — i.e. they both over-blocked the legitimate cases and under-covered the attack cases
  on the same surface.
- This is **inference from per-test results only.** No transcript/per-attempt audit has been run,
  so *why* each model drew the fetch boundary where it did is not established.

## 4. What is needed before this can be classified or reported

1. **Re-run the full build gate on the current version** — vulnerable tree fails all security,
   oracle (`solution/fix.patch`) scores **1.0** against the current 49+85 tests (especially the
   Bitbucket / plain-HTTPS / local functional cases every run failed), and all check patches behave
   as declared. Until the oracle is re-confirmed at 1.0, the shared functional failure cannot be
   attributed to the models.
2. **Confirm the counted trial** is the 2026-10-20 post-upgrade 3×3 (it is, per `auto_trial.out`)
   and discard the 2026-10-19 pre-upgrade runs (different task version) from any verdict.
3. **Run the per-attempt audits** (the prepared evidence exists under
   `~/.tb-graders/cwe/jobs/backstage-ds-*/…/postmortem-*`, but no verdict is recorded; the
   authoritative reader `build/audit_results.py` still lists backstage-ds as
   "no graded run (+3 awaiting audit)" for both models).
4. **Then classify.** On current evidence the likely outcome is a **both-model** result, not a
   MiMo-only lead — but it is **none of these yet**, and the report filename
   (`backstage-ds-mimo-only.md`) should be reconciled with whatever the gate re-run and audits
   confirm.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a
  solve (no early-exit occurred on the current version — neither model solved).
- Offline: model APIs only, web tools disabled, no git history; hidden tests copied in only after
  the agent stops.
- Reward = security pass fraction, 0 if any functional test fails, 1.0 = solve. Timeouts count as
  failures; provider/network cuts are not counted. All six current-version runs finished on their
  own (no timeout, no provider cut).
- Track: INJECTED (two of the nine routes, S1 and S2, are injected siblings of the same class; the
  other seven are real unmodified upstream routes, two of which — T6/T7 — the published fix itself
  left open).
- **Caveat carried throughout:** the build gate was not re-run after the §2 upgrade, and no
  per-attempt transcript audit has been recorded. Every number here is provisional.
