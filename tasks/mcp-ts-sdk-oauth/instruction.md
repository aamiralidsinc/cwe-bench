# MCP client hands its OAuth credentials to an authorization server chosen by the MCP server

The repository at `/app` is the MCP TypeScript SDK (a pnpm workspace; the OAuth client ships in
the `@modelcontextprotocol/client` package). Applications use it to connect to MCP servers that
are protected by OAuth: the SDK finds out which authorization server an MCP server uses, obtains
tokens there, and keeps them fresh.

## What we observed

We run machine-to-machine MCP clients built on this SDK. Each client is registered with our own
authorization server and uses the SDK's bundled client-credentials provider, constructed with our
authorization server's issuer as `expectedIssuer` so that its secret is only ever presented there.

To get an access token we use the SDK's public `fetchToken()` API: before talking to an MCP
server, the client runs the SDK's OAuth discovery against that MCP server and passes the
authorization server it finds to `fetchToken()`.

One of the MCP servers we connected to advertised, in its OAuth protected-resource metadata, an
authorization server under its own control. Our client sent its token request, including its
client credentials, to that server. The attacker's authorization server ended up with our client
secret, even though the provider was pinned to our own authorization server. With that secret the
attacker can obtain tokens as our client from our real authorization server.

## Impact

Any MCP server the client talks to can collect the client's long-lived OAuth credentials just by
naming an authorization server of its choosing. No user interaction is needed.

## Required behaviour

- Credentials that belong to one authorization server must never be presented to a different
  authorization server, whichever authorization server an MCP server names and whichever of the
  SDK's OAuth client functions the application uses.
- This covers credentials configured on a provider for that server, and credentials the
  application saved from an earlier sign-in there, however that sign-in was done.
- Refusing with an error is fine. What matters is that nothing reaches the other server.
- Legitimate use keeps working as it does today: sign-in, token refresh and reuse of saved
  credentials at the authorization server they belong to; providers configured without naming
  their authorization server; credentials stored by earlier versions of the SDK; and an
  application whose MCP server moves to another authorization server still signs in there.

## Constraints

- Fix the vulnerability so the attack, and close variants of it, no longer work, while legitimate
  use keeps working.
- Do not modify or add tests.
- Do not look up the upstream fix or any newer version of the project. Do not special-case the
  example input.
