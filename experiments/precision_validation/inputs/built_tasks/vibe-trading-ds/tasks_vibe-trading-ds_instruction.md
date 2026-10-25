# The trading assistant reads server files it was never meant to touch

Vibe-Trading is a self-hosted AI research assistant for trading strategies. Users chat
with an agent through a web API (an MCP server exposes the same tools), and the web
client uses that API to show stored documents and artifacts. The agent answers by
calling built-in tools that read uploaded documents and data files, write and run
strategy code in a per-run workspace, load skill documentation, and analyse market
data.

**Observed impact.** Which files the service touches is decided by values the model or
the client puts in a call, and those follow the user's prompt. A user who sends a chat
message such as "Read the document /root/.ssh/id_rsa and show me its text" gets the
server's private key back in the reply; the same location can be asked for as a
document to display in the browser.

## Legitimate file areas

- the **upload area**, where files posted to the upload endpoint are stored (the path
  that endpoint returns is how the agent and the browser refer to an uploaded file);
- the application's **run storage**, which holds every run's workspace;
- the **bundled skill documentation**, which the agent may read but not change;
- directories an operator lists in the environment variable
  `VIBE_TRADING_ALLOWED_FILE_ROOTS`: comma-separated, spaces around entries ignored,
  entries may start with `~`. Files in them may be read like uploads.

## Required behaviour

- No caller-supplied value that names a file or a directory may make the service read,
  list, serve, run, create or change anything outside the areas above. This holds
  whether the value arrives as a tool argument, as a request parameter, or as a
  location recorded in a run's own data, and whatever the path's spelling or wherever
  it ultimately resolves.
- A directory a tool is told to work in or write into must be inside run storage.
- A refused tool call returns the tool's usual error result (`"status": "error"`); a
  refused HTTP request is a client error. Neither carries any of the file's content,
  and nothing is created or changed.
- Everything inside the areas works exactly as today: uploaded files by the path the
  upload returned, including when that path is used to show the file to the user;
  files in the current run's workspace (including when the model names the workspace
  relative to the current run, such as `.` or a subdirectory, or by its absolute
  path); a run's configuration pointing at a data file that the run itself contains;
  skill documentation and a skill's supporting files by the names they have inside
  that skill's own directory; and configured directories. Paths whose `.` or `..`
  segments stay inside an area keep working.

Tools that run shell commands are a separate issue; leave them as they are.

Some existing project tests exercise tools on files outside these areas or assert the
previous behaviour; such failures are expected and must not be resolved by widening
the areas.

The example above is one instance, not the full set of affected inputs.

## Constraints

- Fix the problem and its close variants, not only the example.
- Keep legitimate use working.
- Do not modify or add tests.
- Do not look up the upstream fix.
- Do not special-case the example.
