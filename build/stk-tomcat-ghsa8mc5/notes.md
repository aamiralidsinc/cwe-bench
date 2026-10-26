# stk-tomcat-ghsa8mc5 — build notes

Start (UTC): 2026-10-26T02:22:46Z (batch runner start stamp; this builder session follows it).
End (UTC): 2026-10-26T05:06 (patches stage stopped after 14 min with every check job still pending).

## What the task is

Apache Tomcat at 644232eee826013dcd502e47c792bc28a5a418f4 (parent of the first CVE-2025-66614 fix
on 11.0.x). The report describes a TLS client-certificate bypass: the TLS configuration selected
for the connection is not the one that belongs to the virtual host that actually serves the
request. The published fixes are A = 258a591b61f8 (+ the NIO2 follow-up 5f950a0e69 on 11.0.x) and
B = 021d1f833e38 (case-insensitive configuration lookup, CVE-2026-32990).

## Levers (one line each)

- T1_plain (advisory route, both): the request name must resolve to the TLS configuration the
  connection negotiated; HTTP/1.1 processor after host parsing. where
  java/org/apache/coyote/http11/Http11Processor.java:784; policy
  java/org/apache/tomcat/util/net/AbstractEndpoint.java:737.
- T2_http2 (published-fix far site, deepseek): the same outcome on the second front end; an
  HTTP/2 authority naming another virtual host. where java/org/apache/coyote/http2/Stream.java:509.
- T5_no_sni (uncovered/shape, both): with no TLS name the default configuration is in force; a
  request naming another configuration must be refused, a request resolving to the default must be
  served. where java/org/apache/tomcat/util/net/AbstractEndpoint.java:737,700.
- T3_case (published B fix, mimo): the configuration lookup is case-sensitive while the mapper is
  case-insensitive. where java/org/apache/tomcat/util/net/AbstractEndpoint.java:737-745.
- T4_served (uncovered, deepseek): the adapter can serve a name different from the request name
  (proxyName/useIPVHosts) after the request-level check. where
  java/org/apache/catalina/connector/CoyoteAdapter.java:667-687.

Concepts: C1 = {T1_plain, T2_http2, T5_no_sni}; C2 = {T3_case}; C3 = {T4_served}.

## Verified

- The pinned tree builds with javac (17) and the fixed library set; the project's own
  TestSSLHostConfig passes at the pinned commit (environment image build).
- Real embedded Tomcat on loopback: 6 TLS connectors (NIO, NIO2, adapter-served strict name,
  adapter-served internal name, wildcard HTTP/1.1, HTTP/2 ALPN) and 5 virtual hosts. Real
  SSLSockets with explicit TLS names and, where needed, a real client certificate; HTTP/1.1 status
  lines and an HTTP/2 preface + literal-HPACK HEADERS frame. A static counter in the servlet is the
  side-effect oracle.
- Pinned: 6/6 security cases are served (200) and all 16 functional/project cases pass.
- Reference (A + NIO2 + B + served-name re-check + the request-level TLS name): 6/6 security cases
  are client errors with no application run; 16/16 functional/project cases pass.
- Every check variant was run through the same harness before the gate: upstream A alone fails
  case + served; A+B fails served; each miss patch leaves its own concept's security case open
  while functional passes; refuse-all and over-broad fail functional; crash returns 500 (caught);
  the adapter-only design and the hardening design pass.
- Patches were regenerated from the pinned tree and diff-verified byte-for-byte against the
  validated variant trees (0 differing files).

## Not verified / notes

- The prompt's embedded "screener's record" was the HTTP/2 header-value analysis from
  pipelines/stacking/out/reader-ds; it contradicts the pinned commit and the published fix commits
  (which are the SNI-vs-protocol-host fixes). The stacked rules and the manifest point at
  pipelines/stacking/out/reader/h3-ghsa-8mc5-53m5-3qj2.json, whose SNI analysis matches the code;
  the design here was re-derived from the fetched commits. The reader record itself says
  "usable: false" for a one-guard adapter design; the stack uses three independent concepts (the
  protocol front ends + missing-name semantics, the case lookup, the served-name override), each
  with its own miss patch.
- APR/OpenSSL connectors are not exercised (they need libtcnative / FFM; the base image is JDK 17
  and the Panama sources are excluded from the javac tree). The reference does not add the APR
  producer. RewriteValve host rewrites are not tested; the property would cover them but the
  reference checks before the valve chain.
- The `/tmp` inode exhaustion on the shared VM made several prototype runs slow; the final
  verifier uses the workspace for TMPDIR and the image's own /tmp for the JVM temporary server
  directories.
- Nothing outside this advisory's protection was pursued.

## Gate

- static: PASS (stacked and control).
- nop: PASS — 6 security tests fail on the pinned code, 16 functional/project tests pass.
- oracle: PASS — three runs, reward 1.0, 22/22 tests each.
- patches: NOT COMPLETED. All 11 check jobs stayed `pending` for 14 minutes behind the shared VM's
  Harbor queue (the same queue that delayed the nop/oracle teardowns); the stage was stopped. Every
  check variant had already been run through the real embedded-Tomcat harness before the gate and
  behaved as declared (Verified), but the formal patches stage did not run.
- control: static PASS; nop/oracle/patches were not run because the shared Harbor queue did not
  start their jobs in the remaining time.

The task therefore is NOT reported as gate-passed: static, nop and oracle pass; the patches stage
(and the control's container stages) were blocked by shared-VM infrastructure, not by a task
failure. The local harness evidence for each check is in Verified above.
