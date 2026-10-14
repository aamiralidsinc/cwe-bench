# SSH sessions can be brought up with no integrity protection, then crashed by a short packet

## Summary

We operate an SSH server built on this library (the vulnerable source is in
`/app`). To interoperate with some older peers we widened the set of integrity
(MAC) algorithms our configuration is willing to accept so that it also includes
the null / `none` option, on the assumption that our modern authenticated
(AEAD) ciphers would still protect the traffic by themselves.

With that configuration we observe two linked problems, both reachable by a
remote peer through the ordinary SSH handshake (the library's public
client/server transport API, driven exactly as a downstream application drives
it):

1. **Integrity can be silently dropped.** A peer can steer algorithm agreement
   so that the session uses a classic block/stream cipher that is *not*
   self-authenticating (the CTR and CBC family, and triple-DES) while at the
   same time the null MAC is chosen. The handshake nonetheless completes and the
   session is established. Such a session has no message-authentication at all:
   its traffic can be tampered with undetected. This happens whichever side
   makes the offending offer — a malicious client against our server, or a
   malicious server against a client built on this library.

2. **A short packet then crashes the peer.** Once such a non-authenticated
   session exists, a single truncated / undersized record from the peer drives
   the receive path out of bounds and panics the connection task, dropping the
   connection. So the same misconfiguration an attacker can force also becomes a
   remote denial-of-service.

## How it is triggered

Through the public transport API: a peer whose offered algorithms list a
MAC-requiring cipher (for example a CTR or CBC cipher) together with `none` for
the MAC negotiates a session against a counterparty that also permits `none`.
The handshake succeeds and a MAC-less session is set up; a subsequent undersized
packet panics the receiver.

## Required outcome

The library must never finish bringing up a session that pairs a cipher
requiring a separate integrity MAC with the null MAC. That combination must be
rejected during the handshake — cleanly, as a failed negotiation — in **either**
direction of the exchange, so that no non-authenticated session is ever
established and the out-of-bounds receive path is never reached. A fix that only
stops the crash while still allowing such a session to be set up does not meet
this requirement.

Legitimate behaviour must be fully preserved:

- Authenticated (AEAD) ciphers provide their own integrity, so pairing one of
  them with the null MAC is valid and must still connect and carry data.
- Any cipher paired with a genuine MAC must continue to connect and carry data
  as before.
- Ordinary default configurations must continue to interoperate.

## Notes

The repository is in `/app`. There is no network access at run time; any peer
used to reproduce this must be local (in-process or over the loopback
interface).
