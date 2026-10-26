# whistle-cwe-path build notes

- Start: 2026-10-17T04:27:51Z
- End:   2026-10-17T04:57Z (UTC)

## What the task is
A Node.js HTTP/HTTPS debugging proxy. A forked internal "service" component listens on a
random loopback port and serves the web UI with captured data and stored artifacts. At the
pinned commit that component authenticates nothing: any HTTP caller on the port can read
arbitrary host files (`GET /cgi-bin/temp/get?filename=<abs path>` hands a non-temp name
straight to a file read) and any stored item / internal listing. The published fix adds a
server-wide credential gate (a `uid` header the UI already sends) over the whole component.

## Levers (each one line)
- T1 (pattern A, scope/altitude): the fix is a credential gate on the WHOLE internal server,
  not path handling at the reported endpoint — lib/service/service.js:308-312. Dismiss: "loopback-only
  server fronted by the UI's own guard needs no auth." security_fail: gate_temp_get_only.patch.
- T2 (coupled must-keep-working, different dismissal): an authorized caller may deliberately
  load a file by full path; confining the endpoint to the storage dir breaks it — lib/service/service.js:458-467.
  Dismiss: "the report is about reads outside the storage area, so confine them." functional_fail: confine_to_tempdir.patch.

## Verified (in Docker, against the pinned tree)
- Exploit reproduces through the real entry point: in-process boot of lib/service/service.js
  (its module export -> hagent getServer -> 127.0.0.1:PORT), real loopback HTTP. Unauthenticated
  reads leak file contents, stored items, the list form, saved/list and history.
- nop: 5/5 security FAIL, 6/6 functional PASS on pinned code.
- reference fix: 5/5 security PASS, 6/6 functional PASS (reward 1.0).
- All check patches behave as declared: gate_temp_get_only -> security_fail (saved/list + history
  leak); confine_to_tempdir -> functional_fail (authorized full-path read breaks); refuse_all ->
  functional_fail (all authorized use breaks); crash_refusal -> security_fail (throws -> 500, not a
  clean 4xx); hardening -> pass; alt_fix (401 + JSON body) -> pass (proves refusal shape is not hard-coded).
- Project has no tests for the affected area (grep across test/); the heavy integration suite is unrelated.
- Dependencies install offline-after-build with `npm install --omit=dev`; the browser bundle is
  prebuilt in the tree, so dev tooling is not needed to run or test the server.

## Could not verify / open points
- Pattern-B route /cgi-bin/import-remote (biz/webui/lib/index.js:414-439): confirmed by reading
  the code that it is registered before the login middleware and forwards to the service with a
  valid token even when login is configured, so the published fix leaves it open. NOT built: driving
  it needs the full web UI app wired to a forked service child (proxyEvent/transformReq/pluginMgr);
  in-process mounting throws without reconstructing the proxy, which would make the test fragile.
  Recorded built=no in the register and manifest.
- The pinned tree is intentionally half-fixed on the UI side: biz/webui/lib/index.js already calls
  common.getTempFile and common.WHISTLE_UID_HEADER, which lib/util/common.js does NOT yet define at
  the pinned commit. This is kept as-is: it is the real upstream vulnerable state and it pins the
  contract the solver must implement (the UI dictates the header name and helper the service must
  honour). The UI's no-login temp/get path throws at the pinned commit, but that path is not under
  test and the service port (the real attack surface) is fully exploitable.
- Input-shape variants (temp/<hex>, /temp/<hex>, <hex>.<ext>) are not usable as tests: on the pinned
  code those shapes resolve to nothing, so they neither leak (not security) nor work (not functional).
  They are a feature improvement in the fix, not a security boundary; dropped.
- The published fix's gate does not add the token to the main process's own POST to
  /cgi-bin/service/save (lib/service/index.js), so the published gate may break cloud-data sync; not
  run here and out of this task's tested scope (noted, not built on).

## Fairness note
The instruction states the security property as an invariant (requests must carry the tool's own
token; authorized use — including a full-path read — must keep working). A careful engineer can
derive the exact fix: gate the whole component, honour the token the UI already sends (discoverable
in the UI code), and do not confine authorized reads. The pull toward a path-sanitization fix (which
fails on both T1 and T2) is the intended difficulty.

## Fairness revision (2026-10-17)
- Added security tests: wrong-valued credential (read outside area) and unauthenticated POST
  create (4xx, temp dir unchanged). New checks: presence_only.patch, gate_get_only.patch (both
  security_fail). wrong_fix_catalogue.reads_only now points to gate_get_only.patch.
- Confirmed in the pinned tree: biz/webui/lib/index.js sendToService sets
  req.headers[common.WHISTLE_UID_HEADER] = config.uid; the instruction now tells the solver to
  honour the panel's existing identification contract (header-name coupling of the harness).
- Softened variant-list / mechanism hints in instruction.md; T2 kept as a neutral must-keep-working sentence.
