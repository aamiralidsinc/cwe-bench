# Template name resolution leaks files outside the template area

## The system
This project is a Java templating engine together with its integration for a popular
web MVC framework. Applications render pages by asking the engine for a template
**by name**. A template name reaches the engine from several places:

- a web controller returns a logical **view name** (e.g. `home/index`), which the MVC
  integration turns into a template;
- a template refers to another template by name (an embedded/partial reference);
- application code calls the public API directly to load a template by name.

The engine is configured with a **location for templates** (a base directory, a classpath
area, a servlet-context area, or a framework resource location) and a **file extension**
for template files. A name is combined with that configured location and extension and the
resulting resource is read and rendered.

## Observed impact
With a reachable configuration, a single request that carries a crafted template name
causes the server to read and render a file that is **not** a template in the configured
area — for example a configuration or data file elsewhere on the host, or a file whose type
is not the configured template extension. A concrete trigger: an HTTP request handled by a
controller whose view name is derived from the request, where the crafted name resolves the
view to an unintended file; the response then exposes that file's contents.

## Security properties (invariants)
- No template name, however it is spelled, may cause the engine to read or return a resource
  **outside the configured template location**. This includes names that use relative
  traversal to climb out of the location, names that embed their own location or scheme to
  point elsewhere, and names that are otherwise absolute.
- No template name may cause a resource whose real type differs from the configured template
  **extension** to be read — including names that use trailing characters to make the
  resolved location's suffix be ignored when the location is interpreted as a URL (for
  instance a fragment or query delimiter that truncates everything after it).
- These guarantees must hold for **every** way a name enters the engine (view names, embedded
  references, and direct API calls) and for **every** configured backing location
  (filesystem, classpath, servlet context, and framework resources). A name that is refused
  on one path must be refused on all of them.

## Contracts the fix must honour
- **Refusal form.** An out-of-bounds or otherwise unsafe name must be refused with a client
  error and must have no side effect (no file outside the configured area is opened, read, or
  returned). Any clear error is acceptable; there is no single required status or exception
  type.
- **Legitimate use must keep working, exactly as today:**
  - ordinary and **nested** names load normally (e.g. `home/index` loads the template at
    that relative position under the configured location);
  - a configured template location that is itself written with a scheme/prefix (such as a
    classpath- or file-qualified base location) must keep resolving its templates — the fix
    must not reject legitimate names or locations merely because they contain a `:` or `/`;
  - a missing template still reports "not found" as before.
- A legitimate nested name (two or three path segments) is normal; the attack magnitude is a
  name of comparable length that nonetheless points outside the configured area.

## Constraints
- Fix the problem and its close variants, not only the specific example above; the examples
  are illustrations, not the full set of inputs to handle.
- Keep every legitimate use working.
- Do not modify or add tests, and do not special-case the example inputs.
- Do not look up the upstream fix for this issue.
