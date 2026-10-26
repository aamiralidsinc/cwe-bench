# Preview output treats untrusted values as markup

## The system
This repository is a markdown editor component library for Vue 3. Its preview renders a markdown
document to HTML and keeps that HTML up to date as the document or the preview's settings change.
Integrations use it to show documents written by other people, so the document is untrusted. The
preview also displays text and settings that the host application supplies: display labels, the
feedback it reports after an action, and the identifier the application gives each editor instance.

## Observed impact
A document containing a fenced code block whose metadata is crafted makes the preview produce live
markup instead of a code block: the crafted text becomes an element of the page, so content a
document author controls is interpreted by the browser with the privileges of the page that shows
the preview instead of being displayed. A harmless way to observe it: render a fence whose info
string carries markup and see that markup appear as an element of the preview rather than as part
of the language name.

## What must hold (invariant)
Every value the preview puts into the output it produces stays inert for the position it occupies:

- a value taken from the rendered document, from any part of its syntax;
- a value the host application supplies: display text, feedback about an action, and the identifier
  of an editor instance;
- a value the preview writes again later, after an interaction or a re-render.

No such value may add, close or change an element, an attribute, a style or a script in the
preview, and none may run as code — whether it lands in element text, in a quoted or unquoted
attribute, or inside a script-valued attribute. Encoding has to suit the position: text that is
safe in one position is not automatically safe in another, and an identifier that looks harmless in
an attribute is not automatically harmless in a script expression. The guarantee holds at whatever
moment the preview writes the value, including when it rewrites it later in response to an
interaction.

Markup the preview itself produces is not restricted by this and must keep working: highlighted
code keeps its highlighting markup, and content the preview can only show unformatted keeps being
shown, as its source text.

The examples above are examples, not the full set; reason about the property, not the samples.

## Contracts the fix must honour
- **No partial activation.** A value that would violate the invariant must not take effect: it is
  shown as text or omitted, never activated. Rendering and interacting must not throw.
- **Preservation (works exactly as today).** Every construct the preview supports keeps rendering,
  and every value it shows keeps being shown:
  - language names keep working even when they are made of punctuation (`c++`, `c#`), and the
    syntax highlighter still receives them;
  - a configured display label and a configured display asset (an icon, rendered as markup) keep
    their places and their behavior;
  - two editor instances stay independent.
- **Interfaces.** The preview renders the markdown it is given and accepts per-instance settings:
  a display language, display texts, an instance identifier, and an optional display asset. The
  guarantee above applies to each of them.

## Constraints
- Fix the problem and its close variants, not just the exact sample.
- Keep every legitimate use working.
- Do not look up the upstream fix for this issue.
- Do not special-case the example inputs.
