# Running builds and trials on GitHub Actions: how precision_validation did it

**Status:** documentation only (2026-10-28). Nothing here has been run for the diversity experiment.

**Source:** `experiments/precision_validation/` (closed 2026-10-24; see its `README-DO-NOT-USE.md`). Its `actions/`
folder is local only and not in git.

**Why this matters now:** the VM is busy with the scale-run pipeline. precision_validation faced the same problem
and ran 61 builds and about 120 trial jobs on GitHub-hosted runners instead.

**Internal only.** Never copy this folder to the client repo.

## 1. What the experiment was, and what came of it

**The question:** does a frozen pre-build score raise the both-model breaker rate?

| Arm | Candidates | Both-model breakers |
|---|---|---|
| A | 21 above the score bar | 2 (about 10%) |
| B | 40 random controls below the bar | 5 (about 12.5%) |

**The score did not help.** The Actions route did work, end to end:
- builds, gate and trials on runners;
- results brought back and imported into the VM ledger.

**Seven of its both-fail tasks are now in the ledger,** as `ext-actions-pv-*` jobs (VM `build/audit/EXTERNAL-RUNS.md`).

## 2. The approach in one picture

```
Mac                                   GitHub (public repo per account)                 Mac / VM
---                                   --------------------------------                 --------
make_payload.sh                       repo: workflow + README + payload.tar.gz.gpg
  stage builder copy + tasks   --->   secrets: PAYLOAD_KEY, DEEPSEEK_API_KEY, MIMO_API_KEY
  tar + gpg AES-256                   workflow_dispatch(ids, mode)
  id map t01.. -> slug kept local       matrix: one runner per task id (max-parallel 20)
launch_account.sh (per account)          free disk; Docker on /mnt
  create repo, push, set secrets          install pinned Harbor + Claude Code
  dispatch its share of ids               decrypt payload; mask slug + path in logs
                                          run build + gate (or trials)
                                          pack outputs -> gpg -> artifact (kept 7 days)
                                                                               --->   fetch_results.sh /
                                                                                      robust_fetch.sh: download,
                                                                                      decrypt into results/<id>/
                                                                                      import trial runs into the
                                                                                      VM ledger as ext-actions-*
```

## 3. Builds on Actions (`reference/workflows/build-matrix.yml`)

**Inputs:**
- `ids`: comma-separated opaque ids, or `all`;
- `mode`: `probe` or `build`.

**One matrix job per task.** Settings:
- `timeout-minutes: 355`, just under GitHub's 6-hour job limit;
- `max-parallel: 20`;
- `fail-fast: false`.

**Steps:**
1. **Free disk:** remove the preinstalled SDKs (dotnet, android, ghc, CodeQL…), then move Docker's data root to the
   larger of `/` and `/mnt`. Write `daemon.json` with address pools and a shutdown timeout.
2. **Tools:** `uv`, then `harbor==0.23.1.dev202609170426` and Claude Code `2.1.302`. Both pins matched klavis-vm, so
   results compare.
3. **Payload:** `gpg -d payload.tar.gz.gpg` with the `PAYLOAD_KEY` secret.
   - The project root path and the task slug are read from the payload and masked with `::add-mask::`, so the
     public log never shows them.
   - The root is recreated at the same absolute path the build prompts name (`pv_path`).
4. **Model key:** the `DEEPSEEK_API_KEY` secret is written to `~/.tb-graders/cwe/models.env` (mode 600). The
   builder drives DeepSeek through `drive.sh`, as on the VM.
5. **Build and gate:** `pv_pipeline.sh deepseek <slug>` runs build, then gate (nop, oracle, patches). A
   5-minute heartbeat line goes to the log, then one result line: `gate marker=.sound|.unsound|.gate_error`.
6. **Pack:** the task's `build/`, `tasks/`, gate jobs and logs are tarred, encrypted with the same key and uploaded
   as an artifact named by the opaque id (7-day retention).

**Probe mode:** checks four things before any spend:
- Docker works;
- DeepSeek answers through Claude Code;
- a Harbor smoke task grades 1;
- Docker has at least 15 GB free.

**What is public:** the workflow, a one-line README and opaque encrypted blobs. The logs show ids, versions, disk,
heartbeats and the gate marker only.

## 4. Trials on Actions (`reference/workflows/trial.yml`)

**Inputs:**
- `build_run`: the build run whose artifact holds the task;
- `ids`;
- `model`: `deepseek` or `mimo`;
- `runs`: 3;
- `lock`.

**Steps:**
1. **Get the task:** `gh run download <build_run> -n <id>` inside GitHub (fast), then decrypt and relocate it to the
   path it was built at.
