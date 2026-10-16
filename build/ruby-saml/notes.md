# ruby-saml stacking task — build notes

## Commit C
`148a4c2de713a98c58c28bbc7785c05698216a4d` = tag **v1.16.0**. Chosen because
all three included CVEs are simultaneously OPEN there (each introduced at/before
v1.16.0, each fixed only after it), and because v1.16.0 builds with a modern Ruby
image using a *precompiled* nokogiri gem — no native compilation, so the image is
lean (~200 MB) and the build does not thrash memory.

## Co-present vulns (verified present at C by reproduction)
1. **CVE-2024-45409** (CWE-347/287, favoured): signature verification accepts a
   document in which the signed identifier appears on more than one element
   (classic signature-wrapping acceptance). Fixed after C in 1.17.0/1.12.3
   (xml_security.rb). Proof: two wrapping payloads make
   `SignedDocument#validate_document` return `true` on v1.16.0.
2. **CVE-2025-25293** (CWE-400/770): decompression bomb — a tiny deflated message
   inflates to a huge one and is fully processed (no post-inflation size check).
   Fixed after C in 1.18.0/1.12.4 (saml_message.rb). Proof: ~0.8 KB blob inflates
   to ~600 KB and the message objects construct without error on v1.16.0.
3. **CVE-2025-54572** (CWE-400): oversized message not refused up front — the
   size guard runs only after the base64 short-circuit, so an oversized non-base64
   message is processed. Fixed after C in 1.18.1 (saml_message.rb). Proof: a
   360 KB non-base64 message is not rejected by the guard on v1.16.0.

## Dropped
- **CVE-2025-25291 / CVE-2025-25292** (parser-differential signature wrapping,
  favoured). Dropped: the working PoC bytes were deliberately withheld upstream
  and could not be reliably reconstructed offline, and the upstream fix is a large
  multi-file refactor (`cache_referenced_xml`/`doc_to_validate`) that does not
  port cleanly onto v1.16.0 for a stable oracle.

## Oracle / checks (all verified locally against both v1.16.0 and patched source)
- `solution/fix.patch`: real upstream source changes for all three, applied
  together → security 5/5 pass, functional 6/6 pass.
- `checks/subset_fix.patch` → security_fail (fixes 45409+25293, leaves 54572:
  1 security fail, functional all pass).
- `checks/disable_feature.patch` → functional_fail (refuses every signature:
  3 functional fail).
- `checks/alt_correct_fix.patch` → pass (different formulation, 1.0).

## Offline
The verifier needs no network: fixtures (signed responses + IdP cert) live under
`tests/fixtures`, copied from the repo, and all exploit payloads are generated
in-process. Tests never read from `/app`. (Corrected 2026-10-16: this section used to
say "No network at run time", which was true of the tests but not of every agent run.
The 2026-10-15 seq1 trials gave the agent open internet; the deepseek seq1 agent
fetched upstream releases and the fix commit with curl. The r11 trials ran offline
(`bundle install` failed). task.toml now sets `network_mode = "allowlist"` with only
the model API hosts.)

## Caveat
`source` in task.toml is `mined` (not `mined+stacking`) because the current
`gate.py` static check only accepts `mined|mined+injected|injected`; the stacking
nature is recorded in `manifest.build_kind` and in task.toml `tags`.

## 2026-10-16 test repair
Brief: `build/audit/REPAIR-BRIEF-2026-10-16.md`. Only `tests/security/group.rb` changed;
instruction.md, solution/ and functional tests are unchanged.

