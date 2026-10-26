# stk-matrix-appservice-irc-ghsaw9mh — build notes

Start (UTC): 2026-10-26T02:15:59Z
End (UTC): TBD

## Levers

- **T1 (advisory routes, type both, concept 1)** — reply source entitlement: a referenced message is quoted into IRC even when the referring sender arrived after it; the published fixes' join-time guard must use bridge-observed arrival evidence (cached and fetched references, fabricated arrival time, far-future target time). `src/bridge/MatrixHandler.ts:1284-1304,1323,1359; :388`.
- **T2 (uncovered route, type mimo, concept 2)** — fetched target time: the guard compares against the homeserver-supplied `origin_server_ts`, so a far-future value makes a late joiner look present. `src/bridge/MatrixHandler.ts:1292,1300-1303`.
- **T3 (uncovered route, type deepseek, concept 2)** — fetched event identity: the response's `room_id` is never compared with the requested room and an absent one passes. `src/bridge/MatrixHandler.ts:1288-1304`.
- **T4 (uncovered route, type deepseek, concept 3)** — edit diff: the edit branch resolves the referenced original and emits its removed words with no visibility check; the bridge library's parent-sender check is passed when a lying homeserver answers for the editor. `src/bridge/MatrixHandler.ts:1050-1080; src/util/MessageDiff.ts:38,68`.

Concepts: `[T1]`, `[T2,T3]`, `[T4]` (3 independent concepts; T2/T3 are one fetched-response validation, T4 is a separate sink, T1 is the advisory guard).

## Verified

- Pinned commit `fb339d0c` is the first parent of fix A `4af7d300` (advisory GHSA-wm4w-7h2q-3pf7); fix B `1835e047` (GHSA-w9mh-5x8j-9754) is the follow-up that drops the `origin_server_ts` reliance. Read from the actual commits; the screener/reader records were only leads.
- Every security test fails on the pinned tree (8/8) and passes under the reference fix; every functional test passes on both (47/47, including the project's matrix-to-IRC suite and the message-diff/trim unit specs).
- The reference fix was exercised end-to-end in the verifier image: reward 1.0, 55/55 tests; the pinned tree scores 0.0 with 8 security failures and 0 functional failures.
- Check patches measured locally: `miss_guard` fails T1's four tests; `miss_fetched_evidence` fails T2+T3 (three tests); `miss_edit` fails T4; `upstream_first_fix` fails six security tests; `upstream_fix` fails five; `functional_fail` fails seven functional tests; `crash_refusal`, `wrong_resource`, `one_role`, `check_after` each fail only security tests; `hardening` and `alternative` pass everything.
- The upstream revisions of the fixes were applied with `patch -p1` to the pinned tree for both recall patches and pass the whole functional group.
- Both recall patches fail security (stack adds something beyond upstream).

## Could not verify / notes

- The bridge library (`matrix-appservice-bridge`, a dependency) performs the edit parent-sender check. The edit test simulates a homeserver that answers the library's lookup with the editor's id (as a lying homeserver can); no real homeserver was used (offline task).
- The project's integration spec was taken from fix A's revision: the fix itself had to update six synthetic `origin_server_ts` values in that spec, and using the pinned spec would punish any correct join-time fix. The rest of the project's spec is unchanged.
- The media-preview length arithmetic (screener T5), admin-room authorization (T4) and the sender-membership route (T3) are outside this advisory pair's content-disclosure protection or have no fair behavioural test through the appservice entry point; they are not built (see the manifest's `verified.not_routes_at_pinned`).
- No services; the task is offline. Verifier builds the TypeScript project with the dependency tree baked into the verifier image (yarn install --ignore-scripts plus the matrix-sdk-crypto platform download at image build).
