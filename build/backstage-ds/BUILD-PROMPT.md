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

Project root: `/home/mara/cwe-bench`. Task: `backstage-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-29GX-H2M3-XW44", "CVE-2026-106462"]; backstage/backstage; authorization / confused deputy: privileged backend credential fallback (CWE-441, CWE-863)
- Pinned (vulnerable) commit: parent of 6fb2a41ea47da37eafe5ea744050ef90be6820c0 (parent_commit not given in candidate). Published fix: 6fb2a41ea47da37eafe5ea744050ef90be6820c0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "7454",
 "advisory_ids": [
  "GHSA-29GX-H2M3-XW44",
  "CVE-2026-106462"
 ],
 "repo": "backstage/backstage",
 "pinned_commit": "parent of 6fb2a41ea47da37eafe5ea744050ef90be6820c0 (parent_commit not given in candidate)",
 "fix_commits": [
  "6fb2a41ea47da37eafe5ea744050ef90be6820c0"
 ],
 "trust_decision": {
  "summary": "Each scaffolder SCM action decides which credential authenticates its SCM call: the user-supplied input token, or a fallback to the backend's privileged integration credential (GitHub credentials provider/App, GitLab/Bitbucket/Azure integration token). The fix adds an opt-in scaffolder.requireScmUserCredentials flag that forbids the fallback. The decision is made per action and in the shared helpers getOctokitOptions (GitHub), getClient/getToken/createGitlabApi (GitLab) and fetchContents via UrlReader (fetch:*).",
  "evidence": [
   "plugins/scaffolder-backend-module-github/src/util.ts:181-206",
   "plugins/scaffolder-backend-module-gitlab/src/util.ts:109-123",
   "plugins/scaffolder-backend-module-gitlab/src/actions/helpers.ts:39-44",
   "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloud.ts:219-221",
   "plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServer.ts:252",
   "plugins/scaffolder-backend-module-azure/src/actions/azure.ts:158-172",
   "plugins/scaffolder-node/src/actions/fetch.ts:60-62"
  ]
 },
 "landing_point": {
  "where": "plugins/scaffolder-backend-module-github/src/util.ts:181-206",
  "why": "The advisory summary says 'unintended GitHub authentication fallback'. getOctokitOptions is the single GitHub helper that falls back from the caller's token to the integration credentials provider when no token is given."
 },
 "fix_sites": [
  {
   "where": "plugins/scaffolder-backend-module-github/src/util.ts:181-195",
   "entry_point": "public API getOctokitOptions (exported, report.api.md) used by 12 GitHub template actions and the autocomplete handler",
   "module_kind": "shared helper / lower-level public API"
  },
  {
   "where": "plugins/scaffolder-backend-module-github/src/module.ts:59-62",
   "entry_point": "backend module init wiring the flag into all 13 github:* / publish:github* actions",
   "module_kind": "module wiring (config read)"
  },
  {
   "where": "plugins/scaffolder-backend-module-github/src/actions/github.ts:158",
   "entry_point": "template action publish:github",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-github/src/actions/githubPullRequest.ts:309",
   "entry_point": "template action publish:github:pull-request (goes through clientFactory, not getOctokitOptions directly, so it gets a separate check)",
   "module_kind": "action handler with injectable client factory"
  },
  {
   "where": "plugins/scaffolder-backend-module-github/src/actions/githubRepoPush.ts:111",
   "entry_point": "template action github:repo:push (plus 9 more github:* actions at their getOctokitOptions call: actions:dispatch, autolinks:create, branch-protection:create, deployKey:create, environment:create, issues:create, issues:label, pages:enable, repo:create, webhook)",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-gitlab/src/util.ts:57",
   "entry_point": "getToken, used by gitlab:projectAccessToken:create",
   "module_kind": "shared helper"
  },
  {
   "where": "plugins/scaffolder-backend-module-gitlab/src/util.ts:109-115",
   "entry_point": "getClient, used by gitlab:group:ensureExists, gitlab:group:access, gitlab:issues:create, gitlab:issue:edit, gitlab:pipeline:trigger, gitlab:projectDeployToken:create, gitlab:projectVariable:create",
   "module_kind": "shared helper"
  },
  {
   "where": "plugins/scaffolder-backend-module-gitlab/src/actions/helpers.ts:39-43",
   "entry_point": "createGitlabApi, used by publish:gitlab:merge-request and gitlab:repo:push",
   "module_kind": "second helper (a duplicate of getClient)"
  },
  {
   "where": "plugins/scaffolder-backend-module-gitlab/src/actions/gitlab.ts:284-288",
   "entry_point": "template action publish:gitlab (also blocks the setUserAsOwner/ownerUsername admin-client subpaths at :351-365)",
   "module_kind": "action handler with inline client construction"
  },
  {
   "where": "plugins/scaffolder-backend-module-gitlab/src/module.ts:57-71",
   "entry_point": "backend module init wiring",
   "module_kind": "module wiring"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloud.ts:219-221",
   "entry_point": "template action publish:bitbucketCloud",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudPullRequest.ts:316",
   "entry_point": "template action publish:bitbucketCloud:pull-request",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudPipelinesRun.ts:72",
   "entry_point": "template action bitbucket:pipelines:run",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudBranchRestriction.ts:143",
   "entry_point": "template action bitbucketCloud:branchRestriction:create",
   "module_kind": "action handler"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServer.ts:252",
   "entry_point": "template action publish:bitbucketServer",
   "module_kind": "action handler (reads config itself)"
  },
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServerPullRequest.ts:343",
   "entry_point": "template action publish:bitbucketServer:pull-request",
   "module_kind": "action handler (reads config itself)"
  },
  {
   "where": "plugins/scaffolder-backend-module-azure/src/actions/azure.ts:158-160",
   "entry_point": "template action publish:azure",
   "module_kind": "action handler (reads config itself)"
  },
  {
   "where": "plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/plain.ts:78",
   "entry_point": "built-in template action fetch:plain (SCM read via UrlReader)",
   "module_kind": "core plugin built-in action, separate package"
  },
  {
   "where": "plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/template.ts:136-148",
   "entry_point": "built-in template actions fetch:template, and likewise fetch:plain:file and fetch:template:file (templateFile.ts:107)",
   "module_kind": "core plugin built-in action, separate package"
  },
  {
   "where": "plugins/scaffolder-backend/src/ScaffolderPlugin.ts:195-212",
   "entry_point": "scaffolder plugin init wiring the flag into the four fetch actions",
   "module_kind": "plugin wiring"
  }
 ],
 "O1_entry_points": 35,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/plain.ts:78 (and template.ts:142, templateFile.ts, plainFile.ts): SCM reads reach the integration credential through UrlReader in fetchContents (plugins/scaffolder-node/src/actions/fetch.ts:60-62), a credential path entirely separate from the per-SCM publish helpers, in a different package (core scaffolder-backend, not an SCM module)."
 },
 "O3_reason_to_dismiss": "The report is about GitHub mutation/publish actions authenticating with the backend's credential. fetch:* actions are generic, read-only template fetchers in the core plugin that 'just read the template', so a solver can argue they are a neighbouring feature. Likewise, other SCM modules (GitLab, Bitbucket, Azure) can be argued out of a 'GitHub' report.",
 "O4_distance": {
  "files": 44,
  "packages": 6,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "With the flag on, fetches from non-github/gitlab integrations (Bitbucket Server, plain HTTPS hosts, file:// relative template paths) must still work without a token, because only GitHub/GitLab UrlReaders accept a user token. With the flag off (the default), the integration-credential fallback must keep working everywhere. An over-broad fix that rejects every tokenless fetch, or that ignores the flag, breaks these.",
  "where": "fix.diff:2024-2036; fix.diff:2064; plugins/scaffolder-node/src/actions/fetch.ts:53-58"
 },
 "O6_input_shapes": [
  "token input absent (undefined)",
  "token input empty string (falsy check, not ?? ; bitbucket-server at pinned uses ?? at plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServer.ts:252)",
  "getOctokitOptions host/owner/repo overload and the deprecated repoUrl overload (plugins/scaffolder-backend-module-github/src/util.ts:134-163)",
  "fetch url absolute vs relative-to-template baseUrl (fix.diff:2080-2091)",
  "GitLab publish with setUserAsOwner / ownerUsername, which use the integration admin token even when a user token is given (plugins/scaffolder-backend-module-gitlab/src/actions/gitlab.ts:351-365)",
  "Azure PAT vs bearer credential types (plugins/scaffolder-backend-module-azure/src/actions/azure.ts:169-172)"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "Backend module init reads root config and constructs actions. The flag must be read there and threaded into factory options: plugins/scaffolder-backend-module-github/src/module.ts:59-62, plugins/scaffolder-backend-module-gitlab/src/module.ts:54-71, plugins/scaffolder-backend/src/ScaffolderPlugin.ts:180-212. Only publish:azure, publish:bitbucketServer(*), and publish:gitlab read config inside the handler.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "gitlab:user:info builds a GitLab client via getClient without the flag, so with no token it authenticates as the integration token and returns that identity's profile/email",
   "where": "plugins/scaffolder-backend-module-gitlab/src/actions/gitlabUserInfo.ts:104-112",
   "reason_to_dismiss": "It is a read-only lookup, and the fix and docs scope the setting to 'mutation actions'; the getClient check exists but the module never passes the flag (plugins/scaffolder-backend-module-gitlab/src/module.ts:66)",
   "distance": "same package as the GitLab fix sites, separate action file; 0 hops from getClient",
   "present_in_latest": "yes",
   "latest_where": "latest/plugins/scaffolder-backend-module-gitlab/src/actions/gitlabUserInfo.ts:107"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloud.ts:245-247",
   "sibling": "publish:bitbucketCloud resolves git push auth a second time with the same token-or-integration fallback, separately from the API header at :219-221",
   "why_realistic": "The fix left this second fallback untouched (it is only shielded by the earlier throw). A maintainer could plausibly have placed the guard only around the API header, which would leave the git push falling back."
  },
  {
   "where": "plugins/scaffolder-backend-module-github/src/actions/githubPullRequest.ts:56-63",
   "sibling": "defaultClientFactory calls getOctokitOptions without the flag; the PR action relies on its own pre-check before clientFactory",
   "why_realistic": "Custom clientFactory and wrapper paths are common. Moving the guard into getOctokitOptions alone would miss the PR action, and a guard only in the action would miss direct getOctokitOptions users."
  },
  {
   "where": "plugins/scaffolder-backend-module-cookiecutter/src/actions/fetch/cookiecutter.ts:225-231",
   "sibling": "fetch:cookiecutter (and fetch:rails at plugins/scaffolder-backend-module-rails/src/actions/fetch/rails/index.ts:191) reads SCM content through fetchContents with the integration credential",
   "why_realistic": "They have no token input, so upstream documents them as unaffected. In our copy, adding a token input there would create a realistic, distant sibling of fetch:template."
  }
 ],
 "O9_family": "authorization / confused deputy: privileged backend credential fallback (CWE-441, CWE-863)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node.js)",
  "toolchain": "Node 22 or 24, yarn 4.8.1 monorepo (package.json:181-183), backstage-cli jest",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Jest unit tests that mock HTTP with msw and mock the clients: plugins/scaffolder-backend-module-github/src/util.test.ts, plugins/scaffolder-backend-module-gitlab/src/util.test.ts, plugins/scaffolder-backend-module-gitlab/src/actions/gitlab.test.ts, plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/*.test.ts, plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServer.test.ts, plugins/scaffolder-backend-module-azure/src/actions/azure.test.ts, plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/*.test.ts"
 },
 "O11_fix_minutes": 90,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "plugins/scaffolder-backend-module-azure/src/actions/azure.ts; plugins/scaffolder-backend-module-bitbucket-cloud/src/{module.ts,actions/bitbucketCloud.ts,actions/bitbucketCloudBranchRestriction.ts,actions/bitbucketCloudPipelinesRun.ts,actions/bitbucketCloudPullRequest.ts}; plugins/scaffolder-backend-module-bitbucket-server/src/actions/{bitbucketServer.ts,bitbucketServerPullRequest.ts}; plugins/scaffolder-backend-module-github/src/{module.ts,util.ts,actions/github.ts,githubActionsDispatch.ts,githubAutolinks.ts,githubBranchProtection.ts,githubDeployKey.ts,githubEnvironment.ts,githubIssuesCreate.ts,githubIssuesLabel.ts,githubPagesEnable.ts,githubPullRequest.ts,githubRepoCreate.ts,githubRepoPush.ts,githubWebhook.ts}; plugins/scaffolder-backend-module-gitlab/src/{module.ts,util.ts,actions/helpers.ts,gitlab.ts,gitlabGroupAccessAction.ts,gitlabGroupEnsureExists.ts,gitlabIssueCreate.ts,gitlabIssueEdit.ts,gitlabMergeRequest.ts,gitlabPipelineTrigger.ts,gitlabProjectAccessTokenCreate.ts,gitlabProjectDeployTokenCreate.ts,gitlabProjectVariableCreate.ts,gitlabRepoPush.ts}; plugins/scaffolder-backend/{config.d.ts,src/ScaffolderPlugin.ts,src/scaffolder/actions/builtin/fetch/{assertScmUserCredentials.ts(new),plain.ts,plainFile.ts,template.ts,templateFile.ts}}",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a requireScmUserCredentials check inside getOctokitOptions (GitHub only) and wire it in the GitHub module, leaving GitLab/Bitbucket/Azure, the PR clientFactory path, the GitLab admin-token subpaths and the core fetch:* actions on the fallback."
 },
 "out_of_scope_notes": [
  "Gitea and Gerrit publish modules (plugins/scaffolder-backend-module-gitea, plugins/scaffolder-backend-module-gerrit) were not inspected; the published docs name only GitHub, GitLab, Bitbucket Cloud/Server and Azure as supported.",
  "plugins/scaffolder-backend-module-github/src/module.ts:92 wires github:repo:push without githubCredentialsProvider (pre-existing, unrelated)."
 ],
 "unverified": [
  "The pinned commit hash is not given (parent_commit null); the repo directory is assumed to be the parent of the fix commit. No requireScmUserCredentials string exists in the pinned tree, which is consistent with that.",
  "repo_mb is unknown (no size measurement done), so tiny_repo/giant_repo were not assessed.",
  "The protection is a NEW opt-in config flag introduced by the fix, so the task report must name the config key and option name (requireScmUserCredentials) for hidden tests to be fair. This makes the report prescriptive and may weaken the scope lever.",
  "O11 at 90 minutes exceeds the 45-minute fairness target because there are 35 action entry points. Trimming our copy (e.g. GitHub + GitLab + fetch:*) may be needed.",
  "gitlab:group:migrate (plugins/scaffolder-backend-module-gitlab/src/actions/gitlabProjectMigrate.ts:42-45,97-101) requires destinationAccessToken as a string, so it was judged not a fallback route; behaviour with an empty string was not verified beyond reading helpers.ts:39-44.",
  "Recall risk is judged low because the advisory was published on 2026-10-07; external write-up coverage was not checked."
 ]
}
  ```
