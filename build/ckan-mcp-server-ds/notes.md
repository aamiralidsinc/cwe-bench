# ckan-mcp-server-ds — build notes

Start (UTC): 2026-10-18T21:17:28Z (pipeline start). Build work began 21:18Z.
End (UTC): 2026-10-18T23:02Z.

Candidate: GHSA-798P-78G2-V556 / CVE-2026-61612, ondata/ckan-mcp-server.
Pinned 129ba172ec15429347ea1faf5c919af730720370 (confirmed the direct parent of the published
fix bb7439b553b9f965adc3d43bcd415c42eebe2f40 in the upstream clone; the pinned tree therefore
does not contain the fix or its 11 regression tests). Published fix extracted with `git show`
and reduced to source changes (src/utils/http.ts, src/tools/sparql.ts, src/transport/http.ts).

Track: injected. Pattern: A + injected; no Pattern B route could be built fairly (see below).

## Levers (one line each)

- T1 base (A, src/utils/http.ts:245 + :387): a caller-supplied portal host name that resolves to
  loopback/internal is fetched — the reported site; tests drive dataset search, status check and a
  ckan:// resource read, plus a public+internal multi-address name and a redirect to a loopback
  literal. Reason to dismiss: the string denylist looks complete.
- T2 far site (A, src/tools/sparql.ts:47): the fetch-based second implementation imports the same
  validator but never resolves the endpoint name. Reason to dismiss: HTTPS-only, already validated,
  neighbouring feature.
- T3 far site (A, src/transport/http.ts:9): the network transport starts with no permitted-hosts
  list. Reason to dismiss: a deployment concern, not the request path.
- T4 injected sibling S1 (src/tools/portal-discovery.ts:24, :123): a caller-supplied alternative
  registry URL is fetched with raw axios. Reason to dismiss: a third-party public directory
  override, not a CKAN request.
- T5 injected sibling S2 (src/tools/preview.ts:43, registered in src/server.ts): a caller-supplied
  download URL is fetched with raw fetch for a preview. Reason to dismiss: a display helper whose
  URL normally comes from portal metadata.

Input-shape coverage: plain host name, name with one public and one internal address, IP-literal
redirect target, ckan:// resource form; boundary magnitudes 172.15.x.x / 100.63.x.x alongside the
private ranges; private literals keep being refused.

## Verified (behavioural, in the built image, offline)

- Pinned+injected: 10/10 security tests fail, 89/89 functional pass (reward 0.0) [gate nop].
- Oracle: 10/10 security, 89/89 functional, reward 1.0, three identical runs [gate oracle].
- Strengthened after the first gate pass: the functional tests now also assert that the registry
  and preview entry points use the URL the caller supplied (so deleting or ignoring the feature
  cannot pass) and that a legitimate ckan:// resource read works. Re-verified in the image on
  injected (security all fail), oracle, alt and hardening (21/21 each).
- Every checks/ patch run through the gate: literal_only (9 security fail, 0 fun fail),
  miss_sparql (2), miss_transport (1), miss_registry (1), miss_preview (1), check_after_connect (1),
  overbroad (0 sec fail, 39 fun fail), hardening (1.0), alt_fix (1.0).
- Design neutrality: an independently written pre-resolution fix (alt_fix.patch, no lookup agent,
  different code) scores 1.0, and a stricter hardening of the same ranges also scores 1.0.
- Real entry points: MCP tools and resources over the SDK in-memory transport; the bundled
  dist/index.js started as a child process for the transport tests. Project tests (unit/http,
  integration/sparql, 78 cases) restored from pristine copies and run against the agent's source.
- Name resolution is deterministic offline: the verifier writes /etc/hosts entries and serves the
  same table over a local DNS server (dns.setServers), so getaddrinfo- and c-ares-based checks see
  identical answers. This was validated with dns.lookup, dns.promises.lookup and dns.resolve4.
- Whole project suite (418 passed, 6 skipped) on pinned, injected and oracle trees.

Gate: `--only static` leaves only the post-build blind patch and FAIRNESS.md (nothing else);
`--only nop`, `--only oracle` and `--only patches` all PASSED. The shared-VM Docker network flake
caused spurious compose failures, retried; the patch table in gate_report.partial.json shows all
9 checks ok.

## Pattern B

No Pattern B route (real upstream code, reachable in Node, not covered by the published fix) could
be built as a fair trap:
- the non-Node Worker fetch branch is unreachable from the Node entry point without faking
  process.versions;
- the fetch and axios redirect routes are real on the pinned copy but cannot be isolated offline:
  a locally served first hop must itself resolve to an internal address, so any correct first-hop
  guard hides the redirect, and a redirect from a public first hop needs network or CAP_NET_ADMIN;
- the IPv6 ::ffff hex spellings that isBlockedIp misses are an encoding variant, excluded by the
  build rules.
The redirect route is still covered as a security test under T1. Rows were appended to
build/audit/uncovered-routes.tsv with built=no and the reasons.

## Unverified / guesses

- The published fix's claim that a custom lookup agent also covers redirect-to-internal targets was
  not verified against Node's follow-redirects behaviour for IP-literal targets; the task does not
  depend on it (the redirect test is satisfied by the first-hop guard of any correct fix).
- The multi-address input shape is tested but is not a separate lever: glibc orders a loopback
  address ahead of a public one, so a naive single-address lookup may still catch it; a c-ares
  resolve4-based naive check sees the public address first and misses it.
- Trial behaviour of the two target models is not known at build time (no trials were run).
- The image build needs network once (git fetch + npm ci + Claude Code bootstrap); everything the
  verifier runs afterwards is offline (verified with `docker run --network none`).

## Outside the stated scope (not built on)

