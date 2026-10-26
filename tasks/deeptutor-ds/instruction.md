# Ordinary accounts can use MCP tools they were never assigned

DeepTutor is a self-hosted AI learning workspace. An administrator can connect MCP
servers to the deployment, which publishes their tools to the assistant. Administrators
can also assign individual accounts a list of tools they may use, and an account that
has not been assigned a tool is meant to have no access to it.

We observed an ordinary signed-in account, with no tools assigned to it, use a
deployment-wide MCP tool from an ordinary conversation: the assistant offered the tool
and, when the turn asked for it, the tool ran and carried out its action on the
connected server.

The rule we need is:

> An ordinary (non-administrator) account must never be able to see, load, or run an MCP
> tool unless an administrator has explicitly assigned that tool to the account. This
> holds for every feature and request path that can reach such a tool, however the tool
> is named or requested, and for tools a conversation made available earlier. A request
> that is not allowed is refused with a client-visible error and performs no part of the
> tool's work.

Administrators keep unrestricted access. An account with an explicit list of assigned
tools keeps exactly those tools and nothing else. A chat partner keeps the tool set its
owner configured, including the default it has today when no list was configured, on
that partner's own turns, without an administrator assignment. Tools that are not
MCP-backed keep working as they do today.

The example above is an example, not the full set. Fix the problem and its close
variants; keep legitimate use working; do not look up an upstream fix; do not
special-case the example.