2. **Pre-build the image:** with open network, through a `nop` grade.
3. **Isolation:** the task's `task.toml` sets the agent phase to `no-network`. Harbor's `--allow-agent-host <model
   host>` then allows only the model API.
   - The `egress-probe.yml` workflow proved runner containers have open internet by default, and that
     `--network none` cuts it.
   - An iptables allowlist was tried first, then dropped in favour of the native mechanism.
4. **Trials:** `harbor run -a claude-code` with the same model settings as `drive.sh`.
   - DeepSeek: `deepseek-flash[1m]`, `reasoning_effort=max`, large output and thinking caps.
   - MiMo: `mimo-v2.6-pro`.
   - Settings: `--ak disallowed_tools=WebSearch,WebFetch`, `API_TIMEOUT_MS=1200000`, early stop on a solve, up to 3
     counted runs.
5. **Infra versus fail:**
   - A run with a Harbor exception, an agent API or auth error, `num_turns:0` or no reward is retried (up to 6),
     never counted as a model fail.
   - The job ends with a `SUMMARY <id> <model> solved= counted= infra= rewards=[…] status=` line.
6. **Pack:** rewards, `result.json`, verifier output and small logs are encrypted into a `trial-<id>-<model>`
   artifact.

**`trial-from-payload.yml`:** the same trial job, but the task comes from its own encrypted payload instead of a
build artifact. It was used to re-trial already-delivered packages (the "at-risk" seven).

**Orchestration (`reference/orchestrate.py`):**
- One workflow run per (task, model), not one matrix, so each task finishes on its own.
- It dispatches both models for every task (owner rule: MiMo-only breakers count too), polls every 2 minutes,
  reads the `SUMMARY` line from the job's console log through `gh api`, and re-dispatches a job that died without
  a summary (up to 4 times).
- Verdict per task: both-fail, DeepSeek-only, MiMo-only, both-solved or review.
- State in `results/orch/<arm>.state.json` (resumable), verdicts in `<arm>.verdicts.tsv`.

## 5. Capacity and timings seen

| Item | Seen |
|---|---|
| Build job (one task) | 63–189 min (arm A, one account's 7 jobs) |
| Trial job (one task, one model, up to 3 runs) | about 2.5 h (example: t04, 151 min) |
| Jobs per account at once | about **7** got runners in practice, below the configured 20; so the work was split, about 7 jobs per account |
| Accounts used | 6 (arm A on 3; arm B on 6, one of which never registered its workflow) |
| Runner | `ubuntu-latest`, standard GitHub-hosted runner (public repo, so no minute billing) |
| Artifact size | up to about 2.4 GB for large monorepos (angular, sakai) |
| Download to the Mac | about 0.5 MB/s over the home link; about 8 h for arm A's 20 artifacts |
| Artifact retention | 7 days |

## 6. Problems hit, and the fixes

| # | Problem | Fix / lesson |
|---|---|---|
| 1 | Only about 7 of 21 jobs got runners on one account (3 waves, 6–9 h) | split ids across accounts, about 7 each |
| 2 | One account's workflow never registered | its ids were moved to another account; check `gh workflow view` before dispatching |
| 3 | `gh run download <whole run>` died on "connection reset" with big artifacts; nothing came through in 2.5 h | `robust_fetch.sh`: per artifact, smallest first, 5 retries, decrypt at once |
| 4 | Every early trial failed with `UnknownApiError` | the task's agent phase is `no-network`; add `--allow-agent-host <model host>` |
| 5 | Arm-B MiMo "fails" were fake: `MIMO_API_KEY` was never set on those repos (no key, so the agent was not logged in and graded 0.0) | set every secret on every repo; count auth or no-op runs as infra, never as fails |
| 6 | The orchestrator read `solved=?` | the `SUMMARY` line goes to the job console, not to a file; read the console log through `gh api` |
| 7 | "TRIAL-INFEASIBLE" was mostly a false positive: the infra detector matched noise strings (MiMo "overloaded" retries, auth words in task source) on cleanly graded runs, including solves (`results/orch/INFEASIBLE-AUDIT.md`) | decide infra from Harbor's exception count and the reward, not from grepping text |
| 8 | 3 arm-A and 2 arm-B gate errors: a blind patch listed in the manifest was never generated | a builder defect in the frozen copy, fixed later in the live gate (blind-skip) |
| 9 | The safety classifier blocked the agent from `git push` and secret writes | those steps were done by the owner from staged commands |
| 10 | The artifact kept no agent transcript and no final code | audits had to work from tests, grades and logs; next time pack the transcript and `/workspace` |

## 7. Risks and open questions (decide before reusing)

1. **Whose accounts.** precision_validation used 6 accounts, including a friend's (`muhammadyasir-devsinc`) and
   others in `.env` (`fcopyleft`, `afarayafi`, `aamiralidev`). An earlier owner instruction in this project says
   **not to use borrowed friends' GitHub accounts for Actions.** Reusing the multi-account split needs the owner's
   decision on which accounts are allowed.
2. **GitHub's terms.** Two clauses to check before scaling. This is not legal advice; read the current text.
   - GitHub's Terms of Service limit a person to one free account.
   - The Actions terms bar using Actions for work unrelated to the software project in the repository.
   - A public repo that holds only an encrypted payload, spread over several accounts to multiply runners, is the
     pattern those clauses are about.
3. **Secrets on many repos.** The DeepSeek and MiMo keys and the payload passphrase sat as secrets on about 10
   public repos.
4. **Cleanup is still owed.** All 10 repos still exist and are public (checked 2026-10-28):
   - `{aamiralidsinc, marahassan8, muhammadyasir-devsinc}/build-matrix-k7`;
   - `{aamiralidsinc, marahassan8, muhammadyasir-devsinc, fcopyleft, afarayafi, aamiralidev}/build-matrix-b`;
   - `aamiralidsinc/atrisk-trials`.

   The tokens have no `delete_repo` scope, so they must be deleted in the web UI. Their artifacts expired after
   7 days; the encrypted payloads are still in the repos.
5. **Trial policy must match the VM.** `trial.yml` blocked web tools (`disallowed_tools=WebSearch,WebFetch`, model
   API only). Before results from Actions and the VM are mixed, check that the current VM trial setup uses the same
   policy.

## 8. What carries over to the diversity experiment, and what must change

**Reusable as-is (the pattern):**
- the encrypted payload;
- the opaque ids with a local id map;
- log masking;
- probe mode before spending;
- one matrix job per task for builds;
- one run per (task, model) for trials;
- the `SUMMARY` line;
- the robust per-artifact fetch;
- import into the VM ledger as `ext-actions-*` jobs.

**Must change:**
- **What goes in the payload.**
  - The payload root was precision_validation's frozen `root/` (the builder and gate of 2026-10-21, missing the
    later gate fixes). It must not be reused.
  - The diversity payload must hold copies of the **current** builder, gate and launch scripts (in `copied/`,
    logged in `copied/SOURCES.md`) and the sibling build prompts for the `diversity-*` slugs.
