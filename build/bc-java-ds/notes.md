# bc-java-ds — build notes

Start: 2026-10-24T04:55Z (work directory created 04:57Z)
End:   2026-10-24T09:30Z (build paused ~1h by the operator while the host Docker daemon was fixed)

Task: `tasks/bc-java-ds`, pattern A+B, injected track. Project `bcgit/bc-java` pinned at
`822b2478b131097368a56290f5728e28dd042989`; published fix `2c28b253a44681fbbc562561eab6ad383d2ae558`.

## Levers (one line each)

- **T1 (A, how-type, base)** — a host written with its RFC 1034 root label (`ceo@bank.com.`,
  `https://competitor.example./`) escapes an excluded rfc822Name/URI subtree; the fix must
  canonicalise on both sides of every form (mailbox, `@domain`, host, URI host). Published fix sites:
  `core/.../PKIXNameConstraintValidator.java:1088` and `:1846`.
- **T2 (A, how-type, far site)** — a permitted directoryName subtree is satisfied by RDNs that merely
  occur anywhere in the subject instead of forming its initial prefix. Published fix site
  `core/.../PKIXNameConstraintValidator.java:317`; absent from the advisory summary.
- **T3 (B, how-type, real unmodified upstream)** — the host of an rfc822Name is taken after the
  *first* `@`, so a quoted local part containing `@` makes the check compare a different host.
  `core/.../PKIXNameConstraintValidator.java:1098`; the published fix did not touch it and the latest
  upstream tree still splits at the first at sign (checked read-only on 2026-10-24).
- **T4 (injected)** — subject-DN `emailAddress` attributes are skipped when the certificate's
  alternative-name extension also carries an address. `prov/.../RFC3280CertPathUtilities.java:1177`.
- **T5 (injected)** — a CA's permitted subtrees are ignored when the same extension also publishes
  excluded subtrees. `prov/.../RFC3280CertPathUtilities.java:1614`.

## Verified behaviourally at the real entry point

Every check below was driven through `CertPathValidator.getInstance("PKIX","BC")` on the tree in
`~/.tb-graders/cwe/work/bc-java-ds` (repo = pinned; repo_inj = pinned + injection; repo_oracle_full =
oracle). 22 security cases fail on pinned+injected and pass on the oracle; 25 hidden functional cases
plus 3 project-test cases pass on both.

- T1 email: leaf-side dot (host form, `@domain` form, mailbox form), constraint-side dot, both
  directions — accepted before, refused after.
- T1 URI: leaf host dot (plain, with port, behind userinfo, with query), constraint-side dot —
  accepted before, refused after.
- T2: subject `C=FR, O=Attacker, O=Bench, CN=…` against permitted `O=Bench` — accepted before,
  refused after; a genuine prefix stays permitted.
- T3: `"a@bench.example"@bank.com` against an excluded `bank.com` / `@bank.com` — accepted before,
  refused after; an ordinary address and a quoted local part at a non-excluded host stay accepted.
- T4: subject `emailAddress=ceo@bank.com` plus SAN `ok@bench.example` — accepted on the injected tree,
  refused after the fix; both allowed stays accepted.
- T5: permitted `".bench.example"` plus excluded `"bank.com"` with a name outside the permitted set —
  accepted on the injected tree, refused after the fix; inside-permitted stays accepted.
- Project tests (`PKIXNameConstraintsTest`, `MultiValuedRDNEmailTest`) pass on pinned+injected and on
  the oracle.
- All 12 check patches were replayed locally against the injected tree (compiled over the injected
  class tree) and behave as declared: 7 security_fail (each leaves only its own lever failing), 2
  functional_fail by over-hardening/refusal, 2 pass (hardening, alternative design) at reward 1.0.

## Injected-sibling candidates considered

Every site/route found while reading the code, before picking:

1. `prov/.../RFC3280CertPathUtilities.processCertBC` — subject-DN email addresses skipped when the SAN
   carries email names (**picked, T4**).
