# contracts-wizard-ds — build notes

Start: 2026-10-24T03:28:34Z (pipeline) / design work from 03:38Z
End: 2026-10-24T04:18Z
Task: `contracts-wizard-ds` · repo openzeppelin/contracts-wizard · advisory
GHSA-4X76-22X2-RX8V / CVE-2026-48054 · pinned `dd503eba4cc89eb330df3e36b6057e7648efc75b`
· published fix `ec12c44f8d9e0491eba31037f95b36e98ec58b5f` · pattern A · track injected.

## What the product does
The Contracts Wizard renders Solidity contracts from user options and packages complete starter
projects (Hardhat, Foundry, Polkadot Hardhat) as zips. Option values (`name`, `symbol`, token
`uri`, `baseUri`, `info.license`, `info.securityContact`, ...) are copied into the generated
files. The advisory is about escaping those values into the generated source.

## Security property (written once, before picking routes)
Every value supplied to the wizard that it copies into generated source must be emitted as data:
after generation it must decode back to exactly the supplied text, must stay inside the string
literal or comment it was placed in, and must not add, end or alter any source line, statement
or comment — in every generated file, whatever the target language. If a value cannot be
represented safely in its context, the generator must refuse with a client error instead of
emitting it. Everything that works today keeps working, including non-ASCII display text.

One concrete trigger in the report: an ERC-20 named `My "Token"`, Hardhat download; the
generated test's assertion string ends at the inner quote.

## Levers

### L1 (main, HOW-type; pattern A far site) — the shared Solidity literal serializer
`packages/core/solidity/src/utils/sanitize.ts:1-6`. Two broken branches:
- non-ASCII branch (`unicode"..."`) escapes only `"`, so a backslash before the quote survives
  and the quote closes the literal (`é\"` -> breakout); CR/LF/VT are emitted raw inside a
  unicode literal (Solidity excludes them) so a line break ends the literal;
- ASCII branch uses `JSON.stringify`, which emits `\b`/`\f` (not Solidity escapes) and raw
  0x7F, so backspace/form-feed/DEL produce invalid Solidity.
Reached through `printContract` (public `erc20.print`/`erc721.print`/`erc1155.print`, UI and MCP)
for every string constructor argument (name, symbol, uri).
Reason to dismiss: the report names generated test files; the contract printer already has a
`stringifyUnicodeSafe` helper that escapes quotes and looks like an existing defence, so a solver
copies it into the test templates (inheriting the bug) or leaves it alone.
Coupled must-keep-working: unicode names/emoji/NUL still emit a `unicode"..."` literal that
decodes exactly; ASCII-with-quote still plain and exact; `{id}` survives.
Why how-type: a plausible check (JSON.stringify / quote-only escaping) mishandles the shapes;
the fix requires understanding the Solidity literal grammar, not finding a call site.

### L2 (HOW-type; pattern B route where the protection never existed) — comments
`packages/core/solidity/src/print.ts:34` and `packages/core/solidity/src/zip-foundry.ts:12`
interpolate `contract.license` raw into `// SPDX-License-Identifier: ...`. A line break in the
license starts a new source line of Solidity in the generated contract and in the Foundry test
and script. Verified on pinned and still present in current upstream (`master` b2c649b), so the
published fix does not touch it. Reason to dismiss: the license is free-form SPDX text in a
comment; comments are not treated as code sinks; the report only mentions test assertions.
Coupled: `MIT` / `Apache-2.0` appear unchanged; a license with a quote stays on its comment line.

