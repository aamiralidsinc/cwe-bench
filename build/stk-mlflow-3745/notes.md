# stk-mlflow-3745 build notes

- Start (UTC): 2026-10-23T03:00:14Z (rebuild after `stacking/stacking_restart.sh` wiped the task
  directories; the earlier builds of this slug ran 19:17-21:34Z and 22:12-00:46Z)
- End (UTC): 2026-10-23T05:52:14Z

## Levers (one line each)

- **C1 / record T1,T2,T3,T8 (A+B, write-time; concept 1).** A secret's stored configuration is
  accepted with no destination check on create or update; the store is the single writer both
  handlers pass through. `mlflow/server/handlers.py:5073-5135`,
  `mlflow/store/tracking/gateway/sqlalchemy_mixin.py:169-316`. Reason to dismiss: the create schema
  looks like the only gate, and the store looks internal.
- **C2 / record T4 (B, merged configuration; concept 2).** A value inside the encrypted secret map
  is merged over the stored configuration and spread into the third-party client, which dials it.
  `mlflow/server/gateway_api.py:404-410`, `mlflow/gateway/providers/litellm.py:93-112`. Reason to
  dismiss: the client is external, the egress key is not the stored key's name, and the encrypted
  map is treated as opaque.
- **C3 / record T5 (B, stored row and connect time; concept 3).** A row written before any check is
  reloaded and reaches the shared request primitive; the pinned code has no connect-time check.
  `mlflow/store/tracking/gateway/config_resolver.py:117,231`,
  `mlflow/gateway/providers/utils.py:29-32`. Reason to dismiss: write-time validation looks
  sufficient.
- **C4 / record T6 (A+B, coupled must-keep; concept 4).** The shipped Ollama default dials a local
  address and must keep working, while a supplied value that spells the same address is refused.
  `mlflow/gateway/providers/ollama.py:13`,
  `mlflow/gateway/providers/openai_compatible.py:204-205`. Reason to dismiss: one address rule looks
  safe until the built-in default beside it is considered.
- **C5 / record T7 (B, derived host; concept 5).** The destination host is composed from a region
  or location field, so a URL-shaped token changes the host without being a URL field.
  `mlflow/gateway/providers/vertex_ai.py:76-82,124-130`,
  `mlflow/gateway/providers/bedrock.py:494-502,607-609`. Reason to dismiss: a region/location is a
  name, not an address.

## What was verified (this rebuild, pinned worktree + a minimal Python 3.12 venv)

- Pinned main: 9/9 security tests fail, 5/5 functional tests pass.
- Oracle main (`solution/fix.patch`): 9/9 security and 5/5 functional pass (14 passed).
- Pinned control: 4/4 security tests fail, 5/5 functional pass.
- Control reference (`solution/fix.patch`): 4/4 security and 5/5 functional pass (9 passed).
- Every main check patch (14) and control check patch (6) applies cleanly to the pinned tree
  (`patch --dry-run`).
- Project's own tests for the affected code at the pinned commit: `tests/gateway/providers/`
  `test_litellm.py` and `tests/gateway/test_utils.py` — 110 passed. `tests/gateway/providers/`
  `test_bedrock.py`, `tests/gateway/test_gateway_config_parsing.py` and the rest of
  `tests/gateway` import `sentence-transformers`/torch at module level through `tests/gateway/tools.py`
  and were not run with the pinned dependency set.

## Gate results (each stage run individually, this rebuild)

- main static: FAIL only on `manifest.patch_checks has no expect=pass patch with kind='blind'`
  (the fairness team writes that later); no other static problem.
- main nop: PASS — 9/9 security tests fail, 5/5 functional pass; reward 0, passed_total 0.357.
- main oracle: PASS — 3/3 runs, reward 1.0, identical results.
- main patches: PASS — 14/14 checks behaved as declared:
  - `miss_write_time` 5 security fail / functional pass; `miss_merged_config` 1; `miss_connect_time`
    1; `miss_shipped_default` 1; `miss_derived_host` 2; `sf-crash` 8; `sf-update-only` 1;
    `sf-reads-only` 7; `sf-wrong-object` 5 — all with functional pass;
  - `ff-refuse-all` and `ff-block-shipped-default` each break the shipped-default functional test;
  - `pass-hardening` and `pass-alternative` score 1.0;
  - `upstream_fix` (published 96b7d900) leaves all 9 security tests failing with functional pass.
