# stk-lemur-5644 — build notes

Start: 2026-10-23T04:59:14Z (build job start)
End: 2026-10-23T07:36Z

This run re-materialised the task from the same design and the same verified artifacts as the
2026-10-22 build; every gate stage below is from this run.

## Advisory / commits
GHSA-v5rc-cpwc-cfpr (netflix/lemur, CWE-918), fixed by `edca0390f930344d65ff4ca37a669c2320e3dfad`.
Verified in the local clone: the fix commit's parent is exactly
`e9ade7dad5c9bc1369a831554ed6df3277c9cbae` (the pinned commit), and the fix touches
`lemur/authorities/service.py`, `lemur/plugins/lemur_acme/plugin.py` and the project regression test
in `lemur/tests/test_authorities.py`. The pinned tree therefore contains no hidden regression test.
The published fix re-validates the submitted `acme_url` entries on the authority update path and
makes the creation-time validator public. The pinned tree has no validation on the update path and
none on `service.update_options`.

A later, divergent upstream change on `main` also validates inside `update_options`; it is not an
ancestor of the pinned commit or the fix and was only read for the Pattern B register row.

## Mechanism (one line)
An ACME authority's directory address is fetched by the ACME client; at the pinned commit it is
checked (HTTPS + host allowlist) only when an authority is created, so any route that supplies a
directory address reaches the stored value or the fetch unchecked.

## Levers (one line each)
- **T1 (concept C1, reported route)** — `PUT /api/1/authorities/<id>` stores `options` verbatim
  (`lemur/authorities/service.py:42-43`, `views.py:417-424`). Dismiss: none; the report points here.
- **T2 (shape inside C1)** — one payload can carry several `acme_url` entries; the fetch builds its
  map in list order so the last entry wins (`acme_handlers.py:157-158`). Dismiss: one directory per
  authority is normal, so validating the first match looks complete.
- **T3 (coupled shape inside C1)** — options are a free-form JSON string; the legitimate payload
  `[{"updated": "bar"}]` has no `name` key (`test_authorities.py:438`). Dismiss: a check written as
  `option["name"]`, or one gated on a well-formed list of named dicts, rejects or raises on it.
- **T4 (concept C2)** — `update_options` is a second writer with no check (`service.py:49-62`); its
  only in-tree caller re-persists already-trusted rows, so it reads as internal. Dismiss: "it only
  stores options" / "the update fix covers authority options".
- **T5 (coupled value across C2/C3)** — the config fallback, legacy stored addresses and the
  `store_account` write-back must still work. Dismiss: validating the effective address at the
  fetch point is the tempting over-fix; it breaks values the product documents as trusted.
- **T6 (concept C2 reachability, injected)** — `PUT /api/1/authorities/<id>/options` calls the real
  `update_options`. Dismiss: same as T4; the route is easy to miss when the report names the
  authority update.
- **T7 (concept C3, injected)** — a request-scoped directory override is merged just before the
  fetch (`acme_handlers.py:157-163`), reached by `POST /api/1/authorities/<id>/acme-directory`.
  Dismiss: values at the fetch site are documented as trusted stored configuration, so a supplied
  override looks covered by the same trust.

## Concepts (reference fix edit sites)
1. `service.update` — validate every `acme_url` entry in a user-supplied options payload
   (T1/T2/T3).
2. `service.update_options` — validate only values that differ from the stored ones, so the
   internal account write-back of a legacy authority keeps working (T4/T6, conflict with T5).
3. `acme_handlers.setup_acme_client_no_retry` — validate a request-scoped override before it is
   merged, never the stored/configured effective address (T7, conflict with T5).

## Injected code (environment/injection.patch)
- `AuthorityOptionsUpdateSchema` + `AuthorityOptions` at `PUT /authorities/<id>/options`, calling the
  real `service.update_options`.
- `AuthorityAcmeDirectorySchema` + `AuthorityAcmeDirectory` at
  `POST /authorities/<id>/acme-directory`, calling the real `AcmeHandler.setup_acme_client` with an
  optional `acmeUrl` override.
- `setup_acme_client(_no_retry)` accepts `overrides` and merges `acme_url`/`email`/`telephone`
  before assembling the directory URL. `under()` in the product's schema base maps the JSON
  camelCase key to the option name.

## What this run verified
- Pinned+injected tree: **11/11 hidden security tests fail** through the real HTTP entry points;
  **9/9 hidden functional** and **106/106 project** tests pass (gate nop, job
  `stk-lemur-5644-nop-1792731975`, PASSED). The security failures are the real ones: 200 + options
  stored, and the loopback canary records the connection to the supplied address.
- Oracle: **PASSED**, 3 runs at reward 1.0 with identical results (gate oracle, jobs
  `...-oracle1/2/3-1792732232/480/853`).
