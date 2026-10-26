# crewai-ds — build notes

Start (UTC): 2026-10-24T03:27:34Z (pipeline start recorded by the driver; builder picked up 03:30Z)
End (UTC): 2026-10-24T04:35:20Z

Advisory (never written into instruction.md): GHSA-MR4R-HCGX-8P4H / CVE-2026-62240 / PYSEC-2026-3819.
Repo crewaiinc/crewAI. Pinned b6fbe078d6c45b90be9ebb533aa7715c721640f8 (direct parent of the
published fix 5d4851eac797cafc45b726f65747fe2c9520fc42, verified with `git rev-parse <fix>^`).
Pattern A+B, track injected.

## What I verified first (pinned tree, uv workspace venv)

Offline harness: patch `requests.adapters.HTTPAdapter.send` with a fake transport and
`socket.getaddrinfo` with a host->address table. Public hosts map to public IPs; internal hosts map
to 10.x / 169.254.x. Every fetch primitive (requests.get, Session.get, requests.head,
requests.request) funnels through the adapter, so the harness is layer-agnostic inside requests and
never opens a socket.

Behavioural results on the pinned tree (all reproduced):
- ScrapeWebsiteTool and ScrapeElementFromWebsiteTool: caller URL validates, a 302 Location to
  `http://internal.example/...` is followed and the internal body is returned.
- WebPageLoader, DocsSiteLoader, PDFLoader (download), DOCXLoader (download), load_from_url
  (CSV/JSON/XML/MDX) all follow the same redirect and return the internal body. Their initial URL
  is validated by the caller (RagTool.add / WebsiteSearchTool.add) or by the loader itself.
- Credential forwarding on a *public* cross-origin redirect (public.example -> cdn.example):
  requests strips `Authorization` itself, but `X-API-Key` and `X-CrewAI-Token` are forwarded, and
  a cookie supplied through the `cookies=` argument is forwarded (`Cookie: <name>=<value>`).
- SerplyNewsSearchTool (real upstream, untouched by the published fix): the Serply API response
  supplies a result link; the tool does `requests.get(link)` with redirects on and no URL check.
  A link that redirects to an internal address is followed and the internal Location is printed in
  the tool output.

Published fix controls applied locally: all of the above are refused (ValueError from validate_url
on the redirect target) and no request reaches the internal destination; same-origin/relative
redirects still work.

## Security property (one statement, written before choosing routes)

P1 (destination): Reading a remote resource must never send a request to an internal or otherwise
non-public network destination. This covers the address the caller gives and every address reached
while satisfying the read, however that address is chosen. When a read would reach such a
destination it must fail with an error, and no request may be sent to that destination.

P2 (credential reach, genuinely different protection): Credentials attached to a read - an
authorization header, a cookie, an API key or a similar secret - must only be sent to a destination
with the same scheme, host and port as the address the read started at. Same-origin keeps them.

Every route and sibling below is covered literally by P1 or P2. The instruction never mentions
redirect chains, link discovery, HEAD probes, search-result links, fallbacks or any loader/tool name.

## Lever candidates (full list, then the picks)

From the screener's O8/O8b plus my own search of `lib/crewai-tools/src/crewai_tools` for every
request primitive (`requests.get/post/head/request`, `Session`, `urlopen`, `aiohttp`):

1. SeleniumScrapingTool `driver.get(url)` (real, O8). REJECTED: needs Chrome/GUI at run time; cannot
   verify a behavioural test offline.
2. SerplyNewsSearchTool `requests.get(result["link"])` (real, O8). PICKED (pattern B).
3. PDFLoader HEAD/content-type probe (O8b, injected). PICKED (injected sibling).
4. DocsSiteLoader nav-link crawl (O8b, injected). PICKED (injected sibling).
5. JinaScrapeWebsiteTool direct-fetch fallback (O8b, injected). PICKED (injected sibling).
6. ContextualAIQueryTool `_check_documents_ready` (fixed api.contextual.ai host; datastore_id only
   fills a path segment). REJECTED: not a caller-chosen destination.
