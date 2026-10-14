# hickory-dns build notes

## Verified against the code (not trusted from the candidate row)

- **Flaw.** `CachingClient::lookup` in `crates/resolver/src/caching_client.rs`
  computes `is_dnssec = client.client.is_verifying_dnssec()` but, on the
  vulnerable parent commit, never consults the per-record DNSSEC verdict before
  returning. Records that validation marked `Proof::Bogus` are returned to the
  caller inside `Ok(Lookup{..})`. Reproduced directly: on the vulnerable commit
  both `Resolver::lookup` and `Resolver::lookup_ip` return
  `Ok(.. proof: Bogus ..)`; on the fix commit they return an error.

- **Trust decision / entry points.** `Resolver::lookup` routes through
  `inner_lookup` -> `LookupFuture`; `Resolver::lookup_ip` routes through
  `LookupIpFuture` directly. Both converge on `CachingClient::lookup`, which is
  where the upstream fix places the check. Confirmed `lookup_ip` does not call
  the public `lookup`, so a one-site fix inside `lookup` leaves `lookup_ip`
  exploitable — this is the basis of the `security_fail` check.

- **Tempting wrong fix (candidate's claim), verified.** Candidate said a fix in
  `Resolver::lookup` that rejects non-secure records (a) misses `lookup_ip` and
  (b) would break unsigned/insecure zones. Both confirmed:
  - `shallow_poc_only.patch` adds the check only in `Resolver::lookup`; the two
    `lookup_ip` security tests still fail while all functional tests pass.
  - `disable_feature.patch` rejects anything not fully `Secure` regardless of
    whether validation was requested; unsigned (validation-off) answers carry
    `Proof::Indeterminate`, so four functional lookups break.
  - `alt_correct_fix.patch` places the Bogus check at the resolver layer in
    BOTH `lookup` and `lookup_ip`; all 9 tests pass (a valid alternate fix at a
    different layer than upstream).

## No-network design

- The `test-support` crate's `MockProvider`/`MockNetworkHandler`/`MockRecord`
  (present at the vulnerable commit) provide a fully in-process scripted
  upstream. No sockets, no real DNS. This mirrors the upstream fix commit's own
  added unit test.
- `Proof::Bogus` is produced deterministically by giving the validating resolver
  a trust anchor while the scripted upstream denies the DS RRsets with unsigned
  SOA records, so no chain of trust can be built.

## Could NOT verify / guesses

- The crate's own DNSSEC resolver tests query live public resolvers, so they
  were not run in the no-network image (documented in the manifest).
- The upstream fix also touches the server forwarder (`catalog.rs`) and the
  retry handle; those are included in `fix.patch` for fidelity but are not
  exercised by the harness (the harness uses the resolver library API, not the
  server crate). The variants cover the resolver-side entry points, which is the
  documented library entry point for this task.
- Base image is `rust:1-slim-bookworm` (latest stable). The shipped `Cargo.lock`
  was resolved with stable 1.99; the image toolchain must be >= the MSRVs it
  pins (max observed 1.90). Latest stable satisfies this.

## Host validation (outside Docker, for fast iteration)

All four states were run with `cargo nextest` against the real repo at the two
commits and with each check patch applied:
vulnerable -> 4 security FAIL / 5 functional PASS; oracle -> 9 PASS;
shallow -> 2 security FAIL, functional PASS; disable -> 4 functional FAIL;
alt -> 9 PASS. The gate re-runs all of this inside Docker.
