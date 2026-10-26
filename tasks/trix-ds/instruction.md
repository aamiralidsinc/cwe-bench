# A stored document can make the editor run a link's script

## The system
This repository is a browser rich-text editor that applications embed in their pages. A document is
a tree of blocks, formatted text and attachments. Applications hand documents to the editor — for
example when restoring content that a user saved earlier — and users move content into the editor by
dropping or pasting it from other pages and applications. The editor keeps documents in its own
serialised form and renders them into the live page, where links, formatted text and attachments
become real elements.

Document content is untrusted. It can be written by anyone who can save, copy, share or send a
document, and the application that renders it need not be the one that produced it.

## Observed impact
A user opens a document that an attacker prepared, or drops one into the editor. Among its content
is a link whose destination is not a web address but a script URL (for example a `javascript:`
address). The editor renders it as an ordinary clickable link; when the user follows it, the
attacker's script runs in the editor's page with that page's privileges and can read or change the
document and the surrounding application.

## What must hold
For any document the editor accepts, from any of its entry points:

- No value carried by the document may become the destination of a rendered link if following that
  destination would run code. This holds for every spelling and for every value shape the document
  format allows, wherever in the document the value sits.
- Every destination that is legitimately a link — web addresses, mail addresses and relative
  addresses — keeps rendering as a link, with the same visible text and the same other formatting.
- Refusing a destination is an ordinary negative result: the destination is simply not applied, the
  page does not raise an error, and the rest of the document still renders.
- Everything else a document carries keeps working exactly as it does today: other text and block
  formatting, attachment captions and presentation, and attachment content.

The addresses, value shapes and element kinds above are examples of how the flaw can show up, not an
exhaustive list; reason about the property, not the samples.

## Constraints
- Fix the problem and its close variants, not just the exact sample described above.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
