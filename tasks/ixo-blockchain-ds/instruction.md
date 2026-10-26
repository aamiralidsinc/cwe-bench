# Unauthorized balance and record operations

This service is a Cosmos-based public ledger. DIDs identify organisations and people, and each
DID document lists the accounts and keys that may act for it. A request carries the DID it acts
for together with the account address of the party submitting it.

## Observed impact

A client submitted an outcome-payment request that reached its module without the usual
transaction-level signer check (the request was dispatched by another module on the sender's
behalf). It named a DID it does not control, while the request's signer field carried the
client's own address. The ledger took the payment out of the account that the named DID
resolves to, so a party that never authorized anything paid.

## Security invariant

Every request the ledger executes must be authorized by its signer for the exact object it
touches:

* coins must never be taken from an account that does not belong to the request's signer;
* a record that belongs to a DID must only change when the request's signer is one of that DID's
  controllers, meaning a key listed on the DID document under the authentication or
  assertion-method relationship;
* a DID that a request merely names as its subject does not have to authorize the request, and
  naming it does not make the request an action of that DID.

An entry in a DID document does not, by itself, make an account belong to the signer.

This must hold however the request reaches the module.

## Contracts

* Refusal: a request that cannot be authorized must be refused with a client error and must leave
  balances and stored records unchanged.
* Legitimate requests keep working exactly as they do today: a request signed by a controller of
  the DID it acts for succeeds, a controller key registered under either relationship is accepted,
  a DID document may hold several keys and any of them that the signer holds remains usable, and a
  request may name another party as its subject without that party signing.
* Amounts are not restricted: 500 uixo is as valid an amount as 1 uixo.

The examples above are examples, not the full set of requests, records or routes covered by the
invariant.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the reported example.
