# Handoff: build and evaluate one CWE-Bench-style task (posit-dev/py-shiny)

Date: 2026-10-14. This file is the full context for an agent that will run an existing task-building pipeline on one candidate. It contains no API keys; use your own access.

## 1. What the project is

Klavis is building a pipeline that produces **100-200 Harbor-format security-fix tasks** targeting CWE-Bench (a private benchmark, no reference tasks; category: "security fixes: realistic vulnerabilities in real code paths").

**Goal:** every accepted task scores **pass@3 = 0 on both DeepSeek V4.1 Flash (max reasoning) and Xiaomi MiMo-V2.6-Pro**. A failure counts only if the task passes the task rubric check **and** trial analysis attributes the failure to model capability, not a task defect. Quality comes first.

Task spec (from the brief):

| Component | Spec |
|---|---|
| Format | Harbor: `instruction.md`, `task.toml`, `environment/`, `solution/` (oracle), `tests/` (hidden) |
| Environment | Real open-source repo in its vulnerable state; dependencies and any required services installed |
| Instruction | Realistic vulnerability report: observed impact and how it is triggered. **No fix, no file or function hints** |
| Security tests (fail -> pass) | Exploit the vulnerability through a real entry point and assert it is blocked, **including variants beyond any PoC in the report** |
| Functional tests (pass -> pass) | Existing tests of the affected code plus legitimate-use cases, so over-blocking or removing the feature fails |
| Grading | Partial score (meaning not yet defined, see section 7) |
| Metadata | CWE ID, language, repo, source (mined or injected), entry point |

Out of scope: build-from-scratch or secure-code generation; detection-only or exploit-only tasks; fixes that are only a dependency bump or config change; contrived snippets or unreachable code.

Important: the tasks must be **real fixed bugs** (mined from GitHub advisories) or injected realistic bugs. We are not inventing unfixable problems. "Models fail" is only the selection filter applied at the end, after the task is proven valid and fair.

## 2. Your job

Take the single candidate in section 3 through the full pipeline:

1. Resolve the **vulnerable commit** (the parent of the fix commit) and build a working environment at that commit.
2. Write the hidden tests: security (fail -> pass, with variants) and functional (pass -> pass).
3. Write `instruction.md` as a realistic report with **no hints** about files, functions or the fix.
4. Validate: the oracle fix (adapted from the upstream fix, but see rule below) passes all tests; the vulnerable state fails the security tests and passes the functional tests.
5. Run the rubric check.
6. Run both models (3 trials each) on the real task, with real code access and the hidden tests as grader.
7. Trial analysis: for each failure, classify as **model capability** or **task defect**, with evidence (e.g. "patched `../` but not `%2e%2e%2f`; variant test X failed").
8. Return the output described in section 6.

Rules:
- **The tests must accept any correct fix**, not only the upstream patch. Do not assert on the upstream implementation details.
- **The models must never see the fix.** Strip or re-initialise git history (no future commits, tags or branches), install the package from the vulnerable source (not the fixed PyPI release), scrub changelog/release-note/comment mentions of the advisory, and make sure the Docker layers and caches contain no fixed code. Confirm whether the trial sandbox has network access (if it does, the model could look up the advisory); this is currently unknown, see section 7.
- Do not write API keys into any file you create or share.

## 3. The candidate

Record produced by our miner (GitHub Security Advisories, reviewed, pip ecosystem):

```json
{
  "ghsa_id": "GHSA-47c3-hpmg-7j6p",
  "cve_id": "CVE-2026-108258",
  "ecosystem": "pip",
  "repo": "posit-dev/py-shiny",
  "cwes": ["CWE-22"],
  "severity": "medium",
  "published_at": "2026-10-09T20:56:37Z",
  "summary": "Shiny for Python has path traversal in bookmark restore",
  "vulnerabilities": [{"package": "shiny", "vulnerable_range": ">= 1.4.0, <= 1.6.3", "first_patched": "1.6.4"}],
  "fix_commits": [{"repo": "posit-dev/py-shiny", "sha": "1d8ecb46cbc9621b7dc8812111d26692e086b376"}],
  "leak_map": {"external_write_ups": [], "pull_requests": [], "issues": []}
}
```

