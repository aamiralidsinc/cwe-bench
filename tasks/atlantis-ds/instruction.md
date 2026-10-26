# Keep pull-request workspace data inside its own directory

## The system

This project is a server that runs Terraform for a team's pull requests. It
keeps a data directory on disk: for each pull request it allocates a directory
there, and inside that directory it keeps one checkout per Terraform workspace.
A project's files live in a subdirectory of its workspace's checkout. The
server allocates these directories, keeps them in step with the work it is
doing, and removes them when they are no longer needed.

The values that name those locations arrive from several directions: the
repository identity and workspace carried with pull-request events and
comments, the project entries in the repository's own configuration, the
project paths a client supplies to the plan and apply API, and state the server
stored while handling an earlier request.

## Observed problem

A client calls the plan API for a pull request and supplies a workspace name
that walks upward out of that pull request's directory. The server accepts the
request, prepares the workspace, and in doing so removes and re-creates a
directory belonging to a different pull request. The affected directory is
outside everything that request should have been able to touch.

## Security property (invariant)

No repository identity, workspace name, project name, or project directory
that a client supplies -- in a request, in the repository's own configuration,
or in state the server stored during an earlier operation -- may cause the
server to create, modify or delete anything outside the directory the server
allocated at that level. A repository identity must stay inside the server's
managed data area; a workspace must stay inside its pull request's directory;
a project name or project directory must stay inside that project's workspace
directory. This holds however the value is spelled and at every point while a
request is being handled.

When a supplied value would resolve outside the directory allocated at its
level, the server must not act on it: the requested operation fails with an
error and nothing outside is created, changed or deleted. No other file-system
work that the server performs may reach such a location either.

## Keep working

Everything that works today keeps working exactly as today. In particular:

- repository identities whose owner has several path components (hosts that
  use subgroups or multi-part owners) still resolve and clean up;
- the default project directory is the root of the workspace checkout, and
  nested project directories such as `modules/vpc` are ordinary;
- ordinary workspace names, including hyphenated ones, still work;
- deleting a saved plan for a normal project still removes the saved file;
- preparing and running an ordinary plan for an ordinary project still
  succeeds.

For example, a project in `modules/vpc` in workspace `default` is ordinary and
must keep working; a workspace or project path that walks upward out of its
own directory is the case that must be refused. These are examples, not the
full set of inputs.

## Constraints

- Fix the underlying problem and its close variants, not just the example.
- Keep every legitimate use working.
- Do not special-case the example inputs.
- Do not consult any upstream fix, advisory, or changelog for this project.
