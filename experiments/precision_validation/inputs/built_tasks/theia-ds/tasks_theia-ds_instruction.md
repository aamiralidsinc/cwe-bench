# AI features must not act for an untrusted workspace

## The system

Eclipse Theia is an IDE with AI features. It also supports Restricted Mode: a workspace the
user has not trusted must not be able to make those features act on the user's behalf.

## What we observed

We opened a workspace we had not trusted and used an AI feature there. It acted on the
workspace's behalf without the safeguards an untrusted workspace should get. The example is
illustrative; the property below is what must hold.

## Security property that must hold

In a workspace the user has not trusted, no AI feature may start, run or act on the user's
behalf, and nothing the workspace supplies may influence what an AI feature does or draws on.

- **Nothing runs.** Every attempt to use an AI feature is refused with an error, however it is reached, and
  no AI feature starts or initialises on the workspace's behalf. No external effect is produced
  and nothing is left behind as though it had been. Whether AI is enabled is a preference;
  whether it may run is governed by trust.
- **Nothing supplied by the workspace is used as configuration.** No value a workspace, or a
  folder within it, supplies for an AI feature may have any effect. The user's own values and
  the product's built-in defaults keep applying exactly as before, and are never dropped or
  replaced by empty values: where the workspace would otherwise override one of them, the
  user value or the default is what is used. A value naming a location inside the workspace
  is not applied while the workspace is untrusted; other user and default values keep
  applying.
- **Nothing supplied by the workspace is loaded as content.** Content that a workspace
  supplies, or points an AI feature at, is not loaded and does not shape any AI behaviour,
  including content at a location inside the workspace that a built-in default or a user
  value names. Content the user has made available independently of a workspace still loads.
- **Unknown trust is treated as untrusted.** Until trust has been established the workspace is
  treated as untrusted; the IDE must never start out permissive. Trust gained or lost while
  running takes effect immediately, in both directions.
- **A trusted workspace is unchanged.** A trusted workspace behaves exactly as it does today.
  Whether AI is enabled still governs what is offered; trust governs only what may run.
  Enabling AI must not make an untrusted workspace's features usable, and withholding trust
  must not take them out of view. A value the user saves is still saved, and must not be
  silently discarded while a workspace is untrusted.

## Contracts the checks rely on

- The services involved are constructed through Theia's dependency-injection container.
  Workspace trust is supplied as `WorkspaceTrustService` (`getWorkspaceTrust()` and
  `onDidChangeWorkspaceTrust`); hidden checks bind preferences through `PreferenceService`;
  its public API is available. Anything a hidden check resolves must be bound in its
  package's dependency-injection module.
- Hidden checks resolve `AIActivationService` and read `isActive`, `canRun` and their change
  events; `canRun` is false whenever the workspace is not trusted.

## Constraints

- Fix the flaw everywhere it can be reached, not only the example. Do not special-case
  anything taken from this report.
- Keep legitimate use working as described above.
- Do not modify or add tests; hidden tests check the behaviour.
- Do not look up or copy an upstream fix for this issue.

## Notes

The repository is in `/app` with its dependencies installed. There is no network.
The project compiles with `./node_modules/.bin/tsc --build` and its own tests run
with mocha from each package's `lib` output.