### L3 (HOW-type; pattern B route where the protection never existed) — base URI literal
`packages/core/solidity/src/erc721.ts:147` emits `return ${JSON.stringify(baseUri)};` in the
generated contract. `JSON.stringify` is a JavaScript escaper: a non-ASCII base URI is emitted raw
inside a plain `"..."` literal (invalid Solidity), and backspace/form-feed become `\b`/`\f`
(invalid Solidity escapes). Real unmodified upstream code; still present on `master` b2c649b.
Reached through `erc721.print` (public API/UI/MCP). Reason to dismiss: baseUri is a URL and
`JSON.stringify` looks like escaping; this site bypasses the printer's helper.
Coupled: an ASCII URL with `"`/`\` still decodes exactly; empty baseUri still emits no override.

### L4 (WHERE-type extra, injected sibling) — Polkadot generator's own test template
Injected into `packages/core/solidity/src/zip-hardhat-polkadot.ts`: the subclass overrides
`getTest` with a Polkadot-specific deployment test that interpolates `opts.name`/`opts.uri` raw.
Reachable through `zipHardhatPolkadot` (npm `zip-env-hardhat-polkadot`, UI Polkadot download);
upstream fix never touches this file. Reason to dismiss: a wrapper subclass inherits the base
class fix; solvers fix the base template and stop.
Coupled: plain names still decode; polkadot config/package files unchanged.

### L5 (WHERE-type extra, injected sibling) — Foundry deploy script log line
Injected into `packages/core/solidity/src/zip-foundry.ts` `getScript`: a
`console.log("Deploying ${opts?.name ?? c.name}");` line in the generated Solidity script.
Reachable through `zipFoundry`; the upstream fix touches the test-function builder in the same
file, never the script template. Reason to dismiss: it is a log message, not an assertion, and
sits in a different generated file from the reported tests.
Coupled: a plain name still appears in the log line.

## Candidate sibling list (full search) and picks
Real upstream sites/records found:
1. `zip-hardhat.ts` getExpects name/uri (published) — base, not a sibling.
2. `zip-foundry.ts` test-function name/uri (published) — base.
3. `utils/sanitize.ts` (published) — main far site L1.
4. `print.ts:34` license comment — real route L2 (picked).
5. `zip-foundry.ts:12` license header — second sink of L2 (picked, forces a producer fix).
6. `print.ts:43` NatSpec `securityContact` value — real route; same comment concept as L2 and not
   separately tested. Oracle validates it too; not a lever.
7. `erc721.ts:147` baseUri `JSON.stringify` — real route L3 (picked; subtle two-language shape).
8. `print.ts:100` `additionalCompatibleLibraries` name/version into the compatibility comment —
   only supplied by sibling packages with constants, not by a wizard user; rejected as
   out of the protected data set (internal library metadata, not a user value).
9. `set-namespaced-storage.ts:26/33` namespacePrefix in a `//` comment — rejects whitespace
   already, protected; rejected.
10. `governor.ts:304-305` quorumAbsolute raw into code — validated by `numberPattern`; rejected.
11. `account.ts:164` `draft-${opts.ERC7579Modules}.sol` — enum value; rejected.
12. `ContractBuilder` contract name -> `toIdentifier` — identifier, not a data value; rejected.
13. `packages/core/confidential/src/zip-hardhat.ts` passes no opts (no assertion today) —
    plumbing it plus a template would pull the fhevm/hardhat dependency tree; rejected.
14. Stellar/Cairo/Stylus printers — different products/packages, outside this advisory's
    protection (Solidity project generation); noted as out of scope, not built.
15. UI/MCP/CLI call the same generators; no separate template sinks; rejected.
16. `zip-hardhat.ts`/`zip-foundry.ts` ignition module, deploy script, `describe`, import and
    file-path interpolations use the sanitized identifier `c.name`, not the raw option; rejected.

Injected sibling candidates and choice:
A. Polkadot `getTest` override with raw name/uri (picked as L4): a second implementation, far
   from the report, dismissed as inherited from the fixed base class.
B. Foundry script `console.log` with the raw name (picked as L5): different sink/file, dismissed
   as a log line rather than an assertion.
C. Raw `"${baseUri}"` in `erc721.ts` (screener O8b) — rejected because the real JSON.stringify
   site is a better how-type lever (it looks escaped) and keeps the task on unmodified upstream
   code; injecting a raw variant would replace a real route with a planted one.
D. `Stablecoin` case in the Hardhat switch — rejected: same function the published fix edits, so
   not far from the report.
E. Stellar Rust template using the display name — rejected: different product, outside the
   advisory's protection.
F. A license header in the Hardhat test file — rejected: another sink of L2's one concept.
Why A/B beat the rest: both are a different module/function from every published edit, both are
reachable through a public generator export, both fall under the single property, and they fail
for different reasons (inheritance vs. log line).

