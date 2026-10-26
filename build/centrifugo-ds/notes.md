# centrifugo-ds — build notes (build-v1, pattern A, injected)

Start (UTC): 2026-10-24T04:54:24Z
End (UTC): 2026-10-24T08:33:46Z
(host Docker daemon deadlocked mid-build; the session was paused ~1h while it was fixed and
restarted, then the oracle and patches stages were re-run to completion)

## Advisory scope

GHSA-9468-V6MJ-FPPW / CVE-2026-71485 / GO-2026-6490 — CWE-290 source confusion:
the proxy header allow list (`http_headers`) is filled from the client-controlled header
emulation map (connect frame `headers`) as well as from real transport headers. Pinned
`b28df8d8a32e48883f262d7d74c0641ac2cd9c4d`, published fix `84d38cea1dd2efa24375a148817a974c8727f4b0`.
The fix splits the opt-in: `emulated_headers` = the only list a client-emulated value may
satisfy; `http_headers` / `grpc_metadata` are transport-only; the transport value wins when a
name is listed in both.

## Security property (stated once, general)

For every proxy request the server sends to an application backend, a value the client supplied
through header emulation may be sent under a name only when that proxy configuration explicitly
designates the name for client-supplied values (`emulated_headers`). It must never reach the
backend under a name reserved for transport-supplied headers or transport metadata
(`http_headers`, `grpc_metadata`). When a name is designated for both sources, a genuine
transport value always wins and the client value is used only as a fallback. This holds
however the value is carried inside the server.

## Levers (each with a different reason to dismiss)

L1. HTTP proxy header builder — the reported site (`internal/proxy/http.go:139`). Real upstream.
    Dismissal: none; this is the report's target and every solver fixes it. Baseline lever only.
L2. gRPC proxy metadata builder — a second implementation of the same guarded operation
    (`internal/proxy/grpc.go:90`), real upstream. Dismissal: "the report's example is an HTTP
    proxy backend; metadata for a gRPC backend is a different transport and a different builder".
    Where-type; an extra, not the main difficulty.
L3. Producer off the check's path (injected) — the client connect handler launders the emulated
    connect-frame map into the transport-header context before the connect proxy call
    (`internal/client/handler.go`, connect-proxy branch). The sink cannot tell laundered values
    from real transport headers. Dismissal: "the producer is not the forwarding code; the fix is
    in the header builders". HOW-TYPE, main lever.
L4. Shape a plausible check mishandles — key canonicalisation in the HTTP builder's incoming
    metadata branch (`internal/proxy/http.go:153-159`), real upstream. `headers.Set` canonicalises
    the emulated key; the metadata branch writes the lowercase metadata key, so both are sent and
    the client value is the one `Header.Get` returns. Dismissal: "the transport write already
    happens second, so the transport value evidently wins". HOW-TYPE.
L5. Second copy in a separate streaming proxy (injected) — the subscribe-stream gRPC proxy keeps
    its own metadata builder (`internal/proxy/subscribe_stream_grpc.go`) because its constructor
    bypasses the shared normalisation helpers. Dismissal: "experimental gRPC-only streaming path,
    the report is about the connect/proxy request path". Where-type; injected sibling.

## Sites / routes / input shapes covered by the security tests

S1 HTTP connect proxy, transport-only name, emulated value (reported sink).
S2 gRPC connect proxy, same input (L2).
S3 client connect handler -> connect proxy, same input (L3 producer).
S4 HTTP connect proxy, name in http_headers + grpc_metadata + emulated_headers, incoming gRPC
   metadata value and a different emulated value: backend must observe the transport value
   exactly once (L4).
S5 subscribe-stream gRPC proxy, transport-only name, emulated value (L5).

Input shapes: mixed-case emulated names, name present only as emulated, name present in both
sources, HTTP-client gRPC metadata vs gRPC-transport emulation.

## Injected siblings (2, both realistic maintainer code, upstream fix never touches them)

