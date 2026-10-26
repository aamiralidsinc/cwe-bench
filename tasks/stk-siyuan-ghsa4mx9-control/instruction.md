# SVG documents returned by the kernel can run script

SiYuan is a personal knowledge-management application. Its desktop window and browser tabs talk to
a local HTTP kernel, which returns small SVG images to clients. An SVG document opened as an image
is still a document: markup inside it can run script in the kernel's origin.

For example, a request to `/api/icon/getDynamicIcon?type=8` whose text value contains a script URL
returns a document that still carries the URL, and opening the returned image runs the supplied
code with the kernel's privileges.

## Required properties

While the SVG-script setting is off, no SVG document the kernel returns to a client may carry
executable content: it may not run script, and it may not embed or inline-load another document's
active content into the page. Ordinary navigation links and raster images stay as they are.

Text a caller supplies to the icon API is content, never markup: no value of it may become
executable content in the returned document.

A response that would violate this may be refused, but a refusal is a client error, with no
effect. These are invariants, not a list of cases. The example above is one illustration.

## Behaviour that must not change

- Everything that works today keeps working: a legitimate SVG that carries no executable content
  keeps its content intact, and text icons keep displaying their text.
- When the SVG-script setting is on, documents are returned exactly as stored.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
