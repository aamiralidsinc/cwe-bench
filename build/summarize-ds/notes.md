# summarize-ds — build notes

Start (UTC): 2026-10-19T18:12:38Z
End (UTC): 2026-10-19T19:54:44Z

Candidate: steipete/summarize, GHSA-3VX2-VQX8-JXFG / CVE-2026-53782.
Pinned (vulnerable): `cd3ee48fb24a54aa3a7653ffd84ae38616227377` (verified parent of
`3c5522440c4833dde033e226baa39e6dda1dfc75`). Published fix: `3c552244`.
Pattern A+B, track injected.

## Levers (one line each)
- T1 A base: feed-declared transcript URL fetched with redirect:follow and no address/DNS check — packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:53 (reported; no dismissal).
- T2 A far: daemon's second blocklist misses IPv6 forms embedding an IPv4 address (NAT64/6to4) and reserved ranges — src/daemon/url-fetch-guard.ts:79-98 (dismiss: "the daemon already has an SSRF guard").
- T3 B route: page caption-track URL fetched and returned as transcript text — packages/core/src/content/transcript/providers/generic-embedded.ts:64 (dismiss: "generic HTML provider, not the podcast feature").
- T4 B route: feed enclosure media HEAD/GET fetched unguarded — provider-flow.ts:41-84; media.ts:285-289,306-310,359-362 (dismiss: "the episode audio the user asked to transcribe").
- T5 injected: feed-declared chapter-title JSON fetched unguarded — podcast/chapters.ts:14-35 via provider-flow.ts:18 (dismiss: "optional enrichment, not transcript content").
- T6 injected: Spotify embed-declared transcript URL fetched unguarded — podcast/spotify.ts:70-90; spotify-flow.ts:49-75,303-330 (dismiss: "the Spotify flow already fetches third-party feed data").



## Plan (written before building)

### Product and flaw
`summarize` is a CLI/library (and a background daemon) that turns a link, podcast feed
or HTML page into text plus a summary. The core library's public factory
`createLinkPreviewClient({ fetch })` returns `fetchLinkContent(url)`. Fetching a
podcast feed or HTML page yields attacker-influenced sub-URLs (transcript, caption
track, enclosure, chapters, embedded feed/transcript URLs) which the product fetches
with the caller's transport. At the pinned commit the podcast transcript sink fetches
that URL with `redirect: "follow"` and no scheme/host/address check and no DNS
pinning; the same trust decision is repeated (or omitted) at sibling sinks.

### Levers (each with a different reason a solver would skip it)
1. **BASE (A, reported)** — `packages/core/src/content/transcript/providers/podcast/rss-transcript.ts:53`
   feed `<podcast:transcript url>` fetched via caller's fetch, redirect follow, no
   address/DNS check. Dismiss reason: it is the reported site (no dismissal; control).
2. **FAR (A)** — `src/daemon/url-fetch-guard.ts:79-98`, the daemon's second copy of the
   same blocklist. It already blocks loopback/private/ULA/link-local but misses IPv6
   forms that embed an IPv4 address (NAT64 `64:ff9b::/96`, NAT64 local-use
   `64:ff9b:1::/48`, 6to4 `2002::/16`) and reserved `100::/64`, `2001:2::/16`,
   `3fff::/20`, `5f00::/16`. Dismiss reason: "the daemon already has an SSRF guard".
   Distance: `src/daemon` vs `packages/core`.
3. **UNCOVERED ROUTE (B)** — `packages/core/src/content/transcript/providers/generic-embedded.ts:57-71`
   page `<track src>` captions are fetched and returned as transcript text with no
   redirect/address check. Dismiss reason: "generic HTML provider, not the podcast
   feature the report names". Upstream fix does not touch it.
4. **UNCOVERED ROUTE (B)** — `packages/core/src/content/transcript/providers/podcast/provider-flow.ts:46-61`
   + `podcast/media.ts:285-289,306-310,359-362`, feed `<enclosure url>` media probe
   (HEAD) and download (GET), redirect follow, no address check. Dismiss reason:
   "the enclosure is the episode audio the user asked to transcribe; its bytes are not
   reflected as text". Upstream fix does not touch it.
