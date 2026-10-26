# Untrusted CSS and source-map references

This project is a CSS processor. Applications give it a stylesheet and, optionally, a file path
for that stylesheet, transformers to run, and source-map options; it returns the transformed CSS
and, when asked, a source map. The stylesheet may come from an untrusted source.

A stylesheet can carry an annotation comment that names a previous source map. When the processor
follows such a reference supplied with untrusted CSS, it can be made to read a local file the
caller never chose. For example, processing a stylesheet whose annotation names a file outside the
stylesheet's own folder makes the processor read that file; its contents can then appear in the
generated source map or in the exception text.

## Required property

CSS input is untrusted. A source-map reference supplied with untrusted CSS must only select a file
inside the folder that contains the stylesheet (or inside the working directory when the stylesheet
has no file), and only when it is written as a genuine source-map annotation comment. It must never
make the processor read any other file, and the contents of a file the processor reads must never
appear in an error or in the output. Such a reference must also not survive into the CSS the
processor emits, unless the caller explicitly asked to keep it.

## Behaviour that must not change

Everything that works correctly today keeps working exactly as today.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example above.
