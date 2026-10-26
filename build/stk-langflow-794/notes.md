# stk-langflow-794 — build notes

Started 2026-10-23T03:01:27Z (pipeline start). The prior build's `tasks/` trees and manifests were
absent on this host, so this session reconstructed them from the recovered artifacts under
`~/.tb-graders/cwe/work/stk-langflow-794/` (the repo at the pin, the hidden tests and harness, the
check patches, the prior environment build log) and re-verified every file behaviourally here.
Finished: see the last line.

## Pinned code and the published fix

- Pin: `cae2bdfef625fcc5998c9a88ffa8f0cc562ab32b` (2026-04-21). Fetched the published fix
  `f0fd436fe9829192ee550e6cb46961a01dd37032` and confirmed (`git log -1`) that the pin is its direct
  parent; its stat touches `mcp_utils.py`, `mcp_projects.py`, both local storage copies and the two
  project test files. The main-branch copy `b8fe970493fd5fb2e1fc71dfccc79f90b76058fa` carries the
  same source changes. The pinned tree does not contain the fix's added regression tests.
- The published source fix applied verbatim with our two-account harness makes **every** resource
  read raise: it compares the URI namespace (a string) against `Flow.id`, a SQLAlchemy `Uuid` column
  whose bind processor calls `.hex`. Upstream's own regression tests use a fake session and missed
  it. That is why `upstream_fix.patch` is declared `functional_fail`, not `security_fail`.

## Levers, one line each

- **T1 (C1, anchor)** — MCP resource read takes the namespace from the caller's URI and never
  checks ownership; `mcp_utils.py:177-183` (dispatch from `mcp.py:39-42`). Dismissal: the HTTP
  download route next door does the ownership check, so the MCP path looks handled.
- **T2 (C1)** — the project-scoped read dispatch drops `self.project_id`, unlike the sibling listing
  and tool handlers; `mcp_projects.py:1249-1252`. Dismissal: the project is verified at connection
  time, so a cross-project read of one's own flow looks harmless.
- **T3 (C2)** — the global resources listing selects every flow when no project is given;
  `mcp_utils.py:97-105` (dispatch from `mcp.py:33-36`). Dismissal: it returns only URIs/metadata.
- **T4 (C3)** — the global tools listing selects every flow and embeds the flow id in the tool
  description and name; `mcp_utils.py:345-347,379-381` (dispatch from `mcp.py:45-48`). Dismissal:
  tool execution is already caller-scoped, so the listing looks cosmetic.
- **T5 (C4, how-type)** — the URI is split on `/` before the name is decoded, so an encoded separator
  becomes a real one in the name handed to the storage join, which is itself uncontained on
  get/stream/delete/size; `mcp_utils.py:167-178`, `services/storage/local.py:193,207,256,276`.
  Dismissal: the HTTP layer validates separators before storage, so the storage layer looks like
  plain filesystem access and an ownership check looks sufficient.
- **T6 (C5)** — the standalone lfx package ships a second local storage service whose save/get/
  delete/size join the namespace and name with no containment; `lfx/services/storage/local.py:116-118,143,191,211`.
  Dismissal: the running server uses the other copy, so this one looks out of scope.
- **T7 (coupled contract, MiMo-type)** — reads and listings must keep serving the caller's own
  user-level bucket and names with spaces/non-ASCII characters; the listing advertises those
  percent-encoded URIs. Dismissal target: a rule that requires an owned flow, or a check that
  skips decoding, breaks legitimate use.

## What I verified

- Pinned copy, local repo venv: 9/9 security tests fail, 5/5 hidden functional pass, 28/28 project
  tests pass.
- Reference fix (`solution/fix.patch`): 14/14 hidden (9 security + 5 functional) and 28/28 project
  tests pass.
- Per-check local runs (same hidden suites as the verifier): `miss_read_authz` 5 security failing
  with all functional passing; `miss_resources_scope`, `miss_tools_scope`, `miss_containment` and
  `miss_lfx_storage` each 1 security failing with all functional passing; `drop_user_bucket` 1
  security + 1 functional failing; `refuse_quoted`, `refuse_all`, `wrong_resource`, `alt_fix` and
  `hardening` re-run through Harbor and behaved as declared in the prior build's evidence; the
  current gate's patches stage re-runs every one.
