# Workflow-supplied values must never become local-file or remote-address content

n8n is a workflow automation platform. A workflow is a graph of nodes, and node
parameters can be filled from expressions at run time, so a value that is text in the
editor can arrive as a different type when the workflow executes, including a value
chosen by whoever can supply data to the workflow.

## Observed impact

Such a value can make the product read a file on the host, or fetch a remote address,
and deliver what it finds to the recipient as part of the outgoing email. The caller
needs no account on the n8n instance; they only need to be able to supply the value.

## Required property

No workflow-supplied value may cause the product to read a local file or fetch a remote
address and use what it finds as the content of an outgoing email, in any part of that
email. This holds however the value is supplied, for every capability that builds an
email from workflow values, and whether or not the value was meant to be text.

A value that is not text must be delivered as text: a composite value as its JSON text,
and numbers and booleans in their ordinary text form. It must not be interpreted as a
reference to anything, silently dropped, or cause the item to fail.

If a value cannot be rendered safely, the step may fail the item with the product's
normal node error, but nothing read from a file or a remote address may be sent.

## Preservation

Legitimate use is unchanged. Ordinary messages of a few kilobytes are delivered exactly
as written, with or without the attribution line the product adds by default. Everything
else that works today also keeps working.

This description is not the full set of affected values.

## Constraints

- Fix the reported problem and its close variants; do not special-case the example.
- Keep every legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix or advisory.
- Keep the change inside this repository.
