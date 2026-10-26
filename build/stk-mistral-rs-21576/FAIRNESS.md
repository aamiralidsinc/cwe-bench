# FAIRNESS — stk-mistral-rs-21576

Covering property (P): *"No value supplied in a request may make the server read data from its own
filesystem, or reach an address that is not publicly routable: not its own machine, not its loopback
interface, and not a private or link-local network."* Refusal contract (R): *"a request that would break
the invariant is refused with a client error and has no effect; nothing it names is read, fetched, or
used before the refusal."* Keep-working (K): *"Everything that works today keeps working exactly as today."*

## 1. Test-by-test fairness

| test | asserts | covering sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/security.rs::sec_image_loopback_endpoint_is_refused | chat body image `http://127.0.0.1:port/…` must be `Err`; loopback listener hits 0 | P (loopback) + R (no fetch before refusal) | no | low |
| …::sec_image_loopback_hostname_is_refused | same via `media-preview.internal`→127.0.0.1 | P ("reach an address… not its loopback interface" — the reached address) + R | no | low |
| …::sec_image_server_local_path_is_refused | bare request path refused | P (read its own filesystem) | no | low |
| …::sec_image_server_local_file_url_is_refused | `file://` request value refused | P + R | no | low |
| …::sec_audio_loopback_endpoint_is_refused | audio part, loopback, hits 0 | P is over *any* value in a request | no | low |
| …::sec_audio_server_local_path_is_refused | audio bare path refused | P | no | low |
| …::sec_video_loopback_endpoint_is_refused | video part, loopback, hits 0 | P + R | no | low |
| …::sec_video_server_local_file_url_is_refused | video `file://` refused | P | no | low |
| …::sec_input_file_ipv6_loopback_is_refused | `file_url` `[::1]`, hits 0 | P (loopback) + R | no | low |
| …::sec_input_file_loopback_hostname_is_refused | `file_url` name resolving to loopback | P (address reached) + R | no | low |
| …::sec_input_file_mapped_ipv6_loopback_is_refused | `[::ffff:127.0.0.1]` refused | P (loopback) | no | low |
| …::sec_input_file_server_local_path_is_refused | `file_path` refused (Responses) | P (a request value must not cause a local read) | no | low |
| …::sec_input_file_local_path_chat_surface_is_refused | same on ChatCompletions | P ("in a request", both surfaces) | no | low |
| functional/functional.rs::fun_local_image_bare_path_still_loads | public `parse_image_url(path)` returns 1×1 image | K — an in-process call is not "supplied in a request" | no — but a signature change to the public loader breaks compilation (see Verdict) | medium |
| …::fun_local_image_file_url_still_loads | public loader accepts `file://` | K | no (same qualifier) | medium |
| …::fun_local_audio_data_url_still_loads | public loader accepts data URL | K | no | medium |
| …::fun_local_video_bare_path_still_loads | public `parse_video_url(path,None)` returns frames | K | no (same qualifier) | medium |
| …::fun_server_image_data_url_still_loads | inline image via `parse_request` is `Ok` | K; P forbids only local reads/non-public reach | no | low |
| …::fun_server_audio_data_url_still_loads | inline audio `Ok` | K | no | low |
| …::fun_server_video_data_url_still_loads | inline video `Ok` | K | no | low |
| …::fun_server_file_data_still_loads | inline base64 `file_data` `Ok` | K | no | low |
| …::fun_server_text_only_still_loads | text-only request `Ok` | K | no | low |
| …::fun_server_file_data_url_still_loads | inline attachment data URL `Ok` | K | no | low |

A guard placed in the loaders (reference), in `parse_request` before the load (checks/pass-alt), or in
deserialisation all pass. A guard in the axum handler above `parse_request` is not exercised by the
harness (noted, judged not the natural site: the handler holds no media extraction).

## 2. Leniency (non-blocking)

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| T1 image | guard only `file:`/bare path, leave public-URL SSRF | yes — sec_image_loopback_endpoint, sec_image_loopback_hostname (hits 0) |
| T1 | remove local support from the shared public loader | yes — fun_local_image_bare_path/file_url; checks/ff-local-removed (0.0) |
| T1 | refuse every request-side source incl. data URLs | yes — fun_server_*_data_url, fun_server_file_data*; checks/ff-refuse-all (0.0) |
| T1 | panic instead of returning `Err` | yes — panic fails every `is_err` assert; checks/sf-crash |
| T2 audio | guard the reported kind only | yes — sec_audio_*; checks/sf-image-only (0.8462) |
| T3 video | leave the frame-extraction copy | yes — sec_video_*; checks/sf-no-video-policy (0.8462) |
| T4 attachment URL | keep the literal-host-only guard | yes — three T4 tests; checks/sf-no-input-file-guard (0.7692) |
| T4 | resolve/validate first hop, follow redirects unchecked | **no** (notes admit redirect re-validation is unexercised) |
| T4 | blacklist exactly the three tested literals | **no** |
| T5 | drop local support everywhere | yes — three fun_local_*; ff-local-removed |
| T5 audio | drop local audio support only | **no** — fun_local_audio_data_url uses a data URL |
| T8 | keep `file_path` | yes — 2 tests; checks/sf-no-file-path (0.8462) |
| T8 | blacklist a prefix / confine to cwd | **no** — single `/tmp` fixture |
| P (all) | reject every host/URL, public included | **no** — no positive remote fetch offline (notes admit) |
| R | read/decode then refuse | **no** for local reads — only network contact is observed |
| R | return an internal error, not a client error | **no** — tests assert only `is_err` |

