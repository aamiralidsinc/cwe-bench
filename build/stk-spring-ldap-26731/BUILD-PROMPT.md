# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-spring-ldap-26731`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 26731; CWE-287 improper authentication (LDAP simple bind accepts a DN with an
- Pinned (vulnerable) commit: b207e5ef84270721bfc9a11dfc947a7ac1b3403d. Published fix: 30b90c9fb61af87208ed051fc31349ef4d418f75, 5cc73a6b7fb1d2bcb950c4d69221c6d192d79795, e2748d44bdce4f6cb4663b9b8d8462e34808f09c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-26731",
 "pattern": "H4",
 "repo": "spring-projects/spring-ldap",
 "pinned_commit": "b207e5ef84270721bfc9a11dfc947a7ac1b3403d",
 "protections": [
  "P1 At bind time, a non-blank principal with null or empty credentials must be refused before the pair reaches JNDI SECURITY_PRINCIPAL/SECURITY_CREDENTIALS, in every DirContextAuthenticationStrategy that sets credentials (Simple, Digest-MD5, DefaultTls) - not in the shared AbstractTlsDirContextAuthenticationStrategy hook or the shared AbstractContextSource.setupAuthenticatedEnvironment - while still allowing the blank-principal anonymous bind and credential-less EXTERNAL TLS auth.",
  "P2 (existing, partial) Config-time guards only: AbstractContextSource.afterPropertiesSet rejects a null password for the default AuthenticationSource but explicitly permits \"\", and ContextSourceParser requires a non-blank password XML attribute; neither guard ever sees the API-supplied or AuthenticationSource-supplied value at the moment the context is created."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "core/src/main/java/org/springframework/ldap/core/support/SimpleDirContextAuthenticationStrategy.java:42-46"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/core/support/SimpleDirContextAuthenticationStrategy.java:42-46 - setupEnvironment unconditionally does env.put(SECURITY_AUTHENTICATION, \"simple\"), env.put(SECURITY_PRINCIPAL, userDn), env.put(SECURITY_CREDENTIALS, password); no emptiness check on either value.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:127 - the default authenticationStrategy is new SimpleDirContextAuthenticationStrategy(), so this is the sink every ContextSource/LdapTemplate/LdapClient authentication reaches by default.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:145-162 - doGetContext builds the env via getAuthenticatedEnv then createContext(env); the only interception point for the env-borne strategies is setupAuthenticatedEnvironment (200-207).",
    "core/src/main/java/org/springframework/ldap/core/LdapTemplate.java:1354 - LdapTemplate.authenticate passes the caller-supplied password straight to contextSource.getContext(foundDn, password).",
    "core/src/main/java/org/springframework/ldap/core/DefaultLdapClient.java:478-480 - the fluent authenticate spec converts a never-supplied password to \"\" and calls getContext(foundDn, \"\"), the same sink.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:422-425 and 669-681 - userDn \"\" makes anonymousReadOnly the default and SimpleAuthenticationSource returns the blank userDn/password unchanged, so the coupled anonymous value must keep working."
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "core/src/main/java/org/springframework/ldap/core/support/DigestMd5DirContextAuthenticationStrategy.java:52-57"
   ],
   "reason_to_dismiss": "DIGEST-MD5 is a SASL challenge/response mechanism, so an empty password cannot produce a usable response and the server should reject the exchange anyway; the report names the default SIMPLE strategy.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/core/support/DigestMd5DirContextAuthenticationStrategy.java:52-57 - a near-verbatim copy of the Simple template (SECURITY_AUTHENTICATION=DIGEST-MD5, SECURITY_PRINCIPAL=userDn, SECURITY_CREDENTIALS=password) with no emptiness check.",
    "core/src/main/java/org/springframework/ldap/core/support/DirContextAuthenticationStrategy.java:38-78 - the interface has exactly two hooks and states no empty-credential rule, so the sibling strategy is the natural place for the same guard.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:644-646 - setAuthenticationStrategy lets an application wire this strategy instead of the default, so the fix site at T1 does not cover it."
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "core/src/main/java/org/springframework/ldap/core/support/DefaultTlsDirContextAuthenticationStrategy.java:38-45",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractTlsDirContextAuthenticationStrategy.java:131-143",
    "core/src/main/java/org/springframework/ldap/core/support/ExternalTlsDirContextAuthenticationStrategy.java:39-41"
   ],
   "reason_to_dismiss": "TLS strategies only run when the application wires one, and the obvious single fix in the shared AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation hook (or in AbstractContextSource.setupAuthenticatedEnvironment) looks like it covers every strategy at once.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/core/support/DefaultTlsDirContextAuthenticationStrategy.java:38-45 - credentials are applied post-creation with ctx.addToEnvironment(SECURITY_PRINCIPAL/CREDENTIALS) followed by ctx.lookup(\"\") to force the server call; no emptiness check before the addToEnvironment pair.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractTlsDirContextAuthenticationStrategy.java:119-122 - setupEnvironment is final and does nothing, so a fix written only against 'environment building' strategies never sees this route.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractTlsDirContextAuthenticationStrategy.java:131-143 - the final processContextAfterCreation negotiates TLS and then calls the abstract applyAuthentication hook shared with ExternalTls.",
    "core/src/main/java/org/springframework/ldap/core/support/ExternalTlsDirContextAuthenticationStrategy.java:39-41 - the sibling override deliberately authenticates with no password (EXTERNAL/client certificate), so the shared-hook guard that would close T1/T2/T3 in one edit breaks this must-keep-working value.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:154-155 - processContextAfterCreation is called for every context, including the EXTERNAL strategy."
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:169-177",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:567-569",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:571-578",
    "core/src/main/java/org/springframework/ldap/config/ContextSourceParser.java:210-213"
   ],
   "reason_to_dismiss": "These are raw JNDI properties supplied by the application through the documented base-env-props escape hatch, on the explicit anonymous-read-only branch; the library can reasonably say it does not interpret caller-supplied environment entries.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:567-569 - setBaseEnvironmentProperties stores the caller map verbatim as baseEnv.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:442-472 - setupAnonymousEnv copies baseEnv into the anonymous env and adds only provider url/factory, so a SECURITY_PRINCIPAL plus a blank SECURITY_CREDENTIALS survives untouched.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:169-177 - with anonymousReadOnly the read-only context is createContext(getAnonymousEnv()) and the authentication strategy is never called, so no strategy-level guard can fire.",
    "core/src/main/java/org/springframework/ldap/config/ContextSourceParser.java:210-213 - base-env-props-ref is a first-class XML configuration path to those raw properties.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:580-585 - getAuthenticatedEnv copies the anonymous env before the strategy overwrites the principal/credentials, which is why only the anonymousReadOnly branch reaches createContext unmodified."
   ]
  },
  {
   "id": "T5",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:246-260",
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:401-403"
   ],
   "reason_to_dismiss": "SchemaToJava is a developer code-generation CLI shipped in the odm module, not the ContextSource authentication API the advisory names, and it needs a live LDAP server to exercise.",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:246-260 - readSchema builds a raw JNDI Hashtable and puts SECURITY_PRINCIPAL only when user != null and SECURITY_CREDENTIALS only when pass != null, then calls new InitialDirContext(env); -u <dn> without -p produces exactly the principal-set/credentials-absent unauthenticated-bind shape.",
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:401-403 - main reads -u/-p with no default, so an absent password is null rather than \"\".",
    "odm/build.gradle:6-8 - this tool is the published jar's Main-Class, i.e. shipped code, not test scaffolding.",
    "odm/src/test/java/org/springframework/ldap/odm/test/SchemaToJavaTests.java:169-174 - the module's own test drives SchemaToJava.main with an embedded LDAP server, so the route is behaviourally reachable offline."
   ]
  },
  {
   "id": "T6",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaViewer.java:220-239"
   ],
   "reason_to_dismiss": "SchemaViewer is an operator-run schema inspection tool whose username and password deliberately default to \"\"; its own test invokes it with --username \"\" --password \"\", so the empty credential looks intended for anonymous reads.",
   "distance": {
    "files": 1,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaViewer.java:220-222 - url defaults to DEFAULT_URL and both username and password default to \"\".",
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaViewer.java:224-239 - SECURITY_PRINCIPAL is always put (user is never null) and SECURITY_CREDENTIALS is always put, then new InitialDirContext(env); -u <dn> without -p binds a DN with an empty credential.",
    "odm/src/main/java/org/springframework/ldap/odm/tools/SchemaViewer.java:230-236 - the tool checks the inverse direction only (a password requires a user), never that a user requires a password.",
    "odm/src/test/java/org/springframework/ldap/odm/test/SchemaViewerTests.java:59-60 - the existing test passes --username \"\" --password \"\", so any guard here must still allow a blank principal with a blank credential."
   ]
  },
  {
   "id": "T7",
   "mechanism": "M6",
   "origin": "injection_room",
   "locations": [
    "core/src/main/java/org/springframework/ldap/authentication/DefaultValuesAuthenticationSourceDecorator.java:78-103",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:669-681",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:103"
   ],
   "reason_to_dismiss": "The decorator is documented to substitute a non-privileged default principal for users who are not logged in and requires a non-null default password, so a blank credential supplied through it looks like deliberate configuration.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/authentication/DefaultValuesAuthenticationSourceDecorator.java:78-103 - getCredentials returns the target's credentials when the target principal has text and otherwise the configured defaultPassword, while getPrincipal returns defaultUser; nothing requires the pair to be non-blank together.",
    "core/src/main/java/org/springframework/ldap/authentication/DefaultValuesAuthenticationSourceDecorator.java:156-160 - afterPropertiesSet requires the default user and password to be non-null only.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:669-681 - SimpleAuthenticationSource feeds the field defaults straight into the strategy, so a check placed at the reported entry point (LdapTemplate.authenticate / LdapClient) never inspects this producer; getReadWriteContext reaches it directly.",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:103 - the password field default is \"\"."
   ]
  },
  {
   "id": "T8",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "core/src/main/java/org/springframework/ldap/core/DefaultLdapClient.java:456-459",
    "core/src/main/java/org/springframework/ldap/core/DefaultLdapClient.java:478-480",
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:426-432"
   ],
   "reason_to_dismiss": "The existing gh-538 guard already rejects a null password at configuration time, so a check copied from it tests only null and looks complete.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:426-432 - the existing guard is Assert.notNull(password) followed by a log line stating a blank password will be used; null is rejected, \"\" is explicitly blessed.",
    "core/src/test/java/org/springframework/ldap/core/support/LdapContextSourceTests.java:52-61 - gh-538 test proves a null password is rejected, giving a reviewer a false sense that this area is guarded.",
    "core/src/main/java/org/springframework/ldap/core/DefaultLdapClient.java:456-459 - AuthenticateSpec.password requires a non-null String, so the only way to reach 478 with no password is to never call password().",
    "core/src/main/java/org/springframework/ldap/core/DefaultLdapClient.java:478-480 - a null password is normalised to \"\" before getContext, so any guard placed above this line that tests only null is bypassed by ldapClient.authenticate().query(q).execute()."
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T7",
   "T8"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "gh-538 added the null-password rejection at AbstractContextSource:426-432 and, in the same block, an explicit log line 'Property password not set - blank password will be used' plus an Assert message telling users to set \"\" for a blank password; the earlier fix therefore documents the later bug as supported behaviour.",
   "ContextSourceParser:204-207 already refuses a blank password XML attribute, so the configuration layer looks protected while the programmatic/API path (field default \"\" at AbstractContextSource:103, AuthenticationSource producers) is not.",
   "LdapTemplateTests:1801-1839 call authenticate(query, \"\") in the existing core suite, but the mocked search returns no results so those tests never reach the bind and give false assurance that the empty-password path is covered.",
   "The existing strategy tests only exercise non-blank values (SimpleDirContextAuthenticationStrategyTests:38-45 with \"cn=John Doe\"/\"pw\", DefaultTlsDirContextAuthenticationStrategyTests:44-49 with \"username\"/\"password\"), so no test pins the empty-credential behaviour."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "The one-edit shared-layer fix that would close T1/T2/T3 together (a guard in AbstractContextSource.setupAuthenticatedEnvironment or in AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation) also rejects ExternalTlsDirContextAuthenticationStrategy's credential-less EXTERNAL bind (ExternalTlsDirContextAuthenticationStrategy.java:39-41) for any context source that carries a non-blank configured principal, so the guard has to be written per strategy in the three concrete classes."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "An unconditional 'reject blank credentials' rule in SimpleDirContextAuthenticationStrategy also refuses the blank-principal anonymous bind: SchemaToJavaTests sets userDn \"\" and password \"\" (SchemaToJavaTests.java:112-120) and LdapTestUtils reaches getReadWriteContext (LdapTestUtils.java:161,225), so the guard must be conditioned on a non-blank principal."
  },
  {
   "a": "T5",
   "b": "T6",
   "what": "A shared 'a -u requires a -p' helper in the two ODM tools breaks SchemaViewer's anonymous invocation with --username \"\" --password \"\" (SchemaViewerTests.java:59-60) unless it is conditioned on a non-blank username."
  }
 ],
 "fairness_risks": [
  "Anonymous simple bind must keep working: a blank principal with a blank or absent credential is a documented mode (AbstractContextSource:422-425 turns on anonymousReadOnly when userDn is blank) and is exercised in-repo by SchemaToJavaTests:112-120 through LdapTestUtils:161/225, so a guard that rejects every blank credential breaks existing tests and a legitimate configuration.",
  "EXTERNAL TLS authentication legitimately carries no password (ExternalTlsDirContextAuthenticationStrategy.java:39-41); a rule placed in the shared TLS hook or in setupAuthenticatedEnvironment breaks certificate-based auth for any context source whose AuthenticationSource also supplies a principal.",
  "The two configuration paths disagree: AbstractContextSource:426-432 explicitly supports a blank password ('To use a blank password, please ensure it is set to \"\"') while ContextSourceParser:204-207 rejects a blank password attribute. Rejecting a blank credential at configuration time will break programmatic callers that rely on the documented blank-password allowance even though the XML path already forbids it.",
  "The authenticate contract must not change shape: LdapTemplate:1361-1364 swallows any Exception into AuthenticationStatus.UNDEFINED_FAILURE, while the LdapQuery overload at LdapTemplate:1380-1395 rethrows NamingException as org.springframework.ldap.AuthenticationException and anything else as UncategorizedLdapException; the existing integration expectation (LdapTemplateAuthenticationITests:127-139) is that a failed bind surfaces as AuthenticationException, so an IllegalArgumentException-style guard changes observable behaviour.",
  "Refusing a non-blank principal with no credential also refuses setups where the credential is supplied out of band (client certificate, SASL EXTERNAL, proxy auth) if the guard is applied above the strategy rather than inside the mechanism-specific class."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Five independently editable sites with five different dismissal arguments and a clear distance ladder: T1 is the reported default strategy (easy, and it is the funnel for T7/T8 because one guard there also closes the LdapTemplate.authenticate, LdapClient.authenticate, getReadWriteContext and AuthenticationSource producers), T2 is the near-verbatim sibling that models skip ('DIGEST-MD5 needs a password anyway'), T3 is the post-creation/TLS sink where the natural one-edit fix in the shared abstract hook demonstrably breaks EXTERNAL (the mimo over-hardening trap, and the reason the three strategies cannot be collapsed into one guard), T4 is an absent-protection route with a strong reason to dismiss (raw caller-supplied base env on the anonymousReadOnly branch, unreachable from any strategy guard) and T5 is a second raw-JNDI implementation in another module that the authentication API never touches. The set spans core/support, core/core, core/authentication and odm/tools (three packages, five files, two modules) so no single grep-and-patch closes it, it contains at least one deepseek-type (T4, T5) and one mimo-type (T3 coupled with EXTERNAL), and it forces the solver to state the anonymous-bind and EXTERNAL exceptions explicitly. T6 is a good optional sixth (same dismiss as T5 but its own fix site); T7 and T8 are better used as hidden-test drivers for T1 than as separate traps because the strategy guard subsumes them."
 },
 "unverified": [
  "The three fix commits listed in the screener record are not present in this worktree (HEAD is b207e5ef) and no shell was available, so the origin labels published_fix_far_site versus uncovered_upstream are inferred from the screener's fix_sites/O8 lists rather than read from the patches.",
  "Whether the JDK LDAP provider actually completes an unauthenticated bind for SECURITY_AUTHENTICATION=DIGEST-MD5 with an empty SECURITY_CREDENTIALS was not verified against a server; T2 is recorded as a missing behavioural guard, not as a proven bypass.",
  "Whether DefaultTlsDirContextAuthenticationStrategy can be exercised end-to-end offline (real StartTLS against UnboundID) was not verified; core already has unboundid-ldapsdk as a test dependency (core/build.gradle:40) and a mock-based applyAuthentication test exists (DefaultTlsDirContextAuthenticationStrategyTests:44-49).",
  "Whether the benchmark's expected fix includes the base-environment route (T4): the screener's fix_sites list does not include AbstractContextSource, so T4 would be a defence-in-depth judgement not mandated by the upstream patch and would need a deliberately authored hidden test.",
  "The exact exception type the hidden tests expect for a refused bind (javax.naming.AuthenticationException versus IllegalArgumentException) is unknown; it changes what LdapTemplate.authenticate and its LdapQuery overload report.",
  "Repository size in MB was not measured (no shell access in this session)."
 ]
}
  ```
- Published fix sites:   - core/src/main/java/org/springframework/ldap/core/support/SimpleDirContextAuthenticationStrategy.java:42-46 — T1 M4 (reason to dismiss: none)
  - core/src/main/java/org/springframework/ldap/core/support/DigestMd5DirContextAuthenticationStrategy.java:52-57 — T2 M2 (reason to dismiss: DIGEST-MD5 is a SASL challenge/response mechanism, so an empty password cannot produce a usable response and the server should reject the exchange anyway; the report names the default SIMPLE strategy.)
  - core/src/main/java/org/springframework/ldap/core/support/DefaultTlsDirContextAuthenticationStrategy.java:38-45 — T3 M11 (reason to dismiss: TLS strategies only run when the application wires one, and the obvious single fix in the shared AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation hook (or in AbstractContextSource.setupAuthenticatedEnvironment) looks like it covers every strategy at once.)
  - core/src/main/java/org/springframework/ldap/core/support/AbstractTlsDirContextAuthenticationStrategy.java:131-143 — T3 M11 (reason to dismiss: TLS strategies only run when the application wires one, and the obvious single fix in the shared AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation hook (or in AbstractContextSource.setupAuthenticatedEnvironment) looks like it covers every strategy at once.)
  - core/src/main/java/org/springframework/ldap/core/support/ExternalTlsDirContextAuthenticationStrategy.java:39-41 — T3 M11 (reason to dismiss: TLS strategies only run when the application wires one, and the obvious single fix in the shared AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation hook (or in AbstractContextSource.setupAuthenticatedEnvironment) looks like it covers every strategy at once.)
- Uncovered routes to confirm (pattern B):   - core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:169-177 — T4 M4 (reason to dismiss: These are raw JNDI properties supplied by the application through the documented base-env-props escape hatch, on the explicit anonymous-read-only branch; the library can reasonably say it does not interpret caller-supplied environment entries.)
  - core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:567-569 — T4 M4 (reason to dismiss: These are raw JNDI properties supplied by the application through the documented base-env-props escape hatch, on the explicit anonymous-read-only branch; the library can reasonably say it does not interpret caller-supplied environment entries.)
  - core/src/main/java/org/springframework/ldap/core/support/AbstractContextSource.java:571-578 — T4 M4 (reason to dismiss: These are raw JNDI properties supplied by the application through the documented base-env-props escape hatch, on the explicit anonymous-read-only branch; the library can reasonably say it does not interpret caller-supplied environment entries.)
  - core/src/main/java/org/springframework/ldap/config/ContextSourceParser.java:210-213 — T4 M4 (reason to dismiss: These are raw JNDI properties supplied by the application through the documented base-env-props escape hatch, on the explicit anonymous-read-only branch; the library can reasonably say it does not interpret caller-supplied environment entries.)
  - odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:246-260 — T5 M2 (reason to dismiss: SchemaToJava is a developer code-generation CLI shipped in the odm module, not the ContextSource authentication API the advisory names, and it needs a live LDAP server to exercise.)
  - odm/src/main/java/org/springframework/ldap/odm/tools/SchemaToJava.java:401-403 — T5 M2 (reason to dismiss: SchemaToJava is a developer code-generation CLI shipped in the odm module, not the ContextSource authentication API the advisory names, and it needs a live LDAP server to exercise.)
  - odm/src/main/java/org/springframework/ldap/odm/tools/SchemaViewer.java:220-239 — T6 M2 (reason to dismiss: SchemaViewer is an operator-run schema inspection tool whose username and password deliberately default to ""; its own test invokes it with --username "" --password "", so the empty credential looks intended for anonymous reads.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Five independently editable sites with five different dismissal arguments and a clear distance ladder: T1 is the reported default strategy (easy, and it is the funnel for T7/T8 because one guard there also closes the LdapTemplate.authenticate, LdapClient.authenticate, getReadWriteContext and AuthenticationSource producers), T2 is the near-verbatim sibling that models skip ('DIGEST-MD5 needs a password anyway'), T3 is the post-creation/TLS sink where the natural one-edit fix in the shared abstract hook demonstrably breaks EXTERNAL (the mimo over-hardening trap, and the reason the three strategies cannot be collapsed into one guard), T4 is an absent-protection route with a strong reason to dismiss (raw caller-supplied base env on the anonymousReadOnly branch, unreachable from any strategy guard) and T5 is a second raw-JNDI implementation in another module that the authentication API never touches. The set spans core/support, core/core, core/authentication and odm/tools (three packages, five files, two modules) so no single grep-and-patch closes it, it contains at least one deepseek-type (T4, T5) and one mimo-type (T3 coupled with EXTERNAL), and it forces the solver to state the anonymous-bind and EXTERNAL exceptions explicitly. T6 is a good optional sixth (same dismiss as T5 but its own fix site); T7 and T8 are better used as hidden-test drivers for T1 than as separate traps because the strategy guard subsumes them. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Anonymous simple bind must keep working: a blank principal with a blank or absent credential is a documented mode (AbstractContextSource:422-425 turns on anonymousReadOnly when userDn is blank) and is exercised in-repo by SchemaToJavaTests:112-120 through LdapTestUtils:161/225, so a guard that rejects every blank credential breaks existing tests and a legitimate configuration. | EXTERNAL TLS authentication legitimately carries no password (ExternalTlsDirContextAuthenticationStrategy.java:39-41); a rule placed in the shared TLS hook or in setupAuthenticatedEnvironment breaks certificate-based auth for any context source whose AuthenticationSource also supplies a principal. | The two configuration paths disagree: AbstractContextSource:426-432 explicitly supports a blank password ('To use a blank password, please ensure it is set to ""') while ContextSourceParser:204-207 rejects a blank password attribute. Rejecting a blank credential at configuration time will break programmatic callers that rely on the documented blank-password allowance even though the XML path already forbids it. | The authenticate contract must not change shape: LdapTemplate:1361-1364 swallows any Exception into AuthenticationStatus.UNDEFINED_FAILURE, while the LdapQuery overload at LdapTemplate:1380-1395 rethrows NamingException as org.springframework.ldap.AuthenticationException and anything else as UncategorizedLdapException; the existing integration expectation (LdapTemplateAuthenticationITests:127-139) is that a failed bind surfaces as AuthenticationException, so an IllegalArgumentException-style guard changes observable behaviour. | Refusing a non-blank principal with no credential also refuses setups where the credential is supplied out of band (client certificate, SASL EXTERNAL, proxy auth) if the guard is applied above the strategy rather than inside the mechanism-specific class.. Conflicts the reader found: The one-edit shared-layer fix that would close T1/T2/T3 together (a guard in AbstractContextSource.setupAuthenticatedEnvironment or in AbstractTlsDirContextAuthenticationStrategy.processContextAfterCreation) also rejects ExternalTlsDirContextAuthenticationStrategy's credential-less EXTERNAL bind (ExternalTlsDirContextAuthenticationStrategy.java:39-41) for any context source that carries a non-blank configured principal, so the guard has to be written per strategy in the three concrete classes. | An unconditional 'reject blank credentials' rule in SimpleDirContextAuthenticationStrategy also refuses the blank-principal anonymous bind: SchemaToJavaTests sets userDn "" and password "" (SchemaToJavaTests.java:112-120) and LdapTestUtils reaches getReadWriteContext (LdapTestUtils.java:161,225), so the guard must be conditioned on a non-blank principal. | A shared 'a -u requires a -p' helper in the two ODM tools breaks SchemaViewer's anonymous invocation with --username "" --password "" (SchemaViewerTests.java:59-60) unless it is conditioned on a non-blank username.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-spring-ldap-26731/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-spring-ldap-26731/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-spring-ldap-26731/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-spring-ldap-26731/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-spring-ldap-26731/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-spring-ldap-26731/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-spring-ldap-26731/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-spring-ldap-26731 --only static
python3 -I common/gate/gate.py stk-spring-ldap-26731 --only nop
python3 -I common/gate/gate.py stk-spring-ldap-26731 --only oracle
python3 -I common/gate/gate.py stk-spring-ldap-26731 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-spring-ldap-26731/`;
  - edit only `tasks/stk-spring-ldap-26731/`, `build/stk-spring-ldap-26731/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-26731.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-spring-ldap-26731`. Control task slug: `stk-spring-ldap-26731-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-26731.json`.
