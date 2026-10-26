# FAIRNESS — stk-uri-js-ghsagcv8 (stacked H3a, medialize/URI.js)

Reviewed: `tasks/stk-uri-js-ghsagcv8/instruction.md`, every file under `tests/`, `solution/fix.patch`,
`build/stk-uri-js-ghsagcv8/{manifest.json,notes.md,checks/*.patch}`. Nothing was run.

## Legend (the instruction's one-general-property sentences)

- **P** — "For any URL string that a browser would resolve to a particular host, the library must
  report that same host — the host the browser would actually contact. A URL that a browser would
  resolve to a host must never be reported without that host."
- **K** — "Everything that works correctly today keeps working exactly as today, apart from gaining
  the host described above."
- **WH** — standard expert knowledge, WHATWG URL Standard: a browser strips leading/trailing C0
  control or space, removes all ASCII tab or newline before parsing, reads the authority of a
  browser-special scheme (http, https, ftp, ws, wss) regardless of the slash/backslash run, compares
  schemes ASCII case-insensitively, and treats a scheme-less leading `//` run as an authority.

The harness drives every security case through both public entry points (`URI.parse(s).hostname`
and `new URI(s).hostname()`), and the functional group through the parse fields/accessors plus the
pristine project QUnit suite (`tests/functional/project/`). No refusal form is accepted: a thrown
error fails the case.

## 1. Per-test fairness

`security/cases.js::<id>` rows assert `hostname === evil.example` through both entry points.
`functional/cases.js::<id>` rows assert the pinned parse/accessor values.

