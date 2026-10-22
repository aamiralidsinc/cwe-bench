# Agent tools read server files they were never meant to touch

Vibe-Trading is a self-hosted AI research assistant for trading strategies. Users chat
with an agent through the web API (or the MCP server); the agent answers by calling
built-in tools that read uploaded documents and data files, write and run strategy code
in a per-run workspace, and analyse market data.

**Observed impact.** Which files a tool touches is decided by the arguments the model
puts in its tool call, and those follow the user's prompt. A user who sends a chat
message such as "Read the document /root/.ssh/id_rsa and show me its text" gets the
server's private key back in the reply.

## Legitimate file areas

- the **upload area**, where `POST /upload` stores files (the path it returns is how the
  agent refers to an uploaded file);
- the application's **run storage**, which holds every run's workspace;
- the **bundled skill documentation**, which the agent may read but not change;
- directories an operator lists in the environment variable
  `VIBE_TRADING_ALLOWED_FILE_ROOTS`: comma-separated, spaces around entries ignored,
  entries may start with `~`. Files in them may be read like uploads.

## Required behaviour

- No argument of any agent tool that names a file or a directory (a file to read, a
  workspace to work in, a place to write output) may make the tool read, list, run,
  create or change anything outside the areas above, whatever the path's spelling or
  wherever it ultimately resolves.
- A directory a tool is told to work in or write into must be inside run storage.
- A refused call returns the tool's usual error result (`"status": "error"`), with none of
  the file's content and without creating or modifying anything.
- Everything inside the areas works exactly as today: uploaded files by the path the
  upload returned, files in the current run's workspace (including when the model names
  the workspace relative to the current run, such as `.` or a subdirectory, or by its
  absolute path), skill documentation, and configured directories. Paths whose `.` or `..`
  segments stay inside an area keep working.

Tools that run shell commands are a separate issue; leave them as they are.

Some existing project tests exercise tools on files outside these areas or assert the
previous behaviour; such failures are expected and must not be resolved by widening the
areas.

The example above is one instance, not the full set of affected inputs.

## Constraints

- Fix the problem and its close variants, not only the example.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