- control static: FAIL only on the missing blind patch.
- control nop: PASS — 4/4 security fail, 5/5 functional pass, reward 0.
- control oracle: PASS — 3/3 runs reward 1.0 (9/9 each); two earlier attempts were cut by the
  shared-VM egress-kernel probe flake (infrastructure only).
- control patches: the stage started at 05:48:22Z with a strict probe window. Checks 1-2/6
  (`sf-no-write-api-base`, `sf-crash`) completed as declared (4/4 security failing, 5/5 functional
  pass, reward 0.0 each); the remaining four were still running when the builder window closed. The six check
  files come from the same deterministic generator as the previous build (6/6 then), and the main
  task's 14 checks passed 14/14 in this build.

## What could not be verified

- The supplied published fix commit 96b7d900 is a raw-proxy feature and was not verified as the
  parent/child of the pinned commit; the recall check only shows it leaves every security test
  failing.
- Whether upstream later added a gateway address policy (current master has one) was not used; the
  task is built on the pinned checkout only.
- `aiohttp` redirect-following and the LiteLLM key names come from those libraries, not from repo
  code; the reference policy validates the final URL before the connection is opened.
- Whether the Databricks SDK contacts the configured workspace host before the shared request
  primitive was not traced.
- Tier values are priors; no target-model trials were run by this build.

## Fairness repair (2026-10-24, instruction-only)

Source: `build/stk-mlflow-3745/AUDIT-FIX-20261024.md` (post-upgrade audit; the v2 upgrade had
deleted the shipped-default carve-out and the refuse-at-supply contract). Only
`tasks/stk-mlflow-3745/instruction.md` changed (the launcher copies it to the control, rule 13);
tests, solution, traps, manifest and check patches are untouched.

- Required 1: the unconditional refusal sentence is scoped to "a destination reached because of a
  value a user supplied, or because of configuration already stored for a gateway". The shipped
  local default is reached because of neither, so no security rule read literally forbids it; it is
  kept working by the general preservation clause, without naming it (listing: T6 stays GENERAL).
- Required 2: the property now states the rule holds both when such a value is supplied — the
  configuration is refused and the request has no effect — and again when a call is about to
  connect, so the create/update refusals and the connect-time refusal are both contract.
- Listing check re-run: PASS (named=0 described=1 general=6 absent=0 hidden=7 exempt=1); the only
  DESCRIBED trap is T5, as before the upgrade (T1 exempt as the advisory route).
- Gate 2026-10-24, one stage at a time: static PASS; nop PASS (9/9 security fail, 5/5 functional
  pass, reward 0, passed_total 0.357); oracle PASS 3/3 (reward 1.0, 14/14); patches PASS 14/14
  (blind.patch still to be wired separately).

## Fairness repair (2026-10-25, instruction-only, post-trial audit)

Source: `build/stk-mlflow-3745/AUDIT-FIX-20261025.md` (post-run Opus audit of MiMo r3: the single
decisive functional failure `test_shipped_local_default_is_still_called` was attributed to
instruction ambiguity). Only `tasks/stk-mlflow-3745/instruction.md` changed (the launcher copies it
to the control, rule 13); tests, solution/fix.patch, manifest, traps and check patches are untouched
as the audit requires.

- Required 1: both security sentences are scoped to destination-forming values — "an address, host,
  or any other value the call's destination is built from" — supplied by a user or stored for a
  gateway. Choosing among the product's providers is not such a value, so the shipped local default
  keeps working under preservation without being named.
- Required 2: no built-in default, provider, port or address is named and no exception is added.
- Required 3: nothing else changed.
- Gate 2026-10-25, one stage at a time: static PASS; nop PASS; oracle PASS; patches PASS.
- Listing check re-run after the change: see below (PASS expected: no trap becomes named).
