# stk-gonic-15195 — build notes

## Window

- Start (UTC): 2026-10-26T02:02:55Z (build driver start)
- End (UTC): pending (gate running)

## Advisory and pin

- Advisory: GHSA-2FP4-5V5C-4448 / CVE-2026-49339 / GO-2026-5825 (sentriz/gonic), path traversal in the playlist `id`.
- Pinned (vulnerable) commit: `37090aa71c5e0bb7a322313fc8622c828fd9916b`, the parent of the first published fix.
- Published fixes: `6dd71e6a3c966867ef8c900d359a7df75789f410` (playlist ownership on getPlaylist/deletePlaylist) and `0824bed88f6bbc490ba28bf09d28e5dfeb07b445` (path containment in the store + the inverted create/update load). Neither fix's regression tests are in the pinned tree.
- Pattern: A+B, track stacked (H4). Five independent concepts.

## Levers (one line each)

- T1 (deepseek, uncovered_upstream): playlist cover-art route rebuilds the playlist directory from the raw decoded id, outside the store — `server/ctrlsubsonic/handlers_raw.go:243-270`. Reason to dismiss: it is the image endpoint, not a playlist read, and never touches the store the fix lives in. The published fix leaves it open (recall check fails on it alone).
- T2 (both, published_fix_far_site): create/update ownership load is inverted (`err != nil && pl != nil`), so the guard at the next line never sees the stored playlist — `server/ctrlsubsonic/handlers_playlist.go:79`. Reason to dismiss: the guard is visibly present.
- T3 (deepseek, published_fix_far_site): the store joins whatever relative path it is handed in Read/Write/Delete — `playlist/playlist.go:95,153,206`. Reason to dismiss: a handler-level denial looks sufficient; the store looks like a dumb API. Coupled value: the documented nested `<user>/**/<name>.m3u` layout.
- T4 (both, published_fix_far_site): owner identity parsed from the caller's raw relative path while the operation uses the cleaned path — `playlist/playlist.go:108,209-220`. Reason to dismiss: the first path element names the user and the handlers already compare it. The aliased shape defeats a correct-looking check.
- T5 (mimo, advisory_route): the read route has no ownership decision — `server/ctrlsubsonic/handlers_playlist.go:51-60`. Coupled value: shared playlists stay readable by other listeners.
- T6 (deepseek, advisory_route, not a concept): delete hands the decoded id to the store with no ownership decision — `server/ctrlsubsonic/handlers_playlist.go:177-187`.

Concept groups: [T1], [T2], [T3], [T4], [T5]. T6 is real but easy for both models, so it is a security test only; every concept miss-check keeps its fix. The reader's T7 (nested-path shape) is carried as T3's coupled must-keep-working value.

## Reference fix

Published source changes (store containment helper, cleaned-relative-path identity, create/update load condition, read/write ownership checks) plus a containment call in the playlist cover-art lookup. `solution/fix.patch` is source-only; the published test additions are dropped.

## What was verified on the pinned tree (local, Go 1.27 toolchain, module go 1.26, CGO-free wasm sqlite)

- All six mechanisms reproduce through the product's real HTTP server (`ctrlsubsonic.New` mux and login middleware): cover-art escape serves an outside image; read/create/delete with an escaping id reach outside the storage area; an aliased update rewrites another user's playlist; the read route returns a private playlist to another listener; delete removes another user's playlist.
- Local matrix (security / functional): nop 0/8, 5/5; oracle 8/8, 5/5; upstream_fix 7/8 (cover only), 5/5; miss_cover 7/8, 5/5; miss_create_load 7/8, 5/5; miss_containment 5/8, 5/5; miss_identity 7/8, 5/5; miss_read_owner 7/8, 5/5; sf_reads_only 6/8, 5/5; ff_refuse_all 7/8 + 0/5; ff_nested 8/8 + 4/5; pass_alt 8/8, 5/5; pass_hardening 8/8, 5/5.
- Project tests (`./playlist ./fileutil ./server/ctrlsubsonic`) pass at the pinned commit and on the oracle, upstream fix, alternative fix, hardening and every miss variant.

## Control

`stk-gonic-15195-control`: same pinned code and byte-identical report; security tests cover only the advisory's own route (the playlist read operation in plain, aliased and nested shapes) and its reference fixes only that route plus the resolved-path identity. 4/4 security and 5/5 functional on the control reference; 0/4 and 5/5 on pinned.

## What could not be verified

- The published fix commits' own regression tests were not run against the pinned project tests (not present at the pin by design).
- `present_in_latest` for T1: current origin/master `03e696e` wraps the playlist directory in `SafeJoin`, so the route is contained there; the exact release that introduced that is not recorded.
- Host-level gate results are filled in below when the stages finish.

## Outside scope (not built on)

- `ServeUpdatePlaylist` slices `playlist.Items[:i]` for a client `songIndexToRemove` without a bounds check (panic; unrelated to this advisory's protection).
- `coverForArtist` fetches a remote image URL over HTTP in the same file (a separate SSRF-class concern).

## Gate

- static: PASS (both tasks)
- check_stack: conforming (5 concepts, pattern H4)
- nop: PASS (security 0/8; functional 169/169 — 5 hidden + 164 project), 2026-10-26T02:31Z
- oracle: PASS (3 runs, reward 1.0 each, identical; security 8/8, functional 169/169), 2026-10-26T02:42Z
- patches: running (11 checks, GATE_PARALLEL=4)
