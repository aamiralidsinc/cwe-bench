# Users can save links and rich text that run script in other users' browsers

## The system
This repository is a conference-management web application. People with management rights
enter links and rich text in several parts of the product, and the content they save is later
shown to visitors and to co-editors. Some of it is rendered into pages; some is handed to the
browser as JSON for the in-page editors.

## Observed impact
A user who may attach a link to an event's materials can save a target such as
`javascript:alert(1)`. The product keeps it and later offers it as a link, so opening it runs
that script in the browser of whoever follows the link. Separately, minutes text saved by one
editor can carry an image with an `onerror` attribute; when a co-editor fetches the stored
minutes, the markup arrives with the content and the script runs in their browser.

## What must hold
**Link targets.** A link target supplied by a user must never be one that executes code when
opened. A target using a code-executing scheme (for example `javascript:`) must not be kept or
handed back to any client - whichever part of the product receives, stores or returns it, and
whether it is a single value or one item among several. Ordinary `http` and `https` addresses
must keep working exactly as today.

**Stored rich text.** Rich text saved by one user must never be handed to another user, or to
any client, with markup that can execute. Script elements, event-handler attributes and
code-executing link targets must be gone from what is delivered, while ordinary formatting,
images and links are kept. The author's own raw text must still be returned exactly as written,
so that reopening it for editing loses nothing.

The two examples show how the problem appears; they are not the full set of places, inputs or
forms.

## Contracts the fix must honour
- **Refusal.** When a submission is not acceptable, nothing is saved and an existing value stays
  as it was. A normal validation failure, a re-shown form or a client error are all acceptable;
  a server error is not, and a submission must never be applied only in part.
- **Preservation.** Everything that works today keeps working exactly as today: ordinary
  `http`/`https` links are accepted and stored wherever they are accepted today, including a
  single link and a list of several links with their titles; legitimate rich text keeps its
  formatting, images and links; the raw authored text round-trips unchanged; and content that
  was already stored safely is delivered unchanged.

## Constraints
- Fix the problem and its close variants, not just the exact examples above.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
