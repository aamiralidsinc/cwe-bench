# stk-mcp-for-stata-839 - build notes

Started: 2026-10-26T12:19Z
Ended: TBD

Repo `sepinetam/mcp-for-stata`, pinned `3553a42677855f99514392eaf3a90d56d27a2037` (exactly the parent of
the only published fix commit `e6f945941ae0c7cf5e74a428e0b3dc82b396382f`). The published fix changes only
`src/stata_mcp/stata/stata_do/do.py` (log-name regex + `generate_log_file`); it is used verbatim as
`checks/upstream_fix.patch`.

## Levers (one line each)

- T1 (A, both, advisory route): custom log name is joined into a path and interpolated inside
  `log using "..."`; a line break ends the command. `do.py:81-82,126-130,175-186,291-297`,
  `api/stata_do.py:113-118`, `mcp_servers.py:268-271`. Reason to dismiss: none - this is the reported route.
- T2 (B, both, uncovered upstream): the do-file path passes a resolve()d/existence/root boundary check and
  then the same text is interpolated into `do "..."`; a line break in a name inside an allowed root runs a
  command. `do.py:182,298`, `mcp_servers.py:183-208,270`, `api/stata_do.py:51-66`. Reason to dismiss: the
  boundary check makes the path look trusted.
- T4 (B, deepseek, uncovered upstream): the help topic is interpolated into `help {cmd}` and sent to a live
  pexpect session. `stata_help.py:106,119`, `controller.py:99`, `mcp_servers.py:119-135`,
  `api/stata_help.py:16-30`. Reason to dismiss: a read-only documentation lookup in another package.
- T5 (B, both, uncovered upstream): a package name or net source address is interpolated into the installer
  command and sent to a live session. `ssc_install.py:15`, `github_install.py:16`, `net_install.py:16-18`,
  `base.py:43-45`, `mcp_servers.py:348-349`, `api/ado_install.py:36-39`. Reason to dismiss: installation is a
  separate tool and package names read as identifiers.

Concepts (independent edit sites): [[T1], [T2], [T4], [T5]]. Each has a `miss_<concept>.patch` that closes
the other three (proved: its security tests still fail and every functional test passes).

## Harness

The Stata executable is replaced by a stand-in (`tests/fake_stata.py`) that records the bytes the product
sends and answers like a session that succeeded; it is the only stub. Every test drives a real public
surface: the documented Python API (`stata_mcp.api.*`) and the tool functions the MCP server registers
(`stata_mcp.mcp_servers.*`). The assertion is behavioural: no line the product sent to Stata is the caller's
`display` command. Refusal or sanitisation both pass; no exact status is asserted. The stand-in also lets
the functional suite check that documented values reach Stata unchanged: the `%Y%m%d%H%M%S` default
(`src/stata_mcp/utils/__init__.py:11-12`), `log_file_name="my_results"` and
`log_file_name=f"analysis_{dataset}"` (`docs/api/overview.md:128,428`), `SepineTam/TexIV` and the net
example URL (`docs/api/overview.md:229,235`), a do-file path with spaces (`CHANGELOG.md:572`), and a
non-ASCII do-file name.

## Verified (local, same runner as the verifier; one module per process)

- pinned: 10/10 security tests fail, 32/32 functional tests pass.
- reference fix (`solution/fix.patch`): 10/10 security and 32/32 functional pass.
- `upstream_fix.patch` alone: T2/T4/T5 security tests fail, all functional pass (recall check).
- `miss_T1/T2/T4/T5.patch`: only that concept's security tests fail, all functional pass.
- `wrong_resource.patch`, `one_direction.patch`, `check_after_adjustment.patch`, `malformed_identity.patch`,
  `refuse_all.patch`, `adjacent_api.patch`, `hardening.patch`, `alternative.patch`: see
  `verified.local_runs` in the manifest and the gate's patches stage.
- project's own tests for the affected area pass at the pinned commit (50 passed): guard validator, do-file
  boundary, server registration, server parser, CLI install, installer backup. The boundary and guard files
  are copied into the hidden functional suite.
- three repeated runs of both suites on the reference fix: no flake.
- `python3 -I common/gate/gate.py stk-mcp-for-stata-839 --only static` PASSED;
  `check_stack.py stk-mcp-for-stata-839` conforming (4 concepts, H4).

## Control

`tasks/stk-mcp-for-stata-839-control` has the byte-identical `instruction.md`, the same environment and
functional suite, and only the advisory's own route in its four security tests; its reference is the
published fix. Verified locally: pinned 4/4 security fail + 32/32 functional pass; published fix 4/4 +
32/32 pass; the same hardening and alternative patches pass.

## Not verified / unknown

- No real Stata binary is available; the stand-in models a command-per-line session. The injection shape
  (a line break splitting the command) is how the Stata CLI reads piped and interactive commands; a real
  Stata was not run.
- The Windows transport in `do.py` (shell=True, batch file) is covered by the shared `execute_dofile`
  validation in the reference but is not exercised by the tests (the verifier is Linux).
- The record's T3, T6 and T7 were kept as sub-routes of the chosen groups, not separate concepts: T3 is the
  Windows twin of T2, T6 the Windows installer twin of T5, T7 the shared builders of T1.
- Out-of-family sites deliberately not built on: `api/read_log.py` has no directory boundary although
  `mcp_servers.read_log` does, and `get_data_info` resolves arbitrary paths; both are file-read issues, not
  command construction.
- `stacking.reader_record` points at the record actually available in this worktree,
  `pipelines/stacking/out/reader-ds/h4-839.json`; the build request named `pipelines/stacking/out/reader/h4-839.json`,
  which does not exist.
- The hidden-route register rows were appended to `build/audit/uncovered-routes.tsv` (see the report).
