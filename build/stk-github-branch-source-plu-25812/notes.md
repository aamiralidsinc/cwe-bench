# stk-github-branch-source-plu-25812 — build notes

- Start (this build session): 2026-10-26T02:26Z (build/start_utc.txt)
- End: pending gate (filled in below)
- Advisory path: SECURITY-3808, jenkinsci/github-branch-source-plugin. Pinned (vulnerable)
  205fd594c821faaff1a66fedfa7e10973291d70c = direct parent of the published fix
  d869797365462234fe061c74fe6bf0bcae8777ea (verified `git rev-parse d869797^`).
- Track: stacked (H4). Pattern: A+B. Language: Java 17, Maven, Jenkins plugin parent 6.2122,
  Jenkins 2.539, JUnit 4 + JenkinsRule. Fully offline after the image build (/opt/m2, ~400 MB).

## Mechanism (one line)
Descriptor form fills (`/descriptorByName/<descriptor>/fillApiUriItems`) return the global list of
registered GitHub Enterprise endpoints (name + API URL) without checking who is asking.

## Levers (one line each)
- T1 (reported, both): the organization-folder descriptor fill has no check.
  GitHubSCMNavigator.java:1870-1882. Dismiss: the jelly hides the picker behind
  isApiUriSelectable, so the fill looks reachable only from an item configure page.
- T3 (published-fix far site, both): the credential descriptor fill is a one-line delegate to the
  same shared builder through a static import. GitHubAppCredentials.java:820-822. Dismiss: a guard
  in the shared builder looks like it covers the delegate; folder-scoped credential stores are
  managed by Item.CONFIGURE holders who need the list.
- T8 (coupled value, mimo): the list is offered inside items as a GET form fill; an unconditional
  Jenkins.MANAGE check or @RequirePOST (both idioms already present in the package) closes the
  disclosure but blanks the picker for item configurators and stops the fill loading.
  GitHubSCMNavigator.java:1855-1858; GitHubAppCredentials.java:839-848;
  GitHubSCMSource.java:2087-2090. Covered only by the general keep-working sentence plus the
  property's item-scoped branch; tested by the functional suite.
- T2 (published-fix far site, deepseek): the branch-source descriptor carries its own copy of the
  endpoint loop instead of calling the shared builder. GitHubSCMSource.java:2242-2250. Dismiss:
  the picker only renders from a job/folder configure page, so "whoever reaches it can configure
  it", and fixing the shared helper looks like it covers this copy.
- T5 (injected sibling, deepseek): a checkout-trait descriptor endpoint fill added beside the
  trait's credentials fill, which already shows the exact context-dependent rule; the omission
  reads as deliberate. SSHCheckoutTrait.java:176-190. Dismiss: a different file and a different
  form; the reported descriptors look like the whole set.
- T6 (injected sibling, deepseek): an endpoint fill on the global configuration descriptor, whose
  page requires Jenkins.MANAGE, but the descriptor-named fill URL stays individually addressable.
  GitHubConfiguration.java:247-261. Dismiss: the page-level permission looks like it covers the
  fill.

Concepts (one independent edit site each): G1 = T1+T3+T8 (the shared builder carries a nullable
item context and its two callers pass it), G2 = T2 (the duplicated loop), G3 = T5, G4 = T6.

## Verified
- Injected tree and oracle compile with the pinned pom (Maven, offline after warm-up).
- The project's own affected-area test `GitHubSCMNavigatorTest#doFillScanCredentials` passes at
  the pinned commit offline (run in both the environment and verifier image builds).
- nop (pinned+injected): 9/9 security FAIL through real HTTP routes, 8/8 functional PASS.
- oracle: 17/17 PASS (9 security, 8 functional), twice, identical.
- Each `checks/*.patch` was pre-run locally against the hidden suite (results in
  build/stk-.../notes.md's sibling validation logs; summarised in the gate report).
- The upstream published fix applied alone (`upstream_fix.patch`) leaves T5 and T6 failing, so the
  stack adds beyond upstream (recall check expects security_fail).
- Control task built with the same pinned code and byte-identical report; only the advisory route
  is scored there.

## Could not verify / caveats
- The exact advisory text (GHSA/CVE) was not available offline; SECURITY-3808 comes from the
  published fix commit message.
- `GitHubConfiguration.getEndpoints()` is public; whether Stapler exposes it directly to
  Overall/Read callers was not verified and it is not scored.
- `isApiUriSelectable()` is not exposed as a descriptor property URL (404 probed at the pinned
  commit); visibility is checked through the descriptor API under an impersonated ACL, which is
  how its jelly caller reads it.
- The item branch of the credential descriptor is exercised over HTTP under an item ancestor; the
  upstream fix's own regression test calls the method directly, and both agree.

## Outside scope (one line)
ApiRateLimitChecker writes the first endpoint URL to the server log at INFO; no attacker input
reaches it and the log's audience was not verified, so it is not part of this task.

## Record provenance
- The path named in `manifest.stacking.reader_record` (`pipelines/stacking/out/reader/h4-25812.json`)
  is absent in this checkout. The same reader record was read from
  `pipelines/stacking/out/reader-ds/h4-25812.json`; the screener record is
  `pipelines/stacking/out/screener-ds/25812.json`. The manifest keeps the path the build prompt
  specifies.

## Pre-gate local validation (all runs offline, hidden suites, `mvn -o test`)
| variant | result |
| --- | --- |
| pinned+injected (nop) | 9 security FAIL, 8 functional PASS |
| reference (`solution/fix.patch`) | 17/17 PASS |
| miss_G1 (navigator + credential fills unguarded) | 4 security FAIL (T1/T3), functional PASS |
| miss_G2 (branch-source copy unguarded) | 2 security FAIL (T2), functional PASS |
| miss_G3 (checkout-trait fill unguarded) | 2 security FAIL (T5), functional PASS |
| miss_G4 (global-configuration fill unguarded) | 1 security FAIL (T6), functional PASS |
| upstream published fix only | 3 security FAIL (T5/T6), functional PASS |
| ff-refuse-all | 6 functional FAIL, security PASS |
| ff-manage-only | 2 functional FAIL (item configurators), security PASS |
| crash-as-refusal | 9 security FAIL (server error, not a client refusal), functional PASS |
| pass-hardening | 17/17 PASS |
| pass-alt (per-call-site CONFIGURE rule) | 17/17 PASS |
| project tests on injected tree | GitHubAppCredentialsDescriptorTest 3/3, SSHCheckoutTraitTest 6/6 PASS |

Control (`...-control`): pinned 4/4 security FAIL + 8/8 functional PASS; control reference 12/12
PASS; its hardening and alternative pass patches 12/12 PASS each.
