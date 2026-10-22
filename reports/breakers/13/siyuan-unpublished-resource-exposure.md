# siyuan-unpublished-resource-exposure — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness reviews, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- DeepSeek finished on its own in 19, 21 and 31 minutes. MiMo finished in 99 and 103 minutes; its second attempt used the full 2-hour limit and its code was graded as it stood (counted as a failure).
- Every counted attempt was audited independently: all 6 were judged trustworthy model failures with high confidence.
- The task is a real application with real gaps. It is SiYuan (Go) at the commit before a published authorization fix. The advisory's own routes are combined with two real routes the published fix left open, and two injected sibling routes.
- Why both models fail: the rule has several routes and two publication paths. DeepSeek closed the routes it saw and left whole route families open. MiMo closed nearly every route but did not recognise how documents use widgets, so it also refused widgets that are legitimately published.

## 1. The task

**Vulnerability (CWE-862, missing authorization).** A SiYuan owner can publish a workspace so that visitors with the reader role can view selected material. The kernel serves stored resources (templates, export artifacts, widgets, plugins, custom emoji, code snippets) through static routes whose only guard is authentication. A reader therefore gets resources the owner never published, and some APIs describe them.

**Base advisory:** GHSA-FGMR-7W36-9QFQ / CVE-2026-72796 / GO-2026-6423. Vulnerable commit fd6d23d, upstream fix 34be6c0. The published fix adds an owner-only gate for templates and exports, per-resource publish rules, a rule that a widget or custom emoji is published only when a readable document uses it, and safer static file serving.

**What the task contains.** One rule, nine routes, each paired with a legitimate behaviour that must keep working:

| Route | What leaks to a reader | What must keep working next to it | Origin |
|---|---|---|---|
| 1. Widgets and custom emoji | widget packages and emoji files that no readable document uses, or that are marked excluded | widgets and emoji used by a readable document, including references written in other shapes, directory requests and a symlinked package directory | advisory's own route |
| 2. Snippets | a snippet withheld from publishing, a snippet found only on disk, a name served under the wrong type | the snippets the workspace publishes | advisory's own route |
| 3. Templates and export artifacts | template files and generated exports, including the temporary export folder and HEAD requests | the owner keeps full access | advisory's own route |
| 4. Plugins | plugins marked excluded, and installed plugins that are not enabled | enabled, published plugins | advisory's own route |
| 5. Path shapes | a nested symlink that escapes its package; a path that names one package and resolves to another | a top-level package directory that is itself a symlink | advisory's own route |
| 6. Installed-package listings | listings name plugins, widgets and templates that are not published | readers still see published packages; the owner sees all | real upstream code the fix left open |
| 7. Custom emoji catalog | the catalog names emoji no readable document uses | readers still see used emoji; the owner sees all | real upstream code the fix left open |
| 8. A publish-preview file resolver | any stored file, through a second address | published resources keep being served there | added for the task |
| 9. A snippet preview helper | a withheld snippet's content, by name | published snippets keep being served there | added for the task |

**Report given to the agent.** It is written as a bug report. It states the impact (a reader could fetch, and learn about, withheld material) and one property: a reader "must never obtain, and must never be told about, a stored resource that is not published to that visitor". Publication has two paths: the workspace's own selection or enablement settings, or use of the resource by content available to the visitor. The report adds that "a decision about a request must apply to the resource the request actually resolves to". The contracts:
- a refusal is a client error or a negative result code;
- a published resource "keeps being served exactly as it is today, at the same address and with the same content";
- the owner keeps unrestricted access.

No resource class, route, file or function is named.

