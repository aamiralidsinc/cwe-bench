No, we don't follow this format. I've written the comparison to [reports/FRONTIER-SWE-FORMAT-COMPARISON.md](cwe-bench/reports/FRONTIER-SWE-FORMAT-COMPARISON.md). The archive is Klavis's generic task template. It's built for 8-hour build tasks, so a few of its parts don't fit our 2-hour security fixes; I listed those separately rather than counting them as misses. The Harbor version on our VM supports everything the template uses, so nothing blocks adopting it.

**A. Not followed exactly, but covered by something else of ours:**
- **Reference solution:** we apply a patch instead of copying a solution folder. The gate grades it like any submission.
- **Pre-publish checks** (reference scores 1.0, empty fix scores 0, shortcuts fail): our gate does all of this and more (wrong-fix checks per trap, a blind fix, a fairness review).
- **Hidden tests:** ours are copied in only at grading time, never visible to the agent.
- **Agent runtime pre-install:** we pre-install Claude Code, so Harbor skips its Node install. This breaks if a run asks for another Claude Code version or another agent.
- **Offline agent:** same effect as theirs, but we hard-code our two model hosts in each task (see B).
- **No git history:** they create a fresh one-commit repo; we delete `.git`. Same leak protection.
- **Scoring:** they score passed/total over all tests. Ours gives 1.0 only when everything passes, and 0 if a functional test fails. Solved vs unsolved comes out the same at a 1.0 threshold, but partial numbers differ, so this needs confirming with Klavis.
- **Verifier crashes:** theirs write no reward, so Harbor records an error. Ours writes 0, and only the post-run audit catches it: the flowise 0-test runs went into the raw logs as 0.0.
- **Hung submissions:** theirs score 0 within a time limit; ours never count and get re-run.
- **Tampering:** we kill the agent before grading and audit afterwards. That's only a partial cover for B1.

**B. Not covered, to include:**
1. **Separate verifier container.** We grade inside the agent's own container. Adopting it also fixes our regrade problem: Harbor can only regrade from saved artifacts in separate mode, and 137 of 186 round-1 runs couldn't be regraded.
2. **Agent runs as an unprivileged user (uid 1000).** Ours runs as root.
3. **Submission code never runs as root during grading.** Our tests run the project's code in-process as root.
4. **No model allowlist in the task file.** Allow the model host at run time instead. This one matters for delivery: with our two hosts hard-coded, Klavis's own model would be blocked.
5. **The instruction never mentions tests.** Ours says "Do not modify or add tests".
6. **Task file schema 1.4** and the full network and verifier settings.
7. **Klavis metadata:** the `klavis/` name prefix, author, keywords, difficulty, and the three explanation fields (difficulty, solution, verification).
8. **Canary GUID:** none of our tasks has one; this repo's other tasks do.
9. **A `metrics.json` with a status reason.**
10. **Per-test and whole-suite time limits inside the verifier.**
11. **Working directory `/workspace`** instead of our `/app`. Low priority.

**Suggested order:**
1. Items 4 and 5: small changes that block delivery.
2. Items 6 to 10: template changes, re-rendered across all tasks by script.
3. Items 1 to 3 together: piloted on jackson-databind-sib2 first, since that's the structural change.

**For Klavis:** confirm the scoring rule, and whether they want the timer, a README per task, and `/workspace` instead of `/app`.



# cwe-bench tasks vs Klavis's frontier-swe template (2026-10-20)

**What was compared:**
- **Theirs:** `reports/frontier-swe.tar.gz`, Klavis's generic Harbor task template (schema 1.4).
- **Ours:** `builder/templates/` (`task.toml`, `test.sh`, `score.py`) and
  `harness/claude-code.Dockerfile.snippet`, plus two built tasks on the VM:
  - `jackson-databind-sib2`, hand-built;
  - `n8n-ds`, built by the pipeline.
- **Feature support** was checked in the installed Harbor (`0.23.1.dev`, VM).

**Short answer: no, we do not follow this format.** The largest differences are four:
- the verifier runs in the agent's own container (`shared`), not a separate one;
- the agent runs as root;
- the model-API allowlist is hard-coded in `task.toml`;
- the instruction mentions tests.

Every template feature is supported by our Harbor version: schema 1.4, `environment_mode =
"separate"`, `artifacts`, `--allow-agent-host`, and `[agent].user`.

**Read with care.** The template is written for **long-horizon build tasks** (8 hours, build from
a spec, a pytest suite). Some of its parts do not fit a 2-hour security-fix task. Those are listed
separately in part C.

---

## A. Not followed exactly, but covered by another mechanism of ours

