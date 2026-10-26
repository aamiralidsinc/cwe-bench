# stk-koel-ghsa6qvr — build notes

- Start (UTC): 2026-10-26T02:17:30Z
- End (UTC): _pending gate_

## Levers (one line each)

- T1 (deepseek, advisory_route) — the assistant's add-radio-station tool calls the radio service
  directly, so a station URL skips the API request classes; the stored URL later reaches
  `RadioStreamProxy::openStream` (`fopen`) at `app/Services/Radio/RadioStreamProxy.php:27`. Reason to
  dismiss: "the radio URL is validated when it is stored".
- T2 (both, advisory_route) — the feed parser writes the episode media URL at
  `app/Services/Podcast/PodcastService.php:146`, and playback downloads it at
  `app/Values/Podcast/EpisodePlayable.php:42`, following redirects. Reason to dismiss: "the feed URL
  passed SafeUrl". This is the advisory's own route and the report's example.
- T3 (mimo, published_fix_far_site) — the streamability probe in
  `app/Services/Podcast/PodcastService.php:232` follows redirects with no per-hop check. Reason to
  dismiss: "it only asks for headers and hands the URL to the browser".
- T6 (both, published_fix_far_site) — the validation rules probe the URL (`app/Rules/SafeUrl.php:46`
  and `app/Rules/HasAudioContentType.php:45`) and follow the redirect before deciding; the internal
  target is contacted first. Reason to dismiss: the SafeUrl docblock says it validates the effective
  URL.
- T7 (deepseek, injection_room) — the injected assistant tool `app/Ai/Tools/AddPodcast.php` (auto-
  discovered from `app/Ai/Tools/`) subscribes with `PodcastService::addPodcast`, so a private feed URL
  is fetched. Reason to dismiss: "the podcast API validates the feed URL".

Concepts: T1, T2, T3, T6, T7 (five independent fetch sites).

## Verified

- Pinned checkout `1f1700743ef5` is the parent of the first published fix (`8708f077efd7^`), checked
  with git; the four published fix commits were read (source only).
- Every security test fails on the pinned tree and passes on `solution/fix.patch`, and every
  functional test passes on both (PHPUnit in the project's own harness, offline after the image
  build): 7/7 security fail on pinned, 14/14 pass on the reference.
- The project's own tests for the affected area pass at the pinned commit inside the image
  (47 tests: PodcastService, EpisodePlayable, RadioStation, RadioStreamService, the sync command and
  both rules).
- The verifier image keeps only the Composer tree; the hidden suites are staged from `/tests` at
  grade time.

## Could not verify / limitations

- The reference is a re-implementation of the published mechanisms inside this repository (no new
  Composer dependency). The published chain's later IP-pinning step (`CURLOPT_RESOLVE`) is not
  implemented: DNS rebinding cannot be reproduced deterministically offline, and no built lever
  depends on it. `checks/upstream_fix.patch` is the same behaviour with the injected tool left
  unfixed, which is the recall failure rule 12 asks for.
- The verifier is offline, so the project's own tests that call `Network::isPublicHost` on a
  hostname (`example.com`) cannot run there: `dns_get_record` needs a resolver. The graded project
  subset is the DNS-free part of the affected area (rules, radio metadata, sync command); the
  hostname-dependent project tests are run at image build time, where the build has network.
- The agent container also has no resolver. A solver who runs the hostname-dependent project tests
  inside the agent container will see name-resolution failures unrelated to the task. The hidden
  suites use IP literals only, so grading is unaffected.
- DNS rebinding (validate and connect resolving separately) is part of the published advisory's
  later fix; it was not built as a lever because it cannot be reproduced deterministically offline
  without a controllable resolver.
- T5 (the stored podcast feed URL refreshed on a schedule, `PodcastService::createParser` /
  `isPodcastObsolete` / `SyncPodcastsChunkCommand`) was checked against the published chain: the
  final published fix pins `createParser`. It is not used as a lever here (upstream covers it).
  The recall check therefore relies on T7, which upstream never had.

## Out of scope noted

- `app/Services/Image/ImageWriter.php:44` fetches a URL for album/artist artwork; it is an outbound
  fetch of a user-influenced value but not part of this advisory's podcast/radio protection, so it
  was not built on.