- **Fix commit:** `1d8ecb46cbc9621b7dc8812111d26692e086b376`. The **parent commit (vulnerable state) is not resolved yet**: resolve it with git.
- **Files the real fix touched** (ground truth for validation only; never show to the models, never put in the instruction): `shiny/_app.py`, `shiny/bookmark/_bookmark.py`, `shiny/bookmark/_bookmark_state.py`, `shiny/bookmark/_restore_state.py`, `shiny/input_handler.py` (plus test files, excluded here).
- **Why this one:** published 2026-10-09 (after any plausible model training cutoff), no external write-ups, and the fix spans 5 files, so it is more likely to be hard but fair.
- **Likely entry point:** the bookmark-restore path, where a client-supplied bookmark ID reaches the filesystem. Confirm from the code; do not trust this summary blindly.
- **Fallbacks if this one cannot be built:** `GHSA-68w4-83fh-f2w8` (pyload/pyload, CWE-287, fix touched `src/pyload/core/api/__init__.py` and `src/pyload/core/database/user_database.py`), and `GHSA-3hj7-6vmj-h8v4` (john-broadway/pacioli, CWE-863; messy 11-file fix incl. docs, likely a poor task).

## 4. Findings so far (be careful how you use them)

**Mining (GitHub Security Advisories API, pip + maven, published since 2025-01-01):** 592 candidates, 467 (79%) link a fix commit. 72 of 143 fixed repos have two or more fixed advisories. 361 fixed advisories have no external write-ups. Python skews to AI-tooling repos (heavy dependencies may break builds); Java builds are heavy.

**Model access (verified 2026-10-14 via each provider's /models endpoint):**
- DeepSeek: base `https://api.deepseek.com` (OpenAI-compatible `/chat/completions`). Models listed: `deepseek-flash` (= V4.1 Flash; the older `deepseek-v4-flash` name is an alias per DeepSeek docs) and `deepseek-v4-pro`. Reasoning is set with top-level `"thinking": {"type": "enabled"}` and `"reasoning_effort": "max"`. DeepSeek's docs only document `"high"`; `"max"` was accepted without error by the API but is not documented there.
- MiMo (Xiaomi direct): base `https://api.xiaomimimo.com/v1`, model `mimo-v2.6-pro`. Also listed: `mimo-v2.5`, `mimo-v2.5-pro`, `mimo-v2.6-flash`, `mimo-v2.6-pro-ultraspeed` (plus TTS/ASR models).
- Reasoning tokens count toward `max_tokens` on both. **DeepSeek on max effort used all 4,096 and then all 16,000 tokens thinking and returned an empty answer.** Budget at least 32-64k tokens for max effort, or the run proves nothing. MiMo finished in about 7k tokens.
- Latency: DeepSeek about 20-85 s per call; MiMo about 40-180 s per call (set client timeouts to 900 s or more).

**One prompt-only probe (no source code shown; one trial per model; NOT evidence of capability):**
- `pacioli` (obscure repo): both models said plainly they did not recognise it and refused to invent file names.
- `py-shiny`: MiMo recognised the project and the bookmark subsystem, said up front it could not read the source, diagnosed an unsanitised client-supplied bookmark ID joined to a filesystem path (plausible, matches the advisory title), but guessed file names wrongly (`state_store.py`, `restore_state.py`; real files have leading underscores). DeepSeek returned an empty answer (out of tokens).
- This round gave the models no code and had no grader. It cannot show "the model cannot fix it" or "the model hallucinated". Only a real task with hidden tests can.

## 5. Known pitfalls

- Hidden tests that are too strict (reject valid fixes) or too narrow (only the PoC) are the biggest source of defective tasks.
- Empty or truncated model output is a harness problem, not a failure. Record the finish reason and token usage for every trial; discard truncated trials.
- Installing the package from PyPI can pull the already-fixed release into the environment. Install from the vulnerable commit.
- Do not read anything into model recognition of a project as proof of memorised fixes without checking the produced patch against the tests.

## 6. Output we need back

1. The Harbor task folder (`instruction.md`, `task.toml` with metadata, `environment/`, `solution/`, `tests/`).
2. Validation evidence: test results on the vulnerable commit (security fail, functional pass) and with the oracle fix (all pass), including the variant attacks used.
3. The rubric-check result with reasoning.
4. For each model and each of the 3 trials: the full agent trajectory or patch, test results, finish reason, token usage, wall time, and cost if available.
5. Trial analysis: per failure, a classification (model capability or task defect) with concrete evidence.
6. A short list of what broke, what was slow, and any changes you made to the pipeline.
7. Timing and cost per stage, so we can plan the 100-200 task run.

## 7. Open questions (do not assume; ask the user)

- Report-style instruction (as in our brief) or audit-style ("audit the code and fix what you find", as the public CWE-Bench describes)? Public CWE-Bench also has no partial credit, while our brief says "partial score". What does partial score mean here?
- Does the trial sandbox have network access? What agent scaffold and settings will the real trials use?
- What are the two models' training cutoffs? Not yet measured.
- What share of the final set may be injected rather than mined?
