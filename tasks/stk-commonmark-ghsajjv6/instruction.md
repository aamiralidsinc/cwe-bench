# Conversion time grows quadratically on adversarial Markdown

The library converts Markdown documents to HTML. Applications embed it to render user-submitted
Markdown.

Conversion must cost time roughly proportional to the document's size. Today it does not: a
1.2 MB document made of short text runs separated by lone double quotes takes seconds to convert
with the smart-punctuation extension enabled, while the same document converts in a fraction of a
second without it. The gap widens sharply as the document grows. An attacker can post a document
of that shape and occupy a PHP worker, denying service to legitimate users.

## Required property

For every document, the time spent converting it must stay proportional to its length: repeating
a markup construct many times must not make each repetition cost more than the one before it. This
holds however the document is composed.

## Contracts

- Every document that converts successfully today must keep converting to exactly the same HTML
  output.
- Every legitimate document must keep converting, including documents of several megabytes;
  nothing may be refused, truncated or capped.
- The public converter API keeps its current signatures and behaviour.
- The example above is an example, not the complete set.

## Constraints

- Fix the problem and its close variants, not only the example trigger.
- Keep every legitimate use working.
- Do not look up the upstream fix.
- Do not special-case the example values.
