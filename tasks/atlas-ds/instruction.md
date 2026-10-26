# User-authored metadata must not become live markup in the Atlas web UI

Apache Atlas is a metadata catalog. People describe entities with attribute values, business-metadata
values and rich-text descriptions, and other people read those pages in the product's web interface.

## What happens

A user who may edit an entity stores a value such as

`<img src=x onerror="alert(document.cookie)">`

in a business-metadata text attribute (for example with
`POST /api/atlas/v2/entity/guid/{guid}/businessmetadata`). When another user opens that entity's
Properties tab, the value is inserted into the page as HTML and runs in the second user's session.

## Security property

No value that a user authors or supplies — an entity attribute value, a business-metadata value
(including a list of values), a description, a name shown for a stored object, or the account name
the server reports — may become executable markup when any part of the product displays it, whether
the value was stored earlier or carried in the address of a page.

A display that already renders formatted text keeps rendering its supported formatting — paragraphs,
headings, emphasis, underline, lists, and `http`, `https` and `mailto` links — and may not introduce
elements, attributes, event handlers or link schemes outside that set. Every other value is shown as
inert text.

Nothing else changes: plain values display the same text as today, lists keep their current joining,
numbers and dates keep their current presentation, and a value is never dropped, truncated differently
or made unreadable because it contains markup.

These examples are examples, not the full set.

## Constraints

- Fix the problem and its close variants; do not special-case the example above.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- There is no network access.
