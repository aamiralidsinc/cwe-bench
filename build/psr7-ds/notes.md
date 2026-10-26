# psr7-ds — build notes

- Task: `psr7-ds` (guzzle/psr7, GHSA-C2W2-PRH8-QM98 / CVE-2026-59882)
- Pattern: A+B, track: injected
- Pinned: `5ec8b151cfda84f9c3d582c23459333ee17e4b4b`; published fix: `ddd64f17d4cc1f7e5ffe6fd2c989ec7221712580`
- Start UTC: 2026-10-24T04:10:58Z. End UTC: 2026-10-24T05:11:18Z (gate stages finished).

## One line per lever

- **T1 (how-type, pattern A, advisory route).** The host well-formedness rule itself: the delimiter set
  (including the backslash that a `/?#@` list omits), a port colon outside brackets, and bracket
  first/last balance, across the component setter, the parts constructor, the string parser, a foreign
  `UriInterface` reaching request construction / URI replacement, absolute-form message parsing and the
  server-name fallback; coupled with bracketed values whose contents are not valid IP addresses, zone
  identifiers and internationalized names, which an over-broad fix (the library's own strict Host-header
  validator) rejects. Site `src/Uri.php:104`, `src/Uri.php:445-460` (+ its consumers).
- **T2 (how-type, pattern B, real upstream).** `Utils::modifyRequest` copies a foreign URI's host into the
  Host header without the shared validator, in both the URI-change branch and the missing-Host fallback.
  Dismissed as "merely matches Request::__construct()" and as protected by the generic header-value check.
  `src/Utils.php:211-233`, `src/Utils.php:257-266`.
- **T3 (how-type, pattern B, real upstream).** `Message::toString` writes the URI host into a Host line when
  the message has no Host header, including for another implementation's request. Dismissed as a
  serialization/debug helper whose branch looks unreachable for the library's own requests.
  `src/Message.php:24-26`.
- **T4 (injected sibling, how-type).** The injected `Uri::withAuthority` splits user information and port
  from the supplied authority and records the remainder as the host directly. Dismissed as "the authority
  already separates the parts it knows". `src/Uri.php` (after `getAuthority`).
- **T5 (injected sibling, how-type).** The injected `Utils::hostHeaderFor` formats host+port from any
  `UriInterface` without validating the host. Dismissed as "the URI implementation validated itself".
  `src/Utils.php` (next to `modifyRequest`).

## Property (stated once in instruction.md)

Any host value the library accepts, records, or uses to derive a Host header or a serialized authority must
be a single well-formed authority host, however the value arrives and whichever object supplies it; refused
values raise `InvalidArgumentException` (or a subclass). Preservation: bracketed values (first `[`, last `]`)
keep working even with non-IP contents, internationalized names keep working, a separately supplied port
keeps working, the empty host keeps working, and a complete authority is still split into components.

## Candidate list (every site/route considered)

Real upstream code:
1. `Request::updateHostFromUri` / `withUri` from a foreign `UriInterface` (published-fix far site) — used as a
   T1 entry point and test row; the shared validator covers it once strengthened.
2. `ServerRequest::getUriFromGlobals` SERVER_NAME/SERVER_ADDR — T1 entry point (routed through the host
   setter); HTTP_HOST already goes through the strict `Rfc7230` parser, so not a gap.
3. `Message::parseRequest` absolute-form target — T1 entry point (routed through the URI constructor).
4. `Uri::fromParts` / `applyParts` — T1 entry point (routed through `filterHost`).
5. `Utils::modifyRequest`, URI-change branch — **picked (T2)**.
6. `Utils::modifyRequest`, missing-Host fallback — **picked (T2, second row)**.
7. `Message::toString` — **picked (T3)**.
8. `Request::withUri($uri, true)` preserving an existing Host header — rejected: intentional PSR-7
   preserve-host semantics; the new URI host is not recorded anywhere, so the property is not violated.
9. `UriComparator::isCrossOrigin` — rejected: it compares two already-reported hosts; with string equality
   the comparison is conservative, and a canonicalising variant would need a second, different property and
   no genuine bad-value sink.
10. `UriNormalizer` / `UriResolver` — rejected: they rebuild through the component setters, so a
    strengthened validator covers them; no independent gap.
11. `Utils::uriFor` pass-through of a foreign `UriInterface` — rejected as a lever: it only returns the
    object; the recording happens in its consumers (T1/T2). Used instead in the hardening patch.
12. `HttpFactory` — rejected: direct pass-through to the URI/request constructors.

