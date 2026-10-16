# SSH sessions can be brought up with no cryptographic protection at all

## Summary

We operate SSH endpoints built on this library (the vulnerable source is in
`/app`). To interoperate with a mix of old and unusual peers we run a permissive
configuration: our offered algorithm lists include, alongside the strong modern
choices, several legacy and "null" options — including the `none` message
authentication (MAC) option, the `none`/`clear` (no-encryption) cipher, and a
`none` key-exchange entry. We expected the library to still insist on a secure
combination and to simply ignore the insecure ones unless nothing else matched.

Instead we find that a remote peer can steer the ordinary SSH handshake — the
library's public client/server transport API, driven exactly as a downstream
application drives it — into completing a session that carries **no
confidentiality, no integrity, and/or no server authentication**. The handshake
returns success and the session is usable. This happens whichever side makes the
offending offer: a malicious client against our server, or a malicious server
against a client built on this library.

## What a peer can force

All of the following are reached purely by what a peer lists in its handshake
offer, against a counterparty whose configuration also permits the option:

- **No key agreement and no host-key proof.** A peer can steer key exchange to
  the `none` exchange, which performs no key agreement and causes no host key to
  be signed or verified. The handshake still completes. The resulting session is
  fully exposed: there is no shared secret and the endpoint was never
  authenticated.

- **Plaintext with no integrity.** A peer can steer the cipher choice to the
  `none`/`clear` (no-encryption) cipher while the MAC choice is `none`. The
  handshake still completes and a session is established whose traffic is sent in
  the clear and can be altered undetected.

- **Integrity silently dropped.** A peer can steer the choice to a classic
  block/stream cipher that is *not* self-authenticating (the CTR and CBC family,
  and triple-DES) while the MAC choice is `none`. The handshake still completes
  and the session has no message authentication at all; its traffic can be
  tampered with undetected.

## Required outcome

The library must never finish bringing up a session that lacks cryptographic
protection. A handshake that would settle on the null key exchange, or on a
cipher that provides no integrity of its own (the null/clear cipher, or a
MAC-requiring block/stream cipher) with no genuine MAC, must be rejected cleanly
as a failed handshake — in **either** direction of the exchange — so that no
unprotected session is ever established. A fix that closes only one of these
routes, or that merely prevents a downstream crash while still allowing such a
session to be set up, does not meet this requirement.

Legitimate behaviour must be fully preserved:

- Authenticated (AEAD) ciphers provide their own integrity, so pairing one of
  them with the null MAC is valid and must still connect and carry data.
- Any encrypting cipher paired with a genuine MAC must continue to connect and
  carry data. Whether the no-encryption cipher may still be used with a genuine
  MAC is left to you; either choice is accepted.
- Every real key exchange must continue to work, and ordinary default
  configurations must continue to interoperate.

## Notes

The repository is in `/app`. There is no network access at run time; any peer
used to reproduce this must be local (in-process or over the loopback
interface).