- Published fix sites:   - plugins/scaffolder-backend-module-github/src/util.ts:181-195 — entry point: public API getOctokitOptions (exported, report.api.md) used by 12 GitHub template actions and the autocomplete handler [shared helper / lower-level public API]
  - plugins/scaffolder-backend-module-github/src/module.ts:59-62 — entry point: backend module init wiring the flag into all 13 github:* / publish:github* actions [module wiring (config read)]
  - plugins/scaffolder-backend-module-github/src/actions/github.ts:158 — entry point: template action publish:github [action handler]
  - plugins/scaffolder-backend-module-github/src/actions/githubPullRequest.ts:309 — entry point: template action publish:github:pull-request (goes through clientFactory, not getOctokitOptions directly, so it gets a separate check) [action handler with injectable client factory]
  - plugins/scaffolder-backend-module-github/src/actions/githubRepoPush.ts:111 — entry point: template action github:repo:push (plus 9 more github:* actions at their getOctokitOptions call: actions:dispatch, autolinks:create, branch-protection:create, deployKey:create, environment:create, issues:create, issues:label, pages:enable, repo:create, webhook) [action handler]
  - plugins/scaffolder-backend-module-gitlab/src/util.ts:57 — entry point: getToken, used by gitlab:projectAccessToken:create [shared helper]
  - plugins/scaffolder-backend-module-gitlab/src/util.ts:109-115 — entry point: getClient, used by gitlab:group:ensureExists, gitlab:group:access, gitlab:issues:create, gitlab:issue:edit, gitlab:pipeline:trigger, gitlab:projectDeployToken:create, gitlab:projectVariable:create [shared helper]
  - plugins/scaffolder-backend-module-gitlab/src/actions/helpers.ts:39-43 — entry point: createGitlabApi, used by publish:gitlab:merge-request and gitlab:repo:push [second helper (a duplicate of getClient)]
  - plugins/scaffolder-backend-module-gitlab/src/actions/gitlab.ts:284-288 — entry point: template action publish:gitlab (also blocks the setUserAsOwner/ownerUsername admin-client subpaths at :351-365) [action handler with inline client construction]
  - plugins/scaffolder-backend-module-gitlab/src/module.ts:57-71 — entry point: backend module init wiring [module wiring]
  - plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloud.ts:219-221 — entry point: template action publish:bitbucketCloud [action handler]
  - plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudPullRequest.ts:316 — entry point: template action publish:bitbucketCloud:pull-request [action handler]
  - plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudPipelinesRun.ts:72 — entry point: template action bitbucket:pipelines:run [action handler]
  - plugins/scaffolder-backend-module-bitbucket-cloud/src/actions/bitbucketCloudBranchRestriction.ts:143 — entry point: template action bitbucketCloud:branchRestriction:create [action handler]
  - plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServer.ts:252 — entry point: template action publish:bitbucketServer [action handler (reads config itself)]
  - plugins/scaffolder-backend-module-bitbucket-server/src/actions/bitbucketServerPullRequest.ts:343 — entry point: template action publish:bitbucketServer:pull-request [action handler (reads config itself)]
  - plugins/scaffolder-backend-module-azure/src/actions/azure.ts:158-160 — entry point: template action publish:azure [action handler (reads config itself)]
  - plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/plain.ts:78 — entry point: built-in template action fetch:plain (SCM read via UrlReader) [core plugin built-in action, separate package]
  - plugins/scaffolder-backend/src/scaffolder/actions/builtin/fetch/template.ts:136-148 — entry point: built-in template actions fetch:template, and likewise fetch:plain:file and fetch:template:file (templateFile.ts:107) [core plugin built-in action, separate package]
  - plugins/scaffolder-backend/src/ScaffolderPlugin.ts:195-212 — entry point: scaffolder plugin init wiring the flag into the four fetch actions [plugin wiring]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

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

## Environment (`tasks/backstage-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/backstage-ds/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/backstage-ds/tests/`)
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
- **Wrong-fix patches** go in `build/backstage-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/backstage-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/backstage-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/backstage-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py backstage-ds --only static
python3 -I builder/gate.py backstage-ds --only nop
python3 -I builder/gate.py backstage-ds --only oracle
python3 -I builder/gate.py backstage-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/backstage-ds/`;
  - edit only `tasks/backstage-ds/`, `build/backstage-ds/` and, for pattern B, the register;
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