- **Infra detection:** use Harbor's exception count and the reward, not text grepping (problem 7).
- **Packing:**
  - pack the agent transcript and the final `/workspace`, so the post-run audits have the code;
  - set the MiMo key on every repo.
- **Where results go:** fetch artifacts onto the VM, not the Mac. Note the VM link is shared with the running
  pipeline.
- **Accounts:** settle which accounts may be used (section 7) before anything is created.

**Capacity, if the account question is settled:**
- about 7 jobs per account at once;
- builds of about 1–3 h;
- trials of about 2.5 h per (task, model).

Chunk 1 (66 builds) on 3 accounts is about 3 waves, 6–9 h. Its trials are 132 jobs, each up to about 2.5 h.

## 9. Files extracted (`reference/`, unchanged copies)

| Copy | Original (`experiments/precision_validation/actions/`) | Use |
|---|---|---|
| `workflows/build-matrix.yml` | `repo/.github/workflows/matrix.yml` | build + gate, one job per task |
| `workflows/trial.yml` | `repo/.github/workflows/trial.yml` | trials of one model, task from a build artifact |
| `workflows/trial-from-payload.yml` | `repo-atrisk/.github/workflows/trial.yml` | trials of already-built packages |
| `workflows/egress-probe.yml` | `repo/.github/workflows/probe.yml` | network isolation probe, no payload |
| `make_payload.sh` | `make_payload.sh` | stage, tar and gpg-encrypt the payload; local id map |
| `launch_account.sh` | `launch_account.sh` | create repo, push, set secrets, dispatch one account's share |
| `fetch_results.sh` | `fetch_results.sh` | download and decrypt one run's artifacts |
| `robust_fetch.sh` | `robust_fetch.sh` | per-artifact fetch with retries (use this one) |
| `orchestrate.py` | `orchestrate.py` | per-(task, model) trial dispatch, polling and verdicts |
| `repo-README.md` | `repo/README.md` | the public repo's README |

**Not copied, on purpose:**
- `ids*.local.json` (the opaque id to slug maps, and account and run ids);
- the payloads and `results/` (23 GB);
- the per-account repo working copies;
- the frozen `root/`.

The scripts read tokens from `~/terminal-bench/.env` at run time and contain no secrets. The passphrase lived in
`~/.tb-graders/cwe/precision_validation/payload.key`.

**Related records:**
- `experiments/precision_validation/actions/STATE.md` and `AUTONOMOUS-LOG.md`: the run diary;
- `results/orch/INFEASIBLE-AUDIT.md`;
- VM `build/audit/EXTERNAL-RUNS.md`: the ledger import.
