# Playlist access in gonic

gonic is a self-hosted music streaming server that speaks the Subsonic API. People sign in with their own accounts, and each account keeps its playlists in its own part of the server's playlist storage.

## Impact

A signed-in listener can open another listener's private playlist by sending that playlist's identifier to the playlist read operation. The response gives them the other listener's playlist details and the songs it holds.

## Security properties

Playlist identifiers are supplied by clients.

1. **Containment.** No client-supplied playlist identifier may make the server touch anything outside the playlist storage area. After cleaning, an identifier either resolves to a location inside that area, or the request is refused.

2. **Access.** A playlist's contents must stay visible only to the listeners the product's existing sharing rules already allow, and a playlist may be altered only by its owner. Who owns a playlist is decided from the playlist as stored, never from what the caller sends.

## Contracts

- A refused request returns a Subsonic error response and has no effect.
- Everything that works today keeps working exactly as today, for every listener and every playlist.
- The example above is an example, not the full set of affected inputs.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example.
