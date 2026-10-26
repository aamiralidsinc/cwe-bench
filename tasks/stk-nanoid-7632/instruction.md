# An ID request with an unusable length must not block

nanoid is a small JavaScript library that mints short, random, URL-friendly IDs. Applications use
it, and the custom generators it builds from a caller-supplied alphabet, to create identifiers for
URLs, tokens, filenames and database rows, so a single call that never returns stops the process
that made it.

Report: a custom generator created with a size of zero spins forever.

    const gen = customAlphabet('0123456789', 0)
    gen()

The call above never returns and the process has to be killed.

## The property

Every request to generate an ID must return. When the length asked for cannot be produced, the
call must return the empty string rather than blocking or handing back a partial ID.

Everything that works today keeps working exactly as today.

The example above is one example, not the full set.

## Constraints

- Fix the reported problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or the advisory.
- Do not special-case the example.
