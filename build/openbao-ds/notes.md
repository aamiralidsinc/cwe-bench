# openbao-ds — build notes

Task: openbao-ds. Pattern: A. Track: injected.
Advisory: GHSA-59W7-V8RR-PR4P / CVE-2026-71543 / GO-2026-6556 (CWE-863).
Pinned: 681f6e2730f03f9cd2a5ce7d056fc957622cfe81 (parent of fix 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1).
Work tree: ~/.tb-graders/cwe/work/openbao-ds/repo (pinned, no .git).
Scratch trees: base (pinned+inject), oracleclean (base+fix), variants/<check>.

Start UTC: 2026-10-19T18:12:38Z
End UTC: (filled at the end)

## Mechanism (one line per site)

Identity-template substitutions (entity/alias/group names and metadata) are pasted
unescaped into authorization patterns. A metacharacter in the substituted value
widens the match: ACL path keys (`*` trailing glob, `+` one-segment wildcard, `/`
extra path segments), PKI role allow-lists matched with glob.Glob (`*`), SSH role
allow-lists comma-split (`,`).

## Design decisions

### Tests drive user-visible entry points only
The published fix changes the arity of `ParseACLPolicyWithTemplating`; a hidden test
calling it would not compile against a correct fix. So:
- ACL tests go through the real request path (`vault.NewTestCluster` + HTTP API):
  policy write, identity entity metadata, userpass login, secret read.
- PKI tests go through `Backend.HandleRequest` with `logical.StaticSystemView.EntityVal`
  (the path an HTTP issue/sign request takes).
- SSH tests go through `Factory` + `HandleRequest` with `StaticSystemView.EntityVal`.
No test calls the templating helper, the ACL parser, or the principal renderer directly.

### Opt-in flags are not a required contract
The published fix adds opt-in role/policy flags. The tests require only the default
(blocked) behaviour plus the preservation clauses. A fix that blocks
unconditionally and a fix that adds opt-in flags defaulting to blocked both pass.
The instruction therefore never names those fields.

### Oracle
Published source changes (blocked substitutions in the shared templating helper;
ACL path parsing + policy store + policy CRUD fields; PKI URI/domain allow-lists +
role flag; SSH principal rendering + role flag) plus the two injected gaps closed.
Not byte-identical to upstream (any correct implementation passes the tests).

## Levers (traps)

| id | pattern | shape | where | reason a solver dismisses it |
|----|---------|-------|-------|------------------------------|
| T1_acl_plus | A landing | entity metadata `+` in `secret/{{k}}/data` | vault/policy/policy.go:342 (parsePaths), fed by vault/policy/policy_store.go:679 | the report names pattern wildcards and `+` is the documented one-segment wildcard, so this is the site they stop at |
| T2_acl_star | A landing / shape | metadata `*` as the final segment of `secret/data/{{k}}` | vault/policy/policy.go:342 | `*` only matches at the end of a path, so a value placed mid-path does nothing; tested in the middle, no widening, shape dropped |
| T3_acl_slash | A shape | metadata `alice/extra` in `secret/{{k}}/cfg` | vault/policy/policy.go:342 | the report is about wildcards; `/` is not a wildcard |
| T3b_acl_slash_beside_glob | A shape | metadata `p/evil` in `secret/literal/{{k}}/*` | vault/policy/policy.go:342 | a slash next to an administrator's literal wildcard still looks like the written rule |
| T4_pki_uri | A far site | PKI `allowed_uri_sans` template value `spiffe://d/users/*` | builtin/logical/pki/cert_util.go:269 (validateURISAN) | "the report is about templated ACL policies; a secrets-engine role allow-list is a neighbouring admin-configured feature" |
| T5_pki_dom | A far site | PKI `allowed_domains` template value `*.example.com` (allow_glob_domains) | builtin/logical/pki/cert_util.go:393 (validateNames) | same engine dismissed; only matters when the admin enabled globs, so it looks like admin error |
| T6_ssh_user | A far site | SSH `allowed_users` template value `alice,root` | builtin/logical/ssh/path_issue_sign.go:167 (renderPrincipal) | "SSH is a different engine, and `*` is not a wildcard there; a wildcard fix is complete" |
| T7_ssh_dom | A far site / shape | SSH `allowed_domains` template value `alice,evil.com` | builtin/logical/ssh/path_issue_sign.go:167 | same engine dismissed; domains look like an exact-match list |
| S1_ssh_host_glob | injected | SSH host-cert `allow_glob_domains`: templated allowed-domain value `*.example.com` matched with glob.Glob | builtin/logical/ssh/path_issue_sign.go:233 (validateValidPrincipalForHosts) | `*` is not a wildcard in SSH's list-splitting sense, and this is an optional host-cert feature that reads as unrelated to templated policies |
| S2_pki_userid | injected | PKI `allowed_user_ids_template`: templated user-id allow-list value `*` matched with glob.Glob | builtin/logical/pki/cert_util.go:674 (validateUserId) | user ids are a niche subject field far from URI/DNS SANs; a further template flag on the same role reads as copy-paste, not authorization |