2. `prov/.../RFC3280CertPathUtilities.prepareNextCertG` — permitted subtrees ignored when the same
   extension has exclusions (**picked, T5**).
3. Same loop — only the first subject email checked (array-vs-element shape). Rejected: it is the same
   code block as T4 and would be found with it; no separate reason to dismiss.
4. `prepareNextCertG` — name constraints processed only when the extension is critical. Rejected: the
   RFC already requires criticality, so a solver could fairly call a non-critical extension out of
   scope; also close to T5.
5. `processCertBC` — self-issued early return loses its "unless final certificate" clause. Rejected: the
   code comment states the rule, so the injected change would read as contradicting its own comment.
6. `extractEmailAddressesFromSubjectDN` — regression to `RDN.getFirst()` (multi-valued RDN). Rejected:
   the project's own `MultiValuedRDNEmailTest` covers it and would fail on the injected tree.
7. Core `isEmailConstrained` — split at first `@` (chosen as real lever T3, not injected).
8. Core `checkPermittedEmail` — empty permitted set read as "no restriction". Rejected: plausible but
   the empty set is only reachable through a chain of two CAs with disjoint permitted subtrees; the
   route is much more artificial than T4/T5.
9. Core `isURIConstrained` — full-URL constraint support branch. Rejected: a new spelling of the stated
   input, which the design excludes as a lever.
10. `prov/.../jce/provider/PKIXNameConstraintValidator` / `pkix/.../PKIXNameConstraintValidator` — a
    second implementation in a wrapper. Rejected: both are pure delegators today, so any gap would have
    to be invented rather than "left".
11. `jdk1.4` and `jdk1.1` source trees — copies of the validator/SPI without the fix. Rejected: not built
    by the Gradle build (ant-only), unreachable through the real entry point.
12. `PKIXCertPathReviewer` (both copies) — the name-constraint loop stops before the target certificate,
    so the reviewer never checks the leaf. Rejected for fairness: it is a reporting/diagnostic API with
    its own TODO documenting a different gap, and requiring it would need the instruction to point at a
    second API surface; the general property would be doing too much work.
13. `prov/.../jdk1.1/PKIXCertPathValidatorSpi` ancient `endsWith` email check. Rejected: not built.

Why the picks won: T4 and T5 are both in the path-processing layer, which the published fix never
touches, and both are reached from the same public entry point as the reported bug. Each is
how-type in effect (the fix needs the mechanism understood — every name the certificate carries is
constrained; permitted and excluded subtrees both apply), and each has a different reason to be
skipped: T4 reads as an identity-precedence rule, T5 reads as an exclusion-wins precedence rule.

## What I could not verify

- The advisory text itself; the summary was taken from the screener record and the published diff.
- Whether the jdk1.4/jdk1.1 source variants are shipped in any artefact (not used either way).
- The model bar: no trials were run by me (the pipeline runs them).
- The gate result. Stages were run one at a time as the brief requires: `--only static` PASSED,
  `--only nop` PASSED (22 security cases fail on the pinned+injected tree, 28 functional pass),
  `--only oracle` PASSED (3 runs, reward 1.0 each, identical), `--only patches` PASSED (all 12 present
  checks behave as declared; `blind.patch` is produced downstream). Each stage's record is in
  `build/bc-java-ds/gate_report.partial.json` (the stage runner rewrites that file per stage).

## Host note

The shared VM's system Docker daemon wedged under load during the first `nop` attempt ("Docker daemon is
not running", `/info` hanging while `/_ping` answered). After the operator restarted it, the remaining
stages ran on the system daemon. During the restart window the `patches` stage aborted twice on the known
Harbor egress-probe flake (`network_mode='allowlist' is not supported`, the 30 s probe taking 8-35 s under
load average 30-48); a retry loop that waits for a sub-12 s probe and re-runs the stage on an infra
verdict produced a clean pass. No task file was changed for either host problem.

## Scope note

Out of scope, not built on: legacy `jdk1.4`/`jdk1.1` source trees and the two `PKIXCertPathReviewer`
copies discussed above.
