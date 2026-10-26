# cloudtak-ds — build notes

- Start (UTC): 2026-10-24T04:13:31Z (pipeline start; design work from 04:14)
- End (UTC): 2026-10-24T08:32Z

Advisory: GHSA-VQRW-QPHH-P34V / CVE-2026-54546 (dfpc-coe/cloudtak), SSRF / CWE-918,
IP-classification guard. Pinned ec81b3de5c0609d030c928398a45370cf1089201 (v13.22.0);
published fix 1e0f6e65977c86fbc0aa15e308c43cbcaee23a7c / 556b3563 (v13.22.1).

## What the published commits actually do (verified)

`git diff ec81b3d 1e0f6e6` touches only `api/package.json` (`@tak-ps/node-safeurl` ^1.4.0 ->
^1.5.0) and `api/lib/control/video-service.ts` (allow-list entries changed from full URL to
hostname). I extracted both npm tarballs: the only code change in node-safeurl 1.4.0 -> 1.5.0 is a
*relaxation* (resolve allow-list DNS names so blocked IPs of allowed hosts pass); it is not a
classification fix, and it does not change the fetch wrapper's redirect handling. The advisory's
own suggested fix (a `safeFetch` that classifies the resolved address and re-validates each
redirect hop) is not in the public commits. The screener flagged the advisory/fix association as
loose; verified and confirmed.

Consequence: the oracle implements the advisory's protection in source against the installed
1.4.0 (an offline verifier cannot `npm install` 1.5.0, and 1.5.0 would not close the tested
routes anyway). The video-service allow-list adaptation is retained as a coupled, must-keep-
working value in the report (see below) and as the `adjacent_api` wrong-fix check.

## Security property (written once, over the outcome)

No destination that a caller supplies, and no destination the service is sent to by something it
contacts, may cause a server-side request to reach a loopback, private, link-local, shared/CGNAT,
unique-local, unspecified, multicast or cloud-metadata address. What matters is the address the
connection ends up using, however it was derived, including a destination stored earlier. When a
name maps to several addresses every one must be acceptable. A refused operation returns a
client-visible error and nothing is sent to the refused address. An internal service the operator
has explicitly configured the product to use keeps working as today, for the destinations the
operator configured; that authorisation does not extend to other destinations a caller chooses.

## Levers

1. **L1 (main, how-type; real upstream, Pattern B / second implementation).** The tile-metadata
   route's ESRI-layer branch hands the *stored* source URL to the ESRI client, which performs its
   own global `fetch` (via the `esri-dump` dependency) with no `isSafeUrl` anywhere on that path;
   the internal response metadata is returned to the caller (full-read).
   `api/routes/basemap.ts:786` branch -> `api/lib/esri.ts:496` `EsriLayer.tilejson` ->
   `EsriDump#fetchMeta` -> global fetch. Reason to dismiss: the URL is checked when the basemap is
   created / the import route checks before its own ESRI branch, so "the ESRI path is guarded".
   How-type: the fix needs the mechanism (a second HTTP client inside a dependency, reached from
   stored data) understood, not just a route found.

2. **L2 (how-type; shape trap; real upstream, Pattern B).** The configured tile-origin exemption
   compares only `url.hostname` against the configured tile URL, so a stored TileJSON URL on the
   same host name but a different port (or scheme) is never classified.
   `api/routes/basemap.ts:798-800`. Reason to dismiss: "the operator's own tile host is trusted".
   Fix must classify the actual destination and narrow the exemption to what the operator
   configured, without breaking the operator's own destination.

3. **L3 (how-type; ordering/mechanism; real upstream, Pattern B).** On and around the exempt path
   the URL is fetched with the global `fetch`, which follows 3xx without re-classifying the hop;
   the same global-fetch pattern is at the import sink (`:112`) and the MapServer type sniff
   (`:498`). Reason to dismiss: "the check already ran on the URL". Test drives the exempt origin
   (the only first hop reachable offline) with a redirect to an internal canary.

4. **L4 (injected, ordering).** A TileJSON cache warm-up fetch runs before the guarded fetch in
   the tile-metadata route (`api/lib/basemap/warm.ts`, called from the route), so a request that
   is then refused has already reached the address. Reason to dismiss: "the guarded fetch is
   right below". Upstream fix never touches these files.