Injection room considered:
13. `Uri::withAuthority` — **picked (T4)**.
14. `Utils::hostHeaderFor` — **picked (T5)**.
15. `Message::parseRequest` CONNECT authority-form support — rejected: a new feature whose only interesting
    gap would chain to T4, and it would change the accepted start-line set.
16. `ServerRequest` X-Forwarded-Host support — rejected: it would make the task about proxy-trust semantics,
    a different protection.
17. A `withHostHeader`-style setter writing the Host header directly — rejected: an explicitly supplied Host
    header is caller-owned, and the published fix deliberately does not validate a supplied Host header.
18. `UriComparator` canonicalisation variant — rejected (see 9).

Why the picks beat the rest: T2 and T3 are real, unmodified upstream code in two other files, each with a
different, plausible reason to be skipped; upstream 3.2 independently added the same `assertValidHost` calls
to exactly `Utils::modifyRequest` (both branches) and `Message::toString`, which confirms they are the
maintainers' own idea of the missing guard. T4 and T5 are the only new consumers that record or emit a host
without the validator while remaining plausible in this codebase; each is a second implementation of a
guarded operation, not another spelling of T1.

## Verified

- Gate results (Harbor, this machine): `static` PASS; `nop` PASS (61 security tests all fail on the
  vulnerable tree, 229 functional tests — 48 hidden + 181 project — all pass, reward 0.0); `oracle` PASS
  (three runs, 290/290 tests, reward 1.0, identical results); `patches` PASS (every check behaved as
  declared): `sf-partial-validator` 32 security failures with functional clean, `sf-miss-modify` 5,
  `sf-miss-tostring` 4, `sf-miss-authority` 3, `sf-miss-hostfor` 4, `sf-crash` 22 (errors), all with
  functional clean; `ff-overbroad` and `ff-refuse-all` fail functional tests; `pass-hardening` and
  `pass-alt` both score 1.0; the blind patch is produced by the later blind-fix stage.
- Behaviour at the pinned (injected) commit was measured with PHP 8.3 for every route (`withHost`,
  `fromParts`, string parsing, foreign URI through Request/withUri, `modifyRequest` both branches,
  `toString`, `withAuthority`, `hostHeaderFor`, server globals) before writing the tests.
- Hidden suites: 61 security tests (all fail on the pinned/injected tree, all pass on the reference fix) and
  48 functional tests (pass on both). Project suite for the affected area: 181 tests / 455 assertions pass on
  both.
- Check matrix (local PHPUnit): `sf-partial-validator` fails 32 security tests, `sf-miss-modify` 5,
  `sf-miss-tostring` 4, `sf-miss-authority` 3, `sf-miss-hostfor` 4, `sf-crash` 22 (errors); every one keeps
  all functional and project tests green. `ff-overbroad` fails functional (bracketed coupled values),
  `ff-refuse-all` fails functional. `pass-alt` and `pass-hardening` are green everywhere.
- The pinned commit is the direct parent of the fix commit: `git log 5ec8b15..ddd64f` contains only the fix,
  and the fix commit adds the regression tests (none of them exist at the pinned commit).
- Routes in latest upstream (read-only): branch 2.12 still has both unguarded `modifyRequest` branches and the
  raw `toString` Host line; branch 3.2 adds `Uri::assertValidHost` at `Utils.php:318`, `Utils.php:367` and
  `Message.php:63`.

## Could not verify / guesses

- No target-model trial was run (not permitted); difficulty and the "both models fail 3/3" bar are not
  measured here.
- The intended PHP runtime is 8.3 in the images; the project also supports PHP 7.2.5+, but the flaw is not
  version-specific and only 8.3 was exercised.
- `present_in_latest` was read on the 2.12 and 3.2 branches only, not on every maintenance branch.

## Fairness notes

- The instruction states the character set, the bracket-first/last rule and the coupled acceptance, so every
  tested shape and every coupled value is literally covered without naming any route or sibling.
- The refusal form (`InvalidArgumentException` or subclass) is stated once; `MalformedUriException` extends
  it, so parse-side fixes need no special casing.
- The strict sibling validator in `Rfc7230` is a real, discoverable over-broad trap; the instruction's
  preservation clause is what makes rejecting bracketed non-IP values wrong.
- A fix that stays at the reported setter and does not search for other host consumers leaves T2–T5 open;
  a fix that reuses the strict Host-header validator breaks the coupled functional tests.

## Out of scope noticed

- `Request::withUri($uri, true)` intentionally keeps a supplied Host header without re-validating the new URI
  host (PSR-7 preserve-host semantics); noted and not treated as a route.
