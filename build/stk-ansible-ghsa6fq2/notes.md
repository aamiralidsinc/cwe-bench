# stk-ansible-ghsa6fq2 — build notes

Start UTC: 2026-10-26T02:11:54Z
End UTC: 2026-10-26T04:50Z

## What the advisories actually are (the reader record was wrong)

GHSA-cqmr-rcpr-cxh3 / CVE-2019-10206 ("Ansible password prompts could expose passwords") is
**tempering of prompted passwords**: `CLI.ask_passwords()` returns the connection/become password as
a plain (later byte) value, and `PlayContext.post_validate` templates every string attribute, so a
password containing `{{ ... }}` is expanded. GHSA-6fq2-x65v-v9h7 / CVE-2019-14856 is the **incomplete
fix**: wrapping the value as `AnsibleUnsafeBytes` loses the unsafe marker when `get_validated_value`
calls `to_text()` (bytes → plain str), so the same prompt form still expands. The supplied reader
record's traps T1/T2/T3/T6/T7 describe terminal echo, tty detection, persistent logging and become
prompt keys — none of those mechanisms appears in the published fix commits or in the affected
code, so they were not used. The two real fix commits are mapped in the manifest `stacking.history`.

Pin `b2c43bd2b7` is the direct parent of A's 2.8 fix `d39488ece449` (verified from the GitHub commit
parents). B on 2.8 is `2cbd8775ca12`; the other listed commits are the same changes on 2.7/2.6 and
devel.

## Levers (3 concepts)

- **T1 — prompted password (advisory route, deepseek).** `lib/ansible/cli/__init__.py:251-279`
  (`ask_passwords`), through `lib/ansible/playbook/base.py:342` (`get_validated_value`) into
  `lib/ansible/template/__init__.py:229-246` (`_is_unsafe`). Reason to dismiss: getpass already
  hides the input, so the value looks like inert data; the existing `to_bytes` conversion reads as
  ordinary normalisation.
- **T2 — environment source (injected, deepseek).** `lib/ansible/playbook/play_context.py:169-173`:
  `ANSIBLE_CONNECTION_PASSWORD` is stripped and handed on as plain text. Reason to dismiss:
  environment values are read as operator configuration, not as a prompt; the advisory names
  prompts.
- **T3 — password-file source (injected, mimo/how-type).**
  `lib/ansible/playbook/play_context.py:163-167` plus the CLI option in
  `lib/ansible/cli/arguments/optparse_helpers.py:238-240`: the file is read as bytes and the
  trailing CRLF is stripped; wrapping the bytes (the pattern the code itself uses after A), or
  wrapping before the trim, still loses the marker at the byte→text conversion (`to_text` calls
  `bytes.decode`). Reason to dismiss: a file holds a literal secret, and bytes look like the
  natural value to wrap. Coupled must-keep-working: the newline is still trimmed, and a prompted
  password still takes precedence over the file.
- T2 and T3 are the automation-facing sources this project shipped later
  (`--connection-password-file`, `ANSIBLE_CONNECTION_PASSWORD_FILE`); the baseline carries a
  branch-plausible version of them. They are reachable through the ordinary CLI and are covered
  only by the report's general property.

All three sources converge on the same templating sink. The reference fix edits three independent
source sites (prompt wrap, file decode+strip+wrap, env strip+wrap) plus the unsafe check; the
per-concept `miss_*` patches fix the other two and leave that concept failing, so each concept has
its own demonstrated failure mode. A solver who repairs the sink instead of the sources also passes
(tests are behavioural).

## Verified

- Gate `nop` PASSED: 5 security tests fail on the untouched injected baseline, 9 functional tests pass.
- Gate `oracle` PASSED: three runs at reward 1.0 with identical results.
- Gate `patches` PASSED: all 12 checks reproduce their declared outcomes (3 concept miss-checks, 2 recall checks, 4 wrong-fix classes, functional_fail, alternative pass, hardening pass).

- Pinned code expands a prompted `{{ 1 + 2 }}` to `3`; A alone still expands it; A+B keeps it
  literal. Same for the file (CRLF, non-ASCII) and environment sources on the injected baseline.
- Oracle, alternative bytes-based design (encode/decode preservation) and the hardening patch all
  score 1.0 on the hidden suites; the untouched baseline fails exactly the 5 security tests and
  passes all 9 functional tests.
- `miss_prompt/miss_file/miss_env` each leave only their own security tests failing; the recall
  patches (`upstream_fix` = A+B, `upstream_first_fix` = A alone) both leave security tests failing;
  `check_after_adjustment`, `refuse_all`, `crash_as_refusal`, `wrong_resource` and
  `functional_overbroad` behave as declared.
- Project unit tests for the affected area (149/150 cases) pass at the pin, the oracle, the
  alternative fix, the hardening patch and every check patch.

## Could not verify

- The original GitHub PR text for #59246/#63352 beyond the commit messages and diffs; the reader
  record has no advisory text either.
- The listing check (`pipelines/stacking/4-listing`) was not run: it calls a target model, which
  this build must not do. The report states one property over passwords supplied to the CLI and one
  keep-working sentence; it names no source.
- The `blind` patch is declared but not produced (the postbuild blind-fix agent writes it).
- The control task's container stages did not run to a verdict: Harbor environment start timed out
  after 1800 s for nop/oracle/patches under host load average 88-112 (infra, not a task result).
  The control's static stage passed; local runs give nop 4 security fail / 9 functional pass,
  oracle (A+B) 13/13 at 1.0, A-alone security_fail and functional-overbroad functional_fail.

## Uncovered-route register

No row was added to `build/audit/uncovered-routes.tsv`: the published fix commits close every real
prompted-password route at this pin, so there is no real `uncovered_upstream` route. The two hidden
sources (T2, T3) are `injection_room` siblings, not unmodified upstream code; the reader's candidate
routes (terminal echo, tty detection, persistent logging, become prompt keys) are unrelated to the
published fix and to the affected code.

## Scope note

The vault-password and galaxy-login prompts were checked and do not expand their value as a
template. They are outside this advisory's protection and were not used.

## Score at build

`pipelines/stacking/out/stack_scores_ds.tsv` row `h3-ghsa-6fq2-x65v-v9h7`: score 0.547,
p_fail3_deepseek 0.900, p_fail3_mimo 0.607. The prediction was made for the reader's (incorrect)
five-trap design, so it is recorded per the pipeline rule but does not describe this stack.