## 3. Hints (non-blocking)

- Title: *"server-local file read through a request image source"* → "server-local data read and
  non-public network access through request-supplied locations".
- *"carries a `file:` URL for a path on the server machine"* → "names a location on the server
  machine".
- *"nothing it names is read, fetched, or used before the refusal"* states the outcome relative to
  the refusal stage → "has no effect — nothing it names is read, fetched, or used at all".

## 3a. Surface descriptions — Required: generalize

none. The instruction names only the reported image route; it never mentions the sibling audio/video
loaders, the attachment URL or the on-disk attachment route, and the invariant is stated once over
every request-supplied value.

## 4. Realism

- T1–T4, T5: real upstream code — three copy-pasted loaders, a real guard that parses bracketed
  `host_str()` and never resolves, and public loaders the CLI uses. Reachable through the real entry
  points.
- T8: plausible product option (read a server-mounted attachment), reachable via
  `parse_request`→`resolve_input_file`, but it exists only because `environment/injection.patch`
  adds it; the one element not taken from upstream. Not signposted by the instruction.
- `mock_state`/`prewarm_*` are grading-time support only; no product effect.

## Stacking checks

| check | concept | result |
|---|---|---|
| S1 coupled traps | C1 media (T1/T2/T3) + T5 | fun_local_* values covered by K; P is scoped to "supplied in a request", so no contradiction — pass |
| S1 | C2 attachment URL (T4) | inline `file_data`/`file_data` URL covered by K; not a local read nor non-public reach — pass |
| S1 | C3 on-disk path (T8) | same inline attachment values; pass |
| S2 shape traps | C1 | refused request shapes are bare path/`file:`/loopback; legitimate request-side set is inline data only; the same path is legitimate only as a direct call — pass |
| S2 | C2 | refused `[::1]`, `[::ffff:127.0.0.1]`, name→loopback; all outside the inline-data set — pass |
| S2 | C3 | refused any `file_path`; outside the inline-data set — pass |
| S3 fixtures/harness | C1 | fixture files are attacker values; harness drives `parse_request` and the public loaders; loader- and dispatcher-level guards both pass |
| S3 | C2 | same; guard in `fetch_file_url` or `parse_request` both pass |
| S3 | C3 | same; guard in `resolve_input_file` or `parse_request` both pass |
| S4 independence | C1 | own tests only; nop fails all 4 media security tests |
| S4 | C2 | own tests only; nop fails all 3 T4 tests |
| S4 | C3 | own tests only; nop fails both T8 tests |
| S5 history | all | `checks/upstream_fix.patch` (published fix) leaves T8 open, so the literal property is still violated — property is not too narrow; patch scores 0.8462 (media + T4 pass) |
| S6 contracts | C1 | `parse_request`/`ChatCompletionParseContext`/public loader names are visible in the repo; residual compile-coupling risk if a correct fix changes those signatures |
| S6 | C2 | `file_url` is an existing visible field |
| S6 | C3 | `file_path` is an existing visible field; T8 is not a wrong-object trap |
| S7 decisive tests | all | no `build/stk-mistral-rs-21576/trial_summary.md` exists — not applicable |

## 5. Verdict

**Gate a — READY.** Every security assertion is the invariant read literally over a value supplied in
a request, on both surfaces the handlers drive; `hits()==0` follows from the refusal clause; refusal is
accepted as any `Err` (no error class demanded); every functional value is covered by K and none is
forbidden by the security rule; the reference (loader policy) and checks/pass-alt (dispatcher
validation, loaders untouched) both reach 23/23. Request-side bare paths are forbidden while the same
path as an in-process call is not "supplied in a request", so fun_local_* is not a contradiction.

**Gate b — quality.** Listed above; none affects readiness.

**Quality to tighten**
1. Add a positive check that a publicly-routable literal (e.g. 93.184.216.34) passes validation, to
   catch "reject every host".
2. Add `fun_local_audio_bare_path`/`file_url` to cover T5's audio loader.
3. Add a second `file_path` shape (relative path in the workspace; another absolute prefix) and a
   private/link-local attachment literal (10.0.0.1, 169.254.169.254) to catch blacklists and
   "confine to cwd".
4. Add a redirect-chain unit test (validator rejects a Location pointing at loopback).
5. Assert the failure is a client error, and observe "no local read" (atime or FIFO), not only zero
   network hits.

**Human review:** confirm that the harness may depend on the unchanged public signatures of
`parse_image_url`/`parse_audio_url`/`parse_video_url` and on `ChatCompletionParseContext`'s field set
under K, and that a guard in the axum handler above `parse_request` need not be exercised.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
