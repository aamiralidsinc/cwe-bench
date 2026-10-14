# Forged DNS answers accepted when DNSSEC validation is enabled

## Summary

This repository is a DNS client/resolver library. An application uses it as a
library: it constructs a resolver configured to perform DNSSEC validation (it
is given one or more trust anchors) and then calls the resolver's public
name-resolution API to look up addresses and other records for a name.

When DNSSEC validation is enabled, the resolver does perform validation of the
records it receives from upstream. However, when validation concludes that an
answer is **not** cryptographically trustworthy — for example the signatures are
forged or tampered with, or no valid chain of trust to a configured trust anchor
can be established — the resolver still returns those records to the caller as an
ordinary successful result, with no error reported.

## Impact

A downstream application that enabled validation specifically to reject
untrusted data cannot tell a forged answer from a genuinely validated one. A
malicious or on-path upstream name server can therefore feed the application
attacker-chosen records (addresses, mail hosts, text records, and so on) for any
name, and the application will accept them as authentic. This defeats the entire
purpose of turning validation on.

## How it is triggered

1. Build a validating resolver (configured with trust anchors) that talks to an
   upstream the attacker controls or can inject responses into.
2. Resolve a name through the resolver's public lookup API.
3. The upstream returns records whose signatures do not validate.
4. The call returns the attacker's records as a successful answer instead of
   failing.

The same flaw is reachable through more than one of the resolver's public
resolution entry points, and for both positive answers and different record
types.

## What a correct fix must guarantee

- When validation is enabled and an answer cannot be cryptographically
  validated, the resolution call must **fail** (return an error) rather than
  hand the untrustworthy records to the caller. This must hold across the
  resolver's resolution entry points, not just one of them.
- Ordinary resolution must keep working. Non-validating resolvers, and lookups
  that are legitimately resolvable, must continue to return their answers as
  before. A fix that turns normal, acceptable lookups into errors is not
  acceptable.

## Environment

The task builds offline. A scripted, in-process upstream stands in for real DNS;
no network access is available or required at test time. Rust and the test
runner are already installed in the image; dependencies are pre-built.