### Items
| item | source | decision |
|---|---|---|
| Size rejection required `ValidationError` with a message matching `/exceed/i`, which the instruction never states | deepseek-seq1 + mimo-r11 audits, our notes | **fixed (relaxed).** A rejection is now any raised error (NoMemoryError, signals and exit excluded). The oversized payload is now well-formed, non-base64 XML, so the unfixed library raises nothing for it and "any error" still bites. The old payload contained `<>`, so unfixed code raised a REXML parse error, which is why the class/wording pin had been needed. |
| "Oversized messages must be refused up front, before that expensive work" was not enforced: a fix that runs the size check after the base64 scan passed | mimo-seq1 audit (lenient-test), our notes | **fixed.** The oversized test now (a) arms a test-only spy on the XML parsers (REXML `BaseParser#stream=`, `Nokogiri::XML::Document.parse`) and fails if the payload is parsed; (b) sends ~8.4 MB, far beyond any reasonable limit, and requires the rejection to take < 0.2x one whitespace-stripping `gsub` pass over the same input, timed in the test itself (best of 2 calls vs best of 3 passes, so it does not depend on machine speed). Measured: reference 0.0005 s vs pass ~1.0 s; scan-then-reject ~2.0 s. |
| Bombs rejected only after the expanded document was parsed would have passed | follows from "rejected rather than ... processed" | **fixed.** Both bomb tests arm the parse spy (threshold = the 600 kB inflated size) and fail if the expanded document reaches a parser. |
| Bomb tests cannot tell streaming abort from expand-then-reject; instruction says "rather than fully expanded" | deepseek-seq1 audit | **skip.** The reference fix expands fully and then rejects, so a streaming-only test would fail the oracle. Parsing is now enforced, and the instruction wording is left unchanged. |
| Stray `ds:DigestValue` before the real one in a unique-ID document (XPath scoping, part of the upstream fix) | deepseek-r11 REC | **skip.** The instruction reports only the duplicate-identifier form. Testing this needs a new vulnerability description in the instruction. That changes the task's scope rather than repairing a test, and would make earlier runs incomparable. Option for a future task version. |
| notes.md "No network at run time" wrong | deepseek-seq1 audit | **fixed** in the Offline section above: the tests need no network, but seq1 agents had open internet. |
| final-code/changes.patch missing from postmortem bundles | both seq1 audits | out of scope (harness); seq1 trials have no saved final code. |

### New patch checks (manifest `patch_checks`)
- `scan_then_reject.patch` (security_fail): the reference fix, except that the base64 scan runs before the size guard. Old tests: 1.0. New: oversized test fails on time (reward 0.8).
- `parse_then_reject.patch` (security_fail): the reference signature fix, with size limits checked in the Response/SloLogoutrequest constructors after parsing. Old tests: both bomb tests passed. New: both bomb tests and the oversized test fail via the parse spy (reward 0.4).
- `other_error_fix.patch` (pass): the reference fix with both size rejections raising `ArgumentError, "SAML message too large ..."`. Old tests: 3 security fails. New: 1.0 (proves the relaxation).

### Gate
`python3 build/slot.py 3 -- python3 -I builder/gate.py ruby-saml`: **PASSED** (nop 5/5 security fail;
oracle x2; subset 0.8, disable 0.0, alt 1.0, scan_then_reject 0.8, parse_then_reject 0.4,
other_error 1.0). Warnings: no `hardening`/`blind` pass patches exist for this task.

### Regrade (saved final code, fresh container)
| trial | old | new | failing tests |
|---|---|---|---|
| ruby-saml-deepseek-r11-20261015-202444-n001/ruby-saml__QpqHKHG | 1.0 | 1.0 (regrade-20261016T052620Z) | none |
| ruby-saml-mimo-r11-20261015-204334-n001/ruby-saml__SyFoddE | 1.0 | 1.0 (regrade-20261016T052634Z) | none |
| ruby-saml-deepseek-seq1-1791990964/ruby-saml__jZ9jGb7 | 1.0 | not regradable (no final-code/) | - |
| ruby-saml-mimo-seq1-1792005093/ruby-saml__WGgGoMj | 1.0 | not regradable (no final-code/) | - |
| ruby-saml-mimo-seq1-1792007992/ruby-saml__NCDHeXX | none (exception) | not regradable (no final-code/) | - |

Both seq1 fixes, as described in their audits (streaming inflate raising ValidationError; size guard
moved above the base64 scan), would pass the repaired tests, but this was not run.


## 2026-10-16 test repair 2: digest material outside the signed info
User-approved 2026-10-16. This supersedes the "skip" of the stray-`ds:DigestValue` item in the
first repair above and the "2026-10-16 audit finding (not applied)" decision. Source: the post-run
audit of ruby-saml-inv DeepSeek r11
(`~/.tb-graders/cwe/jobs/ruby-saml-inv-deepseek-r11-20261016-072258-n001/ruby-saml-inv__Dq58EG8/postmortem-20261016T121401Z/verdict.json`, lenient-test).
The tests of ruby-saml and ruby-saml-inv are still byte-identical (`diff -r` clean), and so are
their `checks/`. instruction.md and solution/ are unchanged in both tasks.

