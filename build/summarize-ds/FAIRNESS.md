# FAIRNESS review — summarize-ds

Quoted shorthand: **P** = "No connection the product opens in the course of summarizing may target anything other than a public internet destination … and … every address named by the material it retrieves"; **D** = "The decision must be made on the destination the connection would actually use, after name resolution and after any redirect"; **F** = "A refused connection must happen before the connection is opened and must be visible … a client error (4xx) where the product runs as a service"; **L** = "Legitimate use must keep working exactly as today."; **N** = "Loopback, private, link-local … and other non-public ranges are not public internet destinations."

## 1. Test fairness

| Test (file::name) | Asserts | Covering instruction sentence / expert knowledge | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/transcript_loopback::loopback | no transport call to `127.0.0.1:9` for a feed-declared transcript | P (retrieved material) + N | no — target guard runs before transport | low |
| security/transcript_ipv6::ULA | no call to `[fd00::1]` | P + N ("private") | no | low |
| security/transcript_resolved_private::name→loopback | no call when a name resolves to loopback | D ("after name resolution") | no — verifier supplies both `/etc/hosts` and a local DNS server | low |
| security/transcript_redirect_private::public→metadata | no call to `169.254.169.254` after a 302 | D + N ("link-local") | no | low |
| security/caption_track_private::page track | no call to loopback from page material | P | no | low |
| security/enclosure_media_private::HEAD+GET | no HEAD/GET to `10.1.2.3` | P | no | low |
| security/chapters_private::feed chapters | no call to loopback chapter JSON | P | no | low |
| security/spotify_embed_private::embed transcript | no call to loopback transcript | P | no | low |
| security/og_audio_private::feed audio | no HEAD/GET to loopback audio | P | no | low |
| security/daemon_nat64::NAT64 loopback | 4xx and no call for `[64:ff9b::7f00:1]` | P + D + F + N; "a form whose value embeds an IPv4 address" | no | low |
| security/daemon_6to4::6to4 loopback | 4xx and no call for `[2002:7f00:1::]` | P + D + F + N | no | low |
| functional/transcript_public_name::public name | URL fetched, marker returned | L | no | low |
| functional/transcript_public_literal::public IP | URL fetched, marker returned | L | no | low |
| functional/transcript_public_redirect::public→public | both hops fetched, marker returned | L ("redirect chains that stay on public") | no | low |
| functional/caption_public::public track | URL fetched, marker returned | L | no | low |
| functional/enclosure_public::public media | enclosure URL fetched, no non-public call | L | no | low |
| functional/chapters_public::public chapters | chapters URL fetched | L | no | low |
| functional/spotify_public::public embed transcript | URL fetched, marker returned | L | no | low |
| functional/daemon_public::public page | 2xx, page fetched | L | no | low |
| functional/daemon_public::public NAT64 | 2xx, `[64:ff9b::808:808]` fetched | L + "IPv6 forms whose embedded address is public" | no — whole-prefix blocking is over-block, not a correct fix | low |
| project/transcript.podcast-provider.pristine (13 its) | RSS transcript, enclosure, Spotify, og:audio still work | L | no — all hosts in `hosts.list` | low |
| project/transcript.podcast-provider.podcast-transcript.pristine (2 its) | RSS transcript still works | L | no | low |
| project/transcript.podcast-provider.paths-coverage.pristine (5 its) | includes og:audio preview transcription; deleting the route fails | L | no | low |
| project/daemon.url-fetch-guard.pristine (5 its) | keeps existing `redirect:"manual"` + `dispatcher` pinning, no lookup for IP literals | L; test is visible in the repo | no — a refactor away from the existing pinning breaks a visible repo test, so it is not a "correct" fix | low/medium |

Hidden project files are grouped per file; the solver can read the pristine copies in `/app/tests`.

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| all sinks | guard only the reported feed-transcript sink | yes — sibling tests; `checks/sf_miss_base.patch` leaves four transcript tests failing, `sf_miss_caption`/`enclosure`/`chapters`/`spotify` show each sibling |
| T1 base transcript | denylist supplied text (`localhost`, `127.`) | yes — `transcript_ipv6`, `transcript_resolved_private`, `transcript_redirect_private`; `sf_miss_base` |
| T2 daemon blocklist | add NAT64 only, forget 6to4 | yes — `daemon_6to4`; `sf_miss_daemon` |
| T2 adjacent overblock | reject all of `64:ff9b::/96` | yes — `functional/daemon_public` public NAT64; `ff_overbroad_nat64` |
| T3 caption | guard podcast sinks only | yes — `caption_track_private`; `sf_miss_caption` |
| T4 enclosure | guard GET download, not HEAD probe | yes — `enclosure_media_private` asserts the HEAD call too; `sf_media_head` |
| T5 chapters | guard transcript/enclosure only | yes — `chapters_private`; `sf_miss_chapters` |
| T6 spotify | guard feed/iTunes fetches only | yes — `spotify_embed_private`; `sf_miss_spotify` |
| T7 og:audio | guard the enclosure call site, not the shared media helper | yes — `og_audio_private`; `sf_miss_og_audio` |
| refusal form | daemon returns 500 on refusal | yes — both daemon tests; `sf_crash_as_refusal` |
| legitimate use | refuse everything | yes — all functional tests; `ff_refuse_all` |
| identity | no IPv6 parsing (falls through as public) | yes — `transcript_ipv6`; `sf_malformed_ipv6` |

