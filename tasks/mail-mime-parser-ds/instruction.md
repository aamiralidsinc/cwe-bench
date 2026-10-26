# No value from outside the library may add a line to a message it writes

## The system

This project is a PHP library for MIME email messages. An application uses it in two directions.

When the application **composes** a message, it supplies the values that appear in it: it sets
the subject, sets the text or HTML body and the character set to declare for it, attaches files
under names that often come from an end user, embeds an inline image, renames an existing
attachment, and marks a message as signed with the signing details it chooses.

When the application **reads** a message, the library parses and decodes headers and returns the
resulting values: the subject, an attachment's file name, and the parameters of a header,
including values the message does not write out plainly.

Both directions feed the same pipeline: values that come from outside the library enter it and are
placed into the text of a message the library writes, or handed back to the application.

## Observed problem

An application attaches a file to an outgoing message and passes, as the attachment's name, a name
supplied by its user. The name contains a line break followed by a line that looks like an email
header. The library places the name into the message it writes without changing it, so the message
the application receives contains that line as a real header addressed to someone the application
never named: one supplied value has become two headers. Reading a message back shows the same
problem from the other side — a value decoded from an incoming message comes back to the
application with a line break still in it.

## Security property (invariant)

No value that comes from outside the library — a value the application supplies while composing a
message, or a header or parameter value the library decodes from a message it reads — may carry a
line break into the text the library produces. Every such value must be made safe before it is
used: a value placed into a header, or into any other line of a message the library writes, keeps
that line on one line and adds no header or other line, and a decoded header or parameter value
handed back to the application contains no line break. The property covers every public way the
product composes a message and every header or parameter value the product decodes from a message,
however that message spells the value.

When a value cannot be made safe, the operation may refuse with an error instead of writing it; a
refusal must not leave the unsafe value in the message. An operation must not refuse a value that
contains no line break.

## Keep working

Everything that works today keeps working exactly as today, including:

- attaching a file, embedding an inline image, renaming an attachment, setting the body, and
  signing a message with ordinary values;
- non-ASCII attachment names, which are still transliterated to ASCII;
- values decoded from ordinary messages, which still decode to exactly the same text, including
  non-ASCII text and values spread over more than one line;
- the headers the library writes, which keep their existing layout and folding.

These are examples of ordinary use, not the full set.

## Constraints

- Fix the underlying problem and its close variants, not just the exact example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
