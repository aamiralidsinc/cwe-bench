# stk-tomcat-ghsa69r9-control build notes

Start (UTC): 2026-10-26T02:17:04Z
End (UTC): pending

## What this is

The one-bug control for `stk-tomcat-ghsa69r9`: the same pinned Tomcat tree (`81c7afb323cf4f12f8b49a422962ad3588917e9c`), the same byte-identical `instruction.md`, but only the advisory's own route in the security tests and the reference. It isolates the effect of stacking from the effect of the host.

## What differs from the stacked task

- `tests/security/SecClusterMessageIntegrityTest.java`: four cases on the default configuration only (IV first/last byte, first/second ciphertext block). All four fail on the pinned tree for tamper acceptance and pass on the control reference.
- `solution/fix.patch`: change the default algorithm to `AES/GCM/NoPadding` (the same patch as the stacked task's `checks/default_gcm.patch`). This closes only the default-configuration route; the stacked task's other two concepts are absent by construction.
- `tests/functional/` is the same as the stacked task (the project's own `TestEncryptInterceptor` plus the two chain cases), so the control keeps every documented configuration and legitimate channel setup working.
- `checks/` uses the stacked task's applicable patches: `upstream_fix.patch` and `upstream_first_fix.patch` (both fail the four default-route cases), `crash_on_failure.patch` (security_fail), `verify_only.patch` and `functional_fail.patch` (functional_fail), `hardening.patch` and `alt_correct_fix.patch` (pass). The wrong-fix catalogue maps the applicable classes to those patches and explains the n/a classes.

## Verified

- Pinned tree: 4/4 security cases fail (all four deliver the modified plaintext); 18/18 functional cases pass.
- Control reference: 22/22 pass.
- All patches apply with `patch -p1` to the pinned tree.

## Gate

- static: pending
- nop: pending
- oracle: pending
- patches: pending

## Note on the build prompt's screener lead

The embedded screener record (Kubernetes membership providers) does not match the advisories or the fix commits; see the stacked task's notes.md. Both tasks were built from the actual `EncryptInterceptor` fix commits.
