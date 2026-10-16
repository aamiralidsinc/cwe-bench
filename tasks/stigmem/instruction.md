# Security review: stigmem reference node

You are hardening the stigmem reference node (the Python service under
`/app/node`, importable as `stigmem_node`, a FastAPI application). A review of
a recent deployment surfaced several independent weaknesses. Each is reachable
by an ordinary client or operator through the node's real surfaces — its HTTP
API, its service startup/configuration, and its plugin-loading path. Your job
is to close all of them while keeping the node's legitimate behaviour intact.

## Observed problems

**Federation peers trust themselves in.** A remote party can call the node's
peer-registration HTTP endpoint, presenting a declaration it signed with its
own key (the node confirms the key against the party's own published document).
On acceptance the peer immediately reaches a fully-established state and its
federation bearer token is honoured on the federation data endpoints — it can
pull and replicate records straightaway. No human operator at the receiving
node ever has to review or confirm the new relationship out of band. A freshly
self-declared peer must not become established on its own, and its token must
be refused on the federation endpoints until the operator has confirmed it.

**The node will boot wide open when it is not supposed to.** Two startup
configurations that are only ever meant for a developer's local machine are
accepted even when the node is bound to a public, non-loopback address:

- running federation with its transport security (mutual TLS) turned off, so
  federation traffic is unauthenticated cleartext; and
- running with authentication switched off, where the anonymous caller is
  granted full read/write/federate authority over the API.

Started on a non-loopback address, either of these exposes the node to the
network in a state it should never be in. Starting in such a state must be
refused; the same options must still be allowed for a genuine loopback/dev
deployment.

**Risky operational modes engage silently.** Two "off switches" take effect
with nothing more than the flag that disables the protection:

- unsigned third-party plugin code is loaded and executed at startup when
  signature enforcement is turned off; and
- request-quota enforcement is fully disabled (both the read and the write
  limits set to zero), so the node accepts unbounded traffic.

Each of these should demand an explicit, deliberate operator acknowledgement
before it is allowed to take effect; with only the bare flag set and no such
acknowledgement, the node must refuse rather than proceed.

**Local storage is readable by other users.** On startup the node creates its
on-disk database — which holds API-key material, stored records and federation
secrets — with permissions that leave it readable by other local accounts on
the host. The database must be created so that only its owner can access it.

## What must hold

- Every attack path above, exercised through the node's real entry points,
  must be blocked after your change.
- Legitimate use must keep working: a valid peer can still be onboarded; the
  loopback/dev configurations above still start; normal authenticated API
  operation is unaffected; and properly signed/trusted plugins still load.

No dependency may be added that requires network access at test time; the node
runs entirely offline against its default local storage.
