# URL scheme policy bypass in the HTML sanitizer

## The system

The project ships an HTML sanitizer used as a library by content-driven applications. Callers pass untrusted HTML and a configuration object, and receive back HTML that is safe to store and render. The configuration selects the elements and attributes that may be kept, and sets the URL scheme policy that destinations must satisfy.

## Observed impact

A document submitted by an untrusted author can keep a link destination whose scheme the configuration forbids, while the sanitizer reports success and cleans the surrounding markup. With a configuration that allows the SVG elements `svg`, `a`, `text` and `animate` together with their attributes, this input:

```html
<svg><a><animate attributeName="href" values="#safe;javascript:alert(1)"
  dur="0.01s" fill="freeze"></animate><text>Click me</text></a></svg>
```

comes back with the `javascript:` destination still present, so the rendered link can be made to navigate to it when the animation runs.

## The guarantee

Whatever the input, the output must not contain a URL whose scheme the configuration does not permit for the element it is emitted on — whether that URL is an attribute value, one of several destinations inside a list value, or a destination that the browser derives, copies or loads after sanitization. Every destination is judged on its own. Where the configuration names a per-element scheme list, that list is the complete policy for that element; the global list does not widen it.

## Contracts

- The entry point takes the untrusted HTML and the options object and returns the sanitized HTML string. It must return normally for every input. A rejected value or element is left out of the output (or escaped in escape mode) the same way any other disallowed content is, and the rest of the document is sanitized as usual.
- The policy options are `allowedSchemes` (schemes permitted overall), `allowedSchemesByTag` (per-element lists), `allowedSchemesAppliedToAttributes` (the attributes whose values the policy covers) and `allowProtocolRelative`. `allowedTags` and `allowedAttributes` select what may be kept. The documented defaults apply when an option is omitted.
- Everything the configuration permits must keep working exactly as today: permitted-scheme and relative URLs, values that are not destinations, and several separate URLs in one document.

## Constraints

Fix the reported problem and its close variants rather than the one example; do not weaken the allowlists or remove features to make the example disappear; do not look up the upstream fix; do not special-case the example. The example is an example, not the full set.
