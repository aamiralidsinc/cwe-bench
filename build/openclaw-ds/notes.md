# openclaw-ds — build notes

- Start (UTC): 2026-10-24T03:29:06Z (builder began 03:30Z)
- End (UTC): 2026-10-24T05:32Z
- Slug: openclaw-ds · repo openclaw/openclaw · pinned `62563c2cfc482b8aa9997c16f02dcd453b13c925` · published fix `d4f11d3005a56abc709ebc8e715972593ebed96e`
- Advisory: GHSA-2Q7J-2VHX-56G8 / CVE-2026-62187 — CWE-863, per-account Feishu tool configuration not enforced at execution.
- Track: injected · Pattern A+B · toolchain: Node 22 + pnpm 11.2.2 + vitest 4.1.8.

## Verified on the pinned copy (real registration seam, recording client)

Each line was driven through the plugin's real `registerTool` API, with the Feishu client factory
replaced by a recording proxy (the same seam the project's own tests use).

1. `feishu_doc` with the session account = a (a: doc off, b: doc on) → ran as a (`client.docx.documentBlock.list`).
2. `feishu_doc` with an explicit account naming the documents-off account → ran as it.
3. `feishu_app_scopes` with the session account = a (a: doc on, scopes off) → ran as a (`client.application.scope.list`).
4. `feishu_perm` with the session account = b (b never mentions tools → permissions off by default) → ran as b.
5. No account selected (a: wiki off, b: wiki on) → ran as a (first listed, `client.wiki.space.list`).
6. `feishu_wiki` / `feishu_drive` with the session account = a (off for both) → ran as a.
7. `feishu_drive` add_comment with the session account = a (drive off) → ran as a (`client.request`).
8. `feishu_bitable_*` with a disabled account → already refused at the pinned commit (the module's own
   per-account check is the precedent the published fix copies); therefore bitable's existing tools
   are only exercised in the functional group, never in the security group.
9. Injected siblings: `feishu_chat` with `accountId` naming a chat-off account → ran as it
   (`client.im.chat.get`); `feishu_bitable_batch_create_records` on a bitable-off account → ran as it
   (`client.bitable.appTableRecord.batchCreate`).

## Security property (stated once, in instruction.md)

An assistant operation may only run through a Feishu account whose **effective** configuration allows
the tool being used — however the account was chosen (request, session, or the product's default
selection) and even though the tool is offered because another account allows it. A refused request
returns an error result and performs no Feishu operation. A request that names no account must still
be served by an allowed account when one exists. The effective configuration includes the product's
defaults for settings an account never mentions.

## Levers

| id | pattern | shape | where | reason a solver skips it | security_fail |
|----|---------|-------|-------|--------------------------|---------------|
| T1 | A (how-type: coupled re-selection) | the family setting is applied only when tools are announced; execution uses the selected account whatever its own setting; a no-account request must re-select an allowed account, not refuse | `tool-account.ts:16-71` + every tool call site | refusing the unnamed-account case reads as the safe choice; "the default account is the operator's choice" | sf-miss-gate.patch |
| T2 | A far site (wrong object) | the app-scope diagnostic shares the document module's client helper but is a separate setting; gating it as "documents" is over-broad one way and open the other | `docx.ts:1578-1596` | a read-only diagnostic inside the document module looks covered by the document gate | sf-miss-scopes.patch |
| T3 | injected sibling | the chat tool resolves its own account with the lower-level resolver + client factory and applies no family gate | `chat.ts:139-168` | not one of the modules the report names, registered without a session context, invisible to a search for the shared tool helpers | sf-miss-chat.patch |
| T4 | injected sibling | a bulk Bitable import builds its own long-timeout client and bypasses the module's already-gated helper | `bitable.ts:628-640` | Bitable is the module that already enforces the gate — it reads as the correct precedent, so nobody re-audits it | sf-miss-batch.patch |
| T5 | A (defaults route) | an account that never mentions a family that is off by default is treated as allowed by a guard that only honours an explicit false | `tool-account.ts:51-71` + `tools-config.ts:8-29` | "the account turned nothing off" | sf-miss-defaults.patch |

Couples (functional): no-account requests are still served (T1); an allowed session account keeps
working next to a disallowing one (T1); the diagnostic works when documents are off and documents work
when the diagnostic is off (T2); chat / bulk import / bitable metadata work on an allowed account
(T3/T4/T5).

## Candidates considered and rejected

- `channel.ts:955-1023` channel-info / member-info message actions: real, unmodified upstream code with
  no `tools.chat` check. Dismissed as a test: they are channel message actions governed by
  `channels.feishu.actions`, not agent tool settings; the general property read literally does not
  map them, and a blind engineer could not fairly map them to the chat tool setting. Register row added
  (`not built`).
- `chat.ts` as it stands upstream (first enabled account): its own chat setting *is* honoured, so it is
  not a violation. Instead the per-request migration gap was injected.
- `docx.ts:1389-1396` `getMediaMaxBytes` (published-fix second resolver): same account as the client
  helper, so it cannot be security-distinguished; covered by the document write security test.
- A second bitable resolver helper (screener O8b #2) and a drive comment client that wraps the same
  shared helper: rejected because the gated client is always created first, so the second path has no
  teeth for a disabled account.
- `media.ts`, `send.ts`, `outbound.ts`, `comment-handler.ts`, `pins.ts`, `typing.ts`, `reactions.ts`,
  `directory.ts`: channel runtime paths, not agent tool surfaces — outside this advisory's protection.

## Verification matrix (local, Node 22, the delivered test files)

| tree | security | functional |
|------|----------|------------|
| pinned + injection (nop) | 13 fail (all) | 36 pass |
| reference fix (oracle) | 13 pass | 36 pass |
| sf-miss-gate | 12 fail / 1 pass | 36 pass |
| sf-miss-scopes | 1 fail | 36 pass |
| sf-miss-chat | 1 fail | 36 pass |
| sf-miss-batch | 1 fail | 36 pass |
| sf-miss-defaults | 1 fail | 36 pass |
| uf-doc-only | 8 fail | 36 pass |
| rs-reads-only | 3 fail | 36 pass |
| cs-crash (crash on the refusal path only) | 5 fail | 36 pass |
| ff-noreroute | 13 pass | 1 fail |
| ff-scopes-as-doc | 1 fail | 1 fail |
| adj-registration | 13 fail (tools not registered) | 16 fail |
| pass-hardening | 13 pass | 36 pass |
| pass-alt (family-aware resolver) | 13 pass | 36 pass |

Project tests kept in the functional group: `tool-account-routing`, `docx.account-selection`, `chat`
(25 tests). Excluded on purpose: `drive`, `bitable`, `wiki` (they replace the shared tool-account
module with a fixed export map, so a valid fix that adds a new shared helper would fail for a reason
the report never states) and `tool-account.test.ts` (it calls the shared resolver with no family, which
a valid fix that makes the family mandatory — the direction upstream later took — would break).

## Verified / not verified

- Verified: every behaviour above on the pinned copy; the six original project test files pass at the
  pinned commit with Node 22 (44 tests); the whole pnpm workspace installs and the three kept project
  test files pass on both trees; both patches (`environment/injection.patch`, `solution/fix.patch`)
  apply cleanly to a fresh depth-1 checkout; the pnpm 11 install of the workspace completes in the
  image build.
- Not verified: repo_mb / giant-repo flags (the screener left them null; the depth-1 checkout is
  ~237 MB and `.git` ~59 MB); whether upstream considers `tools.chat` to cover channel message actions
  (route dismissed); recall risk; the target models' behaviour (trials are not run by the builder).
- Outside the advisory's scope, noted not built: an explicit account id naming an account with
  `enabled: false` is still resolved at the pinned commit (the published fix gates only the tool
  family); upstream later added an `enabled` check. Not part of this task's property.

## Gate results

- static: PASSED (2026-10-24T03:51Z; re-run after the final edits). No warnings; the only declared
  patch without a file is `blind.patch`, which the blind-fix step writes.
- nop: PASSED (2026-10-24T04:21Z; 13/13 security tests fail on the pinned+injected tree, 36/36 functional tests pass). A first attempt failed on a verifier-side cache permission (`node_modules/.experimental-vitest-cache`); `test.sh` now hands the runner the cache directories and makes node_modules extensible.
- oracle: PASSED (2026-10-24T04:36Z; three runs, each reward 1.0, 49/49 tests, identical results).
- patches: PASSED (2026-10-24T05:32Z; all 13 checks behaved as declared):
  - security_fail: sf-miss-gate (12 security failing), sf-miss-scopes / sf-miss-chat / sf-miss-batch /
    sf-miss-defaults (1 each), uf-doc-only (8), rs-reads-only (3), cs-crash (5) — every one with all 36
    functional tests passing.
  - functional_fail: ff-noreroute (1 functional), ff-scopes-as-doc (1 security + 1 functional),
    adj-registration (13 security + 17 functional).
  - pass: pass-hardening and pass-alt both reward 1.0 (49/49).
- The verify/execute/score path is offline: both images are built at image-build time (agent image
  8m20s/6.2 GB; verifier image 4m15s/5.4 GB) and every trial runs with no network.

## Environment notes

- The agent image creates the uid-1000 user *before* the checkout and installs as that user, so no
  tree-wide chown over the 3 GB dependency tree is needed (the first attempt spent >10 min copying
  the overlay and was replaced).
- Both images build from the pinned commit (agent image 8m20s / 6.2 GB with the whole pnpm
  workspace; verifier image 4m15s / 5.4 GB including its own pristine tree and node_modules).
- The agent image was smoke-tested as uid 1000 in a clean env: 23 project tests (chat + tool-account
  routing) pass inside the built image.
- The verifier links the image's pristine `node_modules` into the restored workspace; Vite needs to
  write `node_modules/.vite` and `node_modules/.vite-temp`, so `test.sh` hands exactly those two
  directories to the runner user. The restored source tree stays root-owned and world-readable; the
  runner only needs write access to its own output and test directories.
