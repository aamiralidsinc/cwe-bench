# Stored credentials can be put to use by callers who cannot read them

Perses keeps reusable connection credentials in separate objects that belong to a project, or to
the whole installation for global datasources. A datasource configuration may name one of those
objects, and when a query travels through the datasource proxy, the server attaches the stored
credentials to the request it forwards to the datasource.

A user who may create and read datasources in a project, but who has not been granted read access
to that project's credentials, can send the proxy a datasource description that names a credential
she may not read. The server resolves the credential and forwards the request carrying it. The
same thing happens when such a reference is saved into configuration and used afterwards: the
server acts with somebody else's credentials for a caller who was never allowed to see them.

## The property that must hold

A caller may cause the server to use a stored credential only when that caller may read the
credential being used. This holds for every way a reference can reach the server, for every form a
reference can take, and for every place the server can be made to resolve one, including
references that were saved earlier and are used later.

A refusal is a client error, and it leaves nothing behind: no request is sent with the credential
and no configuration carrying the reference is kept.

## Everything else must keep working

* Configuration that names no credential keeps saving and working for callers who cannot read any
  secret.
* A caller that may read a datasource but not the credential it names keeps querying that
  datasource exactly as today, once the reference has been accepted from somebody entitled to make
  it.
* A caller that may read a credential keeps referencing it in any form the product accepts, and
  the requests it makes keep carrying the credentials.
* Everything the product already does with configuration it holds keeps working for the callers
  entitled to it.

The example above is one example; the property applies wherever a stored credential can be
referenced, not only to the request shape shown.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.
