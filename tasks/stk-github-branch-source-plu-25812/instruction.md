# Any logged-in user can list the registered GitHub Enterprise servers

Jenkins is a build automation server. This plugin adds multibranch and organization-folder
support for GitHub, and lets an administrator register additional GitHub Enterprise servers,
each with a display name and an API address. Those names and addresses are internal
infrastructure details, and the plugin offers them as the server choices when a GitHub
connection is set up.

Impact: a user who can log in but may configure nothing can read every registered server's name
and API address. One observed case: a user holding only the overall read permission asks the
organization-folder setup form for its server choices directly over HTTP and receives the
complete list of registered servers and their API addresses.

The property: the names and API addresses of the registered GitHub Enterprise servers must never
be disclosed to a caller unless that caller either administers the server and the request is made
outside any item, or may configure the item the request is made for. Any other caller must
receive no registered server in the choices.

Contracts:
- A caller who is not entitled to the list is refused with a client error, or receives a choice
  list that names no registered server. Either refusal has no effect.
- The ordinary public GitHub entry must remain one of the choices.
- Everything that works today keeps working exactly as it does today.
- Fix the problem and its close variants. The example is an example, not the full set.
- Do not look up the upstream fix. Do not special-case the example.
