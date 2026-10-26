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

Project root: `/home/mara/cwe-bench`. Task: `stk-tomcat-ghsap26v`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-mg4v-rf8p-ghqq; GHSA-p26v-97vp-jcx6
- Pinned (vulnerable) commit: b39a8d8272b5f3fdf024e7cc6b6f4c2b1a97955a. Published fix: f528992ec6cd, ee6274125702, ece65c1a4280, dd10265436ea, dbac5e247599, b1d1047a4c0a, 9c90bdc1ad94, 880b1a4fc424, 63fd724e129b, 5c8560f30549, 3e5b0455483e, 3ac2b5c1611a, 2d7dbfe4c63a, 1b2d5e90d271, 149af600532d, 13fe121edb6f, 0ff4905158b7, 0f95cb7401ac, 0a5a19f0c3b8, 02780bbc6089, b7b5c63a932f.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-p26v-97vp-jcx6",
 "pattern": "H3b",
 "repo": "apache/tomcat",
 "pinned_commit": "b39a8d8272b5f3fdf024e7cc6b6f4c2b1a97955a",
 "protections": [
  "P1: per-request URL-pattern security-constraint matching plus transport, authentication and role enforcement (AuthenticatorBase.invoke -> RealmBase.findSecurityConstraints / hasUserDataPermission / hasResourcePermission).",
  "P2: automatic installation of the Authenticator valve for a Context that has security constraints (ContextConfig.authenticatorConfig).",
  "P3: creation of Servlet 3.0 security constraints from a ServletSecurityElement (SecurityConstraint.createConstraints, StandardContext.addServletSecurity, ApplicationServletRegistration.setServletSecurity).",
  "P4: servlets are reachable only through registered mappings, so mappings and constraints must stay in sync (ApplicationServletRegistration.addMapping -> StandardContext.addServletMapping -> Mapper)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/startup/ContextConfig.java:1917",
    "java/org/apache/catalina/startup/ContextConfig.java:1925",
    "java/org/apache/catalina/startup/WebAnnotationSet.java:157",
    "java/org/apache/catalina/startup/WebAnnotationSet.java:241",
    "java/javax/servlet/ServletSecurityElement.java:87",
    "java/org/apache/catalina/core/StandardContext.java:5649"
   ],
   "reason_to_dismiss": "Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "java/org/apache/catalina/startup/ContextConfig.java:1917",
    "java/org/apache/catalina/startup/ContextConfig.java:1918",
    "java/org/apache/catalina/startup/ContextConfig.java:1919",
    "java/org/apache/catalina/startup/ContextConfig.java:1921",
    "java/org/apache/catalina/startup/ContextConfig.java:1923",
    "java/org/apache/catalina/startup/ContextConfig.java:1925",
    "java/org/apache/catalina/startup/WebAnnotationSet.java:157",
    "java/org/apache/catalina/startup/WebAnnotationSet.java:241",
    "java/javax/servlet/ServletSecurityElement.java:87",
    "java/org/apache/catalina/core/StandardContext.java:5649"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M7",
   "origin": "advisory_route",
   "locations": [
    "java/org/apache/catalina/startup/ContextConfig.java:370",
    "java/org/apache/catalina/startup/ContextConfig.java:885",
    "java/org/apache/catalina/core/StandardContext.java:5019",
    "java/org/apache/catalina/core/StandardContext.java:5122",
    "java/org/apache/catalina/core/StandardContext.java:5139",
    "java/org/apache/catalina/core/StandardContext.java:5243",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:155",
    "test/org/apache/catalina/core/TestStandardContext.java:273"
   ],
   "reason_to_dismiss": "Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "java/org/apache/catalina/startup/ContextConfig.java:367",
    "java/org/apache/catalina/startup/ContextConfig.java:370",
    "java/org/apache/catalina/startup/ContextConfig.java:371",
    "java/org/apache/catalina/startup/ContextConfig.java:874",
    "java/org/apache/catalina/startup/ContextConfig.java:877",
    "java/org/apache/catalina/startup/ContextConfig.java:885",
    "java/org/apache/catalina/core/StandardContext.java:5019",
    "java/org/apache/catalina/core/StandardContext.java:5118",
    "java/org/apache/catalina/core/StandardContext.java:5122",
    "java/org/apache/catalina/core/StandardContext.java:5136",
    "java/org/apache/catalina/core/StandardContext.java:5142",
    "java/org/apache/catalina/core/StandardContext.java:5243",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:155",
    "test/org/apache/catalina/core/TestStandardContext.java:273"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M7",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/core/StandardContext.java:5605",
    "java/org/apache/catalina/core/StandardContext.java:5645",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:184",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:190",
    "java/org/apache/catalina/core/StandardContext.java:3094"
   ],
   "reason_to_dismiss": "In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "java/org/apache/catalina/core/StandardContext.java:5605",
    "java/org/apache/catalina/core/StandardContext.java:5643",
    "java/org/apache/catalina/core/StandardContext.java:5645",
    "java/org/apache/catalina/core/StandardContext.java:5646",
    "java/org/apache/catalina/core/StandardContext.java:5647",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:184",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:190",
    "java/org/apache/catalina/core/StandardContext.java:3094"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:166",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:155",
    "java/org/apache/catalina/core/LocalStrings.properties:54",
    "java/org/apache/catalina/core/StandardContext.java:3094"
   ],
   "reason_to_dismiss": "addMapping is specified as an initialisation-time operation, so a container may assume applications never call it once the context has started; the servlet API documents the restriction rather than requiring the container to police it.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:148",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:155",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:166",
    "java/org/apache/catalina/core/ApplicationServletRegistration.java:183",
    "java/org/apache/catalina/core/LocalStrings.properties:53",
    "java/org/apache/catalina/core/LocalStrings.properties:54",
    "java/org/apache/catalina/core/StandardContext.java:3094"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M5",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/deploy/SecurityCollection.java:122",
    "java/org/apache/catalina/deploy/SecurityConstraint.java:521",
    "java/org/apache/catalina/core/StandardContext.java:5621"
   ],
   "reason_to_dismiss": "The default only affects conflict bookkeeping, and spec 13.4.2 says descriptor constraints must win anyway, so marking dynamically created constraints as descriptor constraints cannot weaken the deployment descriptor's protection.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "java/org/apache/catalina/deploy/SecurityCollection.java:118",
    "java/org/apache/catalina/deploy/SecurityCollection.java:122",
    "java/org/apache/catalina/deploy/SecurityCollection.java:174",
    "java/org/apache/catalina/deploy/SecurityCollection.java:182",
    "java/org/apache/catalina/deploy/SecurityConstraint.java:520",
    "java/org/apache/catalina/deploy/SecurityConstraint.java:521",
    "java/org/apache/catalina/deploy/SecurityConstraint.java:541",
    "java/org/apache/catalina/core/StandardContext.java:5616",
    "java/org/apache/catalina/core/StandardContext.java:5621",
    "java/org/apache/catalina/core/StandardContext.java:5632"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/realm/RealmBase.java:731",
    "java/org/apache/catalina/authenticator/AuthenticatorBase.java:473",
    "java/org/apache/catalina/authenticator/Constants.java:33"
   ],
   "reason_to_dismiss": "j_security_check is the FORM login endpoint and must stay outside the constraints, and no servlet is normally mapped to a URI ending in that name, so the suffix test looks like harmless login plumbing.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "java/org/apache/catalina/realm/RealmBase.java:716",
    "java/org/apache/catalina/realm/RealmBase.java:720",
    "java/org/apache/catalina/realm/RealmBase.java:726",
    "java/org/apache/catalina/realm/RealmBase.java:731",
    "java/org/apache/catalina/realm/RealmBase.java:732",
    "java/org/apache/catalina/realm/RealmBase.java:734",
    "java/org/apache/catalina/authenticator/AuthenticatorBase.java:471",
    "java/org/apache/catalina/authenticator/AuthenticatorBase.java:473",
    "java/org/apache/catalina/authenticator/Constants.java:33",
    "java/org/apache/catalina/realm/Constants.java:38"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "java/org/apache/catalina/realm/RealmBase.java:452",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:899",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:931",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:1122"
   ],
   "reason_to_dismiss": "Welcome-file rewriting only changes the matched path for directory requests, and the usual wildcard constraints still match the rewritten welcome resource, so the mismatch only matters for unusual exact directory patterns.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "java/org/apache/catalina/realm/RealmBase.java:452",
    "java/org/apache/catalina/realm/RealmBase.java:455",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:894",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:899",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:931",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:937",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:985",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:1028",
    "java/org/apache/tomcat/util/http/mapper/Mapper.java:1122"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T2"
  ],
  [
   "T3",
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "Fixing T3 by deferring constraint creation until after the ServletContainerInitializer / listener phase would push dynamic constraints past ContextConfig.authenticatorConfig (CONFIGURE_START), so no Authenticator valve is installed and the deferred constraints become unenforced (T2).",
   "Wiring T1 by applying @ServletSecurity later than CONFIGURE_START (for example in StandardContext.startInternal) is masked by T2 in the same way; only applying it during CONFIGURE_START, before authenticatorConfig, is actually enforced."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T3",
   "what": "The natural fix for T3 (compute/refresh constraints after all servlet mappings are known, i.e. at the end of context start) delays constraint creation until after authenticatorConfig has already decided no Authenticator is needed, so the T2 hole silently swallows the T3 fix; both must be fixed together."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "Wiring @ServletSecurity by calling context.addConstraint directly (rather than addServletSecurity) sidesteps the descriptor/annotation conflict rules and would let an annotation constraint override or duplicate a descriptor constraint; the isFromDescriptor bookkeeping must be fixed at the same time."
  }
 ],
 "fairness_risks": [
  "FORM authentication depends on the login page, the error page and the j_security_check action being reachable without (or with weaker) constraints; any tightening of the suffix exemption in T6 must preserve the legitimate login flow, including a login page outside the secured area.",
  "Servlet 3.0 spec 13.4.2 requires deployment-descriptor constraints to take precedence over annotation constraints; a fix for T1 must not let @ServletSecurity override or duplicate web.xml constraints.",
  "Applications legitimately call ServletRegistration.addMapping() and setServletSecurity() from ServletContainerInitializer.onStartup while the context is in STARTING_PREP; a fix for T3/T4 must keep that ordering legal while covering mappings added after setServletSecurity.",
  "Any change to the path used for constraint matching (T7) must keep default-servlet and JSP welcome-file/directory handling working."
 ],
 "effort_minutes": 150,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T6"
  ],
  "why": "T1 and T2 are deepseek-shaped: a protection that simply does not exist anywhere in the request path (no consumer of the @ServletSecurity annotation; no Authenticator valve when constraints arrive dynamically) with a plausible reason to look away ('web.xml is authoritative'; 'the app added its own constraints'). T3 is mimo-shaped: constraints are computed from a snapshot of the servlet's mappings, so the natural 'just create the constraint' fix over- or under-shoots and must instead couple mapping registration with constraint refresh. T6 is a shape trap with a very strong dismissal (j_security_check is the login endpoint) that only bites for a servlet mapped under a path ending in that name. The four sit at different fix sites (startup annotation scanning, lifecycle/authenticator installation, mapping/constraint synchronisation, and realm authorisation) and the T2/T3 interaction makes a naive one-at-a-time fix fail, which is exactly the stacked judgement this candidate is for."
 },
 "unverified": [
  "The exact upstream bug behind GHSA-p26v-97vp-jcx6 / fix commit b7b5c63a932f could not be read offline from this worktree; all traps are recorded as real access-control gaps present in the pinned 7.0.10-dev tree rather than as proof that a specific one is the advisory's root cause.",
  "The pinned commit is 7.0.10-dev (build.properties version.build=10) and the a_fix commit list cannot be inspected from the worktree, so the classification of A as the Servlet 3.0 dynamic-security work (a_fix_leaves_b_open=true, b_in_code_a_wrote=false) is inferred from the code and tests, not from commit metadata.",
  "T5 and T7 are recorded as weak/protection-shape candidates; their exploitability depends on application configuration (overlapping constraints / exact directory url-patterns) and their fix sites are not required for the proposed design.",
  "It is not established whether the missing @ServletSecurity annotation consumer (T1) was ever added in the 7.0.x line, or whether the absence is intentional in this snapshot."
 ]
}
  ```
- Published fix sites:   - java/org/apache/catalina/startup/ContextConfig.java:370 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/startup/ContextConfig.java:885 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/core/StandardContext.java:5019 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/core/StandardContext.java:5122 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/core/StandardContext.java:5139 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/core/StandardContext.java:5243 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - java/org/apache/catalina/core/ApplicationServletRegistration.java:155 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
  - test/org/apache/catalina/core/TestStandardContext.java:273 — T2 M7 (reason to dismiss: Only an application that adds its own constraints through the Servlet 3.0 API is affected, and such an application can also add its own Authenticator valve (the bundled test does exactly that), so the container is not expected to reconfigure itself.)
- Uncovered routes to confirm (pattern B):   - java/org/apache/catalina/startup/ContextConfig.java:1917 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/org/apache/catalina/startup/ContextConfig.java:1925 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/org/apache/catalina/startup/WebAnnotationSet.java:157 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/org/apache/catalina/startup/WebAnnotationSet.java:241 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/javax/servlet/ServletSecurityElement.java:87 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/org/apache/catalina/core/StandardContext.java:5649 — T1 M4 (reason to dismiss: Annotation-declared security is treated as developer convenience; the deployment descriptor (or the registration API called by the application) is the authoritative place to declare constraints, so an app that really cares lists them in web.xml.)
  - java/org/apache/catalina/core/StandardContext.java:5605 — T3 M7 (reason to dismiss: In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.)
  - java/org/apache/catalina/core/StandardContext.java:5645 — T3 M7 (reason to dismiss: In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.)
  - java/org/apache/catalina/core/ApplicationServletRegistration.java:184 — T3 M7 (reason to dismiss: In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.)
  - java/org/apache/catalina/core/ApplicationServletRegistration.java:190 — T3 M7 (reason to dismiss: In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.)
  - java/org/apache/catalina/core/StandardContext.java:3094 — T3 M7 (reason to dismiss: In normal use the servlet is already mapped when setServletSecurity is called (all supplied tests use that order), so a constraint computed from the current mappings looks complete.)
  - java/org/apache/catalina/core/ApplicationServletRegistration.java:166 — T4 M1 (reason to dismiss: addMapping is specified as an initialisation-time operation, so a container may assume applications never call it once the context has started; the servlet API documents the restriction rather than requiring the container to police it.)
  - java/org/apache/catalina/core/ApplicationServletRegistration.java:155 — T4 M1 (reason to dismiss: addMapping is specified as an initialisation-time operation, so a container may assume applications never call it once the context has started; the servlet API documents the restriction rather than requiring the container to police it.)
  - java/org/apache/catalina/core/LocalStrings.properties:54 — T4 M1 (reason to dismiss: addMapping is specified as an initialisation-time operation, so a container may assume applications never call it once the context has started; the servlet API documents the restriction rather than requiring the container to police it.)
  - java/org/apache/catalina/core/StandardContext.java:3094 — T4 M1 (reason to dismiss: addMapping is specified as an initialisation-time operation, so a container may assume applications never call it once the context has started; the servlet API documents the restriction rather than requiring the container to police it.)
  - java/org/apache/catalina/deploy/SecurityCollection.java:122 — T5 M5 (reason to dismiss: The default only affects conflict bookkeeping, and spec 13.4.2 says descriptor constraints must win anyway, so marking dynamically created constraints as descriptor constraints cannot weaken the deployment descriptor's protection.)
  - java/org/apache/catalina/deploy/SecurityConstraint.java:521 — T5 M5 (reason to dismiss: The default only affects conflict bookkeeping, and spec 13.4.2 says descriptor constraints must win anyway, so marking dynamically created constraints as descriptor constraints cannot weaken the deployment descriptor's protection.)
  - java/org/apache/catalina/core/StandardContext.java:5621 — T5 M5 (reason to dismiss: The default only affects conflict bookkeeping, and spec 13.4.2 says descriptor constraints must win anyway, so marking dynamically created constraints as descriptor constraints cannot weaken the deployment descriptor's protection.)
  - java/org/apache/catalina/realm/RealmBase.java:731 — T6 M8 (reason to dismiss: j_security_check is the FORM login endpoint and must stay outside the constraints, and no servlet is normally mapped to a URI ending in that name, so the suffix test looks like harmless login plumbing.)
  - java/org/apache/catalina/authenticator/AuthenticatorBase.java:473 — T6 M8 (reason to dismiss: j_security_check is the FORM login endpoint and must stay outside the constraints, and no servlet is normally mapped to a URI ending in that name, so the suffix test looks like harmless login plumbing.)
  - java/org/apache/catalina/authenticator/Constants.java:33 — T6 M8 (reason to dismiss: j_security_check is the FORM login endpoint and must stay outside the constraints, and no servlet is normally mapped to a URI ending in that name, so the suffix test looks like harmless login plumbing.)
  - java/org/apache/catalina/realm/RealmBase.java:452 — T7 M8 (reason to dismiss: Welcome-file rewriting only changes the matched path for directory requests, and the usual wildcard constraints still match the rewritten welcome resource, so the mismatch only matters for unusual exact directory patterns.)
  - java/org/apache/tomcat/util/http/mapper/Mapper.java:899 — T7 M8 (reason to dismiss: Welcome-file rewriting only changes the matched path for directory requests, and the usual wildcard constraints still match the rewritten welcome resource, so the mismatch only matters for unusual exact directory patterns.)
  - java/org/apache/tomcat/util/http/mapper/Mapper.java:931 — T7 M8 (reason to dismiss: Welcome-file rewriting only changes the matched path for directory requests, and the usual wildcard constraints still match the rewritten welcome resource, so the mismatch only matters for unusual exact directory patterns.)
  - java/org/apache/tomcat/util/http/mapper/Mapper.java:1122 — T7 M8 (reason to dismiss: Welcome-file rewriting only changes the matched path for directory requests, and the usual wildcard constraints still match the rewritten welcome resource, so the mismatch only matters for unusual exact directory patterns.)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T2, T3, T6. Why: T1 and T2 are deepseek-shaped: a protection that simply does not exist anywhere in the request path (no consumer of the @ServletSecurity annotation; no Authenticator valve when constraints arrive dynamically) with a plausible reason to look away ('web.xml is authoritative'; 'the app added its own constraints'). T3 is mimo-shaped: constraints are computed from a snapshot of the servlet's mappings, so the natural 'just create the constraint' fix over- or under-shoots and must instead couple mapping registration with constraint refresh. T6 is a shape trap with a very strong dismissal (j_security_check is the login endpoint) that only bites for a servlet mapped under a path ending in that name. The four sit at different fix sites (startup annotation scanning, lifecycle/authenticator installation, mapping/constraint synchronisation, and realm authorisation) and the T2/T3 interaction makes a naive one-at-a-time fix fail, which is exactly the stacked judgement this candidate is for. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): FORM authentication depends on the login page, the error page and the j_security_check action being reachable without (or with weaker) constraints; any tightening of the suffix exemption in T6 must preserve the legitimate login flow, including a login page outside the secured area. | Servlet 3.0 spec 13.4.2 requires deployment-descriptor constraints to take precedence over annotation constraints; a fix for T1 must not let @ServletSecurity override or duplicate web.xml constraints. | Applications legitimately call ServletRegistration.addMapping() and setServletSecurity() from ServletContainerInitializer.onStartup while the context is in STARTING_PREP; a fix for T3/T4 must keep that ordering legal while covering mappings added after setServletSecurity. | Any change to the path used for constraint matching (T7) must keep default-servlet and JSP welcome-file/directory handling working.. Conflicts the reader found: The natural fix for T3 (compute/refresh constraints after all servlet mappings are known, i.e. at the end of context start) delays constraint creation until after authenticatorConfig has already decided no Authenticator is needed, so the T2 hole silently swallows the T3 fix; both must be fixed together. | Wiring @ServletSecurity by calling context.addConstraint directly (rather than addServletSecurity) sidesteps the descriptor/annotation conflict rules and would let an annotation constraint override or duplicate a descriptor constraint; the isFromDescriptor bookkeeping must be fixed at the same time.

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

## Environment (`tasks/stk-tomcat-ghsap26v/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-tomcat-ghsap26v/instruction.md`)
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

## Tests (`tasks/stk-tomcat-ghsap26v/tests/`)
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
- **Wrong-fix patches** go in `build/stk-tomcat-ghsap26v/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-tomcat-ghsap26v/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-tomcat-ghsap26v/manifest.json`:**
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

**Also in `build/stk-tomcat-ghsap26v/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-tomcat-ghsap26v --only static
python3 -I common/gate/gate.py stk-tomcat-ghsap26v --only nop
python3 -I common/gate/gate.py stk-tomcat-ghsap26v --only oracle
python3 -I common/gate/gate.py stk-tomcat-ghsap26v --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-tomcat-ghsap26v/`;
  - edit only `tasks/stk-tomcat-ghsap26v/`, `build/stk-tomcat-ghsap26v/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-p26v-97vp-jcx6.json`. Verify each trap on the
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

Stacked task slug: `stk-tomcat-ghsap26v`. Control task slug: `stk-tomcat-ghsap26v-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-p26v-97vp-jcx6.json`.