- Control task: pinned copy 4/4 control security tests fail, 5/5 hidden functional pass; its
  reference 9/9 control-suite tests pass; `missing_ownership` and `wrong_resource` leave the four
  security tests failing with all functional passing; `refuse_all` fails the functional suite.
- Two accounts, a shared server, one project: reproduced every lever end to end through the real
  MCP Streamable HTTP surface with the official `mcp` client (httpx ASGITransport, no sockets, no
  network). T7's coupled values (own flow, own bucket, quoted space/non-ASCII names, in-project
  file) all work at the pin.

## What I could not verify

- T6 (the lfx local storage copy) is not reached through the running server: the lfx package has
  no storage service factory. It is exercised through the package's public exported storage class,
  which is the entry point the published fix also protects; the report's containment property
  covers it literally. A reviewer may regard a library-level class as a weaker entry point than the
  HTTP server.
- T8 (S3 keys) is not a filesystem traversal (object keys do not resolve `..`) and the local
  backend is the one the app configures; not built (register row).
- T9 (image/message file paths) only reads through the product when converting a message for an
  LLM; the path is not traced to a client-supplied route at the pin; not built (register row).
- Per-model tiers are the record's, not measured. The reader's chosen design scores 0.407 on
  `score_stack.py` (v1 weights) with the `single-trap-carries` flag; score without the hardest
  concept 0.102. The built stack groups T2 with T1 and also builds T3, giving the same five
  independent concepts. Reported, not hidden.
- The project server's user-bucket policy is undecidable from the pin (the report's fairness
  risk); the tests accept either deny or allow-own for that shape and do not exercise it.
- The recall check (`upstream_fix.patch`, both published commits applied verbatim) is
  `functional_fail` because the published read path raises on every call in a real database
  session. It closes the same places our tests cover, so as a *design* recall it does not prove the
  stack adds coverage beyond upstream; the failure is the upstream bug, not a missing lever. No
  fabricated regression was added to force `security_fail`, which is what
  `stacking/check_stack.py` asks for. `builder/gate.py` is authoritative for the outcome.

## Outside the advisory's protection (noted, not built)

- The `File` component resolves a `flow_id/filename` parameter and reads the file directly, a
  cross-namespace read through the run API. It is real, unmodified upstream code and the published
  fix does not touch it, but it is outside the MCP advisory's own protection (P1-P4); noted only.

## Gate

Re-run from the reconstructed tree, stages in order, 2026-10-23T03:2xZ:

- static: PASSED (no leaks, conformance, catalogue or missing-check problems; the intentionally
  missing `blind` pass patch is declared and skipped).
- nop: PASSED — vulnerable code: 0/9 security passing (every security test fails), 33/33
  functional passing.
- oracle: PASSED — 3 runs, reward 1.0, 42/42 tests (9 security + 33 functional) in every run,
  identical. The first attempt aborted as **infra** at oracle2: Harbor's 30-second nftables
  kernel-support probe timed out under the shared VM's load (`network_mode='no-network' is not
  supported by EnvironmentType.DOCKER`); the same probe measured 4.3 s minutes later, and the
  retry passed. No task file was changed for it.
- patches: PASSED — all 12 declared checks behaved as declared:
  `miss_read_authz` 5 security failing / 0 functional; `miss_resources_scope`,
  `miss_tools_scope`, `miss_containment` and `miss_lfx_storage` 1 security / 0 functional each;
  `upstream_fix` 6 security / 2 functional failing (`functional_fail`);
  `alt_fix` and `hardening` reward 1.0; `drop_user_bucket` 1 security / 2 functional;
  `refuse_quoted` 5 security / 1 functional; `refuse_all` 6 security / 2 functional;
  `wrong_resource` 5 security / 0 functional. The `blind` pass patch is declared but intentionally
  not present (written after handoff).

The control task's static stage PASSED; its nop stage PASSED (vulnerable code: 0/4 control
security passing — all four fail — and 33/33 functional passing). Its oracle and patches stages
were not run in this session; its reference and check patches were verified locally instead
(reference 9/9; `missing_ownership` and `wrong_resource` leave 4 security failing with functional
all passing; `refuse_all` fails functional).

Finished (UTC): 2026-10-23T05:55:34Z (all four main stages green at 05:48:21Z).
