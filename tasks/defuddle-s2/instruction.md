# The reader HTML returned for a page can carry executable markup

Defuddle turns a web page into clean reader content: given a page as a parsed document, it returns the article's HTML, title and related metadata so another application can display it in a reader view, an email or a note.

## What happens now

A page whose article header image carries a crafted `alt` value produces returned HTML in which that value's quote closes the attribute. Rendering the returned content therefore runs an event handler that came from the page. For example, a header image with

    alt='screenshot" onerror="alert(1)'

comes back as content containing

    alt="screenshot" onerror="alert(1)"

and the displaying application executes `alert(1)` when it renders that content. The page author controls the value; the person reading the extracted article runs the code.

## What must hold

No value the library obtains while processing a page may become executable markup in the content it returns. For every response, whatever path its content took to reach it, the returned content must not contain:

- an event-handler attribute (any attribute whose name begins with `on`);
- a `srcdoc` attribute;
- a script-capable element (`script`, `object`, `embed`, `applet`, `base`);
- a link or resource address (`href`, `src`, `action`, `formaction`, `xlink:href`) whose value is a script-capable URI (`javascript:` or `data:text/html`), ignoring whitespace and control characters in the value.

The examples above are examples, not the full set of pages, values or content shapes this covers.

## What must keep working

Everything that works today keeps working exactly as today:

- A page is still parsed and its content returned; this is not a refusal or rejection requirement.
- Ordinary text and ordinary attribute values keep their meaning, including `&`, `<`, `>`, quotes and non-ASCII text.
- Media embeds whose address is an ordinary web address stay in the returned content.
- Relative links and resource addresses in extracted content still resolve against the page's address.
- The response's existing metadata (title, site, word count and the rest) keeps its current meaning.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or an advisory for this project.
- Do not special-case the example above.
