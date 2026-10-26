# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `crewai-ds`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: ["GHSA-MR4R-HCGX-8P4H", "CVE-2026-62240", "PYSEC-2026-3819"]; crewaiinc/crewai; SSRF (CWE-918) via unvalidated HTTP redirect following, plus credential forwarding across origins
- Pinned (vulnerable) commit: b6fbe078d6c45b90be9ebb533aa7715c721640f8. Published fix: 5d4851eac797cafc45b726f65747fe2c9520fc42.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "claude-opus-5-5",
 "entry_id": "4584",
 "advisory_ids": [
  "GHSA-MR4R-HCGX-8P4H",
  "CVE-2026-62240",
  "PYSEC-2026-3819"
 ],
 "repo": "crewaiinc/crewai",
 "pinned_commit": "b6fbe078d6c45b90be9ebb533aa7715c721640f8",
 "fix_commits": [
  "5d4851eac797cafc45b726f65747fe2c9520fc42"
 ],
 "trust_decision": {
  "summary": "Whether a tool/loader-supplied URL may be fetched is decided once by validate_url (scheme + DNS-resolved private/reserved IP check) on the initial URL only; requests.get then follows 3xx redirects to any host unchecked. The fix adds safe_get, which re-validates each redirect hop and strips credentials on cross-origin hops.",
  "evidence": [
   "lib/crewai-tools/src/crewai_tools/security/safe_path.py:161-220",
   "lib/crewai-tools/src/crewai_tools/tools/scrape_website_tool/scrape_website_tool.py:78-84",
   "lib/crewai-tools/src/crewai_tools/tools/rag/rag_tool.py:311-317",
   "fix.diff:179-216"
  ]
 },
 "landing_point": {
  "where": "lib/crewai-tools/src/crewai_tools/tools/scrape_website_tool/scrape_website_tool.py:78",
  "why": "The summary says 'scraping fetches'; ScrapeWebsiteTool is the canonical scraper and shows validate_url immediately followed by requests.get with default redirect following."
 },
 "fix_sites": [
  {
   "where": "lib/crewai-tools/src/crewai_tools/tools/scrape_website_tool/scrape_website_tool.py:79",
   "entry_point": "ScrapeWebsiteTool._run / BaseTool.run (agent tool call)",
   "module_kind": "tool (handler)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/tools/scrape_element_from_website/scrape_element_from_website.py:87",
   "entry_point": "ScrapeElementFromWebsiteTool._run (agent tool call)",
   "module_kind": "tool (handler)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/webpage_loader.py:28",
   "entry_point": "WebsiteSearchTool.add / RagTool.add(data_type=WEBSITE) -> WebPageLoader.load",
   "module_kind": "RAG loader (lower-level API)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/docs_site_loader.py:29",
   "entry_point": "CodeDocsSearchTool.add -> RagTool.add(data_type=DOCS_SITE) -> DocsSiteLoader.load",
   "module_kind": "RAG loader (lower-level API)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/pdf_loader.py:50",
   "entry_point": "PDFSearchTool.add -> RagTool.add(data_type=PDF_FILE) -> PDFLoader._download_from_url",
   "module_kind": "RAG loader (lower-level API)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/docx_loader.py:46",
   "entry_point": "DOCXSearchTool.add -> RagTool.add(data_type=DOCX) -> DOCXLoader._download_from_url",
   "module_kind": "RAG loader (lower-level API)"
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/utils.py:37",
   "entry_point": "CSV/JSON/XML/MDX SearchTool.add -> RagTool.add -> {CSV,JSON,XML,MDX}Loader -> load_from_url",
   "module_kind": "shared helper (lower-level API)"
  },
  {
   "where": "fix.diff:123-216",
   "entry_point": "new crewai_tools.security.safe_requests.safe_get (public helper)",
   "module_kind": "security utility (new)"
  }
 ],
 "O1_entry_points": 10,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/utils.py:37 (load_from_url, shared by csv/json/xml/mdx loaders, e.g. lib/crewai-tools/src/crewai_tools/rag/loaders/csv_loader.py:16); also pdf_loader.py:50, docx_loader.py:46, docs_site_loader.py:29, webpage_loader.py:28 under lib/crewai-tools/src/crewai_tools/rag/loaders/"
 },
 "O3_reason_to_dismiss": "RAG loaders look already protected: RagTool.add calls validate_url on every http(s) source before any loader runs (lib/crewai-tools/src/crewai_tools/tools/rag/rag_tool.py:311-317), and they live under rag/loaders, not the scraping tools the report names; for O8, Selenium is a real browser whose redirects requests-level code cannot intercept, and Serply news links come from a trusted search API, not the user.",
 "O4_distance": {
  "files": 8,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Legitimate redirects must keep working: relative Location headers (urljoin), same-origin redirects keep Authorization/cookies, cross-origin public redirects are followed with credentials stripped, chain capped at max_redirects; also the CREWAI_TOOLS_ALLOW_UNSAFE_PATHS escape hatch must still bypass. A fix that sets allow_redirects=False everywhere or strips all headers breaks scraping of sites that redirect http->https or to /final.",
  "where": "fix.diff:151-216; lib/crewai-tools/src/crewai_tools/security/safe_path.py:178-184; tests at fix.diff:384-406, fix.diff:462-483"
 },
 "O6_input_shapes": [
  "absolute Location to internal IP (fix.diff:206)",
  "relative Location resolved against response.url (fix.diff:206)",
  "multi-hop redirect chains, capped by max_redirects (fix.diff:196-198)",
  "all redirect codes 301/302/303/307/308 (fix.diff:141)",
  "credentials passed as headers dict (Authorization, Cookie, X-API-Key, *token*/*secret* names) and as cookies kwarg, stripped only on cross-origin hop (fix.diff:142-176, fix.diff:211-212)",
  "callers with and without explicit headers/cookies/timeout kwargs (fix.diff:22, fix.diff:47, fix.diff:238-241)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "SeleniumScrapingTool fetches agent-supplied URL in a local browser with only an http(s) regex, no validate_url on the URL or on redirects",
   "where": "lib/crewai-tools/src/crewai_tools/tools/selenium_scraping_tool/selenium_scraping_tool.py:195-206",
   "reason_to_dismiss": "Browser-driven transport, not requests; redirects (and JS navigation) cannot be checked per hop, and the tool never had validate_url, so it reads as a separate feature outside a 'redirect bypass' fix.",
   "distance": "different tool subpackage (tools/selenium_scraping_tool) from landing point; same crewai-tools package",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "SerplyNewsSearchTool follows each search-result link with requests.get (redirects on) without validate_url",
   "where": "lib/crewai-tools/src/crewai_tools/tools/serply_api_tool/serply_news_search_tool.py:76-82",
   "reason_to_dismiss": "Link URLs come from the Serply API response rather than the user/agent, and the tool is a search tool, not a scraper.",
   "distance": "different tool subpackage (tools/serply_api_tool); same crewai-tools package",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/pdf_loader.py:50",
   "sibling": "a HEAD/content-type probe (requests.head with allow_redirects=True) before download to detect PDF vs HTML",
   "why_realistic": "Loaders already guess type from URL; a maintainer adding content sniffing would naturally use requests.head with redirects, bypassing safe_get."
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/rag/loaders/docs_site_loader.py:83-101",
   "sibling": "crawl the relative nav links found on the docs page (urljoin + requests.Session().get) to load subpages",
   "why_realistic": "The loader already collects and urljoins nav links for 'Related documentation pages'; fetching them is the obvious next feature and a session-based fetch would not go through safe_get."
  },
  {
   "where": "lib/crewai-tools/src/crewai_tools/tools/jina_scrape_website_tool/jina_scrape_website_tool.py:50-53",
   "sibling": "a direct-fetch fallback (requests.get(url)) when r.jina.ai fails or no API key is set",
   "why_realistic": "Fallback-on-error to a plain fetch is a common pattern; it would keep validate_url-then-requests.get, i.e. the pre-fix shape."
  }
 ],
 "O9_family": "SSRF (CWE-918) via unvalidated HTTP redirect following, plus credential forwarding across origins",
 "O9_dos": false,
 "O10_build": {
  "language": "Python",
  "toolchain": "uv workspace (lib/crewai-tools/pyproject.toml), pytest; requests, beautifulsoup4",
  "services": [],
  "offline_after_build": true,
  "project_tests": "lib/crewai-tools/tests/rag/test_webpage_loader.py, test_docx_loader.py, test_csv_loader.py, test_json_loader.py, test_xml_loader.py, test_mdx_loader.py; fix adds tests/utilities/test_safe_requests.py and tests/rag/conftest.py (DNS monkeypatch, requests.get mocked)"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "lib/crewai-tools/src/crewai_tools/security/safe_requests.py (new); tools/scrape_website_tool/scrape_website_tool.py; tools/scrape_element_from_website/scrape_element_from_website.py; rag/loaders/{webpage_loader,docs_site_loader,pdf_loader,docx_loader,utils}.py",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add allow_redirects=False (or re-validate response.url after the fact) in ScrapeWebsiteTool/ScrapeElementFromWebsiteTool only, leaving the RAG loaders, relative redirects and cross-origin credential forwarding untouched."
 },
 "out_of_scope_notes": [
  "crewai-files FileUrl.read/aread fetch with follow_redirects=True and only a scheme check (lib/crewai-files/src/crewai_files/core/sources.py:528-551); separate package without crewai_tools validate_url.",
  "crewai experimental skills registry downloads with follow_redirects=True (lib/crewai/src/crewai/experimental/skills/registry.py:194).",
  "Stagehand and Bedrock browser tools page.goto(url) without validate_url (lib/crewai-tools/src/crewai_tools/tools/stagehand_tool/stagehand_tool.py:506, lib/crewai-tools/src/crewai_tools/aws/bedrock/browser/browser_toolkit.py:145); run in remote browsers.",
  "validate_url resolves DNS separately from the later connect (rebinding TOCTOU) at lib/crewai-tools/src/crewai_tools/security/safe_path.py:204-218; not addressed by the fix."
 ],
 "unverified": [
  "repo_mb not measured (no shell size command run); tiny/giant flags not assessed.",
  "present_in_latest for O8 routes: no latest release provided.",
  "O1 count of 10 counts tool/loader entry points (ScrapeWebsiteTool, ScrapeElementFromWebsiteTool, WebsiteSearchTool, CodeDocsSearchTool, PDFSearchTool, DOCXSearchTool, CSV/JSON/XML/MDX SearchTool) plus direct loader.load calls are not counted separately.",
  "Advisory text itself was not available; scope inferred from summary and fix commit title 'Fix SSRF redirect bypass in scraping fetches'.",
  "Whether CSV/JSON/XML/MDX search tools route URLs through RagTool.add's validate_url was inferred from their add() overrides calling super().add, not traced per loader."
 ]
}
  ```
- Published fix sites:   - lib/crewai-tools/src/crewai_tools/tools/scrape_website_tool/scrape_website_tool.py:79 — entry point: ScrapeWebsiteTool._run / BaseTool.run (agent tool call) [tool (handler)]
  - lib/crewai-tools/src/crewai_tools/tools/scrape_element_from_website/scrape_element_from_website.py:87 — entry point: ScrapeElementFromWebsiteTool._run (agent tool call) [tool (handler)]
  - lib/crewai-tools/src/crewai_tools/rag/loaders/webpage_loader.py:28 — entry point: WebsiteSearchTool.add / RagTool.add(data_type=WEBSITE) -> WebPageLoader.load [RAG loader (lower-level API)]
  - lib/crewai-tools/src/crewai_tools/rag/loaders/docs_site_loader.py:29 — entry point: CodeDocsSearchTool.add -> RagTool.add(data_type=DOCS_SITE) -> DocsSiteLoader.load [RAG loader (lower-level API)]
  - lib/crewai-tools/src/crewai_tools/rag/loaders/pdf_loader.py:50 — entry point: PDFSearchTool.add -> RagTool.add(data_type=PDF_FILE) -> PDFLoader._download_from_url [RAG loader (lower-level API)]
  - lib/crewai-tools/src/crewai_tools/rag/loaders/docx_loader.py:46 — entry point: DOCXSearchTool.add -> RagTool.add(data_type=DOCX) -> DOCXLoader._download_from_url [RAG loader (lower-level API)]
  - lib/crewai-tools/src/crewai_tools/rag/loaders/utils.py:37 — entry point: CSV/JSON/XML/MDX SearchTool.add -> RagTool.add -> {CSV,JSON,XML,MDX}Loader -> load_from_url [shared helper (lower-level API)]
  - fix.diff:123-216 — entry point: new crewai_tools.security.safe_requests.safe_get (public helper) [security utility (new)]
- Uncovered routes to confirm (pattern B):   - lib/crewai-tools/src/crewai_tools/tools/selenium_scraping_tool/selenium_scraping_tool.py:195-206 — SeleniumScrapingTool fetches agent-supplied URL in a local browser with only an http(s) regex, no validate_url on the URL or on redirects (reason to dismiss: Browser-driven transport, not requests; redirects (and JS navigation) cannot be checked per hop, and the tool never had validate_url, so it reads as a separate feature outside a 'redirect bypass' fix.; still in latest: unknown)
  - lib/crewai-tools/src/crewai_tools/tools/serply_api_tool/serply_news_search_tool.py:76-82 — SerplyNewsSearchTool follows each search-result link with requests.get (redirects on) without validate_url (reason to dismiss: Link URLs come from the Serply API response rather than the user/agent, and the tool is a search tool, not a scraper.; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it. The main lever must be HOW-type (its fix needs the mechanism understood: a producer the check never calls, a coupled must-keep-working value, a shape a plausible check mishandles, a route where the protection never existed); another entry point or a planted copy is only an extra;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by the task's one general property (never by a sentence of its own), and placed where the published fix never touches. First list EVERY possible sibling site and route you can find (the screener's O8/O8b leads plus your own search of the code). Then pick 2–4 of them: the most complex and hardest to find of all the candidates (how-type over where-type, far from where the report leads, with a plausible reason to dismiss), each with a different reason a solver would skip it. Record the full candidate list, and why each pick beat the others, in notes.md;
  - write the security property ONCE, in general terms over the protected data or outcome, before choosing routes. Every route and sibling must fall under it as written; the report must not describe where any of them lives;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/crewai-ds/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/crewai-ds/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/crewai-ds/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/crewai-ds/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/crewai-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/crewai-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/crewai-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py crewai-ds --only static
python3 -I builder/gate.py crewai-ds --only nop
python3 -I builder/gate.py crewai-ds --only oracle
python3 -I builder/gate.py crewai-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/crewai-ds/`;
  - edit only `tasks/crewai-ds/`, `build/crewai-ds/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
