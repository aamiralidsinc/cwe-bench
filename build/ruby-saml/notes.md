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
No network at run time. Fixtures (signed responses + IdP cert) live under
`tests/fixtures`, copied from the repo, and all exploit payloads are generated
in-process. Tests never read from `/app`.

## Caveat
`source` in task.toml is `mined` (not `mined+stacking`) because the current
`gate.py` static check only accepts `mined|mined+injected|injected`; the stacking
nature is recorded in `manifest.build_kind` and in task.toml `tags`.