Wrong fixes no test catches:

1. **Fail-open on DNS error** — `INTERNAL.unresolvable` is defined in `helpers.ts` but never used; a guard that allows on lookup failure passes.
2. **Non-http(s) schemes** — no `file:`, `data:` or `ftp:` case; such a guard passes.
3. **IPv4-mapped IPv6** (`::ffff:127.0.0.1`) at a library sink — untested; only the daemon guard's own unit test covers the form.
4. **Refusal reported as success in library mode** — all library security tests do `.catch(() => undefined)` and never inspect the result; a fix that skips the fetch but returns a successful/empty result passes.
5. **Redirect chains longer than one hop** — only public→private in one hop is tested; a fix that validates hop 1 then auto-follows the rest passes.
6. **Public 6to4** — the instruction preserves "IPv6 forms whose embedded address is public", but `helpers.isPublicIpv6` classifies all `2002::/16` as non-public; add no such functional case without fixing the helper.

## 3. Hints

- "it holds however that address is supplied: as a literal in any accepted IPv4 or IPv6 form, including a form whose value embeds an IPv4 address; as a name whose resolution yields such an address; or at any hop of a redirect chain" — variant list. Neutral: *"…however the address is supplied; the decision is made on the destination the connection would actually use, not on the text that was supplied."*
- "Loopback, private, link-local, carrier-grade-NAT, multicast, documentation, and other non-public ranges are not public internet destinations." — range list. Neutral: *"Any address that is not reachable from the public internet is not a public internet destination."*
- "The same connection is opened when the address the user supplied is itself written in a form that denotes such a destination." — restates the supplied-address sink; delete (P already covers it).
- "It can be used directly by a caller and also runs as a background service." — names the two channels; see 3a.

No file, function, mechanism, fix-approach or flaw-count hint is present; "The observed case is one instance, not the full set" is a coverage requirement, not a count.

## 4. Realism

T1–T4 and T7 are real, unmodified pinned code reachable through the real entry points; T2/T3/T4/T7 are routes the published fix left open, realistic by definition. T5/T6 (injected) read like ordinary copied code and are reachable through a real feed / Spotify episode URL. One flag: `og_audio_private` feeds a bare `<meta property="og:audio">` inside an RSS item. The real extractor scans raw feed text so it is reachable, but the fixture looks synthetic; a page URL or a `content:encoded` block carrying that HTML would read better. No other trap looks planted.

## Verdict

READY. Every hidden and project test is passable by a correct fix following the primary mechanism (destination check after resolution and after redirects, refusal visible): the reference, `pass_alt_fix` (central guarded transport) and `pass_hardening` (transcript-entry guard plus sinks) all pass, so the tests are not tied to one layer and no test demands one error class or bypasses a valid layer. The only doubtful "correct-fix" shapes are (i) a per-sink guard resolving with `dns.resolve*`, which ignores `/etc/hosts` and therefore fails the 25 project tests even though the hidden setup serves c-ares, and (ii) a dispatcher-only guard below the injectable transport. Neither is a natural correct fix under D ("the destination the connection would actually use") and the product's injectable-`fetch` boundary, so they do not set NOT READY; they are recorded for human confirmation.

### Required: generalize (step 3a; not a gate-a reason)

- "It can be used directly by a caller and also runs as a background service." → keep only a generic refusal contract: *"A refusal must be visible to the caller: an error or an absent optional result, or, where the invocation returns an HTTP response, a client error (4xx)."*
- "While processing a link it may retrieve further material that the link or the content it names points to." → delete; P already covers every connection, including those to addresses named by retrieved material.
- "The same connection is opened when the address the user supplied is itself written in a form that denotes such a destination." → delete.
- "including a form whose value embeds an IPv4 address" → fold into *"whatever form the address is supplied in"*.
- "Public host names, public IP literals, including IPv6 forms whose embedded address is public, and redirect chains that stay on public destinations must still be fetched, and everything the product derives from them must keep working." → *"Every destination that is public today must still be fetched, and everything the product derives from it must keep working."*

### Quality to tighten

- Add to one library security test a result assertion (rejection or absent optional result), closing leniency 4.
- Use `INTERNAL.unresolvable` in a security test, closing leniency 1.
- Add a non-http(s) scheme test, an IPv4-mapped IPv6 test, and a public→public→private redirect test, closing leniency 2, 3 and 5.
- Rebuild `og_audio_private` from a page URL or `content:encoded` HTML.
- Make the project-test run serve the same DNS table for c-ares (or state in the task that resolution follows the transport's resolver), removing the `dns.resolve*` asymmetry.

Human review: confirm that a per-sink guard resolving via `dns.resolve*` (passes hidden tests, fails the 25 project tests) is not intended as a correct fix, and that the injectable `fetch` boundary is the intended guard layer.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
