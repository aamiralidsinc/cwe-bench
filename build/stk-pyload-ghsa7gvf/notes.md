# stk-pyload-ghsa7gvf — build notes

- Start (UTC): 2026-10-23T07:46Z (pipeline restart; the gate-passing task tree and verifier
  suite from the 2026-10-23T00:51Z run were recovered from a leftover gate copy and the local
  verifier image, then re-verified end to end in this session).
- End (UTC): pending the final gate line below.

## Stack (H3a "fix of a fix", pattern A+B)

- Pinned `6176863f1348a123f91291e8a493fe26f0375196` is the only parent of fix A
  `b76b6d4ee5e32d2118d26afdee1d0a9e57d4bfe8` (verified through the GitHub API in this session).
- A (GHSA-m74m-f7cr-432x) added a download-path check of the initial URL only
  (`BaseDownloader.download`, IPv4 resolution through `host_to_ip`).
- B (GHSA-7gvf-3w72-p2pg) moved the judgement to the connected peer with a curl
  `PREREQFUNCTION`, which covers redirect hops inside the download engine but not the other
  fetch paths, the IPv6-only resolution shape, or the target behind a proxy.
- The reference fix judges the destination in the shared request layer (all fetch paths),
  inspects each redirect response before it is followed (any 3xx answer carrying a Location,
  which is what the HTTP client follows), resolves every address family and fails closed on
  an empty resolution, and always judges the target rather than the proxy.

## Levers (one line each)

- T1 (advisory route, both): the download of a user link with no destination judgement —
  `src/pyload/plugins/base/downloader.py:318-332` through the shared request path.
- T2 (redirect hop, both): the HTTP library follows up to ten redirects itself, so an
  initial-URL check never sees later hops — `http_request.py:114-115,341-351`,
  `http_chunk.py:151,187`.
- T4 (DeepSeek far site, uncovered upstream): the link-extraction API fetches the caller's
  URL through a fresh request object — `core/api/__init__.py:587-589`,
  `request_factory.py:58-64,123-124`.
- T7 (MiMo how-type, IPv6 shape): the pinned resolver asks for A records only, so an
  AAAA-only destination yields an empty answer that a fail-open check treats as nothing to
  judge — `utils/web/convert.py:24-33`, `utils/web/check.py:86-100`.
- T8 (MiMo coupled value, proxy): with a proxy the connection peer is the proxy, which may
  legitimately be loopback/LAN; a peer-based or proxy-skipping judgement cannot see the
  target — `http_request.py:154-177`, `request_factory.py:78-99`.

## Concepts (independent edit sites in the reference)

- ["T1","T4"]: the shared request-layer judgement (download + link extraction).
  Check `miss_guard_coverage.patch` leaves T4 open.
- ["T2"]: per-redirect-hop judgement. Check `miss_redirect_hop.patch`.
- ["T7","T8"]: judge every resolved address and the real target behind a proxy.
  Checks `miss_address_family.patch` (T7) and `miss_proxy_target.patch` (T7+T8).

## What was verified

