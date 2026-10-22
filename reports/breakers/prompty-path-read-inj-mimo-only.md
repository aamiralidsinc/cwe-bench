# prompty-path-read-inj — a MiMo-only result (DeepSeek solves, MiMo fails 3/3)

**Status of 2026-10-18. PROVISIONAL — not a confirmed both-models breaker.** This task is a *MiMo-only* result: MiMo-V2.6-Pro failed all 3 counted attempts, but DeepSeek V4.1 Flash solved it. Its pre-trial fairness review returned **NOT READY** and the required fairness changes have **not yet been applied**, and no post-run audit has been run on the MiMo attempts. Treat every number here as provisional until the fairfix + a re-trial + per-attempt audits are done.

Sources: the task build and validation records, the pre-trial fairness review, and the per-run trial detail. (The per-test breakdown and transcript audit that the jackson report relies on have **not** been produced for this task yet.)

## Summary

- **Result (provisional):**
  - MiMo-V2.6-Pro: 0.8333, 0.8333, 0.8333 — failed all 3.
  - DeepSeek V4.1 Flash: 0.8333, then 1.0 — **solved on run 2** (early-exit).
- So this is **not** a breaker (a breaker needs both models to fail all 3). It is a lead: a task that separates the two models.
- Every attempt finished on its own (no timeout). MiMo ran 29–38 minutes per attempt; DeepSeek ran ~5–7 minutes.
- MiMo's score is identical every time — **5 of 6 security routes closed, all functional tests passing, exactly one route left open each attempt.** It never broke a legitimate behaviour (no 0.0); it simply never closed the last route.
- **Caveat:** the fairness review found the one route MiMo keeps missing (the child-prompt tool route, T2) is tested in a way that can mis-score a correct fix. Because DeepSeek did reach 1.0, the route is passable — but the MiMo-only signal cannot be trusted until that test is fixed and the task is re-trialed.

## 1. The task

**Vulnerability (CWE-22 path traversal / CWE-200 information exposure).** microsoft/prompty, GHSA-wxhm-2mq7-7697 / CVE-2026-53598, Python runtime, at the pinned vulnerable commit. A `.prompty` document (YAML frontmatter + markdown body) is **author-controlled content** — applications load `.prompty` files from template galleries, shared repos or end users. A frontmatter reference such as `${file:...}` is read by the loader **relative to the prompt's directory with no containment**, so a hostile document can name a path that escapes the directory and have the contents of an unrelated file on the host pulled into the loaded prompt. Entry point: the public `prompty.load()` / `prompty.load_async()`.

**The rule (as given to the agent).** No path expressed in a prompt document may cause loading to read a file outside the prompt's own directory — for **every** way a document can name an external target, and regardless of how the path is spelled (upward-walking relative path, absolute path, or an outward symlink). When a path would escape, loading fails with a client-side error and nothing outside is opened or read; legitimate in-directory references keep working exactly as today (including a structured JSON/YAML reference that must still come back as parsed structured data).

**Four real routes to the same rule** (none named in the instruction, no file/function/count given):

