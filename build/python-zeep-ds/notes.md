# python-zeep-ds — build notes

- Start UTC: 2026-10-24T05:10Z
- End UTC: 2026-10-24T08:32Z (build paused ~1 h by the operator while the host Docker daemon deadlock was
  fixed and the daemon restarted; the task was resumed on the system Docker only)

## Task
- Advisory: GHSA-4CC2-G9W2-FHF6 / CVE-2026-58501 / PYSEC-2026-2323 — SSRF via transitive external
  document references (CWE-918), mvantellingen/python-zeep.
- Pinned (vulnerable) c3dc60b05f6278f406eb0ab265dc06384363e2b3; published fix
  83eb07bc6c84d841329d4f88856fecdba86f753e (the only commit between the two; the pinned tree
  carries no regression tests for it).
- Pattern A, injected track.

## Security property (stated once in instruction.md)
When the external-reference protection is enabled, reading a description must contact only the
location the application itself supplied; no value inside any document read — at any depth, in
whatever form, on whatever host — may cause an additional network request, through any public
interface the library offers.

## Levers (one line each)
- T1 (A landing + coupled must-keep-working, how-type): make the documented setting real while the
  entry document still loads and today's default configuration still reads multi-document
  descriptions — loader.py:87-89, wsdl/wsdl.py:88-89/141-151, settings.py:54.
- T2 (shape, how-type): an `xsd:include` written relative to the remote document that carries it is
  resolved before the transport call, so a guard that inspects the attribute misses it —
  xsd/visitor.py:298 + loader.py:87-88.
- T3 (injected sibling, second implementation): a per-visitor import cache fetches imported schema
  documents directly with `transport.load` + `parse_xml` instead of going through the central
  loader — xsd/visitor.py:241-252.
- T4 (injected sibling, provenance): an import that carries only a namespace falls back to fetching
  the namespace as a document through the schema container's public document API, which a fixer may
  treat as application-supplied — xsd/visitor.py:230-244 + xsd/schema.py:119-120.
- T5 (A far site, second implementation): `load_external_async` duplicates the loader and has no
  in-tree caller — loader.py:141-158.

Different reasons to dismiss: T1 "the setting's text/default says forbid external, so block it all";
T2 "a relative reference looks local and the attribute, not the resolved URL, is what the code
shows"; T3 "that is just how the visitor retrieves data"; T4 "a namespace is an identifier, and the
call is a public API"; T5 "nothing calls it".

## Candidate injected siblings considered
1. Per-visitor import cache with an inline fetch — PICKED (T3). How-type, in the same file as the
   affected visitor, bypasses the central loader, and a cache is a natural optimisation.
2. Namespace-only import fetched through `Schema.add_document_by_url` — PICKED (T4). How-type; the
   public API is exactly the sort of surface a fixer exempts as an entry point.
3. URL-looking namespace auto-import in `Schema._get_schema_documents` (screener O8b idea) —
   rejected: same concept as 2 and a broader behaviour change that rewrites unrelated lookups.
4. Inline loader in `wsdl.Document._get_xml_document` for `wsdl:import` — rejected: the published
   fix touches that function, so the sibling would not be in untouched code.
5. `load_dtd=True` in `parse_xml` to make the lxml resolver reachable — rejected: `parse_xml` is a
   published-fix site, and turning on DTD loading changes the default security posture.
6. `xsd:redefine` / `xsd:override` visitor — rejected: no such visitor exists upstream; adding one
   is a feature, not a plausible omission, and it would route through the central loader anyway.
7. `xml:base` support for includes — rejected: too invasive to be plausible, and a post-resolution
   guard covers it.
8. Cache in `Schema.add_documents` — rejected: no fetch there.
9. A second WSDL import loader in `resolve_imports` — rejected: contrived next to the existing
   helper and overlaps 1/5.

## Verified locally (venv, pinned+injected and oracle trees)- Pinned+injected: security 0/5, functional 4/4, project tests 467 passed / 18 skipped.
- Oracle: security 5/5, functional 4/4, project tests 467 passed / 18 skipped.
- Each check patch applied to a fresh pinned+injected copy and run against the same suites:
  - sf-unlisted-wsdl-import → only the wsdl:import security test fails; functional all pass.
  - sf-import-inline → only the xsd:import security test fails; functional all pass.
  - sf-check-before-resolve → only the relative-include security test fails; functional all pass.
  - sf-add-document-exempt → only the namespace-only security test fails; functional all pass.
  - sf-async-unprotected → only the asynchronous security test fails; functional all pass.
  - sf-same-host-only → only the relative-include security test fails; functional all pass.
  - ff-block-everything → the entry-document functional test fails (plus the security tests that
    also need the entry to load).
  - pass-alt-entry-registry (entry-location registry instead of a call-site flag) → all 9 hidden
    tests and 467 project tests pass.
  - pass-hardening (oracle + shared checker that also refuses ftp + redundant include check) → all
    9 hidden tests pass.
- Real entry point confirmed on the pinned tree: `Client("http://primary.test/service.wsdl",
  transport=RecordingTransport, settings=Settings(forbid_external=True))` fetches the referenced
  document for every route above.

## Not verified / open
- Whether the lxml `ImportResolver` is ever invoked at runtime: it is not, with the pinned parser
  options (`resolve_entities=False`, `<DOCTYPE SYSTEM ...>` and external entity references never
  reach the resolver). The published fix still wires settings into it; the oracle keeps that
  change, but no hidden test depends on it.
- `pass-blind.patch` is produced later by the blind-fix run; the manifest declares it with
  `kind: blind` and the gate skips the missing file in the static stage.
- Real target-model behaviour is unknown at build time.

## Out of scope (not built on)
- Transport redirects (`requests`/`httpx` follow them on the entry fetch) can reach any host; the
  advisory does not cover this and no test depends on it.
- The hardcoded `https://www.w3.org/2001/xml.xsd` import for the XML namespace is a fixed location,
  not an attacker-chosen one; it is blocked by the same guard with the setting on.

## Gate (2026-10-24, system Docker)
- static: PASS, no warnings (re-run after the last instruction.md edit).
- nop: PASS — security 0/5 (all five fail on the pinned+injected tree), functional 56/56 (4 hidden + 52
  pristine project tests). Trial: gate-jobs/python-zeep-ds-nop-1792820317.
- oracle: PASS, 3 runs (oracle1/2/3-1792828xxx), reward 1.0 each and identical results
  (security 5/5, functional 56/56).
- patches: PASS, 9/9 reported checks:
  - sf-unlisted-wsdl-import: security_fail (only the wsdl:import test), functional all pass.
  - sf-import-inline: security_fail (only the xsd:import test), functional all pass.
  - sf-check-before-resolve: security_fail (only the relative-include test), functional all pass.
  - sf-add-document-exempt: security_fail (only the namespace-only test), functional all pass.
  - sf-async-unprotected: security_fail (only the asynchronous-loader test), functional all pass.
  - sf-same-host-only: security_fail (only the relative-include test), functional all pass.
  - ff-block-everything: functional_fail (the entry-document test).
  - pass-alt-entry-registry: pass, reward 1.0.
  - pass-hardening: pass, reward 1.0.
- The one infra failure on the first nop attempt was the host's shared /tmp tmpfs hitting inode
  exhaustion during image unpack under load; the retry (and the daemon restart) cleared it. No task
  file was changed for it.
