# Sanitized output can still contain disallowed markup

jsoup is a Java library for parsing real-world HTML. Its HTML sanitizer — the `clean` and `isValid`
methods on `Jsoup`, and the `Cleaner` class used with a `Safelist` — is the standard way applications
strip untrusted markup from user-submitted content before storing or displaying it.

We found that a document which should be reduced to a few safe elements instead comes out of the
sanitizer carrying live markup that the safelist never allowed. With a safelist configured like
`Safelist.relaxed()` plus `iframe` (it permits iframes and ordinary text tags, but not SVG):

Input:

```
<iframe\u001E></iframe><svg onload=alert(1)>
```

`Jsoup.clean(input, safelist)` returns:

```
<iframe></iframe><svg onload=alert(1)></iframe>
```

The `svg` element was never allowed, yet a browser reading the sanitized result will run its handler.

## The property

Sanitization must be sound: the result may contain only elements, attributes, and element text that
the configured safelist permits. No markup a submitter supplies may survive sanitization as an
element, an attribute, or unescaped element content unless the safelist allows that element and
attribute — whatever the tag is called, however it is written, and wherever it appears in the
document. Content that is not allowed is dropped; it must never be passed through in a form that a
browser would re-interpret as markup.

## Contracts

- `clean` returns the sanitized markup and `isValid` returns a boolean, as today. The property is
  about what the returned markup contains; disallowed content must simply be absent from it.
- Everything allowed today keeps working exactly as today: permitted elements and attributes are
  kept, URL filtering is unchanged, and an allowed element's own content is still copied verbatim —
  including elements whose content jsoup treats as opaque text.
- Public tag and tag-set lookup APIs keep their current behaviour for user-supplied names:
  surrounding whitespace and letter case are handled exactly as they are today.
- The example above is one illustration, not the complete set of affected inputs.

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
advisory or fix, and do not special-case the example.
