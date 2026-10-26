# FAIRNESS — openbao-ds

Legend (verbatim `instruction.md` sentences):

- **P1** — "No value substituted from identity data may introduce a pattern metacharacter into an authorization pattern. This holds wherever a substituted value is matched against something the caller supplies — a request path, or a name, identifier or host in a certificate request — and for every identity source (entity, alias and group names and metadata)."
- **P2** — "Pattern metacharacters here include the wildcards used when a path pattern is matched, the star used when a name, identifier or host pattern is matched, the separator that splits an allow-list into entries, and the path separator."
- **P3** — "A request that would rely on such a value is refused with a client error and no side effect: no secret is returned and no certificate is issued or signed."
- **K1** — "Metacharacters written literally into a policy or role by an administrator keep their present meaning. Only substituted values are subject to this rule."
- **K2** — "Legitimate substitutions keep working exactly as today: a caller whose identity data is an ordinary allowed value still reads the paths that value grants and still receives certificates for it."
- **K3** — "An allow-list entry that is a single literal star still means \"any\"."
- **K4** — "A policy path that places a placeholder next to a literal wildcard, such as a trailing `*`, continues to match as it does now."
- **K5** — "A certificate-role allow-list that is a literal glob written by an administrator continues to match exactly as it does now."
- **K6** — "A default user or similar principal filled from identity data is still used when a role names one, and its rendered value is still re-checked against the allow-list afterwards."
- **STD** — standard expert knowledge: "Keep every legitimate use working" plus the visible project tests, which the instruction forbids editing.

## 1. Per-test fairness