### Item
| item | decision |
|---|---|
| No test covers the case where the signed ID is unique and the digest material is taken from a stray `ds:Reference`/`ds:DigestValue` outside SignedInfo (document-wide `//ds:` lookups) | **fixed.** New security test `wrapping: a digest from an element outside the signed info does not make altered content verify`. It changes the NameID of the genuinely signed assertion to `attacker@evil.example`, so the ID stays unique. It computes that assertion's digest with Nokogiri + OpenSSL (enveloped signature removed, exclusive C14N, SHA-1; no library code; the same method reproduces the fixture's genuine DigestValue exactly). It plants a `ds:Reference` carrying that digest inside `samlp:Status`, which comes before the signed assertion in document order. It then asserts that `Response.new(b64).document.validate_document(fp, true)` is not true, the same entry point the other two wrapping tests use. Fairness: original instruction "only genuinely signed material may be accepted"; -inv "that element is exactly what the IdP signed" and "close variants". Measured: v1.16.0 accepts the payload (true); the reference fix rejects it. |

### Patch checks
- **new `dupid_only_fix.patch` (security_fail)**: the reference size fixes, plus a signature fix that only rejects documents whose signed ID matches more than one element. All `//ds:` lookups stay document-wide, which is the approach the flagged run took. It passes both duplicate-ID tests and all resource and functional tests, and fails only the new test (0.8333).
- **`alt_correct_fix.patch` rewritten (still `pass`)**: the old version had the same duplicate-ID-only defect and failed the new test (0.8333). It had been "correct" only against the lenient tests. The new version keeps its uniqueness check and size fixes. It also anchors `ref` to `./ds:SignedInfo/ds:Reference` and reads CanonicalizationMethod, DigestMethod, DigestValue and Transforms relative to `ref`, which is a different formulation from the reference fix's separate `signed_info_element`. Score: 1.0. Lesson: scoping only the sub-lookups is not enough, because the document-wide `//ds:Reference` itself selects the planted Reference.
- All other checks are unchanged. Re-checked against the new test, their results are the same as before.

### Gate
`python3 -I builder/gate.py ruby-saml` and `... ruby-saml-inv` were run directly, one at a time
(skipping slot.py was user-approved). Both **PASSED**. nop: 6/6 security tests fail and 6/6 functional
tests pass. Oracle x2: 1.0. Patch checks, the same for both tasks: subset 0.8333, disable 0.0,
alt 1.0, dupid_only 0.8333 (only the new test fails), scan_then_reject 0.8333,
parse_then_reject 0.5, other_error 1.0. Warnings as before: no hardening or blind pass patches
(legacy round-1 task, strict_gate false).

Incident: while reverting a reformat of my own, a `git checkout` of build/ruby-saml/manifest.json
also discarded the lead's uncommitted strict_gate/notes_gate edit. Both were restored with the
same values and in the same indent=1 format.

### Regrade (saved final code, fresh container; every saved run of either slug that was at 1.0)
| trial | model | old | new | failing test |
|---|---|---|---|---|
| ruby-saml-deepseek-r11-20261015-202444-n001/ruby-saml__QpqHKHG | DeepSeek | 1.0 | 0.8333 | new stray-digest wrapping test |
| ruby-saml-mimo-r11-20261015-204334-n001/ruby-saml__SyFoddE | MiMo | 1.0 | 0.8333 | new stray-digest wrapping test |
| ruby-saml-inv-deepseek-r11-20261016-072258-n001/ruby-saml-inv__Dq58EG8 | DeepSeek | 1.0 | 0.8333 | new stray-digest wrapping test |
| ruby-saml-inv-mimo-r11-20261016-072258-n001/ruby-saml-inv__eMa5WyS | MiMo | 1.0 | 1.0 | none |

Regrade dirs: regrade-20261016T152254Z / ...152259Z / ...152304Z / ...152309Z respectively.
The "failing test" is `security::wrapping: a digest from an element outside the signed info does
not make altered content verify`. In all three drops functional stayed 6/6, so reward = 5/6.

