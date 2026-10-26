# stk-mcp-118 build notes

Started: 2026-10-26T12:17:55Z
Ended: (filled when the gate finishes)

## What was built

Stacked H4 task on `awslabs/mcp` at `70d8c4cb82601a0e48328e34bf7a81b5a6fba073` (direct parent of the
published fix `ab1bbebc097d674c1cdd4bd75a8f313be18473bf`, verified with `git log` on a shallow fetch
of both commits). The product is the `aws-api-mcp-server` package of the monorepo; the task is
graded through the MCP tool `call_aws` and the console entry point `main()`.

## Levers (one line each)

- **T1** (advisory route, request path; type both). `server.py:321-341`: when the read-only
  operations index is `None`, the request gate falls through to read-only/consent checks and then
  executes the command, so the operator's deny and consent lists are skipped. Reason to dismiss: the
  else branch reads as a deliberate degraded policy, and the repository's own tests patch the index
  to `None` and expect execution.
- **T2** (advisory route, startup; type mimo). `server.py:440-445`: `main()` catches any failure from
  `get_read_only_operations()`, logs a warning, and serves with no enforcement data. Reason to
  dismiss: the repository's test says the process must not raise, and aborting looks hostile to
  offline starts.
- **T3** (uncovered upstream, Pattern B; type deepseek). `policy.py:56-87`: a policy file that exists
  but cannot be read or parsed is swallowed and leaves the deny and consent lists empty, so an
  operation the operator denied runs. Reason to dismiss: the file is optional user configuration,
  absence is explicitly tolerated, and the repository's own test calls the unreadable/malformed case
  "handled gracefully". The published fix never touches this file. Route still present in current
  upstream `main` (checked read-only on 2026-10-26).

## Reference fix

`solution/fix.patch`: refuse every command when the index is `None`; re-raise at startup; make the
policy loader raise on a file that exists but cannot be read, parsed or understood, while keeping
the absent-file default. Alternative design in `checks/alt_correct_fix.patch`: deny in the policy
decision function, exit non-zero at startup, and mark a failed policy load as a deployment-wide
denial.

## Verified

- Pinned tree: all 10 security tests fail, all 12 functional tests pass (local matrix).
- Oracle: 22/22 pass; alternative fix 22/22; hardening 22/22.
- Re-verified under CPython 3.12.15 with the exact pinned dependency set from
  `environment/requirements.txt`: the whole variant matrix reproduces (pinned 0/10 security and
  12/12 functional; oracle and alternative 22/22; every miss/wrong-fix patch matches its declared
  outcome), matching the images' interpreter.
- Per-concept miss patches: `miss_concept_request_time` fails only T1's 5 tests;
  `miss_concept_startup` fails only T2's 2; `miss_concept_policy_load` fails only T3's 3; all keep
  functional green.
- Recall: `upstream_fix.patch` (the published source changes) still fails T3's 3 tests.
- Wrong fixes: `refuse_all` breaks 9 functional tests; `adjacent_api` breaks 7 (it treats the absent
  policy file as a failure); `crash_as_refusal` fails security with a `SystemExit`; `reads_only`
  leaves the read-only security test failing.
- Patch application: every patch in `checks/` and the oracle apply cleanly to the pinned tree with
  `patch -p1 --dry-run`.
- The project's own affected tests pass at the pinned commit (107 passed) and are run in the agent
  image build.
- `check_stack.py stk-mcp-118`: conforming (3 concepts, pattern H4).

## Could not verify

- No model trials were run (the build instructions forbid running target models). The bar is
  reported, not proven.
- The published fix's regression tests were not carried over: the project's pinned tests encode the
  vulnerable fallback (`main()` must not raise; index `None` executes), so the hidden functional
  suite is written independently rather than copying them.
- Whether the agent's own edits to `pyproject.toml` or dependency needs would break the verifier is
  not controlled; the verifier imports the restored source with the pinned dependency set.

## Notes

- The control task `stk-mcp-118-control` has the same report, the same pinned code and only the
  advisory's own route (T1/T2) in its security tests and reference (`upstream_fix.patch`).
- Pattern B register row added in `build/audit/uncovered-routes.tsv` for T3.