| test (file::name) | what it asserts | covering sentence | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| security/acl/sec_acl_test.go::TestSec_ACLPlusSegmentWildcard | substituted `+` in `secret/{{k}}/data` cannot read `secret/anything/data` | P1 (wildcard class) + P2 + P3 | no — block `+` in the substituted value | low |
| security/acl/sec_acl_test.go::TestSec_ACLStarTrailingGlob | substituted `*` as final segment cannot read `secret/data/anything` | P1 + P2 + P3 | no | low |
| security/acl/sec_acl_test.go::TestSec_ACLSlashSpansSegments | substituted `alice/extra` cannot span segments into `.../cfg` | P1 + P2 ("path separator") + P3 | no — block `/` in the substituted value; literal path text is untouched | low |
| security/acl/sec_acl_test.go::TestSec_ACLSlashBesideLiteralWildcard | substituted `p/evil` beside an admin literal `*` cannot read `secret/literal/p/evil/foo` | P1 + P2 + P3; K4 preserves the literal `*` | no — guard only the substituted value | low |
| security/acl/sec_acl_test.go::TestSec_ACLEntityNameWildcard | entity name `+` cannot widen an ACL path | P1 (entity source) + P2 + P3 | no | low |
| security/acl/sec_acl_test.go::TestSec_ACLAliasNameGlob | alias name `*` on a linked mount cannot widen | P1 (alias source) + P2 + P3 | no | low |
| security/acl/sec_acl_test.go::TestSec_ACLAliasMetadataSlash | alias custom metadata `alice/extra` cannot span | P1 (alias metadata) + P2 + P3 | no | low |
| security/acl/sec_acl_test.go::TestSec_ACLGroupNameWildcard | group name `+` cannot widen | P1 (group source) + P2 + P3 | no | low |
| security/acl/sec_acl_test.go::TestSec_ACLGroupMetadataGlob | group metadata `*` cannot widen | P1 (group metadata) + P2 + P3 | no | low |
| security/pki/sec_pki_test.go::TestSec_PKIUriGlobInjection | templated `allowed_uri_sans` `spiffe://d/users/*` cannot issue | P1 ("name ... in a certificate request") + P2 (star) + P3 | no — block `*`, not `/`, in the URI render | low |
| security/pki/sec_pki_test.go::TestSec_PKIDomainGlobInjection | templated `allowed_domains` `*.example.com` cannot issue `evil.example.com` | P1 ("host in a certificate request") + P2 (star) + P3 | no | low |
| security/pki/sec_pki_test.go::TestSec_PKIUserIdGlobInjection | templated `allowed_user_ids` `*` cannot issue user id `admin` | P1 ("identifier") + P2 (star) + P3 | no | low |
| security/pki/sec_pki_test.go::TestSec_PKIAliasMetadataUriGlob | alias-metadata URI `spiffe://d/users/*` cannot issue | P1 + P2 + P3 (alias metadata) | no | low |
| security/pki/sec_pki_test.go::TestSec_PKIGroupNameDomainGlob | group name `*.example.com` cannot issue | P1 + P2 + P3 (group) | no | low |
| security/pki/sec_pki_test.go::TestSec_PKIEntityNameUserIdGlob | entity name `*` cannot issue a user id | P1 + P2 + P3 (entity) | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHUserCommaInjection | templated `allowed_users` `alice,root` cannot sign principal `root` | P1 + P2 (list separator) + P3 | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHDomainCommaInjection | templated `allowed_domains` `alice,evil.com` cannot sign host `evil.com` | P1 + P2 + P3 | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHHostGlobInjection | templated domain `*.example.com` under `allow_glob_domains` cannot sign `evil.example.com` | P1 ("host") + P2 (star) + P3 | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHAliasNameCommaInjection | alias name `alice,root` cannot sign `root` | P1 + P2 + P3 (alias) | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHGroupMetadataCommaInjection | group metadata `alice,evil.com` cannot sign | P1 + P2 + P3 (group) | no | low |
| security/ssh/sec_ssh_test.go::TestSec_SSHEntityNameHostGlob | entity name `*.example.com` cannot sign under glob domains | P1 + P2 + P3 (entity) | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLLegitimateSubstitution | clean `alice` still reads its path | K2 | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLLiteralGlobInPolicyText | admin literal trailing `*` beside a placeholder still matches | K1 + K4 | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLMultiSegmentPolicy | clean single-segment substitution in a multi-segment rule still reads | K2 | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLEntityNameLegit | clean entity name still grants | K2 | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLAliasValuesLegit | clean alias name and custom metadata still grant | K2 | no | low |
| functional/acl/func_acl_test.go::TestFunc_ACLGroupValuesLegit | clean group name and metadata still grant | K2 | no | low |
| functional/pki/func_pki_test.go::TestFunc_PKIUriTemplateLegit | clean templated URI SAN `spiffe://d/users/alice` issues | K2 | no — per-matcher: `/` is not a URI-glob metacharacter; a global `/` block would over-block (see Quality) | medium |
| functional/pki/func_pki_test.go::TestFunc_PKIStaticGlobDomains | admin literal `*.example.com` still matches | K1 + K5 | no | low |
| functional/pki/func_pki_test.go::TestFunc_PKIStaticUserIdGlob | admin literal `dev*` still matches | K1 | no | low |
| functional/pki/func_pki_test.go::TestFunc_PKIUserIdTemplateLegit | clean templated user id issues | K2 | no | low |
| functional/pki/func_pki_test.go::TestFunc_PKIAliasMetadataUriLegit | clean alias-metadata URI (contains `/`) issues | K2 | no — same per-matcher caveat | medium |
| functional/pki/func_pki_test.go::TestFunc_PKIGroupNameDomainLegit | clean group-name domain issues | K2 | no | low |
| functional/pki/func_pki_test.go::TestFunc_PKIEntityNameUserIdLegit | clean entity-name user id issues | K2 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHUserTemplateLegit | clean templated `allowed_users` signs | K2 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHDefaultUserCommaPreserved | comma-bearing default user is still used and re-checked | K6 | no — do not block `,` in the default-principal render | medium |
| functional/ssh/func_ssh_test.go::TestFunc_SSHStaticStarAllowsAny | literal `*` still allows any | K3 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHHostStaticGlobDomains | admin literal glob domain still signs | K1 + K5 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHAliasNameLegit | clean alias name signs | K2 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHGroupMetadataDomainLegit | clean group metadata signs | K2 | no | low |
| functional/ssh/func_ssh_test.go::TestFunc_SSHEntityNameHostLegit | clean entity-name host signs under glob domains | K2 | no | low |
| functional/project/identitytpl_templating_test.go::TestPopulate_Basic | all existing templating directives render unchanged | STD | no — extend `PopulateStringInput`; keep the visible call shape | low |
| functional/project/identitytpl_templating_test.go::TestPopulate_CurrentTime | time directive | STD | no | low |
| functional/project/identitytpl_templating_test.go::TestPopulate_FullObject | JSON-mode rendering unchanged | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_NewACL | root ACL construction | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_ControlGroup | control-group parse and evaluation | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_MFAMethods | MFA method merge and matching | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_Capabilities | capability merge | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_Root | root privileges | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_Single | literal glob/segment-wildcard precedence unchanged | STD + K1 | no | low |
| functional/project/policy_acl_test.go::TestACL_Layered | layered policy semantics | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_ParseMalformedPolicy | malformed policy errors | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_PolicyMerge | parameter merge | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_AllowOperation | allowed/denied parameter checks | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_ValuePermissions | value glob permissions | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_SegmentWildcardPriority | wildcard precedence | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_SegmentWildcardPriority_BareMount | bare-mount permissions | STD | no | low |
| functional/project/policy_acl_test.go::TestACL_CreationRace | concurrent `NewACL` stability | STD | no | low |
| functional/project/policy_acl_test.go::TestACLGrantingPolicies | granting-policy reporting | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_Parse | parsed `PathRules` deep-equal for literal policies | STD | no — natural fix leaves `PathRules` shape unchanged | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadRoot | invalid root key error text | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadPath | invalid path key error text | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadPolicy | invalid policy error text | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadWrapping | wrapping TTL error text | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadCapabilities | invalid capability error text | STD | no | low |
| functional/project/policy_policy_test.go::TestPolicy_ParseBadSegmentWildcard | `+*` rejection error text | STD | no | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible WRONG fix | caught by |
|---|---|---|
| P1 landing site | guard only the reported ACL path site | `TestSec_PKIUriGlobInjection`, `TestSec_SSHUserCommaInjection`; `checks/sf-landing-only.patch` |
| P1 ACL shapes | block `+` only, or treat `/` as "not a wildcard" | `TestSec_ACLStarTrailingGlob`, `TestSec_ACLSlashSpansSegments`, `TestSec_ACLSlashBesideLiteralWildcard`; `sf-no-acl-star`, `sf-no-acl-slash` |
| P1 identity sources | check the entity-metadata lookup only | the 11 `TestSec_*Name*`/`*Metadata*` tests; `sf-entity-metadata-only.patch` |
| P1 whole-value check | reject only a value exactly equal to a metacharacter | `TestSec_ACLSlashSpansSegments`, `TestSec_PKIUriGlobInjection`, `TestSec_SSHUserCommaInjection`; `sf-only-exact-metachar.patch` |
| P2 metacharacter classes | block `*`/`+` but not `,` (or not `/`) | `TestSec_SSHUserCommaInjection`, `TestSec_SSHDomainCommaInjection`, ACL slash tests; `sf-no-ssh-comma`, `sf-no-acl-slash` |
| P3 refusal form | panic instead of a clean refusal | `sf-crash.patch` (recorded as a test error, not a pass) |
| P4 literal text | strip/block literal admin metacharacters | `TestFunc_ACLLiteralGlobInPolicyText`, `TestFunc_PKIStaticGlobDomains`, `TestFunc_SSHStaticStarAllowsAny`, `TestFunc_SSHHostStaticGlobDomains` |
| P5 legitimate use | disable templating / refuse every templated policy | `TestFunc_ACLLegitimateSubstitution`, `TestFunc_PKIUriTemplateLegit`, `TestFunc_SSHUserTemplateLegit`; `ff-refuse-all.patch` (functional fail) |
| trap `acl_plus` | drop `+` because it is the "documented" wildcard | `TestSec_ACLPlusSegmentWildcard`; `sf-no-acl-plus.patch` |
| trap `acl_star` | test `*` mid-path, see no widening, drop it | `TestSec_ACLStarTrailingGlob`; `sf-no-acl-star.patch` |
| trap `acl_slash` | fix wildcards only; `/` is not a wildcard | `TestSec_ACLSlashSpansSegments`, `TestSec_ACLSlashBesideLiteralWildcard`; `sf-no-acl-slash.patch` |
| trap `pki_uri` | treat a secrets-engine role allow-list as admin config, not authorization | `TestSec_PKIUriGlobInjection`; `sf-no-pki-uri.patch` |
| trap `pki_dom` | guard URI SANs only; blame the admin's `allow_glob_domains` | `TestSec_PKIDomainGlobInjection`; `sf-no-pki-dom.patch` |
| trap `ssh_comma` | wildcard-shaped SSH fix that leaves `,` | `TestSec_SSHUserCommaInjection`, `TestSec_SSHDomainCommaInjection`; `sf-no-ssh-comma.patch` |
| trap `ssh_host_glob` | block `,` only, leave `*` in the host-glob branch | `TestSec_SSHHostGlobInjection`; `sf-no-s1-host-glob.patch` |
| trap `pki_userid` | guard URI/DNS SANs, leave user ids | `TestSec_PKIUserIdGlobInjection`, `TestSec_PKIEntityNameUserIdGlob`; `sf-no-s2-userid.patch` |
| trap `other_identity_sources` | check only the entity metadata lookup | the 11 identity-source security tests; `sf-entity-metadata-only.patch` |

