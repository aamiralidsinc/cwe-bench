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

Project root: `/home/mara/cwe-bench`. Task: `ip-address-s2`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-22JQ-VG5J-6VGG", "CVE-2026-54272"]; beaugunderson/ip-address; IP-literal misclassification / SSRF guard bypass (CWE-20 improper input validation, CWE-918 SSRF) - an embedded IPv4 is never normalised before the trust decision
- Pinned (vulnerable) commit: e82a6812ac9d16f1300d3c2051fe2cc88c5d9161. Published fix: 4a1f613f4c1bec915677dea923c10aaa09361ef9.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v2",
 "model": "deepseek-flash",
 "entry_id": "7328",
 "advisory_ids": [
  "GHSA-22JQ-VG5J-6VGG",
  "CVE-2026-54272"
 ],
 "repo": "beaugunderson/ip-address",
 "pinned_commit": "e82a6812ac9d16f1300d3c2051fe2cc88c5d9161",
 "fix_commits": [
  "4a1f613f4c1bec915677dea923c10aaa09361ef9"
 ],
 "trust_decision": {
  "summary": "Whether an IPv6 literal that embeds a routable IPv4 address (IPv4-mapped ::ffff:0:0/96 or NAT64 well-known 64:ff9b::/96) is treated as loopback/link-local/private/CGNAT/broadcast/unspecified, i.e. whether an SSRF allow-list built on Address6's special-property checks can be steered into internal space, is decided by Address6's property checks and by the TYPES table that getType() consults - not by the parser.",
  "evidence": [
   "src/ipv6.ts:1203-1213",
   "src/ipv6.ts:1219-1222",
   "src/ipv6.ts:1267-1269",
   "src/ipv6.ts:1283-1285",
   "src/ipv6.ts:567-576",
   "src/v6/constants.ts:25-53"
  ]
 },
 "landing_point": {
  "where": "src/ipv6.ts:1243",
  "why": "The advisory summary names 'IPv4-mapped/NAT64', and isMapped4() is the only method in the tree that names that concept; README:233 links straight to it. It sits ~25 lines above the special-property checks that never call it."
 },
 "fix_sites": [
  {
   "where": "src/ipv6.ts:1203-1213",
   "entry_point": "new Address6(host).isLinkLocal()",
   "module_kind": "library public API"
  },
  {
   "where": "src/ipv6.ts:1219-1222",
   "entry_point": "new Address6(host).isMulticast()",
   "module_kind": "library public API"
  },
  {
   "where": "fix.diff:97-103",
   "entry_point": "new Address6(host).embeddedIPv4() (new method, inserted after src/ipv6.ts:1245)",
   "module_kind": "library public API"
  },
  {
   "where": "src/ipv6.ts:1267-1269",
   "entry_point": "new Address6(host).isLoopback()",
   "module_kind": "library public API"
  },
  {
   "where": "fix.diff:134-141",
   "entry_point": "new Address6(host).isPrivate() (new method)",
   "module_kind": "library public API"
  },
  {
   "where": "fix.diff:151-158",
   "entry_point": "new Address6(host).isCGNAT() (new method)",
   "module_kind": "library public API"
  },
  {
   "where": "fix.diff:168-175",
   "entry_point": "new Address6(host).isBroadcast() (new method)",
   "module_kind": "library public API"
  },
  {
   "where": "src/ipv6.ts:1283-1285",
   "entry_point": "new Address6(host).isUnspecified()",
   "module_kind": "library public API"
  },
  {
   "where": "src/v6/constants.ts:44-52",
   "entry_point": "new Address6(host).getType() (TYPES gains '::ffff:0:0/96' at the line-46 insertion point)",
   "module_kind": "constants / type lookup table"
  },
  {
   "where": "src/ipv6.ts:1476-1480",
   "entry_point": "embeddedIPv4() constant NAT64_WELL_KNOWN_SUBNET = 64:ff9b::/96 (appended to the module-level subnet list)",
   "module_kind": "module-level constant"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/v6/constants.ts:25-53"
 },
 "O3_reason_to_dismiss": "A solver can argue the constants table only feeds the display label from getType(), so the property checks can all be fixed inside src/ipv6.ts and the TYPES edit skipped; the same argument extends to 'getScope() is multicast scope, not a trust check' and '6to4/Teredo need a relay, the advisory names only mapped and NAT64'.",
 "O4_distance": {
  "files": 3,
  "packages": 0,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Embedded-IPv4 extraction must stay gated on mapped-or-well-known-NAT64 and must not reclassify native addresses whose trailing 32 bits happen to look internal: with to4() applied unconditionally 2001:db8::a9fe:a9fe would read link-local and fe80::a9fe:a9fe link-local; the fix also deliberately returns null for NAT64 local-use 64:ff9b:1::/48, and isULA() must stay fc00::/7-only rather than absorbing ::ffff:10.0.0.1 (documented at README:237).",
  "where": "src/ipv6.ts:894-910, src/ipv6.ts:1275-1277"
 },
 "O6_input_shapes": [
  "IPv4-mapped ::ffff:0:0/96 in dotted-quad notation (::ffff:127.0.0.1, ::ffff:169.254.169.254)",
  "IPv4-mapped in hex-group notation (::ffff:7f00:1, ::ffff:a9fe:a9fe)",
  "NAT64 well-known 64:ff9b::/96 in hex form (64:ff9b::7f00:1, 64:ff9b::a9fe:a9fe)",
  "NAT64 with a dotted-quad suffix (64:ff9b::127.0.0.1), which the parser accepts via parse4in6",
  "mapped public addresses that must stay global (::ffff:8.8.8.8)",
  "native IPv6 unchanged (::1, ::, fe80::1, fc00::1, ff02::1, 2001:db8::1)",
  "NAT64 local-use 64:ff9b:1::/48 deliberately excluded from extraction"
 ],
 "O7_producer": {
  "kind": "mapper",
  "where": "src/ipv6.ts:735-773 (parse4in6 sets this.address4/this.v4 only when the literal was written with a dotted-quad tail)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Address6.getScope() returns 'Global' for ::ffff:127.0.0.1 and 64:ff9b::7f00:1 both before and after the fix; a guard that allows scope==='Global' is still bypassed",
   "where": "src/ipv6.ts:540-561",
   "reason_to_dismiss": "getScope() is RFC 4007 multicast/unicast scope, not a trust-boundary check; the advisory names the boolean property checks",
   "distance": "same file, ~700 lines from the checks",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "6to4 (2002:7f00:0001::) and Teredo (2001::/32) literals embed an IPv4 gateway/client address that embeddedIPv4() never extracts, so isLoopback/isLinkLocal/isPrivate stay false for them",
   "where": "src/ipv6.ts:937-1016, src/ipv6.ts:1251-1261",
   "reason_to_dismiss": "6to4/Teredo need a relay or tunnel endpoint, and the advisory names only IPv4-mapped and NAT64; the repo exposes them as separate inspect*/is* features",
   "distance": "same file, separate feature block",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "A literal carrying a CIDR prefix is still misclassified: new Address6('::ffff:127.0.0.1/96').isLoopback() is false because isInSubnet() bails when this.subnetMask < 96 (common.ts:10) so isMapped4() is false, and when it does reach to4() a /96 prefix yields Address4 127.0.0.1/0 whose checks all fail",
   "where": "src/common.ts:9-19, src/ipv6.ts:894-910",
   "reason_to_dismiss": "a URL host literal never carries a CIDR prefix, so prefixed input is an unsupported shape",
   "distance": "cause sits in a different module (src/common.ts)",
   "present_in_latest": "unknown",
   "latest_where": ""
  },
  {
   "route": "Addresses produced by Address6.fromAddress4Nat64(v4, '64:ff9b:1::/48') (or any RFC 6052 prefix other than /96) are not normalised: embeddedIPv4() hardcodes 64:ff9b::/96 and takes the trailing 32 bits, while the repo's own toAddress4Nat64(prefix) knows how to split the octets around the reserved bits for /32-/64",
   "where": "src/ipv6.ts:1048-1116",
   "reason_to_dismiss": "local-use NAT64 / non-/96 prefixes are an unsupported combination and the trailing-32 shortcut is deliberately not applied there",
   "distance": "same file, encoder/decoder pair ~200 lines from the checks",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/ipv6.ts:1089",
   "sibling": "toAddress4Nat64(prefix) / fromAddress4Nat64(prefix) sibling that normalises any RFC 6052 prefix length, not just /96",
   "why_realistic": "the encoder/decoder pair already supports /32,/40,/48,/56,/64,/96 and is the obvious primitive a maintainer would reuse instead of a second hardcoded /96 shortcut"
  },
  {
   "where": "src/ipv6.ts:1002",
   "sibling": "inspect6to4()/inspectTeredo() returning an embedded Address4 that the property checks consult",
   "why_realistic": "both methods already decode an embedded IPv4 and the codebase's stated reason for the fix (classify a literal by what it reaches) applies verbatim to them"
  },
  {
   "where": "src/ipv6.ts:735",
   "sibling": "a second producer that fills this.address4/this.v4 for hex-notation mapped literals so object state matches the property checks",
   "why_realistic": "the parser currently produces address4 only for dotted-quad input, and is4() (README:232) exposes that notation-level asymmetry, so a maintainer could extend parse4in6"
  },
  {
   "where": "src/v6/constants.ts:25",
   "sibling": "a per-prefix classification flag in TYPES (e.g. 'internal: true') that embeddedIPv4() and getType() both read",
   "why_realistic": "the fix already had to add one row to this table, so enriching rows rather than hardcoding subnets in ipv6.ts is a natural next maintainer step"
  }
 ],
 "O9_family": "IP-literal misclassification / SSRF guard bypass (CWE-20 improper input validation, CWE-918 SSRF) - an embedded IPv4 is never normalised before the trust decision",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript",
  "toolchain": "Node >= 12 (package.json engines), tsc <5.6 for build, mocha 11 + tsx + source-map-support via .mocharc.yml, c8 for coverage",
  "services": [],
  "offline_after_build": true,
  "project_tests": "mocha specs in test/*.ts; test/functionality-v6-test.ts already covers isMapped4 with both notations (1099-1137), the is4/isMapped4 differential (1128-1136), NAT64 getType (87-92), getScope (35-69) and isULA (1069-1082); the file ends at 1244, so none of the fix's new regression block exists at the pinned commit"
 },
 "O11_fix_minutes": 40,
 "O12_red_flags": [
  "tiny_repo"
 ],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/ipv6.ts, src/v6/constants.ts",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add 'if (this.isMapped4()) return this.to4().isX()' to each existing check - covers ::ffff:0:0/96 in every notation but leaves all 64:ff9b::/96 NAT64 literals global and never adds isPrivate/isCGNAT/isBroadcast."
 },
 "out_of_scope_notes": [
  "Not pursued: the href()/link() HTML builders in the same class use helpers.escapeHtml and are unrelated to this advisory; no other security-relevant observation was made outside the address-classification scope."
 ],
 "unverified": [
  "repo_mb not measured (no shell in this session); tiny_repo is asserted from the file inventory - 12 TypeScript files, largest src/ipv6.ts at 1481 lines - far below 5 MB of source.",
  "Whether the hidden behavioural tests require the three methods the fix introduces (Address6.isPrivate/isCGNAT/isBroadcast, absent at the pinned commit) is unknown; if they do, the problem report must name them or the task becomes API-shape guessing.",
  "present_in_latest is 'unknown' for every O8 route: the input states no latest release for O8, so latest code could not be inspected."
 ]
}
  ```
- Published fix sites:   - src/ipv6.ts:1203-1213 — entry point: new Address6(host).isLinkLocal() [library public API]
  - src/ipv6.ts:1219-1222 — entry point: new Address6(host).isMulticast() [library public API]
  - fix.diff:97-103 — entry point: new Address6(host).embeddedIPv4() (new method, inserted after src/ipv6.ts:1245) [library public API]
  - src/ipv6.ts:1267-1269 — entry point: new Address6(host).isLoopback() [library public API]
  - fix.diff:134-141 — entry point: new Address6(host).isPrivate() (new method) [library public API]
  - fix.diff:151-158 — entry point: new Address6(host).isCGNAT() (new method) [library public API]
  - fix.diff:168-175 — entry point: new Address6(host).isBroadcast() (new method) [library public API]
  - src/ipv6.ts:1283-1285 — entry point: new Address6(host).isUnspecified() [library public API]
  - src/v6/constants.ts:44-52 — entry point: new Address6(host).getType() (TYPES gains '::ffff:0:0/96' at the line-46 insertion point) [constants / type lookup table]
  - src/ipv6.ts:1476-1480 — entry point: embeddedIPv4() constant NAT64_WELL_KNOWN_SUBNET = 64:ff9b::/96 (appended to the module-level subnet list) [module-level constant]
- Uncovered routes to confirm (pattern B):   - src/ipv6.ts:540-561 — Address6.getScope() returns 'Global' for ::ffff:127.0.0.1 and 64:ff9b::7f00:1 both before and after the fix; a guard that allows scope==='Global' is still bypassed (reason to dismiss: getScope() is RFC 4007 multicast/unicast scope, not a trust-boundary check; the advisory names the boolean property checks; still in latest: unknown)
  - src/ipv6.ts:937-1016, src/ipv6.ts:1251-1261 — 6to4 (2002:7f00:0001::) and Teredo (2001::/32) literals embed an IPv4 gateway/client address that embeddedIPv4() never extracts, so isLoopback/isLinkLocal/isPrivate stay false for them (reason to dismiss: 6to4/Teredo need a relay or tunnel endpoint, and the advisory names only IPv4-mapped and NAT64; the repo exposes them as separate inspect*/is* features; still in latest: unknown)
  - src/common.ts:9-19, src/ipv6.ts:894-910 — A literal carrying a CIDR prefix is still misclassified: new Address6('::ffff:127.0.0.1/96').isLoopback() is false because isInSubnet() bails when this.subnetMask < 96 (common.ts:10) so isMapped4() is false, and when it does reach to4() a /96 prefix yields Address4 127.0.0.1/0 whose checks all fail (reason to dismiss: a URL host literal never carries a CIDR prefix, so prefixed input is an unsupported shape; still in latest: unknown)
  - src/ipv6.ts:1048-1116 — Addresses produced by Address6.fromAddress4Nat64(v4, '64:ff9b:1::/48') (or any RFC 6052 prefix other than /96) are not normalised: embeddedIPv4() hardcodes 64:ff9b::/96 and takes the trailing 32 bits, while the repo's own toAddress4Nat64(prefix) knows how to split the octets around the reserved bits for /32-/64 (reason to dismiss: local-use NAT64 / non-/96 prefixes are an unsupported combination and the trailing-32 shortcut is deliberately not applied there; still in latest: unknown)
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

## Environment (`tasks/ip-address-s2/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/ip-address-s2/instruction.md`)
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

## Tests (`tasks/ip-address-s2/tests/`)
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
- **Wrong-fix patches** go in `build/ip-address-s2/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/ip-address-s2/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/ip-address-s2/manifest.json`:**
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

**Also in `build/ip-address-s2/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py ip-address-s2 --only static
python3 -I common/gate/gate.py ip-address-s2 --only nop
python3 -I common/gate/gate.py ip-address-s2 --only oracle
python3 -I common/gate/gate.py ip-address-s2 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/ip-address-s2/`;
  - edit only `tasks/ip-address-s2/`, `build/ip-address-s2/` and, for pattern B, the register;
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