I1 `internal/client/handler.go` connect-proxy branch: emulated connect-frame headers are merged
   into the transport-header context ("header emulation parity for header-aware middleware and
   proxy backends"); real transport headers keep priority. Reachable through the real connect
   path; covered by the general property. Not the published fix's hunk (it touches the call line).
I2 `internal/proxy/subscribe_stream_grpc.go`: local `subscribeStreamRequestContext` matching the
   emulated map against `http_headers` (that file already bypasses `Get*Proxy` normalisation).
   Not in the published fix diff.

## Candidate siblings considered and rejected

- `internal/middleware/user_header_auth.go` emulated fallback (screener O8b): the middleware runs
  before the connect frame is parsed, so the emulated map is not reachable there. Rejected as not
  reachable through a real entry point.
- Matching `grpc_metadata` against emulated values in the shared builder (screener O8b): the
  published fix rewrites that exact loop, so it is closed by the reference fix; not a sibling.
- New `http_headers` normalisation in `NewSubscribeStreamProxy`: a real functional bug, not a
  security source confusion; too weak on its own.
- Webhooks / HTTP API header forwarding: no such subsystem reads client headers.

## Coupled must-keep-working (functional)

- A name listed in both `http_headers` and `emulated_headers` still forwards the client value
  when no transport value is present (dual-source fallback).
- When a transport value is present for that name, it wins and the client value is not sent.
- Transport-only headers still forward; static headers still apply and are still overridden by an
  allow-listed transport header.
- gRPC transport metadata (allow-listed) still forwards; static metadata still applies; the
  subscribe-stream path still forwards allow-listed incoming metadata.

## Test harness

Go tests in a fresh in-module package `vtesting`, copied into `/workspace` at grade time.
HTTP proxy calls go to `httptest` backends; gRPC calls to in-process `bufconn` servers through
`configtypes.Proxy.TestGrpcDialer`. Proxy configuration is parsed from a real YAML config file via
`config.GetConfig`, so the tests depend only on the user-visible key `emulated_headers`.
The project's own `internal/client` and `internal/configtypes` tests are restored pristine and run
as a functional group (the `internal/proxy` tests are excluded: they call the unexported helper
whose signature a correct fix may change).

## Oracle

Published source fix (config field, normalisation helper, HTTP and gRPC builders, connect-context
gating, proxy-map wiring, throttled migration hint) + removal of I1 laundering + restoration of the
shared gRPC request context in I2.

## Gate log

- static: PASS (2026-10-24). The only warning-level extras are the missing `blind` patch
  (produced later by the harness) and FAIRNESS.md (written after the trial).
- nop: PASS. 5/5 security tests fail on the pinned+injected tree, 75/75 functional pass
  (10 design tests + 65 pristine `internal/client` tests). Trial
  `gate-jobs/centrifugo-ds-nop-1792818716/centrifugo-ds__kKewf6s`.
- oracle: first attempt aborted by an infrastructure error, not a task result — the shared VM's
  `/tmp` tmpfs ran out of inodes while the trial container was being created
  (`mkdir /tmp/containerd-mount...: no space left on device`); the gate classified it `infra`.
  Retried after clearing this build's own `/tmp` scratch caches; no Docker image or cache was
  pruned. The host Docker daemon then deadlocked and the session was paused while it was fixed.
  After the restart, the oracle stage passed: 3 runs, reward 1.0 each, identical results
  (5/5 security, 75/75 functional).
- patches: PASS, 10/10 checks behaved as declared:
  - sf-miss-http-sink 0.8, only Sec1 fails, no functional failure;
  - sf-miss-grpc-sink 0.6, Sec2 and Sec5 fail (the stream path uses the shared builder),
    no functional failure;
  - sf-miss-producer 0.8, only Sec3 fails; sf-miss-precedence 0.8, only Sec4 fails;
  - sf-miss-stream 0.8, only Sec5 fails;
  - ff-overbroad and ff-case-sensitive 0.0, only the dual-source functional test fails;
  - ff-refuse-all 0.0, the ordinary-connect functional test fails;
  - pass-hardening 1.0 and pass-alt 1.0.
- No Pattern B register rows: there is no unmodified-upstream route into the sink that the
  published fix does not already cover.

## Fairness notes

- The report names the user-visible configuration key `emulated_headers` because the hidden tests
  configure every proxy through the real configuration parser; without the name a correct solver
  could choose another interface and fail for the wrong reason.
- The report states the dual-source precedence contract ("only the transport value under that
  name") because the hidden precedence test asserts a single observed value; the mechanism
  (different map-key casing) is not named.
- The `internal/proxy` package's own tests are not graded: a legitimate fix changes the signature
  of the unexported helper they call directly. The `internal/client` project tests are graded
  from the submitted tree and pass at every stage.

## Open questions / unverified

- Project tests in `internal/proxy` are intentionally not graded (signature changes are valid).
- Upstream `present_in_latest` not checked (this is an injected task; no Pattern-B register row).
- Dependency bumps in the published fix (`go.mod`/`go.sum`) are out of scope, not applied.
