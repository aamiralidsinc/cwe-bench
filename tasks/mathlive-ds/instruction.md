# Math rendering turns text content into live markup

MathLive renders LaTeX math into output that applications place into a web page. Applications
often render LaTeX they did not write themselves: formulas submitted by users, imported from
documents, or pasted into an editor.

Rendering the input `\text{<img src=x onerror=alert(1)>}` with the library's public conversion
function `convertLatexToMarkup()` returns output in which the tag is a live element. When that
output is inserted into a page, the script runs. The input above is one example, not the full set
of inputs or outputs affected.

## What must be true

No character taken from the LaTeX being rendered may be interpreted as markup by anything that
consumes the library's output. Every output the library produces must carry those characters as
inert text: they display exactly as written, and a literal ampersand or angle bracket stays a
visible character rather than starting or forming a tag. This applies to
text that the author writes and to characters that the author writes as delimiters.

Everything that renders today must keep rendering the same way. In particular, symbols and
characters selected by name or by numeric code must keep producing the same visible character,
and text values must keep displaying exactly the characters that were written.

## Constraints

- Fix the reported problem and its close variants; do not stop at the one input above.
- Keep legitimate use working. A fix that changes which character a legitimate formula displays
  is not acceptable.
- Do not look up the upstream fix for this issue.
- Do not special-case the example input or a fixed set of spellings.