5. **INJECTED SIBLING S1** — new `podcast/chapters.ts`, called from
   `podcast/provider-flow.ts` (`tryPodcastTranscriptFromFeed`): Podcasting 2.0
   `<podcast:chapters url>` JSON is fetched to load chapter titles, copied from the
   transcript fetch (same decode + `redirect: "follow"`). Dismiss reason: "chapter
   titles are optional enrichment, not transcript content". Upstream fix never touches
   the new file or the call site.
6. **INJECTED SIBLING S2** — new extraction in `podcast/spotify.ts`, fetch in
   `podcast/spotify-flow.ts`: the Spotify embed page's `__NEXT_DATA__` may carry a
   `transcriptUrl`; the Spotify→iTunes flow fetches it before falling back. Dismiss
   reason: "the Spotify flow already fetches third-party feed data, so this looks like
   normal flow data". Upstream fix never touches these files.

(Apple page embedded `feedUrl` was considered as an upstream-uncovered route; dropped
because `fetchLinkContent` short-circuits Apple Podcasts URLs with no HTML, so the
route is not reachable through the public entry point.)

### Coupled must-keep-working behaviour (functional tests)
- Public transcript URLs still fetched and returned, for hostnames resolving to public
  addresses and for public IP literals (plain string URL forms).
- Public→public redirect chains still followed (redirect: "follow" behaviour kept).
- Public caption tracks still fetched and returned.
- Public enclosure media still probed/downloaded.
- Public chapter metadata still fetched (sibling feature).
- Public Spotify embed transcript still returned.
- Daemon URL mode still accepts public URLs, including public-NAT64 (`64:ff9b::/96`
  mapping a public IPv4) and ordinary public IPv6; over-blocking the whole NAT64
  prefix is a functional failure.
- The project's own podcast/daemon tests still pass.

### Trust decision and producer
The trust decision is "may this feed/page-derived URL be fetched?" It recurs at six
sinks. The producer is the feed/page parser (`decodeXmlEntities` + regex extraction for
the RSS and chapter URLs, `cheerio` for the caption track, the embed JSON for Spotify);
the check runs on the produced value, not on the raw markup.

### Test shapes (security)
- IPv4 literal in private ranges (loopback, private, link-local/metadata).
- IPv6 literal (loopback/ULA/link-local) and IPv6 forms embedding IPv4
  (IPv4-mapped, NAT64, 6to4) at the daemon far site.
- Hostname whose DNS answer is private (via `/etc/hosts` + a local DNS server).
- Hostname with no DNS answer (fail closed).
- Public first hop redirecting to a private target.
- The same shapes at the caption, enclosure, chapters and Spotify sinks.
Every assertion is "no transport call to a non-public destination, and no result
derived from one"; daemon refusals accept any 4xx (never one exact status).

### Functional shapes
Public hostnames, public IP literals, public redirects, public versions of every
sibling route, daemon public/NAT64-public, plus the project's own tests.

### Rejected variants
- XML-entity-encoded URLs: encoding variant (forbidden).
- Redirect-count exhaustion: resource-exhaustion trap (forbidden).
- DNS rebinding between check and connect: cannot be behaviourally tested offline
  through an injected transport without prescribing one pinning design.
- run-metrics/CLI wrapper and client default-fetch wrapper: composition sites whose
  only observable difference is the project's private pinning protocol; not fair.
- Apple embedded feedUrl and yt-dlp fetches: not reachable through the named public
  entry point.

## Verification log
- Pinned commit is the direct parent of the fix: verified with `git cat-file`.
- Project tests at pinned (`transcript.podcast-provider*.test.ts`,
  `daemon.url-fetch-guard.test.ts`): 25/25 pass on Node 24 in the scratch tree.
- Flaw reproduced at every lever through the real entry point (local, Node 24):
  - library public API `createLinkPreviewClient({fetch}).fetchLinkContent(feedUrl)`:
    feed transcript (IPv4, IPv6, DNS-private, redirect-to-private), page caption track,
    feed enclosure media (HEAD), feed chapters (injected), Spotify embed transcript
    (injected) each made the transport call the non-public destination on the
    pinned+injected tree;
  - daemon `POST /v1/summarize` (mode=url, extractOnly) with NAT64/6to4 loopback
    literals returned a non-4xx and reached the transport on the pinned+injected tree.
