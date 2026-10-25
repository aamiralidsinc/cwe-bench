# Script removal can leave executable content in optimised SVG

This project is a Node.js library and command-line tool that optimises SVG documents. It is also
used as a sanitiser: with its script-removal option enabled, it is expected to return a document
that is safe to serve to a browser, even when the input comes from an untrusted user.

## Observed impact

Running the optimiser with script removal enabled over the document below still returns output
that contains the embedded `srcdoc` payload. A browser that renders the optimised file executes
the attacker's script.

```svg
<svg xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="200" height="200">
    <iframe srcdoc="&lt;script&gt;alert(document.domain)&lt;/script&gt;"></iframe>
  </foreignObject>
</svg>
```

## Required security property

When script removal is enabled, the optimised document must not cause a browser to execute code
when it renders it. For every element and attribute the browser acts on - however it is named,
spelled, or nested - the output must contain:

- no executable code, whether bound to an element or carried in an element;
- no embedded active document; and
- no executable URL in an attribute.

Hostile input must still produce output: dangerous content must be removed, not rejected. The
optimiser must not throw, abort, or fail merely because the input contains it.

## What must keep working

Everything that cannot execute must behave exactly as it does today:

- embedded HTML that is visual or inert keeps its elements, text, styles, classes, titles and
  ordinary links;
- a link whose URL cannot run code keeps working and keeps its element;
- values that describe appearance, geometry or layout keep their spelling and their values;
- elements and attributes that belong to other vocabularies are not acted on as part of the
  document and keep their content.

The example above is one form of the problem, not the complete set.

## Constraints

- Fix the reported problem and the other forms the same property covers.
- Keep all existing legitimate behaviour working.
- Do not look up the upstream fix or the advisory for this problem.
- Do not special-case the example.