| # | Template rule | What we do instead (the covering mechanism) | Gap left |
|---|---|---|---|
| A1 | `solution/solve.sh` overlays `solution/workspace/` onto the workspace | `solve.sh` applies `solution/fix.patch`; `gate.py --only oracle` grades it like any submission (twice, identically) | none |
| A2 | Before publishing: oracle scores 1.0, nop scores 0.0, shortcut solutions score 0 | `builder/gate.py`: nop, oracle, and wrong-fix patch checks (shallow fix, over-broad fix, one per trap), plus a blind fix and a fairness review | none; ours is stronger |
| A3 | Hidden tests stay in `tests/`, never in the agent image (memorization) | `test.sh` copies the real tests in only at grading time; the image is pre-built against stubs | none |
| A4 | Pre-install the agent runtime: an official Node tarball, so Harbor's probe installs no Debian `npm` module tree | `harness/claude-code.Dockerfile.snippet` pre-installs Claude Code natively. Harbor's `install()` returns early when Claude Code is already present at the requested version, so the Node probe never runs | If a run asks for a different Claude Code version, or a different agent, Harbor falls back to installing Debian `nodejs`/`npm`. Our Java and Python images have no node, and the offline agent cannot reach apt. |
| A5 | Agent offline: `[agent] network_mode = "no-network"`, model API allowed with `--allow-agent-host` | `[agent] network_mode = "allowlist"` with `allowed_hosts = [api.deepseek.com, api.xiaomimimo.com]`; verified by `harness/offline-check` | Covers the agent phase only: the agent is offline apart from its model. The hosts fixed in the task file, and the open network during grading, are not covered (B4). |
| A6 | Starting project as a fresh git repo with one commit ("Starting project"), no upstream history | We delete `/app/.git` entirely after checkout, so no later fix leaks. `build/harvest_code.py` records the final diff | The agent has no git baseline to diff against. Harmless, and cheap to match. |
| A7 | reward = passed / total over the whole suite; `metrics.json` reports `scoring_mode: "threshold"` | `score.py`: 1.0 only when every security and functional test passes; otherwise the security fraction (capped at 0.99), or 0 if any functional test fails | At a 1.0 threshold, solved or unsolved comes out the same. The partial numbers differ, so **confirm with Klavis** which scoring they expect. |
| A8 | Verifier defects (`infra:*`) write no reward, so Harbor records an error instead of a misleading 0 | `score.py` scores a group with no results as failed, which writes 0. The post-run Opus audit (`build/postmortem.py`) and `build/audit/excluded_runs.tsv` catch these runs before they count | The raw ledgers still show a 0. The flowise runs that ran 0 or 16 of 32 tests were logged as 0.0. |
| A9 | A hung submission scores 0 inside `BUILD_TIMEOUT` + `SUITE_TIMEOUT`, so a reward is always written | Our rule "timeouts and cut runs never count" (`TRIAL-PROCEDURE.md`); `trial.py` reruns ungraded runs | Reruns cost time, and there are no per-test timeouts in the template test.sh. |
| A10 | Tampering: files the agent must not change stay outside `artifacts` and live in the verifier image | Shared container, mitigated three ways: `test.sh` kills every Claude Code process before grading; tests are copied in at grading time; the post-run audit checks for tampering | Partial: see B1. |

---

## B. Not covered so far: to include

Ordered by importance for delivery.

