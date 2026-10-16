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
