# A refused deletion destroys the image data anyway

Glance is an image service: it stores virtual machine images, each of which has an
owner, and an image can be marked protected.

A signed-in user who can merely see another user's image (a public image) can ask
the service to delete it. The request comes back refused, but by then the image's
stored data has already been removed, while the record still describes the image
as present.

## Requirement

Only the image's owner or an administrator may delete or modify an image, or any of
the data the service stores for it. Being able to see an image never grants that.

While an image is marked protected, it must never be deleted, in whole or in part.

These are invariants over the protected data and outcome. The example above is one
example.

## Contracts

- A refusal is a client error and leaves everything exactly as it was.
- Everything that works today keeps working.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look
up the upstream fix. Do not special-case the example above.
