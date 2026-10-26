# Includes must stay inside the project's partials directory

## System

MJML compiles `.mjml` email templates into responsive HTML. A template can pull in a reusable
partial with `<mj-include path="..."/>`. The same documents are processed by the library API and by
the command-line tool.

## Observed impact

A document that is processed on behalf of an untrusted author can name a partial anywhere on the
machine. That file is read and its content is compiled into the email; nothing restricts the name
to the project the template belongs to.

## Security properties

1. **Include confinement.** No file outside the include base is ever read while a document is
   processed, and nothing taken from such a file may reach a result the product produces or a
   dependency set it maintains. This holds however the target is written and at every depth of
   nesting.

2. **No filesystem locations in diagnostics.** When an include cannot be read or is refused,
   everything the product reports names the target only as the template wrote it. No resolved
   filesystem location of the target or of the including document may appear in compiled output,
   in reports, or in command-line output.

## The include base

- When a partials directory is configured, that directory is the include base. A configured value
  that names a file contributes its directory.
- Otherwise, when the document being processed has a path, that document's directory is the base.
- Otherwise the working directory is the base.
- A partial may still reach another file inside the base, including one above its own directory;
  only targets outside the base are refused.

## Contracts

- **Refusal.** A refused include is reported as an ordinary document or validation error. The run
  does not crash, no content from the target appears anywhere, and the target is not read.
- **Preservation.** Everything that works today keeps working: includes inside the base render;
  nesting resolves relative to the including partial; a configured partials directory takes
  precedence over the document's own directory; a partial with any extension keeps working; a link
  that stays inside the base keeps working; an unreadable include inside the base is still reported
  with the target as written and the enclosing line; an option that skips include processing still
  leaves the filesystem untouched; and a change to a partial inside the base still leads to the
  documents that depend on it being rebuilt.
- **Examples are examples.** The cases above are illustrations, not the full set.

## Constraints

- Fix the flaw and its close variants, not just the example shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