| test (file::name) | what it asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| security/cases.js::T1-http-none | `http:evil.example/account` → host `evil.example` (both entry points) | P + WH (special scheme, empty delimiter run) | no — normalising the run for special schemes passes (reference/alt/hardening) | low |
| security/cases.js::T1-http-one-slash | `http:/evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-three-slashes | `http:///evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-five-slashes | five slashes → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-one-backslash | `http:\evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-three-backslashes | three backslashes → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-four-backslashes | four backslashes → `evil.example` | P + WH | no | low |
| security/cases.js::T1-http-mixed-run | `http:/\/evil…` (slash, backslash, slash) → `evil.example` | P + WH | no | low |
| security/cases.js::T1-https-none | `https:evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T1-ftp-one-slash | `ftp:/evil.example/pub` → `evil.example` | P + WH (ftp is a special scheme) | no — the property says any URL a browser resolves, not only http(s) | low |
| security/cases.js::T1-ws-three-slashes | `ws:///evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T1-wss-backslashes | `wss:\\\evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T2-http-upper-none | `HTTP:evil…` → `evil.example` | P + WH (scheme case-insensitive) | no | low |
| security/cases.js::T2-https-upper-slashes | `HTTPS:///evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T2-http-mixed-backslash | `HtTp:\evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T2-ftp-upper | `FTP:evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T2-wss-mixed | `WsS:\\\evil…` → `evil.example` | P + WH | no | low |
| security/cases.js::T3-two-backslashes | `\\evil…` → host `evil.example` **and** `protocol === null` | P (a browser with any web base resolves the leading run to the host) + K (the existing `//` reference parse in `urls.js` 'scheme-relative URL' uses `protocol: null`) | no — rewriting the run to `//` before the existing branch yields both values; a hand-rolled branch leaving `protocol` undefined would fail but is inconsistent with the visible `//` convention | low/medium |
| security/cases.js::T3-three-backslashes | `\\\evil…` → host + `protocol === null` | P + K | no (same note) | low/medium |
| security/cases.js::T3-slash-backslash | `/\evil…` → host + `protocol === null` | P + K | no (same note) | low/medium |
| security/cases.js::T3-backslash-slash | `\/evil…` → host + `protocol === null` | P + K | no (same note) | low/medium |
| security/cases.js::T3-three-slashes | `///evil…` → host + `protocol === null` | P + WH (special-base authority-ignore-slashes) + K | no — a fix that reads `///` as a path is not browser-equivalent under WH (the project also pins `//` as an authority); the correct fix passes | medium |
| security/cases.js::T3-four-slashes | `////evil…` → host + `protocol === null` | P + WH + K | no (same as above) | medium |
| security/cases.js::T5-leading-spaces | `"  http://evil…"` → `evil.example` | P + WH (leading C0/space strip) | no — the standard strip passes | low |
| security/cases.js::T5-leading-tabs | `"\t\thttp://evil…"` → `evil.example` | P + WH | no | low |
| security/cases.js::T5-leading-newline | `"\nhttp://evil…"` → `evil.example` | P + WH | no | low |
| security/cases.js::T5-leading-nul | `"\u0000http://evil…"` → `evil.example` | P + WH (C0 includes NUL; `String.trim()` alone is not the standard strip) | no — a fix doing the standard leading-C0/space strip passes; `.trim()`-only is incomplete, not correct | medium |
| security/cases.js::T5-embedded-tab | `"ht\ttp://evil…"` → `evil.example` | P + WH (all ASCII tab/newline removed) | no — tab removal passes; leading-only trimming is incomplete | medium |
| security/cases.js::T5-embedded-newline | `"http:\n//evil…"` → `evil.example` | P + WH | no | medium |
| security/cases.js::T5-leading-space-no-slashes | `"  http:evil…"` → `evil.example` | P + WH | no for a complete fix; it needs **both** T5 and T1 (cross-concept, see S4) | low |
| functional/cases.js::F-http-basic | pinned parts of `http://evil.example/account` (protocol/host/port/path/query/fragment/user/pass/urn) | K | no — P demands the same host, and normalisation leaves it unchanged | low |
| functional/cases.js::F-https-userinfo | pinned parts of `https://user:pass@example.org:8443/p?q=1#f` | K | no | low |
| functional/cases.js::F-https-userinfo-accessors | same through the accessors | K | no | low |
| functional/cases.js::F-two-backslashes | `http:\\evil…` keeps host `evil.example`, path `/account` | K (P also demands the host) | no | low |
| functional/cases.js::F-slash-backslash | `http:/\evil…` keeps host/path | K (+P) | no | low |
| functional/cases.js::F-scheme-relative | `//evil.example/account` keeps `protocol: null`, host, path | K (+P) | no | low |
| functional/cases.js::F-protocol-case | `HTTP://evil…` keeps stored protocol `HTTP` | K (P constrains only the host; a fix that lowercases the scheme is not K-compliant) | no | low |
| functional/cases.js::F-food-urn | `food:///test/file.csv` keeps `protocol: food`, no host, path | K; P does not demand a host (a browser's host is empty) | no | low |
| functional/cases.js::F-file-url | `file:///foo/bar/baz.html` keeps empty host | K; P does not demand a host (file URLs have an empty host here) | no | low |
| functional/cases.js::F-userinfo-as-urn | `user:pass@www.example.org:123/account` keeps urn/no host | K; browser parses scheme `user` with an opaque path | no | low |
| functional/cases.js::F-mailto | `mailto:…` keeps opaque parse | K; no browser host | no | low |
| functional/cases.js::F-javascript | `javascript:alert(1)` keeps opaque parse | K; no browser host | no | low |
| functional/cases.js::F-custom-scheme | `custom:thing` keeps opaque parse | K; no browser host | no | low |
| functional/cases.js::F-data-uri | `data:text/plain,hello` keeps opaque parse | K; no browser host | no | low |
| functional/cases.js::F-tel | `tel:+123456` keeps opaque parse | K; no browser host | no | low |
| functional/cases.js::F-empty-scheme-authority | `://user:pass@example.org:123/account` keeps host `example.org`, userinfo and port | K pins today's legacy parse; P does not apply because a scheme-less string has no host of its own (with a base a browser would take the base host, which the parser cannot know). A `//`-form normalisation yields the same expected parts | no — only a fix that mangles the empty-scheme form fails (functional_overbroad), and that is caught as wrong; a correct fix passes | low/medium |
| functional/cases.js::F-plain-path | `/foo/bar` keeps no host, `protocol: undefined` | K; the string carries no authority | no | low |
| functional/cases.js::F-path-with-space | `/foo bar/baz` keeps the literal space | K; WH does not remove interior spaces | no — stripping all whitespace is not browser-equivalent and is caught | low |
| functional/cases.js::F-path-with-space-in-url | `http://example.org/a b/c` keeps host and literal path space | K | no | low |
| functional/cases.js::F-round-trip | `new URI('http://example.org/a/b?c=d#e').toString()` unchanged | K | no | low |
| functional/project/{test.js,test_jim.js,test_template.js}::all 166 QUnit cases | the project's own pinned browser suite (parsing fixtures in `urls.js`, mutation, normalisation, resolution, template), including `file:///`, `food:///`, `user:pass@…`, `://…`, `/…`, and the pinned backslash-authority fixtures `https:/\attacker.com`, `http://i.xss.com\…`, `https://attacker.com\@example.com` | K for every pinned value; the backslash fixtures are also browser-consistent under WH | no — reference, alt and hardening are 186/186; only an over-broad normaliser fails them (36 functional failures) | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible WRONG fix | caught? | test / checks evidence |
|---|---|---|---|
| P — report the browser host | fix only the reported zero-delimiter shape, or only exact `://` | yes | 12 T1 cases; `checks/miss_delimiter.patch` (18 security fail) |
| P — report the browser host | lower-case-only special-scheme allowlist (the historical A-only fix) | yes | 5 T2 cases; `checks/miss_case_variant.patch`, `checks/upstream_first_fix.patch` (18 fail) |
| P — never hostless when a browser has a host | leave the scheme-less branch untouched | yes | 6 T3 cases; `checks/miss_scheme_relative.patch` |
| P — never hostless … | fix the delimiter and the scheme-less run but skip WHATWG whitespace (the blind fix is this shape) | yes | 7 T5 cases; `checks/miss_whitespace.patch`; `checks/blind.patch` scores 0.7667 |
| K — keep today's host-less parses (T4) | normalise every scheme's delimiter / give every scheme an authority, or strip all whitespace including spaces | yes | 12 coupled functional cases (F-food-urn, F-file-url, F-userinfo-as-urn, F-mailto, F-javascript, F-custom-scheme, F-data-uri, F-tel, F-empty-scheme-authority, F-plain-path, F-path-with-space, F-path-with-space-in-url) plus the project suite: 36 functional failures; `checks/functional_overbroad.patch` |
| T1 | accept only the first two characters after the colon | yes | T1-* (12); `miss_delimiter.patch` |
| T2 | case-sensitive comparison | yes | T2-* (5); `miss_case_variant.patch` |
| T3 | fix scheme-prefixed input only | yes | T3-* (6); `miss_scheme_relative.patch` |
| T4 | over-broad normalisation (coupled value, no security test by design) | yes | functional cases above; `functional_overbroad.patch` |
| T5 | no whitespace preprocessing / leading-only trim | yes | T5-* (7); `miss_whitespace.patch` |

Catalogue entries `refuse_all`, `crash_as_refusal`, `one_role_or_direction`, `reads_only`,
`missing_authority` and `adjacent_api` are genuinely n/a on a pure string parser with two entry
points and no deny path. `wrong_resource`/`unlisted_route` = `miss_scheme_relative.patch` (caught),
`check_after_adjustment` = `miss_whitespace.patch` (caught), `malformed_identity` =
`miss_case_variant.patch` (caught).

**Wrong fixes no test catches**

1. **Hardcoding the host.** All 30 security cases use the single host `evil.example`; a fix that
   recognises that literal passes every security case and every functional case. Vary the host in
   at least one case per trap (e.g. a second unrelated host in one T1, one T3 and one T5 case).
2. **Host reported, remainder mangled.** `hostCase` asserts only `hostname`; a fix that reports
   `evil.example` but leaves `urn: true`, drops or rewrites `path`/`query`, or serialises
   non-canonically is not caught. Add `path: '/account'` (and `urn: undefined`) to one T1, one T2
   and one T3 case (T3 already checks `protocol`) — keep the values literal.
3. **Trailing-whitespace stripping** is unasserted (browser-correct, so not a wrong fix, and the
   project pins no trailing-space fixture); no action needed.

## 3. Hints (quality, non-blocking)

| quote | why it is a hint | neutral rewording |
|---|---|---|
| "Fix the problem and its close variants." | announces that a variant family exists (a variant list, in general terms) and implies the fix approach is "generalise" | delete; P already quantifies over "any URL string" |
| "Do not special-case the example above." | names the fix approach (do not special-case) and points at the one example | delete; P already covers every URL string |
| "Do not look up the upstream fix." | acceptable constraint; it reveals only that a published fix exists, not where any site lives | keep |
| "Reading the host of `http:evil.example/account` yields nothing … while a browser opens the URL at `evil.example`." | the single reported example; it states the flaw, is not a variant list and does not place a sibling route | keep (the reported case is the task's reason to exist) |

## 3a. Required: generalize

**none.** The only concrete value is the reported example; `listing.json` records T1 as NAMED and
T2–T5 as GENERAL. No sentence describes a sibling, far site or uncovered route, and no general word
is also the name of one stage or entry point. Nothing in the instruction exists only to cover a
trap.

## 4. Realism (quality, non-blocking)

- T1 and T2 are the two published advisory routes on real pinned code (`src/URI.js:523-534`); the
  delimiter check accepting exactly two normalised characters is the maintainer's own code.
- T3 and T5 are real, unmodified upstream branches fixed only in later releases (1.19.11 / 1.19.9),
  untouched by both published fixes. Real by definition; P covers them.
- T4 is not a planted trap: every coupled value is the project's own fixture (`test/urls.js`
  'missing authority', 'ignoring scheme', file://, magnet:, mailto:, etc.). The over-broad fix is a
  realistic maintainer error, and `functional_overbroad.patch` is a plausible scoping mistake.
- The T5 leading-NUL/tab cases are in the standard's preprocessing steps (the reference cites the
  infra spec), not invented. `hardening.patch` (lower-casing `hostProtocols`) is plausible.
- Harness: the hidden suites import the submitted `src/URI.js` (the repo's `main`), never tests from
  `/workspace`; the pristine project tests come from `/tests`. The `/app` copy in the environment
  image is blind-harness plumbing, not product code. No contrived or planted route found.

## Stacking checks

Concepts (`manifest.stacking.concepts`): **C1 = [T1, T2, T4]**, **C2 = [T3]**, **C3 = [T5]**.
History is H3a (A = GHSA-89gv-h8wf-cg8r, fixed ac43ca8; B = GHSA-gcv8-gh4r-25x6, fixed 6ea641c);
there is no dependency-bump (F5) concept.

| check | concept | result |
|---|---|---|
| S1 coupled traps | C1 | T4 values (F-food-urn, F-file-url, F-userinfo-as-urn, F-mailto, F-javascript, F-custom-scheme, F-data-uri, F-tel, F-empty-scheme-authority, F-plain-path, F-path-with-space, F-path-with-space-in-url) plus F-http-basic, F-two-backslashes, F-slash-backslash, F-scheme-relative, F-protocol-case are covered by **K**: "Everything that works correctly today keeps working exactly as today, apart from gaining the host described above." **P** read literally forbids none: food:/// and file:/// have an empty browser host, mailto/javascript/data/tel/custom and `user:pass@…` are opaque, the already-authority forms already carry the host. PASS. |
| S1 | C2 | F-scheme-relative, F-plain-path, F-empty-scheme-authority covered by **K**; **P** forbids none (`/foo/bar` carries no authority, `//evil` carries its host, `://…` is scheme-less). PASS. |
| S1 | C3 | F-path-with-space, F-path-with-space-in-url, F-round-trip covered by **K**; WH removes only ASCII tab/newline, never interior spaces, so **P** forbids none. PASS. |
| S2 shape traps | C1 | The security tests refuse no shape; they accept `\\\\`/`///` runs that the project's own 'scheme-relative URL' and 'backslashes' fixtures establish as legitimate forms. The host-less shapes the functional suite pins are today's legitimate parses (K). PASS. |
| S2 | C2 | `///` and `\\\\` leading runs are browser-equivalent spellings of the project's `//` fixture; no stated legitimate set excludes them. PASS. |
| S2 | C3 | Leading/embedded whitespace is not part of a legitimate URL (WH drops it); the legitimate interior space in F-path-with-space is preserved because WH does not remove interior spaces. PASS. |
| S3 fixtures/harness | C1 | Pure string parse, no setup or privilege state; both public entry points are driven; the harness imports the submitted source. A guard at parse entry, at the protocol branch, or in `parseAuthority` all pass (reference, alt, hardening; the blind fix passes all of T1/T2 at its own layer). PASS. |
| S3 | C2 | Same; the scheme-relative tests use `URI.parse` and the constructor; a fix at either layer passes. PASS. |
| S3 | C3 | Same; the whitespace cases are entry-point strings, passing at any layer that sees the raw input. PASS. |
| S4 independence | C1 | C1 tests pass with C2/C3 unfixed: `upstream_fix.patch` (A+B) passes all of C1 and fails only T3/T5. PASS. |
| S4 | C2 | T3 passes with C1/C3 unfixed: the miss-patch matrix shows only `miss_scheme_relative` failing T3, and it fails no C1 test. PASS. |
| S4 | C3 | **FAIL (attribution only):** `T5-leading-space-no-slashes` also needs T1 — `miss_delimiter.patch` (whitespace + scheme-relative complete, delimiter absent) fails it, and it is the only T5-labelled case that does. A T5-only correct fix therefore misses one T5-labelled test. No complete correct fix is affected. Remedy: re-attribute that case to C1 (`manifest.stacking.concepts` / `traps.T5.security_tests`) or drop it; T5's other six cases cover the concept. |
| S5 history (H3a) | C1 | `checks/upstream_first_fix.patch` violates **P** read literally: `HTTP:evil.example` and `HtTp:\evil…` are browser-resolved hosts it leaves hostless (T2), and it also leaves T3/T5 hostless. The property is wide enough; upstream A alone does not satisfy it. PASS. |
| S5 | C2 | C2 is real unmodified upstream code (later 1.19.11), and P read literally admits it. PASS. |
| S5 | C3 | Same for the 1.19.9/1.19.11 whitespace routes; P read literally admits them. PASS. |
| S6 contracts | C1 | `parts.hostname`, `parts.protocol` and `hostname()` are the library's visible parse fields/accessors (project fixtures use them); the protected object class ("the host the browser would contact") is named in product terms. No fail-open fallback. PASS. |
| S6 | C2 | Same; `protocol === null` is the library's existing scheme-relative representation (fixture 'scheme-relative URL'), not a guess. PASS. |
| S6 | C3 | Same; no new field or function name is needed. PASS. |
| S7 decisive tests | C1 | No `build/<slug>/trial_summary.md` exists. The available `trial_detail_*.json` records only aggregate rewards (deepseek 0.8 and 1.0; mimo 0.5667, 0.8, 0.9); no per-test deciders are recorded. No run is decided by one test (0.9 = 3 security failures). Does not fire. |
| S7 | C2 | Same; the T3 failures recorded for `miss_scheme_relative` are six distinct tests. Does not fire. |
| S7 | C3 | Same; the T5 failures in the blind run are seven distinct tests (leading spaces/tabs/newline/NUL, embedded tab/newline, leading-space-no-slashes). Does not fire. |

Fairfix note: no instruction change is proposed, so `stacking/run_listing_check.sh` was not run. The
S4 remedy is a manifest attribution change only; if the instruction were changed, the fairfix rules
(keep the instruction, change the test and the reference; never add a route sentence; never name a
coupled value) would apply, and the control wording would be re-copied.

## Verdict reasoning

Gate a: **READY**. A complete fix following the primary mechanism — browser-equivalent preprocessing
(special-scheme delimiter run, scheme-relative leading run, WHATWG whitespace steps) — passes
30/30 security and 186/186 functional: the reference (oracle ×3 at 1.0), `alt_correct_fix` 1.0,
`hardening` 1.0, and a recorded deepseek trial at 1.0. P covers T1/T2/T3/T5 literally; K covers
T4's host-less values, which are also browser-consistent. No rule read literally forbids a T4
value. The blind fix on record (0.7667) omits the standard whitespace step: incomplete, not a
correct-fix counter-example. Judgment points: T5 rests on WHATWG expert knowledge the instruction
never names; T3's `protocol === null` mirrors the existing `//` parse; relative and empty-scheme
forms are hostless under the no-base reading of P.

## Required: generalize

**none** (see §3a).

## Quality to tighten

- Re-attribute `T5-leading-space-no-slashes` to C1/T1 or drop it: it also needs T1, so a T5-only
  fix misses one T5-labelled test (`miss_delimiter.patch` proves it). No complete fix is affected.
- `manifest.patch_checks` expects `blind.patch` to pass; the recorded blind run scores 0.7667 with
  7 T5 failures. Reclassify that entry or regenerate the blind fix.
- Leniency: add a second host to the security table (hardcoding `evil.example` currently passes);
  add one `path: '/account'` assertion to a T1/T2/T3 case (a fix that leaves `urn: true` or mangles
  the path currently passes).
- Hints: delete "Fix the problem and its close variants." and "Do not special-case the example
  above."; P already quantifies over every URL string.

Human review: confirm that T5's whitespace route is fair under "standard expert knowledge" though the instruction never names it (the blind fix missed it), that T3's `protocol === null` and the no-base reading of P for relative/empty-scheme forms are acceptable, and that the S4 attribution defect needs only a manifest change, not GATE_A.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