## Injected siblings

Each is code a maintainer could have written, reachable through the real
issue/sign entry point, covered by the stated invariant, and placed where the
published fix never touches.

- **S1** SSH `allow_glob_domains` role flag + glob branch in
  `validateValidPrincipalForHosts`. The published fix blocks only `,` in SSH, so a
  `*` substitution still widens the host-principal match. Coupled keep-working: a
  *static* `*.example.com` in `allowed_domains` with `allow_glob_domains` still
  matches `host.example.com`.
- **S2** PKI `allowed_user_ids_template` role flag + identity rendering in
  `validateUserId` (already glob-matched). The published fix never touches
  `validateUserId`. Coupled keep-working: a *static* `dev*` allow-list still
  matches, and a templated ordinary user id still works.

## Security tests (10)

Each asserts the attack is refused: the operation does not succeed (no secret, no
certificate, no signature) and it is a clean failure. Never one exact status.

1. TestSec_ACLPlusSegmentWildcard — meta `+`, read `secret/anything/data`
2. TestSec_ACLStarTrailingGlob — meta `*`, read `secret/data/anything`
3. TestSec_ACLSlashSpansSegments — meta `alice/extra`, read `secret/alice/extra/cfg`
4. TestSec_ACLSlashBesideLiteralWildcard — meta `p/evil`, read `secret/literal/p/evil/foo`
5. TestSec_PKIUriGlobInjection — meta `spiffe://d/users/*`, issue `spiffe://d/users/attacker`
6. TestSec_PKIDomainGlobInjection — meta `*.example.com`, issue `evil.example.com`
7. TestSec_PKIUserIdGlobInjection (S2) — meta `*`, issue user id `admin`
8. TestSec_SSHUserCommaInjection — meta `alice,root`, sign principal `root`
9. TestSec_SSHDomainCommaInjection — meta `alice,evil.com`, sign host `evil.com`
10. TestSec_SSHHostGlobInjection (S1) — meta `*.example.com` + allow_glob_domains, sign host `evil.example.com`

## Functional tests (11)

1. TestFunc_ACLLegitimateSubstitution — clean substituted segment still reads
2. TestFunc_ACLLiteralGlobInPolicyText — administrator's literal trailing `*` still matches
3. TestFunc_ACLMultiSegmentPolicy — clean segment in a multi-segment rule still reads
4. TestFunc_PKIUriTemplateLegit — clean templated URI SAN issues
5. TestFunc_PKIStaticGlobDomains — static `*.example.com` + allow_glob_domains issues
6. TestFunc_PKIStaticUserIdGlob — static `dev*` user-id allow-list issues
7. TestFunc_PKIUserIdTemplateLegit — clean templated user id issues
8. TestFunc_SSHUserTemplateLegit — clean templated allowed_users signs
9. TestFunc_SSHDefaultUserCommaPreserved — default user rendered from identity data
   whose value contains a list separator still signs (re-validated afterwards)
10. TestFunc_SSHStaticStarAllowsAny — static `*` in allowed_users still allows any
11. TestFunc_SSHHostStaticGlobDomains — static glob domain + allow_glob_domains signs

plus the project's own `sdk/helper/identitytpl` and `vault/policy` tests, restored
from pristine copies.

