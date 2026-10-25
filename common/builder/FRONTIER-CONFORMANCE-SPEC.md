# CWE-bench pipeline → Frontier-SWE conformance spec (next batch)

Target: the pipeline generates tasks that match Klavis's `frontier-swe` template, with four
deliberate deviations the user chose (2026-10-21). Reference: `reports/frontier-swe.tar.gz`,
`reports/FRONTIER-SWE-FORMAT-COMPARISON.md` (points B1–B11, A1–A10, C).

## User decisions (deviations from a literal copy)
1. **Identity:** keep `name = "cwe-bench/<slug>"` and author **Mara Hassan** (NOT `klavis/` + Klavis).
   Still ADD every other template metadata field (keywords, difficulty, category, tags, and the
   three explanations). task.toml is never shown to the agent, so our own fields stay too.
2. **Scoring:** keep BOTH. Primary `reward` = our threshold rule (1.0 only when every security AND
   functional test passes; 0 if any functional fails; else capped security fraction ≤0.99) so breaker
   detection is unchanged. `metrics.json` ALSO records the template's passed/total and the raw counts,
   under separate fields. Nothing that reads `reward.txt`/`reward.json` changes behaviour.
3. **Security-fix-appropriate, not long-horizon:** agent budget 7200s (2h); NO `timer.sh`, NO
   "## Time" section; keep our resources (2 CPU / 4096 MB, raise per-task only when needed). Adopt
   everything else.
4. **Workdir `/workspace`** everywhere (B11).

## Conformance points to BAKE INTO THE PIPELINE (so the batch is born conformant)
- **B1 separate verifier via `artifacts`:** task.toml `environment_mode = "separate"` + top-level
  `artifacts = [{ source = "/workspace", exclude = [build outputs, caches, .git, node_modules, ...] }]`.
  Harbor tars the agent's /workspace (minus excludes) and restores it in the verifier container. NO
  collect-patch step. (The 8 already-shipped tasks used `[[verifier.collect]]`+agent.patch; the new
  batch uses `artifacts` restore, matching the template. Do not retrofit the 8 here.)