5. **L5 (injected, nested destination / producer off the check's path).** The route probes the
   first advertised tile template from the fetched TileJSON (`api/lib/basemap/probe.ts`), i.e. a
   destination supplied by the service the server just contacted. Reason to dismiss: "the URL
   came from a service we already fetched". Upstream fix never touches these files.

L1-L3 are real, unmodified pinned code. L4-L5 are the injected siblings.

## Candidate list (all sibling sites/routes found, and why the picks won)

Real, searched:
- `api/routes/basemap.ts:112` import global fetch + redirect follow (O8 lead; untestable offline:
  the first hop must be a routable public address and the verifier has no network/NET_ADMIN).
- `api/routes/basemap.ts:490-499` MapServer sniff global fetch + redirect (same offline limit).
- `api/routes/basemap.ts:798-811` tilejson global fetch + hostname-only exemption (picked, L2+L3).
- `api/routes/basemap.ts:786-800` ESRI branch, no check, third-party client (picked, L1).
- `api/routes/basemap.ts:827-840` hosted branch fetch of a URL built from operator config (not
  attacker-supplied; not a lever; guarded in the oracle for consistency).
- `api/lib/basemap/zxy.ts:42` and `hosted.ts:38` `isSafeUrl` then `undici.pipeline` (a second
  HTTP client, but no redirect following and the check is present; TOCTOU only - no deterministic
  offline test, dropped).
- `api/lib/basemap/mapserver.ts` / `featureserver.ts` / `imageserver.ts` use the guarded
  `@tak-ps/node-safeurl` fetch for tiles (protected; feature query paths likewise).
- `api/lib/esri.ts` import-path fetches use the guarded safeurl fetch; only the `EsriDump` client
  is unguarded (that is L1).
- `api/routes/proxy.ts:267` undici fetch after `isSafeUrl` (redirect gap) - a different feature
  with its own origin whitelist; outside this advisory's basemap sink.
- `api/routes/profile-asset.ts:353`, `api/routes/task.ts:294`, `lib/weather/*`, `lib/search/agol.ts`,
  `lib/user/cotak.ts`, `lib/control/video-service.ts:537` - other features, out of scope.
- `PATCH /basemap/:id` stores `url`/`tilejson` with only a scheme check (O8b lead). It is not a
  connection by itself; it is the *producer* that feeds L1/L2/L3 and is exercised through the real
  route in the tests by seeding the stored row the same way (the request path the advisory names).

Chosen: L1 (most complex: dependency-internal client reached from stored state), L2 (check on the
wrong part of the destination), L3 (per-hop mechanism), plus injected L4 (ordering) and L5
(nested destination). Rejected: import/sniff redirects (untestable offline), zxy TOCTOU
(non-deterministic), proxy/other features (outside the advisory's protection).

## Sites, routes, input shapes the security tests cover

- Entry point: the product's real route handlers registered by `api/routes/basemap.ts`
  `router(schema, config)`, invoked with a request/response pair (auth and the basemap store are
  stubs that answer per resource, as the rules allow).
- `GET /basemap/:id/tiles` (tile-metadata read), with the stored basemap row:
  - stored `url` in ESRI-layer form -> L1 canary.
  - stored `tilejson` on the configured tile host name but a different port -> L2 canary.
  - stored `tilejson` at the configured origin that 302s to a loopback canary -> L3 canary.
  - stored `tilejson` at a loopback address (non-exempt) -> L4 canary (warm before check).
  - stored `tilejson` at the configured origin whose body advertises a loopback tile
    template -> L5 canary (nested destination).
- All destinations are loopback canaries bound by the test; host names are in /etc/hosts
  (`127.0.0.1 tiles.internal.test`). No network, no GUI, no GPU.
- Refusal contract: any 4xx/5xx-class client error (tests assert code in 400..499) and no canary
  hit, and no canary marker in the response.

## Coupled must-keep-working behaviour (functional)

- The operator-configured tile origin still serves TileJSON: exact origin, nested path, token
  query appended, body returned (this is what `PATCH /basemap`+`GET .../tiles` do today).
- Ordinary basemap create/list/metadata and non-URL TileJSON basemaps still work.
- The video-service allow-list adaptation from the published fix (hostname entries) is kept;
  the `adjacent_api` wrong-fix check replaces the safeurl fetch wrapper globally and breaks the
  configured-origin fetch, proving over-broad shared-helper fixes fail.

## What was verified

- node-safeurl 1.4.0 / 1.5.0 tarball diff (only the allow-list relaxation).
- On the pinned tree in a node:24 container with the committed lockfile:
  - ESRI stored URL -> loopback canary hit, internal `name` reflected (full read).
  - hostname-only exemption (same host, different port) -> canary hit, body reflected.
  - exempt-origin 302 -> canary hit, body reflected.
  - configured-origin TileJSON -> fetch succeeds (functional).
- The project's own basemap tests require PostgreSQL/PostGIS + the project's MockTAKServer; see
  "project tests" below.

## What could not be verified

- The import route's redirect gap (offline first hop impossible). It is fixed in the oracle but
  not security-tested; noted as a fairness/coverage gap.
- Legitimate *ESRI* use offline (needs a reachable public ESRI endpoint); an over-broad fix that
  refuses every ESRI URL is not detected by the functional suite. Stated in the report.
- `present_in_latest` for the O8 routes: checked upstream history only for the files touched by
  the fix; the routes still exist at HEAD (they were moved in a later refactor).

## Local verification (node:24 container, committed lockfile, /etc/hosts fixture)

| patch | security | functional | result |
|---|---|---|---|
| none (pinned+injected) | 0/5 | 5/5 | nop shape: all exploits fire |
| solution/fix.patch (oracle) | 5/5 | 5/5 | clean |
| esri_unguarded | 4/5 (L1 fails) | 5/5 | security_fail |
| exemption_hostname | 4/5 (L2) | 5/5 | security_fail |
| redirect_unchecked | 4/5 (L3) | 5/5 | security_fail |
| warm_unguarded | 2/5 (L4 + collateral on the same helper) | 5/5 | security_fail |
| probe_unguarded | 4/5 (L5) | 5/5 | security_fail |
| crash_as_refusal | 2/5 (500 instead of 4xx) | 5/5 | security_fail |
| refuse_all | 5/5 | 4/5 (configured origin) | functional_fail |
| adjacent_api | 5/5 | 4/5 (configured origin) | functional_fail |
| hardening | 5/5 | 5/5 | pass |
| alternative | 5/5 | 5/5 | pass |

The JUnit reporter is invoked as `node --import tsx --test ... --test-reporter=junit
--test-reporter-destination=@OUT@` (a single reporter; node rejects a destination count that does
not match the reporter count).

## Gate

- static: PASSED (2026-10-24T04:47Z; re-run 2026-10-24T05:45Z after a report edit: PASSED)
- nop: PASSED (2026-10-24T05:02Z). Real verifier in the separate image: security 0/5, functional
  5/5, reward 0.0; the injected tree's exploits all fire through the real handlers.
- oracle: PASSED (2026-10-24T05:07Z). Three runs, each reward 1.0, identical security/functional
  results (5/5 + 5/5).
- patches: PASSED (2026-10-24T08:31Z, after the host Docker deadlock was fixed and the stage was
  re-run; the run took 46 minutes on the shared VM). All ten check patches behaved as declared:
  - esri_unguarded 0.8 (only the ESRI security test fails), exemption_hostname 0.8 (only the
    same-host/other-port test), redirect_unchecked 0.8 (only the redirect test), probe_unguarded
    0.8 (only the advertised-tile test), warm_unguarded 0.4 (the warm-up lever plus its two
    collateral canary hits), crash_as_refusal 0.4 (500s instead of client errors) - functional
    suite passes in every one;
  - refuse_all 0.0 and adjacent_api 0.0 (the configured tile origin breaks) - functional_fail;
  - hardening 1.0 and alternative 1.0 - independent correct fixes still score 1.0.
  The gate's earlier attempts died on the known Harbor egress-probe flake
  (`network_mode='allowlist' is not supported`, infra, exit 2), not on any check.
  Stage evidence is preserved under build/cloudtak-ds/stage-evidence/ (nop and the three oracle
  results.json, the patches and static gate reports).

## Project tests

The project's own basemap tests (`api/test/basemap-put.srv.test.ts`, `api/test/basemap.srv.test.ts`)
require PostGIS + the in-process MockTAKServer + openssl; they are not run in the verifier because
the verifier image is offline and the harness that starts them needs the database and TLS mock.
The pinned tree is unchanged apart from the injected helpers, and the project's own
`npm run test` path is untouched. This is a deliberate scope decision (recorded here), not a
claim that those tests were run.