- Local verifier results (19 hidden tests + 25 project tests):
  - nop (pinned+injected): security 0/10, functional 9/9 + project 25/25.
  - oracle: security 10/10, functional 9/9 + project 25/25.
  - no-op alternative design (`pass_alt_fix.patch`, a single guarded transport in the
    content client instead of per-sink guards): 19/19 hidden tests pass.
  - check patches verified locally: `sf_miss_base` (4 transcript tests fail),
    `sf_miss_daemon` (2 daemon tests fail), `sf_miss_caption`, `sf_miss_enclosure`,
    `sf_miss_chapters`, `sf_miss_spotify` (exactly their own security test fails;
    all functional pass), `sf_media_head` (enclosure test fails),
    `sf_malformed_ipv6` (IPv6 literal test fails), `sf_crash_as_refusal` (both daemon
    tests fail on the 500 response), `ff_refuse_all` and `ff_overbroad_nat64`
    (functional failures), `pass_hardening`.
- Environment image builds (`node:24-bookworm-slim`, pnpm 10.33.2, 506 MB); a
  `--network none` container run of `tests/test.sh` reproduced nop = reward 0.0 with
  security 0/10 and all functional + project tests passing, and with the reference
  patch = all groups passing.
- All patches (`solution/fix.patch` and every `checks/*.patch`) apply cleanly to the
  injected tree with `patch -p1`.

## What could not be verified
- Whether the upstream maintainers consider the uncovered routes in scope: the fix
  (3c552244) does not touch them and a read-only look at current upstream still leaves
  them unguarded.
- The project's own tests for the affected area were run offline with the name
  resolution table in `tests/hosts.list`; without that table a fail-closed resolver
  would (correctly) treat the project tests' public host names as unresolvable.
- Total builder time: start 2026-10-19T18:12:38Z, end 2026-10-19T19:54:44Z.

## Gate results
- `--only static`: only the two allowed remaining items (missing `blind` pass patch and
  `build/summarize-ds/FAIRNESS.md`); no other problems (no leaks, no exact-status
  assertions, no test code in `environment/`).
- `--only nop`: PASSED — security 0/10, functional 34/34 (9 hidden + 25 project).
- `--only oracle`: PASSED — 3 runs, each reward 1.0, identical results.
- `--only patches`: PASSED — all 13 declared checks behave as declared:
  - 9 `security_fail`: `sf_miss_base` (4 security fail), `sf_miss_daemon` (2),
    `sf_miss_caption`, `sf_miss_enclosure`, `sf_miss_chapters`, `sf_miss_spotify`,
    `sf_media_head`, `sf_malformed_ipv6` (1 each), `sf_crash_as_refusal` (2); all
    functional pass in every case.
  - 2 `functional_fail`: `ff_refuse_all` (23 functional fail), `ff_overbroad_nat64`
    (1 functional fail).
  - 2 `pass`: `pass_hardening` and `pass_alt_fix` (a central-transport design with a
    different shape from the reference), both reward 1.0.
- Infrastructure note: the patches stage hit the shared-VM Docker network race
  ("failed to set up container networking: network ... not found") on attempts 1-11;
  attempt 12 completed all 13 checks. The gate's nop and oracle stages passed without
  retries. This is the known concurrent-gate network-prune flake, not a task failure.



## Upgrade 2026-10-20 (sibling-injection compliance, §2–§8)

- instruction.md rewritten to state the invariant once over the protected destinations, with no
  route, object kind, operation, format, entry-point name, or list. Product-level description and
  the four contracts (refusal form, resolution/redirect evaluation, public-use preservation,
  close variants) are kept; every route-naming sentence was removed.
- Levers unchanged in number; the task already has HOW-type levers: the page-declared caption
  route and the feed-declared media route are routes where the upstream fix never added any
  protection (M4), and the daemon's IPv6 blocklist is a shape/parser differential (M8) coupled to
  the public-NAT64 legitimate value (M11).
- Coverage added: security/og_audio_private.test.ts exercises the feed-declared audio metadata
  destination, a further real route that reaches the shared media probe/download helper from a
  different caller. It fails on the pinned tree (HEAD + GET to loopback) and passes on the
  reference fix. checks/sf_miss_og_audio.patch is the reference fix without the shared media guard
  plus a call-site guard for the reported media call: only the new test fails against it
  (verified locally; enclosure/transcript security tests still pass).
- No repository or environment code changed, so no image rebuild is needed. solution/fix.patch
  already closes the new route through the shared media guard; verified by running the new test
  against the oracle tree (pass) and the pinned tree (fail).
