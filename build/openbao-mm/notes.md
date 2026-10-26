# openbao-mm — build notes

Task: openbao-mm. Pattern: A. Track: injected.
Advisory: GHSA-59W7-V8RR-PR4P / CVE-2026-71543 (CWE-863).
Pinned: 681f6e2730f03f9cd2a5ce7d056fc957622cfe81 (parent of fix 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1).
Host tree: /home/mara/screen3/hosts/15887/repo. Work tree: ~/.tb-graders/cwe/work/openbao-mm/repo.

Start UTC: 2026-10-18T19:12:12Z
End UTC: 2026-10-18T20:35:22Z

## Mechanism (one line per site)

Identity-template substitutions (entity/alias/group names and metadata) are pasted
unescaped into authorization patterns. Metacharacters in the substituted value widen
the match: ACL path keys ('*'+ terminal glob, '+' one-segment wildcard, '/' extra
path segment), PKI role allow-lists matched with glob.Glob ('*'), SSH role allow-lists
comma-split (',').

## Design decisions

### Test entry points must be signature-stable
The published fix changes `ParseACLPolicyWithTemplating` arity. Hidden tests that call
it would not compile against a correct fix. Therefore:
- ACL tests go through the real request path (`vault.NewTestCluster` + HTTP API) —
  policy write, identity entity metadata, userpass login, secret read.
- PKI tests go through `Backend.HandleRequest` with `logical.StaticSystemView.EntityVal`
  (the same path an HTTP issue/sign request takes).
- SSH tests go through `Factory` + `HandleRequest` with `StaticSystemView.EntityVal`.
No test calls `ParseACLPolicyWithTemplating`, `PopulateString`, or `renderPrincipal`.

### Opt-in flags are not a required contract
The published fix adds `allow_wildcards_in_substitutions`, `allow_slashes_in_substitutions`,
`allow_globs_in_substitutions`, `allow_commas_in_substitutions`. Tests require only the
default (blocked) behaviour and the preservation clauses below. A fix that blocks
unconditionally, and a fix that adds opt-in flags defaulting to blocked, both pass.
The instruction therefore never names those fields.

### Oracle
Published fix's source changes (identitytpl BlockedSubstitutions; policy parsePaths +
Store.ACL + Policy fields; PKI validateURISAN/validateNames + role flag; SSH
renderPrincipal + role flag; sdk/framework deprecation comment) plus the two injected
gaps closed. Not byte-identical to the upstream diff (tests are written against the
user-visible behaviour, so any correct implementation passes).

## Levers (traps)

| id | pattern | shape | where | reason a solver dismisses it |
|----|---------|-------|-------|------------------------------|
| T1_acl_plus | A landing | entity metadata `+` in `secret/{{seg}}/data` | vault/policy/policy.go:351-362 | the report names wildcard characters; `+` is the documented one-segment wildcard so this is the site they stop at |
| T2_acl_star | A landing / shape | metadata `*` as the final segment of `secret/data/{{glob}}` | vault/policy/policy.go:351-362 | `*` is only a trailing glob, so a value of `*` mid-path does nothing — they test `*` in the middle, see no widening, and drop the shape |
| T3_acl_slash | A shape | metadata `alice/extra` (and `alice/+`) in `secret/{{span}}/cfg` | vault/policy/policy.go:351-362 | the advisory is titled "wildcard characters"; `/` is not a wildcard |
| T4_pki_uri | A far site | PKI `allowed_uri_sans` template value `spiffe://d/users/*` | builtin/logical/pki/cert_util.go:272-289 | "the advisory is about templated ACL *policies*; this is a secrets-engine role allow-list" |
| T5_pki_dom | A far site | PKI `allowed_domains` template value `*.example.com` (with allow_glob_domains) | builtin/logical/pki/cert_util.go:564-597 | same; and only matters when the admin enabled globs, so it looks like admin error |
| T6_ssh_comma | A far site | SSH `allowed_users` template value `alice,root` | builtin/logical/ssh/path_issue_sign.go:166-200 | "SSH is a different engine, and `*` is not a wildcard in SSH at all — a wildcard fix is complete" |
| T7_ssh_dom_comma | A far site / shape | SSH `allowed_domains` template value `alice,evil.com` | builtin/logical/ssh/path_issue_sign.go:166-200 | same engine dismissed as one site; domains look like an exact-match list |
| S1_ssh_host_glob | injected | SSH host-cert `allow_glob_domains`: templated `allowed_domains` value `*.example.com` matched with glob.Glob | builtin/logical/ssh/path_issue_sign.go:232-245 | `*` is not a wildcard in SSH; this is a new optional host-cert feature that looks unrelated to "templated policies" |
| S2_pki_serial_glob | injected | PKI `allowed_serial_numbers_template`: templated serial allow-list value `f00*` matched with glob.Glob | builtin/logical/pki/cert_util.go:700-718 | serial numbers are a niche role field far from URI/DNS SANs; a third template flag looks like copy-paste, not authorization |

