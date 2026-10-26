# Static file serving can reach a file past its route's access check

This project is a Go web framework. Applications use it to serve static files from a directory
and to protect areas of a site with route-level access checks (for example, an authentication
check on an admin area).

We observed that `GET /admin%2Fsettings.json` returns the contents of `admin/settings.json` even
though the admin area's access check never runs for that request. A request written that way is
answered like an ordinary public file request.

**Property.** Whenever the framework turns request path data into a file location to serve, a
percent-encoded path separator must not act as a path separator. A request that needs one to
reach a file must be refused with a client error and must not return the file's content. This
holds for every way the framework can be asked to serve files and for every part of the request
that supplies the path.

**Contracts.**
- A refused request answers with a 4xx status and no file content.
- Everything that works today keeps working exactly as today: ordinary files, directory requests
  and their redirects, index files, requests whose separators are real separators, and files
  whose names contain a literal percent sign when that sign is requested encoded.
- The example above is one example; it is not the full set of affected inputs or setups.

**Constraints.**
- Fix the problem and its close variants.
- Keep legitimate use working.
- Do not look up the upstream fix or advisory.
- Do not special-case the example path.
