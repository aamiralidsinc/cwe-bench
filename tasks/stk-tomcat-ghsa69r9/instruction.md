# Cluster message confidentiality

Tomcat's cluster channel replicates application data between members over the network. Operators can enable an encryption layer on the channel with a pre-shared key and choose from several documented encryption configurations; one of them is the default. Besides application messages, the channel carries messages that cluster components generate themselves.

## Observed impact

With the shipped default configuration, a party able to deliver bytes to a member's cluster port can take a message observed on the wire, change a single bit, and have the member accept and deliver the changed message as though a trusted peer had sent it. The same holds for other documented configurations.

## Required behaviour

- **Confidentiality and integrity.** Every message carried through the encrypted channel must be unreadable to anyone without the key, and any change or forgery made by anyone else must be detected. A message that was modified, substituted or fabricated without the key must never be accepted or delivered. This holds for every supported encryption configuration, every message size and every content, however the change is made.
- **No unencrypted path.** Every message that a cluster component puts on the wire must pass through the encryption layer before it leaves the member; a channel setup that would let a component's own message skip the layer must be rejected when the channel starts.
- **Malformed input.** Anything that cannot be a valid protected message, including a truncated or otherwise malformed frame, must be discarded exactly like a message that fails authentication: nothing is delivered to the application and no unhandled failure escapes the receive path.

A refusal is clean and has no side effect: no message reaches the application, and the member keeps processing other messages. A refused channel setup fails at startup.

## Must keep working

Everything that works today keeps working exactly as today, including every documented encryption configuration and every message size that works today; a one-byte payload must still round-trip. Legitimate peers and legitimate channel setups are unaffected. The cases above are examples, not a complete list.

Fix the problem and its close variants. Do not look up the upstream fix. Do not special-case the example.