- Patches: **PASSED** on a retry after one shared-VM Harbor `no-network` probe flake
  (`ValueError: network_mode='no-network' is not supported by EnvironmentType.DOCKER`, a
  pre-execution infrastructure error; the first attempt reached ff-refuse-all and aborted). All 11
  checks behaved as declared:
  - `miss_c1` (reported route open): 6 security fail, 0 functional fail (reward 0.4545);
  - `miss_c2` (second writer open): 3 security fail, 0 functional fail (0.7273);
  - `miss_c3` (request-supplied address open): 2 security fail, 0 functional fail (0.8182);
  - `upstream_fix` (recall, published fix alone): 5 security fail, 0 functional fail (0.5455);
  - `sf-first-acme-entry-only` (only the first entry checked): 1 security fail (0.9091);
  - `sf-check-after-store` (check after persistence): 6 security fail (0.4545);
  - `ff-keyerror-shape` (check indexes the entry name): 2 functional fail;
  - `ff-refuse-all`: 10 functional fail;
  - `ff-validate-at-sink` (validates the effective stored/configured address): 7 functional fail;
  - `pass-alt-view-guards` and `pass-hardening`: reward 1.0 (11 security, 115 functional).
  The outcomes are in `build/stk-lemur-5644/patches_gate_report.json` (reconstructed from the retry
  job dirs, because a later static re-run overwrites `gate_report.partial.json`).
- `stacking/check_stack.py stk-lemur-5644`: conforming (3 concepts, pattern H4).
- `builder/conformance_check.py` on both task directories: conforming.
- `git` check: pinned commit is the direct parent of the published fix; the fix's own regression
  test is not in the pinned tree.
- All `checks/*.patch` files and both `solution/fix.patch` files apply with `patch -p1` to the
  pinned+injected tree; the reference patch reproduces the oracle tree exactly (source files).
- Register rows for T4/T6 and T7 are present in `build/audit/uncovered-routes.tsv`.
- Control task `stk-lemur-5644-control` (same pinned+injected code, same report, only the advisory
  route in the security suite and the reference): static conforming (only the blind patch missing),
  **nop PASSED** (6/6 security fail, 9 hidden + 106 project pass), **oracle PASSED** (3 runs, 1.0),
  **patches PASSED** (5/5: `sf-no-update` 6 security fail; `ff-keyerror-shape` 2 functional fail;
  `ff-refuse-all` 10 functional fail; `pass-alt-view-guards` and `pass-hardening` 1.0).

## What I could not verify
- The full multi-stage gate is run stage by stage, because `static` legitimately lacks the `blind`
  patch that the later blind-fix step writes. No target-model trials were run (the build rules
  forbid it here), so the acceptance bar is a design prediction, not an empirical result.
- Upstream's divergent later change to `update_options` was read, not run; nothing in the task
  depends on it.

## Fairness notes
- The instruction states the property over the protected data ("no user-supplied value may cause an
  ACME directory address to be stored, or fetched by the backend, unless it is an HTTPS URL whose
  host is on the configured allowlist ... however the address is supplied, and wherever it is
  supplied"), gives only the reported request as the example, and names no file, function or extra
  route.
- Legacy/config addresses are never re-checked; the functional suite enforces that, and the
  instruction states it as a keep-working value. This is the T4/T5 and T7/T5 conflict: a fix that
  validates the effective address at the fetch point scores 0.
- The no-name options shape is covered by a keep-working clause in product terms.
- The refusal contract is "an error response with the stored options unchanged and no connection
  to the supplied address"; the product turns raised validation errors into 500, and the security
  tests accept any error status.
- The control task (`stk-lemur-5644-control`) uses the same report and pinned+injected code with
  only the advisory's own route in the security tests and the reference.

## Fairness revision 2026-10-24 (AUDIT-FIX-20261024.md, Required item 1)

Instruction-only change. The Required property now reads: "A directory address must be checked when
it arrives in a user request, before it is stored or fetched by the backend: it must be an HTTPS URL
whose host is on the configured allowlist of permitted directory hosts. A request carrying any other
directory address must fail with a client error and have no effect, leaving stored state unchanged."
The previous "No directory address supplied in a user request may be stored, or fetched by the
backend, unless..." could be read to forbid the backend fetching an address stored before the change,
which contradicted `functional/test_legacy_directory.py::test_stored_directory_is_still_contacted`
and `::test_account_write_back_keeps_legacy_directory`. The rule is now scoped to the arrival event;
no test, reference, check patch, trap, leak term or manifest entry changed. The control task gets the
same wording through `stacking/run_fairfix_stack.sh` (build rule 13).

Re-gate on the final tree, stage by stage, one stage at a time:

- `static` PASSED (no leak term; no exact-status assert).
- `nop` PASSED: 11/11 security tests fail, 115/115 functional pass (9 hidden + 106 project),
  reward 0.0.
- `oracle` PASSED: 3 runs at reward 1.0 with identical results.
- `patches` PASSED: all 12 declared checks behaved as declared (11 catalogue/alternative checks
  plus `blind.patch` at 1.0): miss_c1 6 security fail (0.4545), miss_c2 3 (0.7273), miss_c3 2
  (0.8182), upstream_fix 5 (0.5455), sf-first-acme-entry-only 1 (0.9091), sf-check-after-store 6
  (0.4545), ff-keyerror-shape 2 functional fail, ff-refuse-all 10, ff-validate-at-sink 7;
  pass-alt-view-guards, pass-hardening and blind.patch all 1.0.
- Listing check after the rewording: PASS (named=0, described=0; hidden traps T4–T7 GENERAL).

The shared-VM Harbor `network_mode='allowlist'` egress-kernel probe flaked repeatedly under the
nightly load (50 concurrent harbor runs); the stages were re-run through the documented
probe-and-retry loop (`~/.tb-graders/cwe/work/stk-lemur-5644/gate_loop.sh`) and passed on a clean
probe. No task file was changed for it; `task.toml` was not touched.

