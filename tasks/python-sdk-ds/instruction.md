# MCP servers: one client can read and control another client's tasks

The Model Context Protocol Python SDK lets a server run a tool call as a background *task*: the
client gets a task identifier back immediately and later reads the task's status with `tasks/get`,
collects its payload with `tasks/result`, enumerates its tasks with `tasks/list`, or cancels one
with `tasks/cancel`. One server process usually serves many clients at once over a single shared
task store.

## Observed

Two clients are connected to the same server. Client A starts a tool call as a task. Client B
sends `tasks/get` with the identifier A was given and receives A's task status and progress; B
then asks for that task's result and is handed A's payload.

## What must hold

A client session may use only the tasks that its own session created. No message a session
receives — the response to a request or a notification — may reveal the existence, identifier,
status, messages or result of a task created by another session, and no request from a session may
change or remove a task created by another session.

## Contracts

- A request that must not be served fails as a normal client error response — an error code, not
  an internal failure — leaves the target task exactly as it was, and leaves the caller's
  connection serving its own work.
- No part of a response may identify a task the caller did not create.
- Everything that works today keeps working exactly as today for the tasks a session created: a
  session keeps full use of its own tasks however many it has, including listings that span more
  than one page — a client with dozens of tasks must still see all of them.
- A task the application creates without tying it to a client session — an identifier the
  application chose itself, or a deployment in which a session does not survive to the next
  request — stays usable by any client that presents that exact identifier, and is never
  enumerated to anyone.

The behaviour described above is an example, not the full set: the same rule applies to every
operation over a task, whatever it is called and whichever client sends it.

## Constraints

- Fix the problem and its close variants. Do not special-case the example.
- Keep legitimate use working exactly as it does today.
- Do not look up the upstream fix or an existing implementation of it. There is no network access.
