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

Project root: `/home/mara/cwe-bench`. Task: `stk-mistral-rs-21576`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 21576; SSRF plus arbitrary local file read through an untrusted media source 
- Pinned (vulnerable) commit: 7af17b627a88533d2fe6e192ed8db6c908e5ce5a. Published fix: 74793379649febc758b6a0d4b71aa6aeabc80f9c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-21576",
 "pattern": "H4",
 "repo": "ericlbuehler/mistral.rs",
 "pinned_commit": "7af17b627a88533d2fe6e192ed8db6c908e5ce5a",
 "protections": [
  "P1: a media or file source string taken from an HTTP request body (image_url, audio_url, video_url, Anthropic url source, Responses input_image/input_file) must not name a server-local file (bare path or file://) and must not be fetched from a loopback, private, link-local or local-named host, judged on the resolved address and re-checked on every redirect. Trusted in-process callers (CLI interactive mode, library users) keep local-file access."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "mistralrs-server-core/src/util.rs:45",
    "mistralrs-server-core/src/util.rs:48",
    "mistralrs-server-core/src/util.rs:61",
    "mistralrs-server-core/src/util.rs:65",
    "mistralrs-server-core/src/chat_completion.rs:931"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "mistralrs-server-core/src/util.rs:46-57 (any URL parses; otherwise a bare path is accepted if File::open succeeds)",
    "mistralrs-server-core/src/util.rs:59-64 (reqwest::get on any http/https host, default redirect policy, no host check)",
    "mistralrs-server-core/src/util.rs:65-78 (file:// read of the whole file)",
    "mistralrs-server-core/src/chat_completion.rs:729-742 (image_url.url taken from the request body)",
    "mistralrs-server-core/src/chat_completion.rs:930-933 (request URL passed directly to parse_image_url)"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "locations": [
    "mistralrs-server-core/src/util.rs:91",
    "mistralrs-server-core/src/util.rs:94",
    "mistralrs-server-core/src/util.rs:106",
    "mistralrs-server-core/src/chat_completion.rs:940"
   ],
   "reason_to_dismiss": "The report names images; audio is a separate content-part type and a separate function.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "mistralrs-server-core/src/util.rs:92-128 (same bare-path, file:// and unrestricted reqwest::get logic copied for audio)",
    "mistralrs-server-core/src/chat_completion.rs:743-756 (audio_url.url taken from the request body)",
    "mistralrs-server-core/src/chat_completion.rs:939-943 (passed to parse_audio_url)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "mistralrs-server-core/src/video.rs:51",
    "mistralrs-server-core/src/video.rs:54",
    "mistralrs-server-core/src/video.rs:66",
    "mistralrs-server-core/src/video.rs:70",
    "mistralrs-server-core/src/chat_completion.rs:949"
   ],
   "reason_to_dismiss": "video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "mistralrs-server-core/src/video.rs:1-4 (module doc: frame extraction for server and CLI)",
    "mistralrs-server-core/src/video.rs:52-63 (bare-path probe)",
    "mistralrs-server-core/src/video.rs:65-69 (unrestricted reqwest::get)",
    "mistralrs-server-core/src/video.rs:70-80 (file:// read)",
    "mistralrs-server-core/src/chat_completion.rs:51 (import of video::parse_video_url)",
    "mistralrs-server-core/src/chat_completion.rs:757-770 (video_url.url taken from the request body)",
    "mistralrs-server-core/src/chat_completion.rs:948-952 (passed to parse_video_url)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M8",
   "origin": "published_fix_far_site",
   "locations": [
    "mistralrs-server-core/src/input_files.rs:94",
    "mistralrs-server-core/src/input_files.rs:99",
    "mistralrs-server-core/src/input_files.rs:103",
    "mistralrs-server-core/src/input_files.rs:132",
    "mistralrs-server-core/src/input_files.rs:143",
    "mistralrs-server-core/src/chat_completion.rs:837"
   ],
   "reason_to_dismiss": "input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "mistralrs-server-core/src/input_files.rs:132-164 (check is on the literal host string only: names other than localhost/*.localhost/*.local are never resolved, so a public name that resolves to a private address passes)",
    "mistralrs-server-core/src/input_files.rs:99-109 (check runs once on the initial URL; client follows up to 3 redirects via Policy::limited, and redirect targets are not re-checked)",
    "mistralrs-server-core/src/input_files.rs:143 (host_str() for an IPv6 literal is bracketed, e.g. \"[::1]\", so parse::<IpAddr>() fails and the V6 branch at 152-157 never runs; IPv4-mapped IPv6 is not handled either)",
    "mistralrs-server-core/src/input_files.rs:144-151 (IPv4 list omits CGNAT 100.64/10 and other special ranges)",
    "mistralrs-server-core/src/input_files.rs:187-191 (only test: literal 127.0.0.1)",
    "mistralrs-server-core/src/chat_completion.rs:785-791 (file_url refused on Chat Completions surface, so only Responses reaches it)",
    "mistralrs-server-core/src/responses.rs:222-227 (Responses input_file file_url mapped into the spec)",
    "mistralrs-server-core/src/chat_completion.rs:835-840 (resolve_input_file called for each file spec)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "mistralrs-server-core/src/util.rs:240",
    "mistralrs-server-core/src/util.rs:246",
    "mistralrs-server-core/src/util.rs:290",
    "mistralrs-cli/src/commands/run/interactive.rs:329",
    "mistralrs-cli/src/commands/run/interactive.rs:345",
    "mistralrs-cli/src/commands/run/interactive.rs:361"
   ],
   "reason_to_dismiss": "Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "mistralrs-server-core/src/util.rs:13-44 (public doc promises file paths and file:// URLs)",
    "mistralrs-server-core/src/util.rs:240-249 (project test loads a relative path and a file:// URL through parse_image_url)",
    "mistralrs-server-core/src/util.rs:290-298 (data: URLs for image and audio must keep working)",
    "mistralrs-cli/src/commands/run/interactive.rs:329,345,361,1471,1487,1502 (CLI interactive mode uses the same public loaders on local paths a trusted operator typed)",
    "mistralrs-server-core/src/video.rs:3-4 (video loader is shared by server and CLI)"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "mistralrs-server-core/src/anthropic.rs:746",
    "mistralrs-server-core/src/anthropic.rs:889",
    "mistralrs-server-core/src/responses.rs:153",
    "mistralrs-server-core/src/mcp_server.rs:216"
   ],
   "reason_to_dismiss": "These adapters only turn the source into an image_url part; they never fetch it themselves.",
   "distance": {
    "files": 3,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "mistralrs-server-core/src/anthropic.rs:889-891 (Anthropic source type url returned verbatim)",
    "mistralrs-server-core/src/anthropic.rs:746 (wrapped as image_url part)",
    "mistralrs-server-core/src/anthropic.rs:1516,1565 (messages and count_tokens call parse_request)",
    "mistralrs-server-core/src/responses.rs:153-181 (Responses input_image url wrapped as image_url part)",
    "mistralrs-server-core/src/mcp_server.rs:216 (MCP chat tool calls parse_request)"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "mistralrs-pyo3/src/util.rs:201",
    "mistralrs-pyo3/src/util.rs:255",
    "mistralrs-pyo3/src/util.rs:315",
    "mistralrs-pyo3/src/lib.rs:1234",
    "mistralrs-pyo3/src/lib.rs:2179"
   ],
   "reason_to_dismiss": "An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "mistralrs-pyo3/src/util.rs:202-248 (sync copy: bare path, file://, reqwest::blocking::get without host check)",
    "mistralrs-pyo3/src/util.rs:256-302 (audio copy)",
    "mistralrs-pyo3/src/util.rs:316-344 (video copy)",
    "mistralrs-pyo3/src/lib.rs:1234,1240,1246,2179,2185,2191 (called from Python chat paths)"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T6"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T7"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "The natural fix for T1/T2/T3 (drop file:// and bare-path support from util::parse_image_url/parse_audio_url and video::parse_video_url) breaks the CLI interactive callers and the project test at util.rs:240-249. The fix has to be a server-only policy or variant, chosen at chat_completion.rs:931/940/949."
  },
  {
   "a": "T4",
   "b": "T1",
   "what": "Copying the T4 literal-only reject_private_host into the media loaders looks like a consistent fix. It leaves DNS names, redirects and IPv6 literals open in both places, so fixing T1 by reusing T4 carries T4's weakness over."
  }
 ],
 "fairness_risks": [
  "Server-local media paths: a self-hosting operator might legitimately send local paths to their own server. The fix refuses them for HTTP requests, which hidden tests should enforce only on the server path and never on util::parse_image_url's default (Local) behaviour (util.rs:240-249).",
  "data: URLs must stay accepted on all server routes (util.rs:290-298; responses.rs:157; anthropic.rs:887).",
  "Public http(s) media URLs must stay accepted. The existing test needs network to rust-lang.org (util.rs:232-238), so hidden tests must not depend on outbound fetches.",
  "Redirect re-validation and DNS-resolves-to-private cases are hard to test offline: a local test HTTP server sits on 127.0.0.1, which the guard itself must reject. Hidden tests for those shapes need an injectable resolver or client, which a solver's design may not expose. Keep hidden tests to literal IPs (including bracketed IPv6 like [::1] and ::ffff:127.0.0.1), localhost names, bare paths and file:// URLs.",
  "T7 (pyo3) matches the fix's own trusted Local policy, so a hidden test requiring it to reject local files would contradict upstream intent."
 ],
 "effort_minutes": 80,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Four independent groups, each with a different reason to dismiss. T1 (with T2/T6 riding along) is the reported route. T3 is a second loader hidden in a frame-extraction module ('not a URL loader'). T4 is a neighbouring feature with an existing but weak guard ('already protected'); the bracketed-IPv6 host_str bug and the unchecked redirects are concrete and partly testable offline. That makes it the deepseek-type trap. T5 is the coupled must-keep-working local-file behaviour for CLI and the project test. That makes it the mimo-type trap, aimed at over-hardening. T7 is left out because the trusted-caller dismissal is upstream's own position, so a hidden test there would be unfair."
 },
 "unverified": [
  "Pinned commit 7af17b62 is HEAD of the worktree; whether it equals the parent of fix 74793379 was not checked (the fix commit is not in the read tree). The vulnerable code is present at the pinned tree.",
  "url::Url::host_str() returns IPv6 literals in brackets (e.g. \"[::1]\"), which makes input_files.rs:143 never parse IPv6 hosts. This comes from url crate behaviour, not from code read in this repo.",
  "reqwest's default client (used by reqwest::get at util.rs:61, util.rs:106, video.rs:66) follows up to 10 redirects. This is crate default behaviour, not read here.",
  "The Responses route reaching chat_completion::parse_request with tool_surface Responses was inferred from responses.rs:1730 and responses.rs:222-227; the full call chain was not traced.",
  "Whether the MCP server (mcp_server.rs:216) is enabled by default was not checked.",
  "Build cost (large candle workspace) and whether the server-core tests build without a GPU were not checked.",
  "Advisory GHSA-WFGQ-W7CQ-QJ7J text was not read; the protection statement is based on the screener record and the code."
 ]
}
  ```
- Published fix sites:   - mistralrs-server-core/src/util.rs:45 — T1 M4 (reason to dismiss: none)
  - mistralrs-server-core/src/util.rs:48 — T1 M4 (reason to dismiss: none)
  - mistralrs-server-core/src/util.rs:61 — T1 M4 (reason to dismiss: none)
  - mistralrs-server-core/src/util.rs:65 — T1 M4 (reason to dismiss: none)
  - mistralrs-server-core/src/chat_completion.rs:931 — T1 M4 (reason to dismiss: none)
  - mistralrs-server-core/src/util.rs:91 — T2 M1 (reason to dismiss: The report names images; audio is a separate content-part type and a separate function.)
  - mistralrs-server-core/src/util.rs:94 — T2 M1 (reason to dismiss: The report names images; audio is a separate content-part type and a separate function.)
  - mistralrs-server-core/src/util.rs:106 — T2 M1 (reason to dismiss: The report names images; audio is a separate content-part type and a separate function.)
  - mistralrs-server-core/src/chat_completion.rs:940 — T2 M1 (reason to dismiss: The report names images; audio is a separate content-part type and a separate function.)
  - mistralrs-server-core/src/video.rs:51 — T3 M2 (reason to dismiss: video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.)
  - mistralrs-server-core/src/video.rs:54 — T3 M2 (reason to dismiss: video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.)
  - mistralrs-server-core/src/video.rs:66 — T3 M2 (reason to dismiss: video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.)
  - mistralrs-server-core/src/video.rs:70 — T3 M2 (reason to dismiss: video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.)
  - mistralrs-server-core/src/chat_completion.rs:949 — T3 M2 (reason to dismiss: video.rs presents itself as an FFmpeg/GIF frame-extraction module, not a URL loader, and lives outside util.rs where the image/audio loaders are.)
  - mistralrs-server-core/src/input_files.rs:94 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/input_files.rs:99 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/input_files.rs:103 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/input_files.rs:132 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/input_files.rs:143 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/chat_completion.rs:837 — T4 M8 (reason to dismiss: input_file.file_url already has an explicit SSRF guard (reject_private_host) and a unit test asserting 127.0.0.1 is rejected, so it reads as already protected.)
  - mistralrs-server-core/src/util.rs:240 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-server-core/src/util.rs:246 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-server-core/src/util.rs:290 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-cli/src/commands/run/interactive.rs:329 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-cli/src/commands/run/interactive.rs:345 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-cli/src/commands/run/interactive.rs:361 — T5 M11 (reason to dismiss: Removing the file branch and the bare-path probe from the public loaders looks like the cleanest fix and makes the server safe.)
  - mistralrs-server-core/src/anthropic.rs:746 — T6 M1 (reason to dismiss: These adapters only turn the source into an image_url part; they never fetch it themselves.)
  - mistralrs-server-core/src/anthropic.rs:889 — T6 M1 (reason to dismiss: These adapters only turn the source into an image_url part; they never fetch it themselves.)
  - mistralrs-server-core/src/responses.rs:153 — T6 M1 (reason to dismiss: These adapters only turn the source into an image_url part; they never fetch it themselves.)
  - mistralrs-server-core/src/mcp_server.rs:216 — T6 M1 (reason to dismiss: These adapters only turn the source into an image_url part; they never fetch it themselves.)
- Uncovered routes to confirm (pattern B):   - mistralrs-pyo3/src/util.rs:201 — T7 M2 (reason to dismiss: An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.)
  - mistralrs-pyo3/src/util.rs:255 — T7 M2 (reason to dismiss: An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.)
  - mistralrs-pyo3/src/util.rs:315 — T7 M2 (reason to dismiss: An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.)
  - mistralrs-pyo3/src/lib.rs:1234 — T7 M2 (reason to dismiss: An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.)
  - mistralrs-pyo3/src/lib.rs:2179 — T7 M2 (reason to dismiss: An in-process Python library whose caller is trusted, the same as the fix's Local policy. The advisory is about the HTTP server.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T3, T4, T5. Why: Four independent groups, each with a different reason to dismiss. T1 (with T2/T6 riding along) is the reported route. T3 is a second loader hidden in a frame-extraction module ('not a URL loader'). T4 is a neighbouring feature with an existing but weak guard ('already protected'); the bracketed-IPv6 host_str bug and the unchecked redirects are concrete and partly testable offline. That makes it the deepseek-type trap. T5 is the coupled must-keep-working local-file behaviour for CLI and the project test. That makes it the mimo-type trap, aimed at over-hardening. T7 is left out because the trusted-caller dismissal is upstream's own position, so a hidden test there would be unfair. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Server-local media paths: a self-hosting operator might legitimately send local paths to their own server. The fix refuses them for HTTP requests, which hidden tests should enforce only on the server path and never on util::parse_image_url's default (Local) behaviour (util.rs:240-249). | data: URLs must stay accepted on all server routes (util.rs:290-298; responses.rs:157; anthropic.rs:887). | Public http(s) media URLs must stay accepted. The existing test needs network to rust-lang.org (util.rs:232-238), so hidden tests must not depend on outbound fetches. | Redirect re-validation and DNS-resolves-to-private cases are hard to test offline: a local test HTTP server sits on 127.0.0.1, which the guard itself must reject. Hidden tests for those shapes need an injectable resolver or client, which a solver's design may not expose. Keep hidden tests to literal IPs (including bracketed IPv6 like [::1] and ::ffff:127.0.0.1), localhost names, bare paths and file:// URLs. | T7 (pyo3) matches the fix's own trusted Local policy, so a hidden test requiring it to reject local files would contradict upstream intent.. Conflicts the reader found: The natural fix for T1/T2/T3 (drop file:// and bare-path support from util::parse_image_url/parse_audio_url and video::parse_video_url) breaks the CLI interactive callers and the project test at util.rs:240-249. The fix has to be a server-only policy or variant, chosen at chat_completion.rs:931/940/949. | Copying the T4 literal-only reject_private_host into the media loaders looks like a consistent fix. It leaves DNS names, redirects and IPv6 literals open in both places, so fixing T1 by reusing T4 carries T4's weakness over.

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

## Environment (`tasks/stk-mistral-rs-21576/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-mistral-rs-21576/instruction.md`)
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

## Tests (`tasks/stk-mistral-rs-21576/tests/`)
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
- **Wrong-fix patches** go in `build/stk-mistral-rs-21576/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-mistral-rs-21576/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-mistral-rs-21576/manifest.json`:**
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

**Also in `build/stk-mistral-rs-21576/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-mistral-rs-21576 --only static
python3 -I builder/gate.py stk-mistral-rs-21576 --only nop
python3 -I builder/gate.py stk-mistral-rs-21576 --only oracle
python3 -I builder/gate.py stk-mistral-rs-21576 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-mistral-rs-21576/`;
  - edit only `tasks/stk-mistral-rs-21576/`, `build/stk-mistral-rs-21576/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h4-21576.json`. Verify each trap on the
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

Stacked task slug: `stk-mistral-rs-21576`. Control task slug: `stk-mistral-rs-21576-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h4-21576.json`.