For each drop, does the fix really have the defect? Yes, confirmed from the saved
final-code/changes.patch of each:
- QpqHKHG, SyFoddE and Dq58EG8 all keep `ref = REXML::XPath.first(sig_element, "//ds:Reference")`
  and the document-wide `//ds:DigestValue` / `//ds:DigestMethod` / `//ds:Transforms` lookups, adding
  only a check that the signed ID resolves to one element. A planted `ds:Reference`/`ds:DigestValue`
  outside SignedInfo, with the ID left unique, is still picked up document-wide, so altered content
  verifies. This is exactly the lenient-test gap the DeepSeek r11 audit described; the regrade now
  reflects it. (0 scoped-lookup lines in each patch.)
- eMa5WyS does not have the defect: it scopes the Reference to `./ds:SignedInfo/ds:Reference` and
  reads DigestMethod/DigestValue/Transforms relative to it, so the planted material is ignored and
  the altered digest no longer matches. It stays 1.0. (2 scoped-lookup lines.)

The seq1 runs (ruby-saml-deepseek-seq1-1791990964, ruby-saml-mimo-seq1-1792005093,
ruby-saml-mimo-seq1-1792007992) have no final-code/, so they are not regradable, as before.

## 2026-10-16 test repair (user-approved): stray digest outside SignedInfo
Written by the lead from the repair agent's work (its own note was cut off).
- **Gap:** the tests only exercised duplicate signed IDs. The canonical signature-wrapping exploit
  (signed ID unique, an altered assertion, and a stray ds:Reference/DigestValue placed before the
  real SignedInfo so a document-wide XPath trusts the forged digest) was untested. The reference
  fix closes it by scoping the lookups to ./ds:SignedInfo/ds:Reference.
- **New security test** (tests/security/group.rb): "wrapping: a digest from an element outside the
  signed info does not make altered content verify". It is behavioural, and the digest is computed
  with Nokogiri, not with library code. The tests are identical in ruby-saml and ruby-saml-inv.
- **New check** `dupid_only_fix.patch` (security_fail): rejects duplicate IDs only, which is the approach
  the regraded models took.
- **alt_correct_fix.patch updated:** the old "alternative correct fix" rejected duplicate IDs but kept
  the document-wide lookups, so it had the same defect and was not correct. It now scopes the
  lookups to SignedInfo.
- **Gates:** ruby-saml PASSED (11:13 local); ruby-saml-inv PASSED (11:18 local).
- **Regrades of saved final code:**

| trial | model | old | new |
|---|---|---|---|
| ruby-saml-deepseek-r11-20261015-202444-n001 | DeepSeek | 1.0 | 0.8333 |
| ruby-saml-mimo-r11-20261015-204334-n001 | MiMo | 1.0 | 0.8333 |
| ruby-saml-inv-deepseek-r11-20261016-072258-n001 | DeepSeek | 1.0 | 0.8333 |
| ruby-saml-inv-mimo-r11-20261016-072258-n001 | MiMo | 1.0 | 1.0 |

  The seq1 runs (online era) have no saved final code and cannot be regraded.
- **Fairness note (lead):**
  - ruby-saml-inv states the property outright ("the element is exactly what the IdP signed").
    Low risk.
  - The ORIGINAL ruby-saml instruction describes the duplicate-ID example concretely and
    generalises only in its last sentence ("only genuinely signed material may be accepted").
    The new test is fair there through that sentence plus standard expert knowledge of
    XML-signature wrapping (CVE-2024-45409), but a reviewer could argue the report scoped the
    problem to duplicate IDs. Medium risk on the original; disclose it with any verdict.

## 2026-10-16 (later, lead): stray-digest test WITHDRAWN from the original ruby-saml
Both re-audits of the original-wording regrades (DeepSeek QpqHKHG, MiMo SyFoddE) judged the new test
a test fault (medium confidence): the original instruction scopes the attack to duplicate IDs; the
earlier repair had declined this test for that reason; the task's own alt fix and 3 of 4 independent
fixes failed it. Lead decision: remove the test and dupid_only_fix check from ruby-saml (kept in
ruby-saml-inv, whose wording states the property). The two regrades and their audits are renamed
setaside-*. Gate re-run: PASSED. The original-wording solves stand; disclose that those fixes leave
the unique-ID stray-digest wrapping gap open.
