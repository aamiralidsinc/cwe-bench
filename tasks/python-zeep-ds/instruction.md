# A description read by the SOAP client can make it contact arbitrary hosts

## System

python-zeep is a SOAP client library for Python. An application gives `Client`
a service description (a WSDL document) — a URL, a local file, or a file object
— and zeep reads that document and everything it refers to in order to build
the callable service. Real descriptions are often assembled from several
documents: one names others, and those name more.

## Observed impact

An application that reads a description from a source it does not fully control
can be made to send HTTP requests to hosts it never intended to contact.
For example:

```python
from zeep import Client, Settings

client = Client(
    "https://vendor.example/service.wsdl",
    settings=Settings(forbid_external=True),
)
```

If the document served at `service.wsdl` names `http://10.0.0.5/admin` as a
further document to read, zeep issues a request to `http://10.0.0.5/admin` even
though external-reference protection is enabled. The application only ever
asked for `vendor.example`.

## Security property that must hold

When an application enables the external-reference protection, reading a
description must contact only the location the application itself supplied.
No value that appears inside any document zeep reads — at any depth, in
whatever form it is written, and whichever host it names — may cause an
additional network request. This holds for every public interface the library
offers for reading a description, not only the common client path.

## Contracts the fix must honor

- **Refusal.** A refused reference makes the operation fail with a library
  error, and the refused location is never contacted.
- **Switch.** The protection is the existing `forbid_external` option on
  `Settings`; applications enable it as shown above.
- **Transport independence.** The protection must hold whichever HTTP transport
  the application supplied, including a custom one.
- **Preservation.** Everything that works today keeps working exactly as today.
  Applications that use today's configuration (no explicit external-reference
  option) keep reading descriptions that span several network documents, and an
  application that enables the protection still receives the description it
  itself named from the location it named.
- **Scope of the rule.** An additional location is covered whether it is
  written as an absolute address, as a path relative to another document, or in
  another form, and whether or not it is on the same host as the supplied
  description.

The example above is one instance, not the full set of ways the property can be
violated.

## Constraints

- Fix the flaw and its close variants, not just the example shown.
- Keep every legitimate use working.
- Do not special-case the example input.
- Do not consult any upstream advisory or fix for this issue.
- There is no network access.
