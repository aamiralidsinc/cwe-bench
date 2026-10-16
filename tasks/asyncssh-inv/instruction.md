# SSH library: security review findings

## Report

We embed the Python SSH library checked out at `/app` on both sides of our
deployment: as an SSH server (password and public-key logins, command
execution) and as an SSH client (running commands and downloading files with
its SCP support). The server reads an OpenSSH-style configuration in which
each account's authorized keys are found through a per-user path template,
one key directory per account name.

A security review drove the library over loopback through its public API, in
places with a hand-written socket peer standing in for the other side. It
found several ways in which a hostile peer, either a client or a server, can
break the guarantees below. One example: a raw client sent its version line
and then, in plaintext and before any key exchange, a user-authentication
request. The server acted on it and kept the connection open.

## Security properties the library must keep

- A login may only be authorized by keys placed for that account under the
  configured per-user key location. No user name a client presents may steer
  the authorized-keys lookup outside that location; such a login must be
  refused.
- An SCP download writes only inside the local destination the user chose. No
  file name or other data sent by the remote side may make the client create
  or write a file anywhere outside that destination.
- Until the initial key exchange has completed, an endpoint, server or client
  alike, must not act on anything a peer injects into the plaintext handshake
  that is only valid once the secure channel exists (user authentication,
  protocol-extension negotiation and the like). On receiving such a message it
  must drop the connection promptly.
- Each side of a channel states the largest packet it will accept. Whichever
  side states it, whether opening a channel or accepting one, a size too small
  to carry any data (such as zero) must never make the receiving endpoint
  hang. The channel must instead be refused promptly with a protocol error,
  which the application sees as the library's ordinary error.
- Legitimate use must keep working exactly as it does today: password logins;
  public-key logins of ordinary account names through the per-user template;
  command runs with small output and with output of hundreds of kilobytes that
  spans many packets at the default packet sizes; and SCP downloads of
  ordinary file names, including names that contain dots.

## Constraints

- Fix the library so that the reported attack and close variants of it no
  longer work, while the legitimate uses above keep working.
- Do not modify, delete or add tests. Hidden tests will grade the result.
- Do not look up or copy the upstream fix for this issue.
- Do not special-case the example above.

## Environment

Pure Python; no services to start. The library is installed in editable mode
from `/app`, so edits to its source take effect immediately. It must keep
installing and importing from `/app`.