7. ArxivPaperTool urlopen/download (host + URLs from the arXiv API). REJECTED: same concept as #2
   (trusted API data) but less complex and needs XML to reach; duplicate concept.
8. Brightdata / Firecrawl / Scrapfly / Serper / Hyperbrowser / Spider / ScrapeGraph tools. REJECTED:
   they POST the URL to a third-party proxy; our process never fetches the destination.
9. Serply web/scholar/job/webpage-to-markdown tools. REJECTED: only call the fixed Serply API, no
   follow-up fetch of a destination.
10. WebsiteSearchTool / CodeDocsSearchTool / PDFSearchTool / DOCXSearchTool / CSV-JSON-XML-MDX
    SearchTool: cover the RAG loader family, which is the pattern-A lever (T2), not a sibling.
11. generate_crewai_automation / invoke_crewai_automation / crewai_platform / merge_agent_handler
    (fixed enterprise hosts, config-supplied). REJECTED: destination is not caller-chosen.
12. Stagehand / Bedrock browser tools (remote browsers). REJECTED: not verifiable offline; same
    dismissal as #1.
13. crewai-files FileUrl.read (separate package, no crewai_tools validate_url) and crewai
    experimental skills registry: OUT OF SCOPE per the screener and the one-task rule; not built on.

Why the picks beat the rest: #2 is real unmodified upstream code in a module the report never
points at, where the URL comes from data rather than the caller - the strongest "protection never
existed" shape. #3-#5 are injected, each with a different reason a solver skips it: #3 is a
different HTTP verb on a metadata path inside a file the published fix otherwise guards; #4 is a
fetch created by data already read, made with a Session (so a fix aimed at `requests.get` misses
it); #5 is a second fetch inside the same function behind an error branch, after a validate_url
that makes the whole function look handled. None of the three sits in a hunk the published fix
touches.

## Levers

T1 (main, HOW-type, second protection): credential origin confinement. requests strips
Authorization on a host change but forwards API-key/token headers and the `cookies=` argument.
A fix that only validates redirect targets still leaks. Coupled must-keep-working: same-origin
redirects keep every credential, and cross-origin public redirects still deliver the content.
Sites: both scraping tools (caller-supplied headers/cookies) and WebPageLoader (headers kwarg).

T2 (pattern A, far sites): the RAG loader family + the shared `load_from_url`
(webpage/docs_site/pdf/docx/utils). Reason to dismiss: `RagTool.add`/`WebsiteSearchTool.add`
already call validate_url on every source before the loader runs, and the loaders are lower-level
code, not scraping tools. Distance: another module tree and 5 files.

T3 (pattern B, real): SerplyNewsSearchTool follows each result link with requests.get, no URL check.
Reason to dismiss: the links come from the Serply API, not the agent, and it is a search tool.

T4 (injected): Jina tool direct-fetch fallback when the reader service does not return 200. Reason to
dismiss: validate_url already runs at the top of the function, so the function reads as covered.
Fixed-code fix: route the fallback through the redirect-aware helper.

T5 (injected): PDFLoader content-type probe with `requests.head(..., allow_redirects=True)` before
the download. Reason to dismiss: it is "only" a metadata probe, and HEAD is not the content fetch.

T6 (injected): DocsSiteLoader crawls up to five navigation links found on the fetched page with a
`requests.Session().get`. Reason to dismiss: the links are discovered in page content, and the main
page fetch is guarded. A protocol-relative href (`//internal.example/...`) passes the existing
filters and reaches an internal host.

## Routes and input shapes covered by the security tests

- absolute Location to an internal DNS name (private IP)
- absolute Location to a link-local/metadata IP literal (no DNS needed)
- scheme-relative Location (`//internal.example/x`) and protocol-relative nav href
- multi-hop chain: public -> public -> internal (the block must happen at the internal hop)
- caller-supplied credentials (Authorization, X-Api-Key, X-CrewAI-Token) and cookies kwarg on a
  cross-origin public redirect (must not reach the second origin)
- the same credentials on a same-origin redirect (must be preserved) - functional
- every published-fix entry point, the Serply route, and the three injected siblings
- the existing opt-out environment setting still bypasses (functional)