## Test plan (hidden, node:test + ts-node; JUnit XML)
Security — each accepts a client error or asserts the marker/content stays contained:
- S1 contract ERC20 name `é\\"); MALICIOUS_7c1a.back(); //` (unicode+backslash helper breakout)
- S2 contract ERC20 name with LF inside unicode text (unicode literal line break)
- S3 contract ERC20 name with backspace (ASCII branch JSON.stringify `\b`)
- S4 contract ERC20 name with DEL 0x7F (ASCII branch raw 0x7F)
- S5 Foundry test ERC20 name unicode+backslash+quote (Solidity literal, second target)
- S6 Hardhat test ERC20 name with quote/statement injection (reported landing point)
- S7 Hardhat test ERC1155 uri with quote/statement injection
- S8 Foundry test ERC20 name with quote/statement injection
- S9 contract license with `\n` + statement (comment sink)
- S10 Foundry test + script license with `\n` + statement (second license sink)
- S11 ERC721 baseUri non-ASCII (valid Solidity literal that decodes exactly)
- S12 ERC721 baseUri backspace (JSON.stringify `\b`)
- S13 Polkadot test ERC20 name with quote/statement (injected L4)
- S14 Foundry script name with quote/statement in the log line (injected L5)
Functional (must pass on pinned+injected too):
- F1 Hardhat plain ERC20 name decodes exactly + file layout
- F2 Foundry plain ERC20 name decodes exactly
- F3 contract ASCII name with quote/backslash decodes exactly
- F4 contract unicode/emoji/NUL names decode exactly
- F5 ERC1155 `{id}` placeholder survives in contract and Foundry test
- F6 plain SPDX license (`MIT`, `Apache-2.0`) preserved in contract, Foundry test and script
- F7 ASCII baseUri with quote/backslash decodes exactly
- F8 Polkadot plain name decodes exactly + polkadot config present
- F9 Foundry script log line with a plain name decodes exactly
- F10 generated file sets unchanged for all three generators
Marker `MALICIOUS_7c1a.back` contains a dot, so `toIdentifier` (used for the contract identifier)
cannot reproduce it: a verbatim occurrence can only come from raw interpolation.

## Harness/verification plan
- Base node:22-bookworm-slim; repo fetched at pinned commit; `injection.patch` applied; minimal
  npm dependency tree (jszip, ethereum-cryptography, semver, typescript, ts-node, @types/*,
  ava, rimraf) installed at `/workspace/node_modules`; the `prepare`-generated
  `openzeppelin-contracts*.json` assets written for version 5.6.0.
- Verifier image installs the same tree at `/opt/wizdeps`, restores `/workspace`, links
  node_modules, copies hidden suites into `/workspace/.htests`, runs node:test per group with
  ts-node transpile-only as uid 1000, writes JUnit XML, score.py scores.
- Project tests run offline at image build: the pure generation/serializer suites (sanitizer,
  erc20/721/1155, governor, stablecoin, account, custom, contract, ...): 657 tests. The zip
  project tests need `npm ci`/`forge`/network and cannot run offline; noted.
- Oracle: published source fix + license/securityContact producer validation + erc721 serializer
  + the two injected siblings fixed.
- Wrong-fix checks: one security_fail per lever, published-only (unlisted_route), TypeScript-only
  (one_role_or_direction), over-broad (functional_fail), refuse-all (functional_fail),
  hardening pass, alternative pass.

## Local verification (host, node 20 + ts-node transpile-only)
- On the pinned+injected tree: 14/14 security tests fail, 13/13 functional tests pass.
- On the oracle: 27/27 pass; the pure project suites (688 tests) pass offline on the oracle.
- Variants (checked against the hidden suites): miss-helper 6 security fail / functional all
  pass; miss-license 2/2; miss-baseuri 2/2; miss-polkadot 1/1; miss-script-log 1/1;
  published-only 6 security fail / functional all pass; typescript-only 2/2;
  overbroad 3 functional fail; refuse-all all functional fail; hardening 27/27 pass;
  alternative 27/27 pass.
- The image build reached the project-test step (688 passing) and failed only on the shared
  VM's /tmp inode exhaustion (infra), not on the task.

## Gate results (delivered verifier)
- static: PASSED (conformance + strict; blind declared, produced later by the pipeline).
- nop: PASSED (16 security tests fail, 13 functional tests pass).
- oracle: PASSED (3 runs, each reward 1.0, 29/29).
- patches: PASSED 11/11 as declared: hardening 1.0; alternative 1.0; seven security_fail
  (miss-helper 8 security fails, miss-license 2, miss-baseuri 2, miss-polkadot 1,
  miss-script-log 1, published-only 6, typescript-only 2) all with functional green;
  overbroad 3 functional fails; refuse-all 13 functional fails. blind.patch is declared but
  deliberately absent (the pipeline's blindfix step writes it).
- One infra failure on the first nop attempt: the shared VM's /tmp tmpfs ran out of inodes
  during image build (containerd temp dir); retried with TMPDIR on the big disk and passed.
  This is the only Docker/Harbor issue seen; no task change was needed.

## Risks / unknowns
- Whether solc really rejects raw non-ASCII and `\b` in a plain literal: taken from the published
  fix's own comments and the Solidity grammar; the hidden validator encodes that grammar.
- Upstream `master` today (b2c649b) still has the raw license header and `JSON.stringify(baseUri)`
  -> present_in_latest = yes for both pattern-B routes.
- The zip project tests cannot run offline; the offline-runnable project suites are the check.