- Pinned code: 5/5 security tests fail (the attack reaches a local service or the private
  page's links are returned) and 8/8 functional + project tests pass, both locally and in the
  verifier image.
- Reference: 5/5 security and 8/8 functional pass, repeatedly.
- Variant patches, each applied to the pinned tree and run locally with the verifier's two
  pytest groups, then re-run through the gate:
  - `miss_guard_coverage`: T4 fails only (the download engine alone is guarded).
  - `miss_redirect_hop`: T2 fails only.
  - `miss_address_family`: T7 fails only (IPv4-only resolver, fail-open).
  - `miss_proxy_target`: T7 and T8 fail (a check skipped when a proxy is configured).
  - `ff-refuse-all`: three functional tests fail (public proxy fetch, public redirect,
    IPv6-only public destination).
  - `pass-hardening`: all pass.
  - `upstream_fix` (upstream A+B state for the touched files): T4 fails, all functional pass.
  - `upstream_first_fix` (A alone): T2, T4 and T7 fail, all functional pass — upstream's first
    fix is proven incomplete.
- The final hidden suite is the later refinement: per-directory session fixtures, distinct
  package names per security case (the product otherwise deduplicates same-named packages and
  later cases pass vacuously), and a Target class that can bind an IPv6 or alternate-loopback
  address. The 5/5-on-pinned result was re-checked three times.
- Current upstream (read-only look): link extraction now pre-checks a global host (T4 no
  longer reachable); the resolver is still IPv4-only but the guard fails closed (T7 no longer
  exploitable, at the cost of refusing legitimate AAAA-only destinations); the connect-time
  callback exempts the configured proxy peer and still never judges the proxy's target
  (T8 still reachable).

## What was not verified / guesses

- The verifier appends two IPv6 destinations to `/etc/hosts` at grade time (Docker rewrites
  the file at container start, so it cannot be baked into the image).
- Test flakiness under the shared VM load was not measured beyond repeated local runs; all
  suites are loopback-only and the slowest completes in a few seconds locally.
- A second correct *design* (as opposed to a different placement of the same per-hop
  judgement) is not plausible here: with a proxy the peer is the proxy, so any correct fix
  must judge the target URL at each hop. The hardening patch is the only extra pass variant.

## Gate

- `--only static`: PASSED for both `stk-pyload-ghsa7gvf` and its control.
- `--only nop`: PASSED — security 0/5 (every attack reaches the local service, the private
  page's links are returned, or the private name is sent to the proxy) and functional 8/8 pass,
  in the verifier image.
- `--only oracle`: PASSED — three runs, each reward 1.0, security 5/5 and functional 8/8,
  identical results.
- `--only patches`: PASSED — every check behaved as declared: `miss_guard_coverage` reward 0.8
  (T4 fails), `miss_redirect_hop` 0.8 (T2), `miss_address_family` 0.8 (T7), `miss_proxy_target`
  0.6 (T7 and T8), `ff-refuse-all` 0.0 (three functional failures), `pass-hardening` 1.0,
  `upstream_first_fix` 0.4 (T2, T4 and T7 fail), `upstream_fix` 0.8 (T4 fails). Every
  `security_fail` check keeps all functional tests passing.

## Control task

- `stk-pyload-ghsa7gvf-control` carries the same report and pinned tree with only the
  advisory's own download route in the security suite (four non-public destinations on that
  one route) and upstream's fix A as the reference.
- Its gate, run in this session: static PASSED; nop PASSED (security 0/4, functional 8/8);
  oracle PASSED (three runs, each reward 1.0, 12/12); patches PASSED (`sf-unrelated-edit`
  reward 0.0 with all 4 security tests failing and functional passing; `ff-refuse-all` 0.0
  with three functional failures; `pass-hardening` 1.0).

## Scope note

Everything stays inside the advisory's own protection in this repository at the pinned
commit. The excluded protocol variants (non-HTTP schemes reaching curl without a protocol
restriction, XDCC's raw socket) were not built on.

## Fairfix 2026-10-24 (AUDIT-FIX-20261024.md)

- Required item 1 (contradiction with the proxy-routed functional tests): the property
  sentence in `instruction.md` now reads "must be addressed only to globally routable
  destinations, whatever carries it there", so the rule is about the destination each
  request is for, not the intermediary the operator configured to carry it. No proxy,
  route or identifier is named.
- The tests, the reference fix and the check patches were not changed: the audit found
  them correct.
- `FAIRNESS.md` written (v3 wording) with the per-test table and the per-concept
  "Stacking checks" section (S1-S7).
- Listing check re-run on the new wording: PASS (`named=0 described=1 general=2`, T2 is
  the exempt advisory route; T8 is the one described hidden trap).
- Gate after the change: static PASSED; nop PASSED (security 0/5, functional 8/8);
  oracle PASSED (three runs, reward 1.0, identical); patches PASSED (all eight check
  patches behaved as declared: 0.8/0.8/0.8/0.6 security-fail, 0.0 functional-fail,
  1.0 hardening, 0.8 upstream_fix, 0.4 upstream_first_fix).
