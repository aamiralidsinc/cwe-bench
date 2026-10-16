# mcp-ts-sdk-oauth — build notes

Base task and DeepSeek finding by Hadi, 2026-10-15 (`mcp-ts-sdk-oauth-issuer-confusion`,
GHSA-6qxp-vccf-f47h, CWE-522; DeepSeek V4.1 Flash 0.6429 x3 with terminus-2; MiMo solved it).
This version ports it to the cwe-bench layout and adds two traps (BRIEF-trap-stack.md).

- Start: 2026-10-16T11:26:27Z. End: see the bottom of this file.
- Repo: modelcontextprotocol/typescript-sdk at ef39308e (parent of fix edd12e28). Nothing injected:
  both traps are real gaps at that commit, and the upstream fix leaves both open.

## Port
- Dockerfile: Hadi's, with `git fetch --depth 1` of the sha, `python3` for score.py, tmux/asciinema
  dropped (Claude Code agent, not terminus-2), agent layer appended. /app gets one fresh local commit
  (no upstream history) so the solver can diff.
- Tests: Hadi's `security.test.ts` (14), `functional.test.ts` (14) and `support/harness.ts` kept
  unchanged in behaviour (only the import path moved). `test.sh` from the template: kill block,
  vitest per group with the JUnit reporter into /logs/verifier/{security,functional}/. `score.py`
  copied unchanged (Hadi's score.mjs dropped; our scorer is all-or-nothing for 1.0).
- task.toml: template, offline allowlist, agent timeout 7200.

## Traps
1. Standalone refresh / code-exchange helpers (shape: unlisted route to the same sink; other
   credential types). `refreshAuthorization()` (auth.ts:2343) and `exchangeAuthorization()` (:2280)
   send the saved, issuer-stamped client information, refresh token and code to whatever server they
   are pointed at; nothing checks the stamp in `executeTokenRequest()` (:2168). The upstream fix only
   checks in `fetchToken()`. Visible clues: executeTokenRequest's doc names its three callers;
   `discoverOAuthServerInfo()`'s doc recommends it for "token refresh" outside `auth()`.
   Tests: 2 security (refresh helper; code-exchange helper), 3 coupled functional (refresh at the same
   server; refresh given only the AS URL, whose `String(URL)` adds a trailing slash; app-driven code
   exchange). Wrong fix: `miss_trap_helpers.patch`.
2. Tokens returned by the standalone helpers carry no binding (shape: missing-authority fail-open
   fallback, second-order). An application saves what `fetchToken()` / `refreshAuthorization()` return,
   as the docs recommend ("round-trip verbatim and you're protected"); these tokens have no issuer, so
   when a later `auth()` run resolves the attacker's server, the stored (stamped) registration is
   discarded and re-registered there, and the legacy back-stamp (auth.ts:1369-1375) binds the
   unstamped refresh token to the attacker and refreshes it there. Tests: 2 security (fetchToken
   code redemption then `auth()`; refresh-helper output then the transport), 3 coupled functional
   (both token origins keep refreshing at the same server; credentials stored with no binding by an
   earlier version keep working). Wrong fix: `miss_trap_unbound_tokens.patch`.
   Two valid fixes, both accepted: `auth()` ignores unstamped tokens once the stored registration
   proved to belong to another server (reference), or the helpers stamp the tokens they return
   (`alt_correct_fix.patch`; changes the helpers' return value, 14 repo tests' `toEqual` fail).
3. Also added: functional "MCP server moves to another AS: a DCR client signs up there afresh"
   (catches fixes that throw on every mismatch in `auth()`), and preservation clauses for it, for
   providers without `expectedIssuer`, and for legacy unbound storage in the instruction.

Existing shapes already in Hadi's tests (not counted as new traps): data producer off the check's path
(schemas); neighbour precedent (copying auth()'s discard-and-continue into fetchToken still sends
private_key_jwt assertions through addClientAuthentication); check after adjustment (credentials
loaded inside prepareTokenRequest).

## Reference fix
Upstream source-only fix (Hadi's fix.patch) + issuer check on the stamped client information in
`executeTokenRequest()` + `auth()` ignoring unstamped tokens after a mismatched registration.
Typechecks (`tsc --noEmit`, packages/client), repo client tests 900/900 and core tests pass.

## What I verified (local runs in the image, before the gate)
- Vulnerable: 18/18 security fail, each new test on its leak assertion (not setup); 21/21 functional pass.
- Reference: 1.0. alt_correct_fix and hardening_fix: 1.0.
- upstream_fix: fails exactly the 4 trap tests. miss_trap_helpers / miss_trap_unbound_tokens: each
  fails only its own 2 tests. check_only: 4 schema tests (the token-schema test is also closed by the
  trap-2 fix). origin_only / prefix compare: lookalike tenant. secret_only: both assertion tests.
  check_before_prepare_only: lazily-loaded + trap 1. refuse_unbound, throw_on_mismatch_in_auth,
  disable_feature: functional failures.
- Repo's own tests at the vulnerable commit: client 900/900 (auth subset 315/315).
- No advisory text in /app; /app/.git has one local commit.

## Not verified / guesses
- Whether either trap beats MiMo or DeepSeek (no model runs by design).
- Fairness of trap 1 rests on the instruction's "whichever of the SDK's OAuth client functions the
  application uses"; a reviewer could argue a helper given explicit credentials and a destination is
  the caller's responsibility. Trap 2 rests on "however that sign-in was done". The blind fix decides.
- Hadi's finding that one sentence pointing at the saved-credentials path flips DeepSeek: my new
  scope phrases are abstract (no saving/loading/schema words), but they are new text, so DeepSeek's
  0/3 on the base is not guaranteed to carry over.
- Not tested: keyed-by-issuer providers holding single-slot tokens obtained from fetchToken (closed by
  the alt fix, not by the reference); `skipIssuerMetadataValidation` lets a server's self-declared
  issuer pass the stamp check (upstream documents it as accepted risk) — left out as unfair.

## Gate (2026-10-16)
- static: only the expected problems (no blind patch, no FAIRNESS.md yet).
- nop: PASSED (18 security fail, 21 functional pass). oracle: PASSED (3 identical 1.0 runs).
- patches: PASSED, all 13 as declared (gate_report.partial.json). mkpatches.py rebuilds checks/.
- End: 2026-10-16T12:38:08Z

## 2026-10-16 full strict gate: FAILED on the blind patch — ON HOLD (lead)
nop, oracle (3x) and the builder's patch checks passed, but `blind_opus.patch` (Opus, saw only
instruction.md + the vulnerable tree) scored 0.7778: it closed both new traps (helpers route;
unstamped-token back-stamp) but missed Hadi's base producer (credentials saved and reloaded through
the SDK's zod schemas lose `issuer`), failing the 4 "loaded through the client-information schema"
security tests. By the gate rule the task is not shown to be findable from the report alone, so it
is NOT trialled. Evidence is mixed: MiMo found that path in Hadi's runs, under his (slightly
different) wording; the one sentence that would make it findable made DeepSeek solve 3/3 (Hadi).
A second blind attempt was deliberately not run (re-running until one passes would defeat the
check). Decision for the user: (a) drop the base-producer tests and keep the two new traps
(the task then leans on traps 1-2 only), (b) state that applications reload saved credentials with
the SDK's own schemas (likely makes it easy for DeepSeek), or (c) shelve.
