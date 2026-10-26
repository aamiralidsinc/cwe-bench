# PHP document renderer: an unexpected value type breaks rendering

The project is a PHP library that renders rich-text editor documents — a JSON/array tree of nodes, marks and text — for display. An application accepts documents authored or submitted by its clients, hands one to the library, and renders it.

## Observed impact

A client supplied a document in which a link's address was given as a list of strings instead of a string. Rendering that document raised an uncaught PHP type error, so the request that rendered it never returned. The same document with a string address rendered normally.

## Required property

Rendering a client-supplied document must complete without a PHP type error, whatever type each value in it has. A value that the renderer cannot turn into text is treated as absent: it must not appear in the output, and the rest of the document — including the other values on the same element — must render as it does for a valid document.

## Contracts

- Rendering always returns its output; a crash or an uncaught error is not an acceptable outcome.
- Everything that renders today keeps rendering exactly as it does today.
- The example is one instance. Fix the underlying behaviour for values that reach rendering, not that one input.
- Keep legitimate use working; do not disable features or special-case the example to make the problem disappear.
- Do not look up the upstream fix.