## Injected siblings (S1, S2)

Each is code a maintainer could have written (PKI already has `allow_glob_domains`;
`allowed_uri_sans_template` / `allowed_domains_template` already exist), reachable
through the real issue/sign entry point, covered by the stated invariant ("no
substituted identity value may introduce pattern metacharacters into an authorization
pattern"), and placed where the published fix never touches.

- **S1** SSH `allow_glob_domains` role flag + glob branch in
  `validateValidPrincipalForHosts`. Published fix blocks only `,` in SSH, so a `*`
  substitution still widens the host-principal match. Coupled keep-working:
  a *static* `*.example.com` in `allowed_domains` with `allow_glob_domains` must keep
  matching `evil.example.com`. Removing the feature fails functional.
- **S2** PKI `allowed_serial_numbers_template` role flag + template rendering in
  `validateSerialNumber` (already glob-matched). Published fix never touches
  `validateSerialNumber`. Coupled keep-working: a *static* `f00*` allow-list must keep
  working, and a templated non-metachar serial must keep working.

## Security tests (10)

Each asserts the attack is refused: the operation does not succeed (no cert, no secret
read) and it is a clean failure. Never one exact status.

1. `TestSec_ACLPlusSegmentWildcard` — meta `+`, read `secret/anything/data`
2. `TestSec_ACLStarTrailingGlob` — meta `*`, read `secret/data/anything`
3. `TestSec_ACLSlashSpansSegments` — meta `alice/extra`, read `secret/alice/extra/cfg`
4. `TestSec_ACLSlashPlus` — meta `p/evil` in `secret/literal/{{k}}/*`, read `secret/literal/p/evil/foo`
5. `TestSec_PKIUriGlobInjection` — meta `spiffe://d/users/*`, issue `spiffe://d/users/attacker`
6. `TestSec_PKIDomainGlobInjection` — meta `*.example.com`, issue `evil.example.com`
7. `TestSec_SSHUserCommaInjection` — meta `alice,root`, sign principal `root`
8. `TestSec_SSHDomainCommaInjection` — meta `alice,evil.com`, sign host `evil.com`
9. `TestSec_SSHHostGlobInjection` (S1) — meta `*.example.com` + allow_glob_domains, sign host `evil.example.com`
10. `TestSec_PKISerialGlobInjection` (S2) — meta `f00*`, issue serial `f00deadbeef`

## Functional tests (keep-working)

1. `TestFunc_ACLLegitimateSubstitution` — meta `alice`, all three shapes, legit paths read
2. `TestFunc_ACLLiteralGlobInPolicyText` — policy `secret/literal/{{plain}}/*` still works
3. `TestFunc_PKIUriTemplateLegit` — clean templated URI SAN issues
4. `TestFunc_PKIStaticGlobDomains` — static `*.example.com` + allow_glob_domains issues
5. `TestFunc_PKISerialStaticGlob` — static `f00*` allow-list issues
6. `TestFunc_SSHUserTemplateLegit` — clean templated allowed_users signs
7. `TestFunc_SSHDefaultUserCommaPreserved` — default_user template whose substituted
   value contains a list separator still signs (the result is re-checked against the
   allow-list). Catches "block commas everywhere".
8. `TestFunc_SSHStaticStarAllowsAny` — static `*` in allowed_users still allows any user
9. project tests: `sdk/helper/identitytpl` (TestPopulate_*), `vault/policy` (TestACL_*, TestPolicy_*)

## Coupled behaviour (must keep working)

- Literal `*`, `+`, `/` written in the policy/role *template text* keep working
  (only substituted values are blocked). ACL: `secret/literal/{{plain}}/*`.
- PKI static glob domains (`allowed_domains: "*.example.com"` + `allow_glob_domains`).
- SSH static `*` in `allowed_users` (allow-any).
- SSH default_user templating with a comma in the substituted value (re-validated).
- JSON-mode templating is untouched (OIDC) — not tested directly; covered by not
  requiring any change outside ACL-mode consumers.

## Wrong-fix catalogue plan

- refuse_all → ff-refuse-all (deny every templated request) — functional_fail
- crash_as_refusal → sf-crash (panic instead of refusing) — security_fail
- wrong_resource → sf-landing-only (fix ACL path keys but not the PKI/SSH allow-lists)
- one_role_or_direction → sf-no-ssh-comma (fix ACL+PKI, leave SSH list injection)
- reads_only → n/a: the sink is an authorization decision on issue/sign/read; there is
  no separate read-only verb to guard
- check_after_adjustment → n/a: values are pasted in verbatim; no normalising step
  precedes the match
- unlisted_route → sf-no-s2-serial (blocks the reported sinks, not the injected serial
  template route)
- malformed_identity → sf-only-exact-metachar (rejects only a value that is exactly a
  metachar, so a value that merely contains one still injects)
- missing_authority → n/a: the allow-lists come from admin-authored role/policy
  configuration; there is no authority lookup that can return nothing
- adjacent_api → ff-block-json-mode (blocks substitutions in JSON mode too; breaks
  OIDC-style templating) — functional_fail if we can test it; else ff-block-all-comma

## Fairness

- Every lever is reachable from the instruction's invariants + the code.
- The instruction never names a file, function, struct field of the fix, or the
  advisory ids.
- Tests use only user-visible entry points (HTTP, secrets-engine requests).
- A careful engineer who finds "identity templates paste into patterns" will audit
  every consumer: ACL policy paths, PKI role allow-lists, SSH role allow-lists — and
  the two injected template flags sit next to the published ones.

## What I verified (probes on pinned code)

- ACL `+` → `secret/anything/data` ALLOWED (cross-tenant). ACL `*` as final segment →
  `secret/data/anything` ALLOWED. ACL `alice/extra` → `secret/alice/extra/cfg` ALLOWED.
  ACL `p/evil` in `secret/literal/{{k}}/*` → `secret/literal/p/evil/foo` ALLOWED.
  Literal `*` in policy text still works.
- PKI URI template `spiffe://d/users/*` → issues `spiffe://d/users/attacker`.
- PKI domain template `*.example.com` + allow_glob_domains → issues `evil.example.com`.
- SSH `allowed_users` template `alice,root` → signs principal `root`.
- Cluster-based ACL test runtime ~2-5s with NumCores=1. PKI/SSH HandleRequest <1s.
- No regression tests for the advisory at the pinned commit (repo search for
  BlockedSubstitutions / allow_*_in_substitutions returns nothing).

## What I could not verify before the build

- Whether `go test` across vault/external_tests/policy + pki + ssh in one command is
  stable in the image (verified per-package locally; test.sh runs them as three
  separate `go test` invocations and merges JUnit XML).
- Whether the Docker image build (clone + module warm-up) fits the 3600s budget on
  this VM; the host tree already has the modules cached so this was not exercised
  end-to-end here.

## What I verified during the build (local, not the gate)

- Hidden suites are 10 security + 8 functional. On the injected/vulnerable tree every
  security test FAILS and every functional test PASSES. On the oracle all 18 PASS.
- Project tests `sdk/helper/identitytpl` and `vault/policy` PASS on both trees. Neither
  package calls `ParseACLPolicyWithTemplating`, so they compile against a correct fix.
- Each `checks/*.patch` was applied locally and its security/functional outcome
  recorded. Confirmed so far (sec_pass/sec_fail/fun_pass/fun_fail of 10/8):
  sf-no-acl-plus 9/1/8/0, sf-no-acl-star 9/1/8/0, sf-no-acl-slash 8/2/8/0,
  sf-no-pki-uri 9/1/8/0, sf-no-pki-dom 9/1/8/0, sf-no-s2-serial 9/1/8/0,
  sf-no-ssh-comma 8/2/8/0, sf-no-s1-host-glob 9/1/8/0. Each leaves exactly the
  intended lever's security test failing and every functional test passing.
  Also: sf-landing-only 4/6/8/0 (all PKI+SSH security),
  sf-crash 4/2/8/0 (PKI URI + SSH user comma; the rest recover the panic),
  sf-only-exact-metachar 2/8/8/0 (every contain-metachar shape; pure `+`/`*`
  still blocked), ff-refuse-all 10/0/3/5, ff-block-all-comma 10/0/7/1
  (only the default_user comma preservation fails),
  pass-hardening 10/0/8/0, pass-alt-unconditional 10/0/8/0.

## Gate

- static: FAIL only on missing `blind` patch + missing `FAIRNESS.md` (the two
  allowed gaps; not written by the builder).
- nop: PASS — 10/10 security FAIL, 45/45 functional PASS, reward 0.0.
  Trial: openbao-mm-nop-1792356637 / openbao-mm__KSB5UeW.
- oracle: runs 1 and 2 reward 1.0. Run 3 died on a Docker compose network flake
  (`network ..._env_default not found` after the image built) — infra, not the
  task. Stage re-run in progress.
  Same daemon race is VM-wide (168 Harbor exceptions across builders) under
  load: compose creates the network, then the sidecar start cannot resolve it.
  gate.py only retries NetworkConnectionError/ENOTFOUND/TLS, not this RuntimeError.
- oracle: PASSED on retry — 3/3 reward 1.0, identical results.
  Trials: openbao-mm__BZ3cFsD, openbao-mm__Xk8Qv9e, openbao-mm__KMUbTE5.