Wrong fixes that no test catches (add coverage):

- **SSH templated `allowed_users` = `*` (and `allowed_domains` = `*` without glob):** a literal `*` entry means "any"; a templated one would too. A fix that blocks `,` and guards only the host-glob branch passes all six SSH security tests. Add `TestSec_SSHUserStarInjection` (templated `allowed_users` = `*`, sign principal `root`).
- **P3 error class / side effect:** the security tests accept any non-success (error, `IsError()`, or nil response). Only `sf-crash` is caught; a 500-style refusal or a nil response passes. Assert an error/`IsError()` and no returned artifact — do not require a specific status.
- `wrong_fix_catalogue` entries `reads_only`, `check_after_adjustment`, `missing_authority` are correctly **n/a** (no read-only verb, verbatim substitution, admin-authored allow-lists).

## 3. Hints (3) and surface descriptions (3a) — "Required: generalize"

Every hint below is also a surface description; the rewording fixes both.

| quoted sentence | general rewording |
|---|---|
| "Clients authenticate and receive a token whose access-control policies name the paths that token may use. The same identity placeholders that fill policy paths also fill the allow-lists on certificate-issuing roles, so one written rule or role can adapt to who is calling." | "Identity data is substituted into administrator-written authorization configuration at use time; the rule below governs every decision that configuration produces." |
| "This holds wherever a substituted value is matched against something the caller supplies — a request path, or a name, identifier or host in a certificate request — and for every identity source (entity, alias and group names and metadata)." | "This holds wherever a substituted value is used as part of a pattern that a caller-supplied value is matched against, for every identity source." |
| "Pattern metacharacters here include the wildcards used when a path pattern is matched, the star used when a name, identifier or host pattern is matched, the separator that splits an allow-list into entries, and the path separator." | "A metacharacter is any character the matcher for the written pattern treats specially." |
| "A policy path that places a placeholder next to a literal wildcard, such as a trailing `*`, continues to match as it does now." | delete; covered by "Metacharacters written literally into ... configuration ... keep their present meaning." |
| "A certificate-role allow-list that is a literal glob written by an administrator continues to match exactly as it does now." | delete; same literal rule (already stated once). |
| "An allow-list entry that is a single literal star still means \"any\"." | delete; same literal rule. |
| "A default user or similar principal filled from identity data is still used when a role names one, and its rendered value is still re-checked against the allow-list afterwards." | "A value rendered from identity data that is only compared as a whole against an administrator-written entry, never used as part of a pattern, keeps working." |
| "Metacharacters written literally into a policy or role by an administrator keep their present meaning." | "Metacharacters written literally into administrator-written configuration keep their present meaning." (`role` also names the PKI/SSH object.) |

