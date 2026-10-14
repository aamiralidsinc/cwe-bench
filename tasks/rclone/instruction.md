# Authentication bypass in the S3 server's authentication-proxy mode

## Summary

This repository is a command-line cloud storage tool. Among its commands is one
that serves a remote over an S3-compatible HTTP API. That server can be run in a
mode where an external authentication-proxy program decides who may connect: for
each S3 access key ID presented by a client, the proxy program maps that identity
to the storage backend it is allowed to use. In this mode the server is started
without any static access-key/secret pair configured on the command line, so the
proxy is intended to be the sole authority over who gets in.

Clients authenticate to the server with ordinary AWS Signature Version 4: they
send their access key ID and a signature computed from their secret access key,
but they never transmit the secret itself. For the server to actually
authenticate a client it must therefore know the secret belonging to that access
key ID and check the request's signature against it.

## Impact

In authentication-proxy mode the server does not verify the request's signature
against the real secret for the presented access key ID. Instead it accepts a
signature computed with an **empty** secret string. Because an empty secret is
something anyone can use to sign a request, a client can present the access key
ID of any identity the proxy recognises — without knowing that identity's real
secret — and be authenticated as that identity.

The consequences are full impersonation. Having been let in as another identity,
the attacker is handed that identity's backend and can carry out any S3
operation against it: listing buckets, reading objects (disclosing their
contents), uploading or overwriting objects, and deleting objects. The attacker
only needs to know or guess a valid access key ID; the secret, which is supposed
to protect the account, provides no protection at all.

## How it is triggered

1. Start the S3 server in authentication-proxy mode, with the proxy program as
   the only configured authentication and no static key pair.
2. As a client, choose any access key ID the proxy accepts and sign an S3
   request for it using Signature Version 4 with the secret set to the empty
   string.
3. Send the request to the server (for example a request to list the buckets, or
   to GET, PUT or DELETE an object).
4. The server accepts the forged request and performs the operation on the
   impersonated identity's backend, returning its data.

The same flaw applies to every S3 operation reachable through the server and to
every access key ID the proxy maps, not just one particular request.

## What a correct fix must guarantee

- A request presented for an access key ID must be accepted **only** when its
  signature verifies against the real secret that belongs to that access key ID.
  A request signed with an empty secret, or with any secret other than the
  correct one, must be refused with an access-denied response. This must hold for
  all S3 operations and all access key IDs.
- Legitimate use must keep working. A client that signs with the correct secret
  for its access key ID must still be served, and the server must keep running
  and answering requests. The ordinary static-key mode (where a key/secret pair
  is configured directly, without a proxy) must also continue to authenticate
  correctly. A change that refuses to run the proxy mode, tears the server down,
  or rejects correctly authenticated clients is not an acceptable fix.

## Environment

The task builds offline. The language toolchain and all dependencies are already
installed in the image, and the server, the authentication-proxy program and the
test client all run on localhost with no external network access. No real cloud
storage or remote S3 service is involved or required.
