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

Project root: `/home/mara/cwe-bench`. Task: `stk-pyload-ghsa7gvf`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-m74m-f7cr-432x; GHSA-7gvf-3w72-p2pg
- Pinned (vulnerable) commit: 6176863f1348a123f91291e8a493fe26f0375196. Published fix: b76b6d4ee5e3, 33c55da08432.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-7gvf-3w72-p2pg",
 "pattern": "H3a",
 "repo": "pyload/pyload",
 "pinned_commit": "6176863f1348a123f91291e8a493fe26f0375196",
 "protections": [
  "P1 (SSRF destination filter): every outbound fetch of a user-supplied URL, including each redirect hop, must connect only to globally routable addresses (helper exists at src/pyload/core/utils/web/check.py:86-100 but nothing calls it)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/pyload/plugins/base/downloader.py:318",
    "src/pyload/plugins/base/downloader.py:332",
    "src/pyload/plugins/base/downloader.py:237"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "src/pyload/plugins/base/downloader.py:318 (dl_url = self.fixurl(url), no destination check before fetch)",
    "src/pyload/plugins/base/downloader.py:237-249 (req.http_download(url, ...) called directly)",
    "src/pyload/core/managers/plugin_manager.py:372-373 (unmatched http(s) URLs fall back to DefaultPlugin)",
    "src/pyload/plugins/downloaders/Http.py:72 (self.download(url, ...))",
    "src/pyload/core/api/__init__.py:529-558 (add_package passes user links straight to files.add_links)",
    "src/pyload/core/utils/web/check.py:86-100 (is_global_address defined; repo-wide grep finds no caller)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M3",
   "origin": "advisory_route",
   "locations": [
    "src/pyload/core/network/http/http_request.py:114",
    "src/pyload/core/network/http/http_request.py:115",
    "src/pyload/core/network/http/http_chunk.py:151",
    "src/pyload/core/network/http/http_chunk.py:187"
   ],
   "reason_to_dismiss": "the initial URL is checked, and redirects are needed because hosters routinely redirect to CDN download servers",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "bypassed",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "src/pyload/core/network/http/http_request.py:114-115 (FOLLOWLOCATION=1, MAXREDIRS=10 on every handle; libcurl follows Location internally with no per-hop check)",
    "src/pyload/core/network/http/http_chunk.py:151 (download chunks reuse init_handle, so they also follow redirects)",
    "src/pyload/core/network/http/http_chunk.py:187-188 (chunk handle built from the original p.url only)",
    "src/pyload/core/network/http/http_request.py:341-351 (load() turns redirects off only when redirect is falsy; the default is True at src/pyload/plugins/base/plugin.py:164)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "src/pyload/plugins/base/downloader.py:172",
    "src/pyload/plugins/base/downloader.py:181-189"
   ],
   "reason_to_dismiss": "only a HEAD probe (just_header=True) and nothing is saved, so it doesn't look like a download path",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/pyload/plugins/base/downloader.py:172 (self.load(url, just_header=True, redirect=False) on the raw user URL)",
    "src/pyload/plugins/base/downloader.py:181-189 (hand-written redirect loop: Location header -> fixurl -> self.load(location), no destination check)",
    "src/pyload/plugins/base/simple_downloader.py:466 (handle_direct calls isresource(pyfile.url))",
    "src/pyload/plugins/downloaders/TorboxApp.py:77 (isresource(pyfile.url))"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "src/pyload/core/api/__init__.py:587-589",
    "src/pyload/core/network/request_factory.py:58-64",
    "src/pyload/core/network/request_factory.py:123-124"
   ],
   "reason_to_dismiss": "parse_urls is a link-extraction helper in the API module, not the BaseDownloader download path the report names",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/pyload/core/api/__init__.py:587-589 (page = get_url(url); URLs extracted from the response are returned to the caller)",
    "src/pyload/core/network/request_factory.py:62-63 (fresh HTTPRequest(...).load, which follows redirects by default)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "src/pyload/plugins/base/container.py:57-60",
    "src/pyload/plugins/containers/TXT.py:13"
   ],
   "reason_to_dismiss": "containers look like locally uploaded files, and the remote branch goes through plugin.load rather than download()",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/pyload/plugins/base/container.py:57-60 (remote = bool(netloc); content = self.load(self.pyfile.url))",
    "src/pyload/plugins/containers/TXT.py:13 (pattern .+\\.(txt|text)$, so any http URL ending in .txt routes here)",
    "src/pyload/core/managers/plugin_manager.py:361-370 (container plugins are matched before the DefaultPlugin fallback)",
    "src/pyload/plugins/base/plugin.py:200-210 (req.load(..., redirect=redirect) with default redirect=True)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M7",
   "origin": "injection_room",
   "locations": [
    "src/pyload/core/network/http/http_request.py:260",
    "src/pyload/core/network/http/http_request.py:351"
   ],
   "reason_to_dismiss": "DNS rebinding between the check and the connect looks theoretical; resolving once and checking feels sufficient",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "xhard",
   "type": "both",
   "evidence": [
    "src/pyload/core/network/http/http_request.py:260 (only the URL string goes to curl; no CURLOPT_RESOLVE pin or socket callback anywhere in init_handle at :110-138)",
    "src/pyload/core/network/http/http_request.py:351 (c.perform() resolves the host again on its own)",
    "src/pyload/core/utils/web/convert.py:28 (a Python-side check would resolve separately via socket.getaddrinfo)"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M8",
   "origin": "injection_room",
   "locations": [
    "src/pyload/core/utils/web/convert.py:24-33",
    "src/pyload/core/network/http/http_request.py:179-182"
   ],
   "reason_to_dismiss": "host_to_ip is the repo's own resolver, created in the pinned commit, so it looks like the intended building block",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/pyload/core/utils/web/convert.py:28 (getaddrinfo(..., family=socket.AF_INET): AAAA records are never seen; an IPv6-only host returns [])",
    "src/pyload/core/network/http/http_request.py:179-180 (when download.ipv6 is on, curl uses IPRESOLVE_WHATEVER and may connect over IPv6)",
    "src/pyload/core/utils/web/check.py:97-100 (is_global_address returns False for an empty/invalid value, so the result depends on how the caller handles an empty IP list)"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "src/pyload/core/network/http/http_request.py:154-177",
    "src/pyload/core/network/request_factory.py:78-99"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/pyload/core/network/http/http_request.py:154-177 (a configured proxy, which can legitimately be loopback/LAN, becomes the actual connect peer)",
    "src/pyload/core/network/http/http_request.py:160-169 (SOCKS4A / SOCKS5_HOSTNAME when socks_resolve_dns is set: the proxy resolves the target, not the local resolver)",
    "src/pyload/core/network/request_factory.py:82-99 (proxy host/port come from stored config)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T3",
   "T4",
   "T5"
  ],
  [
   "T2"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": false,
  "masking": [
   "T2 (and the per-hop half of T3) only counts as a filter bypass once T1's initial-URL check exists; in the pinned tree no check exists at all (check.py:86 has no callers), so fixing A is what exposes B."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T2",
   "b": "T1",
   "what": "The natural fix for T2, turning FOLLOWLOCATION off globally (http_request.py:114), breaks every hoster/CDN redirect that plugin.load relies on by default (plugin.py:164 redirect=True). Redirects to public hosts must keep working, so the fix has to check each hop."
  },
  {
   "a": "T6",
   "b": "T8",
   "what": "Pinning or checking the connected socket address (the robust T6 fix) checks the proxy's address when a proxy is configured (http_request.py:171-172). That rejects a legitimate loopback/LAN proxy and never sees the real target; with SOCKS remote DNS (:163-168) local resolution is irrelevant."
  },
  {
   "a": "T1",
   "b": "T5",
   "what": "A guard that rejects any non-global or hostless target would also reject the local-path container branch (container.py:57 remote=False), which must keep working for uploaded containers."
  }
 ],
 "fairness_risks": [
  "Downloading from a LAN host such as a NAS at 192.168.x.x through DefaultPlugin is a plausible legitimate use that a strict non-global rule refuses; the pinned code has no allow-list or config switch for it.",
  "A loopback/LAN proxy (http_request.py:154-177) must keep working; a test that refuses non-global connect peers would break it.",
  "Redirects to public CDN hosts must keep working (plugin.py:164, downloader.py:185); a 'no redirects' rule contradicts normal hoster behaviour.",
  "Local container paths (container.py:57 remote=False) and the tmp_ upload path (api/__init__.py:658-665) must not go through a network-address check.",
  "A T6 hidden test has to fix how resolution is mocked (getaddrinfo vs curl's own resolver), so it may unfairly bind the solver to one implementation."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T2",
   "T4",
   "T7",
   "T8"
  ],
  "why": "These are four independent groups. T2 is the advisory B route and sits in the lower network layer (M3). T4 is a deepseek-type M1 entry point in the API module with a strong reason to dismiss ('not a download'). T7 is a mimo-type shape trap: the repo's freshly added IPv4-only resolver lures solvers. T8 is a mimo-type coupled value: proxy connect peers are legitimately loopback, which punishes over-hardening. T1 must be fixed anyway because A is absent from the pinned tree. T3/T5 are alternatives to T4 but share its group: one guard at HTTPRequest.set_request_context (http_request.py:224-260), which HTTPChunk.get_handle also calls (http_chunk.py:187), closes all of T1/T3/T4/T5. T4 is the one furthest from the report. T6 is left out because a test for it is hard to make fair."
 },
 "unverified": [
  "Whether fix A (b76b6d4ee5e3) is an ancestor of the pinned commit: is_global_address exists but has no caller anywhere under src/, so the pinned tree looks like it predates A's guard. Git history was not inspected.",
  "a_fix_leaves_b_open: A's actual code is not in the pinned tree, so it can't be confirmed here; the advisory summary says 'incomplete fix'.",
  "b_in_code_a_wrote=false rests on the redirect handling (http_request.py:114, downloader.py:181-189) being pre-existing code. Not confirmed against A's diff.",
  "Whether upstream B fix 33c55da08432 also covers parse_urls (T4), container remote fetch (T5) or isresource (T3), or only BaseDownloader.download.",
  "Whether upstream added a config switch to allow LAN/private destinations (affects the fairness of a strict non-global test).",
  "Excluded as protocol variants and not recorded as traps: non-http schemes (file://, gopher://) reaching curl with no CURLOPT_PROTOCOLS restriction (http_request.py:110-138), and XDCC's raw socket connect to the URL-supplied IRC server (XDCC.py:139) or the bot-supplied DCC IP (XDCC.py:1123, 1142). libcurl's default REDIR_PROTOCOLS depends on its version and was not checked.",
  "Browser.load delegating to HTTPRequest.load/set_request_context (needed for the T1/T3/T4/T5 shared-guard grouping) was inferred from plugin.py:200 and request_factory.py:39; browser.py was not read."
 ]
}
  ```
- Published fix sites:   - src/pyload/plugins/base/downloader.py:318 — T1 M4 (reason to dismiss: none)
  - src/pyload/plugins/base/downloader.py:332 — T1 M4 (reason to dismiss: none)
  - src/pyload/plugins/base/downloader.py:237 — T1 M4 (reason to dismiss: none)
  - src/pyload/core/network/http/http_request.py:114 — T2 M3 (reason to dismiss: the initial URL is checked, and redirects are needed because hosters routinely redirect to CDN download servers)
  - src/pyload/core/network/http/http_request.py:115 — T2 M3 (reason to dismiss: the initial URL is checked, and redirects are needed because hosters routinely redirect to CDN download servers)
  - src/pyload/core/network/http/http_chunk.py:151 — T2 M3 (reason to dismiss: the initial URL is checked, and redirects are needed because hosters routinely redirect to CDN download servers)
  - src/pyload/core/network/http/http_chunk.py:187 — T2 M3 (reason to dismiss: the initial URL is checked, and redirects are needed because hosters routinely redirect to CDN download servers)
- Uncovered routes to confirm (pattern B):   - src/pyload/plugins/base/downloader.py:172 — T3 M2 (reason to dismiss: only a HEAD probe (just_header=True) and nothing is saved, so it doesn't look like a download path)
  - src/pyload/plugins/base/downloader.py:181-189 — T3 M2 (reason to dismiss: only a HEAD probe (just_header=True) and nothing is saved, so it doesn't look like a download path)
  - src/pyload/core/api/__init__.py:587-589 — T4 M1 (reason to dismiss: parse_urls is a link-extraction helper in the API module, not the BaseDownloader download path the report names)
  - src/pyload/core/network/request_factory.py:58-64 — T4 M1 (reason to dismiss: parse_urls is a link-extraction helper in the API module, not the BaseDownloader download path the report names)
  - src/pyload/core/network/request_factory.py:123-124 — T4 M1 (reason to dismiss: parse_urls is a link-extraction helper in the API module, not the BaseDownloader download path the report names)
  - src/pyload/plugins/base/container.py:57-60 — T5 M1 (reason to dismiss: containers look like locally uploaded files, and the remote branch goes through plugin.load rather than download())
  - src/pyload/plugins/containers/TXT.py:13 — T5 M1 (reason to dismiss: containers look like locally uploaded files, and the remote branch goes through plugin.load rather than download())
- Design plan from the lead: TRACK = STACKED (H3a). Build the stacked design the reader chose: traps T2, T4, T7, T8. Why: These are four independent groups. T2 is the advisory B route and sits in the lower network layer (M3). T4 is a deepseek-type M1 entry point in the API module with a strong reason to dismiss ('not a download'). T7 is a mimo-type shape trap: the repo's freshly added IPv4-only resolver lures solvers. T8 is a mimo-type coupled value: proxy connect peers are legitimately loopback, which punishes over-hardening. T1 must be fixed anyway because A is absent from the pinned tree. T3/T5 are alternatives to T4 but share its group: one guard at HTTPRequest.set_request_context (http_request.py:224-260), which HTTPChunk.get_handle also calls (http_chunk.py:187), closes all of T1/T3/T4/T5. T4 is the one furthest from the report. T6 is left out because a test for it is hard to make fair. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Downloading from a LAN host such as a NAS at 192.168.x.x through DefaultPlugin is a plausible legitimate use that a strict non-global rule refuses; the pinned code has no allow-list or config switch for it. | A loopback/LAN proxy (http_request.py:154-177) must keep working; a test that refuses non-global connect peers would break it. | Redirects to public CDN hosts must keep working (plugin.py:164, downloader.py:185); a 'no redirects' rule contradicts normal hoster behaviour. | Local container paths (container.py:57 remote=False) and the tmp_ upload path (api/__init__.py:658-665) must not go through a network-address check. | A T6 hidden test has to fix how resolution is mocked (getaddrinfo vs curl's own resolver), so it may unfairly bind the solver to one implementation.. Conflicts the reader found: The natural fix for T2, turning FOLLOWLOCATION off globally (http_request.py:114), breaks every hoster/CDN redirect that plugin.load relies on by default (plugin.py:164 redirect=True). Redirects to public hosts must keep working, so the fix has to check each hop. | Pinning or checking the connected socket address (the robust T6 fix) checks the proxy's address when a proxy is configured (http_request.py:171-172). That rejects a legitimate loopback/LAN proxy and never sees the real target; with SOCKS remote DNS (:163-168) local resolution is irrelevant. | A guard that rejects any non-global or hostless target would also reject the local-path container branch (container.py:57 remote=False), which must keep working for uploaded containers.

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

## Environment (`tasks/stk-pyload-ghsa7gvf/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-pyload-ghsa7gvf/instruction.md`)
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

## Tests (`tasks/stk-pyload-ghsa7gvf/tests/`)
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
- **Wrong-fix patches** go in `build/stk-pyload-ghsa7gvf/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-pyload-ghsa7gvf/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-pyload-ghsa7gvf/manifest.json`:**
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

**Also in `build/stk-pyload-ghsa7gvf/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-pyload-ghsa7gvf --only static
python3 -I builder/gate.py stk-pyload-ghsa7gvf --only nop
python3 -I builder/gate.py stk-pyload-ghsa7gvf --only oracle
python3 -I builder/gate.py stk-pyload-ghsa7gvf --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-pyload-ghsa7gvf/`;
  - edit only `tasks/stk-pyload-ghsa7gvf/`, `build/stk-pyload-ghsa7gvf/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-7gvf-3w72-p2pg.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-pyload-ghsa7gvf`. Control task slug: `stk-pyload-ghsa7gvf-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-7gvf-3w72-p2pg.json`.