**Hidden tests.** 20 security tests (4 for route 1, 3 for route 2, 3 for route 3, 2 for route 4, 2 for route 5, 3 for route 6, 1 each for routes 7–9) and 61 functional tests (14 task tests plus 47 of the project's own tests for the area, subtests included). They drive the real gin route handlers and API handlers with the reader or owner role on the request context, the way the publish proxy sets it, over a small real workspace: data directories, installed packages, snippet configuration, a block-tree database, one public document and one withheld document. Reward = the security pass fraction, or 0 if any functional test fails; 1.0 only when everything passes.

## 2. How we know the task is fair

Before any model ran:

| Check | Result |
|---|---|
| Vulnerable code (with the two added routes) | fails all 20 security tests, passes all 61 functional tests |
| Reference fix | 1.0, three times |
| Blind fix (written from the report and code alone) | not run |
| Hardening fix, and an alternative fix that moves the decision to the file-serving layer | pass, as declared |
| The upstream advisory fix alone | not run as a separate check |
| One wrong-fix patch per route (9 patches: templates/exports, snippet toggle, snippet disk fallback, widgets/emoji, readable-document filter, plugins, listings, preview route, symlink) | each fails the matching security tests with all functional tests green |
| An over-broad fix (owner-only gate on every route) | fails the functional tests (published pages break) |
| Fairness review of every test against the report | the first review found one blocking ambiguity (whether template packages can be published). The fixture and report were changed, and a follow-up validation on the final report judged the task ready |

In total, 12 check patches behaved as declared, and the scripted gate passed on the final version.

## 3. Results, attempt by attempt

| Model | Attempt | Minutes | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|---|
| DeepSeek | 1 | 19 | 0.0 | 10/20 | 57/61 | listings (route 6); emoji catalog (7); all of route 1; path shapes (5) | published widget through the preview route; snippet-serving tests |
| DeepSeek | 2 | 21 | 0.0 | 7/20 | 57/61 | routes 1, 5, 6, 7; templates and the temporary export folder (3) | published widget through the preview route; snippet-serving tests |
| DeepSeek | 3 | 31 | 0.0 | 4/6 recorded | 48/50 recorded | not recorded | not recorded |
| MiMo | 1 | 99 | 0.0 | 18/20 | 53/61 | widget listing; temporary export folder | published widgets (direct, directory, other reference shapes, symlinked package, preview); published widget in the listing; snippet-serving tests |
| MiMo | 2 | 120 (limit) | 0.0 | 18/20 | 52/61 | widget listing; emoji catalog | directory requests return 404 for everyone, owner included (published widget directories among them); published widget through the preview route; published widget in the listing; snippet-serving tests |
| MiMo | 3 | 103 | 0.0 | 13/20 | 53/61 | listings; emoji catalog; temporary export folder; an excluded plugin (direct and through the preview route) | published widgets (direct, directory, shapes, symlinked package, preview); a used emoji in the catalog; snippet-serving tests |

- In all 5 attempts with complete per-test results, at least one listing or catalog (routes 6–7) stayed open.
- In all 5, a published widget was no longer served through the preview route (route 8).
- DeepSeek left route 1 (per-document widget and emoji rule) fully open in both completed attempts. MiMo closed it in all 3 but refused published widgets too.
- The temporary export folder stayed open in 3 attempts (DeepSeek 2, MiMo 1 and 3).

One additional DeepSeek attempt, started a minute before the first counted one under the same run number, also scored 0.0 (15/20, 55/61). It is not in the counted set and was not audited.

## 4. Why both models failed

### 4.1 Left open: listings and the emoji catalog (routes 6 and 7)

These routes are API endpoints, not static file routes, and the published fix does not touch them.
- DeepSeek, attempts 1 and 2, worked almost entirely in the file-serving routes (attempt 2 also changed the snippet API and snippet/plugin helpers). Attempt 1 announced its plan as publish-aware checks for "publish-preview, snippets, snippet previews, plugins, and exports". The listings and catalog were never filtered.
- MiMo found the routes and filtered them, but not consistently. Attempt 1's summary states "installed plugin/widget/template descriptions filtered", yet the widget listing still named an unused widget. Attempt 3 did not change the installed-package listing handler; its final route sweep lists a filter for loaded plugins instead. All four listing and catalog tests failed.

### 4.2 Left open: the per-document rule for widgets and emoji (route 1)

A widget or custom emoji has no publish switch of its own. It is published only when a readable document uses it.
- DeepSeek, attempts 1 and 2, never built this rule: unused widgets, unused emoji, excluded widgets and resources used only by the withheld document all stayed reachable.
- DeepSeek, attempt 2, also restricted the preview route to "the two publishable resource kinds (`.sy` documents and `assets/` files)". That closed the route but also refused a published widget there.

### 4.3 Broke: widgets that are legitimately published (all 3 MiMo attempts)

In all 3 attempts, MiMo built the per-document rule on the project's existing asset-link collector. Attempt 1 describes its rule as "referenced from content a visitor can reach (link dests + emojis)". That collector does not read the root-relative source of a widget block, so the used widget was never seen as used. The published widget was refused through the preview route in all 3 attempts. In attempts 1 and 3 it was also refused directly, as a directory, through the other reference shapes and through the symlinked package. The unused widgets were refused as well, so the security tests passed while the functional tests failed. Attempt 2 also broke directory requests for everyone, the owner included (404).

### 4.4 Left open: templates and exports (route 3) and the preview route (route 8)

- DeepSeek, attempt 2, left templates open (GET and HEAD).
- In DeepSeek attempt 2 and MiMo attempts 1 and 3, the main export folder was refused but the temporary export folder inside it still served its artifact.
- MiMo, attempt 3, refused most withheld resources on the preview route, but a plugin marked excluded was still served there and at its direct address.

### 4.5 What they got right

Every completed attempt refused withheld snippets and disk-only snippets and kept the owner's full access to listings. MiMo's attempts were broad: they also covered file APIs, search and attribute views beyond the task's routes. The failures do not come from misreading the bug. They come from route coverage (DeepSeek) and from how documents use widgets (MiMo).

### 4.6 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (19–31 minutes). In attempts 1 and 2 it settled early on one file, `kernel/server/serve.go`, and fixed the routes there. Listings, the catalog and the per-document rule elsewhere stayed open.
- **MiMo-V2.6-Pro:** slow (99 minutes to the full 2 hours) and thorough across routes. Its reference collector missed widget blocks, which cost it the coupled functional tests in every attempt.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each, 2 hours per attempt.
- Network: the agent could reach only the two model APIs, and web tools were disabled. The repository has no git history. The hidden tests are copied in only after the agent stops.
- Grading: for the counted attempts, grading ran after the agent stopped, with the hidden tests copied from the trusted test folder. The delivered package grades in a separate container that applies only the agent's source diff; the report and tests are the same.
- Every counted attempt was audited before it counted:
  - no access to the hidden tests and no lookups;
  - grading started after the agent stopped;
  - the score reflects the model's code.
- What counts: an attempt that reaches the time limit is graded on its code and counts as a failure. An attempt cut off by a provider or network outage is not counted (none was).

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix scores 1.0 three times, and a hardening fix and a structurally different alternative fix both pass. Nine wrong-fix patches each fail only the route they leave out, and an owner-only gate fails the functional tests. Before any trial, a fairness review checked every test against an earlier wording of the report. The one blocking ambiguity it found was resolved, and a follow-up validation on the final report judged the task ready. After each attempt, a separate audit read the transcript and code and judged a genuine model failure.

**Does it hinge on one test?** No. Every attempt with complete per-test results failed at least two independent routes, and none reached 1.0 on security alone: the best was 18 of 20.

**Could the model have seen the answer?** Routes 6–9 are not covered by the published fix. The agent could not reach the internet or the hidden tests, and the audit found no lookups and no reads of hidden test names in any transcript.

**What does a 0.0 mean here?** A 0.0 means at least one legitimate behaviour broke, since any functional failure scores 0. The security column shows how many attack routes were closed: from 7 of 20 (DeepSeek attempt 2) to 18 of 20 (MiMo attempts 1 and 2).

## Appendix

| What | Contents |
|---|---|
| Task | report (`instruction.md`), `task.toml`, environment (Dockerfile, `injection.patch` adding the two task routes), reference fix (`solution/fix.patch`) |
| Hidden tests | two fixtures (server and API), 2 security files, 2 task functional files, 5 restored project test files, `test.sh`, `junit.py`, `score.py`, grader Dockerfile |
| Validation | gate record (nop, oracle 3/3, 12 check patches), fairness review and follow-up validation |
| Attempts | per attempt: score, per-test results, final code and the audit's findings |

Internal build slug: `siyuan-ds`. Counted jobs: `siyuan-ds-deepseek-r1-20261020-233228-n001`, `siyuan-ds-deepseek-r2-20261020-235227-n002`, `siyuan-ds-deepseek-r3-20261021-001405-n003`, `siyuan-ds-mimo-r1-20261021-004613-n004`, `siyuan-ds-mimo-r2-20261021-022617-n005`, `siyuan-ds-mimo-r3-20261021-042720-n006`.

Sources: `tasks/siyuan-unpublished-resource-exposure/` and the RESULTS.md section in the delivered repository; `build/siyuan-ds/` (notes, manifest, FAIRNESS.md, fairness validation, gate report, check patches, run logs); per-attempt `verifier/results.json`, `final-code/changes.patch`, transcripts and POSTMORTEM.json.
