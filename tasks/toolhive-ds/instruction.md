# A locally run MCP server can reach host services by default

ToolHive runs MCP servers as local containers. A server container is meant to sit on its own
network with a controlled egress path. When it is not isolated, it shares the host's network and
can reach services listening on the host, including the container gateway.

## What happens

A user starts a server with the default options and says nothing about network isolation. The
server comes up on the host network instead of the isolated one. A process inside that server's
container can then open a connection to a service bound to the host and reach it.

For example, running a server with the default options and connecting from inside that server's
container to a service listening on the host succeeds, where it should have been refused.

## What must be true

Every MCP server that ToolHive runs as a local container must be on a network isolated from the
host. Isolation may be turned off only when the person starting that server explicitly asks, for
that server, that it run without isolation: a start request that does not mention isolation is
isolated, and one that explicitly disables it is not.

This holds however the server is started and whatever definition supplies its settings, including
a definition that was saved earlier and started again. If a definition does not mention the
setting, the server is isolated; if it explicitly disables the setting, that choice is honoured.

## What must keep working

Everything that works today keeps working exactly as today. In particular, servers still start
with the same names, images, transports, ports, environment, volumes and arguments; an explicit
request to run a server without isolation is still honoured; and a server keeps the isolation
setting it already has when its version changes.

The example above is an example, not the full set of cases.

## Constraints

- Fix the problem and its close variants; do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up the upstream fix or advisory.
