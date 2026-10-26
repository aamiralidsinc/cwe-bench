# olivetin-allowlist-inj — build notes

- Start UTC: 2026-10-18T12:16:08Z
- End UTC:   2026-10-18T12:45:00Z (approx; local verification complete, gate pending)

## Levers (one line each)
- L1 username_into_command (A, report): executor.go:750-753 — identity login name templated into the main shell command unchecked. Dismiss: none (the lead).
- L2 client_reserved_arg_into_env (A, report): executor.go:736-739 / 667-676 — undeclared client arg with the reserved prefix survives the filter and reaches the command environment. Dismiss: partial fix validates the name but keeps the prefix pass-through / inject-before-filter order.
- IS1 group_into_shell (injected): arguments.go parseActionArguments — caller's group line templated into the main shell command unchecked. Dismiss: neighbouring identity field, not the flagged login name; survives a verbatim published-fix reproduction.
- IS2 group_into_exec_env (injected): executor.go handleExecBranch — same group line written into the direct-exec environment. Dismiss: direct-exec is argv-based, assumed injection-proof; different branch the fix never touches.

## Verified
- Pinned 41612c6b is the exact parent of fix ebffd9f0 (git).
- All 4 levers reproduce through the real ExecRequest path on pinned+injected (marker files created); oracle closes all 4; 6 functional (incl. coupled email/plus username, env delivery of name + tracking id, post-completion name) pass on both pinned+injected and oracle.
- Project tests pass at pinned+injected and oracle (go test ./internal/executor/ ./internal/config/).
- inject.patch and fix.patch and all 7 check patches apply with `patch -p1` from a fresh pinned checkout.
- 4 security_fail check patches each isolate exactly one lever (functional all green); func_overbroad breaks the email-username functional tests; hardening and alt_fix pass fully.

## Could not verify / notes
- The published post-completion-command far site is redundant for the login name (main-path validation fails the request before it runs), so it is not a separate lever; kept in the oracle for fidelity. The post-completion stdout-templating and entity-templating paths are different issues/boundaries, left out of scope (not built), noted in manifest.
- Target-model trials (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) not run by me; the blind patch and FAIRNESS.md are produced downstream.

## Fairness
- Every lever is findable by a blind engineer from instruction.md + code: L1/L2 from the report lead and the argument filter; IS1/IS2 from the injected identity-field exposures visible in the two execution branches. The invariant in instruction.md ("no value describing who the caller is ... may change the command or its environment; ... for every branch, shelled or direct, and for the environment as much as the command") covers all four without naming fields.