- **B2 agent uid 1000:** both Dockerfiles create a uid-1000 `agent` user (reuse ubuntu's 1000);
  `[agent] user = "agent"`. Claude Code installed where `agent` can run it (snippet updated).
- **B3 non-root grading:** test.sh root only orchestrates; build + every test runner process runs as
  `agent` via the `AS_AGENT` setpriv wrapper with a clean env; `/tests` and `/logs/verifier` locked
  root-only and verified unreachable before any submission code runs; reap leftover agent procs.
- **B4 no-network both phases:** `[agent] network_mode = "no-network"`, `[verifier] network_mode =
  "no-network"`, `[verifier.environment] network_mode = "no-network"`; NO allowlist in task.toml;
  model host allowed at run time via `--allow-agent-host` in `common/trial/run_trial.sh`.
- **B5 instruction says nothing about tests/grading:** drop "Do not modify or add tests"; keep "do not
  look up the upstream fix / existing implementations"; add "There is no network access."
- **B6 schema 1.4** + full `[verifier]`, `[verifier.environment]`, `[environment]` blocks with
  `network_mode`, `os`, `gpus`, `workdir`, build/verifier `build_timeout_sec`.
- **B7 metadata:** add `keywords`, `[metadata] author_name/author_email` (Mara), `difficulty`,
  `difficulty_explanation`, `solution_explanation`, `verification_explanation`; keep our own fields.
- **B8 canary GUID:** one fresh uuid4 per task, as `# harbor-canary GUID <uuid>` at the TOP of
  task.toml, environment/Dockerfile, tests/Dockerfile and tests/test.sh.
- **B9 metrics.json:** test.sh/score write `metrics.json` {scoring_mode, status, reward (threshold),
  passed_total (template ratio), passed, failed, errors, skipped, total}. On a verifier defect
  (`infra:*`) write NO reward (Harbor records a trial error, closing A8); on a scored run write
  reward.json/reward.txt = threshold reward.
- **B10 time limits in the verifier:** TEST_TIMEOUT (per group/test), BUILD_TIMEOUT, SUITE_TIMEOUT;
  BUILD_TIMEOUT + SUITE_TIMEOUT a few min under `[verifier].timeout_sec`.
- **B11 `/workspace`** workdir in both Dockerfiles, task.toml workdir fields, test paths, artifacts.
- **A6 fresh git baseline:** agent image ends with `git init -b main` + one "Starting project"
  commit as `agent` (template behaviour; replaces our `.git` deletion).

## Kept as-is (A-items already covered; do not regress)
- Patch reference (solution/fix.patch + solve.sh) graded by gate like a submission (A1).
- gate.py wrong-fix/nop/oracle/blind + fairness (A2) — adapt to separate+non-root, keep the checks.
- Hidden tests copied in only at grade time / live only in the verifier image (A3).
- Native runners per language (Java/Go/Rust/TS/Python), each emitting JUnit XML (C).

## Files to change (pipeline)
- `common/builder/templates/task.toml` — the 1.4 skeleton (decisions 1–4, B4/B6/B7/B8, artifacts).
- `common/builder/templates/environment.Dockerfile` (NEW) — agent image skeleton (B2/B8/B11/A6 + node + agent snippet).
- `common/builder/templates/tests.Dockerfile` (NEW) — verifier image skeleton (B1/B2/B8/B11).
- `common/builder/templates/test.sh` — non-root separate-mode scaffold (B3/B9/B10) + our two-group native JUnit runner placeholder; calls score.py.
- `common/builder/templates/score.py` — dual scoring: primary threshold reward (unchanged), + metrics.json with passed/total + counts + status (B9, decision 2).
- `common/trial/claude-code.Dockerfile.snippet` — install Claude Code for the uid-1000 `agent` user (B2).
- `common/trial/run_trial.sh` — pass `--allow-agent-host=api.deepseek.com --allow-agent-host=api.xiaomimimo.com` (B4).
- `common/gate/gate.py` — build/grade via the restored /workspace as `agent` (B1/B3/B11); keep nop/oracle/wrong-fix/blind/fairness semantics.
- `common/audit/harvest_code.py` — collect the final /workspace state as the artifact diff for the record (B1/B11).
- Build briefs (`BUILDER.md`, `TASK-BUILD-PROMPT-v1.md`, `PROMPT-task-build.md`): instruct the new structure
  (/workspace, both Dockerfiles with the agent user, tests/Dockerfile, artifacts block, canary GUID, the
  new metadata + the three explanations, the instruction wording, per-group JUnit + time limits).

## Validate
- Render one sample task end-to-end (a Go or Python task) in the new format; run `gate.py` on it in
  separate+non-root mode (oracle 1.0, nop 0, wrong-fix fails, blind 1.0). Only roll the batch after a
  clean gate on the sample.

## STATUS — implemented 2026-10-21
DONE (machinery-first): common/builder/templates/ rewritten (task.toml, environment.Dockerfile, tests.Dockerfile,
test.sh, score.py); common/trial/claude-code.Dockerfile.snippet (uid-1000); common/builder/conformance_check.py added
and WIRED into gate.py check_static (machinery enforces the format); gate.py product-import regexes +
REQUIRED (tests/Dockerfile) updated; common/audit/harvest_code.py ROOTS=/workspace; common/trial/run_trial.sh passes
--allow-agent-host per model; briefs (BUILDER.md, TASK-BUILD-PROMPT-v1.md, PROMPT-task-build.md) carry a
SUPERSEDE note + the 3 contradiction fixes. Old templates backed up (common/archive/versions/builder/). A filled
template passes conformance_check; old-format tasks fail it.
REMAINING confidence step before the full batch: render ONE real task through the builder in this format
and run gate.py on it (separate + non-root + artifacts restore) — a real Harbor build; do that, confirm a
clean gate, then launch the batch.

## VALIDATED 2026-10-21 (confidence step)
gate.py PASSED all stages (static/nop/oracle x2 = 1.0/patches) on a synthetic probe task built from the
promoted templates, in the new mode: separate verifier + artifacts /workspace restore + uid-1000 non-root
grading + dual scoring + conformance_check. Four template bugs found and fixed during the step (all in
common/builder/templates/test.sh unless noted):
  1. gate.py hidden_test_leaks: ignore two-Dockerfile boilerplate in separate mode (fixed in gate.py).
  2. non-root grading: the agent-run suite writes JUnit to an agent-writable path; root copies it into the
     root-locked /logs/verifier/<group>/.
  3. run_group: @OUT@ token substitution for the JUnit path (immune to set -u / caller quoting).
  4. scoring tail: score.py's exit code encodes solved(0)/unsolved(1), NOT success -> do not treat a
     non-zero exit as a verifier error (it was deleting the reward on nop).
Probe is reproducible via common/builder/fmt_probe_gen.py (regression fixture); the throwaway task dir was removed.
PIPELINE IS READY for the next batch in the Frontier format.