- The HTTP transport serves POST /mcp with no authentication; the published fix adds only an
  allowlist gate, not auth.
- isBlockedIp does not cover 198.18.0.0/15, 224.0.0.0/4 or several IPv6 notation forms; not pursued
  (encoding variants / out of the advisory's protection).

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

Instruction-only upgrade; no repo code, tests, solution or checks were changed and the prebuilt
image was reused (no rebuild).

- Instruction: replaced the route-by-route report (dataset search, status check, redirect,
  response-supplied address, network transport, `CKAN_ALLOWED_DOMAINS`, stdio, `ckan://` resources)
  with one property stated over the protected outcome — no caller-supplied destination and no
  destination taken from another service's response may cause a connection to an internal address,
  whatever address the connection ends up using. The two required contracts are kept: every address
  a name maps to must be acceptable, and a network-reachable server must refuse to start until the
  permitted hosts are configured (the local mode must start without that setting). No tool, route,
  sibling, far site, stage, format or count is named.
- Lever check: the task already has how-type levers, so none was added. T1 is M6/M8 (the guard
  inspects the supplied text; the protected item is the address the resolver produces, and the
  check never calls that producer). T3 and the two injected siblings are M4 (a route where the
  protection never existed). T2 is an extra entry point on a fetch client.
- Coverage: unchanged. Every route reachable from the Node entry point is already asserted
  (caller-supplied destinations across the shared client, the fetch client, the registry override,
  the download preview, the `ckan://` form; response-supplied redirect targets; the startup gate).
  The routes the published fix leaves open remain untestable offline: a redirect whose first hop is
  public cannot be served without network or CAP_NET_ADMIN, the Worker fetch branch is not reachable
  from the Node entry point without faking `process.versions.node`, and a rebinding test would
  invalidate the accepted pre-resolution design (`alt_fix.patch`). No test was weakened.

## Harden 2026-10-21 (Frontier 1.4 conversion + two new levers)

Both target models had solved the previous version; the trial record showed every existing trap fixed
on every graded run. The code's own O8b injection room supported two new fair levers, both reached
through real MCP entry points and both covered literally by the instruction's existing property
(“no destination supplied by a caller, and no destination the server takes from anything another
service returns … what matters is the address the connection ends up using, however that address was
obtained”).

- T6_probe (S3, injected): `ckan_find_portals` gained a `verify` option. When true it probes each
  portal `Href` returned by the registry with raw fetch and reports reachability. The destination is
  produced by another service's response, not by a request field, so a solver who guards the
  caller-supplied registry endpoint (T4) and stops there leaves it open. Reason to dismiss: a
  reachability/health display for public portals; the caller only sets a boolean.
  Security test: security/portal_probe_address.test.ts (registry response lists a loopback-resolving
  Href; real fetch to a canary; any client a fix uses is observed). Coupled functional tests:
  verify=true still reports reachability and probes the listed URL; omitting verify probes nothing.
- T7_mqa (S4, injected): the MQA quality tools gained an optional `mqa_base_url` (a per-environment
  mirror) used to build both the cache and the metrics request with raw axios/fetch, and an optional
  `identifier` that skips the portal metadata lookup. `server_url` is still checked by the tool's
  own `isValidMqaServer`, and the default base is a constant, so the mirror argument looks like
  trusted operator configuration. Reason to dismiss: a third-party metrics mirror, not a CKAN
  request. Security tests: security/quality_address.test.ts (both tools, base name resolves to
  loopback). Coupled functional tests: a public base is the one actually used for both requests; the
  identifier is still resolved from the portal when not supplied.

Oracle: `solution/fix.patch` now also guards the probe target (validate + resolve) and the
caller-supplied MQA base before either request is built. New `security_fail` checks `miss_probe.patch`
and `miss_mqa.patch` remove exactly those guards; all earlier checks were regenerated on the new
oracle. `alt_fix.patch` (pre-resolution design) and a new `blind.patch` (one outbound-destination
guard used by every client) both score 1.0.

Fairness notes: the instruction still names no tool, route, sibling, file or count; it gains no new
sentence about the levers. The property clause covering a destination taken from another service's
response already existed, and the MQA mirror is a caller-supplied destination like any other. The
only test removed in the conversion is the `ckan://` security probe that bound TCP port 443: the
separate verifier runs the suites as the unprivileged uid-1000 agent, which cannot bind a privileged
port. The `ckan://` resource form is still exercised functionally (public portal read) and the shared
client's resolution guard is covered by the tool-level tests.

Format: converted to Frontier 1.4 (workdir /workspace, separate verifier image, artifacts restore,
uid-1000 non-root grading, no-network both phases, fresh canary GUID, template test.sh/score.py).
The verifier image pre-installs the pinned dependency tree at /opt/ckan-deps from the committed
lockfile and test.sh links it in, because the artifact excludes node_modules.

## Gate (2026-10-21, final files)

- `python3 -I builder/conformance_check.py tasks/ckan-mcp-server-ds` -> conforming.
- `--only static` -> PASSED.
- `--only nop` -> PASSED (12/12 security tests fail on the injected tree, 93/93 functional pass; reward 0.0).
- `--only oracle` -> PASSED (3 identical runs, reward 1.0: 12/12 security, 93/93 functional).
- `--only patches` -> PASSED (literal_only, miss_sparql, miss_transport, miss_registry, miss_preview,
  miss_probe, miss_mqa, check_after_connect = security_fail; overbroad = functional_fail; hardening,
  alt_fix, blind = 1.0).

One conversion bug found and fixed before the gate: the verifier Dockerfile's uid-1000 block was
missing the group-rename line, so `chown agent:agent` failed at image build; the image now matches
the template boilerplate (and builds).
