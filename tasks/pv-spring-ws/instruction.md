# Out-of-band SOAP replies can be aimed at internal destinations

Spring Web Services is a framework for building SOAP services and clients. A service built with it can answer a request in two ways: in the same connection, or out of band - by opening a new connection to a destination that the requester supplies in the message's WS-Addressing headers. Applications also use the same transport layer to send requests to destinations that they choose themselves.

## Observed impact

A client sent a request to a WS-Addressing service and asked for the response to be delivered to an address on the service's own private network. The service opened a connection to that address and delivered the complete response there: the internal endpoint received the response body while the client received an empty `202`. The request did not need to be authenticated.

## Required invariant

No request may cause the service to deliver a message out of band to a destination that the requester supplied unless that destination is safe for peer influence on the transport in use; and a request that the service rejects - including one rejected because it is not authenticated - must cause no out-of-band delivery at all.

The invariant applies to every way a response or a fault can be sent out of band, to every transport the framework offers, and to every form that a requester-supplied destination can take, including address literals of any family and transport-specific destination syntax. It also applies to any destination that ends up being used for the delivery, however that destination is expressed in the request.

## Refusal

When an out-of-band destination is not acceptable, the service must refuse cleanly: the client receives an in-band SOAP fault or an HTTP client error, and the service makes no connection and no delivery to that destination.

A single delivery can involve more than one requester-supplied destination. In that case the delivery may proceed only when every one of them is acceptable; otherwise the whole delivery must be refused.

## Must keep working

- Applications that send requests to destinations they choose themselves, including loopback and private-network addresses, must keep working exactly as today. The client side must not be restricted.
- Requests with an anonymous reply destination must still be answered in band; requests that ask for no reply must still have their response discarded.
- A reply destination that is ordinary and legitimate for the transport in use must still receive the out-of-band reply, and ordinary values that accompany it must keep working.
- Everything that works today must keep working exactly as today.

## Notes

The examples above are examples, not the full set. Fix the problem and its close variants; do not special-case the examples. Do not look up the upstream advisory or fix. Keep the change confined to this repository.

The project's dependencies are already available locally; build it with Gradle's offline mode.