| # | Template rule | Ours today | What to change |
|---|---|---|---|
| B1 | **Separate verifier.** `[verifier] environment_mode = "separate"`; a verifier image from `tests/Dockerfile`; only the `artifacts` (`/workspace`) cross over | `environment_mode = "shared"`: grading runs inside the agent's container, after the agent stopped | Add `tests/Dockerfile` (same toolchain plus test runner), `artifacts = [{source = "/app" or "/workspace", exclude = [...]}]` and `environment_mode = "separate"`. It also fixes our regrade problem: Harbor regrades from artifacts alone only in separate mode (`harbor/trial/regrade.py`), and 137 of 186 round-1 runs could not be regraded. Needs `test.sh`, `gate.py` and `harvest_code.py` adapted. |
| B2 | **Agent as an unprivileged user.** `[agent] user = "agent"`, uid 1000, created in both images | The agent runs as root | Create the uid-1000 user in both Dockerfiles, `chown` the workspace, and set `[agent] user = "agent"`. Install Claude Code where that user can run it (our snippet installs under `/root`). |
| B3 | **Submission code never runs as root during grading.** The verifier orchestrates as root, but runs the build and every submission process as uid 1000 (`setpriv`, no capabilities, clean env, `sandbox` fixture); `/tests`, `/logs/verifier` and the `LOCK` paths are made root-only and checked unreachable | Our tests run the project's code in-process as root (JUnit, vitest, pytest importing the library) | Run the native test runner as uid 1000, with a clean environment and the results written to a root-owned path. Make `/tests` and `/logs/verifier` root-only first, and kill leftover uid-1000 processes afterwards. Their `test.sh` and `conftest.py` are the model; we keep JUnit XML from any runner. |
| B4 | **No allowlist in `task.toml`.** `network_mode = "no-network"`, with the model API allowed at run time (`--allow-agent-host`); the template says "Do not add an allowlist here". The verifier is `no-network` too | `[agent]` allowlist with our two hosts, in every task. No `[verifier]` or `[environment]` network setting, so Harbor's default applies: **the verifier phase runs with public internet** (checked in `harbor/trial/network_policy.py` and `models/task/config.py`) | Set `[agent] network_mode = "no-network"` and `[verifier] network_mode = "no-network"`, and pass `--allow-agent-host=api.deepseek.com --allow-agent-host=api.xiaomimimo.com` in `harness/run_trial.sh`. Klavis's model is **not** hard-blocked: `--allow-agent-host` extends a task's allowlist. But every run of our tasks leaves our two providers reachable, which breaks their no-network convention, and the hosts belong to the run, not the task. |
| B5 | **The instruction never mentions grading, tests, scores or verification** | Our standard constraints block says "Do not modify or add tests" | Drop that line. With a separate verifier (B1) the agent's test edits cannot matter. Keep "do not look up the upstream fix" (the template has "Do not look for existing implementations elsewhere"). State "There is no network access", as the template does. |
| B6 | **`schema_version = "1.4"`**, plus the full `[verifier]` / `[verifier.environment]` / `[environment]` blocks: `network_mode`, `os`, `gpus`, `workdir`; build network `public`, verifier `no-network` | `schema_version = "1.1"`; only cpus, memory and storage set | Update `builder/templates/task.toml` and re-render all tasks. |
| B7 | **Klavis metadata:** `name = "klavis/<slug>"`; `[task] keywords`; `authors` with name and email (Klavis, research@klavis.ai); `[metadata] author_name`, `author_email`, `difficulty`, `category`, `tags`, `difficulty_explanation`, `solution_explanation`, `verification_explanation` | `name = "cwe-bench/<slug>"`, author `mason-skillmaker`; our own fields (`cwe_id`, `advisory`, `repo`, commits, `entry_point`, `source`); no difficulty, explanations or keywords | Add the template fields. Our own fields can stay, since `task.toml` is never visible to the agent. The three explanations can be generated from the manifest and notes. |
| B8 | **Canary GUID** (`# harbor-canary GUID <...>`) at the top of `task.toml`, both Dockerfiles and `test.sh` | none in any cwe-bench task (this repo's other tasks do carry one) | Generate one GUID per task and stamp all four files. |
| B9 | **`metrics.json`** with a status (`scored`, `no_submission`, `build_failed`, `build_timeout`, `missing_output:*`, `suite_timeout`, `infra:*`) and the passed/failed/errors/skipped/total counts | `results.json` (per test) only | Write `metrics.json` from `score.py`. On a verifier defect, write no reward (closes the gap in A8). |
| B10 | **Time limits inside the verifier:** per-test `TEST_TIMEOUT`, and `BUILD_TIMEOUT + SUITE_TIMEOUT` a few minutes under `[verifier].timeout_sec` | Per task, ad hoc (VM, 2026-10-20): all 115 `test.sh` wrap their test groups in `timeout`, but only 11 set a per-test limit. In 10 tasks the group limits add up to more than `[verifier].timeout_sec`: arc-ds, astro-csrf-origin, astro-ds, ckan-mcp-server-ds, orval-ds, seaweedfs-ds, seaweedfs-s3tables-authz, summarize-ds, theia-ds (one 10000 s limit under a 900 s verifier), whistle-ds | Add them to `builder/templates/test.sh` (closes the gap in A9). |
| B11 | **Workdir `/workspace`** | `/app` | Low priority: it touches every Dockerfile, test and patch path. Do it together with B1, or ask Klavis whether `/app` is acceptable. |

---

## C. Template parts that probably do not apply to security-fix tasks (confirm with Klavis)

- **8-hour budget, `timer.sh`, and the "Time" section** in the instruction. Our tasks are sized for
  about 45 minutes of expert work within a 2-hour limit. A timer is cheap to add if they want it.
- **`BUILD` / `OUTPUTS` / `LOCK` / `FORBIDDEN`.** These are for build-from-spec, port and clone
  tasks (no wrapping the original, no FFI). A fix to an existing project has nothing to lock or
  forbid, beyond the hidden tests (A3).
- **A pytest-only verifier image.** We test Java, Go, TypeScript, Rust and Python projects with their
  native runners; B3 keeps that, but runs them unprivileged.
- **Resources:** they use 4 CPUs and 16 GB for the agent, and 4 CPUs and 8 GB for the verifier; ours
  are typically 2 CPUs and 4 GB. Raise them only where a task needs it.
- **The template's `README.md`** is an author guide, not a per-task file. This repo's own tasks do
  carry a per-task README checked against `task.toml`, so **ask** whether Klavis wants one for each
  cwe-bench task.

---

## Suggested order

1. **B4 and B5:** small changes, and they block delivery.
2. **B6, B7, B8, B9, B10:** template-level, scriptable re-render of every task.
3. **B1, B2, B3 together:** the separate verifier with unprivileged execution. This is the
   structural change, and B11 rides along. Pilot it on one task (jackson-databind-sib2), re-gate it,
   then roll it out.
4. Confirm A7 (scoring), C (timer, README) and B11 (`/app`) with Klavis.
