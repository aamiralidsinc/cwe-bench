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

Project root: `/home/mara/cwe-bench`. Task: `stk-payara-29001`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 29001; cross-site request forgery: state-changing admin routes authenticated 
- Pinned (vulnerable) commit: a67eae17e621925b072fbc5880f6bd70a4dad5b6. Published fix: be83ab093692bafb09125323f3fdefaeab9cc398.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-29001",
 "pattern": "H4",
 "repo": "payara/payara",
 "pinned_commit": "a67eae17e621925b072fbc5880f6bd70a4dad5b6",
 "protections": [
  "P1 anti-forgery: an inbound admin-console request that causes a privileged admin REST operation must carry a per-request proof of intent (anti-forgery token or origin/referrer check); the FORM-auth session cookie alone must not authorize it (web.xml:180-188, 219-226; AdminConsoleAuthModule.java:169-182; no inbound token or CSRF filter anywhere: web.xml:94-105 is the only filter and it is mapped to FacesServlet only).",
  "P2 endpoint integrity: the admin REST bearer token held in the console session (AdminConsoleAuthModule.java:214-217) must only be sent to the console's own server-derived REST endpoint, never to a base address supplied by the request (RestUtil.java:831-835, 841-846, 992-997 vs LogFilesContentSource.java:89-94, LogViewerContentSource.java:84-91, ClientStubsContentSource.java:87-92, AdminCallbackHandler.java:189-203).",
  "P3 representation control: the response Content-Type/extension must be chosen by the server-side ContentSource, not by a request parameter (DownloadServlet.java:400-414 falls back to request.getParameter for any Context attribute, and DownloadServlet.java:254-266 consumes ContentType/extension when writing the response header).",
  "P4 path shape: values concatenated into the outbound admin REST path or into server-side file names must be constrained to the shape the console generates (ClientStubsContentSource.java:92, 97-100; LogFilesContentSource.java:99-104; LogViewerContentSource.java:91-94)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:166-178",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:212-231",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:132-135"
   ],
   "reason_to_dismiss": "The route is called /download/* and only streams a file back to the browser, and the container already enforces an admin-role FORM-auth constraint on /* (web.xml:180-188) with a re-applied saved Subject on every request (AdminConsoleAuthModule.java:178-182), so the session cookie looks like the intended gate.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:180-188",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:94-105",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/security/AdminConsoleAuthModule.java:178-182"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:166",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:132-135"
   ],
   "reason_to_dismiss": "The console only ever issues GET for downloads, so POST looks like an internal detail of doGet and a GET-only method rule looks sufficient; the mapping has no http-method restriction either way.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:132-135"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:82-105",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:78-95",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:80-100",
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:119-126"
   ],
   "reason_to_dismiss": "They are three pluggable ContentSource implementations registered by an init-param; each one just opens a stream to download, and the servlet looks like the single place to guard, so the per-source request handling reads as ordinary download plumbing.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:119-126",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:105",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:95",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:100"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M3",
   "origin": "uncovered_upstream",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:830-838",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:840-850",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:991-1001"
   ],
   "reason_to_dismiss": "These are shared Jersey client helpers written for JSF handlers; authorization is the caller's job, and the servlet is the caller that should be checking, so the shared layer looks exempt.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:831-835",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:841-846",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:992-997"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:88-94",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:84-91",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:87-92",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:831-835"
   ],
   "reason_to_dismiss": "restUrl is a routing hint that the console's own pages always set to sessionScope.REST_URL (domainLogs.jsf:141, logViewerRaw.jsf:67, subComponentTable.inc:89), so it reads as a trusted internal value; removing it looks like it would break proxy and deployment layouts.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:89-94",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:84-91",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:87-92",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:831-835",
    "nucleus/admin/util/src/main/java/com/sun/enterprise/admin/util/AdminCallbackHandler.java:189-203",
    "appserver/admingui/common/src/main/resources/appServer/domainLogs.jsf:141",
    "appserver/admingui/common/src/main/resources/logViewer/logViewerRaw.jsf:67",
    "appserver/admingui/common/src/main/resources/applications/subComponentTable.inc:89"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:400-414",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:254-266"
   ],
   "reason_to_dismiss": "ContentType and extension only pick a MIME type for a file that is about to be saved; they are documented as Context attributes set by the ContentSource, so the request-parameter fallback in Context.getAttribute reads as a convenience and the header write looks cosmetic.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:406-410",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:254-266",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:80"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:86-92",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:97-100",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:88-104",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:85-94"
   ],
   "reason_to_dismiss": "appName, target and instanceName are chosen from console drop-downs and pagination links, so they read as enumerations of known resources rather than free text, and the request only reaches this code once an admin is logged in.",
   "distance": {
    "files": 3,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:86",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:92",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:97-99",
    "appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:99-100"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
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
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "Fixing T5 by making restUrl optional and defaulting to the session REST_URL leaves T1 fully reachable (a cross-site request simply omits restUrl), so the CSRF route becomes invisible rather than closed.",
   "Fixing T1 with a per-request token stops the cross-site path into T5, but the request-controlled outbound endpoint is still there; a test that only exercises the token will not catch it.",
   "T7 stays reachable after both a T1 and a T5 fix because appName/target/instanceName are still concatenated into the REST path and the server-side file names.",
   "T4 is an alternative fix site for the whole T1-T3 group: a check added in RestUtil's *FromServlet helpers would cover every current caller, but no such check exists at either layer."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "The natural T1 fix (require POST, a request-body token, a custom header, or SameSite=Strict) breaks the cross-page GET downloads that are the legitimate use of the very pages that supply T5's restUrl value (domainLogs.jsf:141-154, logViewerRaw.jsf:67, subComponentTable.inc:89)."
  },
  {
   "a": "T5",
   "b": "T7",
   "what": "A T5 fix that rejects or rewrites the download query string wholesale also drops the target/appName/instanceName parameters that T7's legitimate callers depend on; the two need separate decisions (endpoint source vs path-segment validation)."
  }
 ],
 "fairness_risks": [
  "Legitimate console downloads are opened as cross-page GET navigations (iframe.src and window.location) carrying query parameters: appserver/admingui/common/src/main/resources/appServer/domainLogs.jsf:141-154, likely the most important one; logViewer/logViewerRaw.jsf:67; applications/subComponentTable.inc:89. Any security rule that requires POST, a body-carried token, a custom request header or SameSite=Strict contradicts behaviour these downloads need.",
  "All three pages pass restUrl=#{sessionScope.REST_URL} (encoded on logViewerRaw.jsf), so a rule that rejects a request-supplied restUrl before the pages are updated breaks every log-file, log-view and client-stub download.",
  "The ContentSources init-param (web.xml:119-126) is a servlet extension point; refusing request-parameter ContentType/extension could break content sources shipped outside this repository.",
  "appName and instanceName are user-selected but legal Payara deployment/instance names (domainLogs.jsf:141, subComponentTable.inc:89); an over-broad rejection of separators or slashes can refuse names a real domain accepts."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T5",
   "T6",
   "T7"
  ],
  "why": "Four independent judgements in one servlet surface, each with a different reason to leave it alone: T1 is the CSRF hole on /download/* (absent protection hidden behind an admin-only FORM-auth constraint and a read-only-sounding route, deepseek-type); T5 is the request-chosen REST base that the session's bearer token is attached to, coupled to three JSF pages that must keep passing the same value (mimo-type, and the one site a token-only fix misses); T6 is the Context attribute falling back to request parameters so ContentType/extension steer the response header; T7 is unvalidated appName/target/instanceName concatenated into the REST path and into server-side file names. A single guard closes T1/T2/T3/T4 (hence one group), but it does not touch T5, T6 or T7, and a T5 fix does not touch T1 unless the token is actually implemented. T5 and T6/T7 are the least report-visible and give the stack its depth; T1 provides the in-family anchor. Caveat: T6 and T7 are in-file/in-route siblings rather than members of the CSRF family, so a grader that requires every stacked trap to be the advisory's own CWE should read this candidate as 2 groups (T1, T5) and not as a 4-trap stack."
 },
 "unverified": [
  "The published fix could not be read: be83ab093692bafb09125323f3fdefaeab9cc398 is a merge commit and no diff was available in the worktree, so it is unconfirmed whether the fixed protection is P1 (anti-forgery on the download route) or P2 (request-controlled outbound endpoint with the session token attached). The three fix_sites quoted by the screener are the three files that read restUrl, which fits P2 better than P1, but this is inference.",
  "The advisory text for GHSA-X939-7FQ5-V9V6 / CVE-2026-12986 was not present in the checkout; the CSRF family label is taken from the screener, not verified against the advisory.",
  "No build or run was possible (no shell in this session), so the on-the-wire effect of ?ContentType=... on the response header (T6) and of a slash-bearing appName on the outbound REST URL (T7) is inferred from code, not observed.",
  "git history could not be inspected, so the H3 questions (whether an earlier fix left a later bug open, whether the later bug lives in code the earlier fix wrote) and present_in_latest for all sites are unanswered.",
  "Whether the console session cookie is issued with SameSite=None/Lax/Strict could not be determined from the repository (web.xml:160-164 sets http-only only), so the browser-side reachability of a cross-site GET is not established here.",
  "The claim that JSF command POSTs are effectively protected by the per-view ViewState token (and therefore are not additional in-family traps) is a reasoned judgement from web.xml:70-73, not an observed behaviour."
 ]
}
  ```
- Published fix sites:   - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156 — T1 M4 (reason to dismiss: The route is called /download/* and only streams a file back to the browser, and the container already enforces an admin-role FORM-auth constraint on /* (web.xml:180-188) with a re-applied saved Subject on every request (AdminConsoleAuthModule.java:178-182), so the session cookie looks like the intended gate.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:166-178 — T1 M4 (reason to dismiss: The route is called /download/* and only streams a file back to the browser, and the container already enforces an admin-role FORM-auth constraint on /* (web.xml:180-188) with a re-applied saved Subject on every request (AdminConsoleAuthModule.java:178-182), so the session cookie looks like the intended gate.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:212-231 — T1 M4 (reason to dismiss: The route is called /download/* and only streams a file back to the browser, and the container already enforces an admin-role FORM-auth constraint on /* (web.xml:180-188) with a re-applied saved Subject on every request (AdminConsoleAuthModule.java:178-182), so the session cookie looks like the intended gate.)
  - appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:132-135 — T1 M4 (reason to dismiss: The route is called /download/* and only streams a file back to the browser, and the container already enforces an admin-role FORM-auth constraint on /* (web.xml:180-188) with a re-applied saved Subject on every request (AdminConsoleAuthModule.java:178-182), so the session cookie looks like the intended gate.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:82-105 — T3 M2 (reason to dismiss: They are three pluggable ContentSource implementations registered by an init-param; each one just opens a stream to download, and the servlet looks like the single place to guard, so the per-source request handling reads as ordinary download plumbing.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:78-95 — T3 M2 (reason to dismiss: They are three pluggable ContentSource implementations registered by an init-param; each one just opens a stream to download, and the servlet looks like the single place to guard, so the per-source request handling reads as ordinary download plumbing.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:80-100 — T3 M2 (reason to dismiss: They are three pluggable ContentSource implementations registered by an init-param; each one just opens a stream to download, and the servlet looks like the single place to guard, so the per-source request handling reads as ordinary download plumbing.)
  - appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:119-126 — T3 M2 (reason to dismiss: They are three pluggable ContentSource implementations registered by an init-param; each one just opens a stream to download, and the servlet looks like the single place to guard, so the per-source request handling reads as ordinary download plumbing.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:88-94 — T5 M11 (reason to dismiss: restUrl is a routing hint that the console's own pages always set to sessionScope.REST_URL (domainLogs.jsf:141, logViewerRaw.jsf:67, subComponentTable.inc:89), so it reads as a trusted internal value; removing it looks like it would break proxy and deployment layouts.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:84-91 — T5 M11 (reason to dismiss: restUrl is a routing hint that the console's own pages always set to sessionScope.REST_URL (domainLogs.jsf:141, logViewerRaw.jsf:67, subComponentTable.inc:89), so it reads as a trusted internal value; removing it looks like it would break proxy and deployment layouts.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:87-92 — T5 M11 (reason to dismiss: restUrl is a routing hint that the console's own pages always set to sessionScope.REST_URL (domainLogs.jsf:141, logViewerRaw.jsf:67, subComponentTable.inc:89), so it reads as a trusted internal value; removing it looks like it would break proxy and deployment layouts.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:831-835 — T5 M11 (reason to dismiss: restUrl is a routing hint that the console's own pages always set to sessionScope.REST_URL (domainLogs.jsf:141, logViewerRaw.jsf:67, subComponentTable.inc:89), so it reads as a trusted internal value; removing it looks like it would break proxy and deployment layouts.)
- Uncovered routes to confirm (pattern B):   - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:154-156 — T2 M1 (reason to dismiss: The console only ever issues GET for downloads, so POST looks like an internal detail of doGet and a GET-only method rule looks sufficient; the mapping has no http-method restriction either way.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:166 — T2 M1 (reason to dismiss: The console only ever issues GET for downloads, so POST looks like an internal detail of doGet and a GET-only method rule looks sufficient; the mapping has no http-method restriction either way.)
  - appserver/admingui/war/src/main/webapp/WEB-INF/web.xml:132-135 — T2 M1 (reason to dismiss: The console only ever issues GET for downloads, so POST looks like an internal detail of doGet and a GET-only method rule looks sufficient; the mapping has no http-method restriction either way.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:830-838 — T4 M3 (reason to dismiss: These are shared Jersey client helpers written for JSF handlers; authorization is the caller's job, and the servlet is the caller that should be checking, so the shared layer looks exempt.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:840-850 — T4 M3 (reason to dismiss: These are shared Jersey client helpers written for JSF handlers; authorization is the caller's job, and the servlet is the caller that should be checking, so the shared layer looks exempt.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/util/RestUtil.java:991-1001 — T4 M3 (reason to dismiss: These are shared Jersey client helpers written for JSF handlers; authorization is the caller's job, and the servlet is the caller that should be checking, so the shared layer looks exempt.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:400-414 — T6 M8 (reason to dismiss: ContentType and extension only pick a MIME type for a file that is about to be saved; they are documented as Context attributes set by the ContentSource, so the request-parameter fallback in Context.getAttribute reads as a convenience and the header write looks cosmetic.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/DownloadServlet.java:254-266 — T6 M8 (reason to dismiss: ContentType and extension only pick a MIME type for a file that is about to be saved; they are documented as Context attributes set by the ContentSource, so the request-parameter fallback in Context.getAttribute reads as a convenience and the header write looks cosmetic.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:86-92 — T7 M8 (reason to dismiss: appName, target and instanceName are chosen from console drop-downs and pagination links, so they read as enumerations of known resources rather than free text, and the request only reaches this code once an admin is logged in.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/ClientStubsContentSource.java:97-100 — T7 M8 (reason to dismiss: appName, target and instanceName are chosen from console drop-downs and pagination links, so they read as enumerations of known resources rather than free text, and the request only reaches this code once an admin is logged in.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogFilesContentSource.java:88-104 — T7 M8 (reason to dismiss: appName, target and instanceName are chosen from console drop-downs and pagination links, so they read as enumerations of known resources rather than free text, and the request only reaches this code once an admin is logged in.)
  - appserver/admingui/common/src/main/java/org/glassfish/admingui/common/servlet/LogViewerContentSource.java:85-94 — T7 M8 (reason to dismiss: appName, target and instanceName are chosen from console drop-downs and pagination links, so they read as enumerations of known resources rather than free text, and the request only reaches this code once an admin is logged in.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T5, T6, T7. Why: Four independent judgements in one servlet surface, each with a different reason to leave it alone: T1 is the CSRF hole on /download/* (absent protection hidden behind an admin-only FORM-auth constraint and a read-only-sounding route, deepseek-type); T5 is the request-chosen REST base that the session's bearer token is attached to, coupled to three JSF pages that must keep passing the same value (mimo-type, and the one site a token-only fix misses); T6 is the Context attribute falling back to request parameters so ContentType/extension steer the response header; T7 is unvalidated appName/target/instanceName concatenated into the REST path and into server-side file names. A single guard closes T1/T2/T3/T4 (hence one group), but it does not touch T5, T6 or T7, and a T5 fix does not touch T1 unless the token is actually implemented. T5 and T6/T7 are the least report-visible and give the stack its depth; T1 provides the in-family anchor. Caveat: T6 and T7 are in-file/in-route siblings rather than members of the CSRF family, so a grader that requires every stacked trap to be the advisory's own CWE should read this candidate as 2 groups (T1, T5) and not as a 4-trap stack. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Legitimate console downloads are opened as cross-page GET navigations (iframe.src and window.location) carrying query parameters: appserver/admingui/common/src/main/resources/appServer/domainLogs.jsf:141-154, likely the most important one; logViewer/logViewerRaw.jsf:67; applications/subComponentTable.inc:89. Any security rule that requires POST, a body-carried token, a custom request header or SameSite=Strict contradicts behaviour these downloads need. | All three pages pass restUrl=#{sessionScope.REST_URL} (encoded on logViewerRaw.jsf), so a rule that rejects a request-supplied restUrl before the pages are updated breaks every log-file, log-view and client-stub download. | The ContentSources init-param (web.xml:119-126) is a servlet extension point; refusing request-parameter ContentType/extension could break content sources shipped outside this repository. | appName and instanceName are user-selected but legal Payara deployment/instance names (domainLogs.jsf:141, subComponentTable.inc:89); an over-broad rejection of separators or slashes can refuse names a real domain accepts.. Conflicts the reader found: The natural T1 fix (require POST, a request-body token, a custom header, or SameSite=Strict) breaks the cross-page GET downloads that are the legitimate use of the very pages that supply T5's restUrl value (domainLogs.jsf:141-154, logViewerRaw.jsf:67, subComponentTable.inc:89). | A T5 fix that rejects or rewrites the download query string wholesale also drops the target/appName/instanceName parameters that T7's legitimate callers depend on; the two need separate decisions (endpoint source vs path-segment validation).

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

## Environment (`tasks/stk-payara-29001/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-payara-29001/instruction.md`)
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

## Tests (`tasks/stk-payara-29001/tests/`)
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
- **Wrong-fix patches** go in `build/stk-payara-29001/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-payara-29001/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-payara-29001/manifest.json`:**
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

**Also in `build/stk-payara-29001/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-payara-29001 --only static
python3 -I common/gate/gate.py stk-payara-29001 --only nop
python3 -I common/gate/gate.py stk-payara-29001 --only oracle
python3 -I common/gate/gate.py stk-payara-29001 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-payara-29001/`;
  - edit only `tasks/stk-payara-29001/`, `build/stk-payara-29001/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-29001.json`. Verify each trap on the
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

Stacked task slug: `stk-payara-29001`. Control task slug: `stk-payara-29001-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-29001.json`.
