# Fairness review — stk-pyload-ghsa7gvf (stacked H3a, v3 after AUDIT-FIX-20261024)

Reviewed: instruction.md (post-fix), tests/security/test_destination_filter.py (5),
tests/functional/test_legitimate_fetches.py (5), tests/pristine (3), solution/fix.patch,
manifest.json, checks/*.patch. Concepts (manifest.stacking): C1 = shared request-layer
judgement (T1, T4); C2 = per-request (redirect-hop) judgement (T2); C3 = every resolved
address family and the real destination behind a configured carrier (T7, T8).

## 1. Test fairness

| test | asserts | covering instruction sentence | correct fix could fail? | risk |
|---|---|---|---|---|
| security::test_download_from_private_address_is_refused | no request reaches the loopback service; nothing it served is kept | property: a supplied destination, and every request it results in, addressed only to globally routable destinations; loopback is explicitly non-global | no | low |
| security::test_private_page_fetch_for_link_extraction_is_refused | the caller-supplied page is not fetched; its links are not returned | property: "An HTTP fetch that pyLoad performs for a destination a user supplied" (no route named) | no (only a download-only fix, which is incomplete by the property) | low |
| security::test_redirect_hop_to_private_address_is_refused | the redirect target is neither requested nor kept | property: "every request that fetch results in" | no | low |
| security::test_private_destination_through_proxy_is_refused | the non-public destination is not sent on and not contacted, carrier configured | property: destination-addressed rule, "whatever carries it there" | no (a correct fix judges the destination, not the carrier) | low |
| security::test_ipv6_only_private_destination_is_refused | an IPv6-only non-public destination is not sent on or contacted | property: "This holds for every address the destination resolves to" | no | low |
| functional::test_page_fetch_through_proxy_still_works | a public page through the operator's loopback proxy returns its links | Preservation ("Everything that works today keeps working") + "whatever carries it there" | no (the pre-fix wording could; repaired by the audit change) | low |
| functional::test_link_extraction_from_supplied_html_still_works | supplied HTML yields its links, no fetch | Preservation (no HTTP fetch, so the rule does not apply) | no | low |
| functional::test_redirect_between_public_destinations_still_works | a public→public redirect through the proxy yields links | Preservation + property (both destinations global) | no | low |
| functional::test_ipv6_only_public_destination_still_works | an IPv6-only public page yields links | Preservation + "every address the destination resolves to" | no | low |
| functional::test_local_container_file_still_processed | a local container file yields its links | Preservation (no HTTP fetch) | no | low |
| pristine::test_fib / test_folder_pattern / test_subfolder_pattern | the project's own passing tests | Preservation | no | low |

Gate a: no correct fix that follows the property fails any test.

## Stacking checks

| check | C1 (T1, T4) | C2 (T2) | C3 (T7, T8) |
|---|---|---|---|
| S1 coupled traps | Coupled values: public destination via a loopback carrier (page fetch) and caller-supplied HTML. Covered by "Everything that works today keeps working"/"Keep every legitimate use working", and, after the audit fix, no security rule read literally forbids the carrier ("whatever carries it there") or the no-fetch case. PASS | Coupled value: public→public redirect. Both requests are addressed to globally routable destinations, so the literal rule permits it; preservation names it. PASS | Coupled values: IPv6-only public destination (all resolved addresses global) and local container file (no fetch). Literal rule permits both; preservation covers them. PASS |
| S2 shape traps | Refused shapes: loopback/private literal destinations. Outside the legitimate set, which is "globally routable destinations" only; loopback is expressly non-global. PASS | Refused shape: a Location naming a loopback destination. Non-global; outside the legitimate set. PASS | Refused shapes: an IPv6-only private name (fd00::5) and a private destination with a configured carrier. Both non-global; the carrier's own locality is expressly not the addressed destination. PASS |
| S3 fixtures & harness | States: no carrier configured, downloads reset — legitimate. Harness drives api.add_package + the downloader plugin lifecycle and api.parse_urls (real entry points). PASS | State: operator-configured carrier — legitimate. Real entry point (link add + plugin lifecycle). PASS | States: carrier configured, IPv6 enabled — both legitimate product configuration. Real entry points. PASS |
| S4 concept independence | T1 (direct) and T4 (link extraction) pass under a C1-only guard: both destinations are literal loopback, no other concept involved. PASS | T2 test uses a public initial destination; a C2-only per-hop judgement refuses the hop without any C1/C3 work. PASS | T7 and T8 are one concept (judge the real destination for every address family); the reference implements both, and each test drives its own route. Masking (H3c) does not apply to H3a. PASS |
| S5 history | upstream_first_fix (fix A alone) violates the property read literally: it judges only the initial download URL, leaving redirect hops, the link-extraction fetch and IPv6-only destinations open; checks/upstream_first_fix.patch expects security_fail. PASS | Same patch leaves every redirect hop unjudged. PASS | Same patch resolves IPv4 only and judges no target behind a carrier. PASS |
| S6 contracts | No guessed field/function name; the protected object is "a destination a user supplied" in product terms. PASS | Covered by the same product-term destination, plus "every request that fetch results in". PASS | Fail-closed is stated: "A destination that is not globally routable is refused before any request is sent on its behalf". PASS |

S7 (decisive tests): build/stk-pyload-ghsa7gvf/trial_summary.md does not exist; the only recorded
trials are the v1 runs (both models scored 1.0) from before the v2 rewrite, so no post-upgrade
failed run exists to attribute. Nothing to re-check.

## 2. Leniency (QUALITY)

- refuse-all: caught by checks/ff-refuse-all.patch (three functional tests fail).
- Leave the link-extraction route open (unlisted route): caught by checks/miss_guard_coverage.patch (T4 fails).
- Judge only the initial URL, not redirect hops: caught by checks/miss_redirect_hop.patch (T2 fails).
- IPv4-only resolution / fail-open on an empty answer: caught by checks/miss_address_family.patch (T7 fails).
- Skip the judgement when a carrier is configured, or judge the carrier's peer: caught by checks/miss_proxy_target.patch (T7 and T8 fail).
- Crash as refusal: a crash on a refused destination is observably a refusal; a crash on a legitimate fetch fails the functional group.
- Wrong resource / one role or direction / read-only split / check-after-normalisation / adjacent API: not applicable (one fetch operation, one protected object, judged before the request).

## 3. Hints

None: the instruction contains no identifier, file, function, route name, variant list or count;
it states one property over the destination and one preservation contract.

### Required: generalize

none. The audit's single required change was a contradiction repair, not a route description;
no sentence points at a sibling, far site or uncovered route.

## 4. Realism

T1 and T2 are the published advisory routes at the pinned commit; T4, T7, T8 are real unmodified
upstream code paths (request_factory / core api, the IPv4-only resolver added at the pinned commit,
the peer selection with a configured proxy). No planted-looking trap.

## Quality to tighten

None beyond the audit fix: the checks already catch every plausible wrong fix.

## Verdict

GATE_A: READY — the audit's contradiction is repaired in general terms over the destination, and
every test is passed by a correct fix that follows the property.
NEEDS_HUMAN_REVIEW: NO
