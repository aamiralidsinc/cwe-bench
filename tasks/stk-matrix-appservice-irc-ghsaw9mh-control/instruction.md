# Matrix to IRC bridge: quoted message content

The IRC bridge connects Matrix rooms to IRC channels. Messages sent in a bridged Matrix room are relayed to the linked IRC channel; when a message refers to another Matrix message, the bridge adds a short quotation of the referenced message so IRC readers can follow the conversation.

## What was observed

A user who has just joined a bridged Matrix room can send a message that refers to an older message they were never allowed to see. The bridge follows the reference using its own access, then posts a quotation of that older message into the linked IRC channel. Every channel member can then read text from the older message, including people who were never entitled to see it.

## The property

The bridge must not put any text from a Matrix event into an IRC channel unless the person whose message refers to that event was entitled to see it. When the bridge cannot establish that entitlement, it relays the sender's own message without any of the referenced text.

The entitlement decision must be based on what the bridge itself observed in the room. A time or membership fact supplied by the homeserver, or the absence of one, must not make an event visible to someone who could not see it.

## Contracts

- When referenced text is withheld, the sender's own message is still delivered to the channel. It must not be dropped, and it must not become an error.
- Everything that works today keeps working: ordinary messages, legitimate references the sender is entitled to make, formatting, and message truncation.
- The examples above are examples, not the full set. Fix the problem and its close variants.
- Do not look up the upstream fix, the advisory, or later releases of the project, and do not special-case any single event, sender, room, or message shape.
