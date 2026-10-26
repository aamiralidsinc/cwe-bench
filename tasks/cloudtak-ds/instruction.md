# Basemap sources can reach services that only the API server can see

## What this is

This repository is the API behind CloudTAK, a situational-awareness web application built around a
TAK server. Users add basemaps — tile sources the web client draws behind the map — by importing
one from a URL, recording one directly, or updating an existing entry. The API reads metadata from
those sources and hands tile metadata to clients.

## What was observed

A user can record a basemap whose source is an address only the API server can reach — a service on
the loopback interface, a private-network address, or a link-local address such as a cloud instance
metadata service — and then read that basemap's tile metadata. The API contacts the address
server-side and returns the service's own JSON (including its name and attribution) to the user.

## Required behaviour

- No destination supplied by a caller, and no destination the API is sent to by something it
  contacts, may cause a server-side request to reach a loopback, private, link-local,
  shared/CGNAT, unique-local, unspecified, multicast, or cloud-metadata address. What matters is
  the address the connection ends up using, however that address was derived, including a
  destination that was stored earlier and is contacted later.
- When a name maps to several addresses, every one of them must be acceptable; a single internal
  address is reason enough to refuse.
- A refused operation fails with a client error and nothing is sent to the refused address. The
  wording of the error is not specified.
- An internal service that an operator has explicitly configured the product to use keeps working
  exactly as today, for the destinations the operator configured. That authorisation does not
  extend to other destinations a caller chooses.
- Legitimate use keeps working exactly as today: ordinary public basemap sources are still
  imported, stored, updated, listed and read; metadata from the operator's configured tile
  service is still fetched and returned; public interfaces, field names and response formats do
  not change.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
