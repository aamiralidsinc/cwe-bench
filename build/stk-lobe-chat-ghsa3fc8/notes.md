# stk-lobe-chat-ghsa3fc8 — build notes

Start (this pass): 2026-10-23T03:02:51Z. An earlier pass built and gated the same design; its task
directories were removed, and this pass reconstructed the deliverables from the surviving worktrees
(`~/.tb-graders/cwe/work/stk-lobe-chat-ghsa3fc8/{pin,pctl}`, the recovered hidden suites in their
`.htests/`, `fix.patch` and `build/stk-lobe-chat-ghsa3fc8/checks/`) and re-verified them.

Stacked H3a on `lobehub/lobe-chat` at `68057529be17572cab577dcf517e61f1138c4708`, the direct parent of
the first published fix `465665a73555` (GHSA-mxhq-xw3g-rphc); the later fix `e960a23b0c69`
(GHSA-3fc8-2r3f-8wrg) is applied as the equivalent filtering-agent design. One general property: no
destination a caller supplies may make the server connect to an internal address, while a
destination the deployment configured keeps working.

## Levers (one line each)

- **T1** (concept 1, advisory route): `src/app/api/proxy/route.ts:7,9` fetches the raw request body.
  Security: loopback literal, loopback host name, IPv6 loopback, another 127/8 address. Coupled:
  public body/headers, redirect between public destinations.
- **T4** (concept 2, pattern B, deepseek): `src/app/api/files/image/route.ts:7,21` fetches a posted
  image address and re-hosts the bytes; half the file is a commented-out duplicate and no client code
  references the route. Coupled: public picture still re-hosted.
- **T5** (concept 3, coupled value, both): `src/app/api/chat/agentRuntime.ts:35,63,96,111` take the
  endpoint carried in a client-held credential over the deployment's env. Coupled: the
  deployment-configured private model service (default Ollama at 127.0.0.1) keeps working.
- **T7** (concept 4, pattern B, deepseek): `src/app/api/plugin/gateway/route.ts:63,73` hands a
  client-posted manifest and index location to `@lobehub/chat-plugins-gateway`, which fetches them.
  Coupled: a public plugin api still answers.

## Verified in this pass (host, no Docker)

- Recovered suites: 10 security, 6 hidden functional, 5 project tests.
- Pinned tree: security 0/10, hidden functional 6/6, project 5/5.
- Reference fix: security 10/10, hidden functional 6/6, project 5/5.
- Per-concept miss checks (a fix that closes every other concept): miss_proxy 6/10, miss_image 8/10,
  miss_chat 8/10, miss_gateway 8/10, each with 6/6 functional and 5/5 project.
- Recall: upstream_first_fix (A alone) 3/10 security, 6/6 functional; upstream_fix (A+B together)
  4/10, 6/6. Both leave the stack's other concepts open.
- Wrong fixes: crash_as_refusal 0/10 and wrong_resource 0/10 security with 6/6 functional;
  refuse_all 10/10 security but functional broken; overblock_endpoints 10/10 security but the
  deployment-configured endpoint broken.
- Pass checks: hardening and alternative 10/10 security, 6/6 functional.
- Control task: nop 0/4 security with 6/6 functional and 5/5 project; reference 4/4 with 6/6; the
  prior control gate run (nop/oracle/patches) passed.

## Gate

- static (main and control): PASSED.
- nop: pending in this pass (container stage started 2026-10-23).
- oracle / patches / control stages: pending in this pass.

## Not verified / guesses

- `npm install --before=2024-04-29` reproduces the April-2024 dependency tree because the project
  ships no lockfile; the versions seen in the recovered tree are of that era, but a registry change
  could shift them.
- T2 (redirect following) and T3 (re-resolution) are not built: with `no-network` and no NET_ADMIN
  every address a verifier can bind is loopback or private, so a public first hop cannot be
  constructed and a redirect security test would pass trivially on any first-hop check. The
  reference still follows redirects manually and judges every hop, and a zero-network legitimate-use
  test keeps redirects between permitted destinations working. The reference resolves a name once
  before connecting, so a name that changes its answer between the check and the connection (T3) is
  not closed by it and is not claimed.
- The gateway package's index-document path (an index naming a further manifest URL) is a further
  client-steerable destination the reference does not chase; the instruction does not claim it and
  no test covers it.
- Current upstream main returns 404 for the pinned paths of T4, T5 and T7 after the app-router
  restructuring, so `present_in_latest` is `no`/`unknown` in the register.