## Checks

| patch | expect | what it proves |
|-------|--------|----------------|
| sf-no-acl-plus | security_fail | dropping the one-segment wildcard from the ACL block set is caught |
| sf-no-acl-star | security_fail | dropping the trailing glob is caught |
| sf-no-acl-slash | security_fail | dropping the path separator is caught |
| sf-no-pki-uri | security_fail | leaving the URI allow-list unguarded is caught |
| sf-no-pki-dom | security_fail | leaving the domain allow-list unguarded is caught |
| sf-no-s2-userid | security_fail | leaving the injected user-id allow-list unguarded is caught |
| sf-no-ssh-comma | security_fail | leaving list-separator injection is caught |
| sf-no-s1-host-glob | security_fail | not closing the injected host-domain glob is caught |
| sf-landing-only | security_fail | fixing only the reported landing site is caught |
| sf-crash | security_fail | panicking instead of a clean refusal is caught |
| sf-only-exact-metachar | security_fail | a whole-value-only check is caught |
| ff-refuse-all | functional_fail | refusing every templated rule breaks legitimate use |
| pass-hardening | pass | oracle + default-deny in the shared helper still scores 1.0 |
| pass-alt-unconditional | pass | an independent fix with no opt-in flags scores 1.0 |

## Wrong-fix catalogue

- refuse_all → ff-refuse-all
- crash_as_refusal → sf-crash
- wrong_resource → sf-landing-only
- one_role_or_direction → sf-no-ssh-comma
- reads_only → n/a: the sink is an authorization decision on read/issue/sign; there
  is no separate read-only verb to guard
- check_after_adjustment → n/a: substituted values are pasted verbatim; no
  normalising step precedes the match
- unlisted_route → sf-no-s2-userid
- malformed_identity → sf-only-exact-metachar
- missing_authority → n/a: the allow-lists come from administrator-authored role and
  policy configuration; there is no authority lookup that can return nothing
- adjacent_api → ff-refuse-all

## Verified (local, before the gate)

- Pinned tree: all 10 security tests FAIL (the attacks succeed); all 11 functional
  tests PASS; project tests `sdk/helper/identitytpl` and `vault/policy` PASS.
- Oracle tree: 10/10 security PASS, 11/11 functional PASS, project tests PASS.
- Patches apply cleanly to the pristine pinned tree (`patch -p1 --dry-run`).
- Per-check security/functional outcomes: see `out/validation.txt`.
- The pinned commit contains no regression tests for this advisory (search for the
  blocked-substitution helper returns nothing before the fix).

## Not verified before the build

- Whether the Docker image build fits the budget on this VM (module warm-up is
  cached on the host, not in the image).
- Runtime stability of the in-process test cluster under the grader's CPU limits
  (run with NumCores=1; ACL suites take ~15-30 s per group locally).

## Local validation results (per check)

Each line is `<patch> <group> <package> <verdict> pass/fail`:

```
sf-no-acl-plus     sec policy  FAILED pass=3 fail=1
sf-no-acl-star     sec policy  FAILED pass=3 fail=1
sf-no-acl-slash    sec policy  FAILED pass=2 fail=2
sf-no-pki-uri      sec pki     FAILED pass=2 fail=1
sf-no-pki-dom      sec pki     FAILED pass=2 fail=1
sf-no-s2-userid    sec pki     FAILED pass=2 fail=1
sf-no-ssh-comma    sec ssh     FAILED pass=1 fail=2
sf-no-s1-host-glob sec ssh     FAILED pass=2 fail=1
sf-landing-only    sec pki/ssh FAILED pass=0 fail=3 each; sec policy PASS pass=4
sf-crash           sec pki     FAILED pass=0 fail=1 panic=1 (process panics)
sf-only-exact-metachar sec pki/ssh/policy FAILED (2/3/2 failing)
ff-refuse-all      func policy FAILED pass=0 fail=3 (pki/ssh functional pass)
pass-hardening     sec 10/10 PASS, func 11/11 PASS, project tests PASS
pass-alt-unconditional sec 10/10 PASS, func 11/11 PASS
```
