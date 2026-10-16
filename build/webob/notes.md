# webob — build notes

## What I verified against the real code (not the reader's notes)

- **Flaw, confirmed.** At the vulnerable parent commit `54c1133`, on CPython
  3.11, a redirect target beginning with a stripped-away leading character
  (ASCII space, C0 control, tab) is rewritten to an attacker host when the
  library makes it absolute. Reproduced through three public entry points.

- **Three call sites, confirmed** (the reader guessed 3 + a new util helper):
  1. `Response._make_location_absolute` (the `Location` header path). At the
     parent it strips `\t\r\n` and guards `scheme:` / leading `//`, then calls
     `urllib.parse.urljoin`, which strips *leading space / C0 control* — so
     ` //host` and `\x01//host` and ` https://host` slip through.
  2. The `_HTTPMove`-based HTTP redirect exceptions' WSGI `__call__` — at the
     parent this calls `urllib.parse.urljoin` **directly with no scheme/`//`
     guard at all**, so even a bare `//host` redirects off-site here. (It then
     passes through `_make_location_absolute` via `Response.__call__`, which
     returns an already-absolute off-host URL unchanged.)
  3. `Request.relative_url` — calls `urllib.parse.urljoin` directly.
  The upstream fix replaces the stdlib join with its own RFC-3986 `urljoin` in
  `util.py` and routes all three sites through it.

- **Tempting wrong fix, confirmed and used as the `security_fail` patch.**
  `shallow_strip_one_site.patch` strips leading C0/space in the `Location`
  path only. It leaves the exception path and the relative-resolution path
  exposed, and it is *still* wrong even on the Location path for the
  ` https://host` variant: stripping turns that into an absolute URL the
  scheme guard then trusts. 8 of 10 security tests still fail; all functional
  pass.

- **A `//host`-on-`relative_url` value is NOT part of the vuln.** The upstream
  fix (correctly, per RFC 3986) still resolves a bare protocol-relative
  reference to that host through `relative_url`. So I did not assert anything
  about bare `//` on the relative-resolution path — only the
  whitespace/control-smuggling variants, which the fix does neutralise there.

## Test design

- 10 security tests across the 3 entry points × {leading space, leading C0
  control, leading tab, bare `//` (exception path only), leading space before
  scheme}. Each asserts the browser-visible target stays on the request host.
- 8 functional tests: absolute off-site URL preserved (Response + exception),
  absolute same-site path, relative resolution under the current dir,
  protocol-relative value kept on-host, `to_application` resolution.
- Assertions are property-based (host must not be the attacker host / must be
  the request host), not exact-string, so an independent correct fix also
  scores 1.0 — proven by `alt_percent_encode.patch` (a different-layer fix
  that percent-encodes leading strippable characters and routes all three
  sites through one helper): 18/18.
- `force_same_host.patch` (functional_fail) forces every resolved redirect
  back onto the request host, which kills the legitimate off-site-redirect
  feature: 3 functional tests fail.

## Could not fully verify / caveats

- Only ran the gate's logic locally with pytest from source on CPython 3.11
  before the Docker gate; the authoritative result is the gate run itself.
- The flaw is Python-version dependent (needs the 3.10+ url-join stripping),
  which is why the image pins `python:3.11-slim`. On 3.9 the exploit does not
  reproduce.

## 2026-10-16 test repair

Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Items from `lenient_items_2026-10-16.txt`
(REC lines only, no `==` section), `research/own-runs/TEST-REPAIRS.md ## webob`, and the caller's note.

| Item | Decision |
|---|---|
| deepseek-1014 / mimo-1014 (ksABBkj): image ships upstream GHSA-6hx8 regression tests | already fixed: the image now builds `b240857` (parent of the commit that added those tests), see task.toml |
| mimo-r11 (CeNzGqe) #1: `test_exception_bare_protocol_relative` is outside the instruction | already fixed: the test was removed earlier today (CeNzGqe regraded 1.0 at 02:47Z) |
| mimo-r11 #2: exception path still sends an explicit bare `//host` off-site | skip: the instruction excludes explicit protocol-relative targets from the same-site guarantee and makes no "as today" promise for that path; grading it would first need an instruction change, and both behaviours are reasonable |
| deepseek-r12: confirm later runs use `b240857` | already fixed (task.toml, Dockerfile) |
| mimo-r12 (GTgqHjZ): `Request.relative_url('//other.host/x')` is rewritten onto the request host and no test checks it | **fix**: new functional test |

### Why the relative_url item is fair
- The security bullet covers only targets the app "would regard as same-site (one that is not an
  explicitly absolute URL and is not an explicitly protocol-relative reference)". A bare `//host` is
  explicitly protocol-relative, so the security property does not cover it and gives no reason to change it.
- The preservation bullet says "a reference resolved relative to the current request must resolve
  exactly as it does today". Today (and with the reference fix) `relative_url('//other.example.com/x')`
  gives `http://other.example.com/x`. An agent can check this by running the vulnerable code.
- Three of the four blind model fixes read it this way and kept explicit `//` on `relative_url`
  (deepseek r11 and mimo r11 `allow_protocol_relative=True`, deepseek r12 `neutralize_protocol_relative=False`).
  Only mimo r12 folded it.
- The test asserts only the host and path, both computed in the test. It uses no product helpers and no exact strings.

New test: `tests/functional/test_redirect_feature.py::test_relative_url_explicit_protocol_relative_unchanged`.

### Patch checks
- The old `alt_percent_encode.patch` (`pass`) also folded explicit `//` in `relative_url`, so it broke
  the promise above and failed the new test. It is kept verbatim as the new bite check
  `relative_url_folds_protocol_relative.patch` (`functional_fail`; fails only the new test).
- `alt_percent_encode.patch` (`pass`) is amended: `safe_urljoin(..., fold_protocol_relative=True)`,
  with `relative_url` passing `False`. The design is otherwise unchanged (percent-encode at a different layer). It scores 1.0.
- Before the gate, a local Docker run of the hidden tests gave: reference 18/18, amended alt 18/18,
  bite 17/18 (new test only), vulnerable code security 0/9 with functional 9/9, shallow and force_same_host as before.

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py webob` gave **PASSED** (log `gate-20261016c.log`).
All 4 patch checks are ok. Hardening and blind checks are not required for this pre-2026-10-16 task, and none exist.

### Regrade (`regrade_from_code.py`, 2026-10-16 ~05:08Z)
| trial | old | new | failing tests |
|---|---|---|---|
| deepseek-r11 eSAv3oh | 0.9 (verifier; failed only the since-removed bare-// test, never regraded) | 1.0 | none |
| deepseek-r12 eebKwUc | 1.0 | 1.0 | none |
| mimo-r11 CeNzGqe | 1.0 (regrade 02:47Z) | 1.0 | none |
| mimo-r12 GTgqHjZ | 1.0 | **0.0** | `test_relative_url_explicit_protocol_relative_unchanged` |

The drop is genuine. In `final-code/changes.patch` (util.py), `safe_urljoin` handles anything without a
scheme with `if value.startswith('//') or SCHEME_RE.search(value): value = '/%2f{}'...`, and
`relative_url` calls it with no opt-out. So `relative_url('//other.example.com/x')` gives
`http://localhost/%2fother.example.com/x`. The model's own test asserts this new behaviour. This
changes a result the instruction says must stay "exactly as it does today". It is not a security defect,
but it is a functional regression, and the scorer forces any functional failure to 0.
