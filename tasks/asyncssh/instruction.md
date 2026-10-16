# Security review: SSH library misbehaviours

I have been testing the SSH library in `/app` by driving it over a loopback
socket — standing up a server and a client with its public API, and in a few
cases talking to it from a hand-written socket peer. Several behaviours look
like security problems. Please find the root cause of each and fix them so the
library is safe, while keeping all the normal functionality working. The
library must keep installing and importing from `/app`.

## What I observed

**Unauthenticated traffic is honoured during the handshake.** While the initial
key exchange is still in progress — before any encryption is negotiated — a peer
can send a connection- or authentication-layer packet and the library acts on
it instead of refusing it. I reproduced this in both directions: a raw client
that sends an early authentication request to the server, and a raw server that
sends an early extension-information packet to the client. In each case the
targeted endpoint accepts the out-of-sequence packet and stays connected. A
correct endpoint should never act on these packets before the secure channel is
established; it should drop the connection.

**A user name can escape its key directory.** I configured the server to locate
each account's authorized keys through a per-user path template (one directory
per user, chosen by the account name). A client that presents a user name
containing path-traversal segments makes the server look for authorized keys in
a directory *outside* the key area, and it will authenticate a key planted
there. Connecting as a normal user with a normal name must still work, but a
name that walks outside its own key directory must be refused.

**An SCP download can write outside the target directory.** Using the library's
SCP client to download from a server, a malicious or compromised server can name
a transferred file with a leading traversal segment, and the client writes the
file *outside* the local directory I asked it to download into. A legitimate
download (an ordinary file name, including names with a dot in them) must keep
working, but a name that points outside the destination must be rejected.

**A channel open can hang the endpoint.** When a peer opens a channel it states
the largest packet it will accept. If a peer advertises a maximum packet size of
zero, the endpoint hangs as soon as it has channel data to send back — it spins
on the CPU and never returns, so a single crafted channel open is a
denial-of-service. Normal channels (with a sensible packet size) must keep
carrying data, including transfers large enough to span many packets.

## What must hold afterwards

- Normal password and public-key logins, interactive command runs (small and
  large output), and ordinary SCP downloads all keep working.
- Each of the abuses above is rejected through the same public entry points.