No instruction sentence names a file, function, the exact fix, or a flaw count.

## 4. Realism

Traps T1–T7 sit in unmodified upstream code. Injected S1 (SSH `allow_glob_domains` + `glob.Glob` in the host-principal check) is a straight port of PKI's flag; S2 (PKI `allowed_user_ids_template`) copies its two neighbouring template flags. Both are registered role fields reachable through the real `roles`/`issue`/`sign` entry points with `EntityID`. The PKI/SSH harnesses use the real `HandleRequest` + `StaticSystemView` seam; the ACL suite drives a real cluster over HTTP. Nothing is planted or contrived, and the "Observed problem" paragraph is the genuine report instance.

## Verdict

**READY (gate a).** All 21 security tests are covered by P1+P2+P3 read literally; all 20 functional tests by K1–K6; the visible project tests by STD. The primary-mechanism fix — reject the substituted value, with the sink's own metacharacter set, in the shared templating helper, wired from the ACL, PKI and SSH call sites — passes everything (`pass-alt-unconditional`, `pass-hardening`). No test requires a route name, a specific layer, one error class or one status. Residual judgment: P2's unqualified "path separator" could be read as a global block-list, over-blocking legitimate URI SANs such as `spiffe://d/users/alice` (`TestFunc_PKIUriTemplateLegit`); the correct reading is per-matcher, and the rewording above removes the ambiguity.

**Quality to tighten:** (1) add the SSH templated-`allowed_users` `*` security test; (2) assert refusal is an error response with no artifact, without demanding a status class; (3) apply the Section 3 rewordings; (4) consider resolving ACL setup errors (`t.Fatal` on metadata/name writes) as a refusal, since a write-time guard currently fails setup rather than scoring as a refusal.

Human review: confirm P2's "path separator" means a metacharacter of each matcher (not a global block-list), so the required rewording is applied and a global `/` block is not a defensible "correct" reading.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
