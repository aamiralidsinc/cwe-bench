# Callers can reach alt-text data their collection access rules exclude

## What this is

This repository is a Payload CMS plugin that adds AI-generated alt text and keywords to image
upload collections. It runs inside the host application: its HTTP handlers take a collection and
one or more document identifiers, read the documents, generate text through a configured resolver,
and may save the result. It also exposes server-side functions used by the host application.

## What was observed

An authenticated user who is not allowed to read a given upload collection's documents sent a
request to the plugin's single-image generation endpoint with that document's identifier. The
response contained alt text generated for the image. Sending the same request in its saving form
also wrote the generated alt text and keywords onto the document.

## Required behaviour

Every request handled by the plugin must be limited to what the requesting user's collection access
rules allow on the affected documents:

- Unless the collection's read rule admits the affected data, no one may receive alt text, keywords,
  identifiers, counts, error reports or any other information about documents or collections —
  whatever operation the request uses, and including results the plugin computed earlier and shares
  between requests. A rule that admits only some documents is applied to each document's own alt
  text, keywords and changes.
- No one may cause alt text or keywords to be written to a document they may not change.
- Collection-wide information follows collection-level read access: a rule that limits a user to
  some of a collection's documents still grants that collection's collection-wide information
  (aggregate counts and the collection-wide identifiers).
- When a request cannot be satisfied without disclosing or changing protected data, it fails with an
  error response and leaves nothing changed. When a response can be limited to the data the user may
  access, it contains only that data.
- Everything that works today keeps working exactly as today for a user who is allowed to read or
  change the documents involved. In particular, generating without saving remains available to a
  user who may read a document but may not change it, and saving remains available to a user who may
  change it. A request that covers several documents still processes every document the user may
  access; a legitimate request that covers many documents still completes; and an authorized user
  still receives complete collection-wide information after another user's request.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