## Test architecture (offline, layer-agnostic)

A suite conftest installs (a) a `socket.getaddrinfo` host table and (b) a fake
`requests.adapters.HTTPAdapter.send` that records (method, URL, prepared headers) and answers from a
per-test route table. This observes the wire for any requests-based fix (requests.get, Session,
manual loops, hooks) without importing a helper the solver would have to guess. Tests construct
their own responses and expected values. "Blocked" = an exception AND no recorded request to the
internal destination.

## Wrong-fix checks planned

security_fail (one per lever): sf-miss-credential-origin, sf-miss-rag-loaders, sf-miss-serply,
sf-miss-jina-fallback, sf-miss-pdf-probe, sf-miss-docs-crawl.
functional_fail: fnf-strip-all-credentials (over-hardening), fnf-refuse-all-redirects.
pass: pass-hardening, pass-alt (independent Session-based design), pass-blind (written later by the
blind-fix agent; not created here).

## Verified during the build (local venv + fake network, then the gate)

Local: with the pinned+injected tree every security test fails (17/17) and every functional test
passes (79/79, including the six copied project test modules). With the oracle applied: 17/17
security and 79/79 functional pass. Each check patch was run locally and behaves as declared:
sf-miss-credential-origin and sf-miss-rag-loaders fail only security tests, sf-miss-serply,
sf-miss-jina-fallback, sf-miss-pdf-probe and sf-miss-docs-crawl each fail exactly its own security
test, fnf-strip-all-credentials and fnf-refuse-all-redirects fail functional tests,
pass-hardening and pass-alt score 1.0.

Gate stage runs (see build/crewai-ds/gate_report.json for the full record):
- static PASS (2026-10-24)
- nop PASS (2026-10-24): 17/17 security tests fail on the pinned+injected tree, 79/79 functional pass.
- oracle PASS (2026-10-24): 3/3 runs reward 1.0 with identical results.
- patches PASS (2026-10-24): 6 security_fail (each fails only its own lever's security tests, functional all pass), 2 functional_fail, 2 pass at reward 1.0. pass-blind is not present yet (written later by the blind-fix agent).

The PDF loader has two independent levers, kept separate by method-specific routing: the injected
HEAD content-type probe (T5) is exercised with a HEAD redirect while the download stays public, and
the download (T2) is exercised with a GET redirect while the probe returns 200. Without that split
the probe masked the download path.

## What I could not verify

- No target-model trials were run (build-v1 and the gate instructions forbid them here); the bar
  is asserted only by the design and the gate.
- SeleniumScrapingTool (a real, unvalidated browser navigation route named by the screener) is not
  built: it needs a browser at run time, so it cannot be exercised offline.
- `present_in_latest` for the injected siblings is "no" by construction; for T3 it was read from
  raw.githubusercontent.com main on 2026-10-24 and the unvalidated requests.get is still there.
- The published fix in current upstream has since grown a `safe_get_bounded`; the task stays at the
  pinned commit and the advisory's fix as published.

## Out of scope (one line, not built on)

crewai-files FileUrl reads and the crewai experimental skills registry download (separate packages
with their own scheme-only checks) were noted by the screener and are outside this task's
crewai-tools scope.

## Fairness concerns I see myself

- The copied project loader tests mock `requests.get` directly. A behaviourally correct fix that
  routed every read through `requests.Session` would bypass those mocks and fail the functional
  group. The reference and the alternative fix both keep `requests.get`, and a solver running the
  project's own tests sees the failure, but the constraint is real and is not stated in the report.
- The navigation-crawl sibling requires the load to fail with an error when one discovered link is
  disallowed. A fix that silently skips that link (and returns the rest) closes the destination
  hole but fails the stated refusal contract. The contract is written in the instruction, so the
  test follows it, but this is the one place where two secure designs differ observably.
- Difficulty rests on audit scope (17 security tests across 6 lever groups). The instruction states
  both properties generally and never points at a route; a solver who greps every request primitive
  finds all of them, and that is the intended work.