| Route | Site | Why a solver might skip it |
|---|---|---|
| T1 — base `${file:}` sink (the report's example) | `loader.py` file branch | none; it is the obvious site. Lever: a one-shape fix misses the absolute-path and symlink shapes. |
| T2 — child-prompt tool path via OpenAI wire projection (real, unmodified upstream) | `executor.py` `_project_prompty_tool` | looks like a provider wire adapter for a tool feature, not `${file:}` expansion; different package from the loader. |
| T3 — `${prompt:}` fragment protocol | `loader.py` prompt branch → `utils.load_fragment` (different file) | reads as trusted plumbing / a composition helper for shipped fragments. |
| T4 — `base:` template include | `loader.py` `_build_agent` merges a `base:` document | reads as a separate inheritance / defaults-merge feature, not reference expansion. |

**Scoring.** Reward = security pass fraction, **0 if any functional test fails**. 6 security tests (one per route shape) + functional tests (legitimate in-directory references + the pristine upstream test suites). A score of 0.8333 = 5 of 6 security tests pass with all functional passing — i.e. exactly one route still open and nothing over-hardened.

## 2. Fairness status — NOT READY (fix not yet applied)

The pre-trial review rated T1, T3, T4 and all functional tests low-risk and fair, but flagged the T2 test and some leniency gaps:

1. **T2 test construction (high).** `test_prompty_tool_child_path_traversal` calls `agent = prompty.load(parent)` *outside* the block that expects a refusal. A fix that follows the instruction and rejects an escaping path **at load time** makes that line raise, so the test **errors** (a skip/error counts as a fail). Also the written invariant is scoped to "loading that document", but this sink fires during wire projection, not during load — so a fix that guards every read during load is compliant with the text yet still fails here. Required change: move the `load`/`tools[0]` calls inside the guarded block, and widen the invariant to "loading **or using** that document (including preparing or running the tools it declares)".
2. **Leniency gaps not caught by any test:** a prefix-without-separator containment check (`../prompts-evil/x`), a leaf-only symlink check (symlinked sub-directory), a read-then-discard fix, an unguarded runtime tool-dispatch route (`dispatch_tool`/`PromptyToolHandler`), and a possible async-only gap. Required change: add security tests for the dispatch route, a prefix-sharing sibling dir, and a symlinked sub-directory.
3. **Hints:** the instruction's feature tour and the "every way … — injected file contents, an included text fragment, an inherited base document, and a referenced child prompt —" sentence enumerate the sinks and effectively give the flaw count (4). Required change: neutral wording ("every way a document can name another file").
4. **blind.patch invalid:** it was diffed against the un-injected tree (no `${prompt:}`/`base` hunks; patches the C#/Rust/TS runtimes). Must be regenerated on the built image.
5. **Realism flag (medium):** T3/T4 exist only in the Python runtime; a solver comparing the TS/Rust/C# runtimes could spot them as foreign. Not unfair, but worth a one-line changelog mention or an accepted risk.

**Validation that did pass** (build gate, before the fairness verdict): vulnerable tree fails every security test and passes all functional tests; oracle closes all four routes and scores clean; all six check patches behave as declared; the pristine upstream suites (`test_loader.py` 38, `test_tool_dispatch.py` 39) pass on both trees.

## 3. Why MiMo fails and DeepSeek solves (provisional)

- **MiMo:** identical 0.8333 on all three attempts — it closes 5 of the 6 routes and breaks nothing, but leaves exactly one route open every time. The per-test results that would name *which* route (very likely T2, the child-prompt wire-projection route, given the fairness flag) have not been extracted yet, so this is inference, not confirmed. MiMo's pattern here matches its profile on jackson: it applies a generic containment check that covers the obvious sinks but does not reach a route that lives in a different file/feature.
- **DeepSeek:** reached 0.8333 on run 1 (same one-route-open shape) and 1.0 on run 2 — it found the remaining route on a second pass. This confirms the task (and the T2 test) *is* solvable, so MiMo's miss is a real capability gap on that route, not purely a broken test. But because the T2 test can mis-score a load-time rejection, the MiMo-only verdict is not yet trustworthy.

## 4. What is needed before this can be trusted or reported

1. Apply the fairfix (the §2 required changes), especially the T2 test move and the invariant widening.
2. Regenerate `blind.patch` on the built image and re-gate.
3. Re-trial both models (independent, 3 runs each with early-exit on solve).
4. Run the per-attempt audit (per-test results + transcript) to confirm which route MiMo misses.
5. Only then classify: a confirmed MiMo-only lead, a both-models breaker, or a solved task. **It is none of these yet.**

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each (DeepSeek early-exited after its run-2 solve), 2-hour limit per attempt.
- Offline: model APIs only, web tools disabled, no git history; hidden tests copied in only after the agent stops.
- Track: INJECTED (two of the four routes, T3 and T4, are injected siblings of the same class; T1 and T2 are real unmodified upstream code).
