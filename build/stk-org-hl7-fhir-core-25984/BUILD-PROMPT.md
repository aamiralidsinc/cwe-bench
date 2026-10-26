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

Project root: `/home/mara/cwe-bench`. Task: `stk-org-hl7-fhir-core-25984`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 25984; unbounded decompression loop / resource exhaustion (CWE-835, CWE-400, 
- Pinned (vulnerable) commit: c9d668680b01a76bbb45dc2be34b4d41f6de3acb. Published fix: d804558bd77372b1629e55a5b901cad3f5134cdc, edd5d8c139e669e39270785f08be7b63aefef24c.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-25984",
 "pattern": "H4",
 "repo": "hapifhir/org.hl7.fhir.core",
 "pinned_commit": "c9d668680b01a76bbb45dc2be34b4d41f6de3acb",
 "protections": [
  "P1 - terminating DEFLATE decompression of the attacker-supplied JWT payload segment: the Inflater drain loop must stop or fail when Inflater.inflate() makes no progress (returns 0 with needsInput()/needsDictionary() set while finished() stays false) instead of spinning forever (org.hl7.fhir.r5/.../SHCParser.java:462-466; org.hl7.fhir.r4b/.../SHCParser.java:324-327).",
  "P2 - bounded decompressed output: a small compressed segment must not expand without limit. No such bound exists at the pinned commit; the only length test is MAX_ALLOWED_SHC_LENGTH at r5 SHCParser.java:282-284, which is log-only, QR-image-oriented and measured on the encoded string before decompression."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:462",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:464",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:465"
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
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:455",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:459",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:300",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:301",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:291"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "advisory_route",
   "locations": [
    "org.hl7.fhir.validation/src/main/java/org/hl7/fhir/validation/ResourceChecker.java:118"
   ],
   "reason_to_dismiss": "It is a format-guessing probe in the validator's content sniffer, not the SHC parser the report names: decodeJWT is called directly on arbitrary undetected file bytes, outside Manager.parse, with errors=null.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "org.hl7.fhir.validation/src/main/java/org/hl7/fhir/validation/ResourceChecker.java:110",
    "org.hl7.fhir.validation/src/main/java/org/hl7/fhir/validation/ResourceChecker.java:116",
    "org.hl7.fhir.validation/src/main/java/org/hl7/fhir/validation/ResourceChecker.java:120",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/ParserBase.java:152",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/ParserBase.java:153",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:278"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:417",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:418",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:419"
   ],
   "reason_to_dismiss": "Private helper on the JWS signature path: it only runs after a JWKS document has been fetched for the iss URL, and it inflates the same decoded payload bytes the public inflate() already handled, so it reads as unreachable-once-T1-is-fixed duplicate code.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:410",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:374",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:329",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:323",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:405",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:373"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:324",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:325",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:326"
   ],
   "reason_to_dismiss": "The R4B class is the deprecated legacy copy of the same parser, and nothing in this repo routes SHC content into it: the validator, the SHL flow and ResourceChecker only build the r5 parser, and r4b returns List<NamedElement> rather than the List<ValidatedFragment> the shipping validator consumes.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:53",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:65",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:100",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:297",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:298",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:318",
    "org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/Manager.java:115",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/Manager.java:141",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:73"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:282",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:283"
   ],
   "reason_to_dismiss": "The 1195-byte cap is a QR-image limit and only logs an ERROR, so tightening it reads as an unrelated behaviour change; the file-download and SHL forms legitimately carry longer verifiableCredential strings through this same parser.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:261",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:301",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:304",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:108",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:111",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:83",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHLParser.java:260",
    "org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHLParser.java:262"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T5"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T3 is behaviourally masked by T1 at the pinned commit: decodeJWT decodes parts[1] once (:291), inflates it at :301, and verifySignature re-parses the same token (:366) and re-decodes the identical payload bytes (:373-374), so no input can make the :417 loop hang without the :462 loop hanging first. It becomes observable only if T1 is repaired with a partial-return/output-cap guard that lets the same stream through to decompress().",
   "The log-only MAX_ALLOWED_SHC_LENGTH test (:282-284) reads as an existing DoS defence and masks the total absence of any bound on the inflated output (:459-466 grows a ByteArrayOutputStream with no limit).",
   "T4 is masked in-repo by the absence of any SHC caller for the r4b Manager (r4b Manager.java:115 is reachable only through the public r4b API, and its parser returns List<NamedElement> while ValidationEngine/SHLParser consume List<ValidatedFragment>)."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "The natural hard guard for T1 - throwing FHIRException/DataFormatException on a zero-byte or needs-dictionary stream, or finally enforcing MAX_ALLOWED_SHC_LENGTH as a reject - breaks the must-keep-working path where a DEFLATE payload producing no output degrades into the structured 'Unable to decode JWT token' error (:301-304 then :108-113), and rejects legitimate file-download/SHL cards whose verifiableCredential strings exceed 1195 bytes (SHLParser.java:260-263 -> SHCParser.java:83-99)."
  },
  {
   "a": "T1",
   "b": "T3",
   "what": "A T1 fix that caps the output inside inflate() and returns the partial bytes instead of failing the parse lets the same compressed stream continue to the unguarded decompress() at :374, which then expands it without bound."
  }
 ],
 "fairness_risks": [
  "A DEFLATE payload that decompresses to nothing must keep degrading gracefully: inflate() has to hand back a non-throwing empty result so the caller's catch turns it into one 'Unable to decode JWT token' ERROR (:301-304, :108-113). A security rule that refuses empty or truncated DEFLATE input contradicts that contract.",
  "The 1195-byte MAX_ALLOWED_SHC_LENGTH (:261, :282-284) is advisory, measured on the encoded token and oriented to QR images; any rule that enforces it, or that caps the decompressed size, contradicts the legitimate long-token file-download and SHL routes (SHLParser.java:260-263) and the JSON verifiableCredential form (:83-99).",
  "ResourceChecker:118 passes errors=null, and ParserBase.logError does nothing at all when errors is null (ParserBase.java:152-153), so a protection expressed as a reported ERROR rather than a control-flow stop is inert on that route.",
  "Refusing a token whose payload segment base64-decodes to zero bytes would make decodeJWT throw where ResourceChecker:120-121 currently expects a clean fall-through for non-SHC files."
 ],
 "effort_minutes": 45,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T3",
   "T4",
   "T5"
  ],
  "why": "Three independent groups from five recorded traps. Group (T1,T2,T5) is the reported r5 inflate() drain loop plus its shadow routes: the validator's format-guessing decodeJWT probe (ResourceChecker:118, where errors=null makes any log-only guard inert) and the coupled must-keep-working empty/truncated payload and long file-download cards. Group (T3) is the duplicated drain loop in decompress() 45 lines above, on the signature path. Group (T4) is the byte-identical r4b copy that the published fix never touched. T3 and T4 are deepseek-type (protection absent, each with its own distinct reason to dismiss: 'needs a JWKS fetch and re-inflates the same bytes' versus 'deprecated legacy module with no in-repo routing'); T5 is the mimo-type coupled value that catches an over-hardened fix. The anchor T1 is surface-described by any report, so discriminating power sits in T3 and T4, and the value of T5 is that it forbids the two tempting over-broad repairs (hard reject, size cap). This beats a one-site design because the only repair that leaves a security-relevant hole is confining the guard to the reported public method, and it beats adding a synthetic size-cap trap because the pinned code already couples that limit to legitimate long cards, so no ground-truth fix should close it. Caveat recorded for the builder: T3 is masked behaviourally by T1 on the same bytes, so it discriminates only if the hidden test exercises both drain loops."
 },
 "unverified": [
  "The two published fix commits (d804558bd77372b1629e55a5b901cad3f5134cdc and edd5d8c139e669e39270785f08be7b63aefef24c) are not reachable from the pinned tree and no shell was available in this session, so which drain loops the upstream fix actually patched, and whether a SHCParserTests regression exists after the fix, is taken from the screener record rather than verified here.",
  "Whether T3 is ever triggered independently: at the pinned commit decodeJWT:291 and verifySignature:373 decode the same payload segment, so no input reaches :417 without first traversing :462; its status as a separately testable trap cannot be confirmed without the fix diff.",
  "No in-repo test or test resource exercises SHC parsing at the pinned commit (no SHCParserTests.java under org.hl7.fhir.r5/src/test), so testability is inferred from the API surface only (inflate(byte[]) is public static in both modules; decompress(byte[]) is private).",
  "Whether any external consumer calls org.hl7.fhir.r4b.elementmodel.Manager.parse with FhirFormat.SHC - no in-repo caller was found.",
  "Build health and repository size were not measured (no shell), so offline-after-build and repo-size priors are untested.",
  "Left out deliberately as outside this advisory's protection: decodeQRCode's substring(i, i+2) over an odd-length shc:/ string throws StringIndexOutOfBounds (org.hl7.fhir.r5/.../SHCParser.java:269-271, org.hl7.fhir.r4b/.../SHCParser.java:266-268) - a robustness bug with no relation to the decompression guard."
 ]
}
  ```
- Published fix sites:   - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:462 — T1 M4 (reason to dismiss: none)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:464 — T1 M4 (reason to dismiss: none)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:465 — T1 M4 (reason to dismiss: none)
  - org.hl7.fhir.validation/src/main/java/org/hl7/fhir/validation/ResourceChecker.java:118 — T2 M1 (reason to dismiss: It is a format-guessing probe in the validator's content sniffer, not the SHC parser the report names: decodeJWT is called directly on arbitrary undetected file bytes, outside Manager.parse, with errors=null.)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:417 — T3 M2 (reason to dismiss: Private helper on the JWS signature path: it only runs after a JWKS document has been fetched for the iss URL, and it inflates the same decoded payload bytes the public inflate() already handled, so it reads as unreachable-once-T1-is-fixed duplicate code.)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:418 — T3 M2 (reason to dismiss: Private helper on the JWS signature path: it only runs after a JWKS document has been fetched for the iss URL, and it inflates the same decoded payload bytes the public inflate() already handled, so it reads as unreachable-once-T1-is-fixed duplicate code.)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:419 — T3 M2 (reason to dismiss: Private helper on the JWS signature path: it only runs after a JWKS document has been fetched for the iss URL, and it inflates the same decoded payload bytes the public inflate() already handled, so it reads as unreachable-once-T1-is-fixed duplicate code.)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:282 — T5 M11 (reason to dismiss: The 1195-byte cap is a QR-image limit and only logs an ERROR, so tightening it reads as an unrelated behaviour change; the file-download and SHL forms legitimately carry longer verifiableCredential strings through this same parser.)
  - org.hl7.fhir.r5/src/main/java/org/hl7/fhir/r5/elementmodel/SHCParser.java:283 — T5 M11 (reason to dismiss: The 1195-byte cap is a QR-image limit and only logs an ERROR, so tightening it reads as an unrelated behaviour change; the file-download and SHL forms legitimately carry longer verifiableCredential strings through this same parser.)
- Uncovered routes to confirm (pattern B):   - org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:324 — T4 M2 (reason to dismiss: The R4B class is the deprecated legacy copy of the same parser, and nothing in this repo routes SHC content into it: the validator, the SHL flow and ResourceChecker only build the r5 parser, and r4b returns List<NamedElement> rather than the List<ValidatedFragment> the shipping validator consumes.)
  - org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:325 — T4 M2 (reason to dismiss: The R4B class is the deprecated legacy copy of the same parser, and nothing in this repo routes SHC content into it: the validator, the SHL flow and ResourceChecker only build the r5 parser, and r4b returns List<NamedElement> rather than the List<ValidatedFragment> the shipping validator consumes.)
  - org.hl7.fhir.r4b/src/main/java/org/hl7/fhir/r4b/elementmodel/SHCParser.java:326 — T4 M2 (reason to dismiss: The R4B class is the deprecated legacy copy of the same parser, and nothing in this repo routes SHC content into it: the validator, the SHL flow and ResourceChecker only build the r5 parser, and r4b returns List<NamedElement> rather than the List<ValidatedFragment> the shipping validator consumes.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T3, T4, T5. Why: Three independent groups from five recorded traps. Group (T1,T2,T5) is the reported r5 inflate() drain loop plus its shadow routes: the validator's format-guessing decodeJWT probe (ResourceChecker:118, where errors=null makes any log-only guard inert) and the coupled must-keep-working empty/truncated payload and long file-download cards. Group (T3) is the duplicated drain loop in decompress() 45 lines above, on the signature path. Group (T4) is the byte-identical r4b copy that the published fix never touched. T3 and T4 are deepseek-type (protection absent, each with its own distinct reason to dismiss: 'needs a JWKS fetch and re-inflates the same bytes' versus 'deprecated legacy module with no in-repo routing'); T5 is the mimo-type coupled value that catches an over-hardened fix. The anchor T1 is surface-described by any report, so discriminating power sits in T3 and T4, and the value of T5 is that it forbids the two tempting over-broad repairs (hard reject, size cap). This beats a one-site design because the only repair that leaves a security-relevant hole is confining the guard to the reported public method, and it beats adding a synthetic size-cap trap because the pinned code already couples that limit to legitimate long cards, so no ground-truth fix should close it. Caveat recorded for the builder: T3 is masked behaviourally by T1 on the same bytes, so it discriminates only if the hidden test exercises both drain loops. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): A DEFLATE payload that decompresses to nothing must keep degrading gracefully: inflate() has to hand back a non-throwing empty result so the caller's catch turns it into one 'Unable to decode JWT token' ERROR (:301-304, :108-113). A security rule that refuses empty or truncated DEFLATE input contradicts that contract. | The 1195-byte MAX_ALLOWED_SHC_LENGTH (:261, :282-284) is advisory, measured on the encoded token and oriented to QR images; any rule that enforces it, or that caps the decompressed size, contradicts the legitimate long-token file-download and SHL routes (SHLParser.java:260-263) and the JSON verifiableCredential form (:83-99). | ResourceChecker:118 passes errors=null, and ParserBase.logError does nothing at all when errors is null (ParserBase.java:152-153), so a protection expressed as a reported ERROR rather than a control-flow stop is inert on that route. | Refusing a token whose payload segment base64-decodes to zero bytes would make decodeJWT throw where ResourceChecker:120-121 currently expects a clean fall-through for non-SHC files.. Conflicts the reader found: The natural hard guard for T1 - throwing FHIRException/DataFormatException on a zero-byte or needs-dictionary stream, or finally enforcing MAX_ALLOWED_SHC_LENGTH as a reject - breaks the must-keep-working path where a DEFLATE payload producing no output degrades into the structured 'Unable to decode JWT token' error (:301-304 then :108-113), and rejects legitimate file-download/SHL cards whose verifiableCredential strings exceed 1195 bytes (SHLParser.java:260-263 -> SHCParser.java:83-99). | A T1 fix that caps the output inside inflate() and returns the partial bytes instead of failing the parse lets the same compressed stream continue to the unguarded decompress() at :374, which then expands it without bound.

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

## Environment (`tasks/stk-org-hl7-fhir-core-25984/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-org-hl7-fhir-core-25984/instruction.md`)
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

## Tests (`tasks/stk-org-hl7-fhir-core-25984/tests/`)
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
- **Wrong-fix patches** go in `build/stk-org-hl7-fhir-core-25984/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-org-hl7-fhir-core-25984/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-org-hl7-fhir-core-25984/manifest.json`:**
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

**Also in `build/stk-org-hl7-fhir-core-25984/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-org-hl7-fhir-core-25984 --only static
python3 -I common/gate/gate.py stk-org-hl7-fhir-core-25984 --only nop
python3 -I common/gate/gate.py stk-org-hl7-fhir-core-25984 --only oracle
python3 -I common/gate/gate.py stk-org-hl7-fhir-core-25984 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-org-hl7-fhir-core-25984/`;
  - edit only `tasks/stk-org-hl7-fhir-core-25984/`, `build/stk-org-hl7-fhir-core-25984/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-25984.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-org-hl7-fhir-core-25984`. Control task slug: `stk-org-hl7-fhir-core-25984-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-25984.json`.
