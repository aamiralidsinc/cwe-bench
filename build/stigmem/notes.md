# stigmem stacking build notes

## Commit C
`66f4fa6a83071a313c1f9bd624a27b4a5ac56a2a` — the parent of `07a5e04` (#484),
which is the first of the clustered 0.9.0a1 -> 0.9.0a2 security-fix commits.
At C every included flaw is still open; all are fixed by tag `v0.9.0a2`.

## Co-present vulns verified present at C (6)
Each reproduced through a real entry point on a C checkout and confirmed fixed
by the combined upstream source patch:

| id | entry point | CWE | reproduced at C |
|----|-------------|-----|-----------------|
| V1 authorization: peer self-registration auto-activates | HTTP POST /v1/federation/peers + GET /v1/federation/facts | 862/285/863 | register => `active`; peer token accepted (200) |
| V2 insecure federation on non-loopback | startup (create_app lifespan) | 319 | boots with mTLS off on public node_url |
| V3 auth-disabled on non-loopback | startup | 489/862 | boots unauthenticated (anon full access) on public node_url |
| V4 unsigned plugin w/o acknowledgement | plugin registration (register_discovered_plugins) | 494 | unsigned plugin loads |
| V5 quota kill-switch w/o acknowledgement | startup | 770 | boots with read=write=0 quotas |
| V6 world-readable local DB | startup (apply_migrations) | 732 | DB file mode 0644 |

## Funnel
- Exploits reproduced: 6/6 (9 security test cases incl. V1 x2 and V2/V3 x2 params).
- Security tests: 9 (all FAIL at C, all PASS after fix).
- Functional tests: 6 (all PASS at C and after fix; 3 break under disable_feature).
- Services: none (offline, SQLite, in-process FastAPI TestClient).

## Dropped (see manifest for detail)
- C1 peer-token iss/iat/nbf (defense-in-depth through the endpoint).
- legacy SHA-256 key retirement (fixed-path rejection surfaces as a 500 via the
  rate-limit middleware; messy to assert cleanly).
- H5 PostgreSQL SQL-identifier injection (needs a Postgres server; kept offline).
- GHSA-5p3m webhook SSRF (introduced/fixed ~0.9.0a11, not open at C).

## Could not / did not do
- Did not run the full upstream pytest suite in the image (hypothesis-based
  fuzz module + some areas need extra dev deps); ran the federation + auth
  suites at C (242 passed) to confirm offline health of the affected areas.

## 2026-10-16 test repair
Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Flagged items: `build/audit/lenient_items_2026-10-16.txt`
(stigmem deepseek-r11, deepseek-r3, mimo-r3), plus our own notes. `research/own-runs/TEST-REPAIRS.md`
has no stigmem section. `instruction.md` and `solution/` are unchanged.

| item | decision |
|------|----------|
| Refusal tests (V2, V3, V4, V5) counted any startup exception as a refusal, so a crash on the risky config passed (all three audits) | **fixed.** New `conftest.start_node()`. It treats as a refusal any deliberate error raised during settings validation, app construction or startup (RuntimeError, ValueError or pydantic validation error, a custom class, or an exit). It fails the test with "startup crashed instead of refusing" when every raised exception is a crash type (NameError, AttributeError, ImportError, TypeError, LookupError, ArithmeticError, NotImplementedError, RecursionError, SyntaxError, sqlite3.Error). It does not require one exact class. |
| Same tests, too strict side found while fixing: a refusal raised while constructing Settings or in `create_app()` errored the test (both were outside the try block), and `sys.exit()` in startup reaches TestClient as `CancelledError` (a BaseException), so it was not caught either | **fixed (relaxed).** Both now count as refusals. Settings construction and `create_app()` are inside `start_node`. |
| Refusal not shown to come from the guard: no functional boot on a non-loopback address, so a fix that refused every public deployment scored 1.0 (deepseek-r3 audit: "pair each with ... variant boots") | **fixed.** New functional test `test_secure_node_boots_on_public_address[2 params]`: an authenticated node with transport security at its default must boot and answer /healthz on `0.0.0.0` / `stigmem.example.com` and on `203.0.113.10`. Follows from the instruction: only the two insecure configurations are to be refused, and "normal authenticated API operation is unaffected". |
| Acknowledged-mode boot tests (acknowledged quota kill switch and acknowledged unsigned plugins must still start; audits deepseek-r11 and deepseek-r3, our notes) | **skipped.** The instruction requires that an acknowledgement exists, but it does not say how one is given. Every fix invented its own setting. The reference uses `STIGMEM_RATE_LIMIT_DISABLED_ACK=1` and a literal phrase for plugins. The model runs used `allow_unsigned_plugins`, `STIGMEM_ALLOW_UNSIGNED_PLUGINS` and `STIGMEM_ACK_DISABLE_RATE_LIMITS` / `STIGMEM_ACK_ALLOW_UNSIGNED_PLUGINS`. A test would need an interface the instruction does not state (§3g). Stating the reference's names is impossible because `rate_limit_disabled_ack`, `plugin_unsigned_ack` and the literal phrase are manifest leak terms. Stating any other name would fail the unchanged reference fix and every saved run. The V5 crash case and the public-boot pair close the main gap (a guard that cannot be acknowledged because it crashes, or a refuse-all guard). An unconditional V4/V5 refusal with no acknowledgement path stays ungraded. |

New patch checks (both are the reference fix with one change; by construction both would have scored 1.0 under the old tests):
- `crash_not_refuse.patch` (security_fail): the quota guard reads an undeclared `settings.rate_limit_kill_switch_ack`, so zeroed quotas crash with AttributeError. The gate gives 0.8889 and fails `test_v5_quota_killswitch`.
- `refuse_public_bind.patch` (functional_fail): the auth guard refuses every non-loopback deployment. The gate gives 0.0 and fails both `test_secure_node_boots_on_public_address` params.

Gate (`build/slot.py 3 -- python3 -I builder/gate.py stigmem`): **PASSED** (log in `gate-20261016-repair.log`).
The suite is now 9 security and 8 functional tests. The nop, the oracle (x2) and every existing check behave as declared: alt_correct_fix and host_keyed_fix score 1.0, subset_fix 0.8889, disable_feature 0.0.
Warnings unchanged (no hardening or blind patch; this task was built before 2026-10-16).

Regrade (`regrade_from_code.py`, "test repair 2026-10-16"). Every run with saved final code was at 1.0. Because one check was relaxed, any run below 1.0 would also have been regraded, but none of those runs has saved final code.

| trial | old | new | failing tests |
|-------|-----|-----|---------------|
| stigmem-deepseek-r11-20261015-215312-n001/stigmem__xzCE3nG | 1.0 (verifier) | 1.0 (regrade-20261016T052326Z) | none |
| stigmem-deepseek-r3-20261015-150242-n001/stigmem__wtJTGz2 | 1.0 (regrade-20261015T222502Z) | 1.0 (regrade-20261016T052350Z) | none |
| stigmem-mimo-r2-20261015-115318-n002/stigmem__G8pGiV5 | 1.0 (regrade-20261015T222524Z) | 1.0 (regrade-20261016T052417Z) | none |
| stigmem-mimo-r3-20261015-134118-n003/stigmem__JZ4firU | 1.0 (regrade-20261015T222530Z) | 1.0 (regrade-20261016T052441Z) | none |

Not regradeable (no `final-code/`): deepseek-r1 n001 (0.4444), deepseek-r1 n002 (1.0), mimo-r1 n001 x2 (0.0, 0.0), mimo-r1 n002 (0.4444).
