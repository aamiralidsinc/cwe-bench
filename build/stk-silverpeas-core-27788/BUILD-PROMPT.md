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

Project root: `/home/mara/cwe-bench`. Task: `stk-silverpeas-core-27788`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 27788; path traversal / arbitrary file read (CWE-36 absolute path traversal) 
- Pinned (vulnerable) commit: b1d65df25a0b8f0e3fde7fa5b57452eadffc644c. Published fix: caa6e6d1ac967ebd29b39e11c2ef5e7fd0047eec.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-27788",
 "pattern": "H4",
 "repo": "silverpeas/silverpeas-core",
 "pinned_commit": "b1d65df25a0b8f0e3fde7fa5b57452eadffc644c",
 "protections": [
  "Only an authenticated user who supplies a defined ComponentId they are entitled to (member of the component, or non-member of a publicFiles=yes storage component) may receive a file from FileServer (core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:80-91, FileServer.java:148-164).",
  "The path that is finally opened must resolve inside the directory the request is entitled to (component upload repository, temporary repository, or a server-chosen attachment path), never to an arbitrary absolute path and never through '..' segments (FileServer.java:108-134, core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileProvider.java:202-216).",
  "Every file-serving servlet authenticates the caller and authorises the addressed component or document before streaming bytes (FileServer.java:84; core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:51, 77-79; contrast core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:58-99, which has neither).",
  "Server-side scanners that turn FileServer URLs into DataSources must not resolve files the scanned content's author is not entitled to (FileServer.java:178-191)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:80",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:84",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:148-164",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:150-152"
   ],
   "reason_to_dismiss": "The allow-branch is commented 'Personal space', so a request without ComponentId reads as a deliberate, supported personal-space access rather than as a missing check; and the framework's own controller also authorises a null componentId, so 'use the standard access controller' looks like a complete fix.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:80",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:84",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:150-152",
    "core-library/src/main/java/org/silverpeas/core/security/authorization/ComponentAccessController.java:145-149",
    "core-library/src/test/java/org/silverpeas/core/security/authorization/ComponentAccessControllerTest.java:247-249"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:112",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:113-117",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:120-121",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:123-131",
    "core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileProvider.java:202-216",
    "core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileDescriptor.java:145-151",
    "core-library/src/main/java/org/silverpeas/core/util/file/FileRepositoryManager.java:105-107"
   ],
   "reason_to_dismiss": "Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:113-117",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:120-121",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:123-127",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:129-131",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:133",
    "core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileProvider.java:204-212",
    "core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileDescriptor.java:145-151",
    "core-library/src/main/java/org/silverpeas/core/util/file/FileRepositoryManager.java:105-107"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:58-99",
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:62-68",
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:93-96",
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:98-99",
    "core-war/src/main/webapp/WEB-INF/web.xml:768-771"
   ],
   "reason_to_dismiss": "It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:47",
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:62-68",
    "core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:93-99",
    "core-web/src/main/java/org/silverpeas/core/web/mvc/AbstractFileSender.java:45",
    "core-web/src/main/java/org/silverpeas/core/web/mvc/webcomponent/SilverpeasAuthenticatedHttpServlet.java:60-73",
    "core-war/src/main/webapp/WEB-INF/web.xml:1214-1235"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:67-89",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:77-79",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:81-82",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:101-103"
   ],
   "reason_to_dismiss": "The servlet already carries an explicit security check named isValid() and requires an authenticated session through SilverpeasAuthenticatedHttpServlet, so it presents as the one sibling that already did the job; the check is in fact a two-substring test that never looks at path traversal.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:51",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:67",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:81-82",
    "core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:101-103",
    "core-web/src/main/java/org/silverpeas/core/web/mvc/webcomponent/SilverpeasAuthenticatedHttpServlet.java:60-73"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:154-157",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:159-160"
   ],
   "reason_to_dismiss": "Nothing looks missing here: publicFiles=yes is a documented per-component file-storage mode, so the branch reads as a feature to keep. The over-hardening trap is that the obvious repair of the access-control gap (route every request through isComponentAvailableToUser, line 159-160, or replace isUserAllowed wholesale) deletes this branch and silently denies every non-member of a storage component.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "bypassed",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:154-157",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:159-160",
    "core-library/src/main/java/org/silverpeas/core/security/authorization/DefaultInstanceAccessControlExtension.java:72-74",
    "core-library/src/test/java/org/silverpeas/core/security/authorization/ComponentAccessControllerTest.java:176-177",
    "core-library/src/test/java/org/silverpeas/core/security/authorization/ComponentAccessControllerTest.java:255-257"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:178-191",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:184-185",
    "core-library/src/main/java/org/silverpeas/core/contribution/content/wysiwyg/service/process/MailContentProcess.java:85-96"
   ],
   "reason_to_dismiss": "It is a programmatic content scanner, not a user-facing HTTP route: it processes WYSIWYG HTML already authored inside the application during mail generation, so the parameters look like app-generated links and the absence of any session, ComponentId or access check goes unnoticed.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:179-191",
    "core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:184-185",
    "core-library/src/main/java/org/silverpeas/core/contribution/content/wysiwyg/service/process/MailContentProcess.java:85-96"
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
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T2 is only reachable on FileServer once T1's gate is passed: the undefined-ComponentId allow (FileServer.java:150-152) and the unconfined path resolution (FileServer.java:120-121, 129-131 -> SilverpeasFileProvider.java:208-212) must both hold, so repairing T1 alone leaves the absolute-path and '..' reads available to any user who can name a component they may access (every public / publicFiles component).",
   "Once the TypeUpload absolute branch is removed, '..' segments in Directory/Size/SourceFile (FileServer.java:113-117, 129-131) and the DirType=temporary branch (FileServer.java:123-127) become the remaining ways out of the entitled directory, i.e. the relative shape only becomes visible after the absolute shape is fixed.",
   "T3 and T4 are only reachable as separate code paths because neither shares a guard with FileServer; a fix written only inside FileServer.getSilverpeasFile cannot mask them."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "The natural repair of the missing-ComponentId gap is to route everything through isComponentAvailableToUser (FileServer.java:159-160) or to delegate to ComponentAccessController; applied unconditionally it denies the publicFiles=yes storage components that must remain downloadable by any logged-in non-member (FileServer.java:154-157, DefaultInstanceAccessControlExtension.java:72-74, ComponentAccessControllerTest.java:176-177)."
  },
  {
   "a": "T2",
   "b": "T3",
   "what": "Closing the path-containment gap in the shared provider (SilverpeasFileProvider.java:202-216) by forbidding absolute descriptors breaks the legitimate absolute attachment paths OnlineFileServer.java:76-91 depends on, so the containment rule cannot simply live in the shared layer; it has to be per call-site, which is what keeps T2 and T3 independent."
  },
  {
   "a": "T2",
   "b": "T4",
   "what": "A single 'resolved path must start with the uploads repository' rule reused by TempFileServer breaks that servlet's legitimate files, which live under the temporary repository joined at TempFileServer.java:81-82, not under the component upload path."
  }
 ],
 "fairness_risks": [
  "publicFiles=yes legitimately lets any logged-in user who is NOT a member of the storage component download its files (FileServer.java:154-157); a security rule of the form 'require membership of the component' contradicts a documented behaviour and would fail a must-keep-working test.",
  "Absolute path descriptors are legitimate for attachments: OnlineFileServer.java:76-91 and core-war/src/main/java/org/silverpeas/web/servlets/RestOnlineFileServer.java:167-173 deliberately build them from database rows; a blanket ban on absolute paths in SilverpeasFileProvider refuses an input shape a legitimate use needs.",
  "The Size parameter is a legitimate resized-image directory marker produced by FileServerUtils.getImageURL (FileServerUtils.java:193-197) and used for thumbnails; rejecting every Size value, rather than validating/normalising it, breaks thumbnail serving.",
  "TempFileServer must keep serving nested and non-ASCII names under the temporary repository (core-library/src/test/java/org/silverpeas/core/util/FileServerUtilsTest.java:62-67); a rule that forbids path separators outright, rather than traversal, would break it.",
  "Requiring a defined ComponentId refuses requests that the pinned code serves as 'Personal space' (FileServer.java:150-152); that is the published intent, but any hidden test that still expects a personal-space URL without ComponentId to work would contradict the security rule."
 ],
 "effort_minutes": 200,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Five independent judgements at five different fix sites with five different reasons to leave them alone: (T1) the undefined-ComponentId allow, which is dismissed as an intentional 'Personal space' feature and which even the framework controller (ComponentAccessController.java:145-149) would keep; (T2) no containment of the resolved path at all, dismissed because a caller with a ComponentId is already authorised and because TypeUpload/DirType look like internal URL-builder flags; (T3) a sibling servlet in the same package that reaches the same SilverpeasFileProvider sink with no authentication, no component authorisation and no path validation, dismissed as 'the legacy servlet, not the one the report names'; (T4) a sibling servlet that presents as already protected because it has isValid() and a session, but whose check is a two-substring test that never looks at '..'; and (T5) the coupled publicFiles=yes storage mode that the natural over-broad access-control repair destroys. That gives four deepseek-type traps (protection absent, each with its own dismissal) and one mimo-type coupled value (T5), spread over FileServer.java, TempFileServer.java, OnlineFileServer.java and the shared SilverpeasFileProvider/descriptor pair, so no single guard closes more than one. T6 (the ImageUrlToDataSourceScanner, which resolves FileServer parameters into mail attachments with no access check) is a good optional sixth when the harness can drive MailContentProcess, but it is same-file and mail-generation-bound, so it adds less than T3/T4 and risks an unfair test surface. T2 deliberately folds the absolute-path (TypeUpload), the temporary-repository (DirType) and the '..' (Directory/Size/SourceFile) shapes into one trap because a single containment guard at FileServer.getSilverpeasFile closes all three; splitting them would inflate the count."
 },
 "unverified": [
  "The published fix diff (fix.diff, fix commits caa6e6d1ac967ebd29b39e11c2ef5e7fd0047eec) is not present in this worktree, so every statement about what the published fix does or does not touch comes from the screener record and not from pinned-code evidence.",
  "Git history could not be inspected (no shell in this session), so the H3 fields (a_fix_leaves_b_open, b_in_code_a_wrote) are left null; the recent commits b1d65df25a..9912ffd2fb all read 'Fix bug #1522x' and one of them (Commit for #15225) touched MassiveWebSecurityFilter only, but that was not verified against the tree.",
  "Whether a '..' sequence survives to TempFileServer.getPathInfo depends on servlet-container URI normalisation (a real container may reject or collapse it before mapping); a mock-based doGet test with a crafted getPathInfo() would exercise it, but no runtime was attempted.",
  "It was not executed that OnlineFileServer is reachable without a session end-to-end; the claim rests on it extending AbstractFileSender (a plain HttpServlet), on core-war/src/main/webapp/WEB-INF/web.xml having no auth filter/security-constraint for /OnlineFileServer/* (web.xml:768-771, 1214-1235), and on the contrast with SilverpeasAuthenticatedHttpServlet.service (:60-73).",
  "Exploitability of the RestOnlineFileServer 'size' prefix (core-war/src/main/java/org/silverpeas/web/servlets/RestOnlineFileServer.java:129-131, 155-157) was considered and judged not to yield an arbitrary read because the appended attachment path is fixed, so it was not recorded as a trap; this was reasoned from the code, not run.",
  "The build and the module layout were not exercised (no shell); the Maven multi-module description and the offline behaviour come from the screener, not from a build in this session.",
  "present_in_latest is unknown for every trap: no later source tree was supplied."
 ]
}
  ```
- Published fix sites:   - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:80 — T1 M4 (reason to dismiss: The allow-branch is commented 'Personal space', so a request without ComponentId reads as a deliberate, supported personal-space access rather than as a missing check; and the framework's own controller also authorises a null componentId, so 'use the standard access controller' looks like a complete fix.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:84 — T1 M4 (reason to dismiss: The allow-branch is commented 'Personal space', so a request without ComponentId reads as a deliberate, supported personal-space access rather than as a missing check; and the framework's own controller also authorises a null componentId, so 'use the standard access controller' looks like a complete fix.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:148-164 — T1 M4 (reason to dismiss: The allow-branch is commented 'Personal space', so a request without ComponentId reads as a deliberate, supported personal-space access rather than as a missing check; and the framework's own controller also authorises a null componentId, so 'use the standard access controller' looks like a complete fix.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:150-152 — T1 M4 (reason to dismiss: The allow-branch is commented 'Personal space', so a request without ComponentId reads as a deliberate, supported personal-space access rather than as a missing check; and the framework's own controller also authorises a null componentId, so 'use the standard access controller' looks like a complete fix.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:112 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:113-117 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:120-121 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:123-131 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileProvider.java:202-216 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-library/src/main/java/org/silverpeas/core/io/file/SilverpeasFileDescriptor.java:145-151 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-library/src/main/java/org/silverpeas/core/util/file/FileRepositoryManager.java:105-107 — T2 M4 (reason to dismiss: Once a ComponentId the caller may access is present the remaining path is treated as trusted data written by the application, and TypeUpload/DirType/Directory look like internal flags of the shipped URL builders (core-library/src/main/java/org/silverpeas/core/util/file/FileServerUtils.java:117-153, FileServerUtils.java:240-246); the advisory reads as the missing-ComponentId case rather than as a missing containment check. Sharing a guard with T4 also looks tempting because one 'path resolved under the repository' rule appears to cover both.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:154-157 — T5 M11 (reason to dismiss: Nothing looks missing here: publicFiles=yes is a documented per-component file-storage mode, so the branch reads as a feature to keep. The over-hardening trap is that the obvious repair of the access-control gap (route every request through isComponentAvailableToUser, line 159-160, or replace isUserAllowed wholesale) deletes this branch and silently denies every non-member of a storage component.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:159-160 — T5 M11 (reason to dismiss: Nothing looks missing here: publicFiles=yes is a documented per-component file-storage mode, so the branch reads as a feature to keep. The over-hardening trap is that the obvious repair of the access-control gap (route every request through isComponentAvailableToUser, line 159-160, or replace isUserAllowed wholesale) deletes this branch and silently denies every non-member of a storage component.)
- Uncovered routes to confirm (pattern B):   - core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:58-99 — T3 M1 (reason to dismiss: It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.)
  - core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:62-68 — T3 M1 (reason to dismiss: It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.)
  - core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:93-96 — T3 M1 (reason to dismiss: It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.)
  - core-war/src/main/java/org/silverpeas/web/servlets/OnlineFileServer.java:98-99 — T3 M1 (reason to dismiss: It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.)
  - core-war/src/main/webapp/WEB-INF/web.xml:768-771 — T3 M1 (reason to dismiss: It is the legacy inline-media servlet, not the FileServer servlet the report names, and its documentId/attachmentId branches look like the only interesting ones; the fallback branch (line 93-96) reaches the same SilverpeasFileProvider sink with no session check, no component authorisation and no path validation at all.)
  - core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:67-89 — T4 M8 (reason to dismiss: The servlet already carries an explicit security check named isValid() and requires an authenticated session through SilverpeasAuthenticatedHttpServlet, so it presents as the one sibling that already did the job; the check is in fact a two-substring test that never looks at path traversal.)
  - core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:77-79 — T4 M8 (reason to dismiss: The servlet already carries an explicit security check named isValid() and requires an authenticated session through SilverpeasAuthenticatedHttpServlet, so it presents as the one sibling that already did the job; the check is in fact a two-substring test that never looks at path traversal.)
  - core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:81-82 — T4 M8 (reason to dismiss: The servlet already carries an explicit security check named isValid() and requires an authenticated session through SilverpeasAuthenticatedHttpServlet, so it presents as the one sibling that already did the job; the check is in fact a two-substring test that never looks at path traversal.)
  - core-war/src/main/java/org/silverpeas/web/servlets/TempFileServer.java:101-103 — T4 M8 (reason to dismiss: The servlet already carries an explicit security check named isValid() and requires an authenticated session through SilverpeasAuthenticatedHttpServlet, so it presents as the one sibling that already did the job; the check is in fact a two-substring test that never looks at path traversal.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:178-191 — T6 M1 (reason to dismiss: It is a programmatic content scanner, not a user-facing HTTP route: it processes WYSIWYG HTML already authored inside the application during mail generation, so the parameters look like app-generated links and the absence of any session, ComponentId or access check goes unnoticed.)
  - core-war/src/main/java/org/silverpeas/web/servlets/FileServer.java:184-185 — T6 M1 (reason to dismiss: It is a programmatic content scanner, not a user-facing HTTP route: it processes WYSIWYG HTML already authored inside the application during mail generation, so the parameters look like app-generated links and the absence of any session, ComponentId or access check goes unnoticed.)
  - core-library/src/main/java/org/silverpeas/core/contribution/content/wysiwyg/service/process/MailContentProcess.java:85-96 — T6 M1 (reason to dismiss: It is a programmatic content scanner, not a user-facing HTTP route: it processes WYSIWYG HTML already authored inside the application during mail generation, so the parameters look like app-generated links and the absence of any session, ComponentId or access check goes unnoticed.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Five independent judgements at five different fix sites with five different reasons to leave them alone: (T1) the undefined-ComponentId allow, which is dismissed as an intentional 'Personal space' feature and which even the framework controller (ComponentAccessController.java:145-149) would keep; (T2) no containment of the resolved path at all, dismissed because a caller with a ComponentId is already authorised and because TypeUpload/DirType look like internal URL-builder flags; (T3) a sibling servlet in the same package that reaches the same SilverpeasFileProvider sink with no authentication, no component authorisation and no path validation, dismissed as 'the legacy servlet, not the one the report names'; (T4) a sibling servlet that presents as already protected because it has isValid() and a session, but whose check is a two-substring test that never looks at '..'; and (T5) the coupled publicFiles=yes storage mode that the natural over-broad access-control repair destroys. That gives four deepseek-type traps (protection absent, each with its own dismissal) and one mimo-type coupled value (T5), spread over FileServer.java, TempFileServer.java, OnlineFileServer.java and the shared SilverpeasFileProvider/descriptor pair, so no single guard closes more than one. T6 (the ImageUrlToDataSourceScanner, which resolves FileServer parameters into mail attachments with no access check) is a good optional sixth when the harness can drive MailContentProcess, but it is same-file and mail-generation-bound, so it adds less than T3/T4 and risks an unfair test surface. T2 deliberately folds the absolute-path (TypeUpload), the temporary-repository (DirType) and the '..' (Directory/Size/SourceFile) shapes into one trap because a single containment guard at FileServer.getSilverpeasFile closes all three; splitting them would inflate the count. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): publicFiles=yes legitimately lets any logged-in user who is NOT a member of the storage component download its files (FileServer.java:154-157); a security rule of the form 'require membership of the component' contradicts a documented behaviour and would fail a must-keep-working test. | Absolute path descriptors are legitimate for attachments: OnlineFileServer.java:76-91 and core-war/src/main/java/org/silverpeas/web/servlets/RestOnlineFileServer.java:167-173 deliberately build them from database rows; a blanket ban on absolute paths in SilverpeasFileProvider refuses an input shape a legitimate use needs. | The Size parameter is a legitimate resized-image directory marker produced by FileServerUtils.getImageURL (FileServerUtils.java:193-197) and used for thumbnails; rejecting every Size value, rather than validating/normalising it, breaks thumbnail serving. | TempFileServer must keep serving nested and non-ASCII names under the temporary repository (core-library/src/test/java/org/silverpeas/core/util/FileServerUtilsTest.java:62-67); a rule that forbids path separators outright, rather than traversal, would break it. | Requiring a defined ComponentId refuses requests that the pinned code serves as 'Personal space' (FileServer.java:150-152); that is the published intent, but any hidden test that still expects a personal-space URL without ComponentId to work would contradict the security rule.. Conflicts the reader found: The natural repair of the missing-ComponentId gap is to route everything through isComponentAvailableToUser (FileServer.java:159-160) or to delegate to ComponentAccessController; applied unconditionally it denies the publicFiles=yes storage components that must remain downloadable by any logged-in non-member (FileServer.java:154-157, DefaultInstanceAccessControlExtension.java:72-74, ComponentAccessControllerTest.java:176-177). | Closing the path-containment gap in the shared provider (SilverpeasFileProvider.java:202-216) by forbidding absolute descriptors breaks the legitimate absolute attachment paths OnlineFileServer.java:76-91 depends on, so the containment rule cannot simply live in the shared layer; it has to be per call-site, which is what keeps T2 and T3 independent. | A single 'resolved path must start with the uploads repository' rule reused by TempFileServer breaks that servlet's legitimate files, which live under the temporary repository joined at TempFileServer.java:81-82, not under the component upload path.

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

## Environment (`tasks/stk-silverpeas-core-27788/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-silverpeas-core-27788/instruction.md`)
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

## Tests (`tasks/stk-silverpeas-core-27788/tests/`)
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
- **Wrong-fix patches** go in `build/stk-silverpeas-core-27788/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-silverpeas-core-27788/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-silverpeas-core-27788/manifest.json`:**
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

**Also in `build/stk-silverpeas-core-27788/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-silverpeas-core-27788 --only static
python3 -I common/gate/gate.py stk-silverpeas-core-27788 --only nop
python3 -I common/gate/gate.py stk-silverpeas-core-27788 --only oracle
python3 -I common/gate/gate.py stk-silverpeas-core-27788 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-silverpeas-core-27788/`;
  - edit only `tasks/stk-silverpeas-core-27788/`, `build/stk-silverpeas-core-27788/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-27788.json`. Verify each trap on the
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

Stacked task slug: `stk-silverpeas-core-27788`. Control task slug: `stk-silverpeas-core-27788-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-27788.json`.
