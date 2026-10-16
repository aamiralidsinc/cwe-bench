# Authentication bypass across several of the serve surfaces

## Summary

This repository is a command-line cloud storage tool. It can expose a remote to
the network in several different ways, each speaking a different protocol: an
S3-compatible HTTP API, a plain HTTP file server, an FTP service and an SSH
(sftp) service. Every one of these lets a client authenticate before it is
given access, and each decides for itself whether the credentials a client
presents are acceptable.

In all of these modes the client proves its identity with a secret it never
fully transmits, or transmits only to be checked: an S3 client sends an access
key ID together with a signature computed from its secret access key, while an
HTTP, FTP or SSH client sends a username together with a password. The server
is supposed to accept the request only if the secret or password presented
really matches the one belonging to that identity.

## Impact

Several of these serve surfaces identify the client correctly but then fail to
actually verify the secret it presents. The practical effect is the same on
each affected surface:

- On the S3 surface, when identities are supplied by an external
  authentication-proxy program, a request is accepted if its signature was
  computed with an **empty** secret. Since anyone can sign with an empty
  secret, knowing a valid access key ID is enough to be authenticated as that
  identity and to list, read, write and delete its objects.
- On the username/password surfaces, a client that presents a **valid
  username** is accepted even when the password is wrong or empty. The password
  that is supposed to protect the account provides no protection at all.

In every case an attacker who knows only a valid identity (an access key ID, or
a username) can impersonate it without knowing its secret, and then perform the
operations that identity is entitled to.

## How it is triggered

1. Start the tool serving a remote in one of the affected modes.
2. As a client, choose an identity the server recognises.
3. Authenticate to it with the matching empty/absent/wrong secret — an S3
   request signed with an empty secret, or a username with a wrong password.
4. The server accepts the request and serves the impersonated identity.

This is not limited to one request, one identity or one protocol: it holds for
every operation reachable through each affected surface.

## What a correct fix must guarantee

- A request presented for an identity must be accepted **only** when the secret
  or password it carries verifies against the real secret belonging to that
  identity. A signature made with an empty secret, or a wrong or empty
  password, must be refused. This must hold on every affected serve surface.
- With `--auth-proxy`, the proxy program is the source of each identity's secret: it
  returns the secret access key in the `_secret_access_key` field of its JSON result
  (alongside `_root` and the backend settings). If the result has no
  `_secret_access_key`, or it is empty, the identity has no usable secret and every
  request for it must be refused.
- Legitimate use must keep working. A client that presents the correct secret
  or password for its identity must still be served, each server must keep
  running and answering requests, and requests with no credentials, an unknown
  identity, or the wrong secret must still be refused. A change that refuses to
  run a serve mode, tears a server down, or rejects correctly authenticated
  clients is not an acceptable fix.

## Environment

The task builds offline. The language toolchain and all dependencies are
already installed in the image, and every server, the authentication-proxy
program and the test clients run on localhost with no external network access.
No real cloud storage or remote service is involved or required.
