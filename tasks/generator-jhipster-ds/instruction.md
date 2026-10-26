# Stored file content types can execute script when a generated application opens them

JHipster generates Spring Boot applications with an Angular, React or Vue client. An entity
field of a binary type stores the uploaded file as base64 data next to a content type that comes
from whoever saved the record. The generated client pages display that field and offer a way to
open the file.

## Observed impact

A record can be saved with a binary field whose stored content type is a document type that
executes script. When a user opens that stored file from the generated application, the file is
presented as a document of the stored type and the saved script runs in the new window, where it
can read the user's session and act as them.

## Required invariant

A content type that arrives from stored data must never cause a generated application to open a
document that can execute script. This holds for every action that opens a stored file, in every
generated client, for any spelling or parameterised form of the stored value, and whichever page
or control starts the action. Only kinds of content that cannot execute script may be shown
inline; everything else must not be rendered as a document.

A stored file that cannot be shown safely must still be delivered: opening it completes without
an error and hands the browser an inert download. Silently dropping the action or failing it is
not acceptable.

## Must keep working

Everything that works today keeps working exactly as today. In particular, opening an image that
was stored with an ordinary raster image type still shows the image inline in the new window, and
opening other files still delivers them. Pages, forms, size labels and the visible values of the
entity fields are unchanged.

The examples above describe the problem, not the full set of affected values, clients or actions.

## Constraints

- Fix the problem and close variants of it; do not special-case the example.
- Keep legitimate use working.
- Do not look up the upstream fix.
