# Security report: layout configuration can load code

Craft CMS lets administrators define content models and their field layouts. A field layout is
saved as structured data: a list of tabs, and inside each tab the UI elements that make it up.

A user who can save a field layout can add an extra entry to the layout definition that names a
class. When the platform builds the layout, that class is instantiated and attached to the
resulting object, even though the layout editor never offers that.

Example: an administrator saves the entry-type field layout for a section and includes an extra
behavior entry in the layout definition. The layout saves normally, and the named class runs on
the server.

## The property

No configuration data supplied to the platform may cause it to attach a behavior or register an
event handler that the configuration names. Configuration may select the supported types and set
their supported settings; it must not name classes to attach or events to hook, however that data
reaches the platform.

A request that carries unsupported wiring may be refused with a client error, or the unsupported
wiring may be ignored; either way nothing named in the configuration is attached, loaded or run.

## Contracts

- A request that carries unsupported wiring has no effect beyond an ordinary save.
- Everything that works today keeps working exactly as today.
- The example above is an example, not the full set of forms or sources.

## Constraints

Fix the problem and its close variants. Keep legitimate use working. Do not look up the upstream
fix. Do not special-case the example.

There is no network access.
