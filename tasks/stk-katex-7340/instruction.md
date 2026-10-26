# KaTeX emits attacker-chosen links when a page's object prototype is polluted

KaTeX is a JavaScript library that typesets LaTeX in web pages and in server-side rendering. A
page hands it the LaTeX source and a small options object: how the result should be
displayed, whether the input is trusted, and so on. By default the library refuses commands that could emit
active HTML — links (`\href`, `\url`), images and the HTML-attribute commands — unless the page
opts in through its trust option.

## Impact

A page renders visitor-supplied LaTeX with KaTeX and also loads an unrelated library that has a
prototype-pollution bug. A visitor plants `trust: true` on JavaScript's shared object prototype and
then submits

```latex
\href{javascript:alert(document.cookie)}{click me}
```

KaTeX reads the inherited value, treats the input as trusted, and emits a real `<a>` element whose
`href` is the `javascript:` URL, even though the page never enabled trust and never asked for a
link.

## What must hold

Render options must be taken only from the caller's own entries in the object it passes, and, when
the caller omits one, from KaTeX's own built-in default for that option. A value that exists only
on JavaScript's shared object prototype must never change the rendered result.

A macro name may expand only when KaTeX itself defines it or the render currently defines it. A
name that exists only on the shared object prototype is not a definition.

## Contracts

- When an input is refused, the refused effect must not appear in the output: no link, image
  source or HTML attribute derived from it. Refusing by rendering the command as unsupported is
  fine, and a thrown error is fine, as long as nothing was emitted and no side effect occurred.
- Everything that works today keeps working exactly as today.
- The example above is one example, not the full set of ways the problem can show up. Fix the
  problem and its close variants; do not special-case the example.
- Do not look up the upstream fix for this issue.
